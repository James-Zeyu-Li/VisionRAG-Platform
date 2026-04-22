#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-start}"
NS="${NS:-monitoring}"
PROM_SVC="${PROM_SVC:-kube-prometheus-stack-prometheus}"
GRAFANA_SVC="${GRAFANA_SVC:-kube-prometheus-stack-grafana}"
PROM_PORT_LOCAL="${PROM_PORT_LOCAL:-9090}"
GRAFANA_PORT_LOCAL="${GRAFANA_PORT_LOCAL:-3000}"
PID_DIR="${PID_DIR:-/tmp/visionrag-observability}"
PROM_PID_FILE="${PID_DIR}/prometheus-port-forward.pid"
GRAFANA_PID_FILE="${PID_DIR}/grafana-port-forward.pid"
PROM_LOG="${PID_DIR}/prometheus-port-forward.log"
GRAFANA_LOG="${PID_DIR}/grafana-port-forward.log"

mkdir -p "$PID_DIR"

start_pf() {
  local name="$1"
  local pid_file="$2"
  local log_file="$3"
  shift 3
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" >/dev/null 2>&1; then
    echo "$name port-forward already running (pid $(cat "$pid_file"))."
    return
  fi
  kubectl "$@" >"$log_file" 2>&1 &
  echo $! > "$pid_file"
  sleep 1
  if ! kill -0 "$(cat "$pid_file")" >/dev/null 2>&1; then
    echo "Failed to start $name port-forward. Log: $log_file"
    tail -n 20 "$log_file" || true
    exit 1
  fi
  echo "Started $name port-forward (pid $(cat "$pid_file"))."
}

stop_pf() {
  local name="$1"
  local pid_file="$2"
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" >/dev/null 2>&1; then
    kill "$(cat "$pid_file")" >/dev/null 2>&1 || true
    rm -f "$pid_file"
    echo "Stopped $name port-forward."
  else
    rm -f "$pid_file"
    echo "$name port-forward not running."
  fi
}

status_pf() {
  local name="$1"
  local pid_file="$2"
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" >/dev/null 2>&1; then
    echo "$name: running (pid $(cat "$pid_file"))"
  else
    echo "$name: stopped"
  fi
}

case "$ACTION" in
  start)
    start_pf "Prometheus" "$PROM_PID_FILE" "$PROM_LOG" -n "$NS" port-forward "svc/${PROM_SVC}" "${PROM_PORT_LOCAL}:9090"
    start_pf "Grafana" "$GRAFANA_PID_FILE" "$GRAFANA_LOG" -n "$NS" port-forward "svc/${GRAFANA_SVC}" "${GRAFANA_PORT_LOCAL}:80"
    echo "Prometheus: http://127.0.0.1:${PROM_PORT_LOCAL}"
    echo "Grafana:    http://127.0.0.1:${GRAFANA_PORT_LOCAL}"
    ;;
  stop)
    stop_pf "Prometheus" "$PROM_PID_FILE"
    stop_pf "Grafana" "$GRAFANA_PID_FILE"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    status_pf "Prometheus" "$PROM_PID_FILE"
    status_pf "Grafana" "$GRAFANA_PID_FILE"
    ;;
  *)
    echo "Usage: scripts/observability-ui.sh [start|stop|restart|status]"
    exit 1
    ;;
esac
