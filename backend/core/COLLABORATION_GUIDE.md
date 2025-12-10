# Multi-Agent Collaboration Guide

## Overview

The Powerhouse platform now supports true multi-agent collaboration through the integrated communication protocol. Agents can discover, communicate, delegate tasks, and reach consensus with each other.

## Key Features

### 1. Agent Registration and Discovery
- All agents automatically register with the communication protocol
- Agents can discover each other by capability or type
- Service discovery at runtime

### 2. Inter-Agent Communication
- Direct messaging between agents
- Broadcast messaging to all agents
- Request-response patterns
- Message queuing and delivery

### 3. Shared Context
- Global state accessible to all agents
- Per-agent namespaced state
- State history and versioning
- Watch mechanism for state changes

### 4. Task Delegation
- Agents can delegate subtasks to other agents
- Capability-based agent selection
- Automatic delegation handling
- Result forwarding

### 5. Consensus Mechanisms
- Voting-based consensus
- Proposal and vote messaging
- Majority rule decision making
- Configurable consensus requirements

## Usage

### Basic Collaborative Execution

```python
from core.orchestrator_with_communication import OrchestratorWithCommunication

# Initialize orchestrator with communication
orchestrator = OrchestratorWithCommunication(
    agent_names=["react", "chain_of_thought", "planning", "evaluator"],
    execution_mode="collaborative",
    enable_consensus=True
)

# Run task with collaboration
result = orchestrator.run(
    task="Analyze this complex problem and create a detailed solution plan",
    config={
        "execution_mode": "collaborative",
        "require_consensus": True  # Require consensus on final solution
    }
)

# Access collaboration metadata
print(f"Agents involved: {result['collaboration']['agents_involved']}")
print(f"Messages exchanged: {result['collaboration']['messages_exchanged']}")
print(f"Delegations: {result['collaboration']['delegations']}")
if 'consensus' in result:
    print(f"Consensus reached: {result['consensus']['consensus_reached']}")
```

### Agent-to-Agent Communication

Agents can communicate by returning special output structures:

```python
# In an agent's run() method, return:
{
    "output": "Agent's main output",
    "delegate_to": "planning",  # Delegate to planning capability
    "delegation_task": "Create a detailed plan for this solution",
    "send_message": {
        "receiver": "EvaluatorAgent",
        "message_type": "REQUEST",
        "content": {"question": "Is this solution correct?"}
    },
    "broadcast": {
        "message_type": "NOTIFICATION",
        "content": {"event": "analysis_complete", "results": [...]}
    }
}
```

### Accessing Shared State

Agents can access shared state through the context:

```python
# In agent's run() method:
def run(self, context):
    # Access shared state
    shared_state = context.get("shared_state", {})
    task = shared_state.get("task")
    
    # Access other agents' outputs
    react_output = shared_state.get("ReactAgent_output")
    
    # Access messages
    messages = context.get("messages", [])
    for msg in messages:
        if msg["message_type"] == "TASK_ASSIGNMENT":
            # Handle delegated task
            pass
    
    # Your agent logic here
    return {"output": "Agent result"}
```

### Statistics and Monitoring

```python
# Get collaboration statistics
stats = orchestrator.get_collaboration_stats()
print(f"Total collaborations: {stats['total_collaborations']}")
print(f"Total delegations: {stats['total_delegations']}")
print(f"Total messages: {stats['total_messages_exchanged']}")
print(f"Protocol stats: {stats['protocol_stats']}")
```

## Execution Modes

### Collaborative Mode (New)
- Agents communicate and collaborate
- Task delegation enabled
- Shared context available
- Consensus mechanisms active

### Sequential Mode
- Agents run one after another
- Communication protocol available but limited interaction
- Context is passed sequentially

### Parallel Mode
- Agents run simultaneously
- Can communicate via shared context
- Messages delivered asynchronously

### Adaptive Mode
- Selects agents based on task requirements
- Communication available for selected agents
- Optimized for performance

## Advanced Features

### Custom Consensus Logic

You can implement custom consensus mechanisms by extending the orchestrator:

```python
class CustomOrchestrator(OrchestratorWithCommunication):
    def _reach_consensus(self, context, agents, run_id):
        # Custom consensus logic
        # Could use weighted voting, Byzantine fault tolerance, etc.
        return super()._reach_consensus(context, agents, run_id)
```

### Agent Capabilities

Agents are automatically assigned capabilities based on their type:
- `react`: ["reasoning", "acting", "tool_usage"]
- `chain_of_thought`: ["reasoning", "step_by_step"]
- `tree_of_thought`: ["reasoning", "exploration", "backtracking"]
- `planning`: ["planning", "scheduling"]
- `evaluator`: ["evaluation", "scoring"]

You can override capabilities when registering agents.

## Best Practices

1. **Use Collaborative Mode** for complex tasks requiring multiple perspectives
2. **Enable Consensus** for critical decisions that need agent agreement
3. **Leverage Delegation** to break down complex tasks into subtasks
4. **Monitor Collaboration Stats** to understand system behavior
5. **Use Shared Context** for passing data between agents efficiently
6. **Handle Messages** in agents to respond to delegations and requests

## Performance Considerations

- Communication adds overhead, but enables true collaboration
- Use parallel execution mode with collaboration for better performance
- Limit consensus requirements to critical decisions
- Monitor message queues to prevent bottlenecks

