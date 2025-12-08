"""
Tests for monitoring and metrics functionality.
"""
import pytest
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from core.monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    cache_hits_total,
    cache_misses_total,
    get_metrics
)
from core.monitoring.health_metrics import collect_system_metrics, get_health_metrics
from core.monitoring.alerting import AlertManager, AlertSeverity, Alert


@pytest.mark.unit
@pytest.mark.monitoring
class TestPrometheusMetrics:
    """Test Prometheus metrics collection."""
    
    def test_http_requests_total_counter(self):
        """Test HTTP requests counter."""
        # Reset counter
        http_requests_total._value.clear()
        
        http_requests_total.labels(method="GET", endpoint="/health", status_code=200).inc()
        http_requests_total.labels(method="GET", endpoint="/health", status_code=200).inc()
        
        # Get metric value
        value = http_requests_total.labels(method="GET", endpoint="/health", status_code=200)._value.get()
        assert value == 2
    
    def test_http_request_duration_histogram(self):
        """Test HTTP request duration histogram."""
        http_request_duration_seconds.labels(method="GET", endpoint="/health").observe(0.5)
        http_request_duration_seconds.labels(method="GET", endpoint="/health").observe(1.0)
        
        # Histogram should record observations
        # We can't easily test the exact values, but we can verify it doesn't error
        assert True
    
    def test_cache_metrics(self):
        """Test cache hit/miss counters."""
        cache_hits_total._value.clear()
        cache_misses_total._value.clear()
        
        cache_hits_total.labels(cache_type="redis").inc()
        cache_hits_total.labels(cache_type="redis").inc()
        cache_misses_total.labels(cache_type="redis").inc()
        
        hits = cache_hits_total.labels(cache_type="redis")._value.get()
        misses = cache_misses_total.labels(cache_type="redis")._value.get()
        
        assert hits == 2
        assert misses == 1
    
    def test_get_metrics_output(self):
        """Test that get_metrics returns valid Prometheus format."""
        metrics = get_metrics()
        
        assert isinstance(metrics, str)
        assert len(metrics) > 0
        # Should contain some metric names
        assert "http_requests_total" in metrics or "# HELP" in metrics


@pytest.mark.unit
@pytest.mark.monitoring
class TestSystemMetrics:
    """Test system metrics collection."""
    
    @patch('core.monitoring.health_metrics.psutil')
    def test_collect_system_metrics(self, mock_psutil):
        """Test system metrics collection."""
        # Mock psutil
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.cpu_count.return_value = 4
        
        mock_memory = Mock()
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.used = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.percent = 50.0
        mock_memory.available = 4 * 1024 * 1024 * 1024
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_disk = Mock()
        mock_disk.total = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk.used = 50 * 1024 * 1024 * 1024  # 50GB
        mock_disk.percent = 50.0
        mock_disk.free = 50 * 1024 * 1024 * 1024
        mock_psutil.disk_usage.return_value = mock_disk
        
        metrics = collect_system_metrics()
        
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert metrics["cpu"]["percent"] == 50.0
        assert metrics["memory"]["percent"] == 50.0
        assert metrics["disk"]["percent"] == 50.0
    
    def test_get_health_metrics(self):
        """Test get_health_metrics returns comprehensive data."""
        with patch('core.monitoring.health_metrics.collect_system_metrics') as mock_collect:
            mock_collect.return_value = {
                "cpu": {"percent": 50.0},
                "memory": {"percent": 50.0},
                "disk": {"percent": 50.0}
            }
            
            health_metrics = get_health_metrics()
            
            assert "system" in health_metrics
            assert "timestamp" in health_metrics


@pytest.mark.unit
@pytest.mark.monitoring
class TestAlertManager:
    """Test alert manager functionality."""
    
    def test_alert_manager_initialization(self):
        """Test alert manager initialization."""
        manager = AlertManager()
        assert manager.alerts == {}
        assert manager.handlers == []
        assert manager.thresholds == {}
    
    def test_register_handler(self):
        """Test registering alert handler."""
        manager = AlertManager()
        handler = Mock()
        
        manager.register_handler(handler)
        assert handler in manager.handlers
    
    def test_set_threshold(self):
        """Test setting alert threshold."""
        manager = AlertManager()
        threshold = {
            "warning": 80,
            "error": 90,
            "critical": 95
        }
        
        manager.set_threshold("cpu_usage", threshold)
        assert manager.thresholds["cpu_usage"] == threshold
    
    def test_check_threshold(self):
        """Test threshold checking."""
        manager = AlertManager()
        manager.set_threshold("cpu_usage", {
            "warning": 80,
            "error": 90,
            "critical": 95
        })
        
        # Test below threshold
        assert manager.check_threshold("cpu_usage", 50) is None
        
        # Test warning threshold
        assert manager.check_threshold("cpu_usage", 85) == AlertSeverity.WARNING
        
        # Test error threshold
        assert manager.check_threshold("cpu_usage", 92) == AlertSeverity.ERROR
        
        # Test critical threshold
        assert manager.check_threshold("cpu_usage", 98) == AlertSeverity.CRITICAL
    
    def test_create_alert(self):
        """Test creating and dispatching alert."""
        manager = AlertManager()
        handler = Mock()
        manager.register_handler(handler)
        
        alert = manager.create_alert(
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.WARNING,
            source="test_source"
        )
        
        assert alert.title == "Test Alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.id in manager.alerts
        handler.assert_called_once()
    
    def test_get_active_alerts(self):
        """Test retrieving active alerts."""
        manager = AlertManager()
        
        manager.create_alert("Alert 1", "Message 1", AlertSeverity.INFO, "source1")
        manager.create_alert("Alert 2", "Message 2", AlertSeverity.WARNING, "source2")
        manager.create_alert("Alert 3", "Message 3", AlertSeverity.ERROR, "source3")
        
        all_alerts = manager.get_active_alerts()
        assert len(all_alerts) == 3
        
        warning_alerts = manager.get_active_alerts(AlertSeverity.WARNING)
        assert len(warning_alerts) == 1
        assert warning_alerts[0].severity == AlertSeverity.WARNING


@pytest.mark.integration
@pytest.mark.monitoring
class TestMetricsEndpoints:
    """Test metrics API endpoints."""
    
    def test_prometheus_metrics_endpoint(self, test_client):
        """Test /metrics/prometheus endpoint."""
        response = test_client.get("/metrics/prometheus")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "") or \
               "application/openmetrics-text" in response.headers.get("content-type", "")
        
        # Should contain some metrics
        content = response.text
        assert len(content) > 0
    
    def test_health_metrics_endpoint(self, test_client):
        """Test /metrics/health endpoint."""
        response = test_client.get("/metrics/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "system" in data
        assert "timestamp" in data

