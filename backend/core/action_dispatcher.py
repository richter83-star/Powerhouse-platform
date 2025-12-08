
"""
Action Dispatcher with Real-Time Feedback

This module provides an enhanced action dispatcher that tracks agent executions
and publishes structured outcome events to the feedback pipeline.
"""

import uuid
import time
import traceback
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from contextlib import asynccontextmanager

from core.base_agent import BaseAgent
from core.feedback_pipeline import (
    FeedbackPipeline,
    OutcomeEvent,
    OutcomeStatus,
    EventSeverity,
    get_feedback_pipeline
)
from utils.logging import get_logger

logger = get_logger(__name__)


class ActionDispatcher:
    """
    Dispatcher for agent actions with outcome tracking.
    
    This dispatcher wraps agent execution and automatically captures
    performance metrics, errors, and outcomes, publishing them to
    the feedback pipeline for real-time monitoring and analysis.
    """
    
    def __init__(
        self,
        feedback_pipeline: Optional[FeedbackPipeline] = None,
        enable_metrics: bool = True,
        enable_error_capture: bool = True
    ):
        """
        Initialize action dispatcher.
        
        Args:
            feedback_pipeline: Feedback pipeline instance
            enable_metrics: Enable performance metrics collection
            enable_error_capture: Capture error details
        """
        self.pipeline = feedback_pipeline or get_feedback_pipeline()
        self.enable_metrics = enable_metrics
        self.enable_error_capture = enable_error_capture
        
        # Execution hooks
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
        
        logger.info("ActionDispatcher initialized")
    
    async def dispatch(
        self,
        agent: BaseAgent,
        action_type: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        run_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Dispatch an action to an agent and record the outcome.
        
        Args:
            agent: Agent to execute
            action_type: Type of action being performed
            input_data: Input data for the agent
            context: Execution context
            run_id: Optional run ID
            correlation_id: Optional correlation ID
            workflow_id: Optional workflow ID
            tags: Optional tags for categorization
            
        Returns:
            dict: Agent execution result with added metadata
        """
        event_id = str(uuid.uuid4())
        run_id = run_id or str(uuid.uuid4())
        start_time = datetime.utcnow()
        start_perf = time.perf_counter()
        
        # Initialize result
        result: Dict[str, Any] = {
            "status": OutcomeStatus.PENDING.value,
            "output": None,
            "metadata": {}
        }
        
        # Tracking variables
        error_message = None
        error_type = None
        stack_trace = None
        status = OutcomeStatus.PENDING
        severity = EventSeverity.INFO
        
        try:
            # Execute pre-hooks
            for hook in self._pre_hooks:
                await self._safe_hook_execution(hook, agent, input_data, context)
            
            # Execute the agent
            logger.info(
                f"Dispatching action: agent={agent.name} "
                f"type={action_type} event_id={event_id}"
            )
            
            result = agent.execute(input_data, context)
            
            # Determine status from result
            result_status = result.get("status", "success").lower()
            if result_status == "success":
                status = OutcomeStatus.SUCCESS
                severity = EventSeverity.INFO
            elif result_status == "partial":
                status = OutcomeStatus.PARTIAL
                severity = EventSeverity.WARNING
            elif result_status == "failure":
                status = OutcomeStatus.FAILURE
                severity = EventSeverity.ERROR
                error_message = result.get("error", "Unknown failure")
            else:
                status = OutcomeStatus.SUCCESS
                severity = EventSeverity.INFO
            
        except TimeoutError as e:
            status = OutcomeStatus.TIMEOUT
            severity = EventSeverity.WARNING
            error_message = str(e)
            error_type = "TimeoutError"
            if self.enable_error_capture:
                stack_trace = traceback.format_exc()
            result["status"] = "timeout"
            result["error"] = error_message
            logger.warning(f"Action timeout: {error_message}")
            
        except Exception as e:
            status = OutcomeStatus.FAILURE
            severity = EventSeverity.ERROR
            error_message = str(e)
            error_type = type(e).__name__
            if self.enable_error_capture:
                stack_trace = traceback.format_exc()
            result["status"] = "failure"
            result["error"] = error_message
            logger.error(f"Action failed: {error_message}", exc_info=True)
        
        finally:
            # Calculate metrics
            end_time = datetime.utcnow()
            end_perf = time.perf_counter()
            duration_ms = (end_perf - start_perf) * 1000
            
            # Extract LLM metrics if available
            llm_latency_ms = result.get("metadata", {}).get("llm_latency_ms")
            tokens_used = result.get("metadata", {}).get("tokens_used")
            
            # Create outcome event
            event = OutcomeEvent(
                event_id=event_id,
                run_id=run_id,
                agent_name=agent.name,
                agent_type=agent.agent_type,
                action_type=action_type,
                timestamp=datetime.utcnow().isoformat(),
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration_ms=duration_ms,
                status=status,
                severity=severity,
                latency_ms=duration_ms,
                llm_latency_ms=llm_latency_ms,
                tokens_used=tokens_used,
                output=result.get("output"),
                error_message=error_message,
                error_type=error_type,
                stack_trace=stack_trace,
                input_data=input_data if self.enable_metrics else None,
                context_snapshot=self._create_context_snapshot(context) if self.enable_metrics else None,
                correlation_id=correlation_id,
                workflow_id=workflow_id,
                tags=tags or [],
                metadata=result.get("metadata", {})
            )
            
            # Publish outcome event
            try:
                await self.pipeline.record_outcome(event)
            except Exception as e:
                logger.error(f"Failed to record outcome event: {e}")
            
            # Execute post-hooks
            for hook in self._post_hooks:
                await self._safe_hook_execution(hook, agent, result, event)
            
            # Add event metadata to result
            result["event_id"] = event_id
            result["run_id"] = run_id
            result["duration_ms"] = duration_ms
        
        return result
    
    def _create_context_snapshot(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a lightweight snapshot of the context.
        
        Args:
            context: Full context
            
        Returns:
            dict: Snapshot with key information
        """
        # Only include essential context info to avoid bloat
        return {
            "task": context.get("task"),
            "agent_count": len(context.get("outputs", [])),
            "state_keys": list(context.get("state", {}).keys())
        }
    
    async def _safe_hook_execution(
        self,
        hook: Callable,
        *args,
        **kwargs
    ) -> None:
        """
        Safely execute a hook without failing the main execution.
        
        Args:
            hook: Hook function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        try:
            result = hook(*args, **kwargs)
            # Handle async hooks
            if hasattr(result, '__await__'):
                await result
        except Exception as e:
            logger.warning(f"Hook execution failed: {e}")
    
    def add_pre_hook(self, hook: Callable) -> None:
        """
        Add a pre-execution hook.
        
        Args:
            hook: Function to call before execution
        """
        self._pre_hooks.append(hook)
        logger.debug(f"Added pre-hook: {hook.__name__}")
    
    def add_post_hook(self, hook: Callable) -> None:
        """
        Add a post-execution hook.
        
        Args:
            hook: Function to call after execution
        """
        self._post_hooks.append(hook)
        logger.debug(f"Added post-hook: {hook.__name__}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get dispatcher metrics."""
        return {
            "pre_hooks": len(self._pre_hooks),
            "post_hooks": len(self._post_hooks),
            "pipeline_metrics": self.pipeline.get_metrics()
        }


class OrchestrationDispatcher:
    """
    Enhanced orchestrator with action dispatching and feedback.
    
    This combines the orchestration logic with the action dispatcher
    to provide comprehensive outcome tracking across multi-agent workflows.
    """
    
    def __init__(
        self,
        dispatcher: Optional[ActionDispatcher] = None,
        feedback_pipeline: Optional[FeedbackPipeline] = None
    ):
        """
        Initialize orchestration dispatcher.
        
        Args:
            dispatcher: Action dispatcher instance
            feedback_pipeline: Feedback pipeline instance
        """
        self.pipeline = feedback_pipeline or get_feedback_pipeline()
        self.dispatcher = dispatcher or ActionDispatcher(feedback_pipeline=self.pipeline)
        
        logger.info("OrchestrationDispatcher initialized")
    
    async def execute_workflow(
        self,
        agents: List[BaseAgent],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a multi-agent workflow with outcome tracking.
        
        Args:
            agents: List of agents to execute
            task: Task description
            context: Shared context
            workflow_id: Workflow identifier
            tags: Workflow tags
            
        Returns:
            dict: Workflow results with outcome metadata
        """
        workflow_id = workflow_id or str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        context = context or {}
        context["task"] = task
        context["outputs"] = []
        context["state"] = {}
        
        logger.info(
            f"Starting workflow: workflow_id={workflow_id} "
            f"agents={len(agents)} task={task[:50]}..."
        )
        
        # Execute each agent
        for agent in agents:
            result = await self.dispatcher.dispatch(
                agent=agent,
                action_type="workflow_step",
                input_data={"task": task},
                context=context,
                run_id=run_id,
                workflow_id=workflow_id,
                tags=tags
            )
            
            # Add to outputs
            context["outputs"].append({
                "agent": agent.name,
                "output": result.get("output"),
                "status": result.get("status"),
                "event_id": result.get("event_id")
            })
            
            # Stop on failure if configured
            if result.get("status") == "failure":
                logger.warning(f"Workflow stopped due to failure in {agent.name}")
                break
        
        return {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "outputs": context["outputs"],
            "state": context["state"],
            "metrics": self.dispatcher.get_metrics()
        }


# Factory function
def create_dispatcher(
    kafka_servers: Optional[str] = None,
    kafka_topic: str = "agent-outcomes",
    enable_metrics: bool = True
) -> ActionDispatcher:
    """
    Create an action dispatcher with feedback pipeline.
    
    Args:
        kafka_servers: Kafka bootstrap servers
        kafka_topic: Kafka topic name
        enable_metrics: Enable metrics collection
        
    Returns:
        ActionDispatcher: Configured dispatcher
    """
    pipeline = get_feedback_pipeline(
        kafka_servers=kafka_servers,
        kafka_topic=kafka_topic
    )
    
    return ActionDispatcher(
        feedback_pipeline=pipeline,
        enable_metrics=enable_metrics
    )
