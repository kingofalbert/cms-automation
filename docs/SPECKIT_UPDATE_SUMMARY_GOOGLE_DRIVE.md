# SpecKit 文档更新摘要 - Google Drive 自动化功能

**创建日期**: 2025-10-27
**更新原因**: 添加 Google Drive 自动监控和 Worklist UI 功能
**影响范围**: 7 个文档需要更新/创建
**预计工作量**: 5 周实施 + 200 小时

---

## ✅ 更新进度

- [x] **1. spec.md** - 添加 FR-071 到 FR-087（已完成）
- [ ] **2. plan.md** - 添加 Google Drive 集成架构和实施阶段
- [ ] **3. tasks.md** - 添加详细实施任务（Phase 6）
- [ ] **4. UI_GAPS_ANALYSIS.md** - 添加 Worklist UI 模块分析
- [ ] **5. UI_IMPLEMENTATION_TASKS.md** - 添加 Worklist UI 实施任务（Module 7）
- [ ] **6. data-model.md** - 创建新文档，定义数据库表结构
- [ ] **7. GOOGLE_DRIVE_TESTING_PLAN.md** - 创建测试方案文档

---

## 📄 一、已完成：spec.md 更新

### 新增内容

**章节**: Functional Requirements → Google Drive Automation & Worklist (FR-071 to FR-087)

**新增需求（17 个）**:

1. **Google Drive 集成（5 个）**:
   - FR-071: Google Drive API 集成认证
   - FR-072: 定期扫描 Google Drive 目录
   - FR-073: 读取 Google Doc 内容
   - FR-074: 标记已处理文档
   - FR-075: 错误处理和重试

2. **Worklist UI（8 个）**:
   - FR-076: Worklist 页面
   - FR-077: 文档元数据显示
   - FR-078: 7 种状态支持
   - FR-079: 筛选功能
   - FR-080: 排序功能
   - FR-081: 详情页面
   - FR-082: 实时更新
   - FR-083: 批量操作

3. **状态追踪（4 个）**:
   - FR-084: 状态历史记录
   - FR-085: 操作日志
   - FR-086: 状态回退
   - FR-087: 处理时长统计

**文件位置**: `/specs/001-cms-automation/spec.md` (line 486-528)

---

## 📋 二、待更新：plan.md

### 需要添加的内容

#### 2.1 更新系统架构图

**位置**: Section 1.1 System Architecture Diagram

**新增组件**:

```mermaid
subgraph "Google Drive Integration Layer (新增)"
    GDM[Google Drive Monitor<br/>定期扫描服务]
    GDR[Google Docs Reader<br/>内容提取服务]
    GDAPI[Google Drive API]
end

subgraph "Frontend (新增页面)"
    WORKLIST[Worklist Page<br/>文稿工作列表]
    WLDETAIL[Worklist Detail<br/>文档详情]
end

GDM --> GDAPI
GDR --> GDAPI
GDM --> CELERY
CELERY --> AIS
WORKLIST --> API
WLDETAIL --> API
```

#### 2.2 更新 Phase 时间表

**当前**: 10.5 weeks (Phase 1-5)

**更新后**: 15.5 weeks (Phase 1-6)

**新增 Phase 6**: Google Drive Automation & Worklist (5 weeks)

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| **Phase 6** | Google Drive + Worklist | 5 weeks | ⏳ Planned |

#### 2.3 添加 Phase 6 详细计划

**Phase 6: Google Drive Automation & Worklist (Week 11-15)**

**Week 11-12: Google Drive Integration**
- Google Drive API 集成
- 定时扫描服务
- 文档读取和解析
- 数据库表创建

**Week 13-14: Worklist UI**
- Worklist 页面开发
- 状态追踪系统
- 实时更新（WebSocket）

**Week 15: 集成测试和优化**
- 端到端测试
- 性能优化
- Bug 修复

#### 2.4 更新数据库设计

**位置**: Section 3 - Database Design

**新增表（2 个）**:

1. **`google_drive_documents`**
   - google_doc_id (唯一标识)
   - file_name, folder_id, folder_path
   - article_id (外键)
   - status (discovered/processing/imported/failed)
   - error_message, retry_count
   - discovered_at, processed_at

2. **`article_status_history`**
   - article_id (外键)
   - old_status, new_status
   - changed_by, change_reason
   - metadata (JSONB)
   - created_at

