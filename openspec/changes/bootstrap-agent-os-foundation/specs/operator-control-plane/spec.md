## ADDED Requirements

### Requirement: Task operations API
The Agent OS SHALL provide an operator control API that lists tasks, their current state, start time, owner, failure reason, and latest activity.

#### Scenario: Query active tasks
- **WHEN** an operator or admin client requests the task listing endpoint
- **THEN** the system returns currently active and recently completed tasks with their latest runtime state

#### Scenario: Filter failed tasks
- **WHEN** an operator or admin client requests tasks filtered by failed status
- **THEN** the system returns only tasks in a failed terminal state with their failure reasons visible

#### Scenario: View task detail
- **WHEN** an operator or admin client requests a specific task by identifier
- **THEN** the system returns the task state, active or latest attempt, terminal summary when present, and latest activity timestamp

### Requirement: Manual intervention actions
The Agent OS SHALL allow authorized operators to pause, resume, retry, and cancel tasks through the control API.

#### Scenario: Retry a failed task
- **WHEN** an authorized operator retries a failed task
- **THEN** the system creates a new execution attempt linked to the original task and records the retry action in audit events

#### Scenario: Resume a waiting task
- **WHEN** an authorized operator resumes a task that is in `waiting_user` or paused state
- **THEN** the system restarts execution from the latest valid checkpoint

### Requirement: Execution trace inspection
The Agent OS SHALL allow operators to inspect step history, tool calls, tool outputs, and state transitions for an individual task through queryable interfaces.

#### Scenario: Inspect task trace
- **WHEN** an operator or admin client requests task execution detail
- **THEN** the system returns the ordered execution timeline with steps, tool calls, outputs, and runtime transitions

#### Scenario: Inspect authorization failure
- **WHEN** a task fails because a tool invocation was denied
- **THEN** the task detail response shows the denied tool, required permission scope, and recorded authorization context
