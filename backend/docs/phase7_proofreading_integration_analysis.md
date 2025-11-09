# Phase 7 与 Proofreading 集成需求分析

**文档版本**: 1.0
**创建日期**: 2025-11-08
**状态**: 待实施

---

## 📋 1. 问题陈述

### 1.1 当前实现的问题

**发现的不一致性**:
```
目前 Proofreading 阶段使用 article.body 进行校对
而 Phase 7 Parsing 已经将文章分解为：
- title_prefix, title_main, title_suffix (标题组件)
- author_name, author_line (作者信息)
- body_html (清理后的正文)
- meta_description, seo_keywords (SEO 元数据)
```

**问题**:
- ❌ Proofreading 校对的是 `article.body`（包含标题、作者、原始格式）
- ✅ 应该校对的是 `article.body_html`（只包含正文内容）

**影响**:
1. 校对范围过大，包含了不应校对的结构化数据
2. 重复校对已提取的标题和作者信息
3. 校对结果可能与已确认的解析数据冲突
4. 用户体验混乱（解析时已确认，校对时又提示修改）

---

## 🎯 2. 需求定义

### 2.1 功能需求

**FR-1: Proofreading 内容范围**
```
描述: Proofreading 应该只校对文章正文内容
优先级: P0 (Critical)
验收标准:
- Proofreading 使用 article.body_html 作为校对内容
- 不校对已提取的标题、作者等结构化字段
- 校对结果只针对正文内容
```

**FR-2: 工作流程依赖**
```
描述: Proofreading 依赖于 Parsing 完成
优先级: P0 (Critical)
验收标准:
- 未解析的文章无法进行校对
- API 返回明确的错误提示
- 前端引导用户先进行解析
```

**FR-3: 向后兼容性**
```
描述: 支持未解析的旧文章
优先级: P1 (High)
验收标准:
- 未解析的文章可以使用 article.body 进行校对
- 有明确的提示建议先进行解析
- 不影响现有工作流程
```

**FR-4: 数据一致性**
```
描述: 确保解析和校对数据不冲突
优先级: P0 (Critical)
验收标准:
- 校对结果只更新 body_html
- 不修改已确认的 title_main, author_name 等字段
- 提供合并校对结果的 API
```

### 2.2 非功能需求

**NFR-1: 性能**
```
- Proofreading API 响应时间 < 5 秒
- 不增加额外的数据库查询
```

**NFR-2: 可维护性**
```
- 清晰的代码注释说明逻辑变更
- 完整的测试覆盖
- 详细的 API 文档
```

**NFR-3: 用户体验**
```
- 清晰的错误提示
- 前端流程引导
- 状态可视化
```

---

## 🔄 3. 工作流程设计

### 3.1 理想工作流程（新文章）

```
┌─────────────────────┐
│  1. Import Article  │  从 Google Docs 导入
│     raw_html        │  保存原始 HTML
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  2. Parse Article   │  Phase 7 结构化解析
│     ├─ title_*      │  提取标题组件
│     ├─ author_*     │  提取作者信息
│     ├─ body_html    │  提取清理后正文
│     └─ seo_*        │  提取 SEO 元数据
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. Review Parsing  │  用户审核解析结果
│     ├─ 检查标题     │
│     ├─ 检查作者     │
│     ├─ 管理图片     │
│     └─ 确认         │  parsing_confirmed = true
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  4. Proofread       │  校对正文
│     (body_html)     │  只校对正文内容
│                     │  不校对已确认的结构化数据
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  5. Apply Changes   │  应用校对修改
│     更新 body_html  │  用户接受/拒绝建议
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  6. Publish         │  发布到 WordPress
│     使用所有确认字段 │
└─────────────────────┘
```

### 3.2 兼容工作流程（旧文章）

```
┌─────────────────────┐
│  Legacy Article     │  已存在的文章
│  (only has body)    │  只有 article.body
└──────────┬──────────┘
           │
           ├─ Option A: 解析后校对 (推荐)
           │  └─> Parse → Proofread → Publish
           │
           └─ Option B: 直接校对 (兼容)
              └─> Proofread(body) → Publish
                  ⚠️ 显示警告：建议先解析
```

### 3.3 状态转换

