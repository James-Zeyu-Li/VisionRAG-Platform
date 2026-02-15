# 使用官方 Golang 镜像作为构建环境
FROM golang:1.24-alpine AS builder

# 设置工作目录
WORKDIR /app

# 1. 复制 go.work 和所有相关的 go.mod
COPY go.work go.work.sum ./
COPY pkg/go.mod pkg/go.sum ./pkg/
COPY PublicServiceGo/go.mod PublicServiceGo/go.sum ./PublicServiceGo/
COPY ChatServiceGo/go.mod ChatServiceGo/go.sum ./ChatServiceGo/
COPY GatewayServiceGo/go.mod GatewayServiceGo/go.sum ./GatewayServiceGo/

# 运行 go mod download (在根目录下)
RUN go mod download

# 2. 复制所有源代码
COPY pkg/ ./pkg/
COPY ChatServiceGo/ ./ChatServiceGo/

# 3. 编译指定的微服务
WORKDIR /app/ChatServiceGo
RUN go build -o server main.go

# --- 运行阶段 ---
FROM alpine:latest
RUN apk --no-cache add ca-certificates tzdata
WORKDIR /root/
COPY --from=builder /app/ChatServiceGo/server .
COPY --from=builder /app/ChatServiceGo/config ./config
EXPOSE 9092
CMD ["./server"]
