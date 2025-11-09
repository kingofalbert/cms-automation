# 环境变量持久化问题解决指南

## 问题描述

由于之前的 `export` 命令,某些环境变量被持久化为 JSON 格式:
- `ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]`
- `CELERY_ACCEPT_CONTENT=["json"]`

这导致后端无法启动，因为 Pydantic Settings 无法正确解析这些值。

## 根本原因

环境变量在当前 shell 会话中被设置,并且会被子进程继承。即使使用 `env -i` 也无法完全清除。

## 解决方案

### 方案 1: 使用新的终端会话 (推荐)

1. **打开一个全新的终端窗口**
2. 进入项目目录:
   ```bash
   cd /home/kingofalbert/projects/CMS/backend
   ```
3. 使用干净启动脚本:
   ```bash
   ./start-backend-clean.sh
   ```

### 方案 2: 手动清理并启动

在当前终端中执行:

```bash
# 1. 清理错误的环境变量
unset ALLOWED_ORIGINS
unset CELERY_ACCEPT_CONTENT
unset CELERY_RESULT_BACKEND
unset CELERY_BROKER_URL

# 2. 加载正确的配置
cd /home/kingofalbert/projects/CMS/backend
set -a
source .env
set +a

# 3. 激活虚拟环境
source ../.venv/bin/activate

# 4. 启动后端
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 方案 3: 使用 E2E 测试脚本

对于 E2E 测试,可以在新终端中运行:

```bash
cd /home/kingofalbert/projects/CMS/backend
./start-backend-e2e-clean.sh
```

这个脚本会:
- 清理所有环境变量
- 从 `.env` 加载新配置
- 启动后端并等待就绪
- 输出日志到 `/tmp/backend-e2e-clean.log`

## 验证配置

### 检查环境变量格式

```bash
# 正确的格式 (逗号分隔)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# 错误的格式 (JSON)
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### 测试配置加载

```bash
cd /home/kingofalbert/projects/CMS/backend
set -a && source .env && set +a
echo "ALLOWED_ORIGINS=$ALLOWED_ORIGINS"
echo "CELERY_ACCEPT_CONTENT=$CELERY_ACCEPT_CONTENT"
```

应该输出:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,...
CELERY_ACCEPT_CONTENT=json
```

## 配置文件说明

### .env 文件格式

环境变量应该使用以下格式:

```bash
# ✅ 正确 - 逗号分隔的字符串
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# ✅ 正确 - 单个值
CELERY_ACCEPT_CONTENT=json

# ❌ 错误 - JSON 格式
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]
CELERY_ACCEPT_CONTENT=["json"]
```

### Settings.py 字段验证器

`src/config/settings.py` 中的验证器会自动处理逗号分隔的字符串:

```python
@field_validator("ALLOWED_ORIGINS", mode="before")
@classmethod
def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
    """Parse ALLOWED_ORIGINS from comma-separated string."""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",")]
    return v
```

## 可用的启动脚本

### 1. start-backend-clean.sh
干净的后端启动脚本,适用于开发环境:
```bash
./start-backend-clean.sh
```

特点:
- 清理环境变量
- 从 `.env` 加载配置
- 前台运行 uvicorn
- 支持热重载

### 2. start-backend-e2e-clean.sh
E2E 测试专用启动脚本:
```bash
./start-backend-e2e-clean.sh
```

特点:
- 在后台启动
- 自动等待后端就绪
- 日志输出到 `/tmp/backend-e2e-clean.log`
- 健康检查

## 常见问题

### Q: 为什么 export 会持久化变量?

A: 在 bash 中,`export` 命令会将变量导出到当前 shell 及其所有子进程。这些变量会一直存在,直到:
- Shell 会话关闭
- 使用 `unset` 明确删除
- 启动新的 shell 会话

### Q: env -i 为什么不能完全清理?

A: `env -i` 会清理大部分环境变量,但某些变量(如 PATH, HOME, USER)需要保留以确保脚本正常工作。我们的脚本需要这些基础变量。

### Q: 如何永久防止这个问题?

A:
1. **不要使用 export** - 直接在 `.env` 文件中配置
2. **使用正确的格式** - 逗号分隔,不要用 JSON
3. **使用提供的启动脚本** - 它们会正确加载配置
4. **在新终端中测试** - 避免继承错误的环境变量

## 检查清单

启动后端前,请确认:

- [ ] 已创建 `.env` 文件
- [ ] 环境变量使用逗号分隔格式(不是 JSON)
- [ ] Anthropic API Key 已从 Docker 容器中提取
- [ ] 数据库 URL 指向 Supabase
- [ ] 在新的终端会话中运行(或已 unset 旧变量)

## 相关文件

- `.env` - 环境配置文件
- `.env.example` - 配置模板
- `src/config/settings.py` - Settings 类定义
- `start-backend-clean.sh` - 开发启动脚本
- `start-backend-e2e-clean.sh` - E2E 测试启动脚本
- `CONFIGURATION_COMPLETE.md` - 完整配置文档

---

**最后更新**: 2025-11-09
**状态**: ✅ 解决方案已验证
