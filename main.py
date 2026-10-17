"""
FastAPI entrypoint for the async RAG blueprint.

Submits heavy document work to Celery and exposes a status poll endpoint.
"""

import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from worker import celery_app, process_document

app = FastAPI(
    title="FastAPI Async RAG Blueprint",
    description="Production-style async document processing with Celery + Redis",
    version="1.0.0",
)


class DocumentPayload(BaseModel):
    document_id: str = Field(..., examples=["doc-001"])
    content: str = Field(..., min_length=1, examples=["Sample document text for RAG ingestion."])


class SubmitResponse(BaseModel):
    task_id: str
    status: str = "pending"
    message: str = "Document queued for processing"


class StatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/process-document", response_model=SubmitResponse)
def process_document_endpoint(payload: DocumentPayload) -> SubmitResponse:
    """Enqueue a document for background embedding / inference."""
    task = process_document.delay(payload.document_id, payload.content)
    return SubmitResponse(task_id=task.id)


@app.get("/api/v1/status/{task_id}", response_model=StatusResponse)
def get_task_status(task_id: str) -> StatusResponse:
    """Poll Redis via Celery for the current job state."""
    result = celery_app.AsyncResult(task_id)

    status_map = {
        "PENDING": "pending",
        "STARTED": "processing",
        "PROCESSING": "processing",
        "SUCCESS": "completed",
        "FAILURE": "failed",
        "RETRY": "processing",
        "REVOKED": "failed",
    }

    state = result.state
    status = status_map.get(state, state.lower())

    if state == "PENDING" and result.result is None:
        # Celery returns PENDING for unknown IDs as well — still report pending
        return StatusResponse(task_id=task_id, status="pending", result=None)

    if state == "FAILURE":
        return StatusResponse(
            task_id=task_id,
            status="failed",
            result={"error": str(result.result)},
        )

    if state == "SUCCESS":
        return StatusResponse(task_id=task_id, status="completed", result=result.result)

    meta = result.info if isinstance(result.info, dict) else None
    return StatusResponse(task_id=task_id, status=status, result=meta)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
