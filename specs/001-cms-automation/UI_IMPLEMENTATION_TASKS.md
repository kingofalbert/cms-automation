# UI Implementation Tasks - Filling the Gaps

**创建日期**: 2025-10-27
**版本**: 1.0.0
**基于**: UI_GAPS_ANALYSIS.md
**总工时**: 332 小时
**预计周期**: 6 周（2 前端工程师 + 1 后端工程师）

---

## 任务总览

根据 [UI Gaps Analysis](../../docs/UI_GAPS_ANALYSIS.md)，需要实现 **6 个核心模块**，共 **48 个 UI 组件** 和 **12+ 个 API 端点**。

### 模块分布

| 模块 | 优先级 | 组件数 | 工时 | 周期 |
|------|--------|--------|------|------|
| **Module 1**: Article Import UI | 🔴 P0 | 8 | 50h | Week 1-2 |
| **Module 2**: SEO Optimization UI | 🔴 P0 | 9 | 42h | Week 1-2 |
| **Module 3**: Multi-Provider Publishing UI | 🔴 P0 | 8 | 48h | Week 3-4 |
| **Module 4**: Task Monitoring UI | 🟡 P1 | 7 | 44h | Week 3-4 |
| **Module 5**: Provider Comparison Dashboard | 🟢 P2 | 6 | 30h | Week 5-6 |
| **Module 6**: Settings Page | 🟢 P2 | 5 | 22h | Week 5-6 |
| **Backend APIs** | 🔴 P0 | - | 76h | Week 1-6 |
| **Testing** | 🔴 P0 | - | 20h | Week 5-6 |

---

## Phase 1: Core Functionality (Week 1-4)

### Week 1-2: Article Import + SEO Optimization

---

#### Task Group 1.1: Article Import UI (Module 1) - 50 hours

**目标**: 实现文章导入功能，支持 CSV/JSON/手动输入

##### T-UI-1.1.1 [P0] Create Article Import Page

**Priority**: 🔴 Critical
**Estimated Hours**: 4 hours
**Dependencies**: None

**Description**:
创建文章导入页面主容器，集成 3 种导入方式（CSV/JSON/手动输入）

**Deliverables**:
- `frontend/src/pages/ArticleImportPage.tsx`
- 导航路由配置
- 页面布局（Tab 或 Wizard 模式）

**Acceptance Criteria**:
- [ ] 页面可通过 `/import` 路由访问
- [ ] 包含 3 个 Tab: "CSV 导入", "JSON 导入", "手动输入"
- [ ] 响应式布局（支持移动端）
- [ ] 显示导入历史记录（最近 10 次）

**Code Structure**:
```tsx
// frontend/src/pages/ArticleImportPage.tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { CSVUploadForm } from '@/components/ArticleImport/CSVUploadForm';
import { JSONUploadForm } from '@/components/ArticleImport/JSONUploadForm';
import { ManualArticleForm } from '@/components/ArticleImport/ManualArticleForm';
import { ImportHistoryTable } from '@/components/ArticleImport/ImportHistoryTable';

export default function ArticleImportPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">导入文章</h1>

      <Tabs defaultValue="csv">
        <TabsList>
          <TabsTrigger value="csv">CSV 导入</TabsTrigger>
          <TabsTrigger value="json">JSON 导入</TabsTrigger>
          <TabsTrigger value="manual">手动输入</TabsTrigger>
        </TabsList>

        <TabsContent value="csv">
          <CSVUploadForm />
        </TabsContent>

        <TabsContent value="json">
          <JSONUploadForm />
        </TabsContent>

        <TabsContent value="manual">
          <ManualArticleForm />
        </TabsContent>
      </Tabs>

      <div className="mt-12">
        <h2 className="text-2xl font-semibold mb-4">导入历史</h2>
        <ImportHistoryTable />
      </div>
    </div>
  );
}
```

---

##### T-UI-1.1.2 [P0] Implement CSV Upload Form

**Priority**: 🔴 Critical
**Estimated Hours**: 8 hours
**Dependencies**: T-UI-1.1.1

**Description**:
实现 CSV 文件上传表单，支持拖拽上传、验证、进度显示

