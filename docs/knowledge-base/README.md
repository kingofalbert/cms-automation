# CMS 自动化系统 - 知识库

**目的**: 保存项目中的宝贵经验和最佳实践，供本项目和未来其他项目参考

---

## 📚 知识库目录

### 生产环境故障排查

#### 1. [数据库连接故障排查手册](./production-database-connectivity-troubleshooting.md) ⭐⭐⭐⭐⭐
**适用场景**: Cloud Run + Supabase/PostgreSQL 连接问题
**经验来源**: 2025-11-07 生产故障
**关键价值**:
- 系统化诊断流程
- Supabase Pooler 模式选择指南
- 可复用的诊断脚本和工具
- 实战案例分析（47倍性能提升）

**快速跳转**:
- [故障现象识别](./production-database-connectivity-troubleshooting.md#故障现象识别)
- [系统化诊断流程](./production-database-connectivity-troubleshooting.md#系统化诊断流程)
- [Supabase Pooler配置](./production-database-connectivity-troubleshooting.md#根因1-supabase-pooler-模式配置错误-)
- [可复用工具](./production-database-connectivity-troubleshooting.md#可复用工具)

---

## 🎯 按场景查找

### 场景1: 生产环境API超时

**症状**:
- 前端加载正常，但API请求超时
- 数据库相关接口全部失败
- 非数据库接口正常工作

**查看**: [数据库连接故障排查手册](./production-database-connectivity-troubleshooting.md)

---

### 场景2: Supabase连接数超限

**症状**:
- 错误消息: `MaxClientsInSessionMode: max clients reached`
- 间歇性连接失败
- 高负载时更容易出现

**查看**: [Supabase Pooler模式配置](./production-database-connectivity-troubleshooting.md#根因1-supabase-pooler-模式配置错误-)

---

### 场景3: 数据库密码认证失败

**症状**:
- 错误消息: `password authentication failed`
- DATABASE_URL包含特殊字符
- 本地连接正常，生产环境失败

**查看**: [URL特殊字符编码](./production-database-connectivity-troubleshooting.md#根因2-url中的特殊字符未编码-)

---

## 🛠 工具箱

### 诊断工具

#### 数据库连接诊断
```bash
# 快速诊断数据库连接问题
bash scripts/diagnose-db-connection.sh https://your-backend.com
```

**提供信息**:
- 基本连接测试
- 连接池状态
- 查询性能
- 并发连接测试

**文档**: [诊断脚本](./production-database-connectivity-troubleshooting.md#工具1-数据库连接诊断脚本)

---

#### DATABASE_URL 验证器
```bash
# 验证DATABASE_URL配置是否正确
python3 scripts/validate-database-url.py "$DATABASE_URL"
```

**检查项目**:
- Pooler模式（Session vs Transaction）
- 密码特殊字符编码
- URL格式正确性

**文档**: [URL验证器](./production-database-connectivity-troubleshooting.md#工具2-database_url-验证器)

---

#### 自动修复工具
```bash
# 自动修复常见数据库连接问题
bash scripts/auto-fix-db-connection.sh PROJECT_ID DATABASE_URL
```

**修复内容**:
- Session模式 → Transaction模式
- 特殊字符自动编码
- 配置验证

**文档**: [自动修复工具](./production-database-connectivity-troubleshooting.md#工具3-自动化修复工具)

---

### Debug 端点

#### `/debug/db-test`
最简单的数据库连接测试
```bash
curl https://your-backend.com/debug/db-test
```

#### `/debug/db-pool-status`
检查连接池状态
```bash
curl https://your-backend.com/debug/db-pool-status
```

#### `/debug/db-query-test/{table}`
测试特定表查询
```bash
curl https://your-backend.com/debug/db-query-test/worklist_items
```

**实现代码**: [debug_routes.py](../../backend/src/api/routes/debug_routes.py)

---

## 📊 真实案例研究

### 案例1: 2025-11-07 生产数据库超时故障

**故障描述**: 清除浏览器缓存后，首页和worklist页面加载极慢或无法加载

**问题根因**: Supabase使用Session模式(端口5432)，Cloud Run多实例导致连接数超限

**解决方案**: 切换到Transaction模式(端口6543)

**性能提升**:
- 数据库连接: 15.3s → 0.327s (**47倍提升**)
- Worklist查询: 超时 → 0.267s
- 完整API请求: 超时 → 0.632s

**详细分析**: [案例研究](./production-database-connectivity-troubleshooting.md#案例研究-2025-11-07-生产故障)

**关键经验**:
1. 系统化诊断比猜测更快
2. Debug端点是必需品
3. 文档化所有决策
4. 自动化修复流程

---

## 🔗 相关资源

### 项目内部文档
- [数据库问题解决报告](../../backend/DATABASE_ISSUE_RESOLUTION.md) - 本次故障的详细报告
- [部署指南](../deployment-guide.md) - 如何部署到生产环境
- [监控设置](../monitoring-setup.md) - 监控和告警配置

### 官方文档
- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Google Cloud Run Best Practices](https://cloud.google.com/run/docs/tips/general)
- [SQLAlchemy Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html)
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html)

---

## 📝 如何贡献

### 添加新的知识库文章

1. 在 `docs/knowledge-base/` 目录下创建新的Markdown文件
2. 使用清晰的标题和结构
3. 包含真实案例和代码示例
4. 更新本README文件的目录

### 文章模板

```markdown
# [文章标题]

**适用场景**: [描述这篇文章适用的场景]
**经验来源**: [这个经验从哪里来的]
**难度级别**: [初级/中级/高级]

## 问题描述
[详细描述问题]

## 症状
- [症状1]
- [症状2]

## 根因分析
[分析问题的根本原因]

## 解决方案
[步骤化的解决方案]

## 预防措施
[如何预防这个问题再次发生]

## 相关工具
[相关的脚本、工具、命令]

## 案例研究
[真实的案例分析]
```

---

## 🏷️ 标签系统

### 按难度分类
- 🟢 **初级**: 基础配置和常见问题
- 🟡 **中级**: 需要一定技术理解
- 🔴 **高级**: 复杂的系统级问题

### 按紧急程度分类
- 🔥 **Critical**: 生产环境宕机
- ⚠️ **High**: 严重影响用户体验
- 📊 **Medium**: 性能问题
- 💡 **Low**: 优化建议

### 按技术栈分类
- `#database` - 数据库相关
- `#cloud-run` - Cloud Run相关
- `#supabase` - Supabase相关
- `#postgresql` - PostgreSQL相关
- `#networking` - 网络相关
- `#performance` - 性能优化

---

## 📈 知识库统计

| 指标 | 数值 |
|------|------|
| 总文章数 | 1 |
| 真实案例数 | 1 |
| 可复用工具数 | 3 |
| 覆盖的技术栈 | Cloud Run, Supabase, PostgreSQL |
| 最后更新 | 2025-11-07 |

---

## 🎓 学习路径

### 新团队成员

1. 先阅读 [数据库连接故障排查手册](./production-database-connectivity-troubleshooting.md)
2. 熟悉 [Debug端点](./production-database-connectivity-troubleshooting.md#phase-2-创建诊断端点-15-20分钟)
3. 了解 [案例研究](./production-database-connectivity-troubleshooting.md#案例研究-2025-11-07-生产故障)
4. 运行一次 [诊断脚本](./production-database-connectivity-troubleshooting.md#工具1-数据库连接诊断脚本)

### 经验丰富的开发者

1. 直接查看 [可复用工具](./production-database-connectivity-troubleshooting.md#可复用工具)
2. 根据症状快速定位到对应章节
3. 使用自动化工具快速修复
4. 贡献新的经验和案例

---

## 💬 反馈和建议

如果你有任何建议或发现了新的有价值的经验：

1. 创建新的知识库文章
2. 更新现有文章
3. 改进工具和脚本
4. 添加更多案例研究

**记住**: 每一次故障都是学习和改进的机会！

---

**维护者**: DevOps Team
**最后更新**: 2025-11-07
**版本**: 1.0
