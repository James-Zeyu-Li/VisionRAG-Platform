#!/usr/bin/env bash

# 全局 Docker Compose 一键关闭脚本

echo "========================================================"
echo "正在关闭 VisionRAG 前端、后端与 Ollama 服务..."
echo "========================================================"

# 1. 终止前端 PID
if [ -f .frontend.pid ]; then
  FRONTEND_PID=$(cat .frontend.pid)
  kill -9 $FRONTEND_PID 2>/dev/null
  rm -f .frontend.pid
fi

# 释放可能占用的端口
lsof -ti:8080 | xargs kill -9 2>/dev/null
lsof -ti:8081 | xargs kill -9 2>/dev/null

echo "前端服务 (8080) 已停止"

# 2. 关闭 Docker 后端微服务与中间件
echo "正在停止 Docker 后端微服务与数据库..."
docker-compose down

# 3. 关闭 Ollama 容器
if docker ps --format '{{.Names}}' | grep -qx "ollama"; then
  echo "正在停止 Ollama 本地 AI 容器..."
  docker stop ollama >/dev/null
  echo "Ollama AI 服务已停止"
fi

echo "========================================================"
echo "所有前后端服务、数据库及 Ollama 本地模型已全部安全关闭！"
echo "========================================================"
