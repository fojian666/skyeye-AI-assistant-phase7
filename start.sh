#!/bin/bash

# ============================================
#  gtus 一键启动脚本（前后端）
# ============================================

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/skyeye"
FRONTEND_DIR="$ROOT_DIR/skyeye-ui"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 检查依赖
check_dep() {
    local name=$1 cmd=$2
    if ! command -v "$cmd" &>/dev/null; then
        echo -e "${RED}[错误] $name 未安装，请先安装${NC}"
        return 1
    fi
    echo -e "  ${GREEN}✓${NC} $name"
}

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  gtus 环境检查${NC}"
echo -e "${GREEN}============================================${NC}"

check_dep "Python3" python3 || exit 1
check_dep "Node.js" node || exit 1
check_dep "npm" npm || exit 1

# 检查 PostgreSQL
if pg_isready -q 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL"
else
    echo -e "  ${YELLOW}⚠${NC} PostgreSQL 未运行，请确保已启动"
fi

# 检查 Redis
if redis-cli ping &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Redis"
else
    echo -e "  ${YELLOW}⚠${NC} Redis 未运行，请确保已启动"
fi

# 检查 node_modules
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}前端依赖未安装，正在安装...${NC}"
    cd "$FRONTEND_DIR" && npm install
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  启动服务${NC}"
echo -e "${GREEN}============================================${NC}"

# 启动后端 (Daphne)
echo -e "${YELLOW}[1/2] 启动后端 (Daphne :8009)...${NC}"
cd "$BACKEND_DIR"
python3 -m daphne -b 0.0.0.0 -p 8009 gtus.asgi:application &
BACKEND_PID=$!
sleep 2

# 启动前端 (Vue)
echo -e "${YELLOW}[2/2] 启动前端 (Vue :8088)...${NC}"
cd "$FRONTEND_DIR"
npm run serve &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  服务已启动${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "  后端 API:  ${GREEN}http://localhost:8009/api/${NC}"
echo -e "  前端页面:  ${GREEN}http://localhost:8088/${NC}"
echo -e "  登录账号:  ${GREEN}admin / admin123${NC}"
echo -e ""
echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止所有服务"
echo -e "${GREEN}============================================${NC}"

wait
