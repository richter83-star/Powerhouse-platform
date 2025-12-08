
"""
API routes for online learning module.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from core.online_learning import (
    get_model_updater,
    ModelType,
    LearningMetrics as CoreLearningMetrics
)
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/learning", tags=["learning"])


# Response models
class LearningMetricsResponse(BaseModel):
    """Learning metrics response."""
    total_updates: int
    successful_updates: int
    failed_updates: int
    avg_update_time_ms: float
    samples_processed: int
    current_model_score: float
    improvement_rate: float


class AgentPerformanceResponse(BaseModel):
    """Agent performance response."""
    agent_name: str
    success_rate: float
    avg_latency_ms: float
    total_executions: int


class ModelInfoResponse(BaseModel):
    """Model information response."""
    model_type: str
    update_count: int
    last_update: str
    performance_summary: dict


class PredictionRequest(BaseModel):
    """Request for agent selection prediction."""
    task_type: Optional[str] = None
    context: Optional[dict] = None
    top_k: int = Field(default=3, ge=1, le=10)


class PredictionResponse(BaseModel):
    """Agent selection prediction response."""
    recommendations: List[dict]
    model_score: float
    timestamp: str


# Endpoints

@router.get("/metrics", response_model=LearningMetricsResponse)
async def get_learning_metrics():
    """
    Get current learning metrics.
    
    Returns real-time metrics about the online learning process,
    including update counts, processing times, and model performance.
    """
    updater = get_model_updater()
    if not updater:
        raise HTTPException(
            status_code=503,
            detail="Model updater not available (Kafka may not be configured)"
        )
    
    metrics = updater.get_metrics()
    
    return LearningMetricsResponse(
        total_updates=metrics.get('total_updates', 0),
        successful_updates=metrics.get('successful_updates', 0),
        failed_updates=metrics.get('failed_updates', 0),
        avg_update_time_ms=metrics.get('avg_update_time_ms', 0.0),
        samples_processed=metrics.get('samples_processed', 0),
        current_model_score=metrics.get('current_model_score', 0.0),
        improvement_rate=metrics.get('improvement_rate', 0.0)
    )


@router.get("/agents/performance", response_model=List[AgentPerformanceResponse])
async def get_agent_performance():
    """
    Get performance metrics for all agents.
    
    Returns detailed performance statistics for each agent,
    including success rates and average latencies.
    """
    updater = get_model_updater()
    if not updater:
        raise HTTPException(
            status_code=503,
            detail="Model updater not available"
        )
    
    model = updater.get_model(ModelType.AGENT_SELECTION)
    if not model:
        return []
    
    performances = []
    for agent_name, stats in model.agent_stats.items():
        total = stats['successes'] + stats['failures']
        performances.append(
            AgentPerformanceResponse(
                agent_name=agent_name,
                success_rate=model.get_success_rate(agent_name),
                avg_latency_ms=model.get_avg_latency(agent_name),
                total_executions=total
            )
        )
    
    return performances


@router.get("/models/{model_type}", response_model=ModelInfoResponse)
async def get_model_info(model_type: str):
    """
    Get information about a specific model.
    
    Args:
        model_type: Type of model (e.g., 'agent_selection')
    """
    updater = get_model_updater()
    if not updater:
        raise HTTPException(
            status_code=503,
            detail="Model updater not available"
        )
    
    try:
        mt = ModelType(model_type)
        model = updater.get_model(mt)
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model type '{model_type}' not found"
            )
        
        model_data = model.to_dict()
        
        return ModelInfoResponse(
            model_type=model_type,
            update_count=model_data.get('update_count', 0),
            last_update=model_data.get('last_update', ''),
            performance_summary={
                'total_agents': len(model_data.get('agent_stats', {})),
                'task_patterns': len(model_data.get('task_patterns', {}))
            }
        )
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type: {model_type}"
        )


@router.post("/predict/agent-selection", response_model=PredictionResponse)
async def predict_best_agent(request: PredictionRequest):
    """
    Predict the best agents for a given task.
    
    Uses the trained agent selection model to recommend the most
    suitable agents based on historical performance data.
    """
    updater = get_model_updater()
    if not updater:
        raise HTTPException(
            status_code=503,
            detail="Model updater not available"
        )
    
    try:
        predictions = updater.predict(
            ModelType.AGENT_SELECTION,
            task_type=request.task_type,
            context=request.context,
            top_k=request.top_k
        )
        
        recommendations = [
            {
                'agent_name': agent_name,
                'score': float(score),
                'rank': idx + 1
            }
            for idx, (agent_name, score) in enumerate(predictions)
        ]
        
        metrics = updater.get_metrics()
        
        return PredictionResponse(
            recommendations=recommendations,
            model_score=metrics.get('current_model_score', 0.0),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/models/save")
async def save_models():
    """
    Manually trigger model saving.
    
    Forces all models to be persisted to disk immediately.
    """
    updater = get_model_updater()
    if not updater:
        raise HTTPException(
            status_code=503,
            detail="Model updater not available"
        )
    
    try:
        updater._save_models()
        return {"status": "success", "message": "Models saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save models: {str(e)}"
        )


@router.get("/status")
async def get_updater_status():
    """
    Get the status of the model updater service.
    """
    updater = get_model_updater()
    if not updater:
        return {
            "status": "unavailable",
            "running": False,
            "message": "Kafka not configured or model updater not initialized"
        }
    
    return {
        "status": "running" if updater.running else "stopped",
        "running": updater.running,
        "kafka_topic": updater.kafka_topic,
        "batch_size": updater.batch_size,
        "models_loaded": list(updater.models.keys())
    }
