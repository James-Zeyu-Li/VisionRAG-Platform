# VisionRAG - Core Service (Go Transition)

## Goal
The **VisionRAG** platform is a microservices-based AI system designed for document intelligence. This repository is currently undergoing a strategic refactor:
- **Go**: Serves as the stable infrastructure bridge for User/Session management.
- **C#**: Future core for high-performance business logic, Rate Limiting, and Virtual Waiting Rooms.
- **Python**: Dedicated AI Worker for RAG (Retrieval-Augmented Generation) and LLM orchestration.

## Current Project Status
- **Backend Functional**: Core logic for user registration, authentication, and session management is implemented and connected to infrastructure.
- **Infrastructure Ready**: Fully configured for Docker-based MySQL, Redis, and RabbitMQ.
- **JWT Removed**: The internal JWT middleware has been stripped to facilitate a clean transition to the C# Gateway's security layer.
- **Frontend Disconnected**: The UI is currently not integrated with this simplified backend version.

## Accomplishments
- [x] **Service Scaffolding**: Modular directory structure (Controller, Service, DAO, Helper).
- [x] **Infrastructure Integration**: Established robust connections for persistent storage (MySQL), caching (Redis), and messaging (RabbitMQ).
- [x] **User & Session Core**: Implemented the fundamental lifecycle of users and chat sessions.
- [x] **Dependency Cleanup**: Removed legacy monolithic AI code to prepare for the Python microservice migration.

## Major Roadmap (TODO)
- [ ] **C# Gateway Implementation**: Build the primary entry point with Rate Limiting and Virtual Waiting Room logic.
- [ ] **Python AI Worker**: Implement the RabbitMQ consumer for AI task processing and RAG.
- [ ] **Security Layer**: Re-implement unified authentication (JWT/OAuth2) within the C# Gateway.
- [ ] **Frontend Integration**: Reconnect the React Web interface to the new microservice endpoints.

## Getting Started
1. **Infrastructure**: Run `docker-compose up -d` in the `/Infra` directory.
2. **Launch**: Run `go run main.go` in `/CoreServiceGo`.
3. **Verify**: Use the provided `test_endpoints.sh` to confirm database and messaging connectivity.