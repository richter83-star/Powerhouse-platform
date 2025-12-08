"""
Exponential Learning API Routes

REST API endpoints for the exponential learning system.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import threading
import logging

from core.agent_learning_coordinator import AgentLearningCoordinator
from core.adaptive_orchestrator import AdaptiveOrchestrator
from core.goal_driven_agent import GoalDrivenAgent
from core.forecasting_engine import ForecastingEngine
from core.dynamic_config_manager import get_config_manager
from core.learning_data_plugins import (
    LearningDataOrchestrator,
    CustomerSupportDataPlugin,
    SalesResearchDataPlugin,
    BenchmarkDatasetPlugin
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/learning", tags=["exponential_learning"])

# Global state
_coordinator: Optional[AgentLearningCoordinator] = None
_learning_thread: Optional[threading.Thread] = None
_learning_active = False
_last_report: Optional[Dict[str, Any]] = None


# Request/Response Models
class DeployRequest(BaseModel):
    enable_forecasting: bool = True
    enable_dynamic_config: bool = True
    agents: List[str] = ["react", "planning", "evaluator"]


class StartLearningRequest(BaseModel):
    iterations: int = 100
    batch_size: int = 10
    report_every: int = 10
    async_mode: bool = True


class GenerateTasksRequest(BaseModel):
    plugin: Optional[str] = None
    count: int = 5


@router.post('/deploy')
async def deploy_learning_system(request: DeployRequest):
    """Deploy the exponential learning system."""
    global _coordinator
    
    try:
        # Initialize orchestrator
        orchestrator = AdaptiveOrchestrator(
            agent_names=request.agents,
            enable_adaptation=True
        )
        
        # Initialize goal-driven agent
        goal_agent = GoalDrivenAgent(
            agent_config={"autonomous_mode": True, "continuous_operation": False}
        )
        
        # Initialize forecasting (optional)
        forecasting = None
        if request.enable_forecasting:
            forecasting = ForecastingEngine()
        
        # Initialize config manager (optional)
        config_manager = None
        if request.enable_dynamic_config:
            config_manager = get_config_manager()
        
        # Initialize learning data plugins
        learning_data = LearningDataOrchestrator()
        learning_data.register_plugin(CustomerSupportDataPlugin())
        learning_data.register_plugin(SalesResearchDataPlugin())
        learning_data.register_plugin(BenchmarkDatasetPlugin())
        
        # Create coordinator
        _coordinator = AgentLearningCoordinator(
            orchestrator=orchestrator,
            goal_driven_agent=goal_agent,
            learning_data_orchestrator=learning_data,
            config_manager=config_manager,
            forecasting_engine=forecasting
        )
        
        return {
            'status': 'success',
            'message': 'Exponential learning system deployed',
            'components': {
                'agents': len(orchestrator.agents),
                'plugins': len(learning_data.list_plugins()),
                'forecasting': request.enable_forecasting,
                'dynamic_config': request.enable_dynamic_config
            }
        }
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/start')
async def start_learning(request: StartLearningRequest, background_tasks: BackgroundTasks):
    """Start the exponential learning loop."""
    global _coordinator, _learning_thread, _learning_active, _last_report
    
    if not _coordinator:
        raise HTTPException(status_code=400, detail='System not deployed. Call /deploy first.')
    
    if _learning_active:
        raise HTTPException(status_code=400, detail='Learning already in progress')
    
    try:
        if request.async_mode:
            # Run in background
            def run_learning():
                global _learning_active, _last_report
                _learning_active = True
                try:
                    report = _coordinator.start_exponential_learning_loop(
                        iterations=request.iterations,
                        batch_size=request.batch_size,
                        report_every=request.report_every
                    )
                    _last_report = report
                finally:
                    _learning_active = False
            
            background_tasks.add_task(run_learning)
            
            return {
                'status': 'success',
                'message': 'Learning started in background',
                'config': {
                    'iterations': request.iterations,
                    'batch_size': request.batch_size,
                    'report_every': request.report_every
                }
            }
        else:
            # Run synchronously
            _learning_active = True
            try:
                report = _coordinator.start_exponential_learning_loop(
                    iterations=request.iterations,
                    batch_size=request.batch_size,
                    report_every=request.report_every
                )
                _last_report = report
                
                return {
                    'status': 'success',
                    'message': 'Learning completed',
                    'report': report
                }
            finally:
                _learning_active = False
        
    except Exception as e:
        _learning_active = False
        logger.error(f"Learning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/status')
async def get_status():
    """Get current learning system status."""
    global _coordinator, _learning_active
    
    if not _coordinator:
        return {
            'status': 'not_deployed',
            'message': 'System not deployed'
        }
    
    stats = _coordinator.get_current_stats()
    
    return {
        'status': 'active' if _learning_active else 'idle',
        'deployed': True,
        'learning_active': _learning_active,
        'statistics': stats
    }


@router.get('/stats')
async def get_stats():
    """Get detailed learning statistics."""
    global _coordinator
    
    if not _coordinator:
        raise HTTPException(status_code=400, detail='System not deployed')
    
    stats = _coordinator.get_current_stats()
    plugin_stats = _coordinator.learning_data.get_stats()
    
    return {
        'status': 'success',
        'learning_stats': stats,
        'plugin_stats': plugin_stats
    }


@router.get('/report')
async def get_report():
    """Get the last learning report."""
    global _last_report
    
    if not _last_report:
        raise HTTPException(status_code=404, detail='No learning report available')
    
    return {
        'status': 'success',
        'report': _last_report
    }


@router.get('/plugins/list')
async def list_plugins():
    """List available learning data plugins."""
    global _coordinator
    
    if not _coordinator:
        raise HTTPException(status_code=400, detail='System not deployed')
    
    plugins = _coordinator.learning_data.list_plugins()
    
    return {
        'status': 'success',
        'plugins': plugins,
        'count': len(plugins)
    }


@router.post('/plugins/generate')
async def generate_tasks(request: GenerateTasksRequest):
    """Generate training tasks from plugins."""
    global _coordinator
    
    if not _coordinator:
        raise HTTPException(status_code=400, detail='System not deployed')
    
    try:
        if request.plugin:
            tasks = _coordinator.learning_data.generate_training_batch(
                batch_size=request.count,
                agent_type=request.plugin
            )
        else:
            tasks = []
            for i in range(request.count):
                task = _coordinator.learning_data.generate_task()
                tasks.append(task)
        
        return {
            'status': 'success',
            'tasks': tasks,
            'count': len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Task generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/stop')
async def stop_learning():
    """Stop the learning loop."""
    global _learning_active
    
    if not _learning_active:
        raise HTTPException(status_code=400, detail='No learning in progress')
    
    _learning_active = False
    
    return {
        'status': 'success',
        'message': 'Stop signal sent (will complete current iteration)'
    }
