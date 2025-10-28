# WordPress 视觉自动化发布功能规格说明

**功能模块**: WordPress 后台发布自动化
**创建日期**: 2025-10-27
**最后更新**: 2025-10-27
**状态**: 规划中
**优先级**: P0（核心功能）

## 概述

本功能实现通过视觉自动化方法将文章和图片发布到 WordPress 后台（经典编辑器）。采用**两阶段实施策略**：

- **Phase 1 (MVP)**: 优先使用 **Anthropic Computer Use** 快速验证核心流程，确保功能完整性
- **Phase 2 (优化)**: 引入 **Playwright + Chrome DevTools** 进行成本优化，Computer Use 作为智能降级备选

### 核心价值

- **快速上线**: Computer Use 自然语言控制，无需复杂选择器配置
- **智能适应**: AI 视觉理解，自动应对页面变化
- **成本优化**: Phase 2 引入 Playwright 降低运行成本
- **完整流程**: 覆盖从登录到发布的所有 WordPress 后台操作
- **元数据完整性**: 支持 SEO 插件（Yoast SEO）、标签、分类、特色图片等
- **图片处理**: 自动上传、元数据填写、多尺寸裁切（缩略图、Facebook 分享图等）
- **审计追踪**: 每个关键步骤截图记录，便于调试和验证

---

## 技术选型决策

### 两阶段实施策略

#### 🚀 Phase 1: Computer Use MVP（优先实现）

**主方案：Anthropic Computer Use**

**选择理由**:
- ✅ **快速验证**: 自然语言指令，无需预先探测选择器
- ✅ **智能适应**: 通过视觉识别和自然语言理解适应页面变化
- ✅ **容错能力强**: 即使页面结构变化，仍能通过屏幕截图理解界面
- ✅ **开发效率高**: 直接编写指令模板，大幅缩短开发周期
- ✅ **功能完整**: 适合处理复杂的图片裁切等视觉化操作

**适用场景**:
- MVP 阶段快速验证核心流程
- 图片裁切等需要视觉判断的操作
- WordPress 后台可能频繁更新的环境
- 多站点支持（不同主题/插件配置）

**成本考量**:
- API 调用成本可控（单篇文章约 $0.10-0.30）
- 通过批量处理和缓存优化成本
- Phase 1 重点在功能验证，成本优化留待 Phase 2

#### 📊 Phase 2: Playwright 混合优化（成本优化）

**优化方案：Playwright + Computer Use 混合架构**

**引入 Playwright 的理由**:
- ✅ **成本极低**: 本地浏览器控制，运行成本几乎为零
- ✅ **性能优越**: 响应速度快，适合高频率操作
- ✅ **稳定可靠**: 基于 DOM 选择器，精确定位元素
- ✅ **代码可维护**: 结构化代码，易于版本控制

**混合策略**:
```
┌─────────────────────────────────────────┐
│  默认使用 Playwright（成本优化）          │
└─────────────────────────────────────────┘
                  │
                  ▼
          [Playwright 执行]
                  │
             [成功?]
              /      \
            Yes       No（3次重试失败）
             │         │
             ▼         ▼
        [继续]    [降级到 Computer Use]
                       │
                       ▼
                  [智能恢复]
```

**降级触发条件**（Phase 2）:
1. Playwright 连续 3 次尝试后仍无法定位关键元素
2. WordPress 后台界面发生重大更新
3. 出现非预期的弹窗或警告
4. 选择器验证失败率超过阈值

**成本优化效果**:
- 预计降低 80-90% 的运行成本
- 仅在必要时使用 Computer Use
- 保持功能完整性和可靠性

---

## 功能范围

### 阶段一：文章创建与基本内容设置

#### 1.1 导航至新增文章页面
**输入**: 已登录的 WordPress 后台仪表板
**输出**: 进入「新增文章」编辑器页面

**Playwright 实现要点**:
- 定位左侧菜单：`#menu-posts > a`
- 定位「新增文章」链接：`#menu-posts ul > li > a:has-text("新增文章")`
- 等待页面加载：`h1:has-text("新增文章")`

**Computer Use 指令模板**:
```
找到左側選單中帶有圖釘圖示且標籤為『文章』的項目，點擊它。
在展開的子選單中，找到並點擊標籤為『新增文章』的連結。
等待頁面載入完成，確認頁面頂部出現文字『新增文章』。
```

#### 1.2 输入文章标题
**输入**: 文章标题字符串（已通过 SEO 优化）
**输出**: 标题栏位填充完成