**Deliverables**:
- `frontend/src/components/ArticleImport/CSVUploadForm.tsx`
- `frontend/src/components/ArticleImport/DragDropZone.tsx`
- `frontend/src/components/ArticleImport/TemplateDownloadButton.tsx`
- `frontend/src/components/ArticleImport/ValidationSummary.tsx`

**Acceptance Criteria**:
- [ ] 支持拖拽上传和文件选择
- [ ] 文件格式验证（仅接受 .csv）
- [ ] 文件大小限制（最多 500 篇文章，约 10MB）
- [ ] 实时解析和验证
- [ ] 显示验证错误（行号 + 字段 + 错误信息）
- [ ] 进度条（X/Y 篇已处理）
- [ ] 提供 CSV 模板下载
- [ ] 成功后跳转到文章列表

**Code Structure**:
```tsx
// frontend/src/components/ArticleImport/CSVUploadForm.tsx
import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button, ProgressBar } from '@/components/ui';
import { importCSV } from '@/services/api-client';

export function CSVUploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
    onDrop: (acceptedFiles) => {
      setFile(acceptedFiles[0]);
    }
  });

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const response = await importCSV(file);
      setResult(response);
      // Show success message and redirect
    } catch (error) {
      // Handle error
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Drag & Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'}
        `}
      >
        <input {...getInputProps()} />
        <svg className="mx-auto h-12 w-12 text-gray-400" /* ... */ />
        <p className="mt-2 text-sm text-gray-600">
          {isDragActive
            ? '释放文件以上传'
            : '拖拽 CSV 文件到此处，或点击选择文件'
          }
        </p>
        <p className="text-xs text-gray-500 mt-1">
          最多 500 篇文章，文件大小不超过 10MB
        </p>
      </div>

      {/* Selected File */}
      {file && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="font-medium">{file.name}</p>
          <p className="text-sm text-gray-600">
            {(file.size / 1024).toFixed(2)} KB
          </p>
        </div>
      )}

      {/* Template Download */}
      <div className="flex items-center justify-between">
        <a
          href="/templates/article_import_template.csv"
          download
          className="text-primary-600 hover:underline text-sm"
        >
          📥 下载 CSV 模板
        </a>

        <Button
          onClick={handleUpload}
          disabled={!file || uploading}
          loading={uploading}
        >
          {uploading ? '上传中...' : '开始导入'}
        </Button>
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div className="space-y-2">
          <ProgressBar value={60} max={100} />
          <p className="text-sm text-gray-600 text-center">
            正在处理... 60/100 篇
          </p>
        </div>
      )}

      {/* Validation Summary */}
      {result && (
        <ValidationSummary
          imported={result.imported}
          failed={result.failed}
          errors={result.errors}
        />
      )}
    </div>
  );
}
```

**API Integration**:
```typescript
// frontend/src/services/api-client.ts
export const importCSV = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/v1/articles/import/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });

  return response.data;
  // Response: { imported: 95, failed: 5, errors: [{ row, field, message }] }
};
```

---

##### T-UI-1.1.3 [P0] Implement JSON Upload Form

**Priority**: 🔴 Critical
**Estimated Hours**: 6 hours
**Dependencies**: T-UI-1.1.2 (可复用组件)

**Description**:
实现 JSON 文件上传，类似 CSV 但支持嵌套结构

**Deliverables**:
- `frontend/src/components/ArticleImport/JSONUploadForm.tsx`
- JSON Schema 验证

**Acceptance Criteria**:
- [ ] 支持 JSON 数组和单个对象
- [ ] Schema 验证
- [ ] 复用 DragDropZone 组件
- [ ] 显示 JSON 预览（可选）

---

##### T-UI-1.1.4 [P0] Implement Manual Article Form

**Priority**: 🔴 Critical
**Estimated Hours**: 10 hours
**Dependencies**: T-UI-1.1.1

**Description**:
实现手动输入文章表单，包含富文本编辑器和图片上传

**Deliverables**:
- `frontend/src/components/ArticleImport/ManualArticleForm.tsx`
- `frontend/src/components/ArticleImport/RichTextEditor.tsx`
- `frontend/src/components/ArticleImport/ImageUploadWidget.tsx`

**Acceptance Criteria**:
- [ ] 标题输入（10-500 字符，实时验证）
- [ ] 富文本编辑器（TipTap or Quill）
- [ ] 内容字数统计（最少 100 字）
- [ ] 摘要输入（可选，最多 300 字符）
- [ ] 分类下拉选择
- [ ] 标签输入（多选）
- [ ] 特色图片上传（1 张，最大 5MB）
- [ ] 附加图片上传（最多 10 张）
- [ ] 自动保存草稿（每 30 秒）
- [ ] HTML 预览模式
- [ ] 提交按钮（验证通过后启用）

**Tech Stack**:
- 富文本: **TipTap** (推荐) or Quill
- 图片上传: **react-dropzone** + **preview**

**Code Example**:
```tsx
import { useForm } from 'react-hook-form';
import { Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';

export function ManualArticleForm() {
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const [featuredImage, setFeaturedImage] = useState<File | null>(null);
  const [additionalImages, setAdditionalImages] = useState<File[]>([]);

  const editor = useEditor({
    extensions: [StarterKit],
    content: '<p>开始输入文章内容...</p>',
    onUpdate: ({ editor }) => {
      // Auto-save draft every 30 seconds
    }
  });

  const contentWordCount = editor?.getText().split(/\s+/).length || 0;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Title */}
      <div>
        <label className="block text-sm font-medium mb-2">
          文章标题 <span className="text-red-500">*</span>
        </label>
        <input
          {...register('title', { required: true, minLength: 10, maxLength: 500 })}
          className="w-full px-4 py-2 border rounded-lg"
          placeholder="请输入文章标题（至少 10 个字符）"
        />
        {errors.title && (
          <p className="text-red-500 text-sm mt-1">标题必须是 10-500 个字符</p>
        )}
      </div>

      {/* Rich Text Editor */}
      <div>
        <label className="block text-sm font-medium mb-2">
          文章内容 <span className="text-red-500">*</span>
        </label>
        <div className="border rounded-lg">
          <EditorToolbar editor={editor} />
          <EditorContent editor={editor} className="min-h-[400px] p-4" />
        </div>
        <p className="text-sm text-gray-600 mt-1">
          字数: {contentWordCount} {contentWordCount < 100 && '（最少 100 字）'}
        </p>
      </div>

      {/* Excerpt */}
      <div>
        <label className="block text-sm font-medium mb-2">文章摘要</label>
        <textarea
          {...register('excerpt', { maxLength: 300 })}
          className="w-full px-4 py-2 border rounded-lg"
          rows={3}
          placeholder="简要描述文章内容（可选）"
        />
      </div>

      {/* Category & Tags */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">分类</label>
          <select {...register('category')} className="w-full px-4 py-2 border rounded-lg">
            <option value="">选择分类</option>
            <option value="news">时政新闻</option>
            <option value="opinion">观点评论</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">标签</label>
          <TagInput
            value={tags}
            onChange={setTags}
            placeholder="输入标签，按回车添加"
          />
        </div>
      </div>

      {/* Image Upload */}
      <ImageUploadWidget
        featuredImage={featuredImage}
        onFeaturedImageChange={setFeaturedImage}
        additionalImages={additionalImages}
        onAdditionalImagesChange={setAdditionalImages}
        maxImages={10}
        maxSizePerImage={5 * 1024 * 1024}
      />

      {/* Submit */}
      <div className="flex justify-end gap-4">
        <Button type="button" variant="outline">
          保存草稿
        </Button>
        <Button
          type="submit"
          disabled={contentWordCount < 100 || !watch('title')}
        >
          导入文章
        </Button>
      </div>
    </form>
  );
}
```

---

##### T-UI-1.1.5 [P0] Implement Image Upload Widget

**Priority**: 🔴 Critical
**Estimated Hours**: 8 hours
**Dependencies**: T-UI-1.1.4

**Description**:
通用图片上传组件，支持特色图片 + 附加图片

**Deliverables**:
- `frontend/src/components/ArticleImport/ImageUploadWidget.tsx`
- 图片预览
- 图片裁剪（可选）

**Acceptance Criteria**:
- [ ] 支持拖拽和点击上传
- [ ] 特色图片：1 张，必须上传
- [ ] 附加图片：最多 10 张
- [ ] 单个文件大小限制：5MB
- [ ] 支持格式：JPG, PNG, GIF, WebP
- [ ] 图片预览（缩略图）
- [ ] 删除已上传图片
- [ ] 上传进度显示
- [ ] 图片压缩（客户端，可选）

---

##### T-UI-1.1.6-8 [Medium] Additional Components

- **T-UI-1.1.6**: `BatchImportProgress.tsx` (6h)
- **T-UI-1.1.7**: `ImportValidationErrors.tsx` (4h)
- **T-UI-1.1.8**: `DuplicateDetectionAlert.tsx` (4h)

---

#### Task Group 1.2: SEO Optimization UI (Module 2) - 42 hours

**目标**: 实现 SEO 元数据生成和编辑功能

##### T-UI-1.2.1 [P0] Create SEO Optimizer Panel

**Priority**: 🔴 Critical
**Estimated Hours**: 6 hours
**Dependencies**: 文章详情页存在

**Description**:
SEO 优化面板主容器，展示 AI 生成的 SEO 元数据并支持编辑

**Deliverables**:
- `frontend/src/components/SEO/SEOOptimizerPanel.tsx`
- 集成所有 SEO 子组件

**Acceptance Criteria**:
- [ ] 4 个区域：Meta 字段、关键词、分析图表、优化建议
- [ ] "重新分析" 按钮（触发 Celery 任务）
- [ ] "保存修改" 按钮
- [ ] AI 生成标记（显示哪些字段是 AI 生成的）
- [ ] 手动编辑追踪（记录到 manual_overrides）

---

##### T-UI-1.2.2 [P0] Implement Meta Title Editor

**Priority**: 🔴 Critical
**Estimated Hours**: 4 hours
**Dependencies**: T-UI-1.2.1

**Description**:
Meta Title 编辑器，实时字符计数（50-60 字符）

**Deliverables**:
- `frontend/src/components/SEO/MetaTitleEditor.tsx`
- `frontend/src/components/SEO/CharacterCounter.tsx`

**Acceptance Criteria**:
- [ ] 输入框（textarea for 长中文）
- [ ] 实时字符计数
- [ ] 字符范围提示（50-60，绿色 = OK，红色 = 超出）
- [ ] Focus keyword 高亮显示
- [ ] AI 生成标记

**Code Example**:
```tsx
export function MetaTitleEditor({ value, onChange, focusKeyword, aiGenerated }) {
  const charCount = value.length;
  const isValid = charCount >= 50 && charCount <= 60;

  return (
    <div className="space-y-2">
      <label className="flex items-center gap-2">
        <span className="font-medium">SEO 标题</span>
        {aiGenerated && <Badge variant="secondary">AI 生成</Badge>}
      </label>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full px-4 py-2 border rounded-lg ${
          isValid ? 'border-green-500' : 'border-red-500'
        }`}
        rows={2}
      />

      <CharacterCounter
        current={charCount}
        min={50}
        max={60}
        isValid={isValid}
      />

      {focusKeyword && !value.includes(focusKeyword) && (
        <p className="text-yellow-600 text-sm">
          ⚠️ 建议在标题中包含 Focus Keyword: "{focusKeyword}"
        </p>
      )}
    </div>
  );
}
```

---

##### T-UI-1.2.3 [P0] Implement Meta Description Editor

**Priority**: 🔴 Critical
**Estimated Hours**: 4 hours
**Dependencies**: T-UI-1.2.2 (复用 CharacterCounter)

**Description**:
Meta Description 编辑器（150-160 字符）

**Acceptance Criteria**:
- [ ] 类似 Meta Title Editor
- [ ] 字符范围：150-160
- [ ] 建议包含 Call-to-Action

---

##### T-UI-1.2.4 [P0] Implement Keyword Editor

**Priority**: 🔴 Critical
**Estimated Hours**: 8 hours
**Dependencies**: T-UI-1.2.1

**Description**:
关键词编辑器，支持 Focus/Primary/Secondary 3 种类型

**Deliverables**:
- `frontend/src/components/SEO/KeywordEditor.tsx`
- `frontend/src/components/SEO/KeywordBadge.tsx`

**Acceptance Criteria**:
- [ ] Focus Keyword：单个输入，不可多选
- [ ] Primary Keywords：3-5 个（Tag 形式）
- [ ] Secondary Keywords：5-10 个（Tag 形式）
- [ ] 添加/删除关键词
- [ ] 关键词搜索建议（可选）

**Code Example**:
```tsx
export function KeywordEditor({ type, values, onChange, badge }) {
  const [input, setInput] = useState('');

  const addKeyword = () => {
    if (input.trim() && !values.includes(input.trim())) {
      onChange([...values, input.trim()]);
      setInput('');
    }
  };

  const removeKeyword = (keyword: string) => {
    onChange(values.filter(k => k !== keyword));
  };

  return (
    <div className="space-y-2">
      <label className="flex items-center gap-2">
        <span className="font-medium">{badge} Keywords</span>
        <Badge variant={type === 'focus' ? 'primary' : 'secondary'}>
          {values?.length || 0} / {type === 'focus' ? 1 : type === 'primary' ? '3-5' : '5-10'}
        </Badge>
      </label>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addKeyword();
            }
          }}
          className="flex-1 px-4 py-2 border rounded-lg"
          placeholder={`输入 ${badge} Keyword，按回车添加`}
        />
        <Button onClick={addKeyword} variant="outline">添加</Button>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2">
        {values?.map(keyword => (
          <KeywordBadge
            key={keyword}
            keyword={keyword}
            onRemove={() => removeKeyword(keyword)}
            type={type}
          />
        ))}
      </div>
    </div>
  );
}
```

---

##### T-UI-1.2.5 [High] Implement Keyword Density Chart

**Priority**: 🟡 High
**Estimated Hours**: 6 hours
**Dependencies**: T-UI-1.2.4, Recharts library

**Description**:
关键词密度可视化（柱状图），显示每个关键词的密度百分比

**Deliverables**:
- `frontend/src/components/SEO/KeywordDensityChart.tsx`

**Acceptance Criteria**:
- [ ] 使用 Recharts BarChart
- [ ] X 轴：关键词名称
- [ ] Y 轴：密度百分比 (0.5%-3%)
- [ ] 参考线：0.5% (最低推荐), 3% (最高推荐)
- [ ] Tooltip：显示密度 + 出现次数
- [ ] 颜色编码：绿色=正常，黄色=偏低，红色=过高

**Code Example**:
```tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';

export function KeywordDensityChart({ data }) {
  const chartData = Object.entries(data).map(([keyword, stats]) => ({
    keyword,
    density: stats.density,
    count: stats.count,
    fill: stats.density >= 0.5 && stats.density <= 3 ? '#22C55E' :
          stats.density < 0.5 ? '#EAB308' : '#EF4444'
  }));

  return (
    <div>
      <h3 className="font-medium mb-4">关键词密度分析</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <XAxis dataKey="keyword" />
          <YAxis label={{ value: '密度 (%)', angle: -90 }} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const data = payload[0].payload;
              return (
                <div className="bg-white p-3 border rounded shadow">
                  <p className="font-medium">{data.keyword}</p>
                  <p className="text-sm">密度: {data.density}%</p>
                  <p className="text-sm">出现次数: {data.count}</p>
                </div>
              );
            }}
          />
          <ReferenceLine y={0.5} stroke="#22C55E" strokeDasharray="3 3" label="最低" />
          <ReferenceLine y={3.0} stroke="#EF4444" strokeDasharray="3 3" label="最高" />
          <Bar dataKey="density" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

##### T-UI-1.2.6-9 [High/Medium] Additional SEO Components

- **T-UI-1.2.6**: `ReadabilityScoreGauge.tsx` (4h) - 可读性仪表盘
- **T-UI-1.2.7**: `OptimizationRecommendations.tsx` (4h) - 优化建议列表
- **T-UI-1.2.8**: `CharacterCounter.tsx` (2h) - 通用字符计数器
- **T-UI-1.2.9**: `SEOAnalysisProgress.tsx` (4h) - SEO 分析进度

---

#### Task Group 1.3: Backend Article & SEO APIs - 40 hours

**目标**: 实现后端 API 支持前端 UI

##### T-BE-1.3.1 [P0] Implement Article Import APIs

**Estimated Hours**: 12 hours

**Endpoints**:
```python
# backend/src/api/routes/articles.py

@router.post("/v1/articles/import")
async def import_single_article(article: ArticleImportSchema) -> ArticleResponse:
    """单篇文章导入"""
    pass

@router.post("/v1/articles/import/batch")
async def import_batch_articles(file: UploadFile) -> BatchImportResponse:
    """CSV/JSON 批量导入"""
    pass

@router.post("/v1/articles/{article_id}/images")
async def upload_images(article_id: int, files: List[UploadFile]) -> ImageUploadResponse:
    """上传文章图片"""
    pass
```

---

##### T-BE-1.3.2 [P0] Implement SEO Analysis APIs

**Estimated Hours**: 14 hours

**Endpoints**:
```python
# backend/src/api/routes/seo.py

@router.post("/v1/seo/analyze/{article_id}")
async def analyze_seo(article_id: int) -> TaskResponse:
    """触发 SEO 分析 (Celery 异步任务)"""
    pass

@router.get("/v1/seo/analyze/{article_id}/status")
async def get_seo_analysis_status(article_id: int) -> SEOAnalysisStatusResponse:
    """查询分析状态"""
    pass

@router.get("/v1/seo/metadata/{article_id}")
async def get_seo_metadata(article_id: int) -> SEOMetadataResponse:
    """获取 SEO 元数据"""
    pass

@router.put("/v1/seo/metadata/{article_id}")
async def update_seo_metadata(article_id: int, data: SEOMetadataUpdate) -> SEOMetadataResponse:
    """更新 SEO 元数据（人工编辑）"""
    pass
```

---

##### T-BE-1.3.3 [P0] Implement Article CRUD APIs

**Estimated Hours**: 14 hours

**Endpoints**:
```python
@router.get("/v1/articles")
async def list_articles(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    source: Optional[str] = None
) -> PaginatedArticlesResponse:
    """获取文章列表（支持过滤）"""
    pass

@router.get("/v1/articles/{article_id}")
async def get_article(article_id: int) -> ArticleDetailResponse:
    """获取单篇文章详情"""
    pass

@router.put("/v1/articles/{article_id}")
async def update_article(article_id: int, data: ArticleUpdate) -> ArticleResponse:
    """更新文章"""
    pass

@router.delete("/v1/articles/{article_id}")
async def delete_article(article_id: int) -> DeleteResponse:
    """删除文章"""
    pass
```

---

### Week 3-4: Publishing + Monitoring UI

#### Task Group 2.1: Multi-Provider Publishing UI (Module 3) - 48 hours

**目标**: 实现多 Provider 发布功能

##### T-UI-2.1.1 [P0] Implement Publish Button

**Priority**: 🔴 Critical
**Estimated Hours**: 4 hours

**Description**:
发布按钮，带 Provider 选择下拉菜单

**Acceptance Criteria**:
- [ ] Dropdown 显示 3 个 Provider
- [ ] 每个 Provider 显示图标、名称、描述、预估成本/时间
- [ ] Playwright 标记为"推荐"
- [ ] 点击后弹出确认对话框

---

##### T-UI-2.1.2 [P0] Implement Provider Selection Dropdown

**Priority**: 🔴 Critical
**Estimated Hours**: 4 hours

**Code Example**:
```tsx
export function ProviderSelectionDropdown({ onSelect }) {
  const providers = [
    {
      id: 'playwright',
      name: 'Playwright',
      description: '快速免费',
      cost: '免费',
      duration: '1-2 分钟',
      icon: <PlaywrightIcon />,
      recommended: true
    },
    {
      id: 'anthropic',
      name: 'Anthropic Computer Use',
      description: 'AI 驱动，自适应',
      cost: '$1.50',
      duration: '3-5 分钟',
      icon: <AnthropicIcon />
    },
    {
      id: 'gemini',
      name: 'Gemini Computer Use',
      description: '成本优化',
      cost: '$1.00',
      duration: '2-4 分钟',
      icon: <GeminiIcon />
    }
  ];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button>
          发布到 WordPress
          <ChevronDownIcon className="ml-2" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-80">
        {providers.map(provider => (
          <DropdownMenuItem
            key={provider.id}
            onClick={() => onSelect(provider.id)}
            className="p-4"
          >
            <div className="flex items-start gap-3">
              {provider.icon}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{provider.name}</span>
                  {provider.recommended && (
                    <Badge variant="success">推荐</Badge>
                  )}
                </div>
                <p className="text-sm text-gray-600">{provider.description}</p>
                <div className="flex gap-4 mt-1 text-xs text-gray-500">
                  <span>💰 {provider.cost}</span>
                  <span>⏱️ {provider.duration}</span>
                </div>
              </div>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

---

##### T-UI-2.1.3 [P0] Implement Publish Confirmation Dialog

**Priority**: 🔴 Critical
**Estimated Hours**: 6 hours

**Acceptance Criteria**:
- [ ] 显示文章标题和 Provider
- [ ] 显示预估成本和时间
- [ ] 确认按钮 + 取消按钮
- [ ] 可选：预览 SEO 元数据

---

##### T-UI-2.1.4 [P0] Implement Publish Progress Modal

**Priority**: 🔴 Critical
**Estimated Hours**: 10 hours

**Description**:
实时发布进度弹窗，轮询任务状态

**Acceptance Criteria**:
- [ ] 轮询 `/v1/publish/tasks/{task_id}/status` 每 2 秒
- [ ] 进度条（基于步骤数）
- [ ] 当前步骤显示 + 加载动画
- [ ] 预估剩余时间
- [ ] 成功时显示文章 URL
- [ ] 失败时显示错误信息 + 截图

**Code Example**:
```tsx
import { useQuery } from '@tanstack/react-query';

export function PublishProgressModal({ taskId, onClose }) {
  const { data: taskStatus } = useQuery({
    queryKey: ['publishTask', taskId],
    queryFn: () => getTaskStatus(taskId),
    refetchInterval: (data) => {
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false; // Stop polling
      }
      return 2000; // Poll every 2 seconds
    }
  });

  const steps = [
    'Logging in to WordPress',
    'Creating new post',
    'Filling content',
    'Uploading images',
    'Configuring SEO',
    'Setting categories',
    'Publishing',
    'Verifying'
  ];

  const currentStep = taskStatus?.current_step || 0;
  const progress = (currentStep / steps.length) * 100;

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>正在发布文章...</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <ProgressBar value={progress} />

          <div className="flex items-center gap-3">
            <Spinner className="animate-spin" />
            <span className="text-sm">{steps[currentStep]}</span>
          </div>

          <div className="text-sm text-gray-600">
            已用时间: {formatDuration(taskStatus?.elapsed_seconds)}
            {taskStatus?.estimated_remaining_seconds && (
              <> · 预计剩余: {formatDuration(taskStatus.estimated_remaining_seconds)}</>
            )}
          </div>

          {taskStatus?.status === 'completed' && (
            <PublishSuccessCard
              url={taskStatus.published_url}
              duration={taskStatus.duration_seconds}
            />
          )}

          {taskStatus?.status === 'failed' && (
            <PublishErrorCard
              error={taskStatus.error_message}
              screenshot={taskStatus.error_screenshot}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

##### T-UI-2.1.5-8 [High] Additional Publishing Components

- **T-UI-2.1.5**: `CurrentStepDisplay.tsx` (4h)
- **T-UI-2.1.6**: `ScreenshotGallery.tsx` (8h) - 带 Lightbox
- **T-UI-2.1.7**: `PublishSuccessCard.tsx` (4h)
- **T-UI-2.1.8**: `PublishErrorCard.tsx` (4h)

---

#### Task Group 2.2: Task Monitoring UI (Module 4) - 44 hours

**目标**: 实现发布任务监控面板

##### T-UI-2.2.1 [High] Create Publish Tasks Page

**Priority**: 🟡 High
**Estimated Hours**: 6 hours

**Description**:
任务监控页面，显示所有发布任务

**Deliverables**:
- `frontend/src/pages/PublishTasksPage.tsx`

**Acceptance Criteria**:
- [ ] 路由：`/tasks`
- [ ] 包含任务列表表格
- [ ] 包含过滤器
- [ ] 包含刷新按钮

---

##### T-UI-2.2.2 [High] Implement Task List Table

**Priority**: 🟡 High
**Estimated Hours**: 8 hours

**Description**:
任务列表表格，支持排序、过滤、分页

**Acceptance Criteria**:
- [ ] 列：文章标题、Provider、状态、耗时、成本、操作
- [ ] 状态徽章（颜色编码）
- [ ] 点击行打开详情抽屉
- [ ] 排序：创建时间倒序
- [ ] 分页：20 条/页

---

##### T-UI-2.2.3-7 [High/Medium] Additional Monitoring Components

- **T-UI-2.2.3**: `TaskStatusBadge.tsx` (2h)
- **T-UI-2.2.4**: `TaskDetailDrawer.tsx` (8h)
- **T-UI-2.2.5**: `ExecutionLogsViewer.tsx` (6h)
- **T-UI-2.2.6**: `ScreenshotLightbox.tsx` (6h)
- **T-UI-2.2.7**: `TaskFilters.tsx` (4h)

---

## Phase 2: Enhancement Features (Week 5-6)

### Week 5-6: Provider Comparison + Settings

#### Task Group 3.1: Provider Comparison Dashboard (Module 5) - 30 hours

##### T-UI-3.1.1-6 [Medium] Comparison Components

- **T-UI-3.1.1**: `ProviderComparisonPage.tsx` (6h)
- **T-UI-3.1.2**: `MetricsComparisonTable.tsx` (6h)
- **T-UI-3.1.3**: `SuccessRateLineChart.tsx` (6h)
- **T-UI-3.1.4**: `CostComparisonBarChart.tsx` (4h)
- **T-UI-3.1.5**: `TaskDistributionPieChart.tsx` (4h)
- **T-UI-3.1.6**: `RecommendationCard.tsx` (4h)

---

#### Task Group 3.2: Settings Page (Module 6) - 22 hours

##### T-UI-3.2.1-5 [Medium] Settings Components

- **T-UI-3.2.1**: `SettingsPage.tsx` (4h)
- **T-UI-3.2.2**: `ProviderConfigSection.tsx` (4h)
- **T-UI-3.2.3**: `CMSConfigSection.tsx` (6h)
- **T-UI-3.2.4**: `CostLimitsSection.tsx` (4h)
- **T-UI-3.2.5**: `ScreenshotRetentionSection.tsx` (4h)

---

#### Task Group 3.3: Backend Provider Metrics APIs - 16 hours

##### T-BE-3.3.1 [Medium] Implement Provider Metrics APIs

**Endpoints**:
```python
@router.get("/v1/metrics/provider-comparison")
async def get_provider_comparison() -> ProviderComparisonResponse:
    """获取 Provider 对比数据"""
    pass

@router.get("/v1/metrics/costs/monthly")
async def get_monthly_costs() -> MonthlyCostsResponse:
    """获取月度成本统计"""
    pass
```

---

#### Task Group 3.4: E2E Testing - 20 hours

##### T-TEST-3.4.1 [P0] E2E Test Suite

**Test Scenarios**:
- [ ] Complete workflow: Import → SEO → Publish → Monitor
- [ ] CSV upload → validation errors
- [ ] Manual article form → required fields
- [ ] SEO analysis → edit metadata → save
- [ ] Publish with Playwright → view progress → check screenshots
- [ ] Publish failure → view error → retry
- [ ] Task filtering and sorting
- [ ] Provider comparison dashboard

---

## 总结

### 工时分布

| 模块 | 前端工时 | 后端工时 | 测试工时 | 总计 |
|------|---------|---------|---------|------|
| Module 1: Article Import | 50h | 26h | - | 76h |
| Module 2: SEO Optimization | 42h | 14h | - | 56h |
| Module 3: Publishing UI | 48h | - | - | 48h |
| Module 4: Monitoring UI | 44h | - | - | 44h |
| Module 5: Comparison Dashboard | 30h | 16h | - | 46h |
| Module 6: Settings | 22h | - | - | 22h |
| E2E Testing | - | - | 20h | 20h |
| **总计** | **236h** | **56h** | **20h** | **312h** |

**团队配置**:
- 2 名前端工程师 × 6 周 = 240 小时
- 1 名后端工程师 × 6 周 = 240 小时（其他时间用于维护）
- QA 工程师兼职测试

---

**下一步**: 开始实施 Phase 1 Week 1 任务（Article Import UI）
