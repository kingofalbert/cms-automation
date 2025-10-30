# Google Drive Automation & Worklist Testing Plan

**Document Version**: 1.0
**Last Updated**: 2025-10-29
**Status**: Active
**Related Features**: FR-071 to FR-087

---

## 1. Executive Summary

This document defines the comprehensive testing strategy for the Google Drive integration and Worklist features (Phase 6) of the CMS Automation System.

### 1.1 Testing Objectives

- **Functional Coverage**: Verify all 17 new requirements (FR-071 to FR-087)
- **Integration Reliability**: Ensure seamless Google Drive API integration
- **UI/UX Quality**: Validate Worklist user interface and real-time updates
- **Performance**: Meet response time and throughput targets
- **Data Integrity**: Guarantee accurate status tracking and history

### 1.2 Coverage Targets

| Test Type | Target Coverage | Current Status |
|-----------|----------------|----------------|
| Unit Tests | ≥ 85% | 🔄 Pending |
| Integration Tests | ≥ 75% | 🔄 Pending |
| E2E Tests | 100% critical paths | 🔄 Pending |
| API Tests | 100% endpoints | 🔄 Pending |

---

## 2. Test Strategy

### 2.1 Testing Pyramid

```
         /\
        /  \  E2E Tests (15%)
       /____\  - 5 critical user journeys
      /      \
     / Integr \  Integration Tests (35%)
    /  -ation \  - 12 workflow scenarios
   /___Tests___\
  /            \
 /  Unit Tests  \  Unit Tests (50%)
/________________\  - 40+ test cases
```

### 2.2 Test Environments

| Environment | Purpose | Google Drive Setup |
|-------------|---------|-------------------|
| **Local** | Developer testing | Mock Google Drive API |
| **CI/CD** | Automated testing | Mock + Test Service Account |
| **Staging** | Pre-production validation | Dedicated test folder |
| **Production** | Smoke tests only | Live folder (monitored) |

### 2.3 Test Data Management

**Google Drive Test Documents**:
```
/Google Drive Test Folder/
├── valid_documents/
│   ├── sample_article_001.gdoc  (标准文章)
│   ├── sample_article_002.gdoc  (长文章 5000+ 字)
│   ├── sample_article_003.gdoc  (短文章 500 字)
│   └── sample_article_chinese.gdoc  (中文内容)
├── edge_cases/
│   ├── empty_document.gdoc
│   ├── max_size_10mb.gdoc
│   ├── special_chars_!@#$.gdoc
│   └── emoji_content_😀.gdoc
└── invalid_documents/
    ├── corrupted_file.gdoc
    └── permission_denied.gdoc
```

---

## 3. Unit Tests (Target: 40+ tests, 85% coverage)

### 3.1 GoogleDriveMonitor Service Tests