**验证**:
- 标题长度：50-60 字符（SEO 最佳实践）
- 特殊字符转义：`<` `>` `&` `"` `'`
- 确认输入框值与预期一致

#### 1.3 内容编辑器操作
**子功能**:
1. **切换到文字模式**（推荐）
   - 目的：贴上纯文本，避免格式污染
   - 选择器：`#content-html`

2. **贴入文章内文**
   - 使用 `fill()` 而非 `type()`（清除原有内容）
   - 验证部分内容：检查开头段落是否正确

3. **清除多余 HTML 标签**
   - 移除 `&nbsp;` 等非预期字符
   - 示例代码：
     ```javascript
     const content = await page.locator('#content').inputValue();
     const cleaned = content.replace(/&nbsp;/g, ' ');
     await page.locator('#content').fill(cleaned);
     ```

4. **简繁转换**（可选）
   - 依赖 WordPress 插件或外部工具
   - Playwright: 需提供插件按钮的准确选择器
   - Computer Use: 通过自然语言指令执行
   - ⚠️ **不确定性高**: 不同站点插件配置不同，建议预先在内容准备阶段完成转换

5. **切换回视觉模式**
   - 选择器：`#content-tmce`

6. **设置小标题（H2/H3）**
   - 在 TinyMCE 可视化编辑器中操作
   - ⚠️ **复杂度高**: Playwright 在可视化编辑器中选取文字需要 JavaScript 辅助
   - **建议**: 在内容准备阶段直接插入 HTML 标签（如 `<h2>小标题</h2>`），在文字模式下贴入

#### 1.4 元数据设置

##### 标签 (Tags)
**输入**: 标签数组 `["标签1", "标签2", "标签3"]`
**输出**: 标签已添加到文章

**Playwright 实现**:
```javascript
await page.locator('#new-tag-post_tag').fill('标签1,标签2,标签3');
await page.locator('input.button[value="新增"]').click();
await expect(page.locator('.tagchecklist')).toContainText('标签1');
```

**验证**:
- 确认标签出现在标签列表中
- 检查是否有重复标签
- 截图存档

##### 分类 (Categories)
**输入**: 分类名称数组 `["分类A", "分类B"]`
**输出**: 对应分类已勾选

**Playwright 实现**:
```javascript
await page.locator('label:has-text("分类A") input[type="checkbox"]').check();
await expect(page.locator('label:has-text("分类A") input[type="checkbox"]')).toBeChecked();
```

**注意事项**:
- 如果分类不存在，需先创建（或在失败时提示用户）
- 支持多层级分类（父分类 → 子分类）

##### SEO 插件配置 (Yoast SEO / Rank Math)
**输入**:
- 焦点关键字（Focus Keyword）
- SEO 标题（Meta Title）
- Meta 描述（Meta Description）

**Playwright 实现**:
```javascript
// Yoast SEO 示例
await page.locator('#yoast-google-preview-focus-keyword').fill('焦点关键字');
await page.locator('#yoast-google-preview-title').fill('SEO 标题');
await page.locator('#yoast-google-preview-description').fill('Meta 描述内容');
```

**验证**:
- 检查 Yoast/Rank Math 提供的长度指示器（绿色/橙色/红色）
- Meta 描述长度：150-160 字符
- SEO 标题长度：50-60 字符

#### 1.5 保存草稿
**目的**: 防止意外丢失，在继续上传图片前先保存

**Playwright 实现**:
```javascript
await page.locator('#save-post').click();
await page.waitForSelector('#message p:has-text("文章草稿已更新")');
```

---

### 阶段二：图片处理与上传

#### 2.1 定位图片插入点
**输入**: 内文中的插入位置（例如：第二段之后）
**输出**: 游标定位到目标位置

**Playwright 实现**（示意）:
```javascript
// TinyMCE 在 iframe 中
const frame = page.frameLocator('#content_ifr');
await frame.locator('p:nth-of-type(2)').click();
```

**挑战**:
- TinyMCE 编辑器在 iframe 内，需要使用 `frameLocator`
- 精确定位到段落之间可能需要 JavaScript 辅助

#### 2.2 打开媒体库
**Playwright 实现**:
```javascript
await page.locator('#insert-media-button').click();
await page.waitForSelector('.media-modal');
```

**验证**: 确认弹出窗口出现，标题为「插入媒体」

#### 2.3 上传图片文件
**输入**: 本地图片文件路径
**输出**: 图片上传完成，显示在媒体库中

