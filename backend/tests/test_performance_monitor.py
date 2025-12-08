
"""
Tests for Performance Monitor.
"""

import pytest
import time
from datetime import datetime, timedelta

from core.performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    AgentPerformance,
    PerformanceAlert,
    AlertLevel,
    MetricType,
    get_performance_monitor,
    init_performance_monitor
)


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.monitor = PerformanceMonitor(
            window_size_minutes=60,
            enable_auto_alerts=True,
            enable_trend_analysis=False  # Disable for faster tests
        )
    
    def teardown_method(self):
        """Cleanup after tests."""
        if self.monitor:
            self.monitor.stop()
    
    def test_initialization(self):
        """Test monitor initialization."""
        assert self.monitor is not None
        assert self.monitor.window_size_minutes == 60
        assert self.monitor.enable_auto_alerts is True
        assert self.monitor.enable_trend_analysis is False
    
    def test_record_agent_run(self):
        """Test recording agent run events."""
        self.monitor.record_agent_run(
            run_id="run_123",
            agent_name="test_agent",
            agent_type="react",
            status="success",
            duration_ms=1500,
            tokens_used=250,
            cost=0.05,
            quality_score=0.85
        )
        
        # Check that event was recorded
        stats = self.monitor.get_stats()
        assert stats["events_buffered"] == 1
        assert stats["agents_tracked"] == 1
    
    def test_system_metrics_calculation(self):
        """Test system-wide metrics calculation."""
        # Record several events
        for i in range(10):
            status = "success" if i < 8 else "failure"
            self.monitor.record_agent_run(
                run_id=f"run_{i}",
                agent_name="test_agent",
                agent_type="react",
                status=status,
                duration_ms=1000 + i * 100,
                tokens_used=200 + i * 10,
                cost=0.05 + i * 0.01,
                quality_score=0.8 + i * 0.01
            )
        
        # Get metrics
        metrics = self.monitor.get_system_metrics()
        
        assert metrics.total_tasks == 10
        assert metrics.successful_tasks == 8
        assert metrics.failed_tasks == 2
        assert metrics.success_rate == 0.8
        assert metrics.avg_latency_ms > 0
        assert metrics.total_tokens > 0
        assert metrics.total_cost > 0
    
    def test_agent_metrics(self):
        """Test agent-specific metrics."""
        # Record events for multiple agents
        for agent_name in ["agent_1", "agent_2"]:
            for i in range(5):
                self.monitor.record_agent_run(
                    run_id=f"run_{agent_name}_{i}",
                    agent_name=agent_name,
                    agent_type="react",
                    status="success",
                    duration_ms=1000,
                    tokens_used=200,
                    cost=0.05
                )
        
        # Get agent metrics
        agent1_perf = self.monitor.get_agent_metrics("agent_1")
        agent2_perf = self.monitor.get_agent_metrics("agent_2")
        
        assert agent1_perf.agent_name == "agent_1"
        assert agent1_perf.metrics.total_tasks == 5
        assert agent1_perf.status == "active"
        
        assert agent2_perf.agent_name == "agent_2"
        assert agent2_perf.metrics.total_tasks == 5
    
    def test_accuracy_recording(self):
        """Test accuracy measurement recording."""
        self.monitor.record_accuracy(
            agent_name="test_agent",
            task_id="task_123",
            predicted_outcome={"value": 100},
            actual_outcome={"value": 95},
            feedback_source="user"
        )
        
        stats = self.monitor.get_stats()
        assert stats["accuracy_measurements"] == 1
    
    def test_accuracy_score_calculation(self):
        """Test different accuracy score calculations."""
        monitor = self.monitor
        
        # Exact match
        assert monitor._calculate_accuracy_score(100, 100) == 1.0
        
        # Numeric values
        score = monitor._calculate_accuracy_score(95, 100)
        assert 0.9 < score < 1.0
        
        # String similarity
        score = monitor._calculate_accuracy_score(
            "hello world",
            "hello beautiful world"
        )
        assert 0 < score < 1.0
        
        # Dictionary similarity
        score = monitor._calculate_accuracy_score(
            {"a": 1, "b": 2},
            {"a": 1, "b": 2, "c": 3}
        )
        assert 0.5 < score < 1.0
    
    def test_alert_generation(self):
        """Test alert generation for threshold violations."""
        # Record events that should trigger alerts
        for i in range(5):
            # High latency event
            self.monitor.record_agent_run(
                run_id=f"run_{i}",
                agent_name="slow_agent",
                agent_type="react",
                status="success",
                duration_ms=6000,  # Above threshold
                tokens_used=200
            )
        
        # Get alerts
        alerts = self.monitor.get_alerts()
        
        # Should have at least one alert
        assert len(alerts) > 0
        
        # Check alert properties
        latency_alerts = [a for a in alerts if a.metric_type == MetricType.LATENCY]
        assert len(latency_alerts) > 0
    
    def test_health_score(self):
        """Test health score calculation."""
        # Record good performance
        for i in range(10):
            self.monitor.record_agent_run(
                run_id=f"run_{i}",
                agent_name="test_agent",
                agent_type="react",
                status="success",
                duration_ms=800,
                quality_score=0.9
            )
        
        metrics = self.monitor.get_system_metrics()
        health_score = self.monitor._calculate_health_score(metrics)
        
        assert 80 <= health_score <= 100  # Should be high for good performance
    
    def test_report_generation(self):
        """Test comprehensive report generation."""
        # Record some events
        for i in range(5):
            self.monitor.record_agent_run(
                run_id=f"run_{i}",
                agent_name="test_agent",
                agent_type="react",
                status="success",
                duration_ms=1000,
                tokens_used=200
            )
        
        # Generate report
        report = self.monitor.generate_report(include_agents=True)
        
        assert "generated_at" in report
        assert "system_metrics" in report
        assert "health_score" in report
        assert "agent_metrics" in report
        assert "recommendations" in report
        
        assert report["health_score"] > 0
        assert len(report["recommendations"]) > 0
    
    def test_recommendations(self):
        """Test recommendation generation."""
        # Record poor performance
        for i in range(10):
            self.monitor.record_agent_run(
                run_id=f"run_{i}",
                agent_name="test_agent",
                agent_type="react",
                status="failure",  # All failures
                duration_ms=5000,  # Slow
                tokens_used=4000,  # Many tokens
                cost=0.80  # Expensive
            )
        
        metrics = self.monitor.get_system_metrics()
        recommendations = self.monitor._generate_recommendations(metrics)
        
        assert len(recommendations) > 0
        
        # Should recommend fixing success rate
        assert any("success rate" in r.lower() for r in recommendations)
    
    def test_time_window_filtering(self):
        """Test time window filtering of metrics."""
        # Record old event (outside window)
        old_event = {
            "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
            "run_id": "old_run",
            "agent_name": "test_agent",
            "agent_type": "react",
            "status": "success",
            "duration_ms": 1000,
            "tokens_used": 200,
            "cost": 0.05,
            "memory_mb": 0,
            "cpu_ms": 0,
            "quality_score": None,
            "confidence": None,
            "error_type": None,
            "metadata": {}
        }
        
        # Record recent event
        self.monitor.record_agent_run(
            run_id="recent_run",
            agent_name="test_agent",
            agent_type="react",
            status="success",
            duration_ms=1000,
            tokens_used=200
        )
        
        # Add old event manually
        with self.monitor._lock:
            self.monitor._metrics_buffer.append(old_event)
        
        # Get metrics with 60-minute window
        metrics = self.monitor.get_system_metrics(time_window_minutes=60)
        
        # Should only include recent event
        assert metrics.total_tasks == 1
    
    def test_agent_performance_scores(self):
        """Test agent performance score calculations."""
        # Record high-quality, consistent performance
        for i in range(10):
            self.monitor.record_agent_run(
                run_id=f"run_{i}",
                agent_name="test_agent",
                agent_type="react",
                status="success",
                duration_ms=800,
                tokens_used=150,
                quality_score=0.95,
                confidence=0.90
            )
        
        performance = self.monitor.get_agent_metrics("test_agent")
        
        # Check scores
        assert performance.reliability_score >= 0.9  # High success rate
        assert performance.efficiency_score > 0.5  # Good balance
        assert performance.specialization_score > 0.8  # High quality
    
    def test_cleanup(self):
        """Test old data cleanup."""
        # Record many old events
        for i in range(100):
            old_event = {
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "run_id": f"old_run_{i}",
                "agent_name": "test_agent",
                "agent_type": "react",
                "status": "success",
                "duration_ms": 1000,
                "tokens_used": 200,
                "cost": 0.05,
                "memory_mb": 0,
                "cpu_ms": 0,
                "quality_score": None,
                "confidence": None,
                "error_type": None,
                "metadata": {}
            }
            with self.monitor._lock:
                self.monitor._metrics_buffer.append(old_event)
        
        initial_count = self.monitor.get_stats()["events_buffered"]
        
        # Run cleanup
        self.monitor._cleanup_old_data()
        
        # Check that old data was removed
        final_count = self.monitor.get_stats()["events_buffered"]
        assert final_count < initial_count
    
    def test_global_monitor_instance(self):
        """Test global monitor instance management."""
        # Get global instance
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        # Should be the same instance
        assert monitor1 is monitor2
        
        # Initialize with custom settings
        custom_monitor = init_performance_monitor(window_size_minutes=30)
        
        # Should be a new instance
        assert custom_monitor is not monitor1
        assert custom_monitor.window_size_minutes == 30
        
        # Cleanup
        custom_monitor.stop()


def test_performance_metrics_dataclass():
    """Test PerformanceMetrics dataclass."""
    metrics = PerformanceMetrics(
        total_tasks=100,
        successful_tasks=85,
        failed_tasks=15,
        success_rate=0.85,
        avg_latency_ms=1250.5
    )
    
    assert metrics.total_tasks == 100
    assert metrics.success_rate == 0.85
    assert metrics.avg_latency_ms == 1250.5


def test_performance_alert_dataclass():
    """Test PerformanceAlert dataclass."""
    alert = PerformanceAlert(
        alert_id="alert_123",
        level=AlertLevel.WARNING,
        metric_type=MetricType.LATENCY,
        message="High latency detected",
        current_value=5000,
        threshold=3000,
        agent_name="slow_agent",
        recommendation="Optimize agent prompts"
    )
    
    assert alert.level == AlertLevel.WARNING
    assert alert.metric_type == MetricType.LATENCY
    assert alert.current_value == 5000
    assert alert.threshold == 3000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
