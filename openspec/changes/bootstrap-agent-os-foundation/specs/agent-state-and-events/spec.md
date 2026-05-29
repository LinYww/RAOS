## ADDED Requirements

### Requirement: Persistent task execution record
The Agent OS SHALL persist a task execution record that includes task metadata, runtime state, conversation context, tool call history, and final outcome.

#### Scenario: Persist state after each step
- **WHEN** the runtime completes an execution step
- **THEN** the system updates the task execution record with the new state, step output, and timestamp

#### Scenario: Persist final outcome
- **WHEN** a task reaches a terminal state
- **THEN** the system stores the terminal state, completion timestamp, and outcome summary in the execution record

### Requirement: Replayable event stream
The Agent OS SHALL emit ordered events for task lifecycle transitions, tool invocations, tool results, operator actions, and terminal outcomes.

#### Scenario: Emit runtime events during execution
- **WHEN** a task transitions between runtime states
- **THEN** the system emits ordered events that reflect the transition and the associated task identifier

#### Scenario: Replay task history
- **WHEN** an operator requests the history of a completed or failed task
- **THEN** the system returns the ordered event stream needed to reconstruct the task timeline

### Requirement: Intermediate artifact persistence
The Agent OS SHALL persist intermediate artifacts produced during execution, including structured outputs, tool attachments, and checkpoint payloads.

#### Scenario: Store an intermediate tool artifact
- **WHEN** a tool returns a file, structured object, or other durable artifact
- **THEN** the system stores the artifact with a reference linked to the task and invocation that produced it

#### Scenario: Recover artifact references after restart
- **WHEN** the runtime reloads a task after restart
- **THEN** the system restores references to previously persisted intermediate artifacts from the task record

### Requirement: Phase 1 core persistence entities
The Agent OS SHALL persist a minimum phase 1 entity set consisting of `Agent`, `Task`, `TaskAttempt`, `TaskEvent`, `ToolDefinition`, `ToolInvocation`, and `Checkpoint`.

#### Scenario: Persist a task attempt
- **WHEN** a task is created or retried
- **THEN** the system creates a distinct `TaskAttempt` linked to the parent `Task` and uses that attempt as the execution and replay unit

#### Scenario: Persist an ordered event against an attempt
- **WHEN** the runtime or operator emits an event during execution
- **THEN** the system stores the event against the corresponding `TaskAttempt` with an order key sufficient to replay the execution timeline deterministically
