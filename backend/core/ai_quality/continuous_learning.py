
"""
Continuous Learning System
Enables online learning and model adaptation
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
import asyncio

class LearningBuffer:
    """Buffer for collecting learning examples"""
    def __init__(self, max_size: int = 1000):
        self.buffer: deque = deque(maxlen=max_size)
        self.max_size = max_size
        
    def add(self, example: Dict[str, Any]):
        """Add an example to the buffer"""
        example["timestamp"] = datetime.now().isoformat()
        self.buffer.append(example)
    
    def get_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Get a batch of examples"""
        size = min(batch_size, len(self.buffer))
        return list(self.buffer)[-size:] if size > 0 else []
    
    def clear(self):
        """Clear the buffer"""
        self.buffer.clear()
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)

class ContinuousLearningSystem:
    """Manages continuous learning for AI models"""
    
    def __init__(self):
        self.learning_buffers: Dict[str, LearningBuffer] = {}
        self.learning_stats: Dict[str, Dict] = {}
        self.learning_triggers: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        
        # Learning strategies
        self.strategies = {
            "immediate": "Update model immediately on each example",
            "batch": "Update model in batches",
            "periodic": "Update model on a schedule",
            "threshold": "Update when buffer reaches threshold"
        }
    
    async def configure_learning(
        self,
        model_id: str,
        strategy: str = "batch",
        batch_size: int = 100,
        buffer_size: int = 1000,
        learning_rate: float = 0.001
    ) -> Dict[str, Any]:
        """Configure continuous learning for a model"""
        async with self._lock:
            if model_id not in self.learning_buffers:
                self.learning_buffers[model_id] = LearningBuffer(buffer_size)
            
            self.learning_triggers[model_id] = {
                "strategy": strategy,
                "batch_size": batch_size,
                "buffer_size": buffer_size,
                "learning_rate": learning_rate,
                "enabled": True
            }
            
            self.learning_stats[model_id] = {
                "total_examples": 0,
                "total_updates": 0,
                "last_update": None,
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "model_id": model_id,
                "configuration": self.learning_triggers[model_id],
                "message": "Continuous learning configured"
            }
    
    async def add_learning_example(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        target: Any,
        feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a learning example"""
        async with self._lock:
            if model_id not in self.learning_buffers:
                # Auto-configure with defaults
                await self.configure_learning(model_id)
            
            example = {
                "input": input_data,
                "target": target,
                "feedback": feedback or {}
            }
            
            self.learning_buffers[model_id].add(example)
            self.learning_stats[model_id]["total_examples"] += 1
            
            # Check if update should be triggered
            should_update = await self._should_trigger_update(model_id)
            
            return {
                "success": True,
                "buffer_size": self.learning_buffers[model_id].size(),
                "should_update": should_update
            }
    
    async def _should_trigger_update(self, model_id: str) -> bool:
        """Check if learning update should be triggered"""
        if model_id not in self.learning_triggers:
            return False
        
        config = self.learning_triggers[model_id]
        if not config.get("enabled", False):
            return False
        
        strategy = config.get("strategy", "batch")
        buffer = self.learning_buffers[model_id]
        
        if strategy == "immediate":
            return True
        elif strategy == "batch":
            return buffer.size() >= config.get("batch_size", 100)
        elif strategy == "threshold":
            return buffer.size() >= config.get("buffer_size", 1000) * 0.8
        
        return False
    
    async def trigger_learning_update(
        self,
        model_id: str
    ) -> Dict[str, Any]:
        """Manually trigger a learning update"""
        async with self._lock:
            if model_id not in self.learning_buffers:
                return {"error": "Model not configured for learning"}
            
            buffer = self.learning_buffers[model_id]
            config = self.learning_triggers.get(model_id, {})
            
            # Get batch of examples
            batch_size = config.get("batch_size", 100)
            examples = buffer.get_batch(batch_size)
            
            if not examples:
                return {"message": "No examples to learn from"}
            
            # Simulate learning update
            # In a real system, this would call actual model training
            update_result = await self._perform_learning_update(
                model_id,
                examples,
                config.get("learning_rate", 0.001)
            )
            
            # Update stats
            self.learning_stats[model_id]["total_updates"] += 1
            self.learning_stats[model_id]["last_update"] = datetime.now().isoformat()
            
            # Clear processed examples
            buffer.clear()
            
            return {
                "success": True,
                "model_id": model_id,
                "examples_processed": len(examples),
                "update_result": update_result
            }
    
    async def _perform_learning_update(
        self,
        model_id: str,
        examples: List[Dict[str, Any]],
        learning_rate: float
    ) -> Dict[str, Any]:
        """Perform the actual learning update (simulated)"""
        # In a real system, this would:
        # 1. Load the current model
        # 2. Perform gradient descent or other learning
        # 3. Save updated model
        # 4. Validate performance
        
        # For now, simulate metrics
        return {
            "examples_count": len(examples),
            "learning_rate": learning_rate,
            "simulated_loss": 0.05,
            "simulated_improvement": 0.02,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_learning_status(self, model_id: str) -> Dict[str, Any]:
        """Get current learning status for a model"""
        async with self._lock:
            if model_id not in self.learning_buffers:
                return {"error": "Model not configured for learning"}
            
            buffer = self.learning_buffers[model_id]
            config = self.learning_triggers.get(model_id, {})
            stats = self.learning_stats.get(model_id, {})
            
            return {
                "model_id": model_id,
                "configuration": config,
                "statistics": stats,
                "buffer": {
                    "current_size": buffer.size(),
                    "max_size": buffer.max_size
                },
                "should_update": await self._should_trigger_update(model_id)
            }
    
    async def enable_learning(self, model_id: str) -> bool:
        """Enable continuous learning for a model"""
        async with self._lock:
            if model_id in self.learning_triggers:
                self.learning_triggers[model_id]["enabled"] = True
                return True
            return False
    
    async def disable_learning(self, model_id: str) -> bool:
        """Disable continuous learning for a model"""
        async with self._lock:
            if model_id in self.learning_triggers:
                self.learning_triggers[model_id]["enabled"] = False
                return True
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall continuous learning statistics"""
        total_examples = sum(
            stats.get("total_examples", 0)
            for stats in self.learning_stats.values()
        )
        total_updates = sum(
            stats.get("total_updates", 0)
            for stats in self.learning_stats.values()
        )
        
        return {
            "models_with_learning": len(self.learning_buffers),
            "total_examples_collected": total_examples,
            "total_learning_updates": total_updates,
            "available_strategies": self.strategies
        }

# Global instance
_continuous_learning = None

def get_continuous_learning() -> ContinuousLearningSystem:
    """Get or create the global continuous learning system"""
    global _continuous_learning
    if _continuous_learning is None:
        _continuous_learning = ContinuousLearningSystem()
    return _continuous_learning
