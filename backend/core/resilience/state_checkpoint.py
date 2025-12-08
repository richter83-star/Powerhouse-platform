
"""
State Checkpointing System
Provides automatic state persistence and recovery for resilient multi-agent operations.
"""

import json
import pickle
import gzip
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint"""
    checkpoint_id: str
    timestamp: str
    agent_id: str
    workflow_id: str
    state_hash: str
    size_bytes: int
    compressed: bool
    version: str = "1.0"


class StateCheckpointManager:
    """
    Manages state checkpointing and recovery for agents and workflows.
    Supports automatic snapshots, incremental saves, and fast recovery.
    """
    
    def __init__(self, checkpoint_dir: str = "./checkpoints", compression: bool = True):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.compression = compression
        self.metadata_store: Dict[str, CheckpointMetadata] = {}
        self._load_metadata_index()
    
    def _load_metadata_index(self):
        """Load checkpoint metadata index"""
        index_file = self.checkpoint_dir / "checkpoint_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    self.metadata_store = {
                        k: CheckpointMetadata(**v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.metadata_store)} checkpoint metadata entries")
            except Exception as e:
                logger.error(f"Failed to load checkpoint index: {e}")
    
    def _save_metadata_index(self):
        """Save checkpoint metadata index"""
        index_file = self.checkpoint_dir / "checkpoint_index.json"
        try:
            data = {k: asdict(v) for k, v in self.metadata_store.items()}
            with open(index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save checkpoint index: {e}")
    
    def _compute_state_hash(self, state: Any) -> str:
        """Compute hash of state for integrity checking"""
        state_bytes = pickle.dumps(state)
        return hashlib.sha256(state_bytes).hexdigest()
    
    def save_checkpoint(
        self,
        state: Any,
        agent_id: str,
        workflow_id: str,
        checkpoint_id: Optional[str] = None
    ) -> str:
        """
        Save a checkpoint of the current state.
        
        Args:
            state: State object to checkpoint
            agent_id: ID of the agent
            workflow_id: ID of the workflow
            checkpoint_id: Optional custom checkpoint ID
            
        Returns:
            Checkpoint ID
        """
        if checkpoint_id is None:
            checkpoint_id = f"{agent_id}_{workflow_id}_{datetime.utcnow().isoformat()}"
        
        try:
            # Serialize state
            state_bytes = pickle.dumps(state)
            state_hash = hashlib.sha256(state_bytes).hexdigest()
            
            # Compress if enabled
            if self.compression:
                state_bytes = gzip.compress(state_bytes)
            
            # Save checkpoint file
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.ckpt"
            with open(checkpoint_file, 'wb') as f:
                f.write(state_bytes)
            
            # Create metadata
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                timestamp=datetime.utcnow().isoformat(),
                agent_id=agent_id,
                workflow_id=workflow_id,
                state_hash=state_hash,
                size_bytes=len(state_bytes),
                compressed=self.compression
            )
            
            # Store metadata
            self.metadata_store[checkpoint_id] = metadata
            self._save_metadata_index()
            
            logger.info(f"Saved checkpoint {checkpoint_id} ({len(state_bytes)} bytes)")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint_id}: {e}")
            raise
    
    def load_checkpoint(self, checkpoint_id: str) -> Any:
        """
        Load a checkpoint by ID.
        
        Args:
            checkpoint_id: ID of the checkpoint to load
            
        Returns:
            Restored state object
        """
        if checkpoint_id not in self.metadata_store:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        metadata = self.metadata_store[checkpoint_id]
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.ckpt"
        
        if not checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_file}")
        
        try:
            # Load checkpoint file
            with open(checkpoint_file, 'rb') as f:
                state_bytes = f.read()
            
            # Decompress if needed
            if metadata.compressed:
                state_bytes = gzip.decompress(state_bytes)
            
            # Verify integrity
            actual_hash = hashlib.sha256(state_bytes).hexdigest()
            if actual_hash != metadata.state_hash:
                logger.warning(f"Checkpoint {checkpoint_id} hash mismatch - possible corruption")
            
            # Deserialize state
            state = pickle.loads(state_bytes)
            
            logger.info(f"Loaded checkpoint {checkpoint_id}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            raise
    
    def list_checkpoints(
        self,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> List[CheckpointMetadata]:
        """
        List available checkpoints with optional filtering.
        
        Args:
            agent_id: Filter by agent ID
            workflow_id: Filter by workflow ID
            
        Returns:
            List of checkpoint metadata
        """
        checkpoints = list(self.metadata_store.values())
        
        if agent_id:
            checkpoints = [c for c in checkpoints if c.agent_id == agent_id]
        
        if workflow_id:
            checkpoints = [c for c in checkpoints if c.workflow_id == workflow_id]
        
        # Sort by timestamp descending (newest first)
        checkpoints.sort(key=lambda c: c.timestamp, reverse=True)
        
        return checkpoints
    
    def get_latest_checkpoint(
        self,
        agent_id: str,
        workflow_id: str
    ) -> Optional[str]:
        """
        Get the ID of the most recent checkpoint for an agent/workflow.
        
        Args:
            agent_id: Agent ID
            workflow_id: Workflow ID
            
        Returns:
            Checkpoint ID or None if not found
        """
        checkpoints = self.list_checkpoints(agent_id=agent_id, workflow_id=workflow_id)
        return checkpoints[0].checkpoint_id if checkpoints else None
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            checkpoint_id: ID of checkpoint to delete
            
        Returns:
            True if deleted successfully
        """
        if checkpoint_id not in self.metadata_store:
            return False
        
        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.ckpt"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
            
            del self.metadata_store[checkpoint_id]
            self._save_metadata_index()
            
            logger.info(f"Deleted checkpoint {checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            return False
    
    def cleanup_old_checkpoints(
        self,
        agent_id: str,
        workflow_id: str,
        keep_count: int = 5
    ) -> int:
        """
        Clean up old checkpoints, keeping only the N most recent.
        
        Args:
            agent_id: Agent ID
            workflow_id: Workflow ID
            keep_count: Number of checkpoints to keep
            
        Returns:
            Number of checkpoints deleted
        """
        checkpoints = self.list_checkpoints(agent_id=agent_id, workflow_id=workflow_id)
        
        if len(checkpoints) <= keep_count:
            return 0
        
        to_delete = checkpoints[keep_count:]
        deleted_count = 0
        
        for checkpoint in to_delete:
            if self.delete_checkpoint(checkpoint.checkpoint_id):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old checkpoints")
        return deleted_count


class AutoCheckpointer:
    """
    Automatic checkpointing wrapper for agents and workflows.
    Provides transparent state persistence with configurable intervals.
    """
    
    def __init__(
        self,
        manager: StateCheckpointManager,
        agent_id: str,
        workflow_id: str,
        checkpoint_interval: int = 100  # Checkpoint every N operations
    ):
        self.manager = manager
        self.agent_id = agent_id
        self.workflow_id = workflow_id
        self.checkpoint_interval = checkpoint_interval
        self.operation_count = 0
        self.last_checkpoint_id: Optional[str] = None
    
    def maybe_checkpoint(self, state: Any) -> Optional[str]:
        """
        Conditionally checkpoint based on operation count.
        
        Args:
            state: Current state to checkpoint
            
        Returns:
            Checkpoint ID if saved, None otherwise
        """
        self.operation_count += 1
        
        if self.operation_count % self.checkpoint_interval == 0:
            checkpoint_id = self.manager.save_checkpoint(
                state=state,
                agent_id=self.agent_id,
                workflow_id=self.workflow_id
            )
            self.last_checkpoint_id = checkpoint_id
            
            # Cleanup old checkpoints
            self.manager.cleanup_old_checkpoints(
                agent_id=self.agent_id,
                workflow_id=self.workflow_id,
                keep_count=5
            )
            
            return checkpoint_id
        
        return None
    
    def force_checkpoint(self, state: Any) -> str:
        """
        Force an immediate checkpoint regardless of interval.
        
        Args:
            state: Current state to checkpoint
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = self.manager.save_checkpoint(
            state=state,
            agent_id=self.agent_id,
            workflow_id=self.workflow_id
        )
        self.last_checkpoint_id = checkpoint_id
        return checkpoint_id
    
    def recover(self) -> Optional[Any]:
        """
        Recover from the latest checkpoint.
        
        Returns:
            Recovered state or None if no checkpoint exists
        """
        checkpoint_id = self.manager.get_latest_checkpoint(
            agent_id=self.agent_id,
            workflow_id=self.workflow_id
        )
        
        if checkpoint_id:
            return self.manager.load_checkpoint(checkpoint_id)
        
        return None


# Global checkpoint manager instance
checkpoint_manager = StateCheckpointManager()