```
Article Status Flow:

imported
   │
   ├─> parse_article()
   │   └─> parsing_confirmed = false
   │       │
   │       ├─> confirm_parsing()
   │       │   └─> parsing_confirmed = true
   │       │       │
   │       │       └─> proofread_article()  ← 使用 body_html
   │       │           │
   │       │           └─> publish_article()
   │       │
   │       └─> re-parse (如果不满意)
   │
   └─> proofread_article()  ← 兼容模式：使用 body
       ⚠️ Warning: 建议先解析
```

---

## 🛠️ 4. 实施方案

### 4.1 代码修改点

#### **Modification 1: 更新 Proofreading Content Source**

**文件**: `src/api/routes/articles.py`
**函数**: `_build_article_payload()`

```python
def _build_article_payload(article: Article) -> ArticlePayload:
    """Convert Article ORM object to Proofreading service payload.

    Priority Logic (Phase 7 Integration):
    1. If article.body_html exists (parsed) → use it for proofreading
    2. Otherwise fallback to article.body (legacy/unparsed articles)

    This ensures:
    - Parsed articles: only proofread the cleaned body content
    - Unparsed articles: still work but with a warning
    """
    metadata = dict(article.article_metadata or {})

    # Phase 7: Determine content to proofread
    has_been_parsed = bool(article.body_html)
    content_to_proofread = article.body_html if has_been_parsed else article.body or ""

    sections = _extract_article_sections(metadata, content_to_proofread)

    # Prefer parsed body_html for HTML content
    html_content = (
        article.body_html                    # Phase 7: parsed clean body
        or metadata.get("rendered_html")     # Fallback: metadata
        or metadata.get("html")
        or article.body                      # Final fallback: original body
    )

    target_locale = (
        metadata.get("locale")
        or metadata.get("language")
        or metadata.get("target_locale")
        or "zh-TW"
    )

    # Add parsing status to metadata for downstream processing
    parsing_metadata = {
        "parsed": has_been_parsed,
        "parsing_confirmed": article.parsing_confirmed,
    }
    if has_been_parsed:
        parsing_metadata.update({
            "title_components": {
                "prefix": article.title_prefix,
                "main": article.title_main,
                "suffix": article.title_suffix,
            },
            "author": {
                "name": article.author_name,
                "line": article.author_line,
            }
        })

    metadata["parsing"] = parsing_metadata

    return ArticlePayload(
        article_id=article.id,
        title=article.title,
        original_content=content_to_proofread,   # ← CHANGED
        html_content=html_content,               # ← CHANGED
        sections=sections,
        metadata=metadata,                       # ← ENHANCED
        featured_image=_build_featured_image_metadata(article, metadata),
        images=_build_inline_images(article, metadata),
        keywords=_extract_keywords(metadata),
        target_locale=target_locale,
    )
```

**变更理由**:
1. 优先使用 `body_html`（解析后的清理正文）
2. 保持向后兼容（未解析文章使用 `body`）
3. 在 metadata 中传递解析状态，便于下游处理

#### **Modification 2: 添加解析前置检查（可选但推荐）**

**文件**: `src/api/routes/articles.py`
**函数**: `proofread_article()`

```python
@router.post("/{article_id}/proofread", response_model=ProofreadingResponse)
async def proofread_article(
    article_id: int,
    session: AsyncSession = Depends(get_session),
    skip_parsing_check: bool = False,  # 兼容性参数
) -> ProofreadingResponse:
    """Run unified proofreading (AI + deterministic checks) for an article.

    Phase 7 Integration:
    - Prefers to proofread parsed articles (body_html)
    - For unparsed articles: works but returns a warning
    - Set skip_parsing_check=true to force proofreading unparsed articles
    """
    article = await _fetch_article(session, article_id)

    # Phase 7: Check if article has been parsed
    if not article.body_html and not skip_parsing_check:
        logger.warning(
            "proofreading_unparsed_article",
            article_id=article_id,
            has_body=bool(article.body),
        )
        # Option A: 返回错误 (严格模式)
        # raise HTTPException(
        #     status_code=status.HTTP_400_BAD_REQUEST,
        #     detail={
        #         "error": "article_not_parsed",
        #         "message": "Article must be parsed before proofreading",
        #         "suggestion": f"Parse the article first: POST /v1/articles/{article_id}/parse",
        #         "can_skip": True,
        #     }
        # )

        # Option B: 继续但添加警告 (兼容模式) ← 推荐
        # 警告会在响应中返回

    payload = _build_article_payload(article)
    service = _get_proofreading_service()

    try:
        result = await service.analyze_article(payload)
    except Exception as exc:
        logger.error(
            "proofreading_analysis_failed",
            article_id=article_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Proofreading analysis failed. Please retry later.",
        ) from exc

    # Phase 7: Add warning if article wasn't parsed
    if not article.body_html:
        if not hasattr(result, 'warnings'):
            result.warnings = []
        result.warnings.insert(0, {
            "type": "workflow_suggestion",
            "message": "建议先进行文章解析以获得更准确的校对结果",
            "suggestion": f"解析文章: POST /v1/articles/{article_id}/parse",
            "severity": "info",
        })

    article.proofreading_issues = [
        issue.model_dump(mode="json") for issue in result.issues
    ]
    article.critical_issues_count = result.statistics.blocking_issue_count
    article.article_metadata = _merge_proofreading_metadata(
        article.article_metadata, result.model_dump(mode="json")
    )

    session.add(article)
    await session.commit()

    return ProofreadingResponse.model_validate(result.model_dump())
```

