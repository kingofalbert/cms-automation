# 校对审核页面 - 设计规格总结

**Feature ID:** 003-proofreading-review-ui
**Status:** 📝 Design Complete - Ready for Implementation
**Priority:** P0 (Critical Path)
**Created:** 2025-11-07
**Estimated Effort:** 7-9 days

---

## 📖 Document Index

本feature的完整设计文档包括以下部分：

1. **[requirements-analysis.md](./requirements-analysis.md)** - 需求分析
   - 核心需求定义（FR-001 ~ FR-008）
   - 工作流程上下文
   - 用户场景
   - API需求

2. **[ui-design-spec.md](./ui-design-spec.md)** - UI设计规格
   - 页面布局设计（Desktop & Mobile）
   - 组件详细规格（6个主要组件）
   - 交互动画
   - 响应式设计
   - 键盘快捷键
   - 颜色系统

3. **[api-contracts.md](./api-contracts.md)** - API契约
   - 已存在API：`GET /v1/worklist/{id}`（需增强）
   - 新增API：`POST /v1/worklist/{id}/review-decisions`（核心）
   - 可选API：批量决策、历史记录
   - 数据模型定义（TypeScript & Python）

4. **[testing-acceptance.md](./testing-acceptance.md)** - 测试规格
   - 7个E2E测试套件（Playwright）
   - 单元测试规格（Vitest）
   - 23项验收标准
   - 性能基准
   - CI/CD集成

---

## 🎯 Feature Overview

### 核心价值

校对审核页面是CMS自动化工作流的**关键人工介入点**，连接AI自动校对引擎和最终发布决策：

```
Google Drive (原始文档)
      ↓ 自动同步
Worklist (status: pending)
      ↓ 自动创建Article
Article (status: imported)
      ↓ 自动校对 (AI + Rules)
Article (status: in-review) + Worklist (status: under_review)
      ↓ ⭐ 人工审核 (本页面) ⭐
Article (status: ready_to_publish) + Worklist (status: ready_to_publish)
      ↓ 发布
Published
```

### 主要功能

1. **问题展示** - 左侧列表展示所有校对问题（支持过滤、排序、搜索）
2. **文章渲染** - 中间区域渲染文章，高亮标注问题位置
3. **决策面板** - 右侧面板提供决策操作（接受/拒绝/自定义修改）
4. **批量操作** - 多选问题批量决策
5. **实时预览** - 预览应用修改后的文章效果
6. **保存提交** - 保存决策并转换worklist状态

---

## 🏗️ Architecture

### Frontend Architecture

```
ProofreadingReviewPage (Container)
├── ProofreadingReviewHeader (Top Bar)
├── ReviewStatsBar (Sub-header)
├── Layout (3-Column)
│   ├── ProofreadingIssueList (Left - 20%)
│   │   ├── FilterControls
│   │   ├── IssueSearchInput
│   │   ├── IssueListItem (x N)
│   │   └── BatchActionBar
│   ├── ProofreadingArticleContent (Center - 50%)
│   │   ├── ArticleHeader
│   │   └── ContentWithHighlights
│   └── ProofreadingIssueDetailPanel (Right - 30%)
│       ├── IssueMetadata
│       ├── OriginalVsSuggested
│       ├── Explanation
│       ├── DecisionActions
│       ├── CustomModificationInput
│       ├── DecisionRationaleInput
│       └── FeedbackAccordion
└── ProgressFooterBar (Bottom)
```

### State Management

```typescript
// Zustand Store
interface DecisionStore {
  decisions: Record<string, DecisionPayload>;
  selectedIssue: ProofreadingIssue | null;
  filters: FilterState;
  viewMode: 'original' | 'preview' | 'diff';

  // Actions
  addDecision: (issueId: string, decision: Partial<DecisionPayload>) => void;
  batchAddDecisions: (issueIds: string[], decision: Partial<DecisionPayload>) => void;
  clearDecision: (issueId: string) => void;
  setSelectedIssue: (issue: ProofreadingIssue | null) => void;
  setFilters: (filters: Partial<FilterState>) => void;
  setViewMode: (mode: ViewMode) => void;

  // Computed
  getDirtyCount: () => number;
  getStats: () => DecisionStats;
  isDecided: (issueId: string) => boolean;
}
```

