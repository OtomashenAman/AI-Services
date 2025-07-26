# AI-Services

This repository serves as the backend for an AI-driven service. It is designed to be modular, scalable, and adaptable for various use cases involving large language models (LLMs), retrieval-augmented generation (RAG), and task-specific workflows.

---

## 🗂️ Project Structure

```bash
project-root/
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── config/                      # Settings and .env management
│   │   └── settings.py
│   ├── core/                        # Core utilities (auth, logging, etc.)
│   │   ├── auth.py
│   │   └── logging_config.py
│   ├── services/                    # Business logic layer
│   │   ├── service_a/               # e.g., PDF summarizer
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # Data models
│   │   │   ├── routes.py            # API endpoints
│   │   │   ├── pipeline.py          # Logic/workflows
│   │   │   └── utils.py             # Local helpers
│   │   ├── service_b/               # e.g., Excel KPI extractor
│   │   │   └── ...
│   │   └── shared/                  # Shared across services (e.g., S3, DB)
│   │       ├── s3_handler.py
│   │       └── db_utils.py
│   ├── schemas/                     # Pydantic request/response models
│   ├── api/                         # FastAPI routers aggregation
│   │   └── api_router.py
│   └── utils/                       # Global utility scripts
│       └── file_loader.py
│
├── tests/                           # All tests
│   ├── service_a/
│   ├── service_b/
│   └── conftest.py
│
├── notebooks/                       # Dev notebooks / experiments
├── .env
├── .env.example
├── requirements.txt / pyproject.toml
├── Dockerfile
├── docker-compose.yml               # Local development and testing only
├── Makefile
├── .gitignore
├── README.md


## 🚀 Getting Started

### Run Locally

```bash
make run


