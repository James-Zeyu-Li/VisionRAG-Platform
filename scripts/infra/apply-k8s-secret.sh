#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-default}"
SECRET_NAME="${SECRET_NAME:-visionrag-platform-secrets}"
ENV_FILE="${ENV_FILE:-.secrets/visionrag.env}"
RELEASE_NAME="${RELEASE_NAME:-visionrag}"
CHART_PATH="${CHART_PATH:-charts/visionrag-platform}"
VALUES_FILE="${VALUES_FILE:-}"
HELM_TIMEOUT="${HELM_TIMEOUT:-10m}"
DO_DEPLOY="false"

usage() {
  cat <<'USAGE'
Usage:
  scripts/apply-k8s-secret.sh [--deploy] [--namespace <ns>] [--secret-name <name>] [--env-file <path>] [--values-file <path>] [--helm-timeout <duration>]

Examples:
  scripts/apply-k8s-secret.sh
  scripts/apply-k8s-secret.sh --deploy
  scripts/apply-k8s-secret.sh --namespace dev --secret-name visionrag-platform-secrets --env-file .secrets/visionrag.env --values-file charts/visionrag-platform/values-dev.yaml
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deploy)
      DO_DEPLOY="true"
      shift
      ;;
    --namespace)
      NAMESPACE="${2:?missing namespace value}"
      shift 2
      ;;
    --secret-name)
      SECRET_NAME="${2:?missing secret-name value}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:?missing env-file value}"
      shift 2
      ;;
    --values-file)
      VALUES_FILE="${2:?missing values-file value}"
      shift 2
      ;;
    --helm-timeout)
      HELM_TIMEOUT="${2:?missing helm-timeout value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required but not found."
  exit 1
fi

if [[ "$DO_DEPLOY" == "true" ]] && ! command -v helm >/dev/null 2>&1; then
  echo "helm is required when using --deploy."
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Secret env file not found: $ENV_FILE"
  exit 1
fi

if [[ -n "$VALUES_FILE" ]] && [[ ! -f "$VALUES_FILE" ]]; then
  echo "Values file not found: $VALUES_FILE"
  exit 1
fi

if rg -n "CHANGE_ME" "$ENV_FILE" >/dev/null 2>&1; then
  echo "Found placeholder values in $ENV_FILE. Replace CHANGE_ME_* before applying."
  exit 1
fi

echo "Applying secret '$SECRET_NAME' in namespace '$NAMESPACE' from '$ENV_FILE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$NAMESPACE" create secret generic "$SECRET_NAME" \
  --from-env-file="$ENV_FILE" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secret applied successfully."

if [[ "$DO_DEPLOY" == "true" ]]; then
  echo "Running Helm upgrade/install..."
  VALUES_ARG=()
  if [[ -n "$VALUES_FILE" ]]; then
    VALUES_ARG=(-f "$VALUES_FILE")
  fi
  helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" -n "$NAMESPACE" --create-namespace \
    "${VALUES_ARG[@]}" --atomic --wait --timeout "$HELM_TIMEOUT"
  echo "Deployment updated."
else
  echo "Tip: run with --deploy to apply Helm after secret update."
fi
