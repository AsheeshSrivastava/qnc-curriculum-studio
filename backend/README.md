# Research Portal Backend

FastAPI service orchestrating ingestion, retrieval, and evaluation workflows for the Python programming research portal.

## Local Development

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Environment Configuration

Duplicate `.env.example` to `.env` and provide values for required settings before running the service.

