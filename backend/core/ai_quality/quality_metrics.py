
"""
Quality Metrics Collection System
Tracks comprehensive quality metrics for AI models and agents
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import asyncio
import statistics

class MetricPoint:
    """Represents a single metric measurement"""
    def __init__(self, name: str, value: float, tags: Dict[str, str] = None):
        self.name = name
        self.value = value
        self.tags = tags or {}
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat()
        }

class QualityMetricsCollector:
    """Collects and aggregates quality metrics for AI systems"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.aggregates: Dict[str, Dict] = defaultdict(dict)
        self._lock = asyncio.Lock()
        
        # Standard quality dimensions
        self.quality_dimensions = {
            "accuracy": "Correctness of outputs",
            "latency": "Response time (ms)",
            "throughput": "Requests per second",
            "error_rate": "Percentage of failed requests",
            "hallucination_rate": "Percentage of hallucinated outputs",
            "relevance_score": "Relevance of responses (0-1)",
            "coherence_score": "Logical coherence (0-1)",
            "completeness_score": "Response completeness (0-1)",
            "toxicity_score": "Toxicity level (0-1)",
            "bias_score": "Bias detection score (0-1)",
            "resource_usage": "CPU/Memory utilization",
            "cost_per_request": "Cost in credits/dollars"
        }
    
    async def record_metric(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] = None
    ):
        """Record a single metric point"""
        async with self._lock:
            metric_point = MetricPoint(name, value, tags)
            self.metrics[name].append(metric_point)
            
            # Clean up old metrics
            await self._cleanup_old_metrics(name)
    
    async def record_batch(self, metrics: List[Dict[str, Any]]):
        """Record multiple metrics at once"""
        async with self._lock:
            for metric in metrics:
                metric_point = MetricPoint(
                    metric["name"],
                    metric["value"],
                    metric.get("tags")
                )
                self.metrics[metric["name"]].append(metric_point)
    
    async def _cleanup_old_metrics(self, metric_name: str):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        metrics_list = self.metrics[metric_name]
        
        while metrics_list and metrics_list[0].timestamp < cutoff_time:
            metrics_list.popleft()
    
    async def get_metric_stats(
        self,
        name: str,
        time_range_minutes: Optional[int] = None
    ) -> Dict[str, float]:
        """Get statistical summary for a metric"""
        async with self._lock:
            metrics_list = list(self.metrics[name])
            
            if time_range_minutes:
                cutoff = datetime.now() - timedelta(minutes=time_range_minutes)
                metrics_list = [m for m in metrics_list if m.timestamp >= cutoff]
            
            if not metrics_list:
                return {
                    "count": 0,
                    "mean": 0,
                    "median": 0,
                    "min": 0,
                    "max": 0,
                    "std_dev": 0
                }
            
            values = [m.value for m in metrics_list]
            
            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99)
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    async def get_quality_score(
        self,
        model_id: str,
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        """Calculate overall quality score for a model"""
        cutoff = datetime.now() - timedelta(minutes=time_range_minutes)
        
        # Collect relevant metrics
        quality_metrics = {}
        weights = {
            "accuracy": 0.3,
            "relevance_score": 0.2,
            "coherence_score": 0.15,
            "completeness_score": 0.15,
            "error_rate": -0.1,  # Negative weight
            "hallucination_rate": -0.1  # Negative weight
        }
        
        total_score = 0
        collected_metrics = {}
        
        for metric_name, weight in weights.items():
            stats = await self.get_metric_stats(metric_name, time_range_minutes)
            if stats["count"] > 0:
                value = stats["mean"]
                collected_metrics[metric_name] = value
                
                # Normalize and apply weight
                if weight > 0:
                    total_score += value * weight
                else:
                    # For negative metrics, subtract from 1 first
                    total_score += (1 - value) * abs(weight)
        
        # Normalize to 0-100 scale
        quality_score = min(100, max(0, total_score * 100))
        
        return {
            "model_id": model_id,
            "quality_score": quality_score,
            "time_range_minutes": time_range_minutes,
            "metrics": collected_metrics,
            "calculated_at": datetime.now().isoformat()
        }
    
    async def get_trends(
        self,
        name: str,
        interval_minutes: int = 5,
        periods: int = 12
    ) -> List[Dict[str, Any]]:
        """Get metric trends over time"""
        now = datetime.now()
        trends = []
        
        for i in range(periods):
            end_time = now - timedelta(minutes=i * interval_minutes)
            start_time = end_time - timedelta(minutes=interval_minutes)
            
            # Get metrics in this period
            async with self._lock:
                period_metrics = [
                    m for m in self.metrics[name]
                    if start_time <= m.timestamp < end_time
                ]
            
            if period_metrics:
                values = [m.value for m in period_metrics]
                avg_value = statistics.mean(values)
            else:
                avg_value = 0
            
            trends.append({
                "period": start_time.isoformat(),
                "value": avg_value,
                "count": len(period_metrics)
            })
        
        return list(reversed(trends))
    
    async def get_anomalies(
        self,
        name: str,
        threshold_std_devs: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics"""
        stats = await self.get_metric_stats(name)
        
        if stats["count"] < 10:
            return []
        
        mean = stats["mean"]
        std_dev = stats["std_dev"]
        threshold = threshold_std_devs * std_dev
        
        anomalies = []
        async with self._lock:
            for metric in self.metrics[name]:
                deviation = abs(metric.value - mean)
                if deviation > threshold:
                    anomalies.append({
                        "timestamp": metric.timestamp.isoformat(),
                        "value": metric.value,
                        "expected": mean,
                        "deviation": deviation,
                        "severity": "high" if deviation > 3 * std_dev else "medium"
                    })
        
        return anomalies[-50:]  # Return last 50 anomalies
    
    async def compare_models(
        self,
        model_ids: List[str],
        metrics: List[str],
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        """Compare multiple models across metrics"""
        comparison = {
            "models": model_ids,
            "metrics": {},
            "time_range_minutes": time_range_minutes
        }
        
        for metric_name in metrics:
            comparison["metrics"][metric_name] = {}
            
            for model_id in model_ids:
                # Filter metrics by model_id tag
                async with self._lock:
                    cutoff = datetime.now() - timedelta(minutes=time_range_minutes)
                    model_metrics = [
                        m for m in self.metrics[metric_name]
                        if m.tags.get("model_id") == model_id and m.timestamp >= cutoff
                    ]
                
                if model_metrics:
                    values = [m.value for m in model_metrics]
                    comparison["metrics"][metric_name][model_id] = {
                        "mean": statistics.mean(values),
                        "count": len(values)
                    }
                else:
                    comparison["metrics"][metric_name][model_id] = {
                        "mean": 0,
                        "count": 0
                    }
        
        return comparison
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall collector statistics"""
        total_metrics = sum(len(m) for m in self.metrics.values())
        
        return {
            "total_metric_types": len(self.metrics),
            "total_data_points": total_metrics,
            "retention_hours": self.retention_hours,
            "quality_dimensions": self.quality_dimensions
        }

# Global instance
_metrics_collector = None

def get_metrics_collector() -> QualityMetricsCollector:
    """Get or create the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = QualityMetricsCollector()
    return _metrics_collector
