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
    *   **Port**: 9091

2.  **Chat Service (Go)**: `ChatServiceGo`
    *   **Role**: Core Business Logic.
    *   **Responsibilities**:
        *   Session Management.
        *   Message History / Storage.
        *   Async Communication with AI Workers (RabbitMQ).
    *   **Port**: 9092

3.  **AI Worker (Python)**: `AiWorkerPy`
    *   **Role**: AI Inference Engine.
    *   **Responsibilities**:
        *   RAG (Retrieval-Augmented Generation).
        *   LLM Interaction.
        *   Consumes tasks from RabbitMQ.

## Infrastructure
*   **MySQL**: Persistent storage for Users and Chat History.
*   **Redis**: Caching, Rate Limiting, and Captcha storage.
*   **RabbitMQ**: Asynchronous message broker decoupling Chat Service and AI Worker.

## Getting Started

### 1. Start Infrastructure & Services
The entire stack is containerized. Run the following command in the root directory:

```bash
docker-compose up -d --build
```

### 2. Verify Services
*   **Gateway**: `http://localhost:9091/api/v1/user/login`
*   **Chat**: `http://localhost:9092/api/v1/session/list` (Internal Access)

## Roadmap
- [ ] **Gateway**: Implement JWT Authentication & Rate Limiting (Token Bucket).
- [ ] **Gateway**: Implement Reverse Proxy logic to forward `/session` requests to Chat Service.
- [ ] **Chat**: Implement RabbitMQ Producer for chat messages.
- [ ] **AI Worker**: Implement Python consumer for RAG tasks.
