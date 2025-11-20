
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.worklist.pipeline import WorklistPipelineService
from src.models import WorklistItem, WorklistStatus
from src.services.parser.models import ParsingResult, ParsingError

@pytest.mark.asyncio
async def test_process_new_item_parsing_failure_sets_status_failed():
    # Mock session
    mock_session = AsyncMock()
    
    # Mock parser service
    mock_parser_service = MagicMock()
    # Setup failure result
    failure_result = ParsingResult(
        success=False,
        errors=[ParsingError(error_type="test", error_message="Parsing failed")]
    )
    mock_parser_service.parse_document.return_value = failure_result

    # Initialize service
    service = WorklistPipelineService(
        session=mock_session,
        parser_service=mock_parser_service
    )

    # Create a worklist item
    item = WorklistItem(
        id=1,
        title="Test Doc",
        content="Test Content",
        status=WorklistStatus.PENDING,
        raw_html="<p>Test</p>"
    )
    
    # Mock mark_status to update the item status locally for verification
    def mark_status_side_effect(status):
        item.status = status
    item.mark_status = MagicMock(side_effect=mark_status_side_effect)
    
    # Mock add_note
    item.add_note = MagicMock()

    # Mock _ensure_article to return a dummy article
    service._ensure_article = AsyncMock()

    # Execute
    await service.process_new_item(item)

    # Verify
    assert item.status == WorklistStatus.FAILED
    item.mark_status.assert_called_with(WorklistStatus.FAILED)
