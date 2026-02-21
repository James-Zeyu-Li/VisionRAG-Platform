#!/usr/bin/env python3
import argparse
import base64
import json
import os
import random
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


PID_DIR = "/tmp/visionrag-local-smoke"
STATUS_OK_CODE = 1000


def run_cmd(args, check=True):
    proc = subprocess.run(args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        cmd_text = " ".join(args)
        raise RuntimeError(f"command failed: {cmd_text}\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def kubectl_exec(namespace, resource, container, command):
    args = ["kubectl", "-n", namespace, "exec", resource]
    if container:
        args.extend(["-c", container])
    args.extend(["--", "sh", "-lc", command])
    return run_cmd(args)


def http_json(method, url, payload=None, headers=None, timeout=20):
    body = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode("utf-8")
        return json.loads(text) if text else {}


def http_text(method, url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def wait_port(host, port, timeout=12):
    start = time.time()
    while time.time() - start < timeout:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect((host, port))
            return True
        except Exception:
            time.sleep(0.3)
        finally:
            s.close()
    return False


class PortForwardManager:
    def __init__(self):
        self.procs = []
        os.makedirs(PID_DIR, exist_ok=True)

    def start(self, name, namespace, resource, local_port, remote_port):
        log_file = os.path.join(PID_DIR, f"{name}.log")
        log_handle = open(log_file, "w")
        proc = subprocess.Popen(
            ["kubectl", "-n", namespace, "port-forward", resource, f"{local_port}:{remote_port}"],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        self.procs.append((name, proc, log_handle))
        if proc.poll() is not None:
            raise RuntimeError(f"port-forward for {name} exited immediately (see {log_file})")
        if not wait_port("127.0.0.1", local_port, timeout=15):
            raise RuntimeError(f"port-forward for {name} failed (see {log_file})")

    def stop_all(self):
        for _, proc, log_handle in self.procs:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                log_handle.close()
            except Exception:
                pass
        self.procs = []


def decode_jwt_username(token):
    parts = token.split(".")
    if len(parts) < 2:
        raise RuntimeError("invalid JWT format")
    payload = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")).decode("utf-8"))
    username = data.get("username")
    if not username:
        raise RuntimeError("username not found in JWT payload")
    return username


def expect_code_ok(resp, name):
    code = resp.get("status_code")
    if code != STATUS_OK_CODE:
        body = json.dumps(resp, ensure_ascii=False)
        raise RuntimeError(f"{name} failed: status_code={code}, body={body}")


def check_deployments(namespace):
    expected = [
        "gateway-service",
        "public-service",
        "chat-service",
        "redis",
        "rabbitmq",
        "postgres-db",
    ]
    missing = []
    not_ready = []
    for deploy in expected:
        ready = run_cmd(
            [
                "kubectl",
                "-n",
                namespace,
                "get",
                "deploy",
                deploy,
                "-o",
                "jsonpath={.status.readyReplicas}",
            ],
            check=False,
        )
        replicas = run_cmd(
            [
                "kubectl",
                "-n",
                namespace,
                "get",
                "deploy",
                deploy,
                "-o",
                "jsonpath={.status.replicas}",
            ],
            check=False,
        )
        if ready == "" and replicas == "":
            missing.append(deploy)
            continue
        if (ready or "0") == "0":
            not_ready.append(deploy)
    if missing:
        raise RuntimeError(f"missing deployments: {', '.join(missing)}")
    if not_ready:
        raise RuntimeError(f"deployments not ready: {', '.join(not_ready)}")


def infra_health_checks(namespace):
    redis_ping = kubectl_exec(
        namespace,
        "deploy/redis",
        "redis",
        "redis-cli -a \"$REDIS_PASSWORD\" PING",
    )
    if "PONG" not in redis_ping:
        raise RuntimeError(f"redis ping failed: {redis_ping}")

    rabbit_metrics = kubectl_exec(
        namespace,
        "deploy/rabbitmq",
        None,
        "wget -qO- http://127.0.0.1:15692/metrics | head -n 20",
    )
    if "# TYPE " not in rabbit_metrics and "# HELP " not in rabbit_metrics:
        raise RuntimeError(f"rabbitmq metrics check failed: {rabbit_metrics}")

    pg_ready = kubectl_exec(
        namespace,
        "deploy/postgres-db",
        "postgres",
        "pg_isready -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\"",
    )
    if "accepting connections" not in pg_ready.lower():
        raise RuntimeError(f"postgres check failed: {pg_ready}")


def read_captcha_from_redis(namespace, email):
    out = kubectl_exec(
        namespace,
        "deploy/redis",
        "redis",
        f"redis-cli -a \"$REDIS_PASSWORD\" GET \"captcha:{email}\"",
    )
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("captcha not found in redis")
    return lines[-1]


def app_health_checks(gateway_url, public_url, chat_url):
    gateway_health = http_json("GET", f"{gateway_url}/health")
    if gateway_health.get("status") != "UP":
        raise RuntimeError(f"gateway health failed: {gateway_health}")
    public_health = http_json("GET", f"{public_url}/health")
    if public_health.get("status") != "UP":
        raise RuntimeError(f"public health failed: {public_health}")
    chat_health = http_json("GET", f"{chat_url}/health")
    if chat_health.get("status") != "UP":
        raise RuntimeError(f"chat health failed: {chat_health}")

    if "go_" not in http_text("GET", f"{gateway_url}/metrics"):
        raise RuntimeError("gateway metrics endpoint is not returning expected Prometheus text")
    if "go_" not in http_text("GET", f"{public_url}/metrics"):
        raise RuntimeError("public metrics endpoint is not returning expected Prometheus text")
    if "go_" not in http_text("GET", f"{chat_url}/metrics"):
        raise RuntimeError("chat metrics endpoint is not returning expected Prometheus text")


def run_user_flow(namespace, gateway_url, with_ai, model_type):
    password = "Passw0rd123!"
    register_token = None
    email = None
    register_attempts = 5
    for i in range(register_attempts):
        unique = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        email = f"smoke_{unique}@example.com"
        captcha_resp = http_json("POST", f"{gateway_url}/api/v1/user/captcha", {"email": email})
        expect_code_ok(captcha_resp, "captcha")
        captcha = read_captcha_from_redis(namespace, email)
        register_resp = http_json(
            "POST",
            f"{gateway_url}/api/v1/user/register",
            {"email": email, "password": password, "captcha": captcha},
        )
        if register_resp.get("status_code") == STATUS_OK_CODE:
            register_token = register_resp.get("token")
            break
        if register_resp.get("status_code") != 2002:
            expect_code_ok(register_resp, "register")
        # Retry on conflict-like register failure.
        time.sleep(0.2 + i * 0.1)

    if not register_token:
        raise RuntimeError(
            f"register failed after {register_attempts} attempts: {json.dumps(register_resp, ensure_ascii=False)}"
        )

    username = decode_jwt_username(register_token)
    login_resp = http_json(
        "POST",
        f"{gateway_url}/api/v1/user/login",
        {"username": username, "password": password},
    )
    expect_code_ok(login_resp, "login")
    token = login_resp.get("token")
    if not token:
        raise RuntimeError("login token missing")
    auth = {"Authorization": f"Bearer {token}"}

    create_resp = http_json(
        "POST",
        f"{gateway_url}/api/v1/session/create",
        {"title": "smoke-session"},
        headers=auth,
    )
    expect_code_ok(create_resp, "session.create")
    session_id = create_resp.get("sessionId")
    if not session_id:
        raise RuntimeError("sessionId missing")

    expect_code_ok(
        http_json("GET", f"{gateway_url}/api/v1/session/list", headers=auth),
        "session.list",
    )
    expect_code_ok(
        http_json(
            "POST",
            f"{gateway_url}/api/v1/session/history",
            {"sessionId": session_id},
            headers=auth,
        ),
        "session.history",
    )
    expect_code_ok(
        http_json("GET", f"{gateway_url}/api/v1/AI/chat/sessions", headers=auth),
        "ai.chat.sessions",
    )

    if with_ai:
        expect_code_ok(
            http_json(
                "POST",
                f"{gateway_url}/api/v1/AI/chat/send-new-session",
                {"question": "hello", "modelType": model_type},
                headers=auth,
                timeout=60,
            ),
            "ai.chat.send-new-session",
        )
    return username, email


def main():
    parser = argparse.ArgumentParser(
        description="VisionRAG local smoke CLI: port-forward + health + register/login + chat/session",
    )
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--with-ai", action="store_true", help="also run model inference test")
    parser.add_argument("--model-type", default="4", help='modelType for AI test, default "4" (Ollama)')
    args = parser.parse_args()

    pf = PortForwardManager()
    try:
        print("[1/5] Checking deployment readiness")
        check_deployments(args.namespace)

        print("[2/5] Starting port-forwards")
        pf.start("gateway", args.namespace, "svc/gateway-service", 19000, 9000)
        pf.start("public", args.namespace, "svc/public-service", 19091, 9090)
        pf.start("chat", args.namespace, "svc/chat-service", 19092, 9092)

        gateway_url = "http://127.0.0.1:19000"
        public_url = "http://127.0.0.1:19091"
        chat_url = "http://127.0.0.1:19092"

        print("[3/5] Checking app health and metrics")
        app_health_checks(gateway_url, public_url, chat_url)

        print("[4/5] Checking infra internal health (Redis/RabbitMQ/Postgres)")
        infra_health_checks(args.namespace)

        print("[5/5] Running register/login/session/chat flow")
        username, email = run_user_flow(
            args.namespace,
            gateway_url,
            args.with_ai,
            args.model_type,
        )

        print("OK: local smoke test passed")
        print(f"- namespace: {args.namespace}")
        print(f"- gateway: {gateway_url}")
        print(f"- public: {public_url}")
        print(f"- chat: {chat_url}")
        print(f"- username: {username}")
        print(f"- email: {email}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        print(f"FAILED: HTTP {exc.code} {detail}")
        sys.exit(2)
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)
    finally:
        pf.stop_all()


if __name__ == "__main__":
    main()
