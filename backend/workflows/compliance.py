"""
Compliance Intelligence Workflow.

Orchestrates multiple agents to perform comprehensive compliance analysis:
1. ReAct agent - Analyzes the compliance query
2. Debate agent - Generates multiple perspectives
3. Evaluator agent - Assesses the analysis
4. Governor agent - Performs final compliance check
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from database.models import (
    Run, AgentRun, RunStatus, AgentRunStatus, Tenant, Project
)
from database.session import get_db
from agents.react import Agent as ReActAgent
from agents.debate import Agent as DebateAgent
from agents.evaluator import Agent as EvaluatorAgent
from agents.governor import GovernorAgent

logger = logging.getLogger(__name__)


class ComplianceWorkflow:
    """
    Compliance Intelligence Workflow orchestrator.
    
    This workflow coordinates multiple agents to perform comprehensive
    compliance analysis and risk assessment.
    """
    
    def __init__(self, db_session=None):
        """Initialize the workflow with database session."""
        self.db = db_session
        self.agents = {
            "react": ReActAgent(),
            "debate": DebateAgent(),
            "evaluator": EvaluatorAgent(),
            "governor": GovernorAgent()
        }
    
    async def start_workflow(
        self,
        query: str,
        tenant_id: str,
        project_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new compliance workflow.
        
        Args:
            query: The compliance query to analyze
            tenant_id: Tenant ID for multi-tenancy
            project_id: Optional project ID
            config: Optional configuration parameters
            
        Returns:
            Workflow ID (run_id)
        """
        # Create or get project
        if not project_id:
            project_id = await self._get_or_create_default_project(tenant_id)
        
        # Create run record
        run_id = str(uuid.uuid4())
        run = Run(
            id=run_id,
            project_id=project_id,
            status=RunStatus.PENDING,
            config=config or {},
            input_data={"query": query, "type": "compliance"},
            created_at=datetime.utcnow()
        )
        
        if self.db:
            self.db.add(run)
            self.db.commit()
        
        logger.info(f"Started compliance workflow {run_id} for tenant {tenant_id}")
        
        return run_id
    
    async def execute_workflow(
        self,
        run_id: str,
        query: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the compliance workflow.
        
        Args:
            run_id: The workflow run ID
            query: The compliance query
            config: Optional configuration
            
        Returns:
            Workflow results
        """
        try:
            # Update run status to running
            if self.db:
                run = self.db.query(Run).filter(Run.id == run_id).first()
                if run:
                    run.status = RunStatus.RUNNING
                    run.started_at = datetime.utcnow()
                    self.db.commit()
            
            # Initialize context
            context = {
                "task": query,
                "query": query,
                "outputs": [],
                "state": {},
                "run_id": run_id,
                "config": config or {}
            }
            
            # Step 1: Governor preflight check
            logger.info(f"[{run_id}] Step 1: Governor preflight check")
            governor_result = await self._execute_agent(
                run_id, "governor", "preflight", context
            )
            
            if not governor_result.get("allowed", True):
                error_msg = governor_result.get("message", "Content blocked by governor")
                await self._mark_workflow_failed(run_id, error_msg)
                return {
                    "status": "failed",
                    "error": error_msg,
                    "results": None
                }
            
            # Step 2: ReAct agent analysis
            logger.info(f"[{run_id}] Step 2: ReAct agent analysis")
            react_result = await self._execute_agent(
                run_id, "react", "analysis", context
            )
            context["outputs"].append({
                "agent": "react",
                "output": react_result
            })
            context["state"]["react_analysis"] = react_result
            
            # Step 3: Debate agent - multiple perspectives
            logger.info(f"[{run_id}] Step 3: Debate agent - generating perspectives")
            debate_result = await self._execute_agent(
                run_id, "debate", "perspectives", context
            )
            context["outputs"].append({
                "agent": "debate",
                "output": debate_result
            })
            context["state"]["debate_perspectives"] = debate_result
            
            # Step 4: Evaluator agent - assessment
            logger.info(f"[{run_id}] Step 4: Evaluator agent - assessment")
            evaluator_result = await self._execute_agent(
                run_id, "evaluator", "evaluation", context
            )
            context["outputs"].append({
                "agent": "evaluator",
                "output": evaluator_result
            })
            context["state"]["evaluation"] = evaluator_result
            
            # Step 5: Generate compliance report
            logger.info(f"[{run_id}] Step 5: Generating compliance report")
            compliance_report = self._generate_compliance_report(context)
            
            # Update run with results
            if self.db:
                run = self.db.query(Run).filter(Run.id == run_id).first()
                if run:
                    run.status = RunStatus.COMPLETED
                    run.completed_at = datetime.utcnow()
                    run.output_data = compliance_report
                    self.db.commit()
            
            logger.info(f"[{run_id}] Compliance workflow completed successfully")
            
            return {
                "status": "completed",
                "results": compliance_report
            }
            
        except Exception as e:
            logger.error(f"[{run_id}] Workflow execution failed: {str(e)}")
            await self._mark_workflow_failed(run_id, str(e))
            return {
                "status": "failed",
                "error": str(e),
                "results": None
            }
    
    async def _execute_agent(
        self,
        run_id: str,
        agent_name: str,
        step_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single agent and record its execution.
        
        Args:
            run_id: Workflow run ID
            agent_name: Name of the agent to execute
            step_name: Name of the step
            context: Execution context
            
        Returns:
            Agent output
        """
        agent_run_id = str(uuid.uuid4())
        agent = self.agents.get(agent_name)
        
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")
        
        # Create agent run record
        agent_run = AgentRun(
            id=agent_run_id,
            run_id=run_id,
            agent_name=agent_name,
            agent_type=agent.__class__.__name__,
            status=AgentRunStatus.RUNNING,
            input_data={"context": context.get("task", "")},
            started_at=datetime.utcnow()
        )
        
        if self.db:
            self.db.add(agent_run)
            self.db.commit()
        
        try:
            # Execute agent
            start_time = datetime.utcnow()
            
            if agent_name == "governor":
                ok, msg = agent.preflight(context.get("task", ""))
                output = {"allowed": ok, "message": msg}
            else:
                output = agent.run(context)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Update agent run record
            if self.db:
                agent_run.status = AgentRunStatus.COMPLETED
                agent_run.completed_at = end_time
                agent_run.output_data = {"output": output}
                agent_run.metrics = {"duration_seconds": duration}
                self.db.commit()
            
            return output
            
        except Exception as e:
            logger.error(f"Agent {agent_name} execution failed: {str(e)}")
            
            if self.db:
                agent_run.status = AgentRunStatus.FAILED
                agent_run.error_message = str(e)
                agent_run.completed_at = datetime.utcnow()
                self.db.commit()
            
            raise
    
    def _generate_compliance_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report from agent outputs.
        
        Args:
            context: Workflow context with agent outputs
            
        Returns:
            Compliance report
        """
        react_analysis = context["state"].get("react_analysis", "")
        debate_perspectives = context["state"].get("debate_perspectives", "")
        evaluation = context["state"].get("evaluation", {})
        
        # Extract evaluation score
        eval_score = 0.0
        if isinstance(evaluation, dict):
            eval_score = evaluation.get("score", 0) / 10.0  # Normalize to 0-1
        
        # Determine risk level based on evaluation
        if eval_score >= 0.8:
            risk_level = "low"
        elif eval_score >= 0.5:
            risk_level = "medium"
        elif eval_score >= 0.3:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # Build compliance report
        report = {
            "analysis": {
                "summary": f"Compliance analysis completed for query: {context.get('query', '')}",
                "obligations": [
                    "Data protection and privacy requirements",
                    "Record retention policies",
                    "User consent management",
                    "Data breach notification procedures"
                ],
                "gaps": [
                    "Missing documentation for data processing activities",
                    "Incomplete user consent tracking",
                    "Insufficient data retention schedules"
                ],
                "perspectives": [
                    {
                        "viewpoint": "Legal Compliance",
                        "analysis": str(react_analysis)
                    },
                    {
                        "viewpoint": "Risk Management",
                        "analysis": str(debate_perspectives)
                    }
                ],
                "evaluation_score": eval_score
            },
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": 1.0 - eval_score,  # Inverse of evaluation score
                "findings": [
                    f"ReAct Analysis: {react_analysis}",
                    f"Debate Perspectives: {debate_perspectives}",
                    f"Evaluation Score: {eval_score}"
                ],
                "recommendations": [
                    "Implement comprehensive data mapping",
                    "Establish clear data retention policies",
                    "Deploy automated consent management system",
                    "Create incident response procedures",
                    "Conduct regular compliance audits"
                ],
                "affected_regulations": [
                    "GDPR (General Data Protection Regulation)",
                    "CCPA (California Consumer Privacy Act)",
                    "HIPAA (if applicable)",
                    "SOC 2 Type II"
                ]
            },
            "compliance_report": self._format_markdown_report(
                context.get("query", ""),
                react_analysis,
                debate_perspectives,
                evaluation,
                risk_level,
                eval_score
            )
        }
        
        return report
    
    def _format_markdown_report(
        self,
        query: str,
        react_analysis: str,
        debate_perspectives: str,
        evaluation: Any,
        risk_level: str,
        eval_score: float
    ) -> str:
        """Format a markdown compliance report."""
        
        report = f"""# Compliance Intelligence Report

## Executive Summary

**Query:** {query}

**Risk Level:** {risk_level.upper()}

**Evaluation Score:** {eval_score:.2f}/1.00

---

## Analysis

### ReAct Agent Analysis
{react_analysis}

### Debate Agent Perspectives
{debate_perspectives}

### Evaluator Assessment
Evaluation Score: {evaluation}

---

## Risk Assessment

**Overall Risk Level:** {risk_level.upper()}

**Risk Score:** {1.0 - eval_score:.2f}

### Key Findings
- Comprehensive multi-agent analysis completed
- Multiple perspectives considered
- Evaluation metrics calculated

### Recommendations
1. Implement comprehensive data mapping
2. Establish clear data retention policies
3. Deploy automated consent management system
4. Create incident response procedures
5. Conduct regular compliance audits

### Affected Regulations
- GDPR (General Data Protection Regulation)
- CCPA (California Consumer Privacy Act)
- HIPAA (if applicable)
- SOC 2 Type II

---

## Next Steps

1. Review and prioritize recommendations
2. Assign ownership for each action item
3. Establish timeline for implementation
4. Schedule follow-up compliance review

---

*Report generated by Powerhouse Multi-Agent Platform*
*Timestamp: {datetime.utcnow().isoformat()}Z*
"""
        
        return report
    
    async def _get_or_create_default_project(self, tenant_id: str) -> str:
        """Get or create default project for tenant."""
        if not self.db:
            return "default-project"
        
        # Check if tenant exists
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            tenant = Tenant(id=tenant_id, name=f"Tenant {tenant_id}")
            self.db.add(tenant)
            self.db.commit()
        
        # Check if default project exists
        project = self.db.query(Project).filter(
            Project.tenant_id == tenant_id,
            Project.name == "Default Project"
        ).first()
        
        if not project:
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                tenant_id=tenant_id,
                name="Default Project",
                description="Default project for compliance workflows"
            )
            self.db.add(project)
            self.db.commit()
        
        return project.id
    
    async def _mark_workflow_failed(self, run_id: str, error_message: str):
        """Mark workflow as failed."""
        if self.db:
            run = self.db.query(Run).filter(Run.id == run_id).first()
            if run:
                run.status = RunStatus.FAILED
                run.error_message = error_message
                run.completed_at = datetime.utcnow()
                self.db.commit()
    
    async def get_workflow_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow status and progress.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            Workflow status information
        """
        if not self.db:
            return None
        
        run = self.db.query(Run).filter(Run.id == run_id).first()
        if not run:
            return None
        
        # Get agent runs
        agent_runs = self.db.query(AgentRun).filter(
            AgentRun.run_id == run_id
        ).order_by(AgentRun.created_at).all()
        
        # Calculate progress
        total_agents = 4  # react, debate, evaluator, governor
        completed_agents = sum(1 for ar in agent_runs if ar.status == AgentRunStatus.COMPLETED)
        progress = (completed_agents / total_agents) * 100 if total_agents > 0 else 0
        
        # Get current agent
        current_agent = None
        for ar in agent_runs:
            if ar.status == AgentRunStatus.RUNNING:
                current_agent = ar.agent_name
                break
        
        # Calculate duration
        duration = None
        if run.started_at:
            end_time = run.completed_at or datetime.utcnow()
            duration = (end_time - run.started_at).total_seconds()
        
        return {
            "workflow_id": run.id,
            "status": run.status.value,
            "progress_percentage": progress,
            "current_agent": current_agent,
            "created_at": run.created_at,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "duration_seconds": duration,
            "agent_count": len(agent_runs),
            "completed_agent_count": completed_agents
        }
    
    async def get_workflow_results(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow results.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            Workflow results
        """
        if not self.db:
            return None
        
        run = self.db.query(Run).filter(Run.id == run_id).first()
        if not run:
            return None
        
        # Calculate duration
        duration = None
        if run.started_at and run.completed_at:
            duration = (run.completed_at - run.started_at).total_seconds()
        
        return {
            "workflow_id": run.id,
            "status": run.status.value,
            "results": run.output_data,
            "created_at": run.created_at,
            "completed_at": run.completed_at,
            "duration_seconds": duration
        }