**File**: `tests/unit/services/test_google_drive_monitor.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.services.google_drive_monitor import GoogleDriveMonitor

class TestGoogleDriveMonitor:
    """Unit tests for GoogleDriveMonitor service"""

    @pytest.fixture
    def mock_drive_service(self):
        """Mock Google Drive API service"""
        service = MagicMock()
        return service

    @pytest.fixture
    def monitor(self, mock_drive_service):
        """GoogleDriveMonitor instance with mocked service"""
        with patch('src.services.google_drive_monitor.build', return_value=mock_drive_service):
            return GoogleDriveMonitor(folder_id='test_folder_123')

    # Test 1: Successful document discovery
    def test_scan_for_new_documents_success(self, monitor, mock_drive_service):
        """Should discover new documents from Google Drive"""
        # Arrange
        mock_response = {
            'files': [
                {
                    'id': 'doc_001',
                    'name': 'Test Article 1',
                    'mimeType': 'application/vnd.google-apps.document',
                    'createdTime': '2025-10-29T10:00:00Z',
                    'modifiedTime': '2025-10-29T14:00:00Z'
                },
                {
                    'id': 'doc_002',
                    'name': 'Test Article 2',
                    'mimeType': 'application/vnd.google-apps.document',
                    'createdTime': '2025-10-29T11:00:00Z',
                    'modifiedTime': '2025-10-29T15:00:00Z'
                }
            ]
        }
        mock_drive_service.files().list().execute.return_value = mock_response

        # Act
        since = datetime(2025, 10, 29, 9, 0, 0)
        documents = monitor.scan_for_new_documents(since=since)

        # Assert
        assert len(documents) == 2
        assert documents[0]['id'] == 'doc_001'
        assert documents[0]['name'] == 'Test Article 1'
        assert documents[1]['id'] == 'doc_002'

    # Test 2: Empty folder (no documents)
    def test_scan_for_new_documents_empty(self, monitor, mock_drive_service):
        """Should return empty list when no documents found"""
        mock_drive_service.files().list().execute.return_value = {'files': []}

        since = datetime(2025, 10, 29, 9, 0, 0)
        documents = monitor.scan_for_new_documents(since=since)

        assert len(documents) == 0

    # Test 3: API rate limit error
    def test_scan_for_new_documents_rate_limit(self, monitor, mock_drive_service):
        """Should handle rate limit error gracefully"""
        from googleapiclient.errors import HttpError

        mock_drive_service.files().list().execute.side_effect = HttpError(
            resp=Mock(status=429),
            content=b'Rate Limit Exceeded'
        )

        with pytest.raises(Exception) as exc_info:
            monitor.scan_for_new_documents(since=datetime.now())

        assert 'Rate Limit' in str(exc_info.value)

    # Test 4: Read document content
    def test_read_document_content_success(self, monitor, mock_drive_service):
        """Should successfully read Google Doc content"""
        mock_content = {
            'title': 'Test Article',
            'body': {
                'content': [
                    {'paragraph': {'elements': [{'textRun': {'content': 'This is a test article.'}}]}}
                ]
            }
        }
        mock_drive_service.documents().get().execute.return_value = mock_content

        content = monitor.read_document_content(doc_id='doc_001')

        assert 'This is a test article.' in content

    # Test 5: Mark document as processed
    def test_mark_as_processed_success(self, monitor, mock_drive_service):
        """Should add metadata to mark document as processed"""
        mock_drive_service.files().update().execute.return_value = {'id': 'doc_001'}

        result = monitor.mark_as_processed(doc_id='doc_001')

        assert result is True
        mock_drive_service.files().update.assert_called_once()

    # Test 6: Filter by MIME type
    def test_scan_filters_non_google_docs(self, monitor, mock_drive_service):
        """Should only return Google Docs (not Sheets/Slides)"""
        mock_response = {
            'files': [
                {'id': 'doc_001', 'name': 'Article', 'mimeType': 'application/vnd.google-apps.document'},
                {'id': 'sheet_001', 'name': 'Data', 'mimeType': 'application/vnd.google-apps.spreadsheet'},
                {'id': 'doc_002', 'name': 'Article 2', 'mimeType': 'application/vnd.google-apps.document'}
            ]
        }
        mock_drive_service.files().list().execute.return_value = mock_response

        documents = monitor.scan_for_new_documents(since=datetime.now())

        assert len(documents) == 2
        assert all(doc['mimeType'] == 'application/vnd.google-apps.document' for doc in documents)

    # Test 7: Pagination handling
    def test_scan_handles_pagination(self, monitor, mock_drive_service):
        """Should handle paginated results from Google Drive API"""
        # First page
        page1 = {
            'files': [{'id': f'doc_{i}', 'name': f'Article {i}'} for i in range(100)],
            'nextPageToken': 'token_page2'
        }
        # Second page
        page2 = {
            'files': [{'id': f'doc_{i}', 'name': f'Article {i}'} for i in range(100, 150)]
        }

        mock_drive_service.files().list().execute.side_effect = [page1, page2]

        documents = monitor.scan_for_new_documents(since=datetime.now())

        assert len(documents) == 150

    # Test 8: Document metadata extraction
    def test_extract_document_metadata(self, monitor, mock_drive_service):
        """Should extract all required metadata fields"""
        mock_file = {
            'id': 'doc_001',
            'name': 'Test Article',
            'mimeType': 'application/vnd.google-apps.document',
            'createdTime': '2025-10-29T10:00:00Z',
            'modifiedTime': '2025-10-29T14:00:00Z',
            'size': '45678',
            'owners': [{'emailAddress': 'author@example.com'}],
            'lastModifyingUser': {'emailAddress': 'editor@example.com'},
            'webViewLink': 'https://docs.google.com/document/d/doc_001/edit'
        }
        mock_drive_service.files().get().execute.return_value = mock_file

        metadata = monitor.get_document_metadata(doc_id='doc_001')

        assert metadata['file_size'] == 45678
        assert metadata['owner_email'] == 'author@example.com'
        assert metadata['last_modifying_user'] == 'editor@example.com'
        assert 'web_view_link' in metadata


class TestGoogleDriveIngestion:
    """Tests for document ingestion workflow"""

    # Test 9: Successful ingestion
    @patch('src.services.google_drive_monitor.GoogleDriveMonitor')
    @patch('src.db.repositories.article_repository.ArticleRepository')
    def test_ingest_document_success(self, mock_repo, mock_monitor):
        """Should create article from Google Doc"""
        from src.services.google_drive_ingestion import GoogleDriveIngestionService

        mock_monitor.read_document_content.return_value = "Article content here"
        mock_repo.create.return_value = Mock(id=123)

        service = GoogleDriveIngestionService(monitor=mock_monitor, repo=mock_repo)
        article_id = service.ingest_document(
            doc_id='doc_001',
            file_name='Test Article',
            folder_id='folder_123'
        )

        assert article_id == 123
        mock_repo.create.assert_called_once()

    # Test 10: Duplicate document detection
    def test_ingest_duplicate_document_skipped(self):
        """Should skip already-ingested documents"""
        # Implementation test for duplicate detection
        pass
```

