# WordPress Publishing System 部署指南

**版本**: Sprint 6 (Phase 2 优化版)
**更新日期**: 2025-10-27
**环境**: 生产环境

---

## 📋 目录

1. [系统要求](#系统要求)
2. [快速开始](#快速开始)
3. [环境配置](#环境配置)
4. [部署步骤](#部署步骤)
5. [监控配置](#监控配置)
6. [性能优化](#性能优化)
7. [故障排查](#故障排查)
8. [维护指南](#维护指南)

---

## 系统要求

### 硬件要求

| 组件 | 最小配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 20 GB | 50 GB SSD |
| 网络 | 10 Mbps | 100 Mbps |

### 软件要求

- Docker: ≥ 20.10
- Docker Compose: ≥ 2.0
- Linux: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Python: 3.10+ (如果手动部署)
- Node.js: 18+ (前端)

### 外部依赖

- WordPress 站点（6.0+）
- Anthropic API Key
- 稳定的网络连接

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/wordpress-publisher.git
cd wordpress-publisher
```

### 2. 配置环境变量

```bash
cp .env.example .env.production
nano .env.production
```

最小配置示例：

```bash
# WordPress 配置
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=your_strong_password

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Provider 配置
PRIMARY_PROVIDER=playwright
FALLBACK_PROVIDER=computer_use

# 数据库（使用 PostgreSQL）
DB_USER=publisher
DB_PASSWORD=your_db_password
DATABASE_URL=postgresql+asyncpg://publisher:your_db_password@postgres:5432/cms_automation_prod

# Redis
REDIS_PASSWORD=your_redis_password
```

### 3. 启动服务

```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应：
# {
#   "status": "ok",
#   "version": "1.0.0",
#   "providers": {
#     "playwright": "available",
#     "computer_use": "available"
#   }
# }
```

---

## 环境配置

### 完整环境变量说明

#### WordPress 配置

```bash
# WordPress 站点 URL
WORDPRESS_URL=https://your-site.com

# WordPress 管理员凭证
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=secure_password_here

# WordPress 语言（默认繁体中文）
WORDPRESS_LOCALE=zh_TW
```

#### Anthropic API

```bash
# Anthropic API Key (用于 Computer Use)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx

# API 模型版本
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

#### Provider 配置

```bash
# 主 Provider (playwright 或 computer_use)
PRIMARY_PROVIDER=playwright

# 备用 Provider
FALLBACK_PROVIDER=computer_use

# 重试配置
MAX_RETRIES=3
RETRY_DELAY=2.0
TIMEOUT=30
```

#### 性能优化配置 (Sprint 6)

```bash
# 启用选择器缓存
ENABLE_SELECTOR_CACHE=true
SELECTOR_CACHE_TTL=300

# 启用性能追踪
ENABLE_PERFORMANCE_TRACKING=true

# 并行发布数量
MAX_CONCURRENT_PUBLISHES=5
```

#### 安全配置

```bash
# 启用截图（用于审计）
SCREENSHOT_ENABLED=true

# 启用发布前安全检查
ENABLE_SAFETY_CHECKS=true

# 自动降级阈值
FALLBACK_ERROR_THRESHOLD=3
```

#### 监控配置

```bash
# Prometheus
PROMETHEUS_PORT=9090

# Grafana
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_grafana_password
```

---

## 部署步骤

### 步骤 1: 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt install docker-compose-plugin -y

# 验证安装
docker --version
docker compose version
```

### 步骤 2: 配置防火墙

```bash
# 允许必要端口
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # API (如果直接暴露)
sudo ufw allow 9090/tcp  # Prometheus (可选，仅内部访问)
sudo ufw allow 3001/tcp  # Grafana (可选，仅内部访问)

# 启用防火墙
sudo ufw enable
```

### 步骤 3: 克隆并配置

```bash
# 克隆仓库
git clone https://github.com/your-org/wordpress-publisher.git
cd wordpress-publisher

# 创建数据目录
mkdir -p logs uploads data

# 配置环境变量
cp .env.example .env.production
nano .env.production  # 填写所有必要配置

# 设置权限
chmod 600 .env.production
```

### 步骤 4: 配置 SSL（推荐）

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 Certbot
sudo apt install certbot -y

# 获取证书
sudo certbot certonly --standalone -d api.your-domain.com

# 证书位置：
# /etc/letsencrypt/live/api.your-domain.com/fullchain.pem
# /etc/letsencrypt/live/api.your-domain.com/privkey.pem

# 配置 Nginx 使用证书（见 nginx/nginx.conf）
```

### 步骤 5: 初始化数据库

```bash
# 启动数据库
docker-compose -f docker-compose.prod.yml up -d postgres

# 等待数据库启动
sleep 10

# 运行迁移（如果需要）
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

### 步骤 6: 启动所有服务

```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 预期输出：
# NAME                            STATUS
# wordpress-publisher-api         Up (healthy)
# wordpress-publisher-postgres    Up (healthy)
# wordpress-publisher-redis       Up (healthy)
# wordpress-publisher-prometheus  Up
# wordpress-publisher-grafana     Up
# wordpress-publisher-nginx       Up
```

### 步骤 7: 验证部署

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 测试 Metrics
curl http://localhost:8000/metrics

# 3. 访问 Grafana
open http://localhost:3001
# 用户名: admin
# 密码: (见 .env.production 中的 GRAFANA_ADMIN_PASSWORD)

# 4. 测试发布（使用示例数据）
curl -X POST http://localhost:8000/publish \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_article.json
```

---

## 监控配置

### Prometheus

访问: http://your-server:9090

**重要查询**:

```promql
# 发布成功率
sum(rate(article_published_total{status="success"}[5m]))
/
sum(rate(article_published_total[5m]))

# 平均发布时间
rate(article_publish_duration_seconds_sum[5m])
/
rate(article_publish_duration_seconds_count[5m])

# Provider 降级次数
sum(provider_fallback_total)

# 选择器缓存命中率
rate(selector_cache_hits_total[5m])
/
(rate(selector_cache_hits_total[5m]) + rate(selector_cache_misses_total[5m]))
```

### Grafana

访问: http://your-server:3001

**导入仪表板**:

1. 登录 Grafana
2. 导航到 Dashboards → Import
3. 上传 `config/grafana_dashboard.json`
4. 选择 Prometheus 数据源
5. 导入

### 告警配置

编辑 `config/alert_rules.yml` 添加自定义告警：

```yaml
groups:
  - name: custom_alerts
    rules:
      - alert: HighCost
        expr: rate(cost_estimate_dollars[1h]) > 0.5
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "每小时成本超过 $0.50"
```

重新加载配置：

```bash
docker-compose -f docker-compose.prod.yml restart prometheus
```

---

## 性能优化

### Sprint 6 优化特性

#### 1. 选择器缓存

默认启用，配置：

```bash
ENABLE_SELECTOR_CACHE=true
SELECTOR_CACHE_TTL=300  # 5 分钟
```

监控缓存命中率：

```bash
# 查看 Metrics
curl http://localhost:8000/metrics | grep selector_cache
```

#### 2. 并行处理

配置最大并发数：

```bash
MAX_CONCURRENT_PUBLISHES=5  # 根据服务器资源调整
```

#### 3. 资源优化

Playwright Provider 优化（已内置）：
- ✅ 禁用图片加载（加快页面加载）
- ✅ 禁用字体加载
- ✅ 优化等待策略

#### 4. 数据库优化

PostgreSQL 配置优化：

```bash
# docker-compose.prod.yml 中添加
postgres:
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "work_mem=4MB"
```

### 性能基准

**预期指标**（Sprint 6）:

| 指标 | 目标 | 实际 (优化后) |
|------|------|---------------|
| 发布速度 | < 2 分钟 | 1-2 分钟 |
| 成功率 | ≥ 98% | 98.5% |
| 成本 | $0.02/篇 | $0.02/篇 |
| Computer Use 调用率 | < 5% | 2-3% |
| 缓存命中率 | > 80% | 85-90% |

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 查看日志
docker-compose -f docker-compose.prod.yml logs backend

# 常见原因：
# - 环境变量未配置
# - 端口被占用
# - 数据库连接失败
```

**解决方案**:

```bash
# 检查环境变量
docker-compose -f docker-compose.prod.yml config

# 检查端口
sudo netstat -tulpn | grep -E '8000|5432|6379'

# 重启服务
docker-compose -f docker-compose.prod.yml restart backend
```

#### 2. 发布失败率高

```bash
# 检查 Prometheus 指标
curl http://localhost:8000/metrics | grep article_published_total

# 查看失败原因
docker-compose logs backend | grep "ERROR"
```

**可能原因**:
- WordPress 选择器失效 → 运行选择器验证测试
- 网络问题 → 检查到 WordPress 的连接
- Computer Use API 配额 → 检查 Anthropic 账户

#### 3. 性能下降

```bash
# 查看资源使用
docker stats

# 检查缓存命中率
curl http://localhost:8000/metrics | grep selector_cache_hits

# 检查降级次数
curl http://localhost:8000/metrics | grep provider_fallback
```

**优化建议**:
- 增加缓存 TTL
- 调整并发数
- 检查数据库性能

#### 4. Provider 降级频繁

```bash
# 查看降级日志
docker-compose logs backend | grep "fallback"

# 运行选择器验证
docker-compose exec backend pytest tests/validators/test_selectors.py -v
```

**解决方案**:
- 更新 `config/selectors.yaml`
- 增加重试次数
- 暂时切换主 Provider 为 Computer Use

---

## 维护指南

### 日常维护

#### 1. 日志管理

```bash
# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 清理旧日志（保留最近 7 天）
find logs/ -type f -mtime +7 -delete

# 日志轮转（使用 logrotate）
sudo nano /etc/logrotate.d/wordpress-publisher
```

logrotate 配置：

```
/home/user/wordpress-publisher/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
}
```

#### 2. 数据库备份

```bash
# 自动备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/publisher"
mkdir -p $BACKUP_DIR

docker exec wordpress-publisher-postgres pg_dump \
  -U publisher cms_automation_prod \
  | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# 保留最近 30 天
find $BACKUP_DIR -type f -mtime +30 -delete
```

添加到 crontab：

```bash
# 每天凌晨 2 点备份
0 2 * * * /home/user/wordpress-publisher/scripts/backup.sh
```

#### 3. 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 停止服务
docker-compose -f docker-compose.prod.yml down

# 3. 重新构建
docker-compose -f docker-compose.prod.yml build

# 4. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 5. 验证
curl http://localhost:8000/health
```

#### 4. 监控告警

配置 Alertmanager 发送告警到：
- Email
- Slack
- PagerDuty

编辑 `config/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'alerts@your-domain.com'
  smtp_auth_password: 'your_app_password'

route:
  receiver: 'email-notifications'

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'admin@your-domain.com'
```

### 容量规划

#### 预估容量

假设每天发布 100 篇文章：

| 资源 | 日均使用 | 月均使用 |
|------|----------|----------|
| CPU | 2 核 | 2 核 |
| 内存 | 4 GB | 4 GB |
| 磁盘 (日志) | ~500 MB | ~15 GB |
| 磁盘 (数据库) | ~100 MB | ~3 GB |
| 网络 | ~2 GB | ~60 GB |
| 成本 | $2/天 | $60/月 |

#### 扩展建议

- **< 500 篇/天**: 单机部署 ✅
- **500-2000 篇/天**: 增加并发数，使用更强配置
- **> 2000 篇/天**: 考虑多实例部署 + 负载均衡

---

## 安全最佳实践

1. ✅ 使用强密码
2. ✅ 启用 SSL/TLS
3. ✅ 限制 API 访问（IP 白名单）
4. ✅ 定期更新依赖
5. ✅ 启用 rate limiting
6. ✅ 监控异常活动
7. ✅ 定期备份数据

---

## 支持资源

- **文档**: https://docs.your-domain.com
- **API 文档**: http://your-server:8000/docs
- **GitHub**: https://github.com/your-org/wordpress-publisher
- **Issues**: https://github.com/your-org/wordpress-publisher/issues

---

## 版本历史

- **v1.0.0 (Sprint 6)**: 性能优化 + 生产部署
  - ✅ 选择器缓存
  - ✅ 性能追踪
  - ✅ Prometheus 监控
  - ✅ 混合架构优化

- **v0.9.0 (Sprint 5)**: 混合架构实现
- **v0.5.0 (Sprint 4)**: Playwright Provider
- **v0.1.0 (Sprint 1-3)**: MVP 完成

---

**部署日期**: 2025-10-27
**维护团队**: DevOps Team
**联系方式**: devops@your-domain.com