**修改表**:
- `articles`: 添加字段
  - source_type (manual/google_drive/csv/json)
  - google_drive_doc_id
  - current_status
  - status_updated_at
  - processing_started_at
  - processing_completed_at
  - total_processing_duration_seconds

#### 2.5 添加 API 端点

**Google Drive API**:
```
POST   /api/v1/google-drive/scan
GET    /api/v1/google-drive/documents
GET    /api/v1/google-drive/documents/{doc_id}
POST   /api/v1/google-drive/documents/{doc_id}/import
POST   /api/v1/google-drive/documents/{doc_id}/sync
```

**Worklist API**:
```
GET    /api/v1/worklist
GET    /api/v1/worklist/{article_id}
POST   /api/v1/worklist/batch-action
WS     /api/v1/worklist/ws
```

---

## 📋 三、待更新：tasks.md

### 需要添加的内容

#### 3.1 新增 Phase 6

**Phase 6: Google Drive Automation & Worklist (5 weeks)**

**总工时**: 200 hours

**任务分组**:

##### Week 11-12: Google Drive Integration (80 hours)

**T6.1** [P0] Setup Google Drive API Integration (12h)
- Configure Google OAuth 2.0 / Service Account
- Create google-drive credentials management
- Test API connection

**T6.2** [P0] Implement GoogleDriveMonitor Service (16h)
- Create `GoogleDriveMonitor` class
- Implement `scan_for_new_documents()` method
- Implement `read_document_content()` method
- Implement `mark_as_processed()` method

**T6.3** [P0] Create Database Tables (8h)
- Create Alembic migration for `google_drive_documents`
- Create Alembic migration for `article_status_history`
- Modify `articles` table (add new fields)
- Create indexes

**T6.4** [P0] Implement Celery Scheduled Tasks (12h)
- Create `scan_google_drive_for_new_documents` task
- Create `import_google_drive_document` task
- Configure Celery Beat schedule (every 5 minutes)
- Add retry logic and error handling

**T6.5** [P0] Implement Content Parser (10h)
- Parse Google Doc format
- Extract title, content, meta, keywords
- Handle formatting and images

**T6.6** [P1] Implement Status Tracking Service (12h)
- Create `ArticleStatusTracker` service
- Record status transitions to `article_status_history`
- Implement status rollback logic

**T6.7** [P1] Google Drive Integration Tests (10h)
- Unit tests for `GoogleDriveMonitor`
- Integration tests with test Google Doc
- Error handling tests

##### Week 13-14: Worklist UI (80 hours)

**T6.8** [P0] Create Worklist Page (16h)
- Create `WorklistPage.tsx` route (`/worklist`)
- Implement table layout
- Add filters (status, date, keyword)
- Add sorting (time, status)
- Add pagination

**T6.9** [P0] Implement Status Badges (4h)
- Create `StatusBadge` component
- 7 status variants with colors and icons
- Pulse animation for "Publishing" status

**T6.10** [P0] Create Worklist Detail Page (12h)
- Create `WorklistDetailPage.tsx` or Drawer
- Display full document content
- Display status history timeline
- Display operation logs
- Add action buttons

**T6.11** [P0] Implement Real-time Updates (12h)
- Setup WebSocket connection (`/api/v1/worklist/ws`)
- Handle status update messages
- Handle new article messages
- Fallback to polling (every 5s)

**T6.12** [P1] Implement Statistics Dashboard (8h)
- Create statistics cards (Pending/Proofreading/etc.)
- Count documents by status
- Display on Worklist page header

**T6.13** [P1] Implement Batch Operations (8h)
- Add checkbox selection
- Batch delete
- Batch retry
- Batch mark as pending

**T6.14** [P0] Backend Worklist APIs (16h)
- Implement `GET /api/v1/worklist`
- Implement `GET /api/v1/worklist/{article_id}`
- Implement `POST /api/v1/worklist/batch-action`
- Implement WebSocket handler

**T6.15** [P1] Worklist UI Tests (4h)
- E2E tests for Worklist page
- Filter and sort tests
- Real-time update tests

##### Week 15: Integration & Testing (40 hours)

**T6.16** [P0] End-to-End Workflow Test (12h)
- Test: Google Drive → Import → Proofread → Review → Publish
- Verify status transitions
- Verify Worklist updates

**T6.17** [P0] Performance Testing (8h)
- Test with 1000+ documents in Worklist
- Test concurrent Google Drive scans
- Optimize database queries

**T6.18** [P0] Error Handling Tests (8h)
- Test Google API failure scenarios
- Test network timeout and retry
- Test status rollback