### 3.2 Status Manager Tests

**File**: `tests/unit/services/test_status_manager.py`

```python
class TestStatusTransitions:
    """Tests for article status state machine"""

    # Test 11: Valid status transitions
    def test_valid_status_transitions(self):
        """Should allow valid status transitions"""
        from src.services.status_manager import StatusManager, ArticleStatus

        manager = StatusManager()

        # pending → proofreading
        assert manager.can_transition(ArticleStatus.PENDING, ArticleStatus.PROOFREADING) is True

        # proofreading → under_review
        assert manager.can_transition(ArticleStatus.PROOFREADING, ArticleStatus.UNDER_REVIEW) is True

        # under_review → ready_to_publish
        assert manager.can_transition(ArticleStatus.UNDER_REVIEW, ArticleStatus.READY_TO_PUBLISH) is True

    # Test 12: Invalid status transitions
    def test_invalid_status_transitions(self):
        """Should reject invalid status transitions"""
        from src.services.status_manager import StatusManager, ArticleStatus

        manager = StatusManager()

        # pending → published (skip intermediate steps)
        assert manager.can_transition(ArticleStatus.PENDING, ArticleStatus.PUBLISHED) is False

        # published → pending (cannot rollback from published)
        assert manager.can_transition(ArticleStatus.PUBLISHED, ArticleStatus.PENDING) is False

    # Test 13: Status history recording
    @patch('src.db.repositories.status_history_repository.StatusHistoryRepository')
    def test_status_change_records_history(self, mock_repo):
        """Should record status change in history table"""
        from src.services.status_manager import StatusManager, ArticleStatus

        manager = StatusManager(history_repo=mock_repo)

        manager.transition_status(
            article_id=123,
            from_status=ArticleStatus.PENDING,
            to_status=ArticleStatus.PROOFREADING,
            changed_by='system',
            reason='Automatic transition'
        )

        mock_repo.create.assert_called_once()
        call_args = mock_repo.create.call_args[1]
        assert call_args['article_id'] == 123
        assert call_args['old_status'] == 'pending'
        assert call_args['new_status'] == 'proofreading'
```

### 3.3 Repository Tests

**File**: `tests/unit/repositories/test_google_drive_repository.py`

```python
class TestGoogleDriveDocumentRepository:
    """Tests for google_drive_documents table operations"""

    # Test 14-20: CRUD operations
    # ... (Create, Read, Update, Delete tests)

    # Test 21: Retry logic
    def test_increment_retry_count(self):
        """Should increment retry count on failure"""
        pass

    # Test 22: Query by status
    def test_find_unprocessed_documents(self):
        """Should find all documents with status 'discovered' or 'failed'"""
        pass
```

---

## 4. Integration Tests (Target: 12 scenarios, 75% coverage)

### 4.1 Google Drive → Database Workflow

**File**: `tests/integration/test_google_drive_workflow.py`

