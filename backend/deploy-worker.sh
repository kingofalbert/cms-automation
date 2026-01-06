#!/bin/bash

# 部署 Celery Worker 到 Cloud Run
# 用途：处理 Worklist 中的文件
#
# 使用前请设置以下环境变量：
# - DATABASE_URL: PostgreSQL 数据库连接字符串
# - REDIS_URL: Redis 连接字符串
# - ANTHROPIC_API_KEY: Anthropic API 密钥
# - CMS_BASE_URL: WordPress 站点 URL
# - CMS_USERNAME: WordPress 用户名
# - CMS_APPLICATION_PASSWORD: WordPress 应用密码

set -e

PROJECT_ID="cmsupload-476323"
REGION="us-east1"
SERVICE_NAME="cms-automation-worker"
IMAGE="us-east1-docker.pkg.dev/cmsupload-476323/cms-backend/cms-automation-backend:prod-v20251122"

echo "🚀 部署 Worker 服务..."
echo "项目: $PROJECT_ID"
echo "区域: $REGION"
echo "服务名: $SERVICE_NAME"
echo "镜像: $IMAGE"
echo ""

gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --project=$PROJECT_ID \
  --region=$REGION \
  --platform=managed \
  --set-env-vars="SERVICE_TYPE=worker" \
  --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
  --set-env-vars="REDIS_URL=${REDIS_URL}" \
  --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" \
  --set-env-vars="ANTHROPIC_MODEL=claude-sonnet-4-5-20250929" \
  --set-env-vars="CMS_BASE_URL=${CMS_BASE_URL}" \
  --set-env-vars="CMS_USERNAME=${CMS_USERNAME}" \
  --set-env-vars="CMS_APPLICATION_PASSWORD=${CMS_APPLICATION_PASSWORD}" \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=3 \
  --concurrency=10 \
  --timeout=900 \
  --no-allow-unauthenticated

echo ""
echo "✅ Worker 服务部署完成！"
