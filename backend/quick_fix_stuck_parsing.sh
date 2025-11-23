#!/bin/bash

# ============================================================================
# 一键修复解析卡住问题
# ============================================================================
# 用途: 快速修复 Worklist 文件卡在 parsing 状态的问题
# 优先级: 高
# 预计时间: 5-10 分钟
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ID="cmsupload-476323"
SERVICE_NAME="cms-automation-backend"
REGION="us-east1"

# 数据库配置
DB_HOST="aws-1-us-east-1.pooler.supabase.com"
DB_PORT="6543"
DB_USER="postgres.twsbhjmlmspjwfystpti"
DB_NAME="postgres"
export PGPASSWORD="Xieping890$"

# ============================================================================
# 函数定义
# ============================================================================

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# 步骤 1: 检查卡住的文件
# ============================================================================

check_stuck_items() {
    print_header "步骤 1: 检查卡住的文件"

    RESULT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c \
        "SELECT COUNT(*) FROM worklist_items WHERE status = 'parsing' AND updated_at < NOW() - INTERVAL '1 hour';")

    STUCK_COUNT=$(echo $RESULT | xargs)

    if [ "$STUCK_COUNT" -gt 0 ]; then
        print_warning "发现 $STUCK_COUNT 个卡住的文件"

        echo ""
        echo "卡住的文件详情:"
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
            "SELECT id, title, status, created_at, updated_at FROM worklist_items WHERE status = 'parsing' AND updated_at < NOW() - INTERVAL '1 hour' ORDER BY id;"

        return 1
    else
        print_success "没有发现卡住的文件"
        return 0
    fi
}

# ============================================================================
# 步骤 2: 检查最近的错误日志
# ============================================================================

check_error_logs() {
    print_header "步骤 2: 检查最近的错误日志"

    print_info "正在获取最近 1 小时的错误日志..."

    gcloud logging read \
        "resource.type=cloud_run_revision \
         AND resource.labels.service_name=$SERVICE_NAME \
         AND severity>=ERROR \
         AND timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')\"" \
        --limit 10 \
        --format="table(timestamp, severity, textPayload)" \
        --project=$PROJECT_ID || true

    echo ""
    read -p "是否看到严重错误? (y/N): " has_errors

    if [[ $has_errors =~ ^[Yy]$ ]]; then
        print_warning "检测到错误,建议先修复错误后再继续"
        return 1
    else
        print_success "没有严重错误"
        return 0
    fi
}

# ============================================================================
# 步骤 3: 重启 Cloud Run 服务
# ============================================================================

restart_service() {
    print_header "步骤 3: 重启 Cloud Run 服务"

    print_info "获取当前服务镜像..."
    IMAGE=$(gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(spec.template.spec.containers[0].image)")

    print_info "当前镜像: $IMAGE"

    read -p "是否要重启服务? (Y/n): " do_restart

    if [[ ! $do_restart =~ ^[Nn]$ ]]; then
        print_info "正在重启服务..."

        gcloud run services update $SERVICE_NAME \
            --region=$REGION \
            --project=$PROJECT_ID \
            --image=$IMAGE \
            --min-instances=1 \
            --max-instances=3

        print_success "服务重启命令已发送"
        print_info "等待服务就绪... (约 30-60 秒)"
        sleep 30

        # 检查服务状态
        STATUS=$(gcloud run services describe $SERVICE_NAME \
            --region=$REGION \
            --project=$PROJECT_ID \
            --format="value(status.conditions[0].status)")

        if [ "$STATUS" == "True" ]; then
            print_success "服务已就绪"
            return 0
        else
            print_warning "服务状态: $STATUS"
            return 1
        fi
    else
        print_warning "跳过服务重启"
        return 0
    fi
}

# ============================================================================
# 步骤 4: 重置卡住的文件
# ============================================================================

reset_stuck_items() {
    print_header "步骤 4: 重置卡住的文件"

    # 获取卡住的文件 ID
    STUCK_IDS=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c \
        "SELECT STRING_AGG(id::text, ', ') FROM worklist_items WHERE status = 'parsing' AND updated_at < NOW() - INTERVAL '1 hour';")

    if [ -z "$STUCK_IDS" ] || [ "$STUCK_IDS" == " " ]; then
        print_success "没有需要重置的文件"
        return 0
    fi

    STUCK_IDS=$(echo $STUCK_IDS | xargs)
    print_warning "准备重置文件 ID: $STUCK_IDS"

    read -p "是否要将这些文件重置为 pending 状态? (Y/n): " do_reset

    if [[ ! $do_reset =~ ^[Nn]$ ]]; then
        print_info "正在重置文件状态..."

        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
            "UPDATE worklist_items SET status = 'pending', updated_at = NOW() WHERE status = 'parsing' AND updated_at < NOW() - INTERVAL '1 hour';"

        print_success "文件已重置为 pending 状态"

        echo ""
        echo "重置后的状态:"
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
            "SELECT id, title, status, updated_at FROM worklist_items WHERE id IN ($STUCK_IDS);"

        return 0
    else
        print_warning "跳过文件重置"
        return 0
    fi
}