```python
import pytest
from datetime import datetime
from src.services.google_drive_monitor import GoogleDriveMonitor
from src.services.google_drive_ingestion import GoogleDriveIngestionService
from src.db.database import SessionLocal

@pytest.mark.integration
class TestGoogleDriveWorkflow:
    """Integration tests for complete Google Drive workflow"""

    @pytest.fixture
    def db_session(self):
        """Database session for testing"""
        session = SessionLocal()
        yield session
        session.rollback()
        session.close()

    # Test 1: End-to-end document ingestion
    @pytest.mark.vcr  # Use VCR.py to record/replay Google API calls
    def test_full_ingestion_workflow(self, db_session):
        """
        Scenario: New document appears in Google Drive
        Steps:
          1. Scanner discovers new document
          2. Document content is read
          3. Article record created in database
          4. google_drive_documents record created
          5. Status history initialized
        Expected: All records created successfully
        """
        # Arrange
        monitor = GoogleDriveMonitor(folder_id='test_folder_id')
        ingestion_service = GoogleDriveIngestionService(db=db_session)

        # Act
        # Step 1: Scan
        new_docs = monitor.scan_for_new_documents(since=datetime(2025, 10, 29, 0, 0))
        assert len(new_docs) > 0

        # Step 2: Ingest first document
        doc = new_docs[0]
        article_id = ingestion_service.ingest_document(
            doc_id=doc['id'],
            file_name=doc['name'],
            folder_id='test_folder_id'
        )

        # Assert
        # Verify article created
        from src.db.repositories.article_repository import ArticleRepository
        article_repo = ArticleRepository(db_session)
        article = article_repo.get_by_id(article_id)

        assert article is not None
        assert article.title == doc['name']
        assert article.current_status == 'pending'
        assert article.google_drive_doc_id == doc['id']

        # Verify google_drive_documents record
        from src.db.repositories.google_drive_repository import GoogleDriveRepository
        gd_repo = GoogleDriveRepository(db_session)
        gd_record = gd_repo.get_by_doc_id(doc['id'])

        assert gd_record.status == 'completed'
        assert gd_record.article_id == article_id

        # Verify initial status history
        from src.db.repositories.status_history_repository import StatusHistoryRepository
        history_repo = StatusHistoryRepository(db_session)
        history = history_repo.get_by_article_id(article_id)

        assert len(history) >= 1
        assert history[0].new_status == 'pending'

    # Test 2: Duplicate document handling
    def test_duplicate_document_prevention(self, db_session):
        """
        Scenario: Same document scanned twice
        Expected: Should skip second ingestion attempt
        """
        pass

    # Test 3: Error handling - corrupted document
    def test_corrupted_document_error_handling(self, db_session):
        """
        Scenario: Document content cannot be read
        Expected: Status = 'failed', error_message populated, retry_count incremented
        """
        pass

    # Test 4: Retry logic
    def test_failed_document_retry(self, db_session):
        """
        Scenario: Failed document is retried (retry_count < 3)
        Expected: Document re-processed, retry_count incremented
        """
        pass

    # Test 5: Max retries reached
    def test_max_retries_exceeded(self, db_session):
        """
        Scenario: Document fails 3 times (retry_count = 3)
        Expected: Document marked as permanently failed, no more retries
        """
        pass


@pytest.mark.integration
class TestStatusTransitionWorkflow:
    """Integration tests for status state machine"""

    # Test 6: Complete article lifecycle
    def test_full_article_lifecycle(self, db_session):
        """
        Scenario: Article goes through all statuses
        Steps:
          1. pending → proofreading
          2. proofreading → under_review
          3. under_review → ready_to_publish
          4. ready_to_publish → publishing
          5. publishing → published
        Expected: Each transition recorded in history
        """
        pass

    # Test 7: Rollback to previous status
    def test_status_rollback_under_review_to_proofreading(self, db_session):
        """
        Scenario: Editor rejects article during review
        Expected: Status changes to 'proofreading', history records rollback
        """
        pass
```

### 4.2 Worklist API Integration Tests