**变更理由**:
1. 兼容性优先：不强制要求解析
2. 提供清晰的警告引导用户
3. 允许通过参数跳过检查

#### **Modification 3: 更新 Proofreading 结果应用逻辑**

**文件**: `src/api/routes/proofreading_decisions.py`（或相应的应用修改接口）

```python
@router.post("/{article_id}/apply-proofreading")
async def apply_proofreading_changes(
    article_id: int,
    changes: ProofreadingChanges,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Apply proofreading changes to article.

    Phase 7 Integration:
    - Updates body_html if article has been parsed
    - Updates body if article hasn't been parsed
    - Never modifies title_main, author_name (already confirmed in parsing)
    """
    article = await _fetch_article(session, article_id)

    # Phase 7: Apply changes to the correct field
    if article.body_html:
        # Parsed article: update body_html
        article.body_html = changes.corrected_content
        logger.info(
            "applied_proofreading_to_parsed_article",
            article_id=article_id,
            field="body_html"
        )
    else:
        # Unparsed article: update body (legacy)
        article.body = changes.corrected_content
        logger.warning(
            "applied_proofreading_to_unparsed_article",
            article_id=article_id,
            field="body",
            recommendation="Consider parsing article first"
        )

    # Mark proofreading as complete
    article.proofreading_completed = True
    article.proofreading_completed_at = datetime.utcnow()

    await session.commit()

    return {
        "success": True,
        "article_id": article_id,
        "updated_field": "body_html" if article.body_html else "body",
        "changes_applied": len(changes.applied_issues),
    }
```

### 4.2 数据库 Schema 扩展（可选）

**可能需要的新字段**:

```python
# 添加到 Article 模型
proofreading_completed: Mapped[bool] = mapped_column(
    nullable=False,
    default=False,
    comment="Proofreading stage completed"
)
proofreading_completed_at: Mapped[datetime | None] = mapped_column(
    nullable=True,
    comment="Timestamp when proofreading was completed"
)
```

**Migration 文件**: `migrations/versions/20251108_add_proofreading_completion.py`

---

## 🧪 5. 测试方案

### 5.1 单元测试

#### **Test Suite 1: Payload Construction**

**文件**: `tests/unit/test_articles_proofreading_integration.py`

```python
class TestProofreadingPayloadConstruction:
    """测试 Proofreading payload 构建逻辑"""

    def test_parsed_article_uses_body_html(self):
        """测试解析后的文章使用 body_html"""
        article = Article(
            id=1,
            title="Test",
            body="原始内容包含标题和作者",
            body_html="<p>清理后的正文</p>",  # Phase 7 提取
            title_main="测试标题",
            author_name="张三",
        )

        payload = _build_article_payload(article)

        assert payload.original_content == "<p>清理后的正文</p>"
        assert payload.html_content == "<p>清理后的正文</p>"
        assert payload.metadata["parsing"]["parsed"] is True
        assert payload.metadata["parsing"]["title_components"]["main"] == "测试标题"

    def test_unparsed_article_uses_body(self):
        """测试未解析的文章使用 body"""
        article = Article(
            id=1,
            title="Test",
            body="原始内容",
            body_html=None,  # 未解析
        )

        payload = _build_article_payload(article)

        assert payload.original_content == "原始内容"
        assert payload.metadata["parsing"]["parsed"] is False

    def test_empty_article_handles_gracefully(self):
        """测试空文章的处理"""
        article = Article(id=1, title="Test")

        payload = _build_article_payload(article)

        assert payload.original_content == ""
        assert payload.html_content is not None
```

