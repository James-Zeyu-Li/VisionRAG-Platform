# Local Ollama Worker (Python)

This is a minimal local worker for testing model connectivity against Ollama.

## Prerequisites

- Ollama is installed and running locally
- A model has been pulled, for example:

```bash
ollama pull qwen2.5:7b
```

## Usage

```bash
cd /Users/james/Desktop/1.2-CS/00-projects/VisionRAG-Platform
python3 services/AiWorkerPy/ollama_local_worker.py "Summarize VisionRAG architecture in 3 bullets"
```

Optional env vars:

- `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL_NAME` (or `OLLAMA_MODEL`, default: `qwen2.5:7b`)
- `OLLAMA_TIMEOUT_SECONDS` (default: `120`)

Example:

```bash
export OLLAMA_MODEL_NAME=llama3.1:8b
python3 services/AiWorkerPy/ollama_local_worker.py "hello"
```