**File**: `tests/integration/test_worklist_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.mark.integration
class TestWorklistAPI:
    """Integration tests for Worklist REST API"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    # Test 8: GET /api/v1/worklist with pagination
    def test_get_worklist_with_pagination(self, client, db_session):
        """
        Request: GET /api/v1/worklist?page=1&limit=20&status=under_review
        Expected: 200 OK, returns paginated articles
        """
        # Arrange: Create 50 test articles
        # ... (setup code)

        # Act
        response = client.get('/api/v1/worklist?page=1&limit=20&status=under_review')

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert len(data['items']) <= 20

    # Test 9: GET /api/v1/worklist/{article_id} with history
    def test_get_article_detail_with_history(self, client, db_session):
        """
        Request: GET /api/v1/worklist/123
        Expected: Article details + status history timeline
        """
        pass

    # Test 10: POST /api/v1/worklist/batch-action
    def test_batch_approve_articles(self, client, db_session):
        """
        Request: POST /api/v1/worklist/batch-action
        Body: {"action": "approve", "article_ids": [1, 2, 3]}
        Expected: All 3 articles transition to 'ready_to_publish'
        """
        pass

    # Test 11: WebSocket real-time updates
    @pytest.mark.asyncio
    async def test_websocket_status_updates(self, client):
        """
        Scenario: Article status changes, WebSocket notifies connected clients
        Expected: Clients receive status_update message
        """
        pass

    # Test 12: Filtering and sorting
    def test_worklist_filtering_and_sorting(self, client):
        """
        Request: GET /api/v1/worklist?status=pending&sort=created_at:desc
        Expected: Only pending articles, sorted by creation date descending
        """
        pass
```

---

## 5. End-to-End (E2E) Tests

### 5.1 Critical User Journeys

**Tool**: Playwright (Python)

**File**: `tests/e2e/test_google_drive_worklist_e2e.py`

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
class TestGoogleDriveWorklistE2E:
    """End-to-end tests for Google Drive + Worklist UI"""

    # Test 1: Complete workflow - Google Drive to Published
    def test_complete_workflow_google_drive_to_published(self, page: Page):
        """
        User Journey:
        1. New Google Doc created in monitored folder
        2. System scans and discovers document (wait 5 min or trigger manually)
        3. User navigates to Worklist page
        4. User sees new article with status "pending"
        5. User clicks article to view details
        6. User approves article (status → ready_to_publish)
        7. User triggers publish action
        8. Article status updates to "publishing" then "published"
        """
        # Step 1: Upload test document to Google Drive
        # (Using Google Drive API or pre-uploaded test file)

        # Step 2: Trigger scanner (or wait for scheduled scan)
        page.goto('http://localhost:3000/admin/trigger-scan')
        page.click('button:has-text("Scan Now")')
        expect(page.locator('.toast-success')).to_contain_text('Scan completed')

        # Step 3: Navigate to Worklist
        page.goto('http://localhost:3000/worklist')
        expect(page.locator('h1')).to_contain_text('Worklist')

        # Step 4: Verify new article appears
        article_row = page.locator('tr:has-text("Test Article from Google Drive")').first
        expect(article_row).to_be_visible()
        expect(article_row.locator('.status-badge')).to_contain_text('待处理')

        # Step 5: Open detail view
        article_row.click()
        expect(page.locator('.drawer-title')).to_contain_text('Test Article from Google Drive')

        # Step 6: Approve article
        page.click('button:has-text("批准发布")')
        expect(page.locator('.status-badge')).to_contain_text('待发布')

        # Step 7: Trigger publish
        page.click('button:has-text("立即发布")')

        # Step 8: Wait for publish to complete
        expect(page.locator('.status-badge')).to_contain_text('已发布', timeout=30000)

        # Verify status history shows all transitions
        history_section = page.locator('.status-history')
        expect(history_section.locator('.history-item')).to_have_count(5)  # 5 status changes

    # Test 2: Batch operations
    def test_batch_approve_multiple_articles(self, page: Page):
        """
        User Journey:
        1. Navigate to Worklist
        2. Filter by status "under_review"
        3. Select 3 articles using checkboxes
        4. Click "Batch Approve" button
        5. Verify all 3 articles transition to "ready_to_publish"
        """
        page.goto('http://localhost:3000/worklist')

        # Filter
        page.select_option('select[name="status"]', 'under_review')

        # Select 3 articles
        checkboxes = page.locator('input[type="checkbox"][name="article"]')
        checkboxes.nth(0).check()
        checkboxes.nth(1).check()
        checkboxes.nth(2).check()

        # Batch approve
        page.click('button:has-text("批量批准")')
        page.click('button:has-text("确认")')  # Confirm modal

        # Verify status updates
        expect(page.locator('.toast-success')).to_contain_text('3 篇文章已批准')

        # Check status badges updated
        status_badges = page.locator('tr input[type="checkbox"]:checked ~ td .status-badge')
        for badge in status_badges.all():
            expect(badge).to_contain_text('待发布')

    # Test 3: Real-time WebSocket updates
    def test_realtime_status_updates_websocket(self, page: Page):
        """
        User Journey:
        1. User A opens Worklist page
        2. User B (another browser) changes article status
        3. User A sees status update in real-time (no page refresh)
        """
        # Open two browser contexts (User A and User B)
        pass

    # Test 4: Error handling - failed publish
    def test_publish_failure_error_display(self, page: Page):
        """
        User Journey:
        1. User triggers publish for article
        2. Publish fails (simulate WordPress unavailable)
        3. Status changes to "failed"
        4. Error message displayed in detail view
        """
        pass

    # Test 5: Status history timeline
    def test_status_history_timeline_display(self, page: Page):
        """
        User Journey:
        1. Open article detail drawer
        2. Click "查看历史" tab
        3. Verify timeline shows all status changes with timestamps
        4. Verify metadata (changed_by, reason) displayed correctly
        """
        page.goto('http://localhost:3000/worklist')
        page.locator('tr').first.click()

        page.click('button:has-text("查看历史")')

        history_items = page.locator('.timeline-item')
        expect(history_items).to_have_count_greater_than(0)

        first_item = history_items.first
        expect(first_item.locator('.status')).to_contain_text('pending → proofreading')
        expect(first_item.locator('.timestamp')).to_be_visible()
        expect(first_item.locator('.changed-by')).to_contain_text('system')
