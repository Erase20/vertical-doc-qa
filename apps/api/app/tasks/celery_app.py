from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "vertical_doc_qa",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.documents"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={"app.tasks.documents.*": {"queue": "documents"}},
)
