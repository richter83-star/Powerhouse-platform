
"""
Forecasting Engine - Main Orchestrator

Integrates all forecasting components:
- Time Series Forecasting
- Pattern Recognition
- Predictive State Modeling
- Proactive Goal Setting

Provides a unified interface for predictive capabilities.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from threading import Thread, Lock
import time
import json

from utils.logging import get_logger
from core.time_series_forecaster import TimeSeriesForecaster, ForecastMethod, ForecastResult
from core.pattern_recognizer import PatternRecognizer, Pattern, PatternType
from core.predictive_state_model import (
    PredictiveStateModel, SystemStatePrediction, SystemState, ResourceType
)
from core.proactive_goal_setter import ProactiveGoalSetter, Goal, GoalType, GoalStatus

logger = get_logger(__name__)


class ForecastingEngine:
    """
    Main Forecasting Engine orchestrating all predictive components.
    
    Features:
    - Unified interface for all forecasting capabilities
    - Automatic periodic analysis and goal setting
    - Integration with Performance Monitor
    - Real-time pattern detection and prediction
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.lock = Lock()
        
        # Initialize components
        forecaster_config = self.config.get("forecaster", {})
        self.forecaster = TimeSeriesForecaster(forecaster_config)
        
        pattern_config = self.config.get("pattern_recognizer", {})
        self.pattern_recognizer = PatternRecognizer(pattern_config)
        
        predictive_config = self.config.get("predictive_model", {})
        self.predictive_model = PredictiveStateModel(
            self.forecaster,
            self.pattern_recognizer,
            predictive_config
        )
        
        goal_setter_config = self.config.get("goal_setter", {})
        self.goal_setter = ProactiveGoalSetter(
            self.predictive_model,
            self.pattern_recognizer,
            goal_setter_config
        )
        
        # Analysis settings
        self.auto_analysis_enabled = self.config.get("auto_analysis_enabled", True)
        self.analysis_interval_minutes = self.config.get("analysis_interval_minutes", 60)
        
        # Background thread
        self.analysis_thread: Optional[Thread] = None
        self.running = False
        
        # Statistics
        self.stats = {
            "total_forecasts": 0,
            "total_patterns_detected": 0,
            "total_predictions": 0,
            "total_goals_set": 0,
            "last_analysis_time": None
        }
        
        logger.info("ForecastingEngine initialized")
    
    def start(self):
        """Start the forecasting engine with automatic analysis."""
        if self.running:
            logger.warning("ForecastingEngine already running")
            return
        
        self.running = True
        
        if self.auto_analysis_enabled:
            self.analysis_thread = Thread(target=self._analysis_loop, daemon=True)
            self.analysis_thread.start()
            logger.info("ForecastingEngine started with automatic analysis")
        else:
            logger.info("ForecastingEngine started (manual analysis mode)")
    
    def stop(self):
        """Stop the forecasting engine."""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        logger.info("ForecastingEngine stopped")
    
    def _analysis_loop(self):
        """Background thread for periodic analysis."""
        while self.running:
            try:
                self.analyze_and_set_goals()
                time.sleep(self.analysis_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying
    
    def add_metric_data(
        self,
        metric_name: str,
        value: float,
        timestamp: Optional[datetime] = None
    ):
        """Add a data point for forecasting."""
        with self.lock:
            self.forecaster.add_data_point(metric_name, value, timestamp)
    
    def add_event(
        self,
        event_type: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add an event for pattern recognition."""
        with self.lock:
            ts = timestamp or datetime.now()
            self.pattern_recognizer.add_event(event_type, ts, metadata)
    
    def forecast_metric(
        self,
        metric_name: str,
        method: ForecastMethod = ForecastMethod.ENSEMBLE,
        horizon: int = 24,
        **kwargs
    ) -> ForecastResult:
        """
        Generate a forecast for a specific metric.
        
        Args:
            metric_name: Name of the metric to forecast
            method: Forecasting method to use
            horizon: Forecast horizon in time steps
            **kwargs: Additional parameters for forecasting
        
        Returns:
            ForecastResult with predictions and confidence intervals
        """
        with self.lock:
            forecast = self.forecaster.forecast(metric_name, method, horizon, **kwargs)
            self.stats["total_forecasts"] += 1
        
        logger.info(f"Generated forecast for {metric_name} using {method}")
        return forecast
    
    def detect_patterns(self) -> List[Pattern]:
        """
        Detect patterns in event history.
        
        Returns:
            List of detected patterns
        """
        with self.lock:
            patterns = self.pattern_recognizer.analyze_patterns()
            self.stats["total_patterns_detected"] = len(patterns)
        
        logger.info(f"Detected {len(patterns)} patterns")
        return patterns
    
    def predict_system_state(
        self,
        current_metrics: Optional[Dict[str, float]] = None,
        horizon_hours: int = 24
    ) -> SystemStatePrediction:
        """
        Predict future system state.
        
        Args:
            current_metrics: Current system metrics
            horizon_hours: Prediction horizon in hours
        
        Returns:
            SystemStatePrediction with detailed forecast
        """
        with self.lock:
            prediction = self.predictive_model.predict_system_state(
                horizon_hours, current_metrics
            )
            self.stats["total_predictions"] += 1
        
        logger.info(
            f"Predicted system state: {prediction.current_state} -> {prediction.predicted_state}"
        )
        return prediction
    
    def analyze_and_set_goals(
        self,
        current_metrics: Optional[Dict[str, float]] = None,
        horizon_hours: int = 24
    ) -> List[Goal]:
        """
        Comprehensive analysis: detect patterns, predict state, and set goals.
        
        Args:
            current_metrics: Current system metrics
            horizon_hours: Prediction horizon
        
        Returns:
            List of newly set goals
        """
        with self.lock:
            # Detect patterns
            patterns = self.pattern_recognizer.analyze_patterns()
            
            # Set goals based on predictions and patterns
            goals = self.goal_setter.analyze_and_set_goals(current_metrics, horizon_hours)
            
            self.stats["total_goals_set"] = len(self.goal_setter.goals)
            self.stats["last_analysis_time"] = datetime.now().isoformat()
        
        logger.info(f"Analysis complete: {len(patterns)} patterns, {len(goals)} new goals")
        return goals
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        with self.lock:
            return self.goal_setter.get_active_goals()
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal."""
        with self.lock:
            return self.goal_setter.get_goal(goal_id)
    
    def update_goal_progress(
        self,
        goal_id: str,
        progress: float,
        current_value: Optional[float] = None
    ):
        """Update progress on a goal."""
        with self.lock:
            self.goal_setter.update_goal_progress(goal_id, progress, current_value)
    
    def execute_goal_actions(self, goal_id: str) -> List[str]:
        """Execute actions for a goal."""
        with self.lock:
            return self.goal_setter.execute_goal_actions(goal_id)
    
    def get_patterns(self, pattern_type: Optional[PatternType] = None) -> List[Pattern]:
        """Get detected patterns, optionally filtered by type."""
        with self.lock:
            if pattern_type:
                return self.pattern_recognizer.get_patterns_by_type(pattern_type)
            return self.pattern_recognizer.get_all_patterns()
    
    def get_comprehensive_report(
        self,
        current_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Get a comprehensive report of all forecasting engine components.
        
        Args:
            current_metrics: Current system metrics
        
        Returns:
            Comprehensive report dictionary
        """
        with self.lock:
            # Get patterns
            patterns = self.pattern_recognizer.get_all_patterns()
            
            # Get prediction
            try:
                prediction = self.predictive_model.predict_system_state(
                    horizon_hours=24,
                    current_metrics=current_metrics
                )
                prediction_dict = prediction.to_dict()
            except Exception as e:
                logger.warning(f"Could not generate prediction: {e}")
                prediction_dict = None
            
            # Get goals
            active_goals = self.goal_setter.get_active_goals()
            achievement_report = self.goal_setter.get_achievement_report()
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.stats.copy(),
                "patterns": {
                    "total": len(patterns),
                    "by_type": {
                        pt.value: len(self.pattern_recognizer.get_patterns_by_type(pt))
                        for pt in PatternType
                    },
                    "patterns": [p.to_dict() for p in patterns]
                },
                "prediction": prediction_dict,
                "goals": {
                    "total": len(self.goal_setter.goals),
                    "active": len(active_goals),
                    "achievement_rate": achievement_report["achievement_rate"],
                    "active_goals": [g.to_dict() for g in active_goals],
                    "by_type": {
                        gt.value: len(self.goal_setter.get_goals_by_type(gt))
                        for gt in GoalType
                    }
                },
                "capacity_report": self.predictive_model.get_capacity_report()
            }
        
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        with self.lock:
            return {
                **self.stats,
                "active_goals": len(self.goal_setter.get_active_goals()),
                "detected_patterns": len(self.pattern_recognizer.get_all_patterns()),
                "running": self.running,
                "auto_analysis_enabled": self.auto_analysis_enabled
            }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete engine state for persistence."""
        with self.lock:
            return {
                "config": self.config,
                "statistics": self.stats,
                "forecaster_history": {
                    metric: list(history)
                    for metric, history in self.forecaster.history.items()
                },
                "patterns": self.pattern_recognizer.to_dict(),
                "goals": self.goal_setter.to_dict()
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Get engine state as dictionary."""
        return self.get_comprehensive_report()
