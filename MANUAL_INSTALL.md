# 手动安装中文字体

**当前状态**: ⚠️ 系统中未安装中文字体（0个）
**需要**: sudo 权限（需要输入密码）

---

## 📋 快速安装步骤

### 方法1: 使用安装脚本（推荐）

在终端中执行：

```bash
cd /home/kingofalbert/projects/CMS
./scripts/install-chinese-fonts.sh
```

输入您的 sudo 密码后，脚本将自动：
- 更新包列表
- 安装 Noto CJK、文泉驿正黑、文泉驿微米黑
- 刷新字体缓存
- 验证安装结果

**预计时间**: 3-5 分钟
**磁盘空间**: 约 100 MB

---

### 方法2: 手动命令（如果脚本失败）

```bash
# 1. 更新包列表
sudo apt-get update

# 2. 安装中文字体包
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei fonts-wqy-microhei

# 3. 刷新字体缓存
fc-cache -fv

# 4. 验证安装
fc-list :lang=zh | wc -l
```

如果看到数字大于 0，说明安装成功！

---

## ✅ 验证安装

安装完成后，运行以下命令验证：

```bash
# 检查已安装的中文字体数量
fc-list :lang=zh | wc -l

# 列出前 5 个中文字体
fc-list :lang=zh | head -5

# 重新运行生产环境测试，查看中文显示
source .venv/bin/activate
python tests/prod_env_test_v2.py
```

---

## 📸 对比截图

### 安装前
- 中文显示为: □□□□
- 截图无法阅读

### 安装后
- 中文显示为: 紐約報社-Ping Xie
- 截图清晰可读

---

## 🆘 如果遇到问题

### 问题1: 密码输入失败
**解决**: 确保您的用户在 sudo 组中
```bash
groups $USER
# 应该看到 "sudo" 在列表中
```

### 问题2: 网络连接问题
**解决**: 检查网络连接，或使用国内镜像
```bash
# 测试网络
ping -c 3 archive.ubuntu.com
```

### 问题3: 磁盘空间不足
**解决**: 清理临时文件
```bash
sudo apt-get clean
df -h
```

---

## 💡 为什么需要中文字体？

虽然 Playwright 自动化功能不依赖字体，但中文字体可以：

✅ 让截图显示清晰的中文（而不是方块）
✅ 改善审计日志可读性
✅ 提升调试体验
✅ 支持文本内容验证

**强烈建议安装！** 只需 5 分钟，长期受益。

---

## 🎯 下一步

安装字体后，继续执行：

```bash
# 重新激活虚拟环境
source .venv/bin/activate

# 运行生产环境测试
python tests/prod_env_test_v2.py

# 查看截图（应该能看到清晰的中文）
ls -lh /tmp/prod_*.png
```

---

**需要帮助？** 查看 `docs/CHINESE_FONT_SUPPORT.md` 获取更多信息。
