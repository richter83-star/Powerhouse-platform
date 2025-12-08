
"""
Example usage of the ActionDispatcher with real-time feedback pipeline.

This example demonstrates:
1. Setting up the feedback pipeline with Kafka
2. Using the ActionDispatcher to execute agent actions
3. Tracking outcomes and metrics
4. Querying recent events
"""

import asyncio
from typing import Dict, Any

from core.action_dispatcher import ActionDispatcher, OrchestrationDispatcher, create_dispatcher
from core.feedback_pipeline import get_feedback_pipeline, OutcomeStatus
from core.base_agent import BaseAgent
from config.kafka_config import kafka_config


# Example agent implementation
class ExampleAgent(BaseAgent):
    """Simple example agent for demonstration."""
    
    def __init__(self):
        super().__init__(
            name="example_agent",
            agent_type="example",
            capabilities=["demonstration"]
        )
    
    def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent logic."""
        task = input_data.get("task", "")
        
        # Simulate some processing
        result = f"Processed task: {task}"
        
        return {
            "status": "success",
            "output": result,
            "metadata": {
                "tokens_used": 150,
                "llm_latency_ms": 250.5
            }
        }


async def example_single_dispatch():
    """Example: Single agent dispatch with outcome tracking."""
    
    print("=" * 60)
    print("Example 1: Single Agent Dispatch")
    print("=" * 60)
    
    # Create dispatcher
    dispatcher = create_dispatcher(
        kafka_servers=kafka_config.KAFKA_BOOTSTRAP_SERVERS if kafka_config.ENABLE_KAFKA else None,
        kafka_topic=kafka_config.KAFKA_OUTCOME_TOPIC,
        enable_metrics=True
    )
    
    # Create agent
    agent = ExampleAgent()
    
    # Dispatch action
    result = await dispatcher.dispatch(
        agent=agent,
        action_type="process_task",
        input_data={"task": "Analyze customer feedback"},
        context={"workflow": "customer_analysis"},
        tags=["customer", "feedback", "analysis"]
    )
    
    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    print(f"  Output: {result['output']}")
    print(f"  Duration: {result['duration_ms']:.2f}ms")
    print(f"  Event ID: {result['event_id']}")
    print(f"  Run ID: {result['run_id']}")
    
    # Get metrics
    metrics = dispatcher.get_metrics()
    print(f"\nDispatcher Metrics:")
    print(f"  Pipeline buffer: {metrics['pipeline_metrics']['buffer_size']}")
    if 'kafka' in metrics['pipeline_metrics']:
        kafka_metrics = metrics['pipeline_metrics']['kafka']
        print(f"  Kafka events sent: {kafka_metrics['events_sent']}")
        print(f"  Kafka success rate: {kafka_metrics['success_rate']:.2%}")


async def example_workflow_orchestration():
    """Example: Multi-agent workflow with outcome tracking."""
    
    print("\n" + "=" * 60)
    print("Example 2: Multi-Agent Workflow Orchestration")
    print("=" * 60)
    
    # Create orchestration dispatcher
    orchestrator = OrchestrationDispatcher()
    
    # Create multiple agents
    agents = [
        ExampleAgent(),
        ExampleAgent(),
        ExampleAgent()
    ]
    
    # Update agent names for distinction
    agents[0].name = "analyzer_agent"
    agents[1].name = "processor_agent"
    agents[2].name = "reporter_agent"
    
    # Execute workflow
    result = await orchestrator.execute_workflow(
        agents=agents,
        task="Process compliance report",
        tags=["compliance", "reporting"]
    )
    
    print(f"\nWorkflow Result:")
    print(f"  Workflow ID: {result['workflow_id']}")
    print(f"  Run ID: {result['run_id']}")
    print(f"  Agents executed: {len(result['outputs'])}")
    
    for i, output in enumerate(result['outputs'], 1):
        print(f"\n  Agent {i}: {output['agent']}")
        print(f"    Status: {output['status']}")
        print(f"    Event ID: {output['event_id']}")


async def example_query_events():
    """Example: Query recent outcome events."""
    
    print("\n" + "=" * 60)
    print("Example 3: Query Recent Outcome Events")
    print("=" * 60)
    
    # Get the feedback pipeline
    pipeline = get_feedback_pipeline()
    
    # Get recent events
    recent_events = pipeline.get_recent_events(count=5)
    
    print(f"\nRecent Events (last {len(recent_events)}):")
    for event in recent_events:
        print(f"\n  Event ID: {event.event_id}")
        print(f"    Agent: {event.agent_name}")
        print(f"    Action: {event.action_type}")
        print(f"    Status: {event.status.value}")
        print(f"    Duration: {event.duration_ms:.2f}ms")
        print(f"    Timestamp: {event.timestamp}")
    
    # Get only failed events
    failed_events = pipeline.get_recent_events(
        count=10,
        status=OutcomeStatus.FAILURE
    )
    
    if failed_events:
        print(f"\n\nFailed Events (last {len(failed_events)}):")
        for event in failed_events:
            print(f"\n  Event ID: {event.event_id}")
            print(f"    Agent: {event.agent_name}")
            print(f"    Error: {event.error_message}")


async def example_custom_hooks():
    """Example: Using custom hooks for monitoring."""
    
    print("\n" + "=" * 60)
    print("Example 4: Custom Execution Hooks")
    print("=" * 60)
    
    # Create dispatcher
    dispatcher = create_dispatcher()
    
    # Define custom hooks
    async def pre_execution_hook(agent, input_data, context):
        print(f"\n[PRE-HOOK] About to execute {agent.name}")
        print(f"[PRE-HOOK] Input: {input_data.get('task', 'N/A')}")
    
    async def post_execution_hook(agent, result, event):
        print(f"[POST-HOOK] Completed {agent.name}")
        print(f"[POST-HOOK] Status: {result['status']}")
        print(f"[POST-HOOK] Duration: {event.duration_ms:.2f}ms")
    
    # Add hooks
    dispatcher.add_pre_hook(pre_execution_hook)
    dispatcher.add_post_hook(post_execution_hook)
    
    # Execute with hooks
    agent = ExampleAgent()
    result = await dispatcher.dispatch(
        agent=agent,
        action_type="process_with_hooks",
        input_data={"task": "Test custom hooks"},
        context={}
    )
    
    print(f"\nFinal result: {result['status']}")


async def main():
    """Run all examples."""
    
    print("\n" + "=" * 60)
    print("ActionDispatcher & Feedback Pipeline Examples")
    print("=" * 60)
    
    # Check Kafka availability
    if kafka_config.ENABLE_KAFKA:
        print(f"\n✓ Kafka enabled: {kafka_config.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"✓ Outcome topic: {kafka_config.KAFKA_OUTCOME_TOPIC}")
    else:
        print("\n⚠ Kafka disabled - using logging fallback")
    
    # Run examples
    try:
        await example_single_dispatch()
        await example_workflow_orchestration()
        await example_query_events()
        await example_custom_hooks()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