```

---

## 6. Performance Tests

### 6.1 Load Testing Scenarios

**Tool**: Locust (Python)

**File**: `tests/performance/test_worklist_load.py`

```python
from locust import HttpUser, task, between

class WorklistUser(HttpUser):
    """Simulates user browsing Worklist"""
    wait_time = between(1, 3)

    @task(3)
    def view_worklist(self):
        """Most common action: View worklist page"""
        self.client.get('/api/v1/worklist?page=1&limit=20')

    @task(2)
    def view_article_detail(self):
        """View article details"""
        self.client.get('/api/v1/worklist/123')

    @task(1)
    def approve_article(self):
        """Approve article (status change)"""
        self.client.post('/api/v1/worklist/123/approve')


class GoogleDriveScanUser(HttpUser):
    """Simulates Google Drive scanner"""
    wait_time = between(300, 300)  # 5 minutes

    @task
    def trigger_scan(self):
        """Trigger Google Drive scan"""
        self.client.post('/api/v1/google-drive/scan')
```

**Performance Targets**:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Worklist API Response Time (p95) | < 500ms | 100 concurrent users |
| Article Detail API Response Time (p95) | < 300ms | 100 concurrent users |
| Google Drive Scan Time | < 30s | 100 documents |
| WebSocket Message Latency | < 100ms | Real-time updates |
| Database Query Time (Worklist) | < 200ms | 10,000 articles |

### 6.2 Performance Test Execution

```bash
# Run load test
locust -f tests/performance/test_worklist_load.py \
       --host=http://localhost:8000 \
       --users=100 \
       --spawn-rate=10 \
       --run-time=5m \
       --html=reports/performance_report.html

# Analyze results
# - p50, p95, p99 response times
# - Requests per second (RPS)
# - Error rate (should be < 1%)
```

---

## 7. Test Automation & CI/CD

### 7.1 GitHub Actions Workflow

**File**: `.github/workflows/test_google_drive.yml`

```yaml
name: Google Drive & Worklist Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=html \
            --cov-report=term \
            --cov-fail-under=85

      - name: Upload coverage report
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run integration tests
        env:
          GOOGLE_DRIVE_CREDENTIALS: ${{ secrets.GOOGLE_DRIVE_TEST_CREDENTIALS }}
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        run: |
          pytest tests/integration/ \
            --maxfail=3 \
            --tb=short

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Playwright
        run: |
          pip install playwright pytest-playwright
          playwright install chromium

      - name: Start backend server
        run: |
          uvicorn src.main:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Start frontend dev server
        run: |
          cd frontend && npm install && npm run dev &
          sleep 10

      - name: Run E2E tests
        run: |
          pytest tests/e2e/ \
            --video=retain-on-failure \
            --screenshot=only-on-failure

      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: test-results/
```

### 7.2 Pre-commit Hooks

**File**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: unit-tests
        name: Run unit tests
        entry: pytest tests/unit/ --maxfail=5 --tb=short
        language: system
        pass_filenames: false
        always_run: true
```

---

## 8. Test Data & Fixtures

### 8.1 Database Fixtures

**File**: `tests/fixtures/db_fixtures.py`

