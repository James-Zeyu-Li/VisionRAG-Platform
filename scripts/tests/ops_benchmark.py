#!/usr/bin/env python3
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone


def run_cmd(args, check=True):
    proc = subprocess.run(args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        cmd_text = " ".join(args)
        raise RuntimeError(
            f"command failed: {cmd_text}\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_deploy_replicas(namespace, deploy):
    out = run_cmd(
        [
            "kubectl",
            "-n",
            namespace,
            "get",
            "deploy",
            deploy,
            "-o",
            "jsonpath={.spec.replicas}",
        ]
    )
    if out == "":
        raise RuntimeError(f"deployment {deploy} has no replica count")
    return int(out)


def get_container_image(namespace, deploy, container):
    out = run_cmd(
        [
            "kubectl",
            "-n",
            namespace,
            "get",
            "deploy",
            deploy,
            "-o",
            f"jsonpath={{.spec.template.spec.containers[?(@.name==\"{container}\")].image}}",
        ]
    )
    if out == "":
        raise RuntimeError(
            f"container {container} not found in deployment {deploy}; set --container to a valid container name"
        )
    return out


def set_deploy_image(namespace, deploy, container, image):
    run_cmd(
        [
            "kubectl",
            "-n",
            namespace,
            "set",
            "image",
            f"deploy/{deploy}",
            f"{container}={image}",
        ]
    )


def wait_rollout(namespace, deploy, timeout_seconds):
    run_cmd(
        [
            "kubectl",
            "-n",
            namespace,
            "rollout",
            "status",
            f"deploy/{deploy}",
            f"--timeout={timeout_seconds}s",
        ]
    )


def fault_visible_in_pods(namespace, app_label):
    out = run_cmd(
        [
            "kubectl",
            "-n",
            namespace,
            "get",
            "pods",
            "-l",
            f"app={app_label}",
            "-o",
            "json",
        ]
    )
    data = json.loads(out)
    items = data.get("items", [])
    if not items:
        return False

    bad_waiting = {"ErrImagePull", "ImagePullBackOff", "CrashLoopBackOff"}
    for pod in items:
        for cs in pod.get("status", {}).get("containerStatuses", []):
            waiting = cs.get("state", {}).get("waiting", {})
            reason = waiting.get("reason", "")
            if reason in bad_waiting:
                return True
            # In manual runbooks, "not ready pod" is usually considered an incident signal.
            if cs.get("ready") is False:
                return True
    return False


def find_new_file(dir_path, before_set):
    files = []
    if os.path.isdir(dir_path):
        for name in os.listdir(dir_path):
            full = os.path.join(dir_path, name)
            if os.path.isfile(full) and full not in before_set:
                files.append(full)
    if not files:
        return None
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


def run_alert_experiment(args, report_dir):
    os.makedirs(report_dir, exist_ok=True)
    before = set(
        os.path.join(report_dir, name)
        for name in os.listdir(report_dir)
        if os.path.isfile(os.path.join(report_dir, name))
    )
    cmd = [
        "python3",
        "scripts/alert_experiment.py",
        "--namespace",
        args.namespace,
        "--deployment",
        args.deployment,
        "--fault-mode",
        "bad-image",
        "--container",
        args.container,
        "--fault-image",
        args.fault_image,
        "--target-alert",
        args.target_alert,
        "--inject-seconds",
        str(args.alert_inject_seconds),
        "--poll-seconds",
        str(args.alert_poll_seconds),
        "--report-dir",
        report_dir,
    ]
    print("[benchmark] running alert-driven detection experiment")
    run_cmd(cmd)
    report_file = find_new_file(report_dir, before)
    if not report_file:
        raise RuntimeError("failed to locate alert experiment report file")
    with open(report_file, "r", encoding="utf-8") as f:
        return report_file, json.load(f)


def run_manual_baseline(args):
    print(
        f"[benchmark] running manual baseline (poll interval={args.manual_poll_seconds}s)"
    )
    baseline_image = get_container_image(
        args.namespace, args.deployment, args.container)
    start = time.time()
    detected_at = None
    restored = False
    poll_samples = []

    try:
        set_deploy_image(
            args.namespace,
            args.deployment,
            args.container,
            args.fault_image,
        )
        deadline = start + args.manual_timeout_seconds
        while time.time() < deadline:
            time.sleep(args.manual_poll_seconds)
            ts = time.time()
            visible = fault_visible_in_pods(args.namespace, args.deployment)
            poll_samples.append(
                {
                    "ts": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                    "seconds_from_start": round(ts - start, 3),
                    "fault_visible": visible,
                }
            )
            if visible:
                detected_at = ts
                break
    finally:
        set_deploy_image(
            args.namespace,
            args.deployment,
            args.container,
            baseline_image,
        )
        wait_rollout(args.namespace, args.deployment,
                     args.rollout_timeout_seconds)
        restored = True

    return {
        "started_at": datetime.fromtimestamp(start, tz=timezone.utc).isoformat(),
        "ended_at": now_iso(),
        "detected_at": (
            datetime.fromtimestamp(detected_at, tz=timezone.utc).isoformat()
            if detected_at
            else None
        ),
        "mttd_seconds": round(detected_at - start, 3) if detected_at else None,
        "detected": detected_at is not None,
        "poll_samples": poll_samples,
        "deployment_restored": restored,
    }


def with_prometheus_port_forward(namespace, service_name):
    cmd = [
        "kubectl",
        "-n",
        namespace,
        "port-forward",
        f"svc/{service_name}",
        "9090:9090",
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        ok = subprocess.run(
            ["curl", "-sf", "http://127.0.0.1:9090/-/ready"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if ok.returncode == 0:
            return proc
        time.sleep(1)
    proc.terminate()
    proc.wait(timeout=3)
    raise RuntimeError(
        "Prometheus port-forward failed to become ready in time")


def main():
    parser = argparse.ArgumentParser(
        description="A/B benchmark for alert-driven detection vs manual polling baseline."
    )
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--deployment", default="chat-service")
    parser.add_argument("--container", default="chat-service")
    parser.add_argument(
        "--fault-image",
        default="invalid.local/visionrag/fault-injection:does-not-exist",
    )
    parser.add_argument("--target-alert", default="VisionRAGServiceTargetDown")
    parser.add_argument("--alert-inject-seconds", type=int, default=260)
    parser.add_argument("--alert-poll-seconds", type=int, default=5)
    parser.add_argument(
        "--manual-poll-seconds",
        type=int,
        default=300,
        help="Assumed manual runbook polling interval for baseline detection.",
    )
    parser.add_argument(
        "--manual-timeout-seconds",
        type=int,
        default=900,
        help="Timeout for manual baseline detection loop.",
    )
    parser.add_argument("--rollout-timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--prom-namespace",
        default="monitoring",
        help="Namespace where Prometheus service exists.",
    )
    parser.add_argument(
        "--prom-service",
        default="kube-prometheus-stack-prometheus",
        help="Prometheus service name used for local port-forward.",
    )
    parser.add_argument(
        "--report-dir",
        default="reports/benchmarks",
        help="Directory to write benchmark reports.",
    )
    args = parser.parse_args()

    _ = get_deploy_replicas(args.namespace, args.deployment)
    _ = get_container_image(args.namespace, args.deployment, args.container)

    pf_proc = None
    try:
        print("[benchmark] starting temporary Prometheus port-forward")
        pf_proc = with_prometheus_port_forward(
            args.prom_namespace, args.prom_service)
        alert_report_dir = os.path.join(args.report_dir, "alert-runs")
        alert_report_file, alert_report = run_alert_experiment(
            args, alert_report_dir)
    finally:
        if pf_proc is not None:
            try:
                pf_proc.send_signal(signal.SIGTERM)
                pf_proc.wait(timeout=3)
            except Exception:
                try:
                    pf_proc.kill()
                except Exception:
                    pass

    manual_result = run_manual_baseline(args)

    alert_mttd = alert_report.get("result", {}).get("mttd_seconds")
    manual_mttd = manual_result.get("mttd_seconds")

    mttd_improvement_percent = None
    if alert_mttd is not None and manual_mttd is not None and manual_mttd > 0:
        mttd_improvement_percent = round(
            ((manual_mttd - alert_mttd) / manual_mttd) * 100.0, 3
        )

    benchmark = {
        "experiment": {
            "namespace": args.namespace,
            "deployment": args.deployment,
            "container": args.container,
            "fault_image": args.fault_image,
            "target_alert": args.target_alert,
            "manual_poll_seconds_assumption": args.manual_poll_seconds,
        },
        "alert_path": {
            "report_file": alert_report_file,
            "target_alert_detected": alert_report.get("result", {}).get(
                "target_alert_detected"
            ),
            "mttd_seconds": alert_mttd,
            "collateral_alert_count": alert_report.get("result", {}).get(
                "collateral_alert_count"
            ),
            "collateral_alert_names": alert_report.get("result", {}).get(
                "collateral_alert_names"
            ),
            "deployment_restored": alert_report.get("result", {}).get(
                "deployment_restored"
            ),
        },
        "manual_path": manual_result,
        "comparison": {
            "mttd_improvement_percent": mttd_improvement_percent,
            "formula": "(manual_mttd - alert_mttd) / manual_mttd * 100",
        },
    }

    os.makedirs(args.report_dir, exist_ok=True)
    filename = datetime.now(timezone.utc).strftime(
        "ops-benchmark-%Y%m%dT%H%M%SZ.json")
    out_path = os.path.join(args.report_dir, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(benchmark, f, indent=2)

    print("[benchmark] completed")
    print(f"[benchmark] report: {out_path}")
    print(
        json.dumps(
            {
                "alert_mttd_seconds": alert_mttd,
                "manual_mttd_seconds": manual_mttd,
                "mttd_improvement_percent": mttd_improvement_percent,
                "manual_poll_seconds_assumption": args.manual_poll_seconds,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)
