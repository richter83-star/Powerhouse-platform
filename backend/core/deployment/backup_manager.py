
"""
Backup and Disaster Recovery
Manages automated backups and recovery procedures.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import gzip
import shutil
from pathlib import Path

@dataclass
class BackupMetadata:
    """Metadata for a backup"""
    backup_id: str
    created_at: datetime
    backup_type: str  # full, incremental, snapshot
    size_bytes: int
    status: str  # completed, failed, in_progress
    retention_days: int
    metadata: Dict[str, Any]

class BackupManager:
    """Manages backups and disaster recovery"""
    
    def __init__(self, backup_dir: str = "/tmp/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._backups: Dict[str, BackupMetadata] = {}
        self._retention_policy = {
            "daily": 7,  # Keep daily backups for 7 days
            "weekly": 30,  # Keep weekly backups for 30 days
            "monthly": 365  # Keep monthly backups for 1 year
        }
    
    def create_backup(
        self,
        backup_type: str = "full",
        data: Optional[Dict[str, Any]] = None,
        retention_days: int = 7
    ) -> BackupMetadata:
        """Create a new backup"""
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.json.gz"
        
        # Prepare backup data
        backup_data = {
            "backup_id": backup_id,
            "created_at": datetime.utcnow().isoformat(),
            "backup_type": backup_type,
            "data": data or {}
        }
        
        # Compress and save
        try:
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
            
            size_bytes = backup_path.stat().st_size
            status = "completed"
        except Exception as e:
            size_bytes = 0
            status = f"failed: {str(e)}"
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            created_at=datetime.utcnow(),
            backup_type=backup_type,
            size_bytes=size_bytes,
            status=status,
            retention_days=retention_days,
            metadata={"path": str(backup_path)}
        )
        
        self._backups[backup_id] = metadata
        return metadata
    
    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore from a backup"""
        metadata = self._backups.get(backup_id)
        if not metadata:
            raise ValueError(f"Backup {backup_id} not found")
        
        backup_path = Path(metadata.metadata["path"])
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
            return backup_data
        except Exception as e:
            raise RuntimeError(f"Failed to restore backup: {str(e)}")
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[BackupMetadata]:
        """List all backups"""
        backups = list(self._backups.values())
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]
        return sorted(backups, key=lambda x: x.created_at, reverse=True)
    
    def cleanup_old_backups(self) -> List[str]:
        """Remove backups that exceed retention policy"""
        removed = []
        now = datetime.utcnow()
        
        for backup_id, metadata in list(self._backups.items()):
            age_days = (now - metadata.created_at).days
            if age_days > metadata.retention_days:
                backup_path = Path(metadata.metadata["path"])
                if backup_path.exists():
                    backup_path.unlink()
                del self._backups[backup_id]
                removed.append(backup_id)
        
        return removed
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get overall backup status"""
        backups = list(self._backups.values())
        total_size = sum(b.size_bytes for b in backups)
        
        return {
            "total_backups": len(backups),
            "total_size_gb": total_size / (1024 ** 3),
            "latest_backup": backups[0].created_at.isoformat() if backups else None,
            "oldest_backup": backups[-1].created_at.isoformat() if backups else None,
            "by_type": {
                backup_type: len([b for b in backups if b.backup_type == backup_type])
                for backup_type in set(b.backup_type for b in backups)
            }
        }

# Singleton instance
_backup_manager = BackupManager()

def get_backup_manager() -> BackupManager:
    """Get the global backup manager instance"""
    return _backup_manager
