
"""
Auto Loop Agent with Budget and Rate Limiting
Safe autonomous agent with built-in cost controls
"""

import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from config.budget_config import (
    check_auto_loop_allowed,
    record_auto_loop_iteration,
    get_budget_limits
)

logger = logging.getLogger(__name__)


class SafeAutoLoopAgent:
    """
    Auto Loop Agent with budget and rate limiting protection.
    Prevents runaway costs by checking limits before each iteration.
    """
    
    def __init__(self, agent_name: str = "auto_loop"):
        self.agent_name = agent_name
        self.iteration_count = 0
        self.total_cost = 0.0
        self.start_time = None
        self.status = "idle"
    
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run auto loop agent with budget protection
        
        Args:
            context: Task context including task description and parameters
            
        Returns:
            Dict with results, status, and usage information
        """
        self.start_time = datetime.now()
        self.status = "running"
        
        try:
            # Check if allowed to run
            check = check_auto_loop_allowed()
            
            if not check['allowed']:
                logger.warning(f"Auto loop agent blocked: {check['reason']}")
                return {
                    "success": False,
                    "error": "Budget limit reached",
                    "reason": check['reason'],
                    "usage_stats": check['usage_stats'],
                    "status": "blocked"
                }
            
            # Get task configuration
            max_iterations = context.get('max_iterations', 10)
            task = context.get('task', 'No task specified')
            
            results = []
            warnings = []
            
            logger.info(f"Starting auto loop agent: {task} (max {max_iterations} iterations)")
            
            # Main loop
            for i in range(max_iterations):
                # Check budget before each iteration
                check = check_auto_loop_allowed()
                
                if not check['allowed']:
                    logger.warning(f"Auto loop stopped at iteration {i}: {check['reason']}")
                    return {
                        "success": False,
                        "error": "Budget limit reached during execution",
                        "reason": check['reason'],
                        "iterations_completed": i,
                        "results": results,
                        "usage_stats": check['usage_stats'],
                        "warnings": warnings,
                        "status": "stopped_by_limit"
                    }
                
                # Check for warnings
                if check['budget_status'].get('warning'):
                    warning_msg = check['budget_status'].get('warning_message')
                    warnings.append(warning_msg)
                    logger.warning(f"Budget warning: {warning_msg}")
                
                # Execute iteration
                iteration_result = await self._execute_iteration(i, task, context)
                results.append(iteration_result)
                
                # Record the iteration
                record_result = record_auto_loop_iteration(self.agent_name)
                if record_result.get('warning'):
                    warnings.append(record_result['message'])
                
                self.iteration_count += 1
                
                # Check if task is complete
                if iteration_result.get('complete', False):
                    logger.info(f"Task completed at iteration {i+1}")
                    break
                
                # Small delay between iterations
                await asyncio.sleep(0.5)
            
            self.status = "completed"
            
            return {
                "success": True,
                "agent": self.agent_name,
                "iterations_completed": self.iteration_count,
                "results": results,
                "warnings": warnings,
                "status": "completed",
                "duration_seconds": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error in auto loop agent: {e}")
            self.status = "failed"
            return {
                "success": False,
                "error": str(e),
                "iterations_completed": self.iteration_count,
                "status": "failed"
            }
    
    async def _execute_iteration(self, iteration: int, task: str, context: Dict) -> Dict:
        """
        Execute a single iteration
        
        Args:
            iteration: Iteration number
            task: Task description
            context: Full context
            
        Returns:
            Iteration result
        """
        # This is where you'd call the actual LLM or other processing
        # For now, we'll simulate with a simple response
        
        logger.info(f"Iteration {iteration + 1}: Processing '{task}'")
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # Simulate completion after a few iterations
        complete = iteration >= 3 and context.get('auto_complete', True)
        
        return {
            "iteration": iteration + 1,
            "task": task,
            "result": f"Processed iteration {iteration + 1}",
            "complete": complete,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "agent": self.agent_name,
            "status": self.status,
            "iteration_count": self.iteration_count,
            "total_cost": self.total_cost,
            "start_time": self.start_time.isoformat() if self.start_time else None
        }


# For backwards compatibility with old import
class Agent:
    """Legacy Agent class for compatibility"""
    
    def __init__(self):
        self.safe_agent = SafeAutoLoopAgent()
    
    async def run(self, context: Dict) -> str:
        """Legacy run method"""
        result = await self.safe_agent.run(context)
        if result['success']:
            return f"Auto loop agent completed: {result['iterations_completed']} iterations"
        else:
            return f"Auto loop agent failed: {result.get('error', 'Unknown error')}"
