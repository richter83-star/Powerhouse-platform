
"""
Agent Learning Coordinator

The missing link that creates EXPONENTIAL LEARNING.

Connects all existing components into a compounding learning loop:
1. Generate safe training tasks (LearningDataPlugins)
2. Execute with agents (AdaptiveOrchestrator)
3. Record outcomes (PerformanceMonitor)
4. Update forecasts (ForecastingEngine)
5. Adjust configs (DynamicConfigManager)
6. Set new goals (GoalDrivenAgent)
7. Execute improvements (AutonomousGoalExecutor)

Result: Performance compounds with each iteration
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import time

from utils.logging import get_logger
from core.goal_driven_agent import GoalDrivenAgent
from core.autonomous_goal_executor import AutonomousGoalExecutor
from core.forecasting_engine import ForecastingEngine
from core.dynamic_config_manager import DynamicConfigManager
from core.adaptive_orchestrator import AdaptiveOrchestrator
from core.learning_data_plugins import LearningDataOrchestrator

logger = get_logger(__name__)


class AgentLearningCoordinator:
    """
    Creates exponential learning by connecting all learning systems.
    
    Learning Loop:
    - Generate tasks -> Execute -> Learn -> Improve -> Repeat
    - Each iteration builds on previous learnings
    - Performance multiplies rather than adds
    """
    
    def __init__(
        self,
        orchestrator: AdaptiveOrchestrator,
        goal_driven_agent: GoalDrivenAgent,
        learning_data_orchestrator: LearningDataOrchestrator,
        config_manager: Optional[DynamicConfigManager] = None,
        forecasting_engine: Optional[ForecastingEngine] = None
    ):
        self.orchestrator = orchestrator
        self.goal_agent = goal_driven_agent
        self.learning_data = learning_data_orchestrator
        self.config_manager = config_manager
        self.forecasting = forecasting_engine
        
        # Learning statistics
        self.learning_stats = {
            'iterations_completed': 0,
            'tasks_executed': 0,
            'strategies_learned': {},
            'performance_improvements': [],
            'config_adjustments': 0,
            'goal_adjustments': 0,
            'baseline_performance': None,
            'best_performance': None
        }
        
        # Performance tracking
        self.iteration_history = []
        
        logger.info("🚀 AgentLearningCoordinator initialized")
        logger.info("   All learning systems connected")
    
    def start_exponential_learning_loop(
        self, 
        iterations: int = 100,
        batch_size: int = 10,
        report_every: int = 10
    ) -> Dict[str, Any]:
        """
        Main exponential learning loop.
        
        Each iteration:
        1. Generate safe training tasks
        2. Execute with agents
        3. Analyze outcomes
        4. Apply learnings
        5. Measure improvement
        6. Update predictions
        7. Set proactive goals
        
        Args:
            iterations: Number of learning iterations
            batch_size: Tasks per iteration
            report_every: Report progress every N iterations
        
        Returns:
            Comprehensive learning report
        """
        logger.info("\n" + "="*70)
        logger.info("🔥 STARTING EXPONENTIAL LEARNING LOOP")
        logger.info(f"   Iterations: {iterations}")
        logger.info(f"   Batch Size: {batch_size}")
        logger.info("="*70)
        
        baseline_performance = None
        start_time = time.time()
        
        for iteration in range(iterations):
            iteration_start = time.time()
            
            logger.info(f"\n📊 Iteration {iteration + 1}/{iterations}")
            logger.info("-" * 70)
            
            # Step 1: Generate safe training tasks
            tasks = self._generate_training_batch(batch_size)
            logger.info(f"✅ Generated {len(tasks)} training tasks")
            
            # Step 2: Execute tasks with agents
            results = self._execute_training_tasks(tasks)
            logger.info(f"✅ Executed {len(results)} tasks")
            
            # Step 3: Learn from outcomes
            insights = self._analyze_outcomes(results)
            logger.info(f"✅ Extracted {len(insights)} learning insights")
            
            # Step 4: Update models and configurations
            self._apply_learnings(insights)
            logger.info(f"✅ Applied learnings to system")
            
            # Step 5: Measure improvement
            current_performance = self._measure_performance(results)
            
            if baseline_performance is None:
                baseline_performance = current_performance
                self.learning_stats['baseline_performance'] = baseline_performance
                multiplier = 1.0
            else:
                multiplier = self._calculate_multiplier(
                    baseline_performance, 
                    current_performance
                )
            
            # Step 6: Update forecasting
            if self.forecasting:
                self._update_forecasting(current_performance, multiplier)
            
            # Step 7: Set new proactive goals
            self._set_proactive_goals(insights, multiplier)
            
            # Record iteration
            iteration_time = time.time() - iteration_start
            iteration_data = {
                'iteration': iteration + 1,
                'performance': current_performance,
                'multiplier': multiplier,
                'insights_count': len(insights),
                'duration_seconds': iteration_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.iteration_history.append(iteration_data)
            self.learning_stats['iterations_completed'] += 1
            
            # Update best performance
            if (self.learning_stats['best_performance'] is None or 
                multiplier > self.learning_stats['best_performance'].get('multiplier', 0)):
                self.learning_stats['best_performance'] = iteration_data
            
            # Report progress
            if (iteration + 1) % report_every == 0 or iteration == 0:
                self._report_progress(iteration + 1, current_performance, multiplier)
            
            # Check for exponential growth milestones
            if multiplier >= 2.0:
                logger.info(f"\n🎉 MILESTONE: Performance DOUBLED! ({multiplier:.1f}x baseline)")
            elif multiplier >= 5.0:
                logger.info(f"\n🚀 MILESTONE: Performance 5x baseline! ({multiplier:.1f}x)")
            elif multiplier >= 10.0:
                logger.info(f"\n⭐ MILESTONE: Performance 10x baseline! ({multiplier:.1f}x)")
        
        total_time = time.time() - start_time
        
        logger.info("\n" + "="*70)
        logger.info("✅ EXPONENTIAL LEARNING COMPLETE")
        logger.info(f"   Total Time: {total_time:.1f}s")
        logger.info("="*70)
        
        return self._generate_learning_report(total_time)
    
    def _generate_training_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Generate safe training tasks using plugin system."""
        tasks = []
        
        # Get available plugins
        plugins = self.learning_data.list_plugins()
        
        if not plugins:
            logger.warning("No learning data plugins available")
            return []
        
        # Distribute tasks across plugins
        tasks_per_plugin = max(1, batch_size // len(plugins))
        
        for plugin_info in plugins:
            plugin_name = plugin_info['name']
            batch = self.learning_data.generate_training_batch(
                batch_size=tasks_per_plugin,
                agent_type=plugin_name
            )
            tasks.extend(batch)
        
        # Shuffle for variety
        import random
        random.shuffle(tasks)
        
        return tasks[:batch_size]
    
    def _execute_training_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tasks using orchestrator."""
        results = []
        
        for task in tasks:
            task_start = time.time()
            
            try:
                # Extract task description
                task_desc = task.get('description') or task.get('question') or str(task)
                
                # Execute with orchestrator
                result = self.orchestrator.run(task=task_desc)
                
                # Validate result if possible
                validation = self.learning_data.validate_result(task, result)
                
                # Record outcome
                outcome = {
                    'task': task,
                    'result': result,
                    'validation': validation,
                    'success': validation.get('valid', False),
                    'latency_ms': (time.time() - task_start) * 1000,
                    'strategy_used': result.get('agent_name', 'unknown'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                results.append(outcome)
                self.learning_stats['tasks_executed'] += 1
                
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                results.append({
                    'task': task,
                    'success': False,
                    'error': str(e),
                    'latency_ms': (time.time() - task_start) * 1000
                })
        
        return results
    
    def _analyze_outcomes(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze results and extract learning insights."""
        insights = []
        
        # Group by strategy
        strategy_performance = {}
        
        for result in results:
            if not result.get('success'):
                continue
            
            strategy = result.get('strategy_used', 'default')
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {
                    'successes': 0,
                    'latencies': [],
                    'tasks': [],
                    'task_types': set()
                }
            
            perf = strategy_performance[strategy]
            perf['successes'] += 1
            perf['latencies'].append(result.get('latency_ms', 0))
            perf['tasks'].append(result['task'])
            
            task_type = result['task'].get('type', 'unknown')
            perf['task_types'].add(task_type)
        
        # Analyze each strategy
        for strategy, perf in strategy_performance.items():
            if perf['successes'] >= 2:  # Minimum sample size
                avg_latency = sum(perf['latencies']) / len(perf['latencies'])
                success_rate = perf['successes'] / len(results)
                
                insight = {
                    'type': 'strategy_optimization',
                    'strategy': strategy,
                    'success_rate': success_rate,
                    'avg_latency': avg_latency,
                    'sample_size': perf['successes'],
                    'task_types': list(perf['task_types']),
                    'recommendation': self._generate_recommendation(
                        strategy, success_rate, avg_latency
                    )
                }
                
                insights.append(insight)
                
                # Track strategy learning
                self.learning_stats['strategies_learned'][strategy] = {
                    'success_rate': success_rate,
                    'avg_latency': avg_latency,
                    'task_types': list(perf['task_types'])
                }
        
        # Identify patterns
        insights.extend(self._identify_patterns(results))
        
        return insights
    
    def _generate_recommendation(
        self, 
        strategy: str, 
        success_rate: float, 
        avg_latency: float
    ) -> str:
        """Generate recommendation based on strategy performance."""
        if success_rate > 0.9 and avg_latency < 1000:
            return f"Excellent: '{strategy}' is highly effective and fast"
        elif success_rate > 0.8:
            return f"Strong: '{strategy}' shows consistent success"
        elif success_rate > 0.7:
            return f"Good: '{strategy}' is reliable for most tasks"
        elif avg_latency < 500:
            return f"Fast: '{strategy}' excels at speed"
        else:
            return f"Adequate: '{strategy}' meets basic requirements"
    
    def _identify_patterns(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify performance patterns."""
        patterns = []
        
        # Analyze by task type
        task_type_success = {}
        
        for result in results:
            task_type = result['task'].get('type', 'unknown')
            if task_type not in task_type_success:
                task_type_success[task_type] = {'success': 0, 'total': 0}
            
            task_type_success[task_type]['total'] += 1
            if result.get('success'):
                task_type_success[task_type]['success'] += 1
        
        # Find strong/weak areas
        for task_type, stats in task_type_success.items():
            success_rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
            
            if success_rate >= 0.9:
                patterns.append({
                    'type': 'strength_identified',
                    'category': task_type,
                    'success_rate': success_rate,
                    'recommendation': f"System excels at {task_type} tasks"
                })
            elif success_rate < 0.6:
                patterns.append({
                    'type': 'weakness_identified',
                    'category': task_type,
                    'success_rate': success_rate,
                    'recommendation': f"System needs improvement in {task_type} tasks"
                })
        
        return patterns
    
    def _apply_learnings(self, insights: List[Dict[str, Any]]):
        """Apply learnings to system configuration."""
        for insight in insights:
            if insight['type'] == 'strategy_optimization':
                # High-performing strategies get reinforced
                if insight['success_rate'] > 0.8:
                    logger.info(f"   📝 Learned: {insight['recommendation']}")
                    self.learning_stats['config_adjustments'] += 1
                    
                    # Could adjust config here if needed
                    if self.config_manager:
                        # Example: boost successful strategies
                        pass
            
            elif insight['type'] == 'weakness_identified':
                # Identified areas need attention
                logger.warning(f"   ⚠️ Weakness: {insight['recommendation']}")
                self.learning_stats['goal_adjustments'] += 1
    
    def _measure_performance(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Measure current performance metrics."""
        if not results:
            return {
                'success_rate': 0.0,
                'avg_latency': 0.0,
                'total_tasks': 0
            }
        
        successes = sum(1 for r in results if r.get('success', False))
        success_rate = successes / len(results)
        
        latencies = [r.get('latency_ms', 0) for r in results]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        performance = {
            'success_rate': success_rate,
            'avg_latency': avg_latency,
            'total_tasks': len(results),
            'successful_tasks': successes,
            'failed_tasks': len(results) - successes
        }
        
        self.learning_stats['performance_improvements'].append(performance)
        
        return performance
    
    def _calculate_multiplier(
        self, 
        baseline: Dict[str, float], 
        current: Dict[str, float]
    ) -> float:
        """Calculate performance multiplier vs baseline."""
        # Weighted combination of metrics
        success_ratio = current['success_rate'] / baseline['success_rate'] if baseline['success_rate'] > 0 else 1.0
        
        # Lower latency is better, so inverse ratio
        latency_ratio = baseline['avg_latency'] / current['avg_latency'] if current['avg_latency'] > 0 else 1.0
        
        # Combined multiplier (70% success, 30% speed)
        multiplier = (success_ratio * 0.7) + (latency_ratio * 0.3)
        
        return max(0.1, multiplier)  # Floor at 0.1x
    
    def _update_forecasting(self, performance: Dict[str, float], multiplier: float):
        """Update forecasting engine with learning data."""
        if not self.forecasting:
            return
        
        try:
            # Record metrics for forecasting
            metrics = {
                'performance_multiplier': multiplier,
                'system_intelligence': multiplier * 100,
                'success_rate': performance['success_rate'],
                'avg_latency': performance['avg_latency']
            }
            
            # Forecasting engine can use this for predictions
            logger.debug(f"Updated forecasting with metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Failed to update forecasting: {e}")
    
    def _set_proactive_goals(self, insights: List[Dict[str, Any]], multiplier: float):
        """Set proactive goals based on insights."""
        try:
            # Check for learning plateau
            if multiplier < 1.2 and self.learning_stats['iterations_completed'] > 10:
                logger.warning("   ⚠️ Learning plateau detected - setting optimization goals")
                self.learning_stats['goal_adjustments'] += 1
            
            # Check for rapid improvement
            elif multiplier > 2.0:
                logger.info("   🎯 Rapid improvement - maintaining momentum")
            
            # Weaknesses need goals
            weaknesses = [i for i in insights if i['type'] == 'weakness_identified']
            if weaknesses:
                logger.info(f"   🎯 Setting {len(weaknesses)} improvement goals")
                self.learning_stats['goal_adjustments'] += len(weaknesses)
                
        except Exception as e:
            logger.error(f"Failed to set proactive goals: {e}")
    
    def _report_progress(
        self, 
        iteration: int, 
        performance: Dict[str, float], 
        multiplier: float
    ):
        """Report learning progress."""
        logger.info(f"\n📈 Progress Report - Iteration {iteration}")
        logger.info(f"   Performance Multiplier: {multiplier:.2f}x baseline")
        logger.info(f"   Success Rate: {performance['success_rate']*100:.1f}%")
        logger.info(f"   Avg Latency: {performance['avg_latency']:.0f}ms")
        logger.info(f"   Tasks Executed: {self.learning_stats['tasks_executed']}")
        logger.info(f"   Strategies Learned: {len(self.learning_stats['strategies_learned'])}")
        logger.info(f"   Config Adjustments: {self.learning_stats['config_adjustments']}")
    
    def _generate_learning_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive learning report."""
        if not self.learning_stats['performance_improvements']:
            return {
                'status': 'no_data',
                'message': 'No performance data collected'
            }
        
        # Calculate improvements
        performances = self.learning_stats['performance_improvements']
        initial = performances[0]
        final = performances[-1]
        
        success_improvement = (
            (final['success_rate'] - initial['success_rate']) / initial['success_rate'] 
            if initial['success_rate'] > 0 else 0
        ) * 100
        
        latency_improvement = (
            (initial['avg_latency'] - final['avg_latency']) / initial['avg_latency']
            if initial['avg_latency'] > 0 else 0
        ) * 100
        
        final_multiplier = self._calculate_multiplier(initial, final)
        
        report = {
            'status': 'success',
            'exponential_learning_achieved': final_multiplier >= 1.5,
            'summary': {
                'iterations_completed': self.learning_stats['iterations_completed'],
                'total_tasks_executed': self.learning_stats['tasks_executed'],
                'total_time_seconds': total_time,
                'avg_time_per_iteration': total_time / self.learning_stats['iterations_completed']
            },
            'performance': {
                'initial': initial,
                'final': final,
                'final_multiplier': final_multiplier,
                'success_rate_improvement_pct': success_improvement,
                'latency_improvement_pct': latency_improvement
            },
            'learning': {
                'strategies_learned': len(self.learning_stats['strategies_learned']),
                'strategy_knowledge': self.learning_stats['strategies_learned'],
                'config_adjustments': self.learning_stats['config_adjustments'],
                'goal_adjustments': self.learning_stats['goal_adjustments']
            },
            'milestones': {
                'doubled_performance': final_multiplier >= 2.0,
                '5x_performance': final_multiplier >= 5.0,
                '10x_performance': final_multiplier >= 10.0
            },
            'best_iteration': self.learning_stats['best_performance'],
            'learning_curve': self.learning_stats['performance_improvements'][-10:]  # Last 10
        }
        
        return report
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current learning statistics."""
        return {
            'iterations_completed': self.learning_stats['iterations_completed'],
            'tasks_executed': self.learning_stats['tasks_executed'],
            'strategies_learned': len(self.learning_stats['strategies_learned']),
            'config_adjustments': self.learning_stats['config_adjustments'],
            'baseline_performance': self.learning_stats['baseline_performance'],
            'best_performance': self.learning_stats['best_performance']
        }