**Playwright 实现**:
```javascript
await page.locator('button:has-text("上傳檔案")').click();
const fileChooserPromise = page.waitForEvent('filechooser');
await page.locator('button:has-text("選擇檔案")').click();
const fileChooser = await fileChooserPromise;
await fileChooser.setFiles('/path/to/image.jpg');
await page.waitForSelector('.media-modal .attachment.selected');
```

**支持格式**: JPG, PNG, GIF, WebP
**大小限制**: 参考 WordPress 配置（通常 2-10MB）

**错误处理**:
- 文件过大 → 提示用户或自动压缩
- 格式不支持 → 转换格式或跳过
- 上传失败 → 重试 3 次，失败则记录日志

#### 2.4 设置图片附件详细资料

**必填字段**:
1. **替代文字 (Alt Text)**: 用于 SEO 和无障碍访问
2. **标题 (Title)**: 图片标题
3. **说明 (Caption)**: 显示在图片下方的文字
4. **关键字 (Keywords)**: 逗号分隔，用于媒体库搜索
5. **攝影師/來源 (Photographer/Source)**: 版权信息

**Playwright 实现**:
```javascript
await page.locator('.media-modal .setting[data-setting="alt"] input').fill('替代文字');
await page.locator('.media-modal .setting[data-setting="title"] input').fill('图片标题');
await page.locator('.media-modal .setting[data-setting="caption"] textarea').fill('图片说明');
await page.locator('.media-modal input[id*="keywords"]').fill('关键字1,关键字2');
await page.locator('.media-modal input[id*="photographer"]').fill('攝影師姓名');
```

**注意事项**:
- ⚠️ **选择器不稳定**: 不同 WordPress 版本和插件可能改变字段 ID/class
- 建议使用 `data-setting` 属性（较稳定）
- **Computer Use 备选**: 如果选择器失效，用自然语言指令操作

#### 2.5 设置附件显示设定

**配置项**:
1. **对齐 (Align)**: 无/靠左/置中/靠右
2. **连结至 (Link to)**: 无/媒体档案/附件页面/自订 URL
3. **尺寸 (Size)**: 缩图/中/大/完整尺寸

**Playwright 实现**:
```javascript
await page.locator('.media-modal .setting[data-setting="align"] select').selectOption('center');
await page.locator('.media-modal .setting[data-setting="link"] select').selectOption('none');
await page.locator('.media-modal .setting[data-setting="size"] select').selectOption({ label: '大' });
```

#### 2.6 插入图片至文章
**Playwright 实现**:
```javascript
await page.locator('.media-modal button.media-button-insert').click();
await page.waitForSelector('.media-modal', { state: 'hidden' });
// 验证图片已插入
const frame = page.frameLocator('#content_ifr');
await expect(frame.locator('img[alt="替代文字"]')).toBeVisible();
```

---

### 阶段三：特色图片设置

#### 3.1 打开特色图片设置界面
**Playwright 实现**:
```javascript
await page.locator('#set-post-thumbnail').click();
await page.waitForSelector('.media-modal');
```

#### 3.2 选择或上传特色图片
**策略**:
- 优先使用已上传的图片（避免重复上传）
- 如果需要不同的特色图片，执行上传流程（同 2.3）

**Playwright 实现**:
```javascript
// 从媒体库选择
await page.locator('.media-modal li.attachment[aria-label="图片标题"]').click();
await expect(page.locator('.media-modal li.attachment.selected')).toHaveCount(1);
```

#### 3.3 编辑与裁切特色图片 ⭐ **核心功能**

**需求背景**:
WordPress 会为特色图片生成多个尺寸（缩略图、中型、大型、完整尺寸），某些主题和插件还会定义自定义尺寸（如 Facebook 分享图 700x359px）。通过裁切，可以确保图片在不同场景下的显示效果最佳。

**裁切目标尺寸**:
1. **Thumbnail** (缩略图): 150x150px（正方形）
2. **Facebook 分享图**: 700x359px（OG Image）
3. **其他自定义尺寸**: 根据主题配置

