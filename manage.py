#!/usr/bin/env python3
import subprocess
import sys
import argparse
import os
from datetime import datetime

"""
VisionRAG Platform Manager CLI
Available Actions:
  init   - One-time setup for Minikube: monitoring stack -> build -> image load -> secret apply/deploy -> rollout checks -> UI
  deploy - Daily deploy for Minikube: build(tagged) -> image load -> helm upgrade -> rollout checks
  check  - Run fmt + lint + tidy in one command
  update-secret - Apply/rotate Kubernetes secret and restart dependent deployments
  build  - Build Docker images for all Go services
  verify - Verify Helm, pods, observability stack, and API smoke flow
  smoke-test - Run local smoke tests (port-forward + health + auth + chat flow)
  ollama - Ensure local Ollama docker is running and model is ready
  obs-ui-start - Start Prometheus/Grafana local port-forward in background
  obs-ui-stop  - Stop Prometheus/Grafana local port-forward
  obs-ui-status - Show Prometheus/Grafana port-forward status
  clean  - Uninstall the Helm release from the cluster
  status - Show status of pods, services, and core infrastructure
"""

# 颜色定义
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

CHART_PATH = "charts/visionrag-platform"
SERVICES = {
    "public": {"path": "services/PublicServiceGo", "image": "visionrag-public"},
    "chat": {"path": "services/ChatServiceGo", "image": "visionrag-chat"},
    "gateway": {"path": "services/GatewayServiceGo", "image": "visionrag-gateway"},
}


