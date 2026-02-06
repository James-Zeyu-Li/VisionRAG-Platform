# VisionRAG - Gateway Service (Go)

## Role
This microservice acts as the **Gateway and Authentication Provider**:
- **User Management**: Registration, Login, Captcha.
- **Authentication**: (Future) JWT issuance and validation.
- **Gateway**: (Future) Reverse proxy to ChatService.

**Note**: This service is a placeholder/reference implementation. It is intended to be replaced by a C# (.NET 8) Gateway to leverage advanced Rate Limiting and Governance features.

## API Endpoints (Port 9091)
- **Register**: `POST /api/v1/user/register`
- **Login**: `POST /api/v1/user/login`
- **Captcha**: `POST /api/v1/user/captcha`

## Dependencies
- **MySQL**: Stores user data.
- **Redis**: Stores captcha codes and (future) rate limiting counters.

## How to Run
```bash
cd GatewayServiceGo
go run main.go
```
Or via Docker Compose in the root directory.