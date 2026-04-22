#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-ollama}"
MODEL_NAME="${MODEL_NAME:-qwen2.5:1.5b}"
HOST_PORT="${HOST_PORT:-11434}"
PULL_MODEL="true"

usage() {
  cat <<'USAGE'
Usage:
  scripts/ensure-ollama.sh [--model <name>] [--container <name>] [--port <port>] [--no-pull]

Examples:
  scripts/ensure-ollama.sh
  scripts/ensure-ollama.sh --model llama3.1:8b
  scripts/ensure-ollama.sh --no-pull
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL_NAME="${2:?missing model value}"
      shift 2
      ;;
    --container)
      CONTAINER_NAME="${2:?missing container value}"
      shift 2
      ;;
    --port)
      HOST_PORT="${2:?missing port value}"
      shift 2
      ;;
    --no-pull)
      PULL_MODEL="false"
      shift
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

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but not found."
  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "Starting existing Ollama container: $CONTAINER_NAME"
    docker start "$CONTAINER_NAME" >/dev/null
  else
    echo "Ollama container is already running: $CONTAINER_NAME"
  fi
else
  echo "Creating Ollama container: $CONTAINER_NAME"
  docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "${HOST_PORT}:11434" \
    -v ollama-data:/root/.ollama \
    ollama/ollama >/dev/null
fi

echo "Waiting for Ollama API..."
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${HOST_PORT}/api/tags" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:${HOST_PORT}/api/tags" >/dev/null 2>&1; then
  echo "Ollama API is not ready on port ${HOST_PORT}."
  exit 1
fi

if [[ "$PULL_MODEL" == "true" ]]; then
  echo "Ensuring model exists: $MODEL_NAME"
  docker exec "$CONTAINER_NAME" ollama pull "$MODEL_NAME"
fi

echo "Ollama is ready at http://127.0.0.1:${HOST_PORT}"
echo "Set these env vars for services:"
echo "  OLLAMA_BASE_URL=http://127.0.0.1:${HOST_PORT}"
echo "  OLLAMA_MODEL_NAME=${MODEL_NAME}"