# ============================================================================
# 步骤 5: 监控处理进度
# ============================================================================

monitor_progress() {
    print_header "步骤 5: 监控处理进度"

    print_info "将持续监控 5 分钟,观察文件状态变化"
    print_info "按 Ctrl+C 可随时停止监控"

    echo ""

    for i in {1..10}; do
        clear
        echo "=== 处理进度监控 (第 $i/10 次检查) ==="
        echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""

        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
            "SELECT
                id,
                LEFT(title, 30) as title,
                status,
                TO_CHAR(updated_at, 'HH24:MI:SS') as last_update,
                ROUND(EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60, 1) as minutes_ago
             FROM worklist_items
             WHERE status IN ('pending', 'parsing', 'parsing_review')
             ORDER BY updated_at DESC
             LIMIT 10;"

        echo ""
        echo "状态说明:"
        echo "  pending         - 等待处理"
        echo "  parsing         - 正在解析"
        echo "  parsing_review  - 解析完成,等待审核"
        echo ""

        if [ $i -lt 10 ]; then
            echo "下次检查倒计时: 30 秒..."
            sleep 30
        fi
    done

    print_success "监控完成"
}

# ============================================================================
# 步骤 6: 最终验证
# ============================================================================

final_verification() {
    print_header "步骤 6: 最终验证"

    # 检查是否还有卡住的文件
    STUCK_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c \
        "SELECT COUNT(*) FROM worklist_items WHERE status = 'parsing' AND updated_at < NOW() - INTERVAL '10 minutes';" | xargs)

    echo ""
    echo "验证结果:"
    echo "--------"

    if [ "$STUCK_COUNT" -eq 0 ]; then
        print_success "没有文件卡在 parsing 状态超过 10 分钟"
        print_success "问题已解决!"
        return 0
    else
        print_warning "仍有 $STUCK_COUNT 个文件卡住超过 10 分钟"

        echo ""
        echo "卡住的文件:"
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
            "SELECT id, title, status, updated_at FROM worklist_items WHERE status = 'parsing' AND updated_at < NOW() - INTERVAL '10 minutes';"

        print_warning "可能需要进一步调查"
        print_info "请查看 PARSING_STUCK_TROUBLESHOOTING_GUIDE.md 获取详细故障排除步骤"
        return 1
    fi
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    echo ""
    print_header "CMS 解析卡住问题 - 一键修复工具"
    echo ""
    echo "本工具将执行以下步骤:"
    echo "1. 检查卡住的文件"
    echo "2. 检查错误日志"
    echo "3. 重启 Cloud Run 服务"
    echo "4. 重置卡住的文件"
    echo "5. 监控处理进度"
    echo "6. 最终验证"
    echo ""

    read -p "按 Enter 键开始,或按 Ctrl+C 取消... "

    echo ""

    # 执行各步骤
    check_stuck_items || true
    echo ""

    check_error_logs || true
    echo ""

    restart_service
    echo ""

    # 等待服务重启完成
    print_info "等待服务完全启动... (30 秒)"
    sleep 30
    echo ""

    reset_stuck_items
    echo ""

    # 等待一下让系统开始处理
    print_info "等待系统开始处理... (30 秒)"
    sleep 30
    echo ""

    monitor_progress
    echo ""

    final_verification
    EXIT_CODE=$?

    echo ""
    print_header "执行完成"
    echo ""

    if [ $EXIT_CODE -eq 0 ]; then
        print_success "所有步骤已成功完成!"
        echo ""
        echo "建议:"
        echo "- 继续监控 Worklist 页面,确保新文件能正常处理"
        echo "- 检查应用日志,确认没有新的错误"
    else
        print_warning "部分步骤可能需要额外关注"
        echo ""
        echo "下一步:"
        echo "- 查看详细故障排除指南: PARSING_STUCK_TROUBLESHOOTING_GUIDE.md"
        echo "- 检查应用错误日志"
        echo "- 联系技术团队寻求帮助"
    fi

    exit $EXIT_CODE
}

# 运行主流程
main
