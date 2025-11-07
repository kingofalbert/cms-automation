"""Metrics and monitoring for Google Drive synchronization.

This module provides metrics tracking for:
- Document export and parsing success rates
- Performance metrics (parsing time, document size)
- Error tracking and categorization
- YAML front matter detection rates
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.config import get_logger

logger = get_logger(__name__)


class ExportStatus(str, Enum):
    """Status of document export operation."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ParsingStatus(str, Enum):
    """Status of HTML parsing operation."""

    SUCCESS = "success"
    FALLBACK = "fallback"  # Used simple HTML stripping
    FAILED = "failed"


@dataclass
class DocumentMetrics:
    """Metrics for a single document processing operation."""

    file_id: str
    file_name: str
    mime_type: str
    export_status: ExportStatus
    parsing_status: ParsingStatus | None = None
    original_size_bytes: int = 0
    cleaned_size_bytes: int = 0
    parsing_time_ms: float = 0.0
    has_yaml_front_matter: bool = False
    error_message: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for logging."""
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "export_status": self.export_status.value,
            "parsing_status": self.parsing_status.value if self.parsing_status else None,
            "original_size_bytes": self.original_size_bytes,
            "cleaned_size_bytes": self.cleaned_size_bytes,
            "parsing_time_ms": self.parsing_time_ms,
            "has_yaml_front_matter": self.has_yaml_front_matter,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


class GoogleDriveMetricsCollector:
    """Collector for Google Drive synchronization metrics.

    Tracks and aggregates metrics across multiple document operations.
    Provides summary statistics for monitoring dashboards.
    """

    def __init__(self):
        self.metrics: list[DocumentMetrics] = []

    def record_document(self, metrics: DocumentMetrics) -> None:
        """Record metrics for a document processing operation.

        Args:
            metrics: Document metrics to record
        """
        self.metrics.append(metrics)

        # Log individual document metrics
        logger.info(
            "google_drive_document_processed",
            **metrics.to_dict(),
        )

    def record_export_success(
        self,
        file_id: str,
        file_name: str,
        mime_type: str,
        original_size: int,
    ) -> DocumentMetrics:
        """Record successful document export.

        Args:
            file_id: Google Drive file ID
            file_name: File name
            mime_type: MIME type
            original_size: Size of exported HTML in bytes

        Returns:
            DocumentMetrics instance for further updates
        """
        metrics = DocumentMetrics(
            file_id=file_id,
            file_name=file_name,
            mime_type=mime_type,
            export_status=ExportStatus.SUCCESS,
            original_size_bytes=original_size,
        )
        return metrics

    def record_export_failure(
        self,
        file_id: str,
        file_name: str,
        mime_type: str,
        error: str,
    ) -> None:
        """Record failed document export.

        Args:
            file_id: Google Drive file ID
            file_name: File name
            mime_type: MIME type
            error: Error message
        """
        metrics = DocumentMetrics(
            file_id=file_id,
            file_name=file_name,
            mime_type=mime_type,
            export_status=ExportStatus.FAILED,
            error_message=error,
        )
        self.record_document(metrics)

    def record_export_skipped(
        self,
        file_id: str,
        file_name: str,
        mime_type: str,
        reason: str,
    ) -> None:
        """Record skipped document export.

        Args:
            file_id: Google Drive file ID
            file_name: File name
            mime_type: MIME type
            reason: Reason for skipping
        """
        metrics = DocumentMetrics(
            file_id=file_id,
            file_name=file_name,
            mime_type=mime_type,
            export_status=ExportStatus.SKIPPED,
            error_message=reason,
        )
        self.record_document(metrics)

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics for all recorded metrics.

        Returns:
            Dictionary with aggregated statistics
        """
        if not self.metrics:
            return {
                "total_documents": 0,
                "export_success_count": 0,
                "export_failed_count": 0,
                "export_skipped_count": 0,
                "parsing_success_count": 0,
                "parsing_fallback_count": 0,
                "parsing_failed_count": 0,
                "yaml_front_matter_count": 0,
                "avg_parsing_time_ms": 0.0,
                "avg_original_size_bytes": 0,
                "avg_cleaned_size_bytes": 0,
                "compression_ratio": 0.0,
            }

        total = len(self.metrics)
        export_success = sum(1 for m in self.metrics if m.export_status == ExportStatus.SUCCESS)
        export_failed = sum(1 for m in self.metrics if m.export_status == ExportStatus.FAILED)
        export_skipped = sum(1 for m in self.metrics if m.export_status == ExportStatus.SKIPPED)

        parsing_success = sum(
            1 for m in self.metrics if m.parsing_status == ParsingStatus.SUCCESS
        )
        parsing_fallback = sum(
            1 for m in self.metrics if m.parsing_status == ParsingStatus.FALLBACK
        )
        parsing_failed = sum(
            1 for m in self.metrics if m.parsing_status == ParsingStatus.FAILED
        )

        yaml_count = sum(1 for m in self.metrics if m.has_yaml_front_matter)

        # Calculate averages for successfully parsed documents
        parsed_docs = [
            m
            for m in self.metrics
            if m.parsing_status in (ParsingStatus.SUCCESS, ParsingStatus.FALLBACK)
        ]

        if parsed_docs:
            avg_parse_time = sum(m.parsing_time_ms for m in parsed_docs) / len(parsed_docs)
            avg_original = sum(m.original_size_bytes for m in parsed_docs) / len(parsed_docs)
            avg_cleaned = sum(m.cleaned_size_bytes for m in parsed_docs) / len(parsed_docs)
            compression = avg_cleaned / avg_original if avg_original > 0 else 0.0
        else:
            avg_parse_time = 0.0
            avg_original = 0
            avg_cleaned = 0
            compression = 0.0

        summary = {
            "total_documents": total,
            "export_success_count": export_success,
            "export_failed_count": export_failed,
            "export_skipped_count": export_skipped,
            "export_success_rate": export_success / total if total > 0 else 0.0,
            "parsing_success_count": parsing_success,
            "parsing_fallback_count": parsing_fallback,
            "parsing_failed_count": parsing_failed,
            "parsing_success_rate": parsing_success / total if total > 0 else 0.0,
            "yaml_front_matter_count": yaml_count,
            "yaml_detection_rate": yaml_count / total if total > 0 else 0.0,
            "avg_parsing_time_ms": round(avg_parse_time, 2),
            "avg_original_size_bytes": int(avg_original),
            "avg_cleaned_size_bytes": int(avg_cleaned),
            "compression_ratio": round(compression, 3),
        }

        logger.info("google_drive_sync_summary", **summary)

        return summary

    def reset(self) -> None:
        """Reset all collected metrics."""
        self.metrics.clear()

    def get_error_summary(self) -> dict[str, int]:
        """Get summary of errors grouped by error message.

        Returns:
            Dictionary mapping error messages to occurrence counts
        """
        error_counts: dict[str, int] = {}

        for metrics in self.metrics:
            if metrics.error_message:
                error_counts[metrics.error_message] = (
                    error_counts.get(metrics.error_message, 0) + 1
                )

        return error_counts


# Global metrics collector instance
_metrics_collector: GoogleDriveMetricsCollector | None = None


def get_metrics_collector() -> GoogleDriveMetricsCollector:
    """Get the global metrics collector instance.

    Returns:
        GoogleDriveMetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = GoogleDriveMetricsCollector()
    return _metrics_collector


def reset_metrics() -> None:
    """Reset the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is not None:
        _metrics_collector.reset()