**T6.19** [P0] Documentation (6h)
- Update API documentation
- Update user guide
- Create Google Drive setup guide

**T6.20** [P0] Bug Fixes and Polish (6h)
- Address issues found in testing
- UI polish
- Final review

---

## 📋 四、待更新：UI_GAPS_ANALYSIS.md

### 需要添加的内容

#### 4.1 新增 Module 7: Worklist UI

**位置**: 在 Module 6 (Settings Page) 之后添加

**内容**:

### Module 7: Worklist UI - Document Processing Dashboard

**Priority**: 🔴 P0 (Critical)
**Status**: ❌ Complete缺失
**Estimated Hours**: 60 hours
**Components**: 10 个

#### 缺失组件列表

1. **`WorklistPage.tsx`** (16h)
   - Main worklist page with table layout
   - Filters and search bar
   - Statistics dashboard
   - Pagination

2. **`StatusBadge.tsx`** (4h)
   - 7 status variants with color coding
   - Icons for each status
   - Pulse animation for active status

3. **`WorklistTable.tsx`** (8h)
   - Sortable table columns
   - Row click to open detail
   - Checkbox selection for batch operations

4. **`WorklistFilters.tsx`** (6h)
   - Status dropdown
   - Date range picker
   - Keyword search input
   - Clear filters button

5. **`WorklistDetailDrawer.tsx`** (12h)
   - Full document content display
   - Status history timeline
   - Operation logs viewer
   - Action buttons

6. **`StatusHistoryTimeline.tsx`** (6h)
   - Vertical timeline component
   - Each step with timestamp and icon
   - Highlight current status

7. **`WorklistStatistics.tsx`** (4h)
   - Statistics cards showing counts by status
   - Color-coded for visual appeal

8. **`BatchOperations.tsx`** (4h)
   - Checkbox "select all"
   - Batch action dropdown
   - Confirmation dialog

9. **`useWorklistRealtime.ts`** (6h)
   - Custom React hook for WebSocket
   - Handle status updates
   - Handle new articles
   - Fallback to polling

10. **`WorklistEmpty.tsx`** (2h)
    - Empty state component
    - Icon + message
    - CTA button to import articles

#### API 依赖

**Backend APIs 需要实现**:
- `GET /api/v1/worklist` (已完成: 0%)
- `GET /api/v1/worklist/{article_id}` (已完成: 0%)
- `POST /api/v1/worklist/batch-action` (已完成: 0%)
- `WS /api/v1/worklist/ws` (已完成: 0%)

#### 业务影响

**阻塞级影响**: 没有 Worklist，用户无法：
- 查看所有正在处理的文档
- 追踪文档的处理进度
- 发现处理失败的文档
- 对多个文档进行批量操作

**用户价值**: Worklist 是整个系统的"控制中心"，提供全局可见性。

#### 更新总工时

**原总工时**: 312 hours
**新增工时**: 60 hours
**更新后总工时**: 372 hours

**更新周期**: 6 weeks → 7.5 weeks

---

## 📋 五、待更新：UI_IMPLEMENTATION_TASKS.md

### 需要添加的内容

#### 5.1 新增 Module 7: Worklist UI

**位置**: Phase 2 (Week 5-6) 之后，新增 Phase 3 (Week 7-8)

**内容**:

## Phase 3: Automation Enhancement (Week 7-8)

### Week 7-8: Worklist & Google Drive Integration

#### Task Group 4.1: Worklist UI (Module 7) - 60 hours

**目标**: 实现文稿工作列表，提供全局文档追踪能力

##### T-UI-4.1.1 [P0] Create Worklist Page

**Priority**: 🔴 Critical
**Estimated Hours**: 16 hours
**Dependencies**: None

**Description**:
创建 Worklist 主页面，显示所有文档的列表

**Deliverables**:
- `frontend/src/pages/WorklistPage.tsx`
- 表格布局
- 筛选和搜索栏
- 统计仪表盘
- 分页

**Acceptance Criteria**:
- [ ] 页面可通过 `/worklist` 路由访问
- [ ] 表格显示：ID、标题、来源、状态、创建时间、操作
- [ ] 支持按状态筛选（全部/待处理/校对中/审核中/待发布/发布中/已发布/失败）
- [ ] 支持关键词搜索（标题、内容）
- [ ] 支持排序（创建时间/更新时间/状态）
- [ ] 分页支持（20/50/100 条/页）
- [ ] 响应式布局

