# BuildWise Backend

This repository contains a minimal FastAPI backend for the BuildWise platform.
It provides JWT-based authentication and CRUD endpoints for managing projects.

## Requirements
- Docker & docker-compose
- Python 3.11 (for local development without Docker)

## Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env` and adjust values if needed.
3. Run database migrations: `alembic upgrade head`
4. Start the server: `uvicorn app.main:app --reload`

## Docker
The application can be started using docker-compose which will run both the
PostgreSQL database and the FastAPI app.

```bash
docker-compose up --build
```

The API will then be available at `http://localhost:8000`.

OpenAPI documentation is served automatically at `/docs`.
