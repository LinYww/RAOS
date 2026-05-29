## 1. Runtime foundation

- [x] 1.1 Define the `Task` domain model and lifecycle states for `created`, `queued`, `running`, `waiting_tool`, `waiting_user`, `succeeded`, `failed`, and `cancelled`
- [x] 1.2 Define failure reason codes, step limits, timeout behavior, and checkpoint metadata required by the runtime
- [x] 1.3 Implement the single-agent execution loop with bounded step execution and terminal state handling
- [x] 1.4 Implement pause, resume, and cancel transitions with checkpoint persistence
- [x] 1.5 Define a model provider abstraction and integrate one external hosted model backend for the MVP runtime

## 1A. Bootstrap skeleton

- [x] 1A.1 Create the initial project layout for `api`, `runtime`, `models`, `repositories`, `providers`, `tools`, `workers`, and `core`
- [x] 1A.2 Define the initial SQLAlchemy entities for `Agent`, `Task`, `TaskAttempt`, `TaskEvent`, `ToolDefinition`, `ToolInvocation`, and `Checkpoint`
- [x] 1A.3 Define Pydantic request/response schemas for agent registration, task submission, task detail, task events, cancel, and retry actions
- [x] 1A.4 Wire the initial FastAPI application, Celery app, and shared settings bootstrap

## 2. Tool gateway

- [x] 2.1 Define the tool registration contract, including identity, input schema, output schema, permission scope, timeout policy, and audit fields
- [x] 2.2 Implement tool registration validation and rejection for incomplete or invalid definitions
- [x] 2.3 Implement runtime-to-tool invocation flow with input validation, output validation, and structured error handling
- [x] 2.4 Implement permission enforcement and authorization failure reporting for tool execution

## 3. State and event persistence

- [x] 3.1 Design persistence models for task state, step history, tool invocation history, and intermediate artifacts
- [x] 3.2 Implement append-only event emission for lifecycle transitions, tool calls, tool results, operator actions, and terminal outcomes
- [ ] 3.3 Implement checkpoint loading and task recovery from persisted state after restart
- [ ] 3.4 Implement task history replay using the ordered event stream

## 4. Operator control plane

- [x] 4.1 Define operator-facing APIs for task listing, task detail, retry, resume, pause, and cancel actions
- [x] 4.2 Implement task query endpoints that return state, owner, latest activity, and failure reason for operator use
- [ ] 4.3 Implement CLI or admin workflows that consume the control APIs for task inspection, logs, and runtime transitions
- [x] 4.4 Implement operator action handling with audit logging for retry, resume, pause, and cancel

## 5. Built-in validation tools

- [x] 5.1 Add a minimal built-in file tool that can be invoked through the tool gateway
- [x] 5.2 Add a minimal built-in shell or command execution tool with explicit sandbox and timeout policy
- [x] 5.3 Add a minimal built-in HTTP tool for validating non-local tool invocation behavior
- [x] 5.4 Validate that the runtime can execute a task that uses at least one built-in tool and reaches a terminal state

## 6. Verification and readiness

- [ ] 6.1 Add automated tests for lifecycle transitions, timeout handling, checkpoint recovery, and cancellation
- [x] 6.2 Add automated tests for tool validation, permission denial, and structured tool failure behavior
- [ ] 6.3 Add automated tests for event ordering, task replay, and operator intervention flows
- [x] 6.4 Write the first-version runbook covering startup flow, operator actions, and known first-release limitations
