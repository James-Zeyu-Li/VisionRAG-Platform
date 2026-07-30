# VisionRAG Platform

VisionRAG is a microservices-based AI document intelligence and streaming RAG platform.

> **Frontend Upgrade Note**: The frontend has been fully migrated and upgraded from **Vue 3** to a modern **React 19 + Material UI (MUI)** architecture built with **Vite**, maintaining 100% functional parity with zero backend changes.

---

## Architecture Overview

The platform uses **React 19** for the client layer, **Go** for high-performance service orchestration and streaming, and **Python** for AI workloads (RAG / ONNX inference).

```
 ┌─────────────────────────────────────────────────────────────┐
 │                  React 19 + MUI Frontend                    │
 │                  (Vite SPA, Port: 8080)                     │
 └──────────────────────────────┬──────────────────────────────┘
                                │ HTTP / SSE Stream
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                     Gateway Service (Go)                    │
 │               (Unified Gateway, Port: 9090)                 │
 └──────────────────────────────┬──────────────────────────────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
┌──────────────────┐                         ┌──────────────────┐
│  Public Service  │                         │   Chat Service   │
│     (Go API)     │                         │ (Go Stream / RAG)│
└────────┬─────────┘                         └────────┬─────────┘
         │                                            │
         ├──────────────────────┬─────────────────────┤
         ▼                      ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  PostgreSQL 16   │  │    Redis 6.2     │  │   RabbitMQ 3.9   │
│  (DB, Port 5433) │  │(Cache/Vector:6380│  │(Broker,Port15673)│
└──────────────────┘  └──────────────────┘  └────────┬─────────┘
                                                      │ Async Tasks
                                                      ▼
                                            ┌──────────────────┐
                                            │ AI Worker (Py)   │
                                            │(ONNX / Ollama)   │
                                            └──────────────────┘
```

### Microservices
1. **Frontend App (`frontend`)**:
   * **Tech Stack**: React 19, Material UI (MUI), React Router 7, Vite.
   * **Features**: SSE typewriter stream rendering, multi-model selection (Bailian LLM, RAG, Ollama), Markdown rendering, document upload (.md/.txt), TTS playback, ONNX image classification.
   * **Port**: `http://localhost:8080`

2. **Gateway Service (`GatewayServiceGo`)**:
   * **Role**: Unified API Entry Point & Identity Provider.
   * **Responsibilities**: User Authentication (JWT), Reverse Proxy, Rate Limiting.
   * **Port**: `http://localhost:9090` (exposed)

3. **Public Service (`PublicServiceGo`)**:
   * **Role**: Identity & User Management.
   * **Responsibilities**: Register, Login, Captcha, DB persistence, publishing user events to RabbitMQ.

4. **Chat Service (`ChatServiceGo`)**:
   * **Role**: Core Business Logic & Streaming RAG.
   * **Responsibilities**: Session Management, History Storage, Eino RAG pipeline, Redis Vector Search, HTTP SSE Stream Flushers.

5. **AI Worker (`AiWorkerPy`)**:
   * **Role**: AI Inference Engine.
   * **Responsibilities**: ONNX image classification, Ollama LLM integration, consuming tasks asynchronously from RabbitMQ.

---

## Getting Started

### 1. One-Command Start (Recommended)
Run the automated launcher script at the root directory:

```bash
./start.sh
```

This will automatically:
- Spin up all backend microservices, PostgreSQL, Redis, and RabbitMQ via Docker.
- Start the React 19 frontend development server on `http://localhost:8080`.

### 2. Verify Services & Access Links
- **React 19 Frontend App**: [http://localhost:8080](http://localhost:8080)
- **Go Gateway API**: [http://localhost:9090](http://localhost:9090)
- **RabbitMQ Dashboard**: [http://localhost:15673](http://localhost:15673) (User: `guest`, Pass: `guest`)

### 3. One-Command Shutdown
To safely stop all frontend processes and Docker containers:

```bash
./end.sh
```

---

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

---

## Helm Environment Profiles

This chart supports both in-cluster infrastructure and external managed services.

* `charts/visionrag-platform/values-local.yaml`: use in-cluster PostgreSQL, Redis, RabbitMQ.
* `charts/visionrag-platform/values-gcp.yaml`: disable in-cluster infra and use external hosts.

Deploy with a profile:

```bash
# Local/Minikube (default behavior)
helm upgrade --install visionrag charts/visionrag-platform -n default -f charts/visionrag-platform/values-local.yaml

# GCP/external infra
helm upgrade --install visionrag charts/visionrag-platform -n default -f charts/visionrag-platform/values-gcp.yaml
```

---

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

---

## Alert Experiment (MTTD + Noise)

Run a controlled fault-injection experiment to generate measurable alert quality data:

```bash
# 1) Ensure Prometheus/Grafana local port-forward
python3 manage.py obs-ui-start

# 2) Inject service-down fault and collect report
python3 manage.py alert-experiment --namespace default
```

What this does:
* Scales one deployment (default: `chat-service`) down to `0` for a short window.
* Polls Prometheus for a target alert (default: `VisionRAGServiceTargetDown`).
* Computes `MTTD` (fault start -> first firing detection).
* Captures collateral firing alerts as a practical noise indicator.
* Restores deployment replicas and waits for rollout completion.
* Writes a JSON report to `reports/alert-experiments/`.

Direct script usage (optional):

```bash
python3 scripts/alert_experiment.py --namespace default
python3 scripts/alert_experiment.py --namespace default --deployment public-service --target-alert VisionRAGServiceTargetDown --inject-seconds 240
```

---

## Ops Benchmark (Percentage-Based)

Run an A/B benchmark to compute percentage improvement for failure detection:

```bash
python3 manage.py benchmark --namespace default
```

What this does:
* Path A (alert-driven): runs fault injection and measures alert `MTTD`.
* Path B (manual baseline): runs the same fault injection and measures detection time with manual polling cadence.
* Outputs `mttd_improvement_percent` using:
  * `(manual_mttd - alert_mttd) / manual_mttd * 100`
* Writes JSON report to `reports/benchmarks/`.

Direct script usage (optional):

```bash
python3 scripts/ops_benchmark.py --namespace default --manual-poll-seconds 300
```

---

## Local Ollama Model (Optional for Local Dev)

For local model testing, run:

```bash
python3 services/AiWorkerPy/ollama_local_worker.py "hello"
```

Environment variables:
* `OLLAMA_BASE_URL` (default: `http://127.0.0.1:11434`)
* `OLLAMA_MODEL_NAME` (default: `qwen2.5:1.5b`)

In Chat service or Frontend UI, set request `modelType` to `"4"` to use Ollama.

---

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
* Capacity: CPU request utilization, CPU limit utilization, CPU throttling, memory limit utilization (app + infra).
* Middleware: Redis down, Postgres down, RabbitMQ queue backlog high and critical.

Tune thresholds in:
* `charts/visionrag-platform/values.yaml` -> `observability.prometheusRule.thresholds`
