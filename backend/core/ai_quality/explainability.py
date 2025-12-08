
"""
Model Explainability System
Provides insights into model decisions and predictions
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
import asyncio

class ExplanationRecord:
    """Represents an explanation for a model decision"""
    def __init__(
        self,
        model_id: str,
        prediction: Any,
        explanation: Dict[str, Any],
        confidence: float
    ):
        self.model_id = model_id
        self.prediction = prediction
        self.explanation = explanation
        self.confidence = confidence
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "prediction": self.prediction,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }

class ModelExplainability:
    """Provides explainability features for AI models"""
    
    def __init__(self):
        self.explanations: Dict[str, List[ExplanationRecord]] = defaultdict(list)
        self.feature_importance: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._lock = asyncio.Lock()
    
    async def explain_prediction(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        prediction: Any,
        method: str = "feature_importance"
    ) -> Dict[str, Any]:
        """Generate an explanation for a prediction"""
        
        if method == "feature_importance":
            explanation = await self._feature_importance_explanation(
                model_id, input_data, prediction
            )
        elif method == "counterfactual":
            explanation = await self._counterfactual_explanation(
                model_id, input_data, prediction
            )
        elif method == "attention":
            explanation = await self._attention_explanation(
                model_id, input_data, prediction
            )
        else:
            explanation = {"method": "unknown", "details": {}}
        
        # Calculate confidence score
        confidence = self._calculate_confidence(input_data, prediction)
        
        # Record the explanation
        record = ExplanationRecord(model_id, prediction, explanation, confidence)
        async with self._lock:
            self.explanations[model_id].append(record)
            # Keep only last 1000 explanations per model
            if len(self.explanations[model_id]) > 1000:
                self.explanations[model_id] = self.explanations[model_id][-1000:]
        
        return {
            "model_id": model_id,
            "prediction": prediction,
            "explanation": explanation,
            "confidence": confidence,
            "timestamp": record.timestamp.isoformat()
        }
    
    async def _feature_importance_explanation(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        prediction: Any
    ) -> Dict[str, Any]:
        """Generate feature importance explanation"""
        # Simulate feature importance calculation
        # In a real system, this would use SHAP, LIME, or similar
        
        features = {}
        total_importance = 0
        
        for key, value in input_data.items():
            # Simulate importance score based on value characteristics
            if isinstance(value, (int, float)):
                importance = abs(float(value)) * 0.1
            elif isinstance(value, str):
                importance = len(value) * 0.01
            else:
                importance = 0.5
            
            features[key] = min(1.0, importance)
            total_importance += features[key]
        
        # Normalize
        if total_importance > 0:
            features = {k: v / total_importance for k, v in features.items()}
        
        # Update global feature importance for this model
        async with self._lock:
            for feature, importance in features.items():
                if feature in self.feature_importance[model_id]:
                    # Moving average
                    self.feature_importance[model_id][feature] = (
                        self.feature_importance[model_id][feature] * 0.9 +
                        importance * 0.1
                    )
                else:
                    self.feature_importance[model_id][feature] = importance
        
        return {
            "method": "feature_importance",
            "features": dict(sorted(features.items(), key=lambda x: x[1], reverse=True)),
            "top_features": list(sorted(features.items(), key=lambda x: x[1], reverse=True))[:5]
        }
    
    async def _counterfactual_explanation(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        prediction: Any
    ) -> Dict[str, Any]:
        """Generate counterfactual explanation"""
        # Simulate counterfactual generation
        counterfactuals = []
        
        for key in list(input_data.keys())[:3]:  # Top 3 features
            counterfactual = input_data.copy()
            # Suggest a change
            if isinstance(input_data[key], (int, float)):
                counterfactual[key] = input_data[key] * 1.5
                change_desc = f"Increase {key} by 50%"
            elif isinstance(input_data[key], str):
                counterfactual[key] = input_data[key] + " (enhanced)"
                change_desc = f"Enhance {key}"
            else:
                continue
            
            counterfactuals.append({
                "change": change_desc,
                "feature": key,
                "original_value": input_data[key],
                "suggested_value": counterfactual[key],
                "expected_impact": "positive"
            })
        
        return {
            "method": "counterfactual",
            "counterfactuals": counterfactuals,
            "explanation": "These changes could lead to a different prediction"
        }
    
    async def _attention_explanation(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        prediction: Any
    ) -> Dict[str, Any]:
        """Generate attention-based explanation"""
        # Simulate attention weights
        attention_weights = {}
        
        for key in input_data.keys():
            # Simulate attention based on data type and value
            if isinstance(input_data[key], str):
                attention_weights[key] = min(1.0, len(input_data[key]) / 100)
            else:
                attention_weights[key] = 0.5
        
        # Normalize
        total = sum(attention_weights.values())
        if total > 0:
            attention_weights = {k: v / total for k, v in attention_weights.items()}
        
        return {
            "method": "attention",
            "attention_weights": dict(sorted(attention_weights.items(), key=lambda x: x[1], reverse=True)),
            "explanation": "These features received the most attention during prediction"
        }
    
    def _calculate_confidence(self, input_data: Dict[str, Any], prediction: Any) -> float:
        """Calculate confidence score for a prediction"""
        # Simulate confidence calculation
        # In a real system, this would come from the model
        
        # Base confidence on input completeness
        completeness = sum(
            1 for v in input_data.values()
            if v is not None and v != ""
        ) / len(input_data) if input_data else 0
        
        # Add some randomness to simulate real confidence
        import random
        confidence = completeness * 0.7 + random.uniform(0.2, 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    async def get_feature_importance(self, model_id: str) -> Dict[str, float]:
        """Get aggregated feature importance for a model"""
        async with self._lock:
            return dict(self.feature_importance.get(model_id, {}))
    
    async def get_explanation_history(
        self,
        model_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent explanations for a model"""
        async with self._lock:
            explanations = self.explanations.get(model_id, [])
            return [e.to_dict() for e in explanations[-limit:]]
    
    async def analyze_decision_patterns(
        self,
        model_id: str
    ) -> Dict[str, Any]:
        """Analyze patterns in model decisions"""
        async with self._lock:
            explanations = self.explanations.get(model_id, [])
            
            if not explanations:
                return {"error": "No explanations found for this model"}
            
            # Calculate average confidence
            avg_confidence = sum(e.confidence for e in explanations) / len(explanations)
            
            # Count explanation methods used
            methods_used = defaultdict(int)
            for e in explanations:
                method = e.explanation.get("method", "unknown")
                methods_used[method] += 1
            
            # Get most important features overall
            top_features = dict(
                sorted(
                    self.feature_importance[model_id].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
            
            return {
                "model_id": model_id,
                "total_explanations": len(explanations),
                "average_confidence": avg_confidence,
                "methods_used": dict(methods_used),
                "top_features": top_features,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall explainability statistics"""
        total_explanations = sum(len(exps) for exps in self.explanations.values())
        models_with_explanations = len(self.explanations)
        
        return {
            "models_with_explanations": models_with_explanations,
            "total_explanations": total_explanations,
            "explanation_methods": [
                "feature_importance",
                "counterfactual",
                "attention"
            ]
        }

# Global instance
_explainability_system = None

def get_explainability_system() -> ModelExplainability:
    """Get or create the global explainability system instance"""
    global _explainability_system
    if _explainability_system is None:
        _explainability_system = ModelExplainability()
    return _explainability_system
