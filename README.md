# VisionRAG Platform

## Architecture Overview
VisionRAG is a microservices-based AI document intelligence platform.
The architecture uses **Go** for high-performance service orchestration and **Python** for AI workloads.

### Microservices
1.  **Gateway Service (Go)**: `GatewayServiceGo`
    *   **Role**: Unified API Entry Point & Identity Provider.
    *   **Responsibilities**:
        *   User Authentication (JWT).
        *   User Management (Register/Login).
        *   Request Rate Limiting.
        *   Reverse Proxy (Forwarding requests to ChatService).
    *   **Port**: 9000 (exposed)

2.  **Chat Service (Go)**: `ChatServiceGo`
    *   **Role**: Core Business Logic.
    *   **Responsibilities**:
        *   Session Management.
        *   Message History / Storage.
        *   Async Communication with AI Workers (RabbitMQ).
    *   **Port**: 9092 (internal)

3.  **AI Worker (Python)**: `AiWorkerPy`
    *   **Role**: AI Inference Engine.
    *   **Responsibilities**:
        *   RAG (Retrieval-Augmented Generation).
        *   LLM Interaction.
        *   Consumes tasks from RabbitMQ.

## Infrastructure
*   **PostgreSQL**: Persistent storage for Users and Chat History.
*   **Redis**: Caching, Rate Limiting, and Captcha storage.
*   **RabbitMQ**: Asynchronous message broker decoupling Chat Service and AI Worker.

## Getting Started

### 1. Start Infrastructure and Services
The entire stack is containerized. Run the following command in the root directory:

```bash
docker-compose up -d --build
```

### 2. Verify Services
*   **Gateway health/login entry**: `http://localhost:9000/api/v1/user/login`
*   **Chat service**: internal by default in compose (`chat-service:9092`)

## Kubernetes Secret Management

Use an external env file (not committed to Git) and apply it to Kubernetes Secret:

```bash
scripts/apply-k8s-secret.sh
```

Or apply and deploy in one step:

```bash
scripts/apply-k8s-secret.sh --deploy
```

Default secret name:

* `visionrag-platform-secrets`

Default env source file:

* `.secrets/visionrag.env`

## Local Smoke Test CLI

Run one command to validate:

* Kubernetes service port-forward (gateway/public/chat)
* App health and metrics (`/health`, `/metrics`)
* Internal dependency health (Redis, RabbitMQ, PostgreSQL)
* End-to-end auth and chat/session flow (captcha -> register -> login -> session/chat)

```bash
python3 manage.py smoke-test
```

Direct script usage (optional):

```bash
python3 scripts/local_smoke_cli.py --namespace default
python3 scripts/local_smoke_cli.py --namespace default --with-ai --model-type 4
```

## Local Ollama Model (Optional for Local Dev)

For local model testing, run:

```bash
python3 services/AiWorkerPy/ollama_local_worker.py "hello"
```

Environment variables:

* `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
* `OLLAMA_MODEL_NAME` (default: `qwen2.5:1.5b`)

In Chat service, set request `modelType` to `"4"` to use Ollama.

## Observability Status

Current state:

* Services expose `/metrics`.
* K8s services include `prometheus.io/scrape` annotations.
* Redis/Postgres/RabbitMQ metrics endpoints are enabled in chart templates.
* A prebuilt Grafana dashboard (`VisionRAG Overview`) is provisioned by Helm via ConfigMap in `monitoring` namespace.
* Helm-managed Prometheus alert rules are enabled via `PrometheusRule` (`visionrag-platform-alert-rules`).

### Alert Rules (Helm)

Default rule groups:

* Availability: service target down, infra target down, deployment unavailable.
* Stability: crash loop, restart burst, OOMKilled.
* Capacity: chat CPU high, app pod memory high.
* Middleware: Redis down, Postgres down, RabbitMQ queue backlog high and critical.

Tune thresholds in:

* `charts/visionrag-platform/values.yaml` -> `observability.prometheusRule.thresholds`

Quick checks:

```bash
kubectl -n default get prometheusrule
kubectl -n default get prometheusrule visionrag-platform-alert-rules -o yaml
```

Recommended next steps:

* Deploy `kube-prometheus-stack` (Prometheus + Grafana + Alertmanager).
* Add `ServiceMonitor`/`PodMonitor` resources in Helm chart.
* Add baseline alerts: pod restart spikes, 5xx rate, latency, queue depth, DB availability.

## Roadmap
- [ ] **Gateway**: Implement JWT Authentication & Rate Limiting (Token Bucket).
- [ ] **Gateway**: Implement Reverse Proxy logic to forward `/session` requests to Chat Service.
- [ ] **Chat**: Implement RabbitMQ Producer for chat messages.
- [ ] **AI Worker**: Implement Python consumer for RAG tasks.
