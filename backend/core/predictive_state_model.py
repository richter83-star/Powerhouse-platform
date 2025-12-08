
"""
Predictive State Model

Estimates future system states based on:
- Historical performance data
- Detected patterns
- Resource usage trends
- Forecasted metrics

Provides predictions for:
- Future resource demands
- Potential bottlenecks
- System capacity needs
- Performance degradation risks
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from utils.logging import get_logger
from core.time_series_forecaster import TimeSeriesForecaster, ForecastResult, ForecastMethod
from core.pattern_recognizer import PatternRecognizer, Pattern, PatternType

logger = get_logger(__name__)


class SystemState(str, Enum):
    """Possible system states."""
    OPTIMAL = "optimal"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OVERLOADED = "overloaded"


class ResourceType(str, Enum):
    """Types of resources to track."""
    CPU = "cpu"
    MEMORY = "memory"
    API_CALLS = "api_calls"
    TOKEN_BUDGET = "token_budget"
    STORAGE = "storage"
    NETWORK = "network"


@dataclass
class ResourceDemand:
    """Predicted resource demand."""
    resource_type: ResourceType
    current_usage: float
    predicted_usage: float
    prediction_time: datetime
    confidence: float
    capacity: float
    utilization_percent: float
    will_exceed_capacity: bool
    time_to_capacity: Optional[timedelta] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "current_usage": self.current_usage,
            "predicted_usage": self.predicted_usage,
            "prediction_time": self.prediction_time.isoformat(),
            "confidence": self.confidence,
            "capacity": self.capacity,
            "utilization_percent": self.utilization_percent,
            "will_exceed_capacity": self.will_exceed_capacity,
            "time_to_capacity": self.time_to_capacity.total_seconds() if self.time_to_capacity else None
        }


@dataclass
class Bottleneck:
    """Predicted bottleneck."""
    bottleneck_id: str
    location: str  # Component or service name
    severity: str  # "low", "medium", "high", "critical"
    description: str
    predicted_time: datetime
    confidence: float
    affected_resources: List[ResourceType]
    mitigation_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bottleneck_id": self.bottleneck_id,
            "location": self.location,
            "severity": self.severity,
            "description": self.description,
            "predicted_time": self.predicted_time.isoformat(),
            "confidence": self.confidence,
            "affected_resources": [r.value for r in self.affected_resources],
            "mitigation_suggestions": self.mitigation_suggestions
        }


@dataclass
class SystemStatePrediction:
    """Complete system state prediction."""
    prediction_id: str
    current_state: SystemState
    predicted_state: SystemState
    prediction_horizon: timedelta
    prediction_time: datetime
    confidence: float
    resource_demands: List[ResourceDemand]
    predicted_bottlenecks: List[Bottleneck]
    risk_factors: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "current_state": self.current_state,
            "predicted_state": self.predicted_state,
            "prediction_horizon": self.prediction_horizon.total_seconds(),
            "prediction_time": self.prediction_time.isoformat(),
            "confidence": self.confidence,
            "resource_demands": [rd.to_dict() for rd in self.resource_demands],
            "predicted_bottlenecks": [b.to_dict() for b in self.predicted_bottlenecks],
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations
        }


class PredictiveStateModel:
    """
    Main predictive state modeling engine.
    
    Combines forecasting and pattern recognition to predict future system states.
    """
    
    def __init__(
        self,
        forecaster: TimeSeriesForecaster,
        pattern_recognizer: PatternRecognizer,
        config: Optional[Dict[str, Any]] = None
    ):
        self.forecaster = forecaster
        self.pattern_recognizer = pattern_recognizer
        self.config = config or {}
        
        # Resource capacities (can be configured)
        self.resource_capacities = self.config.get("resource_capacities", {
            ResourceType.CPU: 100.0,
            ResourceType.MEMORY: 100.0,
            ResourceType.API_CALLS: 10000.0,
            ResourceType.TOKEN_BUDGET: 1000000.0,
            ResourceType.STORAGE: 1000.0,
            ResourceType.NETWORK: 1000.0
        })
        
        # Thresholds for state determination
        self.thresholds = self.config.get("thresholds", {
            "optimal": 60.0,
            "healthy": 75.0,
            "degraded": 85.0,
            "critical": 95.0
        })
        
        logger.info("PredictiveStateModel initialized")
    
    def predict_system_state(
        self,
        horizon_hours: int = 24,
        current_metrics: Optional[Dict[str, float]] = None
    ) -> SystemStatePrediction:
        """
        Predict future system state.
        
        Args:
            horizon_hours: How far into the future to predict
            current_metrics: Current resource usage metrics
        
        Returns:
            SystemStatePrediction with detailed forecast
        """
        prediction_time = datetime.now()
        prediction_id = f"pred_{int(prediction_time.timestamp())}"
        
        # Get current state
        current_state = self._determine_current_state(current_metrics or {})
        
        # Predict resource demands
        resource_demands = self._predict_resource_demands(horizon_hours, current_metrics)
        
        # Identify potential bottlenecks
        bottlenecks = self._identify_bottlenecks(resource_demands)
        
        # Determine predicted state based on resource demands
        predicted_state = self._determine_future_state(resource_demands)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(resource_demands, bottlenecks)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            predicted_state, resource_demands, bottlenecks, risk_factors
        )
        
        # Calculate overall confidence
        confidence = self._calculate_overall_confidence(resource_demands)
        
        prediction = SystemStatePrediction(
            prediction_id=prediction_id,
            current_state=current_state,
            predicted_state=predicted_state,
            prediction_horizon=timedelta(hours=horizon_hours),
            prediction_time=prediction_time,
            confidence=confidence,
            resource_demands=resource_demands,
            predicted_bottlenecks=bottlenecks,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
        
        logger.info(
            f"Generated system state prediction: {current_state} -> {predicted_state} "
            f"(confidence: {confidence:.2f})"
        )
        
        return prediction
    
    def _determine_current_state(self, current_metrics: Dict[str, float]) -> SystemState:
        """Determine current system state from metrics."""
        if not current_metrics:
            return SystemState.HEALTHY
        
        # Calculate average utilization
        utilizations = []
        for resource_type, capacity in self.resource_capacities.items():
            metric_name = resource_type.value
            if metric_name in current_metrics:
                util = (current_metrics[metric_name] / capacity) * 100
                utilizations.append(util)
        
        if not utilizations:
            return SystemState.HEALTHY
        
        max_util = max(utilizations)
        
        if max_util < self.thresholds["optimal"]:
            return SystemState.OPTIMAL
        elif max_util < self.thresholds["healthy"]:
            return SystemState.HEALTHY
        elif max_util < self.thresholds["degraded"]:
            return SystemState.DEGRADED
        elif max_util < self.thresholds["critical"]:
            return SystemState.CRITICAL
        else:
            return SystemState.OVERLOADED
    
    def _predict_resource_demands(
        self,
        horizon_hours: int,
        current_metrics: Optional[Dict[str, float]]
    ) -> List[ResourceDemand]:
        """Predict future resource demands."""
        demands = []
        
        for resource_type, capacity in self.resource_capacities.items():
            metric_name = resource_type.value
            
            try:
                # Get forecast
                forecast = self.forecaster.forecast(
                    metric_name,
                    method=ForecastMethod.SARIMA,
                    horizon=horizon_hours
                )
                
                # Get current usage
                current_usage = current_metrics.get(metric_name, 0.0) if current_metrics else 0.0
                
                # Get predicted usage (average of forecast)
                predicted_usage = np.mean(forecast.predictions)
                
                # Calculate utilization
                utilization = (predicted_usage / capacity) * 100
                
                # Check if will exceed capacity
                will_exceed = any(p > capacity for p in forecast.predictions)
                
                # Calculate time to capacity if trending up
                time_to_capacity = None
                if will_exceed:
                    for i, pred in enumerate(forecast.predictions):
                        if pred > capacity:
                            time_to_capacity = timedelta(hours=i)
                            break
                
                demand = ResourceDemand(
                    resource_type=resource_type,
                    current_usage=current_usage,
                    predicted_usage=predicted_usage,
                    prediction_time=datetime.now() + timedelta(hours=horizon_hours),
                    confidence=0.8,  # From forecast
                    capacity=capacity,
                    utilization_percent=utilization,
                    will_exceed_capacity=will_exceed,
                    time_to_capacity=time_to_capacity
                )
                demands.append(demand)
                
            except Exception as e:
                logger.warning(f"Failed to predict demand for {metric_name}: {e}")
        
        return demands
    
    def _identify_bottlenecks(self, resource_demands: List[ResourceDemand]) -> List[Bottleneck]:
        """Identify potential bottlenecks from resource demands."""
        bottlenecks = []
        
        for demand in resource_demands:
            if demand.will_exceed_capacity:
                severity = "critical" if demand.utilization_percent > 95 else "high"
                
                # Generate mitigation suggestions
                suggestions = self._generate_mitigation_suggestions(demand)
                
                bottleneck = Bottleneck(
                    bottleneck_id=f"bottleneck_{demand.resource_type.value}",
                    location=demand.resource_type.value,
                    severity=severity,
                    description=f"{demand.resource_type.value} will exceed capacity",
                    predicted_time=demand.prediction_time,
                    confidence=demand.confidence,
                    affected_resources=[demand.resource_type],
                    mitigation_suggestions=suggestions
                )
                bottlenecks.append(bottleneck)
            
            elif demand.utilization_percent > 85:
                bottleneck = Bottleneck(
                    bottleneck_id=f"bottleneck_{demand.resource_type.value}",
                    location=demand.resource_type.value,
                    severity="medium",
                    description=f"{demand.resource_type.value} utilization will be high",
                    predicted_time=demand.prediction_time,
                    confidence=demand.confidence,
                    affected_resources=[demand.resource_type],
                    mitigation_suggestions=self._generate_mitigation_suggestions(demand)
                )
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def _generate_mitigation_suggestions(self, demand: ResourceDemand) -> List[str]:
        """Generate mitigation suggestions for a resource demand."""
        suggestions = []
        
        if demand.resource_type == ResourceType.API_CALLS:
            suggestions.append("Enable request caching to reduce API calls")
            suggestions.append("Implement rate limiting for non-critical operations")
            suggestions.append("Consider batch processing for API requests")
        
        elif demand.resource_type == ResourceType.TOKEN_BUDGET:
            suggestions.append("Use smaller models for simple tasks")
            suggestions.append("Implement response caching")
            suggestions.append("Optimize prompts to reduce token usage")
        
        elif demand.resource_type == ResourceType.CPU:
            suggestions.append("Scale horizontally by adding more instances")
            suggestions.append("Optimize compute-intensive operations")
            suggestions.append("Consider offloading to background workers")
        
        elif demand.resource_type == ResourceType.MEMORY:
            suggestions.append("Implement memory-efficient data structures")
            suggestions.append("Enable garbage collection tuning")
            suggestions.append("Consider scaling vertically or horizontally")
        
        else:
            suggestions.append(f"Monitor {demand.resource_type.value} usage closely")
            suggestions.append("Consider capacity planning and scaling")
        
        return suggestions
    
    def _determine_future_state(self, resource_demands: List[ResourceDemand]) -> SystemState:
        """Determine predicted future state from resource demands."""
        if not resource_demands:
            return SystemState.HEALTHY
        
        max_utilization = max(d.utilization_percent for d in resource_demands)
        
        if max_utilization < self.thresholds["optimal"]:
            return SystemState.OPTIMAL
        elif max_utilization < self.thresholds["healthy"]:
            return SystemState.HEALTHY
        elif max_utilization < self.thresholds["degraded"]:
            return SystemState.DEGRADED
        elif max_utilization < self.thresholds["critical"]:
            return SystemState.CRITICAL
        else:
            return SystemState.OVERLOADED
    
    def _identify_risk_factors(
        self,
        resource_demands: List[ResourceDemand],
        bottlenecks: List[Bottleneck]
    ) -> List[str]:
        """Identify risk factors in the prediction."""
        risks = []
        
        # Check for high resource utilization
        high_util_resources = [d for d in resource_demands if d.utilization_percent > 80]
        if high_util_resources:
            resources_str = ", ".join([d.resource_type.value for d in high_util_resources])
            risks.append(f"High utilization predicted for: {resources_str}")
        
        # Check for capacity exceeded
        exceeded = [d for d in resource_demands if d.will_exceed_capacity]
        if exceeded:
            resources_str = ", ".join([d.resource_type.value for d in exceeded])
            risks.append(f"Capacity will be exceeded for: {resources_str}")
        
        # Check for critical bottlenecks
        critical_bottlenecks = [b for b in bottlenecks if b.severity == "critical"]
        if critical_bottlenecks:
            risks.append(f"{len(critical_bottlenecks)} critical bottlenecks predicted")
        
        # Check patterns for concerning trends
        patterns = self.pattern_recognizer.get_all_patterns()
        spike_patterns = [p for p in patterns if p.pattern_type == PatternType.PERIODIC_SPIKE]
        if spike_patterns:
            risks.append("Recurring spike patterns detected - prepare for peak loads")
        
        return risks
    
    def _generate_recommendations(
        self,
        predicted_state: SystemState,
        resource_demands: List[ResourceDemand],
        bottlenecks: List[Bottleneck],
        risk_factors: List[str]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # State-based recommendations
        if predicted_state in [SystemState.CRITICAL, SystemState.OVERLOADED]:
            recommendations.append("URGENT: System capacity planning needed immediately")
            recommendations.append("Consider emergency scaling procedures")
        elif predicted_state == SystemState.DEGRADED:
            recommendations.append("Plan capacity upgrades in near term")
            recommendations.append("Review and optimize resource-intensive operations")
        
        # Resource-specific recommendations
        for demand in resource_demands:
            if demand.utilization_percent > 85:
                recommendations.append(
                    f"Monitor {demand.resource_type.value} closely - "
                    f"predicted {demand.utilization_percent:.1f}% utilization"
                )
        
        # Bottleneck-specific recommendations
        for bottleneck in bottlenecks:
            if bottleneck.severity in ["critical", "high"]:
                recommendations.extend(bottleneck.mitigation_suggestions[:2])
        
        # Pattern-based recommendations
        patterns = self.pattern_recognizer.get_all_patterns()
        recurring_tasks = [p for p in patterns if p.pattern_type == PatternType.RECURRING_TASK]
        if recurring_tasks:
            recommendations.append(
                f"Optimize {len(recurring_tasks)} recurring tasks to reduce baseline load"
            )
        
        # General recommendations
        if len(risk_factors) > 3:
            recommendations.append("Multiple risk factors detected - comprehensive review recommended")
        
        return recommendations
    
    def _calculate_overall_confidence(self, resource_demands: List[ResourceDemand]) -> float:
        """Calculate overall confidence in the prediction."""
        if not resource_demands:
            return 0.5
        
        confidences = [d.confidence for d in resource_demands]
        return float(np.mean(confidences))
    
    def get_capacity_report(self) -> Dict[str, Any]:
        """Get current capacity status report."""
        return {
            "resource_capacities": {k.value: v for k, v in self.resource_capacities.items()},
            "thresholds": self.thresholds,
            "timestamp": datetime.now().isoformat()
        }
