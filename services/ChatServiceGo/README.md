# VisionRAG - Chat Service (Go)

## Role
This microservice is responsible for the **Core Domain** of the chat application:
- Managing Chat Sessions.
- Storing and retrieving Message History.
- Async communication with AI Workers (via RabbitMQ).

## API Endpoints (Port 9092)
- **Session List**: `GET /api/v1/session/list?username={username}`
- **Create Session**: `POST /api/v1/session/create?username={username}`
- **Get History**: `POST /api/v1/session/history?username={username}`

## Dependencies
- **MySQL**: Stores sessions and messages.
- **RabbitMQ**: Consumes AI task results (future) or publishes chat events.

## How to Run
```bash
cd ChatServiceGo
go run main.go
```
Or via Docker Compose in the root directory.