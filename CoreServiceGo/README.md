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

### 1. Run Everything (Docker)
This is the easiest way to verify the entire stack, including the Go service.
```bash
docker-compose up --build -d
```

### 2. Run Infrastructure Only (Local Dev)
If you want to run the Go service locally (for debugging) but keep DBs in Docker:
```bash
# In the project root
docker-compose up -d mysql redis rabbitmq
# Then inside CoreServiceGo
cd CoreServiceGo
go run main.go
```

## Testing Rules (Postman / No JWT)

Since JWT authentication has been removed for this transition phase, you must manually identify the user when making API calls.

### 1. Register Flow
*   **Step 1: Send Captcha**
    *   **Method**: `POST`
    *   **URL**: `http://localhost:9090/api/v1/user/captcha`
    *   **Body**: `{"email": "your_email@example.com"}`
    *   **Note**: The code is sent to your email (if configured) or stored in Redis.
*   **Step 2: Register**
    *   **Method**: `POST`
    *   **URL**: `http://localhost:9090/api/v1/user/register`
    *   **Body**: `{"email": "your_email@example.com", "password": "yourpassword", "captcha": "THE_CODE_FROM_STEP_1"}`

### 2. Login Flow
*   **Method**: `POST`
    *   **URL**: `http://localhost:9090/api/v1/user/login`
    *   **Body**: `{"username": "ACCOUNT_ID_FROM_REGISTER", "password": "yourpassword"}`
    *   **Response**: You will receive a `token` field, but **ignore it**. It is a mock string. The important part is to get the `code: 1000` (success).

### 3. Session Flow (Authentication via Query Param)
Because there is no Token header parsing, you **MUST** append the `username` query parameter to let the backend know who is operating.

*   **Create Session**
    *   **Method**: `POST`
    *   **URL**: `http://localhost:9090/api/v1/session/create?username=ACCOUNT_ID`
    *   **Body**: `{"title": "My New Chat"}`

*   **Get Session List**
    *   **Method**: `GET`
    *   **URL**: `http://localhost:9090/api/v1/session/list?username=ACCOUNT_ID`

*   **Get History**
    *   **Method**: `POST`
    *   **URL**: `http://localhost:9090/api/v1/session/history?username=ACCOUNT_ID`
    *   **Body**: `{"sessionId": "SESSION_ID_FROM_LIST"}`
