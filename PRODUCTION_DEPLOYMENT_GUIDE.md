# 生产环境部署指南

## 📋 部署前确认

### ✅ 已完成的准备工作

- [x] 代码已提交到 GitHub (commit: 55516b6)
- [x] 所有测试通过 (4/4 integration tests)
- [x] 代码审查完成
- [x] 文档编写完成
- [x] 监控系统就绪

### 🎯 部署目标

将 Google Docs HTML 解析功能部署到生产环境,提升文档格式保留能力。

---

## 🚀 快速部署 (推荐)

### 方式 1: CI/CD 自动部署

如果你的项目配置了 CI/CD:

```bash
# 确认 main 分支最新
git pull origin main

# 触发部署 (根据你的 CI/CD 配置)
# GitHub Actions, Jenkins, GitLab CI 等会自动执行
```

### 方式 2: 手动部署

```bash
# 1. 拉取最新代码
cd /path/to/CMS
git pull origin main

# 2. 确认最新 commit
git log --oneline -1
# 应该看到: 55516b6 fix(google-drive): Upgrade to HTML export...

# 3. 如果使用 Docker
docker-compose down
docker-compose build backend
docker-compose up -d

# 4. 如果使用虚拟环境
source .venv/bin/activate
pip install -r backend/requirements.txt  # 如果有新依赖
python backend/manage.py migrate  # 如果有数据库变更

# 5. 重启服务
systemctl restart cms-backend  # 根据你的服务名
```

---

## 📊 部署后验证

### 1. 健康检查 (1分钟内)

```bash
# 检查服务状态
systemctl status cms-backend

# 检查 API 健康
curl https://your-api-domain.com/health

# 查看最新日志
tail -f /var/log/cms-backend.log
```

期望结果: 服务正常运行,无错误日志

### 2. 功能验证 (5分钟内)

```bash
# 触发一次 Google Drive 同步测试
curl -X POST https://your-api-domain.com/api/v1/sync/google-drive \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

期望结果:
- HTTP 200 响应
- 返回同步统计信息
- 日志中包含 `google_drive_sync_metrics`

### 3. 监控指标检查 (15分钟内)

在日志中查找以下指标:

```bash
# 查找监控指标日志
grep "google_drive_sync_metrics" /var/log/cms-backend.log | tail -1 | jq .
```

期望指标:
```json
{
  "export_success_rate": ">= 0.95",
  "parsing_success_rate": ">= 0.98",
  "avg_parsing_time_ms": "< 100",
  "yaml_detection_rate": "> 0"
}
```

---

## ⚠️ 回滚方案

如果出现问题,立即执行回滚:

### 快速回滚

```bash
# 1. 回滚到上一个版本
git revert 55516b6
git push origin main

# 2. 重新部署
# (根据你的部署方式重新执行部署步骤)

# 3. 验证回滚成功
curl https://your-api-domain.com/health
```

### 回滚触发条件

立即回滚如果:
- ❌ 导出失败率 > 20%
- ❌ 解析失败率 > 10%
- ❌ 服务响应时间增加 > 200%
- ❌ 数据库错误激增
- ❌ 收到 5+ 用户投诉

---

## 📈 监控和告警

### 关键指标

在部署后 24 小时内密切监控:

| 指标 | 正常范围 | 告警阈值 | 检查频率 |
|-----|---------|----------|----------|
| 导出成功率 | >= 95% | < 90% | 每小时 |
| 解析成功率 | >= 98% | < 95% | 每小时 |
| 平均解析时间 | < 100ms | > 200ms | 每小时 |
| 错误率 | < 2% | > 5% | 实时 |
| API 响应时间 | < 2s | > 5s | 实时 |

### 日志查询命令

```bash
# 查看所有 Google Drive 相关日志
grep "google_drive" /var/log/cms-backend.log | tail -50

# 查看错误日志
grep "ERROR.*google_drive" /var/log/cms-backend.log

# 查看性能指标
grep "google_drive_sync_metrics" /var/log/cms-backend.log | \
  jq '{success_rate: .export_success_rate, parse_time: .avg_parsing_time_ms}'

# 查看 YAML 检测率
grep "google_drive_sync_metrics" /var/log/cms-backend.log | \
  jq .yaml_detection_rate
```

---

## 🔧 故障排查

### 常见问题

#### 问题 1: 导出失败

**症状**: `export_success_rate` 低于 90%

**排查**:
```bash
# 检查 Google Drive API 配置
grep "GOOGLE_DRIVE" backend/.env

# 检查 Service Account 权限
# 查看错误日志
grep "google_drive_fetch_failed" /var/log/cms-backend.log
```

**解决**:
- 验证 Google Service Account 凭证
- 检查 Google Drive Folder ID 配置
- 确认 API 配额未超限

#### 问题 2: 解析失败

**症状**: `parsing_success_rate` 低于 95%

**排查**:
```bash
# 查看解析错误
grep "html_parsing_failed" /var/log/cms-backend.log

# 检查 fallback 使用率
grep "parsing_fallback" /var/log/cms-backend.log | wc -l
```

**解决**:
- 检查是否有特殊 HTML 结构无法解析
- 验证 fallback 机制是否正常工作
- 收集失败案例用于优化

#### 问题 3: 性能问题

**症状**: `avg_parsing_time_ms` > 200ms

**排查**:
```bash
# 查看慢查询
grep "parsing_time_ms" /var/log/cms-backend.log | \
  jq 'select(.parsing_time_ms > 100)' | head -10
```

**解决**:
- 检查是否有超大文档 (> 1MB)
- 考虑添加解析缓存
- 优化 HTML 解析器性能

---

## 📞 支持联系

### 技术支持
- **Email**: tech-support@your-company.com
- **Slack**: #cms-automation-support
- **On-call**: [On-call rotation]

### 紧急情况
- **24/7 Hotline**: [Emergency phone]
- **PagerDuty**: [PagerDuty link]

---

## ✅ 部署检查清单

完成以下检查项后再部署:

- [ ] 代码已合并到 main 分支
- [ ] 所有测试通过
- [ ] 代码审查批准
- [ ] 备份当前配置
- [ ] 通知相关团队
- [ ] 准备好回滚计划
- [ ] 监控系统就绪

**部署执行人**: _______________
**部署时间**: _______________  
**验证人**: _______________
**验证时间**: _______________

---

## 📝 部署记录

### 部署详情

```
Commit: 55516b6
Branch: main
Date: 2025-11-07
Deployer: [Your Name]
Environment: Production
Status: ___________
```

### 验证结果

```
Health Check: [ ] Pass  [ ] Fail
Functional Test: [ ] Pass  [ ] Fail
Metrics Check: [ ] Pass  [ ] Fail
Performance: [ ] Normal  [ ] Degraded  [ ] Critical
```

### 备注

```
[记录任何特殊情况、问题或观察]
```

---

**最后更新**: 2025-11-07
**版本**: 1.0
**状态**: ✅ 准备就绪
