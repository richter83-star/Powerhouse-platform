
"""
Training Data Management System
Manages training datasets, validation, and quality control
"""
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict
import asyncio

class DatasetVersion:
    """Represents a versioned dataset"""
    def __init__(
        self,
        dataset_id: str,
        version: str,
        metadata: Dict[str, Any],
        data_path: Optional[str] = None
    ):
        self.dataset_id = dataset_id
        self.version = version
        self.metadata = metadata
        self.data_path = data_path
        self.created_at = datetime.now().isoformat()
        self.stats: Dict[str, Any] = {}
        self.quality_score = 0.0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "metadata": self.metadata,
            "data_path": self.data_path,
            "created_at": self.created_at,
            "stats": self.stats,
            "quality_score": self.quality_score
        }

class TrainingDataManager:
    """Manages training datasets with versioning and quality control"""
    
    def __init__(self, storage_path: str = "./data/training_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.datasets: Dict[str, List[DatasetVersion]] = defaultdict(list)
        self.data_lineage: Dict[str, List[str]] = defaultdict(list)
        self.quality_checks: Dict[str, List[Dict]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._load_metadata()
    
    def _load_metadata(self):
        """Load dataset metadata from disk"""
        metadata_file = self.storage_path / "datasets_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                
                # Reconstruct datasets
                for dataset_id, versions in data.get("datasets", {}).items():
                    for v_data in versions:
                        version = DatasetVersion(
                            dataset_id=v_data["dataset_id"],
                            version=v_data["version"],
                            metadata=v_data["metadata"],
                            data_path=v_data.get("data_path")
                        )
                        version.created_at = v_data["created_at"]
                        version.stats = v_data.get("stats", {})
                        version.quality_score = v_data.get("quality_score", 0.0)
                        self.datasets[dataset_id].append(version)
                
                self.data_lineage = data.get("data_lineage", {})
                self.quality_checks = data.get("quality_checks", {})
    
    def _save_metadata(self):
        """Save dataset metadata to disk"""
        data = {
            "datasets": {
                dataset_id: [v.to_dict() for v in versions]
                for dataset_id, versions in self.datasets.items()
            },
            "data_lineage": self.data_lineage,
            "quality_checks": self.quality_checks
        }
        
        metadata_file = self.storage_path / "datasets_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def register_dataset(
        self,
        dataset_id: str,
        version: str,
        metadata: Dict[str, Any],
        data_path: Optional[str] = None,
        parent_version: Optional[str] = None
    ) -> DatasetVersion:
        """Register a new dataset version"""
        async with self._lock:
            dataset = DatasetVersion(dataset_id, version, metadata, data_path)
            self.datasets[dataset_id].append(dataset)
            
            # Track lineage
            if parent_version:
                self.data_lineage[dataset_id].append(
                    f"{parent_version} -> {version}"
                )
            
            self._save_metadata()
            return dataset
    
    async def get_dataset(
        self,
        dataset_id: str,
        version: Optional[str] = None
    ) -> Optional[DatasetVersion]:
        """Get a dataset version (latest if version not specified)"""
        async with self._lock:
            versions = self.datasets.get(dataset_id, [])
            if not versions:
                return None
            
            if version:
                for v in versions:
                    if v.version == version:
                        return v
                return None
            else:
                return versions[-1]  # Return latest
    
    async def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets with their latest versions"""
        async with self._lock:
            result = []
            for dataset_id, versions in self.datasets.items():
                if versions:
                    latest = versions[-1]
                    result.append({
                        "dataset_id": dataset_id,
                        "latest_version": latest.version,
                        "total_versions": len(versions),
                        "created_at": latest.created_at,
                        "quality_score": latest.quality_score
                    })
            return result
    
    async def update_stats(
        self,
        dataset_id: str,
        version: str,
        stats: Dict[str, Any]
    ):
        """Update statistics for a dataset version"""
        async with self._lock:
            dataset = await self.get_dataset(dataset_id, version)
            if dataset:
                dataset.stats.update(stats)
                self._save_metadata()
    
    async def run_quality_checks(
        self,
        dataset_id: str,
        version: str,
        data_sample: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run quality checks on a dataset"""
        checks = {
            "completeness": self._check_completeness(data_sample),
            "consistency": self._check_consistency(data_sample),
            "validity": self._check_validity(data_sample),
            "uniqueness": self._check_uniqueness(data_sample),
            "accuracy": self._check_accuracy(data_sample)
        }
        
        # Calculate overall quality score
        quality_score = sum(checks.values()) / len(checks)
        
        # Update dataset quality score
        async with self._lock:
            dataset = await self.get_dataset(dataset_id, version)
            if dataset:
                dataset.quality_score = quality_score
                self._save_metadata()
        
        # Record the check
        check_record = {
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "checks": checks,
            "quality_score": quality_score
        }
        self.quality_checks[dataset_id].append(check_record)
        self._save_metadata()
        
        return {
            "dataset_id": dataset_id,
            "version": version,
            "checks": checks,
            "quality_score": quality_score,
            "passed": quality_score >= 0.7
        }
    
    def _check_completeness(self, data_sample: List[Dict[str, Any]]) -> float:
        """Check data completeness (no missing values)"""
        if not data_sample:
            return 0.0
        
        total_fields = 0
        complete_fields = 0
        
        for item in data_sample:
            for value in item.values():
                total_fields += 1
                if value is not None and value != "":
                    complete_fields += 1
        
        return complete_fields / total_fields if total_fields > 0 else 0.0
    
    def _check_consistency(self, data_sample: List[Dict[str, Any]]) -> float:
        """Check data consistency (consistent schema and types)"""
        if len(data_sample) < 2:
            return 1.0
        
        # Check schema consistency
        first_keys = set(data_sample[0].keys())
        consistent_count = sum(
            1 for item in data_sample[1:]
            if set(item.keys()) == first_keys
        )
        
        return (consistent_count + 1) / len(data_sample)
    
    def _check_validity(self, data_sample: List[Dict[str, Any]]) -> float:
        """Check data validity (reasonable values)"""
        if not data_sample:
            return 0.0
        
        # Simple validity checks
        valid_count = 0
        total_count = 0
        
        for item in data_sample:
            for key, value in item.items():
                total_count += 1
                # Check for reasonable values (not too long, not malformed)
                if isinstance(value, str):
                    if len(value) < 10000 and value.isprintable():
                        valid_count += 1
                elif isinstance(value, (int, float)):
                    if -1e10 < value < 1e10:  # Reasonable range
                        valid_count += 1
                else:
                    valid_count += 1
        
        return valid_count / total_count if total_count > 0 else 0.0
    
    def _check_uniqueness(self, data_sample: List[Dict[str, Any]]) -> float:
        """Check data uniqueness (no excessive duplicates)"""
        if len(data_sample) < 2:
            return 1.0
        
        # Convert to JSON strings for comparison
        json_strings = [json.dumps(item, sort_keys=True) for item in data_sample]
        unique_count = len(set(json_strings))
        
        return unique_count / len(data_sample)
    
    def _check_accuracy(self, data_sample: List[Dict[str, Any]]) -> float:
        """Check data accuracy (placeholder - would need ground truth)"""
        # In a real system, this would compare against ground truth
        # For now, return a baseline score
        return 0.8
    
    async def get_data_lineage(self, dataset_id: str) -> List[str]:
        """Get the lineage/history of a dataset"""
        async with self._lock:
            return self.data_lineage.get(dataset_id, [])
    
    async def compare_versions(
        self,
        dataset_id: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """Compare two versions of a dataset"""
        async with self._lock:
            dataset_a = await self.get_dataset(dataset_id, version_a)
            dataset_b = await self.get_dataset(dataset_id, version_b)
            
            if not dataset_a or not dataset_b:
                return {"error": "One or both versions not found"}
            
            return {
                "dataset_id": dataset_id,
                "version_a": {
                    "version": version_a,
                    "stats": dataset_a.stats,
                    "quality_score": dataset_a.quality_score
                },
                "version_b": {
                    "version": version_b,
                    "stats": dataset_b.stats,
                    "quality_score": dataset_b.quality_score
                },
                "quality_improvement": dataset_b.quality_score - dataset_a.quality_score
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall training data statistics"""
        total_datasets = len(self.datasets)
        total_versions = sum(len(versions) for versions in self.datasets.values())
        
        avg_quality = 0.0
        if total_versions > 0:
            all_scores = [
                v.quality_score
                for versions in self.datasets.values()
                for v in versions
            ]
            avg_quality = sum(all_scores) / len(all_scores)
        
        return {
            "total_datasets": total_datasets,
            "total_versions": total_versions,
            "average_quality_score": avg_quality,
            "total_quality_checks": sum(len(checks) for checks in self.quality_checks.values())
        }

# Global instance
_data_manager = None

def get_data_manager() -> TrainingDataManager:
    """Get or create the global data manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = TrainingDataManager()
    return _data_manager
