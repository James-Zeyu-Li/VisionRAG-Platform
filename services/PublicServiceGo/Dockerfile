# 使用官方 Golang 镜像作为构建环境
FROM golang:1.24-alpine AS builder

# 设置工作目录
WORKDIR /app

# 1. 复制 go.work 和所有相关的 go.mod
COPY go.work go.work.sum ./
COPY shared/go.mod shared/go.sum ./shared/
COPY services/PublicServiceGo/go.mod services/PublicServiceGo/go.sum ./services/PublicServiceGo/
COPY services/ChatServiceGo/go.mod services/ChatServiceGo/go.sum ./services/ChatServiceGo/
COPY services/GatewayServiceGo/go.mod services/GatewayServiceGo/go.sum ./services/GatewayServiceGo/

# 运行 go mod download (在根目录下)
RUN go mod download

# 2. 复制所有源代码
COPY shared/ ./shared/
COPY services/PublicServiceGo/ ./services/PublicServiceGo/

# 3. 编译指定的微服务
WORKDIR /app/services/PublicServiceGo
RUN go build -o server main.go

# --- 运行阶段 ---
FROM alpine:latest
RUN apk --no-cache add ca-certificates tzdata
WORKDIR /root/
COPY --from=builder /app/services/PublicServiceGo/server .
COPY --from=builder /app/services/PublicServiceGo/config ./config
EXPOSE 9091
CMD ["./server"]