```python
import pytest
from src.db.database import Base, engine, SessionLocal
from src.models import Article, GoogleDriveDocument, ArticleStatusHistory

@pytest.fixture(scope='function')
def db_session():
    """Create clean database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_article(db_session):
    """Create sample article for testing"""
    article = Article(
        title='Sample Article',
        original_content='This is a sample article for testing.',
        current_status='pending',
        google_drive_doc_id='doc_sample_001',
        google_drive_file_name='Sample Article.gdoc'
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article

@pytest.fixture
def sample_google_drive_document(db_session, sample_article):
    """Create sample Google Drive document record"""
    gd_doc = GoogleDriveDocument(
        google_doc_id='doc_sample_001',
        file_name='Sample Article.gdoc',
        folder_id='folder_123',
        article_id=sample_article.id,
        status='completed'
    )
    db_session.add(gd_doc)
    db_session.commit()
    return gd_doc
```

### 8.2 Mock Google Drive API

**File**: `tests/mocks/google_drive_mock.py`

```python
from unittest.mock import MagicMock

def create_mock_drive_service():
    """Create mock Google Drive API service"""
    service = MagicMock()

    # Mock files().list() response
    service.files().list().execute.return_value = {
        'files': [
            {
                'id': 'doc_001',
                'name': 'Test Article 1',
                'mimeType': 'application/vnd.google-apps.document',
                'createdTime': '2025-10-29T10:00:00Z',
                'modifiedTime': '2025-10-29T14:00:00Z'
            }
        ]
    }

    # Mock documents().get() response
    service.documents().get().execute.return_value = {
        'title': 'Test Article 1',
        'body': {
            'content': [
                {
                    'paragraph': {
                        'elements': [
                            {'textRun': {'content': 'This is the article content.'}}
                        ]
                    }
                }
            ]
        }
    }

    return service
```

---

## 9. Bug Tracking & Reporting

### 9.1 Test Failure Protocol

1. **Automated Failure Detection**: GitHub Actions reports failures
2. **Issue Creation**: Auto-create GitHub issue with:
   - Test name
   - Failure message
   - Stack trace
   - Test logs
3. **Assignment**: Assign to relevant developer based on component
4. **Resolution Tracking**: Update issue when fixed

### 9.2 Test Metrics Dashboard

**Metrics to Track**:
- Test pass rate (overall and by category)
- Code coverage percentage
- Average test execution time
- Flaky test identification
- Bug detection rate

**Tools**:
- Codecov for coverage
- GitHub Actions for CI metrics
- Custom dashboard (Grafana/Metabase)

---

## 10. Test Schedule

### 10.1 Development Phase

| Week | Test Activities |
|------|----------------|
| **Week 11** | Unit tests for GoogleDriveMonitor (T6.3) |
| **Week 12** | Integration tests for ingestion workflow (T6.7) |
| **Week 13** | Unit tests for StatusManager + repositories (T6.11) |
| **Week 14** | E2E tests for Worklist UI (T6.17) |
| **Week 15** | Performance testing + bug fixes (T6.19) |

### 10.2 Ongoing Testing (Post-Launch)

- **Daily**: Unit tests on every commit
- **Weekly**: Full integration test suite
- **Monthly**: Performance regression tests
- **Quarterly**: Security audit + penetration testing

---

## 11. Acceptance Criteria

### 11.1 Phase 6 Testing Sign-off

All criteria must be met before Phase 6 release:

- [ ] ≥ 85% unit test coverage
- [ ] All 12 integration tests passing
- [ ] All 5 E2E critical paths passing
- [ ] Performance targets met (see Section 6.1)
- [ ] Zero P0/P1 bugs remaining
- [ ] Manual QA approval
- [ ] Security review completed

### 11.2 Release Checklist

- [ ] All automated tests passing in CI/CD
- [ ] Manual smoke tests completed in staging
- [ ] Database migration tested with production-like data
- [ ] Rollback plan documented and tested
- [ ] Monitoring alerts configured
- [ ] User documentation updated

---

## 12. Test Maintenance

### 12.1 Quarterly Test Review

- Review flaky tests and fix/remove
- Update test data for relevance
- Review coverage gaps
- Performance benchmarks update

### 12.2 Test Code Quality

- Follow same code standards as production code
- Use descriptive test names
- Avoid test interdependencies
- Keep tests fast (unit tests < 1s each)

---

**Document Owner**: QA Lead
**Review Frequency**: After each sprint
**Last Reviewed**: 2025-10-29
