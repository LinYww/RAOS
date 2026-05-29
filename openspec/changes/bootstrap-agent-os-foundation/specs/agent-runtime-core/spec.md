## ADDED Requirements

### Requirement: Task lifecycle state machine
The Agent OS runtime SHALL execute every task through a defined lifecycle state machine that includes `created`, `queued`, `running`, `waiting_tool`, `waiting_user`, `succeeded`, `failed`, and `cancelled`.

#### Scenario: Task starts execution
- **WHEN** a new task is accepted by the runtime
- **THEN** the system records the task in `created`, transitions it to `queued`, and promotes it to `running` when execution begins

#### Scenario: Task waits on a tool result
- **WHEN** an executing agent requests a tool invocation that has not yet completed
- **THEN** the runtime transitions the task to `waiting_tool` and resumes it to `running` after the tool result is available

#### Scenario: Task is interrupted by an operator
- **WHEN** an operator cancels a running task
- **THEN** the runtime stops further execution, records a terminal `cancelled` state, and preserves the latest execution snapshot

### Requirement: Bounded execution control
The Agent OS runtime SHALL enforce execution boundaries for each task, including maximum step count, timeout limits, and explicit failure reasons.

#### Scenario: Task exceeds step limit
- **WHEN** a task consumes more steps than its configured maximum
- **THEN** the runtime marks the task as `failed` and records `step_limit_exceeded` as the failure reason

#### Scenario: Task exceeds timeout
- **WHEN** a task runs longer than its configured timeout window
- **THEN** the runtime terminates execution, marks the task as `failed`, and records `timeout_exceeded` in the execution record

### Requirement: Resumable execution snapshots
The Agent OS runtime SHALL persist resumable checkpoints that capture the current step, runtime state, task context, and pending dependencies.

#### Scenario: Resume after runtime restart
- **WHEN** the runtime restarts while a task has a valid persisted checkpoint
- **THEN** the system can reload the checkpoint and resume execution without losing completed steps or tool results

#### Scenario: Resume after waiting for user input
- **WHEN** a task is paused in `waiting_user` and the required user input is later provided
- **THEN** the runtime resumes the task from the saved checkpoint instead of replaying the task from the beginning

### Requirement: Provider-abstracted model execution
The Agent OS runtime SHALL invoke language models through a provider abstraction that supports an external hosted model backend in the first milestone.

#### Scenario: Execute a task with an external model provider
- **WHEN** a task requires model inference during runtime execution
- **THEN** the runtime sends the request through the provider interface and records the normalized model response in task state and events

#### Scenario: Replace the hosted model backend
- **WHEN** the implementation adds another model backend in the future
- **THEN** the runtime can switch providers without changing task lifecycle semantics, checkpoint structure, or tool gateway contracts
