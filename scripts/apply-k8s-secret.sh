#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-visionrag}"
SECRET_NAME="${SECRET_NAME:-visionrag-platform-secrets}"
ENV_FILE="${ENV_FILE:-.secrets/visionrag.env}"
RELEASE_NAME="${RELEASE_NAME:-visionrag}"
CHART_PATH="${CHART_PATH:-charts/visionrag-platform}"
DO_DEPLOY="false"

usage() {
  cat <<'USAGE'
Usage:
  scripts/apply-k8s-secret.sh [--deploy] [--namespace <ns>] [--secret-name <name>] [--env-file <path>]

Examples:
  scripts/apply-k8s-secret.sh
  scripts/apply-k8s-secret.sh --deploy
  scripts/apply-k8s-secret.sh --namespace dev --secret-name visionrag-platform-secrets --env-file .secrets/visionrag.env
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
  helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" -n "$NAMESPACE" --create-namespace
  echo "Deployment updated."
else
  echo "Tip: run with --deploy to apply Helm after secret update."
fi