**Playwright 实现流程**:
```javascript
// 1. 点击「编辑图片」
await page.locator('.media-modal a.edit-attachment').click();
await page.waitForSelector('img#image-preview');

// 2. 选择裁切尺寸 - Thumbnail
await page.locator('input[value="thumbnail"]').click();
await page.waitForSelector('.imgareaselect-outer'); // 等待裁切框出现

// 3. 调整裁切框（高级操作）
// ⚠️ 挑战：需要模拟鼠标拖拽，Playwright 需要精确坐标
// 建议：接受 WordPress 自动建议的裁切框，或使用 Computer Use

// 4. 执行裁切
await page.locator('button[aria-label="裁切"]').click();

// 5. 保存裁切
await page.locator('input[value="儲存"]').click();
await page.waitForResponse(resp => resp.url().includes('admin-ajax.php') && resp.status() === 200);

// 6. 重复以上步骤裁切 Facebook 分享图
await page.locator('input[value="facebook_700_359"]').click();
// ... 裁切 + 保存
```

**Computer Use 备选方案**:
对于裁切框调整这种高度视觉化的操作，Computer Use 可能更适合：
```
指令：「在图片上拖曳裁切框，确保人物面部完整出现在框内，然后点击裁切按钮，再点击储存。」
```

**验证**:
- 检查裁切后的图片预览
- 确认没有重要内容被裁掉
- 保存后截图存档

#### 3.4 设置为特色图片
**Playwright 实现**:
```javascript
await page.locator('.media-modal button.media-button-select').click();
await page.waitForSelector('.media-modal', { state: 'hidden' });
// 验证特色图片已设置
await expect(page.locator('#postimagediv .inside img')).toBeVisible();
```

---

### 阶段四：最终保存与发布

#### 4.1 保存草稿
**Playwright 实现**:
```javascript
await page.locator('#save-post').click();
await page.waitForSelector('#message p:has-text("文章草稿已更新")');
```

#### 4.2 预览文章
**目的**: 在发布前检查排版、图片显示、SEO 元素

**Playwright 实现**:
```javascript
const previewPromise = page.waitForEvent('popup');
await page.locator('#post-preview').click();
const previewPage = await previewPromise;
await previewPage.waitForLoadState();

// 在预览页面执行检查
await expect(previewPage.locator('h1')).toHaveText('文章标题');
await expect(previewPage.locator('img[alt="替代文字"]')).toBeVisible();

// 检查 SEO meta 标签
const metaTitle = await previewPage.locator('meta[property="og:title"]').getAttribute('content');
expect(metaTitle).toBe('SEO 标题');

await previewPage.close();
```

#### 4.3 发布文章
**Playwright 实现**:
```javascript
await page.locator('#publish').click();
await page.waitForSelector('#message p:has-text("文章已發佈")');
```

**获取发布后的文章 URL**:
```javascript
const publishedUrl = await page.locator('#message a').getAttribute('href');
console.log('文章已发布:', publishedUrl);
```

#### 4.4 排程发布（可选）
**Playwright 实现**:
```javascript
// 点击「编辑」调整发布时间
await page.locator('a[href="#edit_timestamp"]').click();

// 设置日期时间
await page.locator('#mm').selectOption('12'); // 月份
await page.locator('#jj').fill('25'); // 日期
await page.locator('#aa').fill('2025'); // 年份
await page.locator('#hh').fill('14'); // 小时
await page.locator('#mn').fill('30'); // 分钟

// 确认
await page.locator('a.save-timestamp').click();

// 点击排程按钮（此时按钮文字变为「排程」）
await page.locator('#publish').click();
await page.waitForSelector('#message p:has-text("文章已排程")');
```

---

## 关键技术挑战与解决方案

### 挑战 1: TinyMCE 可视化编辑器中的文本选择与格式化

**问题描述**:
- Playwright 难以在 TinyMCE（可视化编辑器）中精确选取文本
- 设置小标题（H2/H3）需要先选中文字，再操作工具栏

**解决方案**:
1. **推荐方案**: 在内容准备阶段直接生成 HTML 标签，在「文字」模式下贴入
   ```html
   <h2>小标题1</h2>
   <p>段落内容...</p>
   <h2>小标题2</h2>
   ```

2. **备选方案**: 使用 JavaScript 注入来操作 TinyMCE API
   ```javascript
   await page.evaluate((heading) => {
     const editor = tinymce.get('content');
     editor.selection.select(editor.dom.select('p:contains("要设为标题的文字")')[0]);
     editor.execCommand('FormatBlock', false, 'h2');
   }, headingText);
   ```

3. **Computer Use 方案**: 当以上方案失效时降级使用

### 挑战 2: 图片裁切框的拖拽操作

**问题描述**:
- WordPress 图片编辑器使用 imgAreaSelect 插件，需要拖拽裁切框
- Playwright 需要模拟鼠标按下、移动、释放，需精确坐标

