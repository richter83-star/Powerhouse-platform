
"""
Unit Tests for Forecasting Engine

Tests all forecasting components:
- Time Series Forecaster
- Pattern Recognizer
- Predictive State Model
- Proactive Goal Setter
- Forecasting Engine Integration
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

from core.time_series_forecaster import TimeSeriesForecaster, ForecastMethod
from core.pattern_recognizer import PatternRecognizer, PatternType
from core.predictive_state_model import PredictiveStateModel, SystemState, ResourceType
from core.proactive_goal_setter import ProactiveGoalSetter, GoalType, GoalStatus
from core.forecasting_engine import ForecastingEngine


class TestTimeSeriesForecaster:
    """Test TimeSeriesForecaster functionality."""
    
    def test_initialization(self):
        forecaster = TimeSeriesForecaster()
        assert forecaster is not None
        assert forecaster.history == {}
    
    def test_add_data_point(self):
        forecaster = TimeSeriesForecaster()
        forecaster.add_data_point("test_metric", 10.0)
        
        history = forecaster.get_history("test_metric")
        assert len(history) == 1
        assert history[0][1] == 10.0
    
    def test_forecast_exponential_smoothing(self):
        forecaster = TimeSeriesForecaster()
        
        # Add historical data
        base_time = datetime.now()
        for i in range(20):
            ts = base_time + timedelta(hours=i)
            value = 10.0 + i * 0.5 + np.random.normal(0, 0.5)
            forecaster.add_data_point("test_metric", value, ts)
        
        # Generate forecast
        forecast = forecaster.forecast("test_metric", ForecastMethod.EXPONENTIAL_SMOOTHING, horizon=10)
        
        assert forecast is not None
        assert len(forecast.predictions) == 10
        assert len(forecast.confidence_intervals) == 10
        assert forecast.mae is not None
    
    def test_forecast_arima(self):
        forecaster = TimeSeriesForecaster()
        
        # Add trending data
        base_time = datetime.now()
        for i in range(30):
            ts = base_time + timedelta(hours=i)
            value = 10.0 + i * 1.2
            forecaster.add_data_point("test_metric", value, ts)
        
        forecast = forecaster.forecast("test_metric", ForecastMethod.ARIMA, horizon=10)
        
        assert forecast is not None
        assert len(forecast.predictions) == 10
        # Should capture trend
        assert forecast.predictions[-1] > forecast.predictions[0]
    
    def test_forecast_sarima(self):
        forecaster = TimeSeriesForecaster()
        
        # Add seasonal data
        base_time = datetime.now()
        for i in range(50):
            ts = base_time + timedelta(hours=i)
            # Seasonal pattern with period 24
            seasonal = 10 * np.sin(2 * np.pi * i / 24)
            trend = i * 0.1
            value = 50 + trend + seasonal
            forecaster.add_data_point("test_metric", value, ts)
        
        forecast = forecaster.forecast("test_metric", ForecastMethod.SARIMA, horizon=24, seasonal_period=24)
        
        assert forecast is not None
        assert forecast.metadata.get("seasonal_period") == 24
    
    def test_insufficient_history(self):
        forecaster = TimeSeriesForecaster(config={"min_history_for_forecast": 10})
        
        # Add only 5 points
        for i in range(5):
            forecaster.add_data_point("test_metric", float(i))
        
        with pytest.raises(ValueError, match="Insufficient history"):
            forecaster.forecast("test_metric")


class TestPatternRecognizer:
    """Test PatternRecognizer functionality."""
    
    def test_initialization(self):
        recognizer = PatternRecognizer()
        assert recognizer is not None
        assert recognizer.patterns == {}
    
    def test_add_event(self):
        recognizer = PatternRecognizer()
        recognizer.add_event("test_event", datetime.now())
        
        assert len(recognizer.event_history) == 1
    
    def test_detect_recurring_tasks(self):
        recognizer = PatternRecognizer()
        
        # Add recurring events (every hour)
        base_time = datetime.now()
        for i in range(10):
            ts = base_time + timedelta(hours=i)
            recognizer.add_event("hourly_task", ts)
        
        patterns = recognizer.analyze_patterns()
        
        # Should detect recurring pattern
        recurring = [p for p in patterns if p.pattern_type == PatternType.RECURRING_TASK]
        assert len(recurring) > 0
    
    def test_detect_periodic_spikes(self):
        recognizer = PatternRecognizer()
        
        # Add events with spikes at specific hours
        base_time = datetime.now().replace(hour=0, minute=0, second=0)
        for day in range(5):
            for hour in range(24):
                ts = base_time + timedelta(days=day, hours=hour)
                # Spikes at 9am and 5pm
                if hour in [9, 17]:
                    for _ in range(10):  # Many events
                        recognizer.add_event("user_activity", ts)
                else:
                    recognizer.add_event("user_activity", ts)
        
        patterns = recognizer.analyze_patterns()
        
        # Should detect spike pattern
        spikes = [p for p in patterns if p.pattern_type == PatternType.PERIODIC_SPIKE]
        assert len(spikes) > 0
    
    def test_detect_workflow_sequences(self):
        recognizer = PatternRecognizer()
        
        # Add common workflow sequence
        base_time = datetime.now()
        for i in range(5):
            ts = base_time + timedelta(minutes=i * 10)
            recognizer.add_event("start_task", ts)
            recognizer.add_event("process_data", ts + timedelta(minutes=1))
            recognizer.add_event("finish_task", ts + timedelta(minutes=2))
        
        patterns = recognizer.analyze_patterns()
        
        # Should detect workflow
        workflows = [p for p in patterns if p.pattern_type == PatternType.WORKFLOW_SEQUENCE]
        assert len(workflows) > 0


class TestPredictiveStateModel:
    """Test PredictiveStateModel functionality."""
    
    def test_initialization(self):
        forecaster = TimeSeriesForecaster()
        recognizer = PatternRecognizer()
        model = PredictiveStateModel(forecaster, recognizer)
        
        assert model is not None
        assert model.forecaster == forecaster
        assert model.pattern_recognizer == recognizer
    
    def test_determine_current_state(self):
        forecaster = TimeSeriesForecaster()
        recognizer = PatternRecognizer()
        model = PredictiveStateModel(forecaster, recognizer)
        
        # Low utilization
        metrics = {"cpu": 30.0, "memory": 40.0}
        state = model._determine_current_state(metrics)
        assert state == SystemState.OPTIMAL
        
        # High utilization
        metrics = {"cpu": 95.0, "memory": 98.0}
        state = model._determine_current_state(metrics)
        assert state == SystemState.CRITICAL
    
    def test_predict_system_state(self):
        forecaster = TimeSeriesForecaster()
        recognizer = PatternRecognizer()
        model = PredictiveStateModel(forecaster, recognizer)
        
        # Add historical data
        base_time = datetime.now()
        for i in range(30):
            ts = base_time + timedelta(hours=i)
            forecaster.add_data_point("cpu", 50.0 + i * 1.5, ts)
            forecaster.add_data_point("memory", 40.0 + i * 1.0, ts)
        
        # Predict future state
        current_metrics = {"cpu": 80.0, "memory": 70.0}
        prediction = model.predict_system_state(horizon_hours=24, current_metrics=current_metrics)
        
        assert prediction is not None
        assert prediction.current_state in SystemState
        assert prediction.predicted_state in SystemState
        assert len(prediction.resource_demands) > 0


class TestProactiveGoalSetter:
    """Test ProactiveGoalSetter functionality."""
    
    def test_initialization(self):
        forecaster = TimeSeriesForecaster()
        recognizer = PatternRecognizer()
        model = PredictiveStateModel(forecaster, recognizer)
        goal_setter = ProactiveGoalSetter(model, recognizer)
        
        assert goal_setter is not None
        assert goal_setter.goals == {}
    
    def test_analyze_and_set_goals(self):
        forecaster = TimeSeriesForecaster()
        recognizer = PatternRecognizer()
        model = PredictiveStateModel(forecaster, recognizer)
        goal_setter = ProactiveGoalSetter(model, recognizer)
        
        # Add data indicating high resource usage
        base_time = datetime.now()
        for i in range(30):
            ts = base_time + timedelta(hours=i)
            forecaster.add_data_point("cpu", 70.0 + i * 1.0, ts)
        
        # Set goals
        current_metrics = {"cpu": 90.0}
        goals = goal_setter.analyze_and_set_goals(current_metrics, horizon_hours=24)
        
        assert len(goals) > 0
        # Should have resource optimization or capacity planning goals
        assert any(g.goal_type in [GoalType.RESOURCE_OPTIMIZATION, GoalType.CAPACITY_PLANNING] for g in goals)
    
    def test_update_goal_progress(self):
        forecaster = TimeSeriesForecaster()
        recognizer = PatternRecognizer()
        model = PredictiveStateModel(forecaster, recognizer)
        goal_setter = ProactiveGoalSetter(model, recognizer)
        
        # Create a goal manually
        from core.proactive_goal_setter import Goal, GoalPriority
        import uuid
        
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            goal_type=GoalType.PERFORMANCE_TARGET,
            priority=GoalPriority.HIGH,
            description="Test goal",
            target_metric="latency",
            current_value=300.0,
            target_value=200.0,
            deadline=datetime.now() + timedelta(days=1)
        )
        goal_setter.goals[goal.goal_id] = goal
        
        # Update progress
        goal_setter.update_goal_progress(goal.goal_id, 0.5, 250.0)
        
        assert goal.progress == 0.5
        assert goal.current_value == 250.0
        assert goal.status == GoalStatus.ACTIVE
        
        # Complete the goal
        goal_setter.update_goal_progress(goal.goal_id, 1.0, 200.0)
        assert goal.status == GoalStatus.ACHIEVED


class TestForecastingEngine:
    """Test ForecastingEngine integration."""
    
    def test_initialization(self):
        engine = ForecastingEngine()
        assert engine is not None
        assert engine.forecaster is not None
        assert engine.pattern_recognizer is not None
        assert engine.predictive_model is not None
        assert engine.goal_setter is not None
    
    def test_add_metric_and_forecast(self):
        engine = ForecastingEngine()
        
        # Add data
        base_time = datetime.now()
        for i in range(30):
            ts = base_time + timedelta(hours=i)
            engine.add_metric_data("test_metric", 10.0 + i * 0.5, ts)
        
        # Generate forecast
        forecast = engine.forecast_metric("test_metric", ForecastMethod.ARIMA, horizon=10)
        
        assert forecast is not None
        assert len(forecast.predictions) == 10
    
    def test_add_event_and_detect_patterns(self):
        engine = ForecastingEngine()
        
        # Add recurring events
        base_time = datetime.now()
        for i in range(20):
            ts = base_time + timedelta(hours=i)
            engine.add_event("recurring_task", ts)
        
        # Detect patterns
        patterns = engine.detect_patterns()
        
        assert len(patterns) > 0
    
    def test_comprehensive_report(self):
        engine = ForecastingEngine()
        
        # Add some data
        base_time = datetime.now()
        for i in range(30):
            ts = base_time + timedelta(hours=i)
            engine.add_metric_data("cpu", 50.0 + i * 1.0, ts)
            engine.add_event("task_execution", ts)
        
        # Generate report
        report = engine.get_comprehensive_report({"cpu": 80.0})
        
        assert "patterns" in report
        assert "statistics" in report
        assert "goals" in report
    
    def test_auto_analysis(self):
        config = {
            "auto_analysis_enabled": False  # Disable for testing
        }
        engine = ForecastingEngine(config)
        engine.start()
        
        assert not engine.analysis_thread
        
        engine.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
