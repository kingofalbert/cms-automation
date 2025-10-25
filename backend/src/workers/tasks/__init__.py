"""Celery tasks for background processing."""

from src.workers.tasks.generate_article import generate_article_task

__all__ = ["generate_article_task"]