**解决方案**:
1. **接受默认裁切**: WordPress 会自动建议一个裁切区域，直接点击「裁切」按钮
2. **使用 Computer Use**: 对于需要手动调整的情况，用 AI 视觉识别更可靠
3. **预处理图片**: 在上传前使用 Sharp.js 等库预先裁切到目标尺寸

### 挑战 3: 选择器稳定性

**问题描述**:
- WordPress 版本更新可能改变 DOM 结构
- 不同主题和插件会修改后台界面
- CSS class 名称可能改变

**解决方案**:
1. **优先使用稳定的选择器**:
   - `id` 属性（最稳定）
   - `data-*` 属性
   - `name` 属性
   - `aria-label` 属性
   - 避免使用纯 CSS class

2. **多级备选选择器**:
   ```javascript
   const selectors = [
     '#new-tag-post_tag',
     'input[name="newtag[post_tag]"]',
     '.tagsdiv input.newtag'
   ];

   let element;
   for (const selector of selectors) {
     element = await page.locator(selector).first();
     if (await element.isVisible()) break;
   }
   ```

3. **选择器验证与更新机制**:
   - 定期在测试环境中运行验证脚本
   - 记录失败的选择器，触发告警
   - 维护选择器配置文件，支持热更新

### 挑战 4: 异步操作与等待时机

**问题描述**:
- WordPress 使用 AJAX 保存草稿、上传图片
- 某些操作（如图片裁切）需要等待服务器响应
- 固定延迟 (`waitForTimeout`) 不可靠且浪费时间

**解决方案**:
1. **等待 DOM 元素**:
   ```javascript
   await page.waitForSelector('#message.updated');
   ```

2. **等待网络请求**:
   ```javascript
   await page.waitForResponse(resp =>
     resp.url().includes('admin-ajax.php') &&
     resp.status() === 200
   );
   ```

3. **等待元素状态变化**:
   ```javascript
   await expect(page.locator('#publish')).toBeEnabled();
   ```

4. **组合等待**:
   ```javascript
   await Promise.all([
     page.waitForNavigation(),
     page.locator('#publish').click()
   ]);
   ```

---

## 两阶段实施策略详解

### Phase 1: Computer Use MVP 实施

#### 架构设计

```python
class WordPressPublisher:
    """Phase 1: 纯 Computer Use 实现"""

    def __init__(self, api_key: str, instructions: InstructionTemplate):
        self.computer_use_provider = ComputerUseProvider(api_key, instructions)
        self.current_provider = self.computer_use_provider
        self.audit_logger = AuditLogger()

    async def publish_article(
        self,
        article: Article,
        images: List[ImageAsset],
        metadata: ArticleMetadata
    ) -> PublishResult:
        """发布文章主入口（MVP）"""
        task_id = self._generate_task_id()

        try:
            # 初始化 Computer Use
            await self.current_provider.initialize(wordpress_url)

            # 执行 5 个阶段
            await self._execute_phase("login", ...)
            await self._execute_phase("content", ...)
            await self._execute_phase("images", ...)
            await self._execute_phase("metadata", ...)
            await self._execute_phase("publish", ...)

            return PublishResult(success=True, ...)

        except Exception as e:
            self.audit_logger.log_failure(task_id, str(e))
            raise

    async def _execute_phase(self, phase_name: str, phase_func, context):
        """执行阶段（MVP：无需降级逻辑）"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # 执行 Computer Use 指令
                await phase_func(self.current_provider, context)
                self.audit_logger.log_phase_success(context.task_id, phase_name, attempt)
                return
            except Exception as e:
                self.audit_logger.log_phase_failure(context.task_id, phase_name, attempt, str(e))
                if attempt >= max_retries - 1:
                    raise
                await asyncio.sleep(2)
```

#### MVP 验收标准

**功能完整性**:
- ✅ 能登录 WordPress 后台
- ✅ 能创建文章并填充内容
- ✅ 能上传图片并设置元数据
- ✅ 能设置特色图片并裁切
- ✅ 能配置标签、分类、SEO
- ✅ 能成功发布文章

**性能要求**:
- 单篇文章发布时间：≤ 5 分钟
- 成功率：≥ 95%
- 审计日志完整

### Phase 2: Playwright 混合优化

#### 升级策略

