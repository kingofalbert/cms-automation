# Google Cloud Secret Manager 設置指南

## 概述

本指南將幫助你設置 Google Cloud Secret Manager 來安全地管理 CMS Automation 系統的敏感憑證。

**為什麼選擇 GCP Secret Manager？**
- ✅ 與你現有的 GCP Redis 在同一平台
- ✅ 統一的憑證和訪問管理
- ✅ 比 AWS Secrets Manager 更便宜（~$0.06/10K 訪問 vs ~$0.05/10K）
- ✅ 自動加密、審計追蹤、版本控制
- ✅ 與 Supabase 架構兼容

---

## 前置條件

1. **GCP 項目**: 你已經有的 GCP 項目（運行 Redis 的項目）
2. **GCP CLI**: 安裝並配置 `gcloud` CLI
3. **權限**: 擁有項目的 Owner 或 Secret Manager Admin 角色

---

## 第一步：啟用 Secret Manager API

### 方法 A: 使用 GCP Console

1. 打開 [GCP Console](https://console.cloud.google.com/)
2. 選擇你的項目
3. 導航到：**APIs & Services > Library**
4. 搜索 "Secret Manager API"
5. 點擊 **Enable**

### 方法 B: 使用 gcloud CLI

```bash
# 設置你的項目
gcloud config set project YOUR_PROJECT_ID

# 啟用 Secret Manager API
gcloud services enable secretmanager.googleapis.com

# 驗證已啟用
gcloud services list --enabled | grep secretmanager
```

---

## 第二步：創建服務帳戶

### 創建服務帳戶

```bash
# 設置變量
export PROJECT_ID="cms-automation-2025"
export SERVICE_ACCOUNT_NAME="cms-automation-secrets"
export SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 創建服務帳戶
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
    --display-name="CMS Automation Secrets Manager" \
    --description="Service account for CMS automation to access secrets" \
    --project=${PROJECT_ID}

# 驗證創建成功
gcloud iam service-accounts list --project=${PROJECT_ID}
```

### 授予權限

```bash
# 授予 Secret Manager Secret Accessor 角色（讀取權限）
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

# 如果需要創建/更新 secrets（用於自動輪換），額外授予：
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretVersionAdder"
```

### 創建服務帳戶密鑰

```bash
# 創建密鑰文件
gcloud iam service-accounts keys create ~/gcp-credentials.json \
    --iam-account=${SERVICE_ACCOUNT_EMAIL} \
    --project=${PROJECT_ID}

# 查看密鑰信息
cat ~/gcp-credentials.json | jq '.client_email'

# 移動到安全位置
mkdir -p /path/to/cms_automation/backend/credentials
mv ~/gcp-credentials.json /path/to/cms_automation/backend/credentials/gcp-credentials.json
chmod 600 /path/to/cms_automation/backend/credentials/gcp-credentials.json
```

**重要**:
- ❌ **絕對不要** 將此文件提交到 git
- ✅ 確認 `.gitignore` 已排除 `backend/credentials/` 目錄
- ✅ 在生產環境使用 Workload Identity 或 ADC

---

## 第三步：創建 Secrets

### 方法 A: 使用 gcloud CLI（推薦）

```bash
# 設置項目
export PROJECT_ID="cms-automation-2025"

# 創建 secrets
gcloud secrets create ANTHROPIC_API_KEY \
    --replication-policy="automatic" \
    --project=${PROJECT_ID}

gcloud secrets create CMS_APPLICATION_PASSWORD \
    --replication-policy="automatic" \
    --project=${PROJECT_ID}

gcloud secrets create CMS_HTTP_AUTH_PASSWORD \
    --replication-policy="automatic" \
    --project=${PROJECT_ID}

gcloud secrets create DATABASE_PASSWORD \
    --replication-policy="automatic" \
    --project=${PROJECT_ID}

gcloud secrets create SECRET_KEY \
    --replication-policy="automatic" \
    --project=${PROJECT_ID}

gcloud secrets create SUPABASE_SERVICE_KEY \
    --replication-policy="automatic" \
    --project=${PROJECT_ID}

# 添加 secret 值
echo -n "sk-ant-api03-your-key-here" | \
    gcloud secrets versions add ANTHROPIC_API_KEY \
    --data-file=- \
    --project=${PROJECT_ID}

echo -n "your-cms-password" | \
    gcloud secrets versions add CMS_APPLICATION_PASSWORD \
    --data-file=- \
    --project=${PROJECT_ID}

# ... 重複其他 secrets
```

### 方法 B: 使用 GCP Console

1. 打開 [Secret Manager Console](https://console.cloud.google.com/security/secret-manager)
2. 點擊 **Create Secret**
3. 填寫:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Secret value**: 你的 API key
   - **Replication policy**: Automatic
4. 點擊 **Create Secret**
5. 重複其他 secrets

### 方法 C: 使用 Python 腳本（批量導入）

```python
# scripts/migrate_secrets_to_gcp.py
import os
from google.cloud import secretmanager
from dotenv import load_dotenv

# 加載當前 .env 文件
load_dotenv('/path/to/cms_automation/.env')

# 初始化 client
project_id = "cms-automation-2025"
client = secretmanager.SecretManagerServiceClient()
parent = f"projects/{project_id}"

# 需要遷移的 secrets
SECRETS_TO_MIGRATE = [
    "ANTHROPIC_API_KEY",
    "CMS_APPLICATION_PASSWORD",
    "CMS_HTTP_AUTH_PASSWORD",
    "DATABASE_PASSWORD",
    "SECRET_KEY",
    "SUPABASE_SERVICE_KEY",
]

for secret_key in SECRETS_TO_MIGRATE:
    value = os.getenv(secret_key)

    if not value:
        print(f"⚠️  {secret_key} not found in .env, skipping")
        continue

    try:
        # 創建 secret
        secret = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_key,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        print(f"✅ Created secret: {secret_key}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️  Secret {secret_key} already exists, updating...")
        else:
            print(f"❌ Failed to create {secret_key}: {e}")
            continue

    try:
        # 添加 secret 版本
        secret_path = f"{parent}/secrets/{secret_key}"
        client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": value.encode("UTF-8")},
            }
        )
        print(f"✅ Added version for: {secret_key}")
    except Exception as e:
        print(f"❌ Failed to add version for {secret_key}: {e}")

print("\n✅ Migration complete!")
```

運行遷移腳本：

```bash
# 設置 GCP 憑證
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json

# 運行腳本
poetry run python scripts/migrate_secrets_to_gcp.py
```

---

## 第四步：配置應用程序

### 更新 .env 文件

```bash
# Credential Storage Backend
CREDENTIAL_STORAGE_BACKEND=gcp_secret_manager

# GCP Configuration
GCP_PROJECT_ID=cms-automation-2025

# Optional: Prefix for secrets (useful for multi-environment)
# GCP_SECRET_PREFIX=cms-automation-prod-

# GCP Credentials (for development/local testing)
# In production, use Workload Identity or Application Default Credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/cms_automation/backend/credentials/gcp-credentials.json

# Credential Cache (optional)
CREDENTIAL_CACHE_TTL=300  # 5 minutes
CREDENTIAL_CACHE_ENABLED=true

# 保留非敏感配置
CMS_BASE_URL=https://admin.epochtimes.com
CMS_USERNAME=ping.xie
CMS_TYPE=wordpress
DATABASE_HOST=aws-1-us-east-1.pooler.supabase.com
REDIS_HOST=your-redis-host
# ... 其他非敏感配置
```

### 測試配置

```bash
# 測試 GCP Secret Manager 連接
poetry run python -c "
import asyncio
import os

os.environ['CREDENTIAL_STORAGE_BACKEND'] = 'gcp_secret_manager'
os.environ['GCP_PROJECT_ID'] = 'cms-automation-2025'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/gcp-credentials.json'

from src.services.credentials import get_credential_manager

async def test():
    manager = get_credential_manager()
    api_key = await manager.get('ANTHROPIC_API_KEY')

    if api_key:
        print(f'✅ Retrieved ANTHROPIC_API_KEY: {api_key[:20]}...')
    else:
        print('❌ Failed to retrieve credential')

asyncio.run(test())
"
```

---

## 第五步：生產部署

### 選項 A: 使用 Workload Identity（推薦）

如果在 GKE 或 Cloud Run 上運行：

```yaml
# kubernetes deployment
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cms-automation
  annotations:
    iam.gke.io/gcp-service-account: cms-automation-secrets@PROJECT_ID.iam.gserviceaccount.com
```

```bash
# 綁定 Workload Identity
gcloud iam service-accounts add-iam-policy-binding \
    cms-automation-secrets@PROJECT_ID.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/cms-automation]"
```

**環境變量**：
```bash
CREDENTIAL_STORAGE_BACKEND=gcp_secret_manager
GCP_PROJECT_ID=cms-automation-2025
# GOOGLE_APPLICATION_CREDENTIALS 不需要設置（自動使用 Workload Identity）
```

### 選項 B: 使用 Application Default Credentials

在 GCE、Cloud Run、或其他 GCP 服務上：

```bash
# 環境變量
CREDENTIAL_STORAGE_BACKEND=gcp_secret_manager
GCP_PROJECT_ID=cms-automation-2025
# ADC 會自動使用實例的服務帳戶
```

### 選項 C: 使用服務帳戶密鑰文件（不推薦生產使用）

```bash
# 僅用於測試環境
CREDENTIAL_STORAGE_BACKEND=gcp_secret_manager
GCP_PROJECT_ID=cms-automation-2025
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

---

## Secret 命名規範

### 基本命名

```
ANTHROPIC_API_KEY
CMS_APPLICATION_PASSWORD
DATABASE_PASSWORD
```

### 帶前綴命名（多環境）

如果你想在同一項目中管理多個環境的 secrets：

```bash
# .env
GCP_SECRET_PREFIX=cms-automation-prod-

# GCP 中的 secret 名稱
cms-automation-prod-ANTHROPIC_API_KEY
cms-automation-prod-CMS_APPLICATION_PASSWORD
cms-automation-prod-DATABASE_PASSWORD
```

**好處**：
- ✅ 清晰的環境隔離
- ✅ 避免意外訪問錯誤環境的 secrets
- ✅ 更好的審計和追蹤

---

## IAM 權限詳解

### 最小權限原則

**開發環境**：
```bash
# 需要讀取和創建權限（用於測試）
roles/secretmanager.secretAccessor  # 讀取 secret 值
roles/secretmanager.secretVersionAdder  # 添加新版本（用於測試輪換）
```

**生產環境**：
```bash
# 僅需要讀取權限
roles/secretmanager.secretAccessor  # 讀取 secret 值
```

**CI/CD 管道**：
```bash
# 需要完整管理權限
roles/secretmanager.admin  # 創建、更新、刪除 secrets
```

### 自定義 IAM 角色

創建最小權限角色：

```bash
# 創建自定義角色
gcloud iam roles create cmsAutomationSecretsReader \
    --project=${PROJECT_ID} \
    --title="CMS Automation Secrets Reader" \
    --description="Read-only access to CMS automation secrets" \
    --permissions=secretmanager.versions.access,secretmanager.versions.get \
    --stage=GA

# 授予角色
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="projects/${PROJECT_ID}/roles/cmsAutomationSecretsReader"
```

---

## 成本估算

### GCP Secret Manager 定價

**存儲成本**：
- 每個活躍 secret 版本: $0.06/月
- 6 個 secrets × $0.06 = **$0.36/月**

**訪問成本**：
- 前 10,000 次訪問: 免費
- 之後每 10,000 次訪問: $0.03

**帶緩存的實際成本** (5分鐘 TTL)：
- 每天 ~1000 次應用重啟/緩存過期
- 每月 ~30,000 次訪問
- 30,000 次 × $0.03/10,000 = **$0.09/月**

**總成本**: $0.36 + $0.09 = **~$0.45/月** 💰

對比：
- AWS Secrets Manager: ~$5-10/月
- HashiCorp Vault 自托管: ~$15-30/月（EC2成本）

---

## Secret 輪換

### 手動輪換

```bash
# 添加新版本
echo -n "new-api-key-value" | \
    gcloud secrets versions add ANTHROPIC_API_KEY \
    --data-file=- \
    --project=${PROJECT_ID}

# 禁用舊版本（可選）
gcloud secrets versions disable 1 \
    --secret=ANTHROPIC_API_KEY \
    --project=${PROJECT_ID}

# 應用會自動使用最新版本（緩存過期後）
```

### 自動輪換（使用 Cloud Functions）

```python
# functions/rotate_secret.py
from google.cloud import secretmanager
import anthropic

def rotate_anthropic_key(event, context):
    """輪換 Anthropic API Key"""
    # 1. 生成新 key（如果 API 支持）
    # 2. 添加新版本到 Secret Manager
    # 3. 測試新 key
    # 4. 如果成功，禁用舊版本
    pass
```

設置 Cloud Scheduler 定期觸發：

```bash
gcloud scheduler jobs create http rotate-secrets \
    --schedule="0 0 1 * *" \
    --uri="https://YOUR_REGION-YOUR_PROJECT.cloudfunctions.net/rotate_anthropic_key" \
    --http-method=POST
```

---

## 監控和審計

### 啟用審計日誌

```bash
# 審計日誌會自動記錄所有 secret 訪問
# 在 Cloud Logging 中查看
```

### 查看訪問日誌

```bash
# 查看最近的 secret 訪問
gcloud logging read \
    "resource.type=secretmanager.googleapis.com/Secret
     AND protoPayload.methodName=AccessSecretVersion" \
    --limit=50 \
    --format=json
```

### 設置告警

```yaml
# alerting-policy.yaml
displayName: "Secret Access Spike"
conditions:
  - displayName: "High secret access rate"
    conditionThreshold:
      filter: 'resource.type="secretmanager.googleapis.com/Secret"'
      comparison: COMPARISON_GT
      thresholdValue: 1000
      duration: "60s"
notificationChannels:
  - "projects/PROJECT_ID/notificationChannels/CHANNEL_ID"
```

---

## 故障排除

### 問題 1: Permission Denied

**錯誤**:
```
google.api_core.exceptions.PermissionDenied: 403 Permission denied
```

**解決**:
```bash
# 檢查服務帳戶權限
gcloud projects get-iam-policy ${PROJECT_ID} \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT_EMAIL}"

# 授予權限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"
```

### 問題 2: Secret Not Found

**錯誤**:
```
google.api_core.exceptions.NotFound: 404 Secret not found
```

**解決**:
```bash
# 列出所有 secrets
gcloud secrets list --project=${PROJECT_ID}

# 檢查 secret 名稱和前綴
echo "Looking for: ${GCP_SECRET_PREFIX}ANTHROPIC_API_KEY"

# 創建缺失的 secret
gcloud secrets create ANTHROPIC_API_KEY \
    --replication-policy="automatic" \
    --project=${PROJECT_ID}
```

### 問題 3: Application Default Credentials 未找到

**錯誤**:
```
google.auth.exceptions.DefaultCredentialsError
```

**解決**:
```bash
# 方法 A: 設置憑證文件
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# 方法 B: 使用 gcloud 登錄
gcloud auth application-default login

# 方法 C: 在 GCP 上運行（自動使用實例服務帳戶）
```

---

## 最佳實踐

### ✅ 做

1. **使用 Workload Identity**（在 GKE/Cloud Run 上）
2. **啟用審計日誌**（追蹤所有訪問）
3. **使用緩存**（減少 API 調用和成本）
4. **定期輪換 secrets**（每 90 天）
5. **使用環境前綴**（區分 dev/staging/prod）
6. **監控訪問模式**（檢測異常）

### ❌ 不要

1. **不要提交服務帳戶密鑰到 git**
2. **不要在日誌中記錄 secret 值**
3. **不要給過多權限**（最小權限原則）
4. **不要在多個環境共享 secrets**
5. **不要硬編碼 project ID**（使用環境變量）

---

## 遷移檢查清單

### 遷移前

- [ ] GCP Secret Manager API 已啟用
- [ ] 服務帳戶已創建並配置權限
- [ ] 所有 secrets 已創建在 GCP
- [ ] 本地測試已通過

### 遷移中

- [ ] 更新 `.env` 文件配置
- [ ] 設置 `CREDENTIAL_STORAGE_BACKEND=gcp_secret_manager`
- [ ] 設置 `GCP_PROJECT_ID`
- [ ] 設置 `GOOGLE_APPLICATION_CREDENTIALS`（本地）
- [ ] 測試應用程序啟動
- [ ] 測試 credential 讀取

### 遷移後

- [ ] 驗證所有功能正常
- [ ] 從 `.env` 中刪除敏感值
- [ ] 設置審計日誌
- [ ] 設置監控告警
- [ ] 文檔更新
- [ ] 團隊培訓

---

## 相關文檔

- [Security Architecture](/backend/docs/SECURITY_ARCHITECTURE.md)
- [Configuration Guide](/CONFIGURATION_COMPLETED.md)
- [GCP Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)

---

**版本**: 1.0
**最後更新**: 2025-11-03
**狀態**: 生產就緒 ✅
