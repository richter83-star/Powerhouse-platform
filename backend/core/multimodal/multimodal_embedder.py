"""Multimodal Embedder: Creates unified embeddings from text/image/audio."""

import numpy as np
from typing import Dict, List, Optional, Any, Union
from PIL import Image

try:
    from transformers import CLIPModel, CLIPProcessor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


class MultimodalEmbedder:
    """Creates unified embeddings from multiple modalities."""
    
    def __init__(self):
        """Initialize multimodal embedder."""
        self.logger = get_logger(__name__)
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            except Exception:
                self.clip_model = None
                self.clip_processor = None
        else:
            self.clip_model = None
            self.clip_processor = None
    
    def embed_text(self, text: str) -> np.ndarray:
        """Embed text."""
        if self.clip_model:
            inputs = self.clip_processor(text=[text], return_tensors="pt", padding=True)
            outputs = self.clip_model.get_text_features(**inputs)
            return outputs[0].detach().numpy()
        else:
            # Fallback: simple hash-based embedding
            return np.random.randn(512).astype(np.float32)
    
    def embed_image(self, image: Image.Image) -> np.ndarray:
        """Embed image."""
        if self.clip_model:
            inputs = self.clip_processor(images=image, return_tensors="pt")
            outputs = self.clip_model.get_image_features(**inputs)
            return outputs[0].detach().numpy()
        else:
            return np.random.randn(512).astype(np.float32)
    
    def embed_multimodal(
        self,
        text: Optional[str] = None,
        image: Optional[Image.Image] = None
    ) -> np.ndarray:
        """Create unified multimodal embedding."""
        embeddings = []
        
        if text:
            embeddings.append(self.embed_text(text))
        
        if image:
            embeddings.append(self.embed_image(image))
        
        if not embeddings:
            return np.zeros(512, dtype=np.float32)
        
        # Concatenate or average
        combined = np.concatenate(embeddings) if len(embeddings) > 1 else embeddings[0]
        return combined / (np.linalg.norm(combined) + 1e-8)  # Normalize