```python
class WordPressPublisher:
    """Phase 2: Playwright + Computer Use 混合架构"""

    def __init__(
        self,
        playwright_provider: PlaywrightProvider,
        computer_use_provider: ComputerUseProvider,
        config: PublishingConfig
    ):
        # Phase 2: 默认使用 Playwright（成本优化）
        self.primary_provider = playwright_provider
        self.fallback_provider = computer_use_provider
        self.current_provider = playwright_provider
        self.config = config

    async def _execute_phase(self, phase_name: str, phase_func, context):
        """执行阶段（Phase 2：带智能降级）"""
        max_retries = self.config.max_retries
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 使用当前 Provider 执行
                await phase_func(self.current_provider, context)
                self.audit_logger.log_phase_success(context.task_id, phase_name, retry_count)
                return

            except (ElementNotFoundError, TimeoutError) as e:
                retry_count += 1
                self.audit_logger.log_phase_failure(context.task_id, phase_name, retry_count, str(e))

                if retry_count >= max_retries:
                    # Playwright 失败，降级到 Computer Use
                    if self.current_provider == self.primary_provider:
                        logger.warning(f"Playwright 失败，降级到 Computer Use")
                        await self._fallback_to_computer_use(context)
                        retry_count = 0  # 重置计数
                    else:
                        raise  # Computer Use 也失败，抛出异常

                await asyncio.sleep(self.config.retry_delay)

    async def _fallback_to_computer_use(self, context):
        """降级到 Computer Use（Phase 2）"""
        # 关闭 Playwright
        await self.current_provider.close()

        # 切换到 Computer Use
        self.current_provider = self.fallback_provider

        # 重新初始化（尝试复用会话）
        await self.current_provider.initialize(
            context.wordpress_url,
            cookies=context.browser_cookies  # 传递 cookies
        )

        self.audit_logger.log_provider_switch(context.task_id, "computer_use")
```

#### 成本优化指标

**Phase 1 (Computer Use Only)**:
- 预估成本：$0.10-0.30 / 文章
- 发布速度：3-5 分钟 / 文章
- 成功率：95%

**Phase 2 (Playwright + Computer Use)**:
- 预估成本：$0.01-0.05 / 文章（降低 80-90%）
- 发布速度：1.5-3 分钟 / 文章（提升 40-50%）
- 成功率：98%（混合架构更可靠）
- Computer Use 调用率：< 5%（仅降级时使用）

---

## 审计与日志记录

### 必须截图的关键步骤

1. ✅ 登录成功后的仪表板
2. ✅ 文章标题和内容填写完成
3. ✅ 标签和分类设置完成
4. ✅ SEO 插件配置完成（显示绿灯/橙灯状态）
5. ✅ 图片上传完成（显示在媒体库中）
6. ✅ 图片元数据填写完成
7. ✅ 图片插入到文章内容中
8. ✅ 特色图片设置完成（显示在右侧栏）
9. ✅ 图片裁切完成（各尺寸的预览）
10. ✅ 保存草稿成功提示
11. ✅ 预览页面（完整文章）
12. ✅ 发布成功提示（包含文章 URL）

### 日志记录内容

```json
{
  "task_id": "publish-12345",
  "article_id": 67890,
  "start_time": "2025-10-27T10:30:00Z",
  "end_time": "2025-10-27T10:35:00Z",
  "status": "success",
  "provider": "playwright",
  "fallback_used": false,
  "steps": [
    {
      "step_name": "navigate_to_new_post",
      "status": "success",
      "duration_ms": 1200,
      "screenshot": "/logs/task-12345/step-01.png",
      "timestamp": "2025-10-27T10:30:01Z"
    },
    {
      "step_name": "fill_title",
      "status": "success",
      "duration_ms": 300,
      "screenshot": "/logs/task-12345/step-02.png",
      "timestamp": "2025-10-27T10:30:02Z"
    },
    // ... 更多步骤
  ],
  "errors": [],
  "warnings": [
    {
      "step_name": "upload_image",
      "message": "Image size exceeds 5MB, consider compression",
      "timestamp": "2025-10-27T10:32:00Z"
    }
  ],
  "published_url": "https://example.com/2025/10/27/article-title/",
  "metadata": {
    "wordpress_version": "6.4.2",
    "theme": "Astra",
    "plugins": ["Yoast SEO", "Classic Editor"]
  }
}
```

---

## 验收标准

### 功能正确性