### Data Flow

```
User Action (UI) → Zustand Store Update → React Re-render
                                             ↓
                                    (Optimistic Update)
                                             ↓
                                    Background API Call
                                             ↓
                                    Server Response
                                             ↓
                                    Store Sync
                                             ↓
                                    UI Confirmation
```

---

## 🛠️ Implementation Plan

### Phase 1: Core Functionality (Days 1-4)

**Backend (Day 1-2):**
- [ ] Enhance `GET /v1/worklist/{id}` API
  - Add `proofreading_issues` field
  - Add `proofreading_stats` field
  - Include decision status for each issue
- [ ] Implement `POST /v1/worklist/{id}/review-decisions` API
  - Create ProofreadingDecision records
  - Update worklist/article status
  - Create ArticleStatusHistory records
- [ ] Add validation and error handling
- [ ] Write backend unit tests

**Frontend (Day 3-4):**
- [ ] Create page route `/worklist/:id/review`
- [ ] Implement ProofreadingReviewPage container
- [ ] Implement ProofreadingIssueList component
- [ ] Implement IssueListItem component
- [ ] Implement basic decision actions (accept/reject)
- [ ] Integrate with API
- [ ] Add loading/error states

### Phase 2: Enhanced Interactions (Days 5-6)

**Frontend:**
- [ ] Implement ProofreadingArticleContent with highlighting
- [ ] Implement ProofreadingIssueDetailPanel
- [ ] Add issue navigation (prev/next)
- [ ] Add custom modification input
- [ ] Add decision rationale input
- [ ] Add feedback accordion
- [ ] Implement filter controls
- [ ] Implement search functionality
- [ ] Add keyboard shortcuts
- [ ] Add scroll-to-issue functionality

### Phase 3: Advanced Features (Day 7)

**Frontend:**
- [ ] Implement batch selection
- [ ] Implement batch actions (accept/reject)
- [ ] Implement preview mode
- [ ] Implement diff mode
- [ ] Add progress footer bar
- [ ] Add save draft functionality
- [ ] Add complete review flow

### Phase 4: Polish & Testing (Days 8-9)

**Frontend:**
- [ ] Responsive layout for mobile/tablet
- [ ] Performance optimization (virtual scrolling)
- [ ] Accessibility improvements
- [ ] Animation polish
- [ ] Error handling refinement

**Testing:**
- [ ] Write E2E tests (7 test suites)
- [ ] Write unit tests for stores
- [ ] Write component tests
- [ ] Manual QA testing
- [ ] Performance testing

**Documentation:**
- [ ] Update user guide
- [ ] Update developer docs
- [ ] Create demo video

---

## 📦 Technical Dependencies

### Frontend Libraries

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0",
    "react-hotkeys-hook": "^4.4.0",
    "lucide-react": "^0.263.1",
    "@radix-ui/react-accordion": "^1.1.2",
    "@radix-ui/react-checkbox": "^1.0.4",
    "@radix-ui/react-radio-group": "^1.1.3",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-toggle-group": "^1.0.4"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0"
  }
}
```

### Backend Dependencies

```toml
[tool.poetry.dependencies]
# Already installed:
fastapi = "^0.104.0"
sqlalchemy = "^2.0.0"
pydantic = "^2.5.0"
asyncpg = "^0.29.0"

# No new dependencies needed
```

---

## 🎨 Design System Integration

### Components Used

From existing Design System (`/frontend/src/components/ui/`):
- ✅ Button
- ✅ Input
- ✅ Textarea
- ✅ Select
- ✅ Checkbox
- ✅ RadioGroup
- ✅ Badge
- ✅ Separator
- ✅ Accordion
- ✅ ToggleGroup
- ✅ Skeleton
- ✅ Toast

### Color Palette

```css
/* Severity Colors */
--critical: #EF4444 (red-500)
--warning: #F59E0B (yellow-500)
--info: #3B82F6 (blue-500)

/* Decision Status Colors */
--accepted: #10B981 (green-500)
--rejected: #9CA3AF (gray-400)
--modified: #A855F7 (purple-500)
--pending: #D1D5DB (gray-300)

