
"""
API Routes for Forecasting Engine

Provides REST API endpoints for:
- Forecasting metrics
- Pattern detection
- System state prediction
- Goal management
- Comprehensive reports
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field

from utils.logging import get_logger
from core.forecasting_engine import ForecastingEngine
from core.time_series_forecaster import ForecastMethod
from core.pattern_recognizer import PatternType
from core.proactive_goal_setter import GoalType, GoalPriority, GoalStatus

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/forecasting", tags=["forecasting"])

# Global forecasting engine instance (will be initialized in main app)
forecasting_engine: Optional[ForecastingEngine] = None


def get_forecasting_engine() -> ForecastingEngine:
    """Get the global forecasting engine instance."""
    if forecasting_engine is None:
        raise HTTPException(status_code=503, detail="Forecasting engine not initialized")
    return forecasting_engine


def initialize_forecasting_engine(config: Optional[Dict[str, Any]] = None):
    """Initialize the global forecasting engine."""
    global forecasting_engine
    forecasting_engine = ForecastingEngine(config)
    forecasting_engine.start()
    logger.info("Forecasting engine initialized and started")


# Pydantic models for request/response
class MetricDataPoint(BaseModel):
    metric_name: str
    value: float
    timestamp: Optional[str] = None


class EventData(BaseModel):
    event_type: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ForecastRequest(BaseModel):
    metric_name: str
    method: str = "ensemble"
    horizon: int = Field(24, gt=0, le=168)  # 1 hour to 1 week
    parameters: Optional[Dict[str, Any]] = None


class PredictionRequest(BaseModel):
    current_metrics: Optional[Dict[str, float]] = None
    horizon_hours: int = Field(24, gt=0, le=168)


class GoalUpdate(BaseModel):
    progress: float = Field(..., ge=0.0, le=1.0)
    current_value: Optional[float] = None


# API Endpoints

@router.get("/health")
async def health_check():
    """Check forecasting engine health."""
    try:
        engine = get_forecasting_engine()
        stats = engine.get_statistics()
        return {
            "status": "healthy",
            "running": stats["running"],
            "statistics": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/metrics")
async def add_metric_data(data: MetricDataPoint):
    """Add a metric data point for forecasting."""
    try:
        engine = get_forecasting_engine()
        
        timestamp = None
        if data.timestamp:
            timestamp = datetime.fromisoformat(data.timestamp)
        
        engine.add_metric_data(data.metric_name, data.value, timestamp)
        
        return {
            "status": "success",
            "message": f"Added data point for {data.metric_name}"
        }
    except Exception as e:
        logger.error(f"Error adding metric data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/batch")
async def add_batch_metric_data(data: List[MetricDataPoint]):
    """Add multiple metric data points."""
    try:
        engine = get_forecasting_engine()
        
        for point in data:
            timestamp = None
            if point.timestamp:
                timestamp = datetime.fromisoformat(point.timestamp)
            engine.add_metric_data(point.metric_name, point.value, timestamp)
        
        return {
            "status": "success",
            "message": f"Added {len(data)} data points"
        }
    except Exception as e:
        logger.error(f"Error adding batch metric data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events")
async def add_event(data: EventData):
    """Add an event for pattern recognition."""
    try:
        engine = get_forecasting_engine()
        
        timestamp = None
        if data.timestamp:
            timestamp = datetime.fromisoformat(data.timestamp)
        
        engine.add_event(data.event_type, timestamp, data.metadata)
        
        return {
            "status": "success",
            "message": f"Added event: {data.event_type}"
        }
    except Exception as e:
        logger.error(f"Error adding event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast")
async def generate_forecast(request: ForecastRequest):
    """Generate a forecast for a metric."""
    try:
        engine = get_forecasting_engine()
        
        # Parse method
        try:
            method = ForecastMethod(request.method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid forecast method: {request.method}. "
                       f"Valid options: {[m.value for m in ForecastMethod]}"
            )
        
        # Generate forecast
        forecast = engine.forecast_metric(
            request.metric_name,
            method,
            request.horizon,
            **(request.parameters or {})
        )
        
        return {
            "status": "success",
            "forecast": forecast.to_dict()
        }
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def get_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type")
):
    """Get detected patterns."""
    try:
        engine = get_forecasting_engine()
        
        if pattern_type:
            try:
                pt = PatternType(pattern_type.lower())
                patterns = engine.get_patterns(pt)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid pattern type: {pattern_type}"
                )
        else:
            patterns = engine.get_patterns()
        
        return {
            "status": "success",
            "count": len(patterns),
            "patterns": [p.to_dict() for p in patterns]
        }
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/analyze")
async def analyze_patterns():
    """Trigger pattern analysis."""
    try:
        engine = get_forecasting_engine()
        patterns = engine.detect_patterns()
        
        return {
            "status": "success",
            "count": len(patterns),
            "patterns": [p.to_dict() for p in patterns]
        }
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def predict_system_state(request: PredictionRequest):
    """Predict future system state."""
    try:
        engine = get_forecasting_engine()
        
        prediction = engine.predict_system_state(
            request.current_metrics,
            request.horizon_hours
        )
        
        return {
            "status": "success",
            "prediction": prediction.to_dict()
        }
    except Exception as e:
        logger.error(f"Error predicting system state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goals/analyze")
async def analyze_and_set_goals(request: PredictionRequest):
    """Analyze system and set proactive goals."""
    try:
        engine = get_forecasting_engine()
        
        goals = engine.analyze_and_set_goals(
            request.current_metrics,
            request.horizon_hours
        )
        
        return {
            "status": "success",
            "count": len(goals),
            "goals": [g.to_dict() for g in goals]
        }
    except Exception as e:
        logger.error(f"Error analyzing and setting goals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals")
async def get_goals(
    status: Optional[str] = Query(None, description="Filter by status"),
    goal_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority")
):
    """Get goals with optional filters."""
    try:
        engine = get_forecasting_engine()
        goals = engine.get_active_goals()
        
        # Apply filters
        if status:
            try:
                status_enum = GoalStatus(status.lower())
                goals = [g for g in goals if g.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if goal_type:
            try:
                type_enum = GoalType(goal_type.lower())
                goals = [g for g in goals if g.goal_type == type_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid goal type: {goal_type}")
        
        if priority:
            try:
                priority_enum = GoalPriority(priority.lower())
                goals = [g for g in goals if g.priority == priority_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
        
        return {
            "status": "success",
            "count": len(goals),
            "goals": [g.to_dict() for g in goals]
        }
    except Exception as e:
        logger.error(f"Error getting goals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str = Path(..., description="Goal ID")):
    """Get a specific goal."""
    try:
        engine = get_forecasting_engine()
        goal = engine.get_goal(goal_id)
        
        if not goal:
            raise HTTPException(status_code=404, detail=f"Goal not found: {goal_id}")
        
        return {
            "status": "success",
            "goal": goal.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: str = Path(..., description="Goal ID"),
    update: GoalUpdate = Body(...)
):
    """Update progress on a goal."""
    try:
        engine = get_forecasting_engine()
        
        engine.update_goal_progress(goal_id, update.progress, update.current_value)
        
        goal = engine.get_goal(goal_id)
        
        return {
            "status": "success",
            "message": f"Updated progress for goal {goal_id}",
            "goal": goal.to_dict() if goal else None
        }
    except Exception as e:
        logger.error(f"Error updating goal progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goals/{goal_id}/execute")
async def execute_goal_actions(goal_id: str = Path(..., description="Goal ID")):
    """Execute actions for a goal."""
    try:
        engine = get_forecasting_engine()
        
        executed_actions = engine.execute_goal_actions(goal_id)
        
        return {
            "status": "success",
            "goal_id": goal_id,
            "executed_actions": executed_actions
        }
    except Exception as e:
        logger.error(f"Error executing goal actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_comprehensive_report(
    include_metrics: bool = Query(True, description="Include current metrics in report")
):
    """Get comprehensive forecasting report."""
    try:
        engine = get_forecasting_engine()
        
        # Could fetch current metrics from performance monitor here
        current_metrics = None
        
        report = engine.get_comprehensive_report(current_metrics)
        
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """Get forecasting engine statistics."""
    try:
        engine = get_forecasting_engine()
        stats = engine.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_state():
    """Export complete forecasting engine state."""
    try:
        engine = get_forecasting_engine()
        state = engine.export_state()
        
        return {
            "status": "success",
            "state": state
        }
    except Exception as e:
        logger.error(f"Error exporting state: {e}")
        raise HTTPException(status_code=500, detail=str(e))
