# 使用官方 Golang 镜像作为构建环境
FROM golang:1.23-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制 go.mod 和 go.sum 并下载依赖
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码
COPY . .

# 构建可执行文件
RUN go build -o server main.go

# 使用轻量级 Alpine 镜像作为运行环境
FROM alpine:latest

# 安装基础库（有些应用可能需要 libc）
RUN apk --no-cache add ca-certificates

WORKDIR /root/

# 从构建阶段复制二进制文件
COPY --from=builder /app/server .
# 复制配置文件 (确保配置文件也在容器里)
COPY --from=builder /app/config ./config

# 暴露端口
EXPOSE 9092

# 运行服务
CMD ["./server"]
