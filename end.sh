#!/usr/bin/env bash

# 根目录全局一键关闭脚本

echo "========================================================"
echo "🛑 正在关闭 VisionRAG 前端与后端服务..."
echo "========================================================"

# 1. 终止前端 PID
if [ -f .frontend.pid ]; then
  FRONTEND_PID=$(cat .frontend.pid)
  kill -9 $FRONTEND_PID 2>/dev/null
  rm -f .frontend.pid
fi

# 兼容释放可能占用的端口
lsof -ti:8080 | xargs kill -9 2>/dev/null
lsof -ti:8081 | xargs kill -9 2>/dev/null

echo "✅ 前端服务 (8080) 已停止"

# 2. 关闭 Docker 后端微服务与中间件
echo "🛑 正在停止 Docker 后端微服务与数据库..."
docker-compose down

echo "========================================================"
echo "🎉 所有前后端服务与数据库已全部安全关闭！"
echo "========================================================"
