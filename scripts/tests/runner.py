#!/usr/bin/env python3
import argparse
import os
import shlex
import scripts.lib.common as common


def run_unit_tests():
    print(f"{common.YELLOW}--- Running Unit Tests (Go) ---{common.RESET}")
    for name, info in common.SERVICES.items():
        common.run_command(
            f"cd {info['path']} && go test ./...", f"Unit testing Go {name} service")
    common.run_command("cd shared && go test ./...",
                       "Unit testing Go shared module")
    print(f"{common.GREEN}Unit tests complete.{common.RESET}")


def run_smoke_tests(namespace):
    print(f"{common.YELLOW}--- Running Smoke Tests (API/Auth) ---{common.RESET}")
    common.run_command(
        f"python3 scripts/tests/local_smoke_cli.py --namespace {shlex.quote(namespace)}",
        "Running health/internal/auth/chat smoke tests",
    )


def run_experimental_tests(namespace):
    print(f"{common.YELLOW}--- Running Experimental/MTTD Tests ---{common.RESET}")
    common.run_command(
        f"python3 scripts/tests/alert_experiment.py --namespace {shlex.quote(namespace)}",
        "Injecting controlled failure and metrics collection",
    )
    common.run_command(
        f"python3 scripts/tests/ops_benchmark.py --namespace {shlex.quote(namespace)}",
        "Running benchmark and generating report",
    )


def run_all(namespace):
    run_unit_tests()
    run_smoke_tests(namespace)
    run_experimental_tests(namespace)


def main_dispatch(level, namespace):
    if level == "unit":
        run_unit_tests()
    elif level == "smoke":
        run_smoke_tests(namespace)
    elif level == "experiment":
        run_experimental_tests(namespace)
    elif level == "all":
        run_all(namespace)


def main():
    parser = argparse.ArgumentParser(
        description="VisionRAG Platform Unified Test Runner")
    parser.add_argument(
        "--level", choices=["unit", "smoke", "experiment", "all"], default="smoke")
    parser.add_argument("--namespace", default="default")
    args = parser.parse_args()
    main_dispatch(args.level, args.namespace)


if __name__ == "__main__":
    main()
