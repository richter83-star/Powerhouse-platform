"""
Main entry point for the Powerhouse B2B Platform backend.
"""

import uuid
from typing import Optional

from core import Orchestrator
from database import init_db, get_session, Tenant, Project
from config import get_settings
from utils import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def initialize_database():
    """Initialize database with tables."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


def create_demo_tenant_and_project() -> tuple[str, str]:
    """
    Create a demo tenant and project for testing.
    
    Returns:
        tuple: (tenant_id, project_id)
    """
    db = get_session()
    try:
        # Check if demo tenant exists
        tenant = db.query(Tenant).filter(Tenant.name == "Demo Tenant").first()
        
        if not tenant:
            tenant_id = str(uuid.uuid4())
            tenant = Tenant(
                id=tenant_id,
                name="Demo Tenant",
                metadata={"type": "demo"}
            )
            db.add(tenant)
            db.commit()
            logger.info(f"Created demo tenant: {tenant_id}")
        else:
            tenant_id = tenant.id
            logger.info(f"Using existing demo tenant: {tenant_id}")
        
        # Check if demo project exists
        project = db.query(Project).filter(
            Project.tenant_id == tenant_id,
            Project.name == "Demo Project"
        ).first()
        
        if not project:
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                tenant_id=tenant_id,
                name="Demo Project",
                description="Demo project for testing the platform",
                metadata={"type": "demo"}
            )
            db.add(project)
            db.commit()
            logger.info(f"Created demo project: {project_id}")
        else:
            project_id = project.id
            logger.info(f"Using existing demo project: {project_id}")
        
        return tenant_id, project_id
        
    finally:
        db.close()


def run_demo():
    """Run a demo execution of the platform."""
    settings = get_settings()
    
    logger.info("=" * 80)
    logger.info("Powerhouse B2B Multi-Agent Platform - Demo")
    logger.info("=" * 80)
    
    # Initialize database
    initialize_database()
    
    # Create demo tenant and project
    tenant_id, project_id = create_demo_tenant_and_project()
    
    # Create orchestrator with subset of agents
    logger.info("\nInitializing orchestrator with agents...")
    orchestrator = Orchestrator(
        agent_types=["react", "evaluator"]  # Just 2 agents for demo
    )
    
    # Display loaded agents
    logger.info(f"\nLoaded agents: {[a.name for a in orchestrator.agents]}")
    
    # Run a demo task
    task = "Analyze the benefits of multi-agent systems for enterprise applications"
    logger.info(f"\nExecuting task: {task}")
    
    try:
        results = orchestrator.run(
            task=task,
            project_id=project_id,
            execution_strategy="sequential"
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)
        logger.info(f"Run ID: {results['run_id']}")
        logger.info(f"Task: {results['task']}")
        logger.info(f"\nAgent Outputs:")
        
        for output in results.get("agent_outputs", []):
            agent_name = output.get("agent", "unknown")
            logger.info(f"\n  {agent_name}:")
            if "output" in output:
                logger.info(f"    Status: {output['output'].get('status', 'unknown')}")
                logger.info(f"    Output: {output['output'].get('output', 'N/A')}")
            elif "error" in output:
                logger.info(f"    Error: {output['error']}")
        
        # Display communication stats
        stats = orchestrator.get_stats()
        logger.info("\n" + "=" * 80)
        logger.info("COMMUNICATION STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total agents: {stats['total_agents']}")
        logger.info(f"Message bus stats: {stats['communication']['message_bus']}")
        logger.info(f"Agent registry stats: {stats['communication']['agent_registry']}")
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}", exc_info=True)
    
    finally:
        # Cleanup
        orchestrator.shutdown()
        logger.info("\nDemo completed")


if __name__ == "__main__":
    run_demo()
