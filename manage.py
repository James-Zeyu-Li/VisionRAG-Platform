#!/usr/bin/env python3
import subprocess
import sys
import argparse

"""
VisionRAG Platform Manager CLI
Available Actions:
  init   - One-time setup for Minikube: monitoring stack -> build -> image load -> secret apply/deploy -> rollout checks -> UI
  deploy - Daily deploy for Minikube: build -> image load -> helm upgrade -> rollout checks
  check  - Run fmt + lint + tidy in one command
  update-secret - Apply/rotate Kubernetes secret and restart dependent deployments
  build  - Build Docker images for all Go services
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


def build():
    print(f"{YELLOW}--- Building Docker Images ---{RESET}")
    for name, info in SERVICES.items():
        cmd = f"docker build -t {info['image']}:latest -f {info['path']}/Dockerfile ."
        run_command(cmd, f"Building {name} service")


def load_images_to_minikube():
    print(f"{YELLOW}--- Loading images into Minikube ---{RESET}")
    for _, info in SERVICES.items():
        run_command(
            f"minikube image load {info['image']}:latest",
            f"Loading image {info['image']}:latest into Minikube",
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


def deploy():
    print(f"{YELLOW}--- Minikube deploy ---{RESET}")
    ensure_ollama()
    build()
    load_images_to_minikube()
    lint()
    run_command(
        f"helm upgrade --install visionrag {CHART_PATH} -n default --create-namespace",
        "Helm upgrade/install",
    )
    rollout_and_wait()
    print(f"\n{GREEN}Deploy completed.{RESET}")


def init():
    print(f"{YELLOW}--- Minikube init ---{RESET}")
    ensure_monitoring_stack()
    ensure_ollama()
    build()
    load_images_to_minikube()
    run_command("scripts/apply-k8s-secret.sh --deploy",
                "Applying secret and deploying Helm")
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
                 "smoke-test",
                 "obs-ui-start", "obs-ui-stop", "obs-ui-status",
                 "clean", "status"],
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "build":
        build()
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
