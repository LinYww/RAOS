# RA_OS

First-version Agent OS runtime foundation built around FastAPI, Celery, and SQLAlchemy.

## Project Layout

This repository uses a `src` layout. Application code lives under `src/`, tests live under `tests/`, and planning/spec artifacts live under `openspec/`.

The main reason for using `src/` is to keep package imports honest:

- local test runs are less likely to accidentally import files from the repository root
- the runtime behavior is closer to an installed package layout
- code boundaries are clearer for API, runtime, persistence, and tool modules

### Top-level files

- [AGENTS.md](D:/myproject/RA_OS/AGENTS.md)
  Global engineering and collaboration rules for this repository.
- [README.md](D:/myproject/RA_OS/README.md)
  Entry document for setup, structure, and local MVP usage.
- [pyproject.toml](D:/myproject/RA_OS/pyproject.toml)
  Python project metadata and tool configuration. In this repository it is mainly used for build/tool settings such as setuptools discovery and pytest options.
- [requirements.txt](D:/myproject/RA_OS/requirements.txt)
  Runtime dependency list.
- [requirements-dev.txt](D:/myproject/RA_OS/requirements-dev.txt)
  Development dependency list built on top of `requirements.txt`.

### Directory map

```text
RA_OS/
  AGENTS.md
  README.md
  pyproject.toml
  requirements.txt
  requirements-dev.txt
  src/
    app/
      main.py
      api/
      core/
      models/
      providers/
      repositories/
      runtime/
      schemas/
      services/
      tools/
      workers/
  tests/
  openspec/
```

### Application package structure

- [src/app/main.py](D:/myproject/RA_OS/src/app/main.py)
  Application entrypoint. Exposes the FastAPI app object for `uvicorn`.
- [src/app/api](D:/myproject/RA_OS/src/app/api)
  Web/API layer. Contains route definitions, dependency wiring, and app bootstrap.
- [src/app/core](D:/myproject/RA_OS/src/app/core)
  Shared infrastructure such as settings, database setup, and low-level system wiring.
- [src/app/models](D:/myproject/RA_OS/src/app/models)
  SQLAlchemy ORM entities. These define the persisted data model such as `Agent`, `Task`, `TaskAttempt`, and `TaskEvent`.
- [src/app/schemas](D:/myproject/RA_OS/src/app/schemas)
  Pydantic request/response models used by the API boundary.
- [src/app/repositories](D:/myproject/RA_OS/src/app/repositories)
  Data-access layer. Encapsulates reads/writes for agents, tasks, checkpoints, tools, and events.
- [src/app/services](D:/myproject/RA_OS/src/app/services)
  Business orchestration layer. Connects repositories, runtime, and tool execution into use-case level operations.
- [src/app/runtime](D:/myproject/RA_OS/src/app/runtime)
  Runtime engine and state transition logic. This is the core of task execution behavior.
- [src/app/providers](D:/myproject/RA_OS/src/app/providers)
  Model provider abstraction and concrete implementations such as `mock` and hosted backends.
- [src/app/tools](D:/myproject/RA_OS/src/app/tools)
  Tool registration contracts, validation, permission checks, built-in tools, and invocation gateway logic.
- [src/app/workers](D:/myproject/RA_OS/src/app/workers)
  Background worker integration, currently centered around Celery task entrypoints.

### Non-application directories

- [tests](D:/myproject/RA_OS/tests)
  Automated tests for bootstrap behavior, runtime execution, transitions, tool gateway behavior, and service-level flows.
- [openspec](D:/myproject/RA_OS/openspec)
  Product and engineering planning artifacts such as proposals, design docs, specs, and task lists. This directory is for change management, not runtime code.

### Layering rules

To keep the structure maintainable, use these conventions when adding code:

- `api` should call `services`, not reach directly into unrelated runtime internals.
- `services` may coordinate repositories, runtime, providers, and tools.
- `repositories` should focus on persistence concerns, not business workflow decisions.
- `schemas` define API contracts, while `models` define database entities; do not mix them together.
- `runtime` owns execution semantics and state transitions; it should not become a general dumping ground for API or storage logic.
- `tools` should expose validated and permission-aware execution paths instead of ad hoc helper calls.

## Local MVP

The repository now includes a local single-node MVP path:

- `FastAPI` control API
- `SQLAlchemy` persistence with an in-memory SQLite default
- `Celery` configured for eager in-process execution by default
- Built-in tools for file read, shell exec, and HTTP fetch
- A local `mock` model provider so the MVP can run without external API credentials

## Run

1. Install dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

2. Start the API:

```bash
uvicorn app.main:app --app-dir src --reload
```

The FastAPI app now performs database initialization and built-in tool bootstrap through the application `lifespan` hook rather than the deprecated `startup` event API.

3. Verify the service is up:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

4. Create an agent:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/agents ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"local-mock-agent\",\"version\":\"v1\",\"system_prompt\":\"You are a helpful runtime agent.\",\"model_provider\":\"mock\",\"model_name\":\"mock\",\"enabled\":true}"
```

5. Submit a task:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tasks ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_id\":\"<AGENT_ID>\",\"prompt\":\"hello from the MVP\",\"allowed_scopes\":[]}"
```

6. Submit a task that uses a built-in tool:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tasks ^
  -H "Content-Type: application/json" ^
  -d "{\"agent_id\":\"<AGENT_ID>\",\"prompt\":\"tool:file.read README.md\",\"allowed_scopes\":[\"workspace.read\"]}"
```

## Test

Run the automated test suite with:

```bash
pytest -q
```

`pytest` cacheprovider is disabled in `pyproject.toml` so the suite can exit cleanly in restricted or sandboxed environments where writing `.pytest_cache` is unreliable.

## First-Version Runbook

### Startup flow

1. `uvicorn` imports `app.main:app`.
2. `create_app()` builds the FastAPI app and registers routers.
3. The application `lifespan` hook initializes the database and bootstraps built-in tool definitions.
4. Health endpoints become available at `/health/live` and `/health/ready`.

### Operator actions

- Register agents through `POST /api/v1/agents`.
- Submit tasks through `POST /api/v1/tasks`.
- Inspect task state through `GET /api/v1/tasks` and `GET /api/v1/tasks/{task_id}`.
- Review task history through `GET /api/v1/tasks/{task_id}/events`.
- Pause, resume, cancel, or retry tasks through the corresponding task action endpoints.

### Known first-release limitations

- The default runtime path is local-first and optimized for MVP validation, not distributed production deployment.
- The default database is in-memory SQLite, so data does not survive process restart unless `RA_OS_DATABASE_URL` is changed.
- Celery runs in eager in-process mode by default.
- The mock model provider is the default backend; hosted provider support exists but is not the default local path.
- Checkpoint recovery and event replay are not fully implemented yet.

## Notes

- The default runtime path is intentionally local-first so the MVP can run without Redis, PostgreSQL, or external model credentials.
- The default database is in-memory SQLite for zero-setup local runs. Set `RA_OS_DATABASE_URL` if you want file-backed or external persistence.
- To switch to a hosted model backend later, set `RA_OS_HOSTED_MODEL_PROVIDER=openai_compatible` and configure the matching API settings.
