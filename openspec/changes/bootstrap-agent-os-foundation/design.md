## Context

This change bootstraps the first version plan for a new Agent OS. The goal is not to ship a general-purpose AI desktop or a multi-agent orchestration platform in the first milestone. Instead, the project needs a stable operating core that can run one agent task safely, invoke tools through a controlled interface, persist execution state, and expose an operator-facing control surface.

The main constraint is scope discipline. Early Agent projects often over-invest in chat UI, autonomous behavior, or long-term memory before the runtime model is stable. This design intentionally makes the runtime lifecycle, tool boundary, state persistence, and observability the foundation for later layers.

The implementation baseline for this milestone is:
- `FastAPI` for control APIs
- `PostgreSQL` for system-of-record persistence
- `Redis` as the Celery broker
- `Celery` for asynchronous task execution
- `SQLAlchemy` for relational data access
- `Pydantic Settings` for configuration
- `Docker Compose` for local deployment and service orchestration
- An external hosted model API as the first LLM backend

Stakeholders for the first milestone are:
- Product owner, who needs a credible first-version scope
- Platform engineer, who needs clear module boundaries
- Operator or admin, who needs visibility and control over running tasks

## Goals / Non-Goals

**Goals:**
- Define a first-version architecture centered on a single-agent runtime
- Establish a task-centric lifecycle and state machine
- Use an external model provider for the first implementation without coupling runtime logic to a single vendor
- Define a standard contract for tool registration and execution
- Define a persistent state and event model that supports recovery and replay
- Define an API-first operator control plane that can inspect and intervene in tasks without requiring a web frontend

**Non-Goals:**
- Multi-agent coordination and delegation
- Plugin marketplace or third-party extension ecosystem
- Long-term user memory or persona modeling
- Dedicated web frontend or polished end-user product UX in the first milestone
- Local model serving infrastructure as part of the first implementation path
- Hardware-level or kernel-level operating system functionality

## Decisions

### Decision: Use a task-centric architecture instead of a chat-centric architecture
The first version will model execution around `Task` as the primary object, not conversation threads. A task can contain messages and context, but the runtime contract, state transitions, and recovery model will all attach to the task record.

Rationale:
- Task is the unit that operators can schedule, inspect, pause, retry, and audit
- Tool execution and bounded runtime controls fit naturally around task state
- This keeps the platform usable for both chat and non-chat automations later

Alternatives considered:
- Chat-first model: simpler for demos, but weak for retries, checkpoints, and operator control
- Workflow-first model: too heavy for the first milestone and likely to overfit orchestration before core runtime behavior is proven

### Decision: Start with a single-agent runtime
The first milestone will support one active agent execution loop per task rather than agent teams, planners, or delegated workers.

Rationale:
- Single-agent execution reduces coordination complexity
- It makes state persistence, failure handling, and trace inspection much easier to validate
- It creates a clean baseline for future multi-agent expansion

Alternatives considered:
- Multi-agent from day one: higher demo appeal, but much higher failure surface and observability burden
- Pure workflow engine without agent reasoning: safer, but no longer validates Agent OS behavior

### Decision: Introduce a dedicated tool gateway
Tool invocation will go through a standard gateway layer rather than allowing the runtime to call arbitrary adapters directly.

Rationale:
- Centralizes validation, permission checks, timeout policy, and audit logging
- Makes tools composable and safer to expose
- Creates a stable contract for future pluginization

Alternatives considered:
- Direct runtime-to-tool calls: faster to prototype, but hard to secure or observe consistently
- Full external plugin RPC bus: more flexible, but unnecessary complexity for the first version

### Decision: Persist execution state and events separately but link them by task identity
The system will maintain a current task state record plus an append-only event stream for replay and debugging.

Rationale:
- Current state supports fast operator views
- Event history supports debugging, replay, audit, and future analytics
- This separation avoids reconstructing current state from a long event log on every read

Alternatives considered:
- Event sourcing only: clean model, but heavier to implement for the first milestone
- Mutable state only: simpler, but weak for replay, audit, and root-cause analysis

### Decision: Ship an API-first control plane and defer the web frontend
The first control surface will be `FastAPI` endpoints plus developer/admin interfaces such as CLI or scripts. A dedicated web frontend is deferred to a later phase.

Rationale:
- Execution transparency is critical for validating the runtime
- Operator actions like retry, cancel, and resume must exist before autonomy grows
- This keeps the project centered on operating-system concerns rather than assistant presentation
- API-first contracts make it cheaper to add a web console later without reworking runtime interfaces

Alternatives considered:
- Minimal web dashboard in the first milestone: adds delivery overhead before runtime behavior is stable
- CLI-only control with no APIs: acceptable for very early experiments, but too limiting for later integrations and automation

### Decision: Use FastAPI, PostgreSQL, Redis, and Celery as the implementation baseline
The first implementation will use `FastAPI` for the control plane, `PostgreSQL` for persisted runtime state, `Redis` as the Celery broker, and `Celery` workers for asynchronous execution.

Rationale:
- `FastAPI` gives a fast path to typed APIs and operational endpoints
- `PostgreSQL` should remain the system of record for task state, logs, checkpoints, and results
- `Celery` provides mature async execution, retries, and worker scaling semantics
- `Redis` is a practical initial broker with low setup friction for local deployment

Alternatives considered:
- `Arq` instead of `Celery`: lighter, but less aligned with the desired maturity and scheduling ecosystem
- Web-first application framework: unnecessary before a frontend exists
- Using Celery result backend as the primary system record: weaker fit than storing Agent OS execution truth in business persistence

### Decision: Use an external hosted model backend first and defer local serving
The first implementation will call an external model provider through a dedicated provider interface. Local model deployment remains a later extension behind the same abstraction boundary.