/* UI Colors */
--primary: #2563EB (blue-600)
--secondary: #4B5563 (gray-600)
--background: #FFFFFF (white)
--surface: #F9FAFB (gray-50)
--border: #E5E7EB (gray-200)
```

---

## 📊 Success Metrics

### Quantitative Metrics

1. **Adoption Rate**: ≥ 95% of articles pass through review page
2. **Average Review Time**: < 10 minutes per article
3. **Decision Rate**: ≥ 90% of issues decided
4. **Error Rate**: < 1% of reviews fail to save
5. **Performance**: Page load < 2s (p95)

### Qualitative Metrics

1. **User Satisfaction**: ≥ 4.5/5 rating from reviewers
2. **Ease of Use**: ≥ 80% of users complete review without help
3. **Feature Discovery**: ≥ 70% of users use keyboard shortcuts within 1 week

---

## 🚧 Known Limitations & Future Enhancements

### Current Limitations

1. **No Real-time Collaboration**: Multiple users cannot review同时 the same article
2. **No Undo/Redo**: Cannot undo decisions after saving
3. **Limited Issue Types**: Only supports text-based issues
4. **No Offline Support**: Requires network connection

### Future Enhancements (Out of Scope)

1. **Real-time Collaboration**
   - WebSocket integration
   - Live cursor indicators
   - Conflict resolution

2. **AI-Assisted Review**
   - Smart recommendations based on history
   - Auto-accept high-confidence suggestions
   - Pattern learning from user decisions

3. **Advanced Visualizations**
   - Issue heatmap
   - Review analytics dashboard
   - Quality score trends

4. **Batch Review Mode**
   - Review multiple articles in sequence
   - Carry over decision patterns

5. **Mobile App**
   - Native iOS/Android apps
   - Offline review capability

---

## 🔒 Security Considerations

### Authentication & Authorization

- All API calls require JWT authentication
- Role-based access control (RBAC):
  - `reviewer`: Can make decisions
  - `admin`: Can make decisions + force publish
  - `viewer`: Read-only access

### Data Privacy

- Decisions are logged with user ID for audit
- Sensitive content is not exposed in frontend logs
- API responses exclude internal metadata

### Input Validation

- Custom modifications sanitized to prevent XSS
- Decision rationale limited to 1000 characters
- Feedback notes limited to 2000 characters

---

## 📞 Support & Contact

### Development Team

- **Frontend Lead**: [Name]
- **Backend Lead**: [Name]
- **UX Designer**: [Name]
- **QA Engineer**: [Name]

### Documentation

- **API Docs**: `/api-contracts.md`
- **UI Specs**: `/ui-design-spec.md`
- **Testing**: `/testing-acceptance.md`
- **User Guide**: TBD (post-implementation)

### Issue Tracking

- **Jira Board**: [Link]
- **GitHub Issues**: [Link]
- **Slack Channel**: #proofreading-review-ui

---

## ✅ Pre-Implementation Checklist

Before starting implementation, ensure:

- [ ] All design documents reviewed and approved
- [ ] API contracts agreed upon by backend team
- [ ] UI mockups reviewed by UX team
- [ ] Testing strategy approved by QA team
- [ ] Dependencies installed and versions confirmed
- [ ] Development environment set up
- [ ] Feature branch created: `003-proofreading-review-ui`
- [ ] Kick-off meeting scheduled with team

---

## 📝 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-07 | Claude | Initial design complete |

---

**Document Status**: ✅ Ready for Implementation
**Next Step**: Backend API implementation (Phase 1, Day 1)
**Estimated Start**: 2025-11-08
**Estimated Completion**: 2025-11-18

---

## 🎉 Summary

This feature brings a **professional, efficient, and user-friendly** proofreading review interface to the CMS automation workflow. With careful attention to:

- **Clarity**: Clear visual hierarchy and information architecture
- **Efficiency**: Keyboard shortcuts, batch operations, smart defaults
- **Elegance**: Smooth animations, Apple-inspired minimalist design
- **Reliability**: Comprehensive testing, error handling, performance optimization

The校对审核页面 will significantly improve the review workflow and establish a foundation for future AI-assisted content quality enhancements.

**Let's build it! 🚀**
