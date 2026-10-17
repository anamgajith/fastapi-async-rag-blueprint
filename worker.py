"""
Celery worker for background document processing.

In production this would call an LLM API or embedding model.
Here we simulate heavy inference with a short sleep.
"""

import os
import time

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "rag_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(bind=True, name="process_document", max_retries=3)
def process_document(self, document_id: str, content: str) -> dict:
    """
    Simulate heavy RAG work: embedding + LLM inference.

    Updates task state so the API status endpoint can report progress.
    """
    self.update_state(
        state="PROCESSING",
        meta={"document_id": document_id, "stage": "embedding"},
    )

    # Stand-in for vector embedding / LLM call
    time.sleep(5)

    return {
        "document_id": document_id,
        "status": "completed",
        "chunks_indexed": max(1, len(content) // 100),
        "message": "Document processed and indexed successfully",
    }
