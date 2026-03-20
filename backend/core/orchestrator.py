from typing import List, Dict, Any, Optional, Callable
from importlib import import_module
import asyncio
import concurrent.futures
import time
from concurrent.futures import ThreadPoolExecutor
from utils.logging import get_logger

logger = get_logger(__name__)

# Import communication protocol (optional dependency)
try:
    from communication import CommunicationProtocol
    COMMUNICATION_AVAILABLE = True
except ImportError:
    COMMUNICATION_AVAILABLE = False
    CommunicationProtocol = None


class Orchestrator:
    """
    Multi-agent orchestrator supporting sequential, parallel, and adaptive execution.
    """
    
    def __init__(self, agent_names: List[str], max_agents: int = 19, execution_mode: str = "sequential"):
        """
        Initialize orchestrator.
        
        Args:
            agent_names: List of agent names to load
            max_agents: Maximum number of agents
            execution_mode: Execution mode - "sequential", "parallel", or "adaptive"
        """
        if len(agent_names) > max_agents:
            raise ValueError(f"Too many agents: {len(agent_names)} > {max_agents}")
        self.agent_names = agent_names
        self.agents = [self._load_agent(n) for n in agent_names]
        self.execution_mode = execution_mode
        self.executor = ThreadPoolExecutor(max_workers=min(max(len(self.agents), 1), 10))

        # Cache settings for use in hot paths (avoids repeated get_settings() calls)
        self._settings = None
        try:
            from config.settings import get_settings as _gs
            self._settings = _gs()
        except Exception:
            pass

        # Per-agent circuit breakers (Feature 8)
        self._circuit_breakers: Dict[str, Any] = {}
        try:
            from core.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
            _failure_threshold = getattr(self._settings, "circuit_breaker_failure_threshold", 3)
            _cb_timeout = getattr(self._settings, "circuit_breaker_timeout_seconds", 60)
            for agent in self.agents:
                name = agent.__class__.__name__
                self._circuit_breakers[name] = CircuitBreaker(
                    name=name,
                    config=CircuitBreakerConfig(
                        failure_threshold=_failure_threshold,
                        timeout_seconds=_cb_timeout,
                    ),
                )
            logger.info("Circuit breakers initialised for %d agents", len(self._circuit_breakers))
        except Exception as _cb_exc:
            logger.debug("Circuit breakers unavailable: %s", _cb_exc)

        # Optional feedback pipeline – publishes OutcomeEvent after each agent run
        self._pipeline = None
        try:
            from config.settings import get_settings as _gs
            from config.kafka_config import kafka_config as _kc
            _settings = _gs()
            if getattr(_settings, "enable_feedback_pipeline", True) and _kc.ENABLE_OUTCOME_LOGGING:
                from core.feedback_pipeline import FeedbackPipeline
                self._pipeline = FeedbackPipeline(
                    kafka_servers=_kc.KAFKA_BOOTSTRAP_SERVERS if _kc.ENABLE_KAFKA else None,
                    kafka_topic=_kc.KAFKA_OUTCOME_TOPIC,
                    enable_kafka=_kc.ENABLE_KAFKA,
                    enable_logging=True,
                )
                logger.info("FeedbackPipeline attached to Orchestrator")
        except Exception as _fp_exc:
            logger.debug("FeedbackPipeline not available: %s", _fp_exc)

    def _emit(
        self,
        agent_name: str,
        status: str,
        start_ts: float,
        end_ts: float,
        output: Any,
        error: Optional[str],
        run_id: str,
    ) -> None:
        """
        Publish an OutcomeEvent to the feedback pipeline (best-effort, never raises).

        Args:
            agent_name: Class name of the agent that executed.
            status: "success" or "error".
            start_ts: ``time.perf_counter()`` value captured before execution.
            end_ts: ``time.perf_counter()`` value captured after execution.
            output: Agent output (may be None on error).
            error: Error message string (or None on success).
            run_id: Orchestrator run identifier for correlation.
        """
        if self._pipeline is None:
            return
        try:
            import uuid as _uuid
            from datetime import datetime
            from core.feedback_pipeline import OutcomeEvent, OutcomeStatus, EventSeverity
            duration_ms = (end_ts - start_ts) * 1000.0
            event = OutcomeEvent(
                event_id=str(_uuid.uuid4()),
                run_id=run_id,
                agent_name=agent_name,
                agent_type=agent_name,
                action_type="orchestrator_run",
                timestamp=datetime.utcnow().isoformat(),
                start_time=str(start_ts),
                end_time=str(end_ts),
                duration_ms=duration_ms,
                latency_ms=duration_ms,
                status=OutcomeStatus.SUCCESS if status == "success" else OutcomeStatus.FAILURE,
                severity=EventSeverity.INFO if status == "success" else EventSeverity.ERROR,
                output={"output": str(output)[:500]} if output is not None else None,
                error_message=error,
                workflow_id=run_id,
            )
            self._pipeline.record_outcome_sync(event)
        except Exception as _exc:
            logger.debug("_emit failed (non-critical): %s", _exc)

    def _load_agent(self, name: str):
        """Load an agent by name."""
        module = import_module(f"agents.{name}")
        agent_class_name = name.title().replace('_', '') + 'Agent'
        return module.Agent() if hasattr(module, 'Agent') else module.__dict__[agent_class_name]()

    def run(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents with the configured execution mode.
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        config = config or {}
        execution_mode = config.get("execution_mode", self.execution_mode)
        
        if execution_mode == "swarm":
            return self.run_swarm(task, config)
        elif execution_mode == "parallel":
            return self.run_parallel(task, config)
        elif execution_mode == "adaptive":
            return self.run_adaptive(task, config)
        else:
            return self.run_sequential(task, config)

    def _maybe_decompose_task(self, task: str, context: Dict[str, Any]) -> str:
        """
        Optionally decompose a complex task using HierarchicalTaskDecomposer.

        Returns the (possibly annotated) task string.  Decomposition is skipped
        when:
        - ``AdvancedFeaturesConfig.ENABLE_HIERARCHICAL_DECOMPOSITION`` is False
        - The task is short / simple (complexity heuristic < 0.6)
        - The decomposer raises any exception (gracefully ignored)
        """
        try:
            from config.advanced_features_config import advanced_features_config as _afc
            if not _afc.ENABLE_HIERARCHICAL_DECOMPOSITION:
                return task
        except Exception:
            return task

        # Simple complexity estimate: word count + multi-step indicators
        words = task.split()
        step_words = ['and', 'then', 'also', 'after', 'before', 'while', 'finally']
        step_count = sum(1 for w in step_words if w.lower() in task.lower())
        complexity = min(1.0, len(words) / 50.0 + step_count * 0.1)
        if complexity < 0.6:
            return task

        try:
            from core.planning.hierarchical_decomposer import TaskDecomposer
            decomposer = TaskDecomposer()
            dag = decomposer.decompose(task)
            subtasks = [t.description for t in dag.tasks.values() if t.depth > 0]
            if subtasks:
                context['subtasks'] = subtasks
                logger.info(
                    "Hierarchical decomposition produced %d subtasks", len(subtasks)
                )
                return f"{task} [Subtasks: {', '.join(subtasks[:4])}]"
        except Exception as exc:
            logger.debug("Hierarchical decomposition skipped: %s", exc)
        return task

    def run_sequential(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents sequentially (original behavior).

        Args:
            task: Task description
            config: Optional configuration

        Returns:
            Execution results
        """
        context = {"task": task, "outputs": [], "state": {}}
        task = self._maybe_decompose_task(task, context)
        context["task"] = task
        config = config or {}
        
        # Pre-flight check with Governor
        gov = next((a for a in self.agents if a.__class__.__name__ == "GovernorAgent"), None)
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}"}

        # Load memory if available
        mem = next((a for a in self.agents if a.__class__.__name__ == "AdaptiveMemoryAgent"), None)
        if mem:
            context["state"]["memory"] = mem.load()
        meta_memory = next((a for a in self.agents if a.__class__.__name__ == "MetaMemoryAgent"), None)
        if meta_memory:
            context["state"]["meta_memory"] = meta_memory

        _run_id = context.get("run_id") or str(id(context))

        # Execute agents sequentially
        for agent in self.agents:
            if hasattr(agent, "skip_in_main") and getattr(agent, "skip_in_main"):
                continue

            _t0 = time.perf_counter()
            try:
                out = self._run_agent_with_timeout(agent, context)
                _t1 = time.perf_counter()
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": out,
                    "status": "success"
                })
                self._emit(agent.__class__.__name__, "success", _t0, _t1, out, None, _run_id)
                if mem:
                    mem.update(context, out)
                if meta_memory:
                    meta_memory.add_memory(
                        content=str(out),
                        tags=["agent_output"],
                        metadata={"agent_name": agent.__class__.__name__, "task": task}
                    )
                    if hasattr(agent, "reflect"):
                        reflection = agent.reflect({"task": task, "status": "success"})
                        meta_memory.add_memory(
                            content=reflection,
                            tags=["reflection"],
                            metadata={"agent_name": agent.__class__.__name__, "task": task}
                        )
            except Exception as e:
                _t1 = time.perf_counter()
                logger.error(f"Agent {agent.__class__.__name__} failed: {e}", exc_info=True)
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": None,
                    "status": "error",
                    "error": str(e)
                })
                self._emit(agent.__class__.__name__, "error", _t0, _t1, None, str(e), _run_id)
                # Continue with other agents unless configured to stop on error
                if config.get("stop_on_error", False):
                    break

        # Post-processing
        evalr = next((a for a in self.agents if a.__class__.__name__ == "EvaluatorAgent"), None)
        if evalr:
            context["evaluation"] = evalr.evaluate(context)
            if meta_memory:
                meta_memory.add_memory(
                    content=f"Evaluation summary: {context['evaluation']}",
                    tags=["evaluation"],
                    metadata={"task": task, "agent_name": "EvaluatorAgent"},
                    evaluation=context["evaluation"]
                )

        meta = next((a for a in self.agents if a.__class__.__name__ == "MetaEvolverAgent"), None)
        if meta:
            meta.evolve(self.agents, context)

        return context

    def run_parallel(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents in parallel where possible.
        
        Groups agents into execution groups:
        - Sequential: Agents that must run in order (based on dependencies)
        - Parallel: Agents that can run simultaneously
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        context = {"task": task, "outputs": [], "state": {}}
        task = self._maybe_decompose_task(task, context)
        context["task"] = task
        config = config or {}

        # Pre-flight check
        gov = next((a for a in self.agents if a.__class__.__name__ == "GovernorAgent"), None)
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}"}

        # Load memory
        mem = next((a for a in self.agents if a.__class__.__name__ == "AdaptiveMemoryAgent"), None)
        if mem:
            context["state"]["memory"] = mem.load()
        meta_memory = next((a for a in self.agents if a.__class__.__name__ == "MetaMemoryAgent"), None)
        if meta_memory:
            context["state"]["meta_memory"] = meta_memory

        # Group agents by execution constraints
        sequential_agents = []
        parallel_agents = []
        
        for agent in self.agents:
            if hasattr(agent, "skip_in_main") and getattr(agent, "skip_in_main"):
                continue
            
            # Check if agent has dependencies or must run sequentially
            if hasattr(agent, "requires_sequential") and getattr(agent, "requires_sequential"):
                sequential_agents.append(agent)
            else:
                parallel_agents.append(agent)
        
        _run_id = context.get("run_id") or str(id(context))

        # Execute sequential agents first
        for agent in sequential_agents:
            _t0 = time.perf_counter()
            try:
                out = self._run_agent_with_timeout(agent, context)
                _t1 = time.perf_counter()
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": out,
                    "status": "success"
                })
                self._emit(agent.__class__.__name__, "success", _t0, _t1, out, None, _run_id)
                if mem:
                    mem.update(context, out)
                if meta_memory:
                    meta_memory.add_memory(
                        content=str(out),
                        tags=["agent_output"],
                        metadata={"agent_name": agent.__class__.__name__, "task": task}
                    )
                    if hasattr(agent, "reflect"):
                        reflection = agent.reflect({"task": task, "status": "success"})
                        meta_memory.add_memory(
                            content=reflection,
                            tags=["reflection"],
                            metadata={"agent_name": agent.__class__.__name__, "task": task}
                        )
            except Exception as e:
                _t1 = time.perf_counter()
                logger.error(f"Agent {agent.__class__.__name__} failed: {e}", exc_info=True)
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": None,
                    "status": "error",
                    "error": str(e)
                })
                self._emit(agent.__class__.__name__, "error", _t0, _t1, None, str(e), _run_id)

        # Execute parallel agents concurrently
        if parallel_agents:
            def run_agent(agent):
                """Run a single agent with timeout + circuit breaker protection."""
                _t0 = time.perf_counter()
                try:
                    agent_context = context.copy()
                    out = self._run_agent_with_timeout(agent, agent_context)
                    _t1 = time.perf_counter()
                    self._emit(agent.__class__.__name__, "success", _t0, _t1, out, None, _run_id)
                    return {
                        "agent": agent.__class__.__name__,
                        "output": out,
                        "status": "success"
                    }
                except Exception as e:
                    _t1 = time.perf_counter()
                    self._emit(agent.__class__.__name__, "error", _t0, _t1, None, str(e), _run_id)
                    logger.error(f"Agent {agent.__class__.__name__} failed: {e}", exc_info=True)
                    return {
                        "agent": agent.__class__.__name__,
                        "output": None,
                        "status": "error",
                        "error": str(e)
                    }

            # Execute in parallel using thread pool
            futures = [self.executor.submit(run_agent, agent) for agent in parallel_agents]
            results = [future.result() for future in futures]
            
            # Update context with results
            for result in results:
                context["outputs"].append(result)
                if mem and result["status"] == "success":
                    mem.update(context, result["output"])
                if meta_memory and result["status"] == "success":
                    meta_memory.add_memory(
                        content=str(result["output"]),
                        tags=["agent_output"],
                        metadata={"agent_name": result["agent"], "task": task}
                    )

        # Post-processing (sequential)
        evalr = next((a for a in self.agents if a.__class__.__name__ == "EvaluatorAgent"), None)
        if evalr:
            context["evaluation"] = evalr.evaluate(context)
            if meta_memory:
                meta_memory.add_memory(
                    content=f"Evaluation summary: {context['evaluation']}",
                    tags=["evaluation"],
                    metadata={"task": task, "agent_name": "EvaluatorAgent"},
                    evaluation=context["evaluation"]
                )

        meta = next((a for a in self.agents if a.__class__.__name__ == "MetaEvolverAgent"), None)
        if meta:
            meta.evolve(self.agents, context)

        return context

    def run_swarm(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Execute task using swarm intelligence.
        
        Uses stigmergic communication and emergent behaviors.
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        try:
            from core.swarm.swarm_orchestrator import SwarmOrchestrator
            
            swarm_orch = SwarmOrchestrator(base_orchestrator=self)
            
            # Register all agents
            for agent in self.agents:
                agent_id = agent.__class__.__name__
                swarm_orch.register_agent(agent_id, agent)
            
            return swarm_orch.execute_swarm(
                task=task,
                max_iterations=config.get("max_iterations", 10) if config else 10,
                use_stigmergy=config.get("use_stigmergy", True) if config else True
            )
        except ImportError:
            logger.warning("Swarm intelligence not available, falling back to adaptive mode")
            return self.run_adaptive(task, config)
        except Exception as e:
            logger.error(f"Swarm execution failed: {e}")
            return {"error": str(e), "fallback": "adaptive", "result": self.run_adaptive(task, config)}
    
    def run_with_causal_awareness(
        self,
        task: str,
        causal_graph: Any,  # CausalGraph from reasoning module
        config: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Execute with causal awareness.
        
        Uses causal graph to route tasks intelligently based on cause-effect relationships.
        
        Args:
            task: Task description
            causal_graph: CausalGraph instance
            config: Optional configuration
            
        Returns:
            Execution results
        """
        try:
            from core.reasoning.causal_reasoner import CausalReasoner
            
            reasoner = CausalReasoner(causal_graph)
            
            # Analyze task to identify key variables
            # Simplified: would use NLP to extract variables
            task_variables = self._extract_variables(task)
            
            # Determine best agent based on causal relationships
            selected_agents = []
            for agent in self.agents:
                agent_capabilities = getattr(agent, 'capabilities', [])
                # Check if agent capabilities match causal requirements
                # Simplified heuristic
                if any(cap.lower() in task.lower() for cap in agent_capabilities):
                    selected_agents.append(agent)
            
            if not selected_agents:
                selected_agents = self.agents  # Fallback to all agents
            
            # Execute with selected agents
            context = {"task": task, "outputs": [], "state": {}}
            config = config or {}
            
            for agent in selected_agents:
                try:
                    result = agent.run(context)
                    context["outputs"].append({
                        "agent": agent.__class__.__name__,
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Agent {agent.__class__.__name__} failed: {e}")
            
            return context
            
        except ImportError:
            logger.warning("Causal reasoning not available, falling back to sequential mode")
            return self.run_sequential(task, config)
        except Exception as e:
            logger.error(f"Causal-aware execution failed: {e}")
            return {"error": str(e), "result": self.run_sequential(task, config)}
    
    def _extract_variables(self, task: str) -> list:
        """Extract variables/concepts from task (simplified)."""
        # Simplified: would use NLP
        words = task.split()
        # Filter for capitalized words or common variable patterns
        variables = [w for w in words if w[0].isupper() and len(w) > 2]
        return variables[:5]  # Return top 5
    
    def _execute_with_timeout(self, agent: Any, context: Dict[str, Any]) -> Any:
        """
        Submit ``agent.run(context)`` to the executor and wait with a timeout.

        Raises:
            TimeoutError: If the agent exceeds ``agent_execution_timeout_seconds``.
        """
        timeout = getattr(self._settings, "agent_execution_timeout_seconds", 30)
        future = self.executor.submit(agent.run, context)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            try:
                from core.monitoring.metrics import agent_timeout_total
                agent_timeout_total.labels(agent_name=agent.__class__.__name__).inc()
            except Exception:
                pass
            raise TimeoutError(
                f"Agent {agent.__class__.__name__} exceeded {timeout}s execution timeout"
            )

    def _run_agent_with_timeout(self, agent: Any, context: Dict[str, Any]) -> Any:
        """
        Execute an agent with timeout (Feature 7), circuit breaker (Feature 8),
        and OpenTelemetry tracing (Feature 9).

        Raises:
            TimeoutError: Agent exceeded the per-call timeout.
            CircuitBreakerOpenError: Agent's circuit is currently open.
        """
        try:
            from core.monitoring.tracing import get_tracer as _get_tracer
            _tracer = _get_tracer("orchestrator")
        except Exception:
            _tracer = None

        agent_name = agent.__class__.__name__
        caps = getattr(type(agent), "CAPABILITIES", None) or getattr(agent, "capabilities", []) or []

        def _protected_call():
            breaker = self._circuit_breakers.get(agent_name)
            if breaker:
                try:
                    return breaker.call(lambda: self._execute_with_timeout(agent, context))
                except Exception as exc:
                    if "CircuitBreakerOpen" in type(exc).__name__:
                        try:
                            from core.monitoring.metrics import circuit_breaker_open_total
                            circuit_breaker_open_total.labels(agent_name=agent_name).inc()
                        except Exception:
                            pass
                    raise
            return self._execute_with_timeout(agent, context)

        if _tracer is not None:
            with _tracer.start_as_current_span(f"agent.{agent_name}") as span:
                span.set_attribute("agent.name", agent_name)
                span.set_attribute("agent.capabilities", str(caps))
                try:
                    result = _protected_call()
                    span.set_attribute("agent.status", "success")
                    return result
                except Exception as exc:
                    span.set_attribute("agent.status", "error")
                    span.set_attribute("agent.error", str(exc))
                    span.record_exception(exc)
                    raise
        else:
            return _protected_call()

    def _agent_has_capability(self, agent: Any, capability: str) -> bool:
        """
        Return True if *agent* has *capability*.

        Checks (in order):
        1. Class-level ``CAPABILITIES`` list (e.g. ``Agent.CAPABILITIES``).
        2. Instance-level ``capabilities`` attribute set by ``BaseAgent.__init__``.
        3. Fallback: substring match on the class name (legacy behaviour).
        """
        caps = getattr(type(agent), "CAPABILITIES", None) or getattr(agent, "CAPABILITIES", None)
        if caps is None:
            caps = getattr(agent, "capabilities", None)
        if caps:
            return capability in caps
        # Fallback: name-keyword heuristic for agents without a CAPABILITIES attribute
        return capability in agent.__class__.__name__.lower()

    def run_adaptive(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents adaptively based on task requirements and agent capabilities.
        
        This mode:
        1. Analyzes the task to determine required capabilities
        2. Selects relevant agents (skips irrelevant ones)
        3. Determines optimal execution order and parallelism
        4. Executes with dynamic routing
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        context = {"task": task, "outputs": [], "state": {}}
        task = self._maybe_decompose_task(task, context)
        context["task"] = task
        config = config or {}

        # Pre-flight check
        gov = next((a for a in self.agents if a.__class__.__name__ == "GovernorAgent"), None)
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}"}

        # Capability-based adaptive agent selection.
        task_lower = task.lower()
        selected_agents = []

        # Determine which capability the task requires
        required_capability: Optional[str] = None
        if any(kw in task_lower for kw in ["reason", "think", "analyze", "solve", "explain"]):
            required_capability = "reasoning"
        elif any(kw in task_lower for kw in ["plan", "schedule", "strateg", "orchestrat"]):
            required_capability = "planning"
        elif any(kw in task_lower for kw in ["generat", "write", "create", "synth"]):
            required_capability = "generation"
        elif any(kw in task_lower for kw in ["search", "lookup", "find", "retriev"]):
            required_capability = "tool_use"

        for agent in self.agents:
            if hasattr(agent, "skip_in_main") and getattr(agent, "skip_in_main"):
                continue

            # Always include support agents (memory, evaluation, safety)
            if any(
                self._agent_has_capability(agent, cap)
                for cap in ("memory", "evaluation", "safety")
            ):
                selected_agents.append(agent)
            elif required_capability and self._agent_has_capability(agent, required_capability):
                selected_agents.append(agent)
            elif required_capability is None:
                # No specific capability inferred — include all task agents
                selected_agents.append(agent)
        
        logger.info(f"Adaptive mode selected {len(selected_agents)} agents for task")
        
        # Execute selected agents (can use parallel execution)
        execution_mode = config.get("adaptive_execution_mode", "parallel")
        if execution_mode == "parallel":
            # Temporarily replace agents list
            original_agents = self.agents
            self.agents = selected_agents
            try:
                result = self.run_parallel(task, config)
            finally:
                self.agents = original_agents
            return result
        else:
            # Sequential execution of selected agents
            original_agents = self.agents
            self.agents = selected_agents
            try:
                result = self.run_sequential(task, config)
            finally:
                self.agents = original_agents
            return result

    def run_streaming(
        self,
        task: str,
        config: Dict[str, Any],
        callback: Callable[[Dict[str, Any]], None],
    ) -> Dict[str, Any]:
        """
        Sequential execution that fires ``callback(result)`` after each agent finishes.

        Used by the ``/run/stream`` SSE endpoint so clients receive incremental results
        in real time rather than waiting for all agents to complete.

        Args:
            task: Task description.
            config: Execution configuration dict.
            callback: Called with each agent's result dict immediately after it finishes.

        Returns:
            Final context dict with all results.
        """
        context = {"task": task, "outputs": [], "state": {}}
        task = self._maybe_decompose_task(task, context)
        context["task"] = task
        config = config or {}

        _run_id = context.get("run_id") or str(id(context))

        for agent in self.agents:
            if getattr(agent, "skip_in_main", False):
                continue

            _t0 = time.perf_counter()
            try:
                out = self._run_agent_with_timeout(agent, context)
                _t1 = time.perf_counter()
                result: Dict[str, Any] = {
                    "agent": agent.__class__.__name__,
                    "status": "success",
                    "output": str(out)[:500] if out is not None else None,
                    "duration_ms": round((_t1 - _t0) * 1000, 2),
                }
                self._emit(agent.__class__.__name__, "success", _t0, _t1, out, None, _run_id)
            except Exception as exc:
                _t1 = time.perf_counter()
                result = {
                    "agent": agent.__class__.__name__,
                    "status": "error",
                    "error": str(exc),
                    "duration_ms": round((_t1 - _t0) * 1000, 2),
                }
                self._emit(agent.__class__.__name__, "error", _t0, _t1, None, str(exc), _run_id)
                logger.error("Agent %s failed in streaming run: %s", agent.__class__.__name__, exc)

            context["outputs"].append(result)
            try:
                callback(result)
            except Exception as _cb_exc:
                logger.debug("Streaming callback error: %s", _cb_exc)

        return {"results": context["outputs"], "mode": "streaming", "task": task}

    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