✅ **必须满足**:
1. 文章标题、内容准确无误地发布到 WordPress
2. 所有图片成功上传，元数据（Alt、Title、Caption）完整
3. 特色图片正确设置，并完成至少 2 种尺寸的裁切（Thumbnail、Facebook）
4. 标签和分类正确关联
5. SEO 插件配置完整（焦点关键字、Meta Title、Meta Description）
6. 发布后能获取正确的文章 URL

### 性能要求

- **单篇文章发布时间**: ≤ 3 分钟（包含 3-5 张图片）
- **Playwright 步骤平均耗时**: ≤ 2 秒/步
- **图片上传速度**: ≥ 1MB/秒
- **降级切换时间**: ≤ 10 秒

### 可靠性要求

- **成功率**: ≥ 95%（Playwright）
- **成功率（含降级）**: ≥ 99%（Playwright + Computer Use）
- **错误恢复**: 能从任意失败步骤恢复执行
- **数据完整性**: 即使中途失败，已保存的草稿数据不丢失

### 可维护性要求

- **选择器更新**: 提供配置文件维护所有选择器，支持版本管理
- **日志完整性**: 每个步骤都有详细日志和截图
- **调试友好**: 支持单步调试模式，逐步验证每个操作

---

## 风险与限制

### 已知限制

1. **WordPress 版本兼容性**:
   - 本方案基于 WordPress **经典编辑器**
   - **Gutenberg（区块编辑器）需要单独适配**（优先级 P2）
   - 建议在测试环境中验证具体版本

2. **主题与插件依赖**:
   - 不同主题可能修改后台界面布局
   - 某些插件会添加额外字段或弹窗
   - 需要针对常用主题（Astra、GeneratePress）和插件（Yoast、Rank Math）进行测试

3. **网络依赖**:
   - 上传大图片时对网络速度敏感
   - 建议在服务器端运行，避免公共网络不稳定

4. **浏览器环境**:
   - Playwright 需要在 Headless Chrome 中运行
   - 某些 WordPress 插件可能检测无头浏览器并阻止操作（罕见）

### 未来改进方向

1. **支持 Gutenberg 编辑器**（P2）
2. **支持更多 SEO 插件**（如 All in One SEO）
3. **AI 辅助图片裁切**：自动识别主体并智能裁切
4. **批量发布优化**：并行处理多篇文章
5. **多语言支持**：自动检测 WordPress 后台语言并适配

---

## 成功指标

### Phase 1 (MVP) 指标

#### 业务指标
- **功能完整性**: 100%（所有核心功能可用）
- **发布成功率**: ≥ 95%
- **发布速度**: ≤ 5 分钟 / 文章
- **人工成本降低**: 每篇文章节省 **25 分钟人工时间**

#### 技术指标
- **API 调用成功率**: ≥ 95%
- **审计日志完整性**: 100%（所有关键步骤有截图）
- **代码覆盖率**: ≥ 75%
- **部署成功**: 能在生产环境稳定运行 1 周

### Phase 2 (优化) 指标

#### 业务指标
- **成本降低**: 80-90%（$0.20 → $0.02 / 文章）
- **发布速度提升**: 40-50%（5分钟 → 2-3分钟）
- **发布成功率**: ≥ 98%（混合架构更可靠）
- **错误率降低**: SEO 元数据遗漏率 < 1%

#### 技术指标
- **代码覆盖率**: ≥ 85%
- **选择器准确率**: ≥ 95%
- **降级触发率**: ≤ 5%（大多数情况用 Playwright）
- **平均故障恢复时间**: ≤ 2 分钟
- **Playwright 使用率**: ≥ 95%

### ROI 分析

**Phase 1 投入**:
- 开发时间：2 周
- API 成本：$0.20 / 文章 × 100 文章/月 = $20/月

**Phase 2 投入**:
- 开发时间：2 周（增量）
- API 成本：$0.02 / 文章 × 100 文章/月 = $2/月（节省 $18/月）

**预期回报**:
- 人工成本节省：25 分钟 × 100 文章/月 = 2500 分钟/月（约 42 小时）
- 质量提升：SEO 完整性从 70% 提升到 99%
- Phase 2 额外收益：运行成本降低 90%

---

## 附录

### A. 关键 DOM 选择器速查表

