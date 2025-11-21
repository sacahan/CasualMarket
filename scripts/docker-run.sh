#!/bin/bash

# ============================================
# CasualMarket MCP Server Docker 執行腳本
# ============================================
# 用法：./docker-run.sh [command] [options]
#
# 命令：
#   pull        - 從 Docker Hub 拉取鏡像
#   up          - 啟動容器（後台）
#   down        - 停止並移除容器
#   restart     - 重啟容器
#   logs        - 查看容器日誌
#   shell       - 進入容器 shell
#   test        - 測試服務端點
#   info        - 顯示服務信息
#   clean       - 清理所有 Docker 資源
#   help        - 顯示幫助信息
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案根目錄
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 預設環境文件
ENV_FILE="${PROJECT_DIR}/scripts/.env.docker"

# Docker 鏡像和容器名稱
IMAGE_NAME="${DOCKER_IMAGE_NAME:-sacahan/casual-market-mcp:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-casual-market}"

# 讀取 Docker 端口配置（預設 8066）
DOCKER_PORT="${DOCKER_PORT:-8066}"

# 檢查 .env.docker 是否存在
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠️  未找到 $ENV_FILE${NC}"
        echo -e "${YELLOW}正在從示例複製...${NC}"
        if [ -f "${PROJECT_DIR}/scripts/.env.docker.example" ]; then
            cp "${PROJECT_DIR}/scripts/.env.docker.example" "$ENV_FILE"
            echo -e "${GREEN}✓ 已建立 $ENV_FILE${NC}"
            echo -e "${BLUE}💡 您可以編輯 scripts/.env.docker 檔案來自訂配置${NC}"
        else
            echo -e "${YELLOW}ℹ️  未找到 .env.docker.example，將使用預設配置${NC}"
        fi
    fi
}

# 拉取 Docker 鏡像
pull_image() {
    echo -e "${BLUE}📥 從 Docker Hub 拉取鏡像: $IMAGE_NAME${NC}"

    if docker pull "$IMAGE_NAME"; then
        echo -e "${GREEN}✓ 鏡像拉取成功${NC}"
        echo ""
        echo -e "${BLUE}💡 下一步:${NC}"
        echo -e "   使用 ${GREEN}./docker-run.sh up${NC} 啟動容器"
    else
        echo -e "${RED}✗ 鏡像拉取失敗${NC}"
        echo -e "${YELLOW}請確保:${NC}"
        echo "   1. Docker 已安裝並運行"
        echo "   2. 網路連接正常"
        echo "   3. 鏡像名稱正確: $IMAGE_NAME"
        exit 1
    fi
}

# 啟動容器
start_container() {
    check_env_file

    # 檢查是否已運行
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}ℹ️  容器已在運行${NC}"
        show_info
        return 0
    fi

    # 檢查是否存在但未運行
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${BLUE}🔄 啟動現有容器...${NC}"
        docker start "$CONTAINER_NAME"
        echo -e "${GREEN}✓ 容器已啟動${NC}"
        show_info
        return 0
    fi

    echo -e "${BLUE}🚀 啟動新容器...${NC}"

    # 準備環境變數參數
    ENV_ARGS=""
    if [ -f "$ENV_FILE" ]; then
        ENV_ARGS="--env-file $ENV_FILE"
    fi

    # 啟動容器
    docker run -d \
        --name "$CONTAINER_NAME" \
        $ENV_ARGS \
        -p 8066:8000 \
        -v casualmarket-logs:/app/logs \
        -v casualmarket-data:/app/src/data \
        --restart unless-stopped \
        "$IMAGE_NAME"

    echo -e "${GREEN}✓ 容器已啟動${NC}"
    echo ""
    
    # 等待服務啟動
    echo -e "${BLUE}⏳ 等待服務啟動...${NC}"
    sleep 3
    
    show_info
}

# 停止容器
stop_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}ℹ️  容器未運行${NC}"
        return 0
    fi

    echo -e "${BLUE}🛑 停止容器...${NC}"
    docker stop "$CONTAINER_NAME"
    echo -e "${GREEN}✓ 容器已停止${NC}"
}