def run_command(cmd, description):
    print(f"{BLUE}==>{RESET} {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"{GREEN}  Done!{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}  Error during: {description}{RESET}")
        sys.exit(1)


def run_command_soft(cmd, description):
    print(f"{BLUE}==>{RESET} {description}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode == 0:
        print(f"{GREEN}  Done!{RESET}")
    else:
        print(f"{YELLOW}  Skip (non-blocking): {description}{RESET}")


def resolve_image_tag():
    forced_tag = os.getenv("VISIONRAG_IMAGE_TAG", "").strip()
    if forced_tag:
        return forced_tag

    git_tag = subprocess.run(
        "git rev-parse --short HEAD",
        shell=True,
        capture_output=True,
        text=True,
    )
    if git_tag.returncode == 0:
        return git_tag.stdout.strip()

    return datetime.utcnow().strftime("dev-%Y%m%d%H%M%S")


def build(tag):
    print(f"{YELLOW}--- Building Docker Images ---{RESET}")
    for name, info in SERVICES.items():
        cmd = (
            f"docker build -t {info['image']}:{tag} -t {info['image']}:latest "
            f"-f {info['path']}/Dockerfile ."
        )
        run_command(cmd, f"Building {name} service")


def load_images_to_minikube(tag):
    print(f"{YELLOW}--- Loading images into Minikube ---{RESET}")
    for _, info in SERVICES.items():
        run_command(
            f"minikube image load {info['image']}:{tag}",
            f"Loading image {info['image']}:{tag} into Minikube",
        )


def format_code():
    print(f"{YELLOW}--- Formatting Codebase ---{RESET}")
    # 1. 格式化 Go 代码
    for name, info in SERVICES.items():
        run_command(
            f"cd {info['path']} && go fmt ./...", f"Formatting Go {name} service"
        )
    run_command("cd shared && go fmt ./...", "Formatting Go shared module")

    # 2. 格式化 Python 文件 (如果安装了 black)
    if subprocess.run("which black", shell=True, capture_output=True).returncode == 0:
        run_command("black manage.py", "Formatting Python script")
    else:
        print(f"{BLUE}  Skip Python formatting (black not found){RESET}")

    print(f"{GREEN}Format complete.{RESET}")


def lint():
    print(f"{YELLOW}--- Linting Helm Charts ---{RESET}")
    run_command(f"helm lint {CHART_PATH}", "Helm linting")


def clean():
    print(f"{RED}--- Cleaning Helm Release ---{RESET}")
    run_command("scripts/observability-ui.sh stop",
                "Stopping observability UIs")
    run_command("helm uninstall visionrag", "Uninstalling Helm release")


def tidy():
    print(f"{YELLOW}--- Tidy Go Modules ---{RESET}")
    for name, info in SERVICES.items():
        run_command(f"cd {info['path']} && go mod tidy",
                    f"Tidying {name} service")
    run_command("cd shared && go mod tidy", "Tidying shared module")


def check():
    print(f"{YELLOW}--- Running check suite (fmt + lint + tidy) ---{RESET}")
    format_code()
    lint()
    tidy()


def ensure_ollama():
    print(f"{YELLOW}--- Ensuring local Ollama ---{RESET}")
    run_command("scripts/ensure-ollama.sh",
                "Starting/checking Ollama container")


def smoke_test():
    print(f"{YELLOW}--- Running local smoke test CLI ---{RESET}")
    run_command(
        "python3 scripts/local_smoke_cli.py",
        "Running health/internal/auth/chat smoke tests",
    )


def verify():
    print(f"{YELLOW}--- Verifying platform ---{RESET}")
    run_command("kubectl config current-context",
                "Checking current kubectl context")
    run_command("helm list -n default", "Checking Helm release status")
    run_command("kubectl -n default get pods", "Checking app pods")
    run_command("kubectl -n default get svc", "Checking app services")
    run_command("kubectl -n default get servicemonitor",
                "Checking ServiceMonitors")
    run_command("kubectl -n default get prometheusrule",
                "Checking Prometheus alert rules")
    run_command("kubectl -n monitoring get pods", "Checking monitoring pods")
    run_command("kubectl -n monitoring get svc kube-prometheus-stack-prometheus kube-prometheus-stack-grafana",
                "Checking Prometheus/Grafana services")
    obs_ui_status()
    run_command_soft("curl -sf http://127.0.0.1:9090/-/ready >/dev/null",
                     "Checking local Prometheus readiness (port-forward optional)")
    run_command_soft("curl -sf http://127.0.0.1:3000/api/health >/dev/null",
                     "Checking local Grafana health (port-forward optional)")
    smoke_test()
    print(f"\n{GREEN}Verify completed.{RESET}")


def ensure_monitoring_stack():
    print(f"{YELLOW}--- Ensuring monitoring stack (CRDs + Prometheus/Grafana) ---{RESET}")
    run_command(
        "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true",
        "Adding prometheus-community Helm repo",
    )
    run_command("helm repo update", "Updating Helm repos")
    run_command(
        "helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack "
        "-n monitoring --create-namespace --set nodeExporter.enabled=false",
        "Installing/upgrading kube-prometheus-stack",
    )


def rollout_and_wait():
    run_command(
        "kubectl -n default rollout restart deploy/chat-service deploy/public-service deploy/gateway-service",
        "Restarting application deployments",
    )
    run_command(
        "kubectl -n default rollout status deploy/chat-service --timeout=240s",
        "Waiting for chat-service to become Ready",
    )
    run_command(
        "kubectl -n default rollout status deploy/public-service --timeout=240s",
        "Waiting for public-service to become Ready",
    )
    run_command(
        "kubectl -n default rollout status deploy/gateway-service --timeout=240s",
        "Waiting for gateway-service to become Ready",
    )


def update_secret():
    print(f"{YELLOW}--- Updating Kubernetes secret ---{RESET}")
    run_command(
        "scripts/apply-k8s-secret.sh --namespace default --secret-name visionrag-platform-secrets",
        "Applying visionrag-platform-secrets in default namespace",
    )
    run_command(
        "kubectl -n default rollout restart deploy/chat-service deploy/public-service deploy/gateway-service deploy/postgres-db deploy/redis deploy/rabbitmq",
        "Restarting deployments that depend on secret values",
    )


def helm_upgrade_with_tag(tag):
    run_command(
        f"helm upgrade --install visionrag {CHART_PATH} -n default --create-namespace "
        f"--set-string microservices.public.tag={tag} "
        f"--set-string microservices.chat.tag={tag} "
        f"--set-string microservices.gateway.tag={tag}",
        f"Helm upgrade/install (tag={tag})",
    )


def deploy():
    tag = resolve_image_tag()
    print(f"{YELLOW}--- Minikube deploy ---{RESET}")
    print(f"{BLUE}Using image tag: {tag}{RESET}")
    ensure_ollama()
    build(tag)
    load_images_to_minikube(tag)
    lint()
    helm_upgrade_with_tag(tag)
    rollout_and_wait()
    print(f"\n{GREEN}Deploy completed.{RESET}")


def init():
    tag = resolve_image_tag()
    print(f"{YELLOW}--- Minikube init ---{RESET}")
    print(f"{BLUE}Using image tag: {tag}{RESET}")
    ensure_monitoring_stack()
    ensure_ollama()
    build(tag)
    load_images_to_minikube(tag)
    run_command("scripts/apply-k8s-secret.sh --namespace default --secret-name visionrag-platform-secrets",
                "Applying secret")
    helm_upgrade_with_tag(tag)
    rollout_and_wait()
    obs_ui_start()
    print(f"\n{GREEN}Observability UIs are ready:{RESET}")
    print(f"Prometheus: {BLUE}http://127.0.0.1:9090/targets{RESET}")
    print(f"Grafana:    {BLUE}http://127.0.0.1:3000{RESET}")


def obs_ui_start():
    run_command("scripts/observability-ui.sh start",
                "Starting observability UIs")


def obs_ui_stop():
    run_command("scripts/observability-ui.sh stop",
                "Stopping observability UIs")
    # Fallback cleanup for manually started or stale port-forward processes.
    run_command("pkill -f 'kubectl.*port-forward.*kube-prometheus-stack-prometheus' || true",
                "Killing any stale Prometheus port-forward processes")
    run_command("pkill -f 'kubectl.*port-forward.*kube-prometheus-stack-grafana' || true",
                "Killing any stale Grafana port-forward processes")


def obs_ui_status():
    run_command("scripts/observability-ui.sh status",
                "Checking observability UI status")


def main():
    parser = argparse.ArgumentParser(description="VisionRAG Platform Manager")
    parser.add_argument(
        "action",
        choices=["init", "deploy", "check", "update-secret", "build", "ollama",
                 "smoke-test", "verify",
                 "obs-ui-start", "obs-ui-stop", "obs-ui-status",
                 "clean", "status"],
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "build":
        tag = resolve_image_tag()
        print(f"{BLUE}Using image tag: {tag}{RESET}")
        build(tag)
    elif args.action == "deploy":
        deploy()
    elif args.action == "init":
        init()
    elif args.action == "check":
        check()
    elif args.action == "update-secret":
        update_secret()
    elif args.action == "ollama":
        ensure_ollama()
    elif args.action == "smoke-test":
        smoke_test()
    elif args.action == "verify":
        verify()
    elif args.action == "obs-ui-start":
        obs_ui_start()
    elif args.action == "obs-ui-stop":
        obs_ui_stop()
    elif args.action == "obs-ui-status":
        obs_ui_status()
    elif args.action == "clean":
        clean()
    elif args.action == "status":
        run_command("kubectl get pods,svc", "Cluster Status")


if __name__ == "__main__":
    main()