#### **Test Suite 2: Proofreading Endpoint**

```python
class TestProofreadingEndpoint:
    """测试 Proofreading API endpoint"""

    @pytest.mark.asyncio
    async def test_proofread_parsed_article(self, db_session, client):
        """测试校对已解析的文章"""
        article = Article(
            title="Test",
            body_html="<p>正文内容有一个拼写错误：測試</p>",
            title_main="测试标题",
            parsing_confirmed=True,
        )
        db_session.add(article)
        await db_session.commit()

        response = await client.post(f"/v1/articles/{article.id}/proofread")

        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        # 验证只检查了正文，没有检查标题

    @pytest.mark.asyncio
    async def test_proofread_unparsed_article_shows_warning(self, db_session, client):
        """测试校对未解析文章时显示警告"""
        article = Article(
            title="Test",
            body="原始内容",
            body_html=None,
        )
        db_session.add(article)
        await db_session.commit()

        response = await client.post(f"/v1/articles/{article.id}/proofread")

        assert response.status_code == 200
        data = response.json()
        assert "warnings" in data
        assert any("解析" in w.get("message", "") for w in data["warnings"])
```

### 5.2 集成测试

#### **Test Suite 3: Complete Workflow**

**文件**: `tests/integration/test_parsing_proofreading_workflow.py`

```python
class TestParsingProofreadingWorkflow:
    """测试完整的 Parsing → Proofreading 工作流"""

    @pytest.mark.asyncio
    async def test_complete_workflow_parsed_then_proofread(self, client, db_session):
        """测试：导入 → 解析 → 确认 → 校对"""

        # Step 1: Create article with raw HTML
        article = Article(
            title="Workflow Test",
            raw_html="""
                <h1>【專題】測試標題：副標題</h1>
                <p>文／張三</p>
                <p>這是正文内容，有一些錯誤需要校對。</p>
            """,
            status="imported",
        )
        db_session.add(article)
        await db_session.commit()
        article_id = article.id

        # Step 2: Parse article
        parse_response = await client.post(
            f"/v1/articles/{article_id}/parse",
            json={"use_ai": False, "download_images": False}
        )
        assert parse_response.status_code == 200

        # Step 3: Get parsing result
        result_response = await client.get(
            f"/v1/articles/{article_id}/parsing-result"
        )
        assert result_response.status_code == 200
        parsing_data = result_response.json()
        assert parsing_data["title_main"] == "測試標題"
        assert parsing_data["author_name"] == "張三"

        # Step 4: Confirm parsing
        confirm_response = await client.post(
            f"/v1/articles/{article_id}/confirm-parsing",
            json={"confirmed_by": "test_user"}
        )
        assert confirm_response.status_code == 200

        # Step 5: Proofread (should only check body_html)
        proofread_response = await client.post(
            f"/v1/articles/{article_id}/proofread"
        )
        assert proofread_response.status_code == 200
        proofread_data = proofread_response.json()

        # Verify: no warnings about parsing
        if "warnings" in proofread_data:
            assert not any("解析" in str(w) for w in proofread_data["warnings"])

        # Verify: issues only in body, not in title/author
        # (具体验证逻辑取决于 proofreading 返回格式)

    @pytest.mark.asyncio
    async def test_unparsed_article_proofreading_compatibility(self, client, db_session):
        """测试：未解析文章的兼容性"""

        # Create unparsed article
        article = Article(
            title="Legacy Article",
            body="This is the original body content.",
            status="draft",
        )
        db_session.add(article)
        await db_session.commit()

        # Proofread without parsing
        response = await client.post(f"/v1/articles/{article.id}/proofread")

        assert response.status_code == 200
        data = response.json()

        # Should have warning about parsing
        assert "warnings" in data
        assert any("解析" in str(w) for w in data["warnings"])
```

### 5.3 回归测试

确保修改不影响现有功能：

```python
class TestBackwardCompatibility:
    """回归测试：确保向后兼容性"""

    @pytest.mark.asyncio
    async def test_existing_proofreading_still_works(self, client, db_session):
        """测试现有的 proofreading 功能仍然正常"""
        # 使用旧数据结构的文章
        article = Article(title="Old", body="Content", status="draft")
        db_session.add(article)
        await db_session.commit()

        response = await client.post(f"/v1/articles/{article.id}/proofread")
        assert response.status_code == 200
```

