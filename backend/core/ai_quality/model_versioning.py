
"""
Model Versioning System
Manages model versions, A/B testing, and rollback capabilities
"""
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from collections import defaultdict

class ModelVersion:
    """Represents a specific model version"""
    def __init__(
        self,
        model_id: str,
        version: str,
        metadata: Dict[str, Any],
        model_path: Optional[str] = None
    ):
        self.model_id = model_id
        self.version = version
        self.metadata = metadata
        self.model_path = model_path
        self.created_at = datetime.now().isoformat()
        self.metrics: Dict[str, float] = {}
        self.status = "active"
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "version": self.version,
            "metadata": self.metadata,
            "model_path": self.model_path,
            "created_at": self.created_at,
            "metrics": self.metrics,
            "status": self.status
        }

class ModelVersioningSystem:
    """Manages model versions with A/B testing capabilities"""
    
    def __init__(self, storage_path: str = "./data/model_versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.versions: Dict[str, List[ModelVersion]] = defaultdict(list)
        self.active_versions: Dict[str, str] = {}  # model_id -> version
        self.ab_tests: Dict[str, Dict] = {}
        self._load_metadata()
        
    def _load_metadata(self):
        """Load versioning metadata from disk"""
        metadata_file = self.storage_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                self.active_versions = data.get("active_versions", {})
                
                # Reconstruct versions
                for model_id, versions in data.get("versions", {}).items():
                    for v_data in versions:
                        version = ModelVersion(
                            model_id=v_data["model_id"],
                            version=v_data["version"],
                            metadata=v_data["metadata"],
                            model_path=v_data.get("model_path")
                        )
                        version.created_at = v_data["created_at"]
                        version.metrics = v_data.get("metrics", {})
                        version.status = v_data.get("status", "active")
                        self.versions[model_id].append(version)
                        
                self.ab_tests = data.get("ab_tests", {})
    
    def _save_metadata(self):
        """Save versioning metadata to disk"""
        data = {
            "active_versions": self.active_versions,
            "versions": {
                model_id: [v.to_dict() for v in versions]
                for model_id, versions in self.versions.items()
            },
            "ab_tests": self.ab_tests
        }
        
        metadata_file = self.storage_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def register_version(
        self,
        model_id: str,
        version: str,
        metadata: Dict[str, Any],
        model_path: Optional[str] = None
    ) -> ModelVersion:
        """Register a new model version"""
        model_version = ModelVersion(model_id, version, metadata, model_path)
        self.versions[model_id].append(model_version)
        
        # If this is the first version, make it active
        if model_id not in self.active_versions:
            self.active_versions[model_id] = version
            
        self._save_metadata()
        return model_version
    
    async def get_version(self, model_id: str, version: str) -> Optional[ModelVersion]:
        """Get a specific model version"""
        for v in self.versions.get(model_id, []):
            if v.version == version:
                return v
        return None
    
    async def list_versions(self, model_id: str) -> List[ModelVersion]:
        """List all versions for a model"""
        return self.versions.get(model_id, [])
    
    async def set_active_version(self, model_id: str, version: str) -> bool:
        """Set the active version for a model"""
        version_obj = await self.get_version(model_id, version)
        if version_obj:
            self.active_versions[model_id] = version
            self._save_metadata()
            return True
        return False
    
    async def get_active_version(self, model_id: str) -> Optional[ModelVersion]:
        """Get the active version for a model"""
        version = self.active_versions.get(model_id)
        if version:
            return await self.get_version(model_id, version)
        return None
    
    async def update_metrics(self, model_id: str, version: str, metrics: Dict[str, float]):
        """Update metrics for a model version"""
        version_obj = await self.get_version(model_id, version)
        if version_obj:
            version_obj.metrics.update(metrics)
            self._save_metadata()
    
    async def create_ab_test(
        self,
        test_id: str,
        model_id: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5,
        metrics_to_track: List[str] = None
    ) -> Dict[str, Any]:
        """Create an A/B test between two model versions"""
        if metrics_to_track is None:
            metrics_to_track = ["accuracy", "latency", "success_rate"]
            
        ab_test = {
            "test_id": test_id,
            "model_id": model_id,
            "version_a": version_a,
            "version_b": version_b,
            "traffic_split": traffic_split,
            "metrics_to_track": metrics_to_track,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "results": {
                "version_a": defaultdict(list),
                "version_b": defaultdict(list)
            }
        }
        
        self.ab_tests[test_id] = ab_test
        self._save_metadata()
        return ab_test
    
    async def record_ab_result(
        self,
        test_id: str,
        version: str,
        metrics: Dict[str, float]
    ):
        """Record results for an A/B test"""
        if test_id in self.ab_tests:
            test = self.ab_tests[test_id]
            version_key = "version_a" if version == test["version_a"] else "version_b"
            
            for metric, value in metrics.items():
                test["results"][version_key][metric].append(value)
                
            self._save_metadata()
    
    async def get_ab_test_summary(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for an A/B test"""
        if test_id not in self.ab_tests:
            return None
            
        test = self.ab_tests[test_id]
        summary = {
            "test_id": test_id,
            "model_id": test["model_id"],
            "version_a": test["version_a"],
            "version_b": test["version_b"],
            "status": test["status"],
            "created_at": test["created_at"],
            "comparison": {}
        }
        
        # Calculate average metrics for each version
        for metric in test["metrics_to_track"]:
            a_values = test["results"]["version_a"].get(metric, [])
            b_values = test["results"]["version_b"].get(metric, [])
            
            a_avg = sum(a_values) / len(a_values) if a_values else 0
            b_avg = sum(b_values) / len(b_values) if b_values else 0
            
            summary["comparison"][metric] = {
                "version_a_avg": a_avg,
                "version_b_avg": b_avg,
                "version_a_samples": len(a_values),
                "version_b_samples": len(b_values),
                "improvement": ((b_avg - a_avg) / a_avg * 100) if a_avg > 0 else 0
            }
        
        return summary
    
    async def conclude_ab_test(self, test_id: str, winner: str) -> bool:
        """Conclude an A/B test and promote the winner"""
        if test_id not in self.ab_tests:
            return False
            
        test = self.ab_tests[test_id]
        test["status"] = "concluded"
        test["winner"] = winner
        test["concluded_at"] = datetime.now().isoformat()
        
        # Set the winner as active version
        await self.set_active_version(test["model_id"], winner)
        self._save_metadata()
        return True
    
    async def rollback_version(self, model_id: str, target_version: str) -> bool:
        """Rollback to a previous version"""
        version_obj = await self.get_version(model_id, target_version)
        if version_obj:
            # Mark current version as rolled back
            current_version = self.active_versions.get(model_id)
            if current_version:
                current = await self.get_version(model_id, current_version)
                if current:
                    current.status = "rolled_back"
            
            # Activate target version
            version_obj.status = "active"
            self.active_versions[model_id] = target_version
            self._save_metadata()
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall versioning statistics"""
        total_versions = sum(len(versions) for versions in self.versions.values())
        active_ab_tests = sum(1 for test in self.ab_tests.values() if test["status"] == "active")
        
        return {
            "total_models": len(self.versions),
            "total_versions": total_versions,
            "active_ab_tests": active_ab_tests,
            "total_ab_tests": len(self.ab_tests)
        }

# Global instance
_versioning_system = None

def get_versioning_system() -> ModelVersioningSystem:
    """Get or create the global versioning system instance"""
    global _versioning_system
    if _versioning_system is None:
        _versioning_system = ModelVersioningSystem()
    return _versioning_system