# 重啟容器
restart_container() {
    echo -e "${BLUE}🔄 重啟容器...${NC}"
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker restart "$CONTAINER_NAME"
        echo -e "${GREEN}✓ 容器已重啟${NC}"
        show_info
    else
        echo -e "${YELLOW}ℹ️  容器不存在，啟動新容器...${NC}"
        start_container
    fi
}

# 查看日誌
show_logs() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}✗ 容器未運行${NC}"
        exit 1
    fi

    echo -e "${BLUE}📋 顯示容器日誌（按 Ctrl+C 退出）...${NC}"
    docker logs -f "$CONTAINER_NAME"
}

# 進入容器 shell
enter_shell() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}✗ 容器未運行${NC}"
        exit 1
    fi

    echo -e "${BLUE}🐚 進入容器 shell...${NC}"
    docker exec -it "$CONTAINER_NAME" /bin/bash
}

# 測試服務端點
test_service() {
    echo -e "${BLUE}🧪 測試服務端點...${NC}"
    echo ""
    
    # 檢查容器是否運行
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}✗ 容器未運行，請先啟動: ./docker-run.sh up${NC}"
        exit 1
    fi
    
    # 測試健康檢查
    echo -e "${BLUE}1. 測試健康檢查端點...${NC}"
    if curl -f -s http://localhost:${DOCKER_PORT}/health > /dev/null; then
        echo -e "   ${GREEN}✓ Health check passed${NC}"
        curl -s http://localhost:${DOCKER_PORT}/health | python3 -m json.tool || true
    else
        echo -e "   ${RED}✗ Health check failed${NC}"
    fi
    echo ""
    
    # 測試根端點
    echo -e "${BLUE}2. 測試根端點...${NC}"
    if curl -f -s http://localhost:${DOCKER_PORT}/ > /dev/null; then
        echo -e "   ${GREEN}✓ Root endpoint accessible${NC}"
        curl -s http://localhost:${DOCKER_PORT}/ | python3 -m json.tool || true
    else
        echo -e "   ${RED}✗ Root endpoint failed${NC}"
    fi
    echo ""
    
    # 測試 SSE 端點
    echo -e "${BLUE}3. 測試 SSE 端點（列出工具）...${NC}"
    RESPONSE=$(curl -s -X POST http://localhost:${DOCKER_PORT}/sse \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}')
    
    if [ $? -eq 0 ]; then
        echo -e "   ${GREEN}✓ SSE endpoint working${NC}"
        echo "$RESPONSE" | grep "^data: " | sed 's/^data: //' | python3 -m json.tool 2>/dev/null | head -20 || true
        echo "   ... (truncated)"
    else
        echo -e "   ${RED}✗ SSE endpoint failed${NC}"
    fi
    echo ""
    
    echo -e "${GREEN}✅ 測試完成${NC}"
    echo ""
    echo -e "${BLUE}📚 更多測試:${NC}"
    echo -e "   API 文檔: ${GREEN}http://localhost:${DOCKER_PORT}/docs${NC}"
    echo -e "   範例客戶端: ${GREEN}python examples/sse_client_example.py${NC}"
}

# 移除容器
remove_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${BLUE}🗑️  移除容器...${NC}"
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME"
        echo -e "${GREEN}✓ 容器已移除${NC}"
    else
        echo -e "${YELLOW}ℹ️  容器不存在${NC}"
    fi
}

# 清理資源
clean_up() {
    echo -e "${YELLOW}⚠️  此操作將刪除容器、磁碟區和本地鏡像...${NC}"
    read -p "確認要繼續嗎？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}清理中...${NC}"

        # 停止並移除容器
        remove_container

        # 移除磁碟區
        docker volume rm casualmarket-logs 2>/dev/null || true
        docker volume rm casualmarket-data 2>/dev/null || true

        # 移除本地鏡像
        docker rmi casualmarket-mcp:latest 2>/dev/null || true

        # 系統清理
        docker system prune -f

        echo -e "${GREEN}✓ 清理完成${NC}"
    else
        echo -e "${YELLOW}已取消${NC}"
    fi
}

