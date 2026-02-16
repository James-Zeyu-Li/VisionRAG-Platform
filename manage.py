#!/usr/bin/env python3
import subprocess
import sys
import os
import argparse

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
    "gateway": {"path": "services/GatewayServiceGo", "image": "visionrag-gateway"}
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


def deploy():
    print(f"{YELLOW}--- Deploying with Helm ---{RESET}")
    # 检查 Helm 是否安装
    run_command(
        f"helm upgrade --install visionrag {CHART_PATH}", "Helm upgrade/install")
    print(f"\n{GREEN}System deployed via Helm!{RESET}")
    print(f"Check status with: {BLUE}kubectl get pods{RESET}")


def format_code():
    print(f"{YELLOW}--- Formatting Codebase ---{RESET}")
    # 格式化 YAML 和 TPL 文件
    run_command(
        "prettier --write 'charts/**/*.{yaml,tpl}'", "Formatting Helm Charts")
    # 格式化 Python 文件 (如果安装了 black)
    if subprocess.run("which black", shell=True, capture_output=True).returncode == 0:
        run_command("black manage.py", "Formatting Python script")
    else:
        print(f"{BLUE}  Skip Python formatting (black not found){RESET}")


def lint():
    print(f"{YELLOW}--- Linting Helm Charts ---{RESET}")
    run_command(f"helm lint {CHART_PATH}", "Helm linting")


def clean():
    print(f"{RED}--- Cleaning Helm Release ---{RESET}")
    run_command("helm uninstall visionrag", "Uninstalling Helm release")


def main():
    parser = argparse.ArgumentParser(description="VisionRAG Platform Manager")
    parser.add_argument("action", choices=["build", "deploy", "up", "clean", "status", "fmt", "lint"],
                        help="Action to perform")

    args = parser.parse_args()

    if args.action == "fmt":
        format_code()
    elif args.action == "lint":
        lint()
    elif args.action == "build":
        build()
    elif args.action == "deploy":
        lint()
        deploy()
    elif args.action == "up":
        build()
        lint()
        deploy()
    elif args.action == "clean":
        clean()
    elif args.action == "status":
        run_command("kubectl get pods,svc", "Cluster Status")


if __name__ == "__main__":
    main()
