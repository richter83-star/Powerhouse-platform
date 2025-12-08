
"""
AI Quality API Routes
Endpoints for model versioning, quality metrics, and explainability
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from core.ai_quality import (
    get_versioning_system,
    get_metrics_collector,
    get_data_manager,
    get_explainability_system
)

router = APIRouter(prefix="/ai-quality", tags=["ai-quality"])

# Pydantic models for request/response
class VersionRegistration(BaseModel):
    model_id: str
    version: str
    metadata: Dict[str, Any]
    model_path: Optional[str] = None

class MetricUpdate(BaseModel):
    model_id: str
    version: str
    metrics: Dict[str, float]

class ABTestCreate(BaseModel):
    test_id: str
    model_id: str
    version_a: str
    version_b: str
    traffic_split: float = 0.5
    metrics_to_track: List[str] = ["accuracy", "latency"]

class ABTestResult(BaseModel):
    test_id: str
    version: str
    metrics: Dict[str, float]

class DatasetRegistration(BaseModel):
    dataset_id: str
    version: str
    metadata: Dict[str, Any]
    data_path: Optional[str] = None
    parent_version: Optional[str] = None

class QualityCheckRequest(BaseModel):
    dataset_id: str
    version: str
    data_sample: List[Dict[str, Any]]

class MetricRecord(BaseModel):
    name: str
    value: float
    tags: Optional[Dict[str, str]] = None

class ExplanationRequest(BaseModel):
    model_id: str
    input_data: Dict[str, Any]
    prediction: Any
    method: str = "feature_importance"

# ============================================================================
# MODEL VERSIONING ENDPOINTS
# ============================================================================

@router.post("/models/versions")
async def register_model_version(data: VersionRegistration):
    """Register a new model version"""
    try:
        system = get_versioning_system()
        version = await system.register_version(
            data.model_id,
            data.version,
            data.metadata,
            data.model_path
        )
        return {"success": True, "version": version.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/versions")
async def list_model_versions(model_id: str):
    """List all versions for a model"""
    try:
        system = get_versioning_system()
        versions = await system.list_versions(model_id)
        return {
            "model_id": model_id,
            "versions": [v.to_dict() for v in versions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/versions/{version}")
async def get_model_version(model_id: str, version: str):
    """Get a specific model version"""
    try:
        system = get_versioning_system()
        version_obj = await system.get_version(model_id, version)
        if not version_obj:
            raise HTTPException(status_code=404, detail="Version not found")
        return version_obj.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_id}/versions/{version}/activate")
async def activate_version(model_id: str, version: str):
    """Set a version as active"""
    try:
        system = get_versioning_system()
        success = await system.set_active_version(model_id, version)
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        return {"success": True, "active_version": version}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_id}/versions/{version}/rollback")
async def rollback_version(model_id: str, version: str):
    """Rollback to a previous version"""
    try:
        system = get_versioning_system()
        success = await system.rollback_version(model_id, version)
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        return {"success": True, "rolled_back_to": version}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/models/versions/metrics")
async def update_version_metrics(data: MetricUpdate):
    """Update metrics for a model version"""
    try:
        system = get_versioning_system()
        await system.update_metrics(data.model_id, data.version, data.metrics)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@router.post("/ab-tests")
async def create_ab_test(data: ABTestCreate):
    """Create a new A/B test"""
    try:
        system = get_versioning_system()
        test = await system.create_ab_test(
            data.test_id,
            data.model_id,
            data.version_a,
            data.version_b,
            data.traffic_split,
            data.metrics_to_track
        )
        return {"success": True, "test": test}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ab-tests/results")
async def record_ab_test_result(data: ABTestResult):
    """Record results for an A/B test"""
    try:
        system = get_versioning_system()
        await system.record_ab_result(
            data.test_id,
            data.version,
            data.metrics
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ab-tests/{test_id}/summary")
async def get_ab_test_summary(test_id: str):
    """Get summary of an A/B test"""
    try:
        system = get_versioning_system()
        summary = await system.get_ab_test_summary(test_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Test not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ab-tests/{test_id}/conclude")
async def conclude_ab_test(test_id: str, winner: str = Body(..., embed=True)):
    """Conclude an A/B test and promote winner"""
    try:
        system = get_versioning_system()
        success = await system.conclude_ab_test(test_id, winner)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return {"success": True, "winner": winner}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# QUALITY METRICS ENDPOINTS
# ============================================================================

@router.post("/metrics")
async def record_metric(data: MetricRecord):
    """Record a single metric"""
    try:
        collector = get_metrics_collector()
        await collector.record_metric(data.name, data.value, data.tags)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/batch")
async def record_metrics_batch(metrics: List[MetricRecord]):
    """Record multiple metrics at once"""
    try:
        collector = get_metrics_collector()
        metrics_data = [
            {"name": m.name, "value": m.value, "tags": m.tags}
            for m in metrics
        ]
        await collector.record_batch(metrics_data)
        return {"success": True, "count": len(metrics)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{name}/stats")
async def get_metric_stats(name: str, time_range_minutes: Optional[int] = None):
    """Get statistical summary for a metric"""
    try:
        collector = get_metrics_collector()
        stats = await collector.get_metric_stats(name, time_range_minutes)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{name}/trends")
async def get_metric_trends(
    name: str,
    interval_minutes: int = 5,
    periods: int = 12
):
    """Get metric trends over time"""
    try:
        collector = get_metrics_collector()
        trends = await collector.get_trends(name, interval_minutes, periods)
        return {"metric": name, "trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{name}/anomalies")
async def get_metric_anomalies(name: str, threshold: float = 2.0):
    """Detect anomalies in metrics"""
    try:
        collector = get_metrics_collector()
        anomalies = await collector.get_anomalies(name, threshold)
        return {"metric": name, "anomalies": anomalies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/quality-score")
async def get_quality_score(model_id: str, time_range_minutes: int = 60):
    """Get overall quality score for a model"""
    try:
        collector = get_metrics_collector()
        score = await collector.get_quality_score(model_id, time_range_minutes)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/compare")
async def compare_models(
    model_ids: List[str] = Body(...),
    metrics: List[str] = Body(...),
    time_range_minutes: int = Body(60)
):
    """Compare multiple models across metrics"""
    try:
        collector = get_metrics_collector()
        comparison = await collector.compare_models(
            model_ids,
            metrics,
            time_range_minutes
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TRAINING DATA MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/datasets")
async def register_dataset(data: DatasetRegistration):
    """Register a new dataset version"""
    try:
        manager = get_data_manager()
        dataset = await manager.register_dataset(
            data.dataset_id,
            data.version,
            data.metadata,
            data.data_path,
            data.parent_version
        )
        return {"success": True, "dataset": dataset.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets")
async def list_datasets():
    """List all datasets"""
    try:
        manager = get_data_manager()
        datasets = await manager.list_datasets()
        return {"datasets": datasets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, version: Optional[str] = None):
    """Get a dataset (latest or specific version)"""
    try:
        manager = get_data_manager()
        dataset = await manager.get_dataset(dataset_id, version)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/datasets/quality-check")
async def run_quality_check(data: QualityCheckRequest):
    """Run quality checks on a dataset"""
    try:
        manager = get_data_manager()
        result = await manager.run_quality_checks(
            data.dataset_id,
            data.version,
            data.data_sample
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets/{dataset_id}/lineage")
async def get_dataset_lineage(dataset_id: str):
    """Get the lineage/history of a dataset"""
    try:
        manager = get_data_manager()
        lineage = await manager.get_data_lineage(dataset_id)
        return {"dataset_id": dataset_id, "lineage": lineage}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/datasets/{dataset_id}/compare")
async def compare_dataset_versions(
    dataset_id: str,
    version_a: str = Body(...),
    version_b: str = Body(...)
):
    """Compare two versions of a dataset"""
    try:
        manager = get_data_manager()
        comparison = await manager.compare_versions(dataset_id, version_a, version_b)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EXPLAINABILITY ENDPOINTS
# ============================================================================

@router.post("/explain")
async def explain_prediction(data: ExplanationRequest):
    """Generate an explanation for a prediction"""
    try:
        explainer = get_explainability_system()
        explanation = await explainer.explain_prediction(
            data.model_id,
            data.input_data,
            data.prediction,
            data.method
        )
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/feature-importance")
async def get_feature_importance(model_id: str):
    """Get aggregated feature importance for a model"""
    try:
        explainer = get_explainability_system()
        importance = await explainer.get_feature_importance(model_id)
        return {"model_id": model_id, "feature_importance": importance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/explanations")
async def get_explanation_history(model_id: str, limit: int = 10):
    """Get recent explanations for a model"""
    try:
        explainer = get_explainability_system()
        history = await explainer.get_explanation_history(model_id, limit)
        return {"model_id": model_id, "explanations": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/decision-patterns")
async def analyze_decision_patterns(model_id: str):
    """Analyze patterns in model decisions"""
    try:
        explainer = get_explainability_system()
        patterns = await explainer.analyze_decision_patterns(model_id)
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SYSTEM STATS ENDPOINTS
# ============================================================================

@router.get("/stats")
async def get_ai_quality_stats():
    """Get overall AI quality system statistics"""
    try:
        versioning = get_versioning_system()
        metrics = get_metrics_collector()
        data_mgr = get_data_manager()
        explainer = get_explainability_system()
        
        return {
            "versioning": versioning.get_stats(),
            "metrics": metrics.get_stats(),
            "training_data": data_mgr.get_stats(),
            "explainability": explainer.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