# 顯示幫助信息
show_help() {
    cat << 'EOF'
CasualMarket MCP Server - Docker 執行腳本

用法: ./docker-run.sh [command]

📋 命令:

    pull       從 Docker Hub 拉取鏡像
  up         啟動容器
  down       停止並移除容器
  restart    重啟容器
  logs       查看日誌
  shell      進入容器 shell
  test       測試服務端點
  info       顯示服務信息
  clean      清理資源
  help       顯示此幫助信息

🚀 快速開始:

    步驟:
        1. 拉取鏡像:    ./docker-run.sh pull
        2. 啟動服務:    ./docker-run.sh up
        3. 查看日誌:    ./docker-run.sh logs

🔗 服務端點:
  Root:      http://localhost:${DOCKER_PORT}
  Health:    http://localhost:${DOCKER_PORT}/health
  SSE:       http://localhost:${DOCKER_PORT}/sse
  API 文檔:  http://localhost:${DOCKER_PORT}/docs

📝 環境配置:
  配置文件: scripts/.env.docker (自動從 .env.docker.example 創建)

🧪 測試服務:
  ./docker-run.sh test
  或訪問: http://localhost:8000/docs

💡 更多幫助: ./docker-run.sh info

EOF
}

# 顯示服務信息
show_info() {
    echo -e "${BLUE}📊 服務信息：${NC}"
    echo ""
    
    # 檢查容器狀態
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "  狀態: ${GREEN}運行中 ✓${NC}"
        
        # 獲取容器 IP
        CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || echo "N/A")
        echo -e "  容器 IP: $CONTAINER_IP"
    else
        echo -e "  狀態: ${RED}未運行 ✗${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🌐 服務端點：${NC}"
    echo -e "  Root:      ${GREEN}http://localhost:${DOCKER_PORT}/${NC}"
    echo -e "  Health:    ${GREEN}http://localhost:${DOCKER_PORT}/health${NC}"
    echo -e "  SSE:       ${GREEN}http://localhost:${DOCKER_PORT}/sse${NC}"
    echo -e "  API 文檔:  ${GREEN}http://localhost:${DOCKER_PORT}/docs${NC}"
    echo ""
    echo -e "${BLUE}📂 磁碟區：${NC}"
    echo -e "  Logs:      casualmarket-logs  -> /app/logs"
    echo -e "  Data:      casualmarket-data  -> /app/src/data"
    echo ""
    echo -e "${BLUE}🔧 常用命令：${NC}"
    echo -e "  查看日誌:   ${GREEN}./docker-run.sh logs${NC}"
    echo -e "  進入容器:   ${GREEN}./docker-run.sh shell${NC}"
    echo -e "  測試服務:   ${GREEN}./docker-run.sh test${NC}"
    echo -e "  重啟服務:   ${GREEN}./docker-run.sh restart${NC}"
    echo -e "  停止服務:   ${GREEN}./docker-run.sh down${NC}"
}

# 主函式
main() {
    local command=${1:-help}

    case "$command" in
    pull)
        pull_image
        ;;
    up)
        start_container
        ;;
    down)
        remove_container
        ;;
    restart)
        restart_container
        ;;
    logs)
        show_logs
        ;;
    shell)
        enter_shell
        ;;
    test)
        test_service
        ;;
    clean)
        clean_up
        ;;
    info)
        show_info
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $command${NC}"
        echo ""
        echo -e "${BLUE}使用 '${GREEN}./docker-run.sh help${BLUE}' 查看完整幫助信息${NC}"
        echo ""
        echo "快速命令列表:"
        echo "  pull     - 拉取鏡像"
        echo "  up       - 啟動服務"
        echo "  down     - 停止並移除服務"
        echo "  restart  - 重啟服務"
        echo "  logs     - 查看日誌"
        echo "  shell    - 進入容器"
        echo "  test     - 測試服務"
        echo "  info     - 顯示信息"
        echo "  clean    - 清理資源"
        echo "  help     - 顯示幫助"
        exit 1
        ;;
    esac
}

main "$@"
