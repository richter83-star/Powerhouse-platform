"""Vision-Language Model: Integrates vision and text understanding."""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from PIL import Image
import io

try:
    from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VisionLanguageResult:
    """Result of vision-language processing."""
    text: str
    image_description: Optional[str] = None
    similarity_score: Optional[float] = None


class VisionLanguageModel:
    """Integrates vision models (CLIP, BLIP) with text."""
    
    def __init__(self, model_type: str = "clip"):
        """
        Initialize vision-language model.
        
        Args:
            model_type: "clip" or "blip"
        """
        self.model_type = model_type
        self.logger = get_logger(__name__)
        
        if TRANSFORMERS_AVAILABLE:
            try:
                if model_type == "clip":
                    self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                    self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                elif model_type == "blip":
                    self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                    self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                else:
                    self.model = None
                    self.processor = None
            except Exception as e:
                self.logger.warning(f"Failed to load {model_type} model: {e}")
                self.model = None
                self.processor = None
        else:
            self.model = None
            self.processor = None
    
    def process(self, image: Image.Image, text: str) -> VisionLanguageResult:
        """Process image and text together."""
        if not self.model:
            return VisionLanguageResult(text=text, image_description="[Vision model not available]")
        
        try:
            if self.model_type == "clip":
                # CLIP: compute similarity
                inputs = self.processor(text=[text], images=image, return_tensors="pt", padding=True)
                outputs = self.model(**inputs)
                similarity = outputs.logits_per_text[0][0].item()
                
                return VisionLanguageResult(
                    text=text,
                    similarity_score=float(similarity)
                )
            elif self.model_type == "blip":
                # BLIP: generate image caption
                inputs = self.processor(image, text, return_tensors="pt")
                outputs = self.model.generate(**inputs)
                caption = self.processor.decode(outputs[0], skip_special_tokens=True)
                
                return VisionLanguageResult(
                    text=text,
                    image_description=caption
                )
        except Exception as e:
            self.logger.error(f"Vision-language processing failed: {e}")
        
        return VisionLanguageResult(text=text)