### 5.4 性能测试

```python
class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_proofreading_performance(self, client, db_session):
        """测试 proofreading 响应时间"""
        import time

        article = create_large_article(word_count=5000)  # 5000 字文章
        db_session.add(article)
        await db_session.commit()

        start = time.time()
        response = await client.post(f"/v1/articles/{article.id}/proofread")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 5.0  # 应在 5 秒内完成
```

---

## 📚 6. 文档更新

### 6.1 需要更新的文档

1. **API 文档** (`docs/phase7_parsing_api.md`)
   - 添加 Proofreading 集成说明
   - 更新工作流程图

2. **SpecKit** (`specs/001-cms-automation/`)
   - `spec.md`: 更新 Phase 7 功能描述
   - `plan.md`: 添加 Proofreading 集成任务
   - `tasks.md`: 添加新的实施任务

3. **架构文档**
   - 更新数据流图
   - 更新状态转换图

---

## 📊 7. 实施计划

### 7.1 任务分解

| 任务 ID | 任务名称 | 估时 | 优先级 | 依赖 |
|---------|----------|------|--------|------|
| T7.19 | 更新 payload 构建逻辑 | 2h | P0 | - |
| T7.20 | 添加解析前置检查 | 1h | P1 | T7.19 |
| T7.21 | 更新校对结果应用逻辑 | 1.5h | P0 | T7.19 |
| T7.22 | 编写单元测试 | 2h | P0 | T7.19-21 |
| T7.23 | 编写集成测试 | 2h | P0 | T7.19-21 |
| T7.24 | 更新 API 文档 | 1h | P1 | T7.19-21 |
| T7.25 | 更新 SpecKit | 1.5h | P1 | All |

**总计**: ~11 小时

### 7.2 实施顺序

```
Phase 1: 核心逻辑修改 (3.5h)
├─ T7.19: 更新 payload 构建
├─ T7.20: 添加前置检查
└─ T7.21: 更新结果应用

Phase 2: 测试 (4h)
├─ T7.22: 单元测试
└─ T7.23: 集成测试

Phase 3: 文档 (2.5h)
├─ T7.24: API 文档
└─ T7.25: SpecKit
```

---

## ✅ 8. 验收标准

### 8.1 功能验收

- [ ] 解析后的文章校对只检查 `body_html`
- [ ] 未解析的文章可以校对但有警告提示
- [ ] 校对结果正确应用到对应字段
- [ ] 不修改已确认的结构化字段

### 8.2 测试验收

- [ ] 单元测试覆盖率 > 90%
- [ ] 所有集成测试通过
- [ ] 回归测试全部通过
- [ ] 性能测试达标 (< 5s)

### 8.3 文档验收

- [ ] API 文档完整准确
- [ ] SpecKit 更新完整
- [ ] 代码注释清晰
- [ ] 示例代码可运行

---

## 🚨 9. 风险与缓解

### 9.1 已识别风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 破坏现有 Proofreading 功能 | 高 | 中 | 完整回归测试 + 向后兼容设计 |
| 性能下降 | 中 | 低 | 性能测试 + 优化查询 |
| 数据迁移问题 | 中 | 低 | 不需要数据迁移，只是逻辑调整 |
| 用户困惑 | 中 | 中 | 清晰的 UI 提示 + 文档 |

### 9.2 回滚计划

如果出现问题：
1. 通过 git revert 回滚代码
2. 添加 feature flag 控制新逻辑
3. 逐步灰度发布

---

## 📝 10. 附录

### 10.1 相关文件清单

**后端代码**:
- `src/api/routes/articles.py` (修改)
- `src/api/routes/proofreading_decisions.py` (修改)
- `src/models/article.py` (可能扩展)

**测试代码**:
- `tests/unit/test_articles_proofreading_integration.py` (新增)
- `tests/integration/test_parsing_proofreading_workflow.py` (新增)

**文档**:
- `docs/phase7_parsing_api.md` (更新)
- `specs/001-cms-automation/spec.md` (更新)
- `specs/001-cms-automation/plan.md` (更新)
- `specs/001-cms-automation/tasks.md` (更新)

### 10.2 技术参考

- Phase 7 Parsing Spec
- Proofreading Service Architecture
- Article Data Model Schema
- API 设计指南

---

**文档维护者**: CMS Development Team
**最后更新**: 2025-11-08
**审核状态**: 待审核
