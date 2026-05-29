## Why

The project needs a clear first version plan for a new Agent OS so we can start with a stable core instead of jumping straight into UI polish, multi-agent orchestration, or loosely scoped "AI assistant" features. The first milestone should prove that an agent can be created, executed, controlled, and observed safely inside a consistent runtime.

## What Changes

- Define the first-version scope for a new Agent OS around a single-agent runtime and control plane.
- Define the first-version delivery shape as an API-first, no-frontend MVP for a new Agent OS.
- Introduce a task-centric execution model with explicit lifecycle states, pause/resume/cancel semantics, and execution checkpoints.
- Introduce a hosted-model-first provider integration strategy for the first milestone, while preserving an abstraction layer for future local model backends.
- Introduce a tool execution contract that standardizes registration, input/output validation, permission declaration, timeout handling, and audit metadata.
- Introduce a state and event model for task context, tool history, intermediate artifacts, and replayable execution traces.
- Introduce an operator-facing control plane delivered through APIs and developer/admin interfaces for viewing task status, failures, step history, and manual intervention actions.
- Exclude multi-agent collaboration, plugin marketplace, long-term persona memory, and advanced autonomous workflows from the first version scope.
- Exclude a dedicated web frontend from the first implementation milestone.

## Capabilities

### New Capabilities
- `agent-runtime-core`: Execute a single agent task through a controlled runtime lifecycle with resumable state and bounded execution.
- `tool-execution-gateway`: Register and run tools through a standard protocol with validation, permission checks, and auditable results.
- `agent-state-and-events`: Persist task state, execution events, tool history, and intermediate artifacts needed for recovery and replay.
- `operator-control-plane`: Provide operational visibility and controls for monitoring, interrupting, retrying, and inspecting agent tasks.

### Modified Capabilities
- None.

## Impact

- Affects the architecture and delivery plan for the new Agent OS project.
- Establishes the initial module boundaries for runtime, tools, state storage, event streaming, and control APIs.
- Defines the first set of APIs, persistence models, and operator workflows that implementation will follow.
- Locks the first implementation baseline to `FastAPI + PostgreSQL + Redis + Celery + SQLAlchemy + Pydantic Settings + Docker Compose`.
- Establishes external model APIs as the first LLM backend, with local model serving deferred behind a provider abstraction.
- Reduces delivery risk by narrowing the first milestone to a verifiable execution loop instead of a broad assistant product surface.
