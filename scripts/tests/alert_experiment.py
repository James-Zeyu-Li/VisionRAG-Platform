#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def run_cmd(args, check=True):
    proc = subprocess.run(args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        cmd_text = " ".join(args)
        raise RuntimeError(
            f"command failed: {cmd_text}\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def prom_query(prom_url, expr):
    query = urllib.parse.quote(expr, safe="")
    url = f"{prom_url.rstrip('/')}/api/v1/query?query={query}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot query Prometheus at {url}: {exc}") from exc

    if payload.get("status") != "success":
        raise RuntimeError(f"Prometheus query failed: {payload}")
    return payload.get("data", {}).get("result", [])


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


def scale_deploy(namespace, deploy, replicas):
    run_cmd(
        [
            "kubectl",
            "-n",
            namespace,
            "scale",
            "deploy",
            deploy,
            f"--replicas={replicas}",
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


def query_firing_summary(prom_url, namespace, target_alert):
    target_expr = (
        f'ALERTS{{namespace="{namespace}",alertstate="firing",alertname="{target_alert}"}}'
    )
    total_expr = f'sum(ALERTS{{namespace="{namespace}",alertstate="firing"}}) or vector(0)'
    by_name_expr = (
        f'sum by (alertname) (ALERTS{{namespace="{namespace}",alertstate="firing"}})'
    )

    target_rows = prom_query(prom_url, target_expr)
    total_rows = prom_query(prom_url, total_expr)
    by_name_rows = prom_query(prom_url, by_name_expr)

    target_firing = 0.0
    for row in target_rows:
        target_firing += float(row["value"][1])

    total_firing = 0.0
    if total_rows:
        total_firing = float(total_rows[0]["value"][1])

    by_name = {}
    for row in by_name_rows:
        alert_name = row.get("metric", {}).get("alertname", "")
        if alert_name:
            by_name[alert_name] = float(row["value"][1])

    return target_firing, total_firing, by_name


def ensure_prometheus_ready(prom_url):
    ready_url = f"{prom_url.rstrip('/')}/-/ready"
    try:
        with urllib.request.urlopen(ready_url, timeout=5) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Prometheus not ready: HTTP {resp.status}")
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Prometheus is unreachable at {ready_url}. Run `python3 manage.py obs-ui-start` first."
        ) from exc


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fault-injection experiment for alert quality metrics: detects MTTD and collateral alert noise."
        )
    )
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--deployment", default="chat-service")
    parser.add_argument(
        "--fault-mode",
        choices=["scale-zero", "bad-image"],
        default="scale-zero",
        help="How to inject fault: scale deployment to zero replicas, or set invalid image to force unavailable replicas.",
    )
    parser.add_argument(
        "--container",
        default="",
        help="Container name for --fault-mode bad-image (default: same as --deployment).",
    )
    parser.add_argument(
        "--fault-image",
        default="invalid.local/visionrag/fault-injection:does-not-exist",
        help="Invalid image used for --fault-mode bad-image.",
    )
    parser.add_argument("--target-alert", default="VisionRAGServiceTargetDown")
    parser.add_argument("--prom-url", default="http://127.0.0.1:9090")
    parser.add_argument(
        "--inject-seconds",
        type=int,
        default=210,
        help="How long to keep deployment scaled to 0 before recovery.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=5,
        help="Prometheus polling interval.",
    )
    parser.add_argument(
        "--rollout-timeout-seconds",
        type=int,
        default=300,
        help="Timeout while waiting deployment rollout after restoration.",
    )
    parser.add_argument(
        "--report-dir",
        default="reports/alert-experiments",
        help="Where JSON report is written.",
    )
    args = parser.parse_args()

    ensure_prometheus_ready(args.prom_url)

    baseline_replicas = get_deploy_replicas(args.namespace, args.deployment)
    baseline_image = None
    container_name = args.container or args.deployment
    if args.fault_mode == "scale-zero":
        if baseline_replicas <= 0:
            raise RuntimeError(
                f"baseline replicas for {args.deployment} is {baseline_replicas}; cannot inject service-down fault"
            )
    else:
        baseline_image = get_container_image(
            args.namespace, args.deployment, container_name)

    started_at = time.time()
    started_at_iso = now_iso()
    detected_at = None
    restored = False
    samples = []

    print(
        f"[experiment] injecting fault mode={args.fault_mode} on deploy/{args.deployment} "
        f"in namespace={args.namespace} for {args.inject_seconds}s"
    )

    try:
        if args.fault_mode == "scale-zero":
            scale_deploy(args.namespace, args.deployment, 0)
        else:
            print(
                f"[experiment] setting image {container_name}={args.fault_image} "
                f"(baseline={baseline_image})"
            )
            set_deploy_image(
                args.namespace,
                args.deployment,
                container_name,
                args.fault_image,
            )

        deadline = started_at + args.inject_seconds
        while time.time() < deadline:
            poll_ts = time.time()
            target_firing, total_firing, by_name = query_firing_summary(
                args.prom_url, args.namespace, args.target_alert
            )

            samples.append(
                {
                    "ts": datetime.fromtimestamp(poll_ts, tz=timezone.utc).isoformat(),
                    "seconds_from_start": round(poll_ts - started_at, 3),
                    "target_alert_firing": target_firing,
                    "total_firing_alerts": total_firing,
                    "firing_by_alert": by_name,
                }
            )

            if detected_at is None and target_firing > 0:
                detected_at = poll_ts
                print(
                    f"[experiment] target alert {args.target_alert} detected at "
                    f"{poll_ts - started_at:.1f}s"
                )

            time.sleep(args.poll_seconds)
    finally:
        if args.fault_mode == "scale-zero":
            print(
                f"[experiment] restoring deploy/{args.deployment} replicas to {baseline_replicas}"
            )
            scale_deploy(args.namespace, args.deployment, baseline_replicas)
        else:
            print(
                f"[experiment] restoring image {container_name}={baseline_image} "
                f"for deploy/{args.deployment}"
            )
            set_deploy_image(
                args.namespace,
                args.deployment,
                container_name,
                baseline_image,
            )
        wait_rollout(args.namespace, args.deployment,
                     args.rollout_timeout_seconds)
        restored = True

    ended_at = time.time()
    max_total_firing = max((s["total_firing_alerts"]
                           for s in samples), default=0.0)

    collateral_alerts = set()
    for sample in samples:
        for alert_name, value in sample["firing_by_alert"].items():
            if alert_name != args.target_alert and value > 0:
                collateral_alerts.add(alert_name)

    report = {
        "experiment": {
            "namespace": args.namespace,
            "deployment": args.deployment,
            "fault_mode": args.fault_mode,
            "container": container_name if args.fault_mode == "bad-image" else None,
            "fault_image": args.fault_image if args.fault_mode == "bad-image" else None,
            "target_alert": args.target_alert,
            "prom_url": args.prom_url,
            "inject_seconds": args.inject_seconds,
            "poll_seconds": args.poll_seconds,
        },
        "timeline": {
            "started_at": started_at_iso,
            "ended_at": datetime.fromtimestamp(ended_at, tz=timezone.utc).isoformat(),
            "detected_at": (
                datetime.fromtimestamp(
                    detected_at, tz=timezone.utc).isoformat()
                if detected_at
                else None
            ),
        },
        "result": {
            "target_alert_detected": detected_at is not None,
            "mttd_seconds": round(detected_at - started_at, 3) if detected_at else None,
            "max_total_firing_alerts": max_total_firing,
            "collateral_alert_count": len(collateral_alerts),
            "collateral_alert_names": sorted(collateral_alerts),
            "deployment_restored": restored,
        },
        "samples": samples,
    }

    os.makedirs(args.report_dir, exist_ok=True)
    filename = datetime.now(timezone.utc).strftime(
        "alert-experiment-%Y%m%dT%H%M%SZ.json")
    report_path = os.path.join(args.report_dir, filename)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("[experiment] completed")
    print(f"[experiment] report: {report_path}")
    print(
        json.dumps(
            {
                "target_alert_detected": report["result"]["target_alert_detected"],
                "mttd_seconds": report["result"]["mttd_seconds"],
                "collateral_alert_count": report["result"]["collateral_alert_count"],
                "collateral_alert_names": report["result"]["collateral_alert_names"],
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
