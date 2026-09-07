#!/bin/bash
set -eu

# Finder 启动时也能找到 Homebrew 安装的 Node.js。
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR/web"
mkdir -p "$PROJECT_DIR/output"
LOG_FILE="$PROJECT_DIR/output/local-server.log"

fail() {
  echo "启动失败：$1"
  echo "日志：$LOG_FILE"
  read -r -p "按回车关闭…" _unused
  exit 1
}

command -v npm >/dev/null 2>&1 || fail "未找到 Node.js / npm。"
[ -d node_modules ] || fail "缺少依赖，请在 web 目录运行 npm install。"
[ -f public/campus.glb ] || fail "未找到校园模型 campus.glb。"

# 重用已运行的校园页面；其他程序占用端口时选择下一个端口。
for PORT in {5173..5183}; do
  URL="http://localhost:$PORT/"
  if curl -fsS --max-time 3 "$URL" 2>/dev/null | grep -q '校园空间重现'; then
    echo "校园网页已经运行，正在打开 $URL"
    open "$URL"
    exit 0
  fi
  if ! lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    break
  fi
  [ "$PORT" != 5183 ] || fail "5173–5183 端口均被占用。"
done

echo "正在启动校园网页，首次加载可能需要约半分钟…"
nohup npm run dev -- --host 127.0.0.1 --port "$PORT" > "$LOG_FILE" 2>&1 < /dev/null &
SERVER_PID=$!
for ((i=0; i<90; i++)); do
  if curl -fsS --max-time 2 "$URL" 2>/dev/null | grep -q '校园空间重现'; then
    echo "校园网页已启动：$URL"
    echo "服务在后台运行，可以关闭此窗口。"
    open "$URL"
    exit 0
  fi
  kill -0 "$SERVER_PID" 2>/dev/null || fail "本地服务已退出，请查看日志。"
  sleep 1
done
fail "等待服务超时，请查看日志。"