| 功能 | 选择器 (Playwright) | 备选选择器 | 稳定性 |
|------|---------------------|------------|--------|
| 新增文章菜单 | `#menu-posts > a` | `a[href="edit.php"]` | ⭐⭐⭐⭐⭐ |
| 新增文章链接 | `#menu-posts ul > li > a:has-text("新增文章")` | `a[href="post-new.php"]` | ⭐⭐⭐⭐⭐ |
| 文章标题 | `#title` | `input[name="post_title"]` | ⭐⭐⭐⭐⭐ |
| 内容编辑器（文字模式） | `#content-html` | `a.wp-switch-editor[data-mode="html"]` | ⭐⭐⭐⭐ |
| 内容编辑器（可视化模式） | `#content-tmce` | `a.wp-switch-editor[data-mode="tmce"]` | ⭐⭐⭐⭐ |
| 内容文本区域 | `#content` | `textarea[name="content"]` | ⭐⭐⭐⭐⭐ |
| TinyMCE iframe | `#content_ifr` | `iframe.wp-editor-area` | ⭐⭐⭐⭐ |
| 新增标签输入框 | `#new-tag-post_tag` | `input.newtag` | ⭐⭐⭐⭐ |
| 标签新增按钮 | `input.button[value="新增"]` | `.tagsdiv input.button` | ⭐⭐⭐ |
| 分类复选框 | `label:has-text("分类名") input[type="checkbox"]` | `.categorychecklist input` | ⭐⭐⭐ |
| 新增媒体按钮 | `#insert-media-button` | `button.insert-media` | ⭐⭐⭐⭐⭐ |
| 媒体弹窗 | `.media-modal` | `.media-frame` | ⭐⭐⭐⭐ |
| 上传文件按钮 | `button:has-text("選擇檔案")` | `.media-toolbar-primary button` | ⭐⭐⭐ |
| 图片替代文字 | `.media-modal .setting[data-setting="alt"] input` | `input[id*="alt-text"]` | ⭐⭐⭐⭐ |
| 插入至文章按钮 | `.media-modal button.media-button-insert` | `button:has-text("插入至文章")` | ⭐⭐⭐⭐ |
| 设置特色图片 | `#set-post-thumbnail` | `a[href="#set-post-thumbnail"]` | ⭐⭐⭐⭐⭐ |
| 特色图片区域 | `#postimagediv` | `.inside #set-post-thumbnail` | ⭐⭐⭐⭐⭐ |
| 编辑图片链接 | `.media-modal a.edit-attachment` | `button:has-text("編輯圖片")` | ⭐⭐⭐ |
| 裁切尺寸选择 | `input[value="thumbnail"]` | `.imgedit-group input[type="radio"]` | ⭐⭐⭐ |
| 保存草稿 | `#save-post` | `input[name="save"]` | ⭐⭐⭐⭐⭐ |
| 预览按钮 | `#post-preview` | `a#preview-action` | ⭐⭐⭐⭐ |
| 发布按钮 | `#publish` | `input[name="publish"]` | ⭐⭐⭐⭐⭐ |
| 成功消息 | `#message.updated` | `.notice.notice-success` | ⭐⭐⭐⭐ |

### B. Computer Use 指令模板库

#### 1. 导航类指令
```
找到左側選單中帶有圖釘圖示且標籤為『文章』的項目，點擊它。
在展開的子選單中，找到並點擊標籤為『新增文章』的連結。
等待頁面載入完成，確認頁面頂部出現文字『新增文章』。
```

#### 2. 输入类指令
```
找到標籤為『新增標題』或 ID 為 'title' 的大型文字輸入框。
在此輸入框中輸入以下文字：『{article_title}』。
確認輸入框中已顯示輸入的標題文字。
```

#### 3. 图片上传指令
```
找到標籤為『新增媒體』的按鈕，點擊它。
等待一個標題為『插入媒體』的彈出視窗出現。
點擊標籤為『上傳檔案』的分頁。
將圖片檔案『{image_path}』拖曳到標有『請將檔案拖曳到這裡上傳』的區域。
等待圖片上傳完成（會看到圖片縮圖和進度條）。
```

#### 4. 图片裁切指令（高价值）
```
在圖片預覽下方，找到並點擊標籤為『編輯圖片』的連結。
等待進入圖片編輯介面。
在右側找到標籤為『縮圖設定』或類似名稱的區塊。
找到標籤為『Thumbnail』(或『縮圖』) 的選項，點擊它。
調整圖片上出現的裁切框，確保主要內容（例如人物面部）在框內。
點擊裁切按鈕（通常是一個方形圖示）。
點擊『儲存』或『更新』按鈕。
```

---

**文档版本**: v1.0
**作者**: AI Architect
**审核**: Pending
**下一步**: 创建实施计划 (plan.md) 和任务清单 (tasks.md)
