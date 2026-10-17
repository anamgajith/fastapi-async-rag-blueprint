# FastAPI + Celery + Redis: Asynchronous RAG Blueprint

## The Problem
When building AI automation and RAG (Retrieval-Augmented Generation) pipelines, direct synchronous API calls to LLMs (OpenAI, Anthropic) or Vector Databases (Pinecone, Weaviate) often result in frontend timeouts, rate-limit blocking, and dropped client sessions during high traffic. 

## The Solution
This blueprint demonstrates a production-grade asynchronous architecture. By decoupling heavy inference tasks and document embedding into background workers, the frontend remains hyper-responsive while the backend safely processes high-throughput queues.

### Architecture Stack
* **Web Framework:** FastAPI (Async Python)
* **Task Queue:** Celery 
* **Message Broker & Result Backend:** Redis
* **Infrastructure:** Docker & Docker Compose

## Quickstart (Run Locally)

Spin up the entire microservice architecture with one command:

```bash
docker-compose up -d --build

```

### Endpoints

1. `POST /api/v1/process-document` -> Submits a heavy payload to the Celery queue. Returns a `task_id`.
2. `GET /api/v1/status/{task_id}` -> Polls Redis for the execution state (Pending, Processing, Completed, Failed).

## Why This Matters for Enterprise

* **Rate-Limit Resilience:** Celery workers can be configured to respect strict third-party API rate limits.
* **Fault Tolerance:** If a vector database request fails, the task is automatically retried with exponential backoff.
* **Horizontal Scalability:** You can scale the `worker` container independently from the API server depending on the LLM load.
