#!/usr/bin/env python3
import os
import shlex
import subprocess
import json
from scripts.lib.common import (
    CHART_PATH, MONITORING_STACK_VALUES_PATH, SERVICES,
    YELLOW, GREEN, BLUE, RED, RESET,
    run_command, run_command_soft, abort_with_message
)

def ensure_monitoring_stack(monitoring_namespace, helm_timeout):
    print(f"{YELLOW}--- Ensuring monitoring stack (CRDs + Prometheus/Grafana) ---{RESET}")
    run_command(
        "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true",
        "Adding prometheus-community Helm repo",
    )
    run_command("helm repo update", "Updating Helm repos")
    values_arg = ""
    if os.path.exists(MONITORING_STACK_VALUES_PATH):
        values_arg = f"-f {shlex.quote(MONITORING_STACK_VALUES_PATH)} "
    run_command(
        "helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack "
        f"-n {shlex.quote(monitoring_namespace)} --create-namespace "
        f"{values_arg}"
        f"--atomic --wait --timeout {shlex.quote(helm_timeout)}",
        "Installing/upgrading kube-prometheus-stack",
    )

def rollout_and_wait(namespace):
    run_command(
        f"kubectl -n {shlex.quote(namespace)} rollout restart deploy/chat-service deploy/public-service deploy/gateway-service",
        f"Restarting application deployments in {namespace}",
    )
    for service in ["chat-service", "public-service", "gateway-service"]:
        run_command(
            f"kubectl -n {shlex.quote(namespace)} rollout status deploy/{service} --timeout=240s",
            f"Waiting for {service} to become Ready",
        )

def helm_upgrade_with_tag(release_name, namespace, values_file, tag, helm_timeout):
    run_command(
        f"helm upgrade --install {shlex.quote(release_name)} {shlex.quote(CHART_PATH)} "
        f"-n {shlex.quote(namespace)} --create-namespace "
        f"-f {shlex.quote(values_file)} "
        f"--set-string microservices.public.tag={shlex.quote(tag)} "
        f"--set-string microservices.chat.tag={shlex.quote(tag)} "
        f"--set-string microservices.gateway.tag={shlex.quote(tag)} "
        f"--atomic --wait --timeout {shlex.quote(helm_timeout)}",
        f"Helm upgrade/install (release={release_name}, tag={tag})",
    )

def rollback(release_name, namespace, revision, helm_timeout):
    target_revision = revision
    if not target_revision:
        cmd = f"helm history {shlex.quote(release_name)} -n {shlex.quote(namespace)} -o json"
        history = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if history.returncode != 0:
            abort_with_message("Unable to query Helm history.")
        entries = json.loads(history.stdout)
        if len(entries) < 2:
            abort_with_message("No previous release revision found.")
        target_revision = int(entries[-2]["revision"])
    
    run_command(
        f"helm rollback {shlex.quote(release_name)} {target_revision} "
        f"-n {shlex.quote(namespace)} --wait --timeout {shlex.quote(helm_timeout)}",
        f"Rolling back release {release_name} to revision {target_revision}",
    )
    rollout_and_wait(namespace)

def clean(release_name, namespace):
    print(f"{RED}--- Cleaning Helm Release ---{RESET}")
    run_command("scripts/infra/observability-ui.sh stop", "Stopping observability UIs")
    run_command(
        f"helm uninstall {shlex.quote(release_name)} -n {shlex.quote(namespace)}",
        f"Uninstalling Helm release {release_name}",
    )

def update_secret(namespace):
    print(f"{YELLOW}--- Updating Kubernetes secret ---{RESET}")
    run_command(
        f"scripts/infra/apply-k8s-secret.sh --namespace {shlex.quote(namespace)} --secret-name visionrag-platform-secrets",
        f"Applying secrets in {namespace}",
    )
    run_command(
        f"kubectl -n {shlex.quote(namespace)} rollout restart deploy/chat-service deploy/public-service deploy/gateway-service deploy/postgres-db deploy/redis deploy/rabbitmq",
        "Restarting deployments that depend on secrets",
    )
