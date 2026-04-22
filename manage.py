#!/usr/bin/env python3
import argparse
import os
import shlex
import scripts.lib.common as common
import scripts.engines.build_engine as build_engine
import scripts.engines.deploy_engine as deploy_engine
import scripts.engines.quality_check as quality_check
import scripts.tests.runner as test_runner


def verify(namespace, monitoring_namespace):
    print(f"{common.YELLOW}--- Verifying platform ---{common.RESET}")
    common.run_command(
        f"kubectl -n {shlex.quote(namespace)} get pods,svc", "Checking app pods/svc")
    common.run_command(
        f"kubectl -n {shlex.quote(monitoring_namespace)} get pods,svc", "Checking monitoring stack")
    test_runner.run_smoke_tests(namespace)


def main():
    parser = argparse.ArgumentParser(
        description="VisionRAG Platform Manager CLI")
    parser.add_argument("action", choices=[
        "init", "deploy", "rollback", "check", "update-secret", "build", "ollama",
        "test", "smoke-test", "alert-experiment", "benchmark", "verify",
        "obs-ui-start", "obs-ui-stop", "obs-ui-status", "clean", "status"
    ], help="Action to perform")

    parser.add_argument(
        "--namespace", default=os.getenv("VISIONRAG_NAMESPACE", "default"))
    parser.add_argument("--monitoring-namespace",
                        default=os.getenv("VISIONRAG_MONITORING_NAMESPACE", "monitoring"))
    parser.add_argument(
        "--release", default=os.getenv("VISIONRAG_RELEASE", "visionrag"))
    parser.add_argument(
        "--environment", choices=["dev", "staging", "prod"], default="dev")
    parser.add_argument("--values-file", default="")
    parser.add_argument("--helm-timeout", default="10m")
    parser.add_argument("--revision", type=int, default=0)
    parser.add_argument(
        "--test-level", choices=["unit", "smoke", "experiment", "all"], default="smoke")

    args = parser.parse_args()

    # Resolve global configs
    tag = common.resolve_image_tag()
    values_file = common.resolve_values_file(
        args.environment, args.values_file)

    if args.action == "build":
        build_engine.build(tag)
    elif args.action == "deploy":
        common.run_command("scripts/infra/ensure-ollama.sh", "Ensuring Ollama")
        build_engine.build(tag)
        build_engine.load_images_to_minikube(tag)
        deploy_engine.helm_upgrade_with_tag(
            args.release, args.namespace, values_file, tag, args.helm_timeout)
        deploy_engine.rollout_and_wait(args.namespace)
    elif args.action == "init":
        deploy_engine.ensure_monitoring_stack(
            args.monitoring_namespace, args.helm_timeout)
        common.run_command("scripts/infra/ensure-ollama.sh", "Ensuring Ollama")
        build_engine.build(tag)
        build_engine.load_images_to_minikube(tag)
        deploy_engine.update_secret(args.namespace)
        deploy_engine.helm_upgrade_with_tag(
            args.release, args.namespace, values_file, tag, args.helm_timeout)
        deploy_engine.rollout_and_wait(args.namespace)
        common.run_command(
            "scripts/infra/observability-ui.sh start", "Starting UI")
    elif args.action == "check":
        quality_check.check()
    elif args.action == "rollback":
        deploy_engine.rollback(args.release, args.namespace,
                               args.revision, args.helm_timeout)
    elif args.action == "update-secret":
        deploy_engine.update_secret(args.namespace)
    elif args.action == "test":
        test_runner.main_dispatch(args.test_level, args.namespace)
    elif args.action == "smoke-test":
        test_runner.run_smoke_tests(args.namespace)
    elif args.action == "alert-experiment":
        test_runner.run_experimental_tests(args.namespace)
    elif args.action == "benchmark":
        test_runner.run_experimental_tests(args.namespace)
    elif args.action == "verify":
        verify(args.namespace, args.monitoring_namespace)
    elif args.action == "clean":
        deploy_engine.clean(args.release, args.namespace)
    elif args.action == "status":
        common.run_command(
            f"kubectl -n {args.namespace} get pods,svc", "Status")
    elif args.action.startswith("obs-ui-"):
        cmd = args.action.split("-")[-1]
        common.run_command(
            f"scripts/infra/observability-ui.sh {cmd}", f"UI {cmd}")


if __name__ == "__main__":
    main()
