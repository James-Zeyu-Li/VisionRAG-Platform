#!/usr/bin/env bash

# 根目录全局交互式可选择控制脚本

show_menu() {
  echo "========================================================"
  echo "         VisionRAG Platform Management CLI              "
  echo "========================================================"
  echo "  [1] Start Docker Services (Backend + React 19 + Ollama)"
  echo "  [2] Stop Docker Services (All Containers & Frontend)"
  echo "  [3] Deploy to Kubernetes / Minikube"
  echo "  [4] Run Local Smoke Tests"
  echo "  [5] Run Alert MTTD Experiment"
  echo "  [6] Exit"
  echo "========================================================"
}

run_option() {
  case "$1" in
    1|start)
      ./scripts/docker-start.sh
      ;;
    2|stop|end)
      ./scripts/docker-end.sh
      ;;
    3|deploy|k8s)
      python3 manage.py deploy
      ;;
    4|smoke|test)
      python3 manage.py smoke-test
      ;;
    5|alert|mttd)
      python3 manage.py alert-experiment --namespace default
      ;;
    6|exit|q)
      echo "Exiting..."
      exit 0
      ;;
    *)
      echo "Invalid option. Please choose [1-6]."
      ;;
  esac
}

# 支持直接传参 (例如: ./start.sh 1 或 ./start.sh stop)
if [ -n "$1" ]; then
  run_option "$1"
  exit 0
fi

# 无参数时进入交互式菜单选择
while true; do
  show_menu
  read -p "Please select an option [1-6]: " choice
  echo ""
  run_option "$choice"
  echo ""
done
