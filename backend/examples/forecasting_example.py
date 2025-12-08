
"""
Forecasting Engine Example

Demonstrates how to use the forecasting engine for:
- Time series forecasting
- Pattern recognition
- System state prediction
- Proactive goal setting
"""

import asyncio
from datetime import datetime, timedelta
import numpy as np

from core.forecasting_engine import ForecastingEngine
from core.time_series_forecaster import ForecastMethod
from core.pattern_recognizer import PatternType
from utils.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Main example demonstrating forecasting engine usage."""
    
    print("=" * 80)
    print("FORECASTING ENGINE EXAMPLE")
    print("=" * 80)
    
    # Initialize forecasting engine
    config = {
        "forecaster": {
            "max_history_size": 1000,
            "min_history_for_forecast": 10,
            "default_horizon": 24
        },
        "pattern_recognizer": {
            "max_history_size": 10000,
            "min_confidence_threshold": 0.7
        },
        "predictive_model": {
            "resource_capacities": {
                "cpu": 100.0,
                "memory": 100.0,
                "api_calls": 10000.0,
                "token_budget": 1000000.0
            }
        },
        "goal_setter": {
            "auto_goal_setting": True,
            "max_active_goals": 10
        },
        "auto_analysis_enabled": False  # Manual for demo
    }
    
    engine = ForecastingEngine(config)
    engine.start()
    
    print("\n✓ Forecasting engine initialized")
    
    # ========================================================================
    # 1. TIME SERIES FORECASTING
    # ========================================================================
    print("\n" + "=" * 80)
    print("1. TIME SERIES FORECASTING")
    print("=" * 80)
    
    # Simulate historical CPU usage data
    print("\n📊 Adding historical CPU usage data...")
    base_time = datetime.now() - timedelta(days=2)
    
    for i in range(48):  # 48 hours of data
        timestamp = base_time + timedelta(hours=i)
        
        # Simulate CPU usage with trend and noise
        trend = i * 0.5  # Increasing trend
        noise = np.random.normal(0, 3)
        cpu_usage = 40.0 + trend + noise
        
        engine.add_metric_data("cpu_usage", cpu_usage, timestamp)
    
    print(f"   Added 48 hours of historical data")
    
    # Generate forecasts using different methods
    print("\n🔮 Generating forecasts...")
    
    methods = [
        ForecastMethod.EXPONENTIAL_SMOOTHING,
        ForecastMethod.ARIMA,
        ForecastMethod.SARIMA,
        ForecastMethod.ENSEMBLE
    ]
    
    for method in methods:
        try:
            forecast = engine.forecast_metric("cpu_usage", method, horizon=24)
            print(f"\n   {method.value.upper()}:")
            print(f"      Next 24h prediction range: [{min(forecast.predictions):.1f}, {max(forecast.predictions):.1f}]")
            print(f"      MAE: {forecast.mae:.2f}, RMSE: {forecast.rmse:.2f}")
            print(f"      Confidence: {forecast.confidence_level * 100:.0f}%")
        except Exception as e:
            print(f"   {method.value}: Failed - {e}")
    
    # ========================================================================
    # 2. PATTERN RECOGNITION
    # ========================================================================
    print("\n" + "=" * 80)
    print("2. PATTERN RECOGNITION")
    print("=" * 80)
    
    # Simulate recurring tasks
    print("\n📝 Simulating recurring events...")
    
    # Daily backup at 2 AM
    for day in range(14):
        timestamp = datetime.now() - timedelta(days=14-day, hours=-2)
        engine.add_event("daily_backup", timestamp, {"duration": 3600})
    
    # Hourly health check
    for hour in range(48):
        timestamp = base_time + timedelta(hours=hour)
        engine.add_event("health_check", timestamp, {"status": "ok"})
    
    # User activity spikes (9 AM and 5 PM)
    for day in range(7):
        for hour in [9, 17]:
            base_ts = datetime.now() - timedelta(days=7-day)
            timestamp = base_ts.replace(hour=hour, minute=0, second=0)
            for _ in range(20):  # Many events during spike
                engine.add_event("user_activity", timestamp)
    
    print("   Added various recurring events")
    
    # Detect patterns
    print("\n🔍 Detecting patterns...")
    patterns = engine.detect_patterns()
    
    print(f"\n   Detected {len(patterns)} patterns:")
    for pattern in patterns:
        print(f"\n   • {pattern.pattern_type.value.upper()}")
        print(f"     Description: {pattern.description}")
        print(f"     Frequency: {pattern.frequency}")
        print(f"     Confidence: {pattern.confidence * 100:.0f}%")
        print(f"     Occurrences: {pattern.occurrences}")
    
    # ========================================================================
    # 3. SYSTEM STATE PREDICTION
    # ========================================================================
    print("\n" + "=" * 80)
    print("3. SYSTEM STATE PREDICTION")
    print("=" * 80)
    
    # Add more resource metrics
    print("\n📈 Adding resource usage history...")
    for i in range(48):
        timestamp = base_time + timedelta(hours=i)
        
        # Simulate various metrics
        engine.add_metric_data("cpu", 50.0 + i * 0.8 + np.random.normal(0, 5), timestamp)
        engine.add_metric_data("memory", 60.0 + i * 0.5 + np.random.normal(0, 3), timestamp)
        engine.add_metric_data("api_calls", 5000 + i * 50 + np.random.normal(0, 200), timestamp)
    
    # Current metrics
    current_metrics = {
        "cpu": 85.0,
        "memory": 75.0,
        "api_calls": 7500.0,
        "token_budget": 800000.0
    }
    
    print("\n🔮 Predicting system state (24h horizon)...")
    prediction = engine.predict_system_state(current_metrics, horizon_hours=24)
    
    print(f"\n   CURRENT STATE: {prediction.current_state.value.upper()}")
    print(f"   PREDICTED STATE: {prediction.predicted_state.value.upper()}")
    print(f"   Confidence: {prediction.confidence * 100:.0f}%")
    
    print(f"\n   Resource Demands:")
    for demand in prediction.resource_demands:
        print(f"      • {demand.resource_type.value}:")
        print(f"        Current: {demand.current_usage:.1f}")
        print(f"        Predicted: {demand.predicted_usage:.1f}")
        print(f"        Utilization: {demand.utilization_percent:.1f}%")
        if demand.will_exceed_capacity:
            print(f"        ⚠️  Will exceed capacity!")
    
    if prediction.predicted_bottlenecks:
        print(f"\n   Predicted Bottlenecks:")
        for bottleneck in prediction.predicted_bottlenecks:
            print(f"      • {bottleneck.location} ({bottleneck.severity})")
            print(f"        {bottleneck.description}")
            print(f"        Mitigations:")
            for suggestion in bottleneck.mitigation_suggestions[:2]:
                print(f"          - {suggestion}")
    
    if prediction.risk_factors:
        print(f"\n   Risk Factors:")
        for risk in prediction.risk_factors:
            print(f"      ⚠️  {risk}")
    
    if prediction.recommendations:
        print(f"\n   Recommendations:")
        for rec in prediction.recommendations[:5]:
            print(f"      💡 {rec}")
    
    # ========================================================================
    # 4. PROACTIVE GOAL SETTING
    # ========================================================================
    print("\n" + "=" * 80)
    print("4. PROACTIVE GOAL SETTING")
    print("=" * 80)
    
    print("\n🎯 Analyzing and setting proactive goals...")
    goals = engine.analyze_and_set_goals(current_metrics, horizon_hours=24)
    
    print(f"\n   Set {len(goals)} new goals:")
    for goal in goals:
        print(f"\n   • {goal.goal_type.value.upper()} [{goal.priority.value.upper()}]")
        print(f"     {goal.description}")
        print(f"     Target: {goal.target_metric}")
        print(f"     Current: {goal.current_value:.1f} → Target: {goal.target_value:.1f}")
        print(f"     Deadline: {goal.deadline.strftime('%Y-%m-%d %H:%M')}")
        print(f"     Actions:")
        for action in goal.actions[:3]:
            print(f"       - {action}")
    
    # ========================================================================
    # 5. COMPREHENSIVE REPORT
    # ========================================================================
    print("\n" + "=" * 80)
    print("5. COMPREHENSIVE REPORT")
    print("=" * 80)
    
    report = engine.get_comprehensive_report(current_metrics)
    
    print(f"\n📊 Engine Statistics:")
    print(f"   Total forecasts: {report['statistics']['total_forecasts']}")
    print(f"   Patterns detected: {report['statistics']['total_patterns_detected']}")
    print(f"   Predictions made: {report['statistics']['total_predictions']}")
    print(f"   Active goals: {report['goals']['active']}")
    print(f"   Goal achievement rate: {report['goals']['achievement_rate'] * 100:.0f}%")
    
    print(f"\n📈 Patterns by Type:")
    for pattern_type, count in report['patterns']['by_type'].items():
        if count > 0:
            print(f"   {pattern_type}: {count}")
    
    print(f"\n🎯 Goals by Type:")
    for goal_type, count in report['goals']['by_type'].items():
        if count > 0:
            print(f"   {goal_type}: {count}")
    
    # ========================================================================
    # 6. GOAL EXECUTION
    # ========================================================================
    print("\n" + "=" * 80)
    print("6. GOAL EXECUTION SIMULATION")
    print("=" * 80)
    
    active_goals = engine.get_active_goals()
    if active_goals:
        goal = active_goals[0]
        print(f"\n🎯 Executing goal: {goal.description}")
        
        # Simulate progress updates
        for progress in [0.3, 0.6, 0.9, 1.0]:
            await asyncio.sleep(0.5)  # Simulate work
            new_value = goal.current_value + (goal.target_value - goal.current_value) * progress
            engine.update_goal_progress(goal.goal_id, progress, new_value)
            print(f"   Progress: {progress * 100:.0f}% (Value: {new_value:.1f})")
        
        print(f"\n   ✓ Goal achieved!")
    
    # Cleanup
    engine.stop()
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
