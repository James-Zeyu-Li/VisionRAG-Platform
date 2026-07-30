#!/usr/bin/env bash

# 根目录全局一键启动脚本

echo "========================================================"
echo "🚀 正在启动 VisionRAG 后端微服务与数据库 (Docker)..."
echo "========================================================"
docker-compose up -d

echo ""
echo "⚛️  正在启动 React 19 + MUI 前端开发服务器 (Port: 8080)..."
(cd frontend && npm run dev) > /dev/null 2>&1 &
FRONTEND_PID=$!

echo "$FRONTEND_PID" > .frontend.pid

echo ""
echo "========================================================"
echo "✨ 所有服务已成功启动！"
echo "========================================================"
echo "💻 前端应用访问链接:      http://localhost:8080"
echo "🔌 Go 网关 API 接口地址:    http://localhost:9090"
echo "🐰 RabbitMQ 管理控制台:     http://localhost:15673"
echo "========================================================"
echo "💡 提示：如需一键停止所有服务，请运行: ./end.sh"
echo "========================================================"

wait
