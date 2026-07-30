#!/usr/bin/env python3
import subprocess
import sys
import os
import shlex
from datetime import datetime

# 颜色定义
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

CHART_PATH = "charts/visionrag-platform"
MONITORING_STACK_VALUES_PATH = "monitoring/kube-prometheus-stack.values.yaml"
SERVICES = {
    "public": {"path": "services/PublicServiceGo", "image": "visionrag-public"},
    "chat": {"path": "services/ChatServiceGo", "image": "visionrag-chat"},
    "gateway": {"path": "services/GatewayServiceGo", "image": "visionrag-gateway"},
    "combined-shop": {"path": "services/CombinedShopServiceCs", "image": "visionrag-combined-shop"},
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


def abort_with_message(message):
    print(f"{RED}{message}{RESET}")
    sys.exit(1)


def resolve_values_file(environment, explicit_values_file):
    if explicit_values_file:
        if not os.path.exists(explicit_values_file):
            abort_with_message(
                f"Values file not found: {explicit_values_file}")
        return explicit_values_file

    env_values_file = f"{CHART_PATH}/values-{environment}.yaml"
    if os.path.exists(env_values_file):
        return env_values_file

    return f"{CHART_PATH}/values.yaml"


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
