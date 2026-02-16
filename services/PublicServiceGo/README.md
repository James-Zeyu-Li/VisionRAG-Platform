# VisionRAG - Public Service (Go)

## Role
This microservice acts as the **Public and Authentication Provider**:
- **User Management**: Registration, Login, Captcha.
- **Authentication**: JWT issuance and validation.

## API Endpoints (Port 9091)
- **Register**: `POST /api/v1/user/register`
- **Login**: `POST /api/v1/user/login`
- **Captcha**: `POST /api/v1/user/captcha`

## Dependencies
- **MySQL**: Stores user data.
- **Redis**: Stores captcha codes.

## How to Run
```bash
cd PublicServiceGo
go run main.go
```
Or via Docker Compose in the root directory.