Rationale:
- The first milestone needs to validate Agent OS runtime behavior, not operate an LLM serving platform
- Hosted APIs reduce startup complexity around GPUs, model packaging, serving reliability, and inference tuning
- A provider abstraction preserves the option to add local backends later without refactoring the task runtime

Alternatives considered:
- Local model serving from day one: increases infrastructure scope and slows validation of the runtime core
- Binding the runtime directly to one hosted vendor SDK: faster initially, but creates avoidable migration cost later

## Risks / Trade-offs

- [Scope expansion into "AI product" features] -> Keep first milestone limited to runtime, tools, state, and control plane; defer memory, marketplace, and multi-agent
- [Runtime model becomes too abstract to implement quickly] -> Use a minimal lifecycle and add states only when they serve recovery or operator control
- [Tool contract is either too rigid or too loose] -> Start with schema validation, permissions, timeout, and audit as the mandatory core; defer advanced features
- [State persistence adds implementation weight] -> Separate must-have checkpoint/state fields from optional analytics data
- [Control plane becomes a frontend project] -> Limit first version to task APIs plus minimal CLI/admin workflows
- [Celery state diverges from business task state] -> Treat PostgreSQL as the source of truth and use Celery only for dispatch and worker execution
- [Hosted provider lock-in leaks into runtime design] -> Isolate model invocation behind a provider interface with normalized request and response contracts

## Implementation Shape

### Proposed module boundaries

- `app.api`: FastAPI routers, request/response schemas, and operator-facing endpoints
- `app.runtime`: task execution loop, step policies, checkpoint handling, and runtime lifecycle transitions
- `app.models`: SQLAlchemy entities and persistence mappings
- `app.repositories`: database access patterns for tasks, events, tool history, and checkpoints
- `app.services`: orchestration services for task submission, retry, cancellation, and agent registration
- `app.providers`: model provider abstraction plus hosted provider adapters
- `app.tools`: tool registry, validation, permission enforcement, and built-in tools
- `app.workers`: Celery app, task dispatch entrypoints, and worker-side execution bootstrap
- `app.core`: settings, logging, security helpers, time utilities, and shared constants

### Proposed project layout

```text
src/
  app/
    api/
      routers/
    core/
    models/
    providers/
    repositories/
    runtime/
    schemas/
    services/
    tools/
    workers/
    main.py
tests/
  api/
  runtime/
  providers/
  tools/
  workers/
ops/
  docker/
  scripts/
```

### Core entities for phase 1

- `Agent`: agent identity, version, system prompt, model provider key, model name, default runtime policy, enabled flag
- `Task`: externally visible task record with agent reference, current state, trigger source, priority, timestamps, and terminal summary
- `TaskAttempt`: execution attempt record linked to a task for initial runs and retries
- `TaskEvent`: append-only ordered event log for lifecycle transitions, tool activity, operator actions, and model calls
- `ToolDefinition`: registered tool metadata, schemas, timeout policy, permission scope, and enabled flag
- `ToolInvocation`: per-attempt record of tool requests, validation results, authorization context, outputs, and errors
- `Checkpoint`: resumable runtime snapshot per attempt, including step index, serialized context, and pending dependency state

### Model provider contract

The provider layer should normalize hosted model backends behind one internal interface:

- `generate(request) -> response`
- `stream(request) -> event iterator` is optional and can be deferred if phase 1 only needs non-streaming execution
- `count_tokens(request) -> usage estimate` is optional for the MVP

Normalized request fields:
- `messages`
- `system_prompt`
- `tools`
- `temperature`
- `max_output_tokens`
- `metadata`

Normalized response fields:
- `output_text`
- `tool_calls`
- `stop_reason`
- `usage`
- `raw_provider_response`

The runtime must depend only on this normalized contract, not on vendor SDK response shapes.

### Phase 1 API surface

Agent APIs:
- `POST /agents`
- `GET /agents`
- `GET /agents/{agent_id}`

Task APIs:
- `POST /tasks`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `GET /tasks/{task_id}/events`
- `POST /tasks/{task_id}/cancel`
- `POST /tasks/{task_id}/retry`

Operational health APIs:
- `GET /health/live`
- `GET /health/ready`

### Execution flow

1. Client creates a task through `POST /tasks`
2. API validates the task request, persists `Task` and `TaskAttempt`, emits a `created` event, and queues Celery work
3. Worker loads the attempt, transitions state to `queued` then `running`, and enters the runtime loop
4. Runtime calls the model provider, decides on next action, invokes tools through the gateway when needed, and persists checkpoints after each bounded step
5. Runtime appends events and updates current task state after every significant transition
6. Runtime writes terminal state and result summary to `PostgreSQL`
7. Operator reads status and history through control APIs and can cancel or retry when allowed

## Migration Plan

This is a greenfield project, so the migration plan is a staged implementation plan rather than a legacy migration.

1. Define task model, lifecycle states, and event schema
2. Define the model provider abstraction and integrate one external hosted backend
3. Implement runtime loop with bounded execution and checkpoint persistence
4. Implement tool gateway with registration, validation, and permission checks
5. Implement state store and event stream persistence
6. Implement API-first control plane for task inspection and intervention
7. Validate the end-to-end loop with one agent and a small set of tools

Rollback strategy:
- If a later layer is unstable, keep the runtime and tool gateway operational behind a limited developer interface
- Disable control plane actions that are not yet safe instead of widening the runtime surface prematurely

## Open Questions

- Should the first version target local single-node deployment only, or also include a minimal distributed deployment model?
- What is the minimum set of built-in tools needed to validate the OS concept: file, shell, HTTP, or browser as well?
- Does the first version need tenant isolation from day one, or can it be introduced in the second milestone?
