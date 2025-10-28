# WordPress 测试环境使用指南

本文档说明如何搭建和使用 WordPress 测试环境进行自动化测试。

## 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [启动测试环境](#启动测试环境)
- [停止测试环境](#停止测试环境)
- [测试环境信息](#测试环境信息)
- [常见问题](#常见问题)
- [高级配置](#高级配置)

---

## 快速开始

```bash
# 1. 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 2. 等待初始化完成 (约 1-2 分钟)
docker-compose -f docker-compose.test.yml logs -f wp-cli

# 3. 访问 WordPress
open http://localhost:8000/wp-admin

# 4. 登录
# 用户名: admin
# 密码: password
```

---

## 环境要求

### 必需软件

- **Docker** >= 20.10
- **Docker Compose** >= 2.0

### 端口要求

确保以下端口未被占用：

- `8000`: WordPress 前台和后台
- `8081`: phpMyAdmin (可选，仅在 debug profile 启用时)

---

## 启动测试环境

### 标准启动

```bash
# 启动 WordPress + MySQL
docker-compose -f docker-compose.test.yml up -d

# 查看日志
docker-compose -f docker-compose.test.yml logs -f
```

### 首次启动

首次启动时，系统会自动：

1. 下载 WordPress 和 MySQL Docker 镜像
2. 创建数据库
3. 安装 WordPress
4. 安装并激活经典编辑器 (Classic Editor)
5. 安装并激活 Yoast SEO
6. 创建测试分类和标签
7. 配置基本设置

**预计时间**: 3-5 分钟

### 查看初始化进度

```bash
# 查看 WP-CLI 容器日志
docker-compose -f docker-compose.test.yml logs -f wp-cli
```

当你看到以下消息时，表示初始化完成：

```
✓ 初始化完成！可以开始测试了。
```

---

## 停止测试环境

### 停止但保留数据

```bash
docker-compose -f docker-compose.test.yml stop
```

### 停止并删除容器 (保留数据卷)

```bash
docker-compose -f docker-compose.test.yml down
```

### 完全清理 (删除所有数据)

```bash
# 警告：这将删除所有测试数据！
docker-compose -f docker-compose.test.yml down -v
```

---

## 测试环境信息

### 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| WordPress 前台 | http://localhost:8000 | 网站首页 |
| WordPress 后台 | http://localhost:8000/wp-admin | 管理后台 |
| phpMyAdmin | http://localhost:8081 | 数据库管理 (debug mode) |

### 登录凭证

**WordPress 管理员:**
- 用户名: `admin`
- 密码: `password`

**数据库:**
- 主机: `db` (容器内) 或 `localhost` (主机)
- 数据库名: `wordpress`
- 用户名: `wordpress`
- 密码: `wordpress`

**数据库 Root:**
- 用户名: `root`
- 密码: `rootpassword`

### 已安装插件

- **Classic Editor** (经典编辑器) - 已激活
- **Yoast SEO** - 已激活

### 测试数据

**预创建的分类:**
- 技术
- 教程
- 测试

**预创建的标签:**
- Playwright
- 自动化
- 测试
- WordPress

---

## 运行测试

### 使用 Playwright 测试

```bash
# 确保测试环境已启动
docker-compose -f docker-compose.test.yml up -d

# 激活虚拟环境
source .venv/bin/activate

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行 E2E 测试
pytest tests/e2e/ -v -m e2e
```

### 使用 pytest markers

```bash
# 只运行 WordPress 相关测试
pytest -m wordpress

# 只运行选择器验证测试
pytest -m validator

# 跳过慢速测试
pytest -m "not slow"
```

---

## 常见问题

### Q: 端口 8000 已被占用怎么办？

**A:** 修改 `docker-compose.test.yml` 中的端口映射：

```yaml
wordpress:
  ports:
    - "8001:80"  # 改为 8001 或其他未占用端口
```

### Q: WordPress 初始化失败怎么办？

**A:** 尝试以下步骤：

```bash
# 1. 停止所有容器
docker-compose -f docker-compose.test.yml down

# 2. 清理数据卷
docker-compose -f docker-compose.test.yml down -v

# 3. 重新启动
docker-compose -f docker-compose.test.yml up -d

# 4. 查看日志
docker-compose -f docker-compose.test.yml logs -f wp-cli
```

### Q: 如何重置 WordPress 到初始状态？

**A:** 删除数据卷并重新启动：

```bash
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

### Q: 如何访问 WordPress 容器内部？

**A:** 使用 docker exec：

```bash
# 进入 WordPress 容器
docker exec -it cms_test_wordpress bash

# 或者使用 WP-CLI
docker exec -it cms_test_wordpress wp --allow-root post list
```

### Q: 如何查看数据库内容？

**A:** 有两种方式：

```bash
# 方式 1: 使用 phpMyAdmin (启用 debug profile)
docker-compose -f docker-compose.test.yml --profile debug up -d phpmyadmin
# 访问 http://localhost:8081

# 方式 2: 使用 MySQL CLI
docker exec -it cms_test_mysql mysql -u wordpress -pwordpress wordpress
```

### Q: 测试失败后如何清理测试文章？

**A:** 使用 WP-CLI 批量删除：

```bash
# 删除所有文章 (保留默认页面)
docker exec cms_test_wordpress \
  wp post delete $(wp post list --post_type=post --format=ids --allow-root) \
  --force --allow-root
```

---

## 高级配置

### 启用 phpMyAdmin (调试模式)

```bash
docker-compose -f docker-compose.test.yml --profile debug up -d
```

访问: http://localhost:8081

### 修改 WordPress 配置

编辑 `docker-compose.test.yml` 中的环境变量：

```yaml
wordpress:
  environment:
    WORDPRESS_CONFIG_EXTRA: |
      /* 你的自定义配置 */
      define('WP_DEBUG', true);
      define('WP_DEBUG_LOG', true);
```

### 安装额外插件

**方式 1: 修改 setup.sh**

编辑 `tests/docker/wordpress/setup.sh`，添加：

```bash
wp plugin install [plugin-name] --activate --allow-root
```

**方式 2: 使用 docker exec**

```bash
docker exec cms_test_wordpress \
  wp plugin install [plugin-name] --activate --allow-root
```

### 导入测试数据

```bash
# 导入 WXR 文件
docker exec cms_test_wordpress \
  wp import test-data.xml --authors=create --allow-root

# 或者使用 SQL 文件
docker exec -i cms_test_mysql mysql -u wordpress -pwordpress wordpress < backup.sql
```

### 备份测试数据

```bash
# 备份数据库
docker exec cms_test_mysql \
  mysqldump -u wordpress -pwordpress wordpress > backup.sql

# 备份 WordPress 文件
docker cp cms_test_wordpress:/var/www/html ./wordpress_backup
```

---

## 选择器验证

### 验证选择器是否有效

```bash
# 运行选择器验证测试
pytest tests/integration/test_selectors.py -v

# 只验证关键选择器
pytest tests/integration/test_selectors.py::test_critical_selectors -v
```

### 更新选择器

如果 WordPress 更新导致选择器失效：

1. 启动测试环境
2. 使用浏览器开发者工具检查新的选择器
3. 更新 `config/selectors.yaml`
4. 运行验证测试

---

## 性能测试

```bash
# 测试文章发布性能
pytest tests/performance/ -v

# 设置目标时间
pytest tests/performance/ -v --benchmark-max-time=180
```

---

## 持续集成 (CI)

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start WordPress Test Environment
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 120  # 等待初始化

      - name: Run Tests
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements.txt
          pytest tests/ -v

      - name: Cleanup
        if: always()
        run: docker-compose -f docker-compose.test.yml down -v
```

---

## 故障排除

### 检查容器状态

```bash
docker-compose -f docker-compose.test.yml ps
```

### 查看所有日志

```bash
docker-compose -f docker-compose.test.yml logs
```

### 重启特定服务

```bash
# 重启 WordPress
docker-compose -f docker-compose.test.yml restart wordpress

# 重启数据库
docker-compose -f docker-compose.test.yml restart db
```

### 检查网络连接

```bash
# 检查容器网络
docker network inspect cms_test_network

# 测试容器间连通性
docker exec cms_test_wordpress ping db
```

---

## 资源清理

### 定期清理

```bash
# 清理未使用的 Docker 资源
docker system prune -a

# 清理测试环境数据卷
docker volume ls | grep cms_test | awk '{print $2}' | xargs docker volume rm
```

---

## 技术支持

如果遇到问题：

1. 查看 [常见问题](#常见问题)
2. 检查 Docker 日志
3. 提交 Issue 到项目仓库

---

## 相关文档

- [WordPress Publishing Plan](../specs/001-cms-automation/wordpress-publishing-plan.md)
- [WordPress Publishing Testing](../specs/001-cms-automation/wordpress-publishing-testing.md)
- [Selectors Configuration](../config/selectors.yaml)
- [Instructions Configuration](../config/instructions.yaml)