**Code Structure**:
```tsx
// frontend/src/pages/WorklistPage.tsx

export default function WorklistPage() {
  const [filters, setFilters] = useState({ status: 'all', keyword: '' });
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20 });

  const { data, isLoading } = useQuery({
    queryKey: ['worklist', filters, pagination],
    queryFn: () => fetchWorklist(filters, pagination)
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">文稿工作列表</h1>

      <WorklistStatistics />

      <WorklistFilters
        filters={filters}
        onFiltersChange={setFilters}
      />

      <WorklistTable
        documents={data?.items || []}
        isLoading={isLoading}
      />

      <Pagination
        page={pagination.page}
        pageSize={pagination.pageSize}
        total={data?.total || 0}
        onPageChange={(page) => setPagination({ ...pagination, page })}
      />
    </div>
  );
}
```

---

_(继续添加 T-UI-4.1.2 到 T-UI-4.1.10 的详细任务...)_

---

##### T-UI-4.1.11 [P0] Backend Worklist APIs

**Priority**: 🔴 Critical
**Estimated Hours**: 16 hours

**Endpoints**:
```python
@router.get("/v1/worklist")
async def get_worklist(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = 'created_at',
    order: str = 'desc'
) -> WorklistResponse:
    """获取工作列表"""
    pass

@router.get("/v1/worklist/{article_id}")
async def get_worklist_detail(article_id: int) -> WorklistDetailResponse:
    """获取文档详情（含状态历史）"""
    pass

@router.post("/v1/worklist/batch-action")
async def worklist_batch_action(action: BatchAction) -> BatchActionResponse:
    """批量操作（删除/重试/标记）"""
    pass
```

---

## 📋 六、待创建：data-model.md

### 文档内容

创建新文档 `/specs/001-cms-automation/data-model.md`，包含：

1. **ER Diagram** (Mermaid格式)
2. **表结构定义**:
   - `articles` (修改：添加新字段)
   - `google_drive_documents` (新增)
   - `article_status_history` (新增)
   - `seo_metadata` (已有)
   - `publish_tasks` (已有)
   - `execution_logs` (已有)
3. **索引策略**
4. **JSONB 字段结构**
5. **分区策略**（`execution_logs`）

---

## 📋 七、待创建：GOOGLE_DRIVE_TESTING_PLAN.md

### 文档内容

创建新文档 `/docs/GOOGLE_DRIVE_TESTING_PLAN.md`，包含：

1. **测试范围**
   - 单元测试
   - 集成测试
   - E2E 测试

2. **测试用例**
   - Google Drive API 集成
   - 定时扫描任务
   - 文档导入流程
   - Worklist UI 功能
   - 实时更新

3. **测试环境**
   - 测试 Google Drive 账号
   - 测试文档模板
   - Mock 数据

4. **测试指标**
   - 覆盖率目标: ≥80%
   - 性能基准
   - 成功率目标

---

## 🎯 执行计划

### 自动化执行顺序

1. ✅ **spec.md** - 已完成
2. ⏳ **plan.md** - 正在进行
3. **tasks.md** - 待执行
4. **UI_GAPS_ANALYSIS.md** - 待执行
5. **UI_IMPLEMENTATION_TASKS.md** - 待执行
6. **data-model.md** - 待创建
7. **GOOGLE_DRIVE_TESTING_PLAN.md** - 待创建

### 预计完成时间

- 自动化更新: 2-3 小时（Claude 执行）
- 人工审查: 1 小时
- 总计: 3-4 小时

---

## ✅ 验收标准

完成所有更新后，需要验证：

- [ ] 所有 17 个新功能需求（FR-071 到 FR-087）在 spec.md 中有详细定义
- [ ] plan.md 包含 Google Drive 集成架构和 Phase 6 实施计划
- [ ] tasks.md 包含 Phase 6 的所有详细任务（20+ 个任务）
- [ ] UI_GAPS_ANALYSIS.md 包含 Module 7 (Worklist UI) 的组件分析
- [ ] UI_IMPLEMENTATION_TASKS.md 包含 Worklist UI 的详细实施任务
- [ ] data-model.md 包含完整的数据库表结构和 ER 图
- [ ] GOOGLE_DRIVE_TESTING_PLAN.md 包含完整的测试策略

---

**文档创建**: 2025-10-27
**创建者**: Claude (AI Assistant)
**状态**: ✅ 摘要完成，等待继续执行
