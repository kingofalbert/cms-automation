"""Celery Beat periodic task schedule configuration."""

from celery.schedules import crontab

from src.workers.celery_app import celery_app

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Scan for scheduled publications every minute
    "scan-scheduled-publications": {
        "task": "src.workers.tasks.publish_scheduled.scan_scheduled_publications",
        "schedule": 60.0,  # Every 60 seconds
        "options": {"queue": "publishing"},
    },
    # Clean up old completed tasks every hour
    "cleanup-old-tasks": {
        "task": "src.workers.tasks.maintenance.cleanup_old_tasks",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"queue": "maintenance"},
    },
    # Update tagging accuracy metrics daily
    "update-tagging-metrics": {
        "task": "src.workers.tasks.metrics.update_tagging_accuracy",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
        "options": {"queue": "metrics"},
    },
    # Check system health every 5 minutes
    "health-check": {
        "task": "src.workers.tasks.maintenance.health_check",
        "schedule": 300.0,  # Every 5 minutes
        "options": {"queue": "maintenance"},
    },
}
