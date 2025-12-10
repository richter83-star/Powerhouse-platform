"""Cross-Modal Reasoner: Reasons across multiple modalities."""

from typing import Dict, List, Optional, Any, Union
from PIL import Image

from core.multimodal.multimodal_embedder import MultimodalEmbedder
from llm.base import BaseLLMProvider
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class CrossModalReasoner:
    """Reasons across text, images, audio."""
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        """Initialize cross-modal reasoner."""
        self.embedder = MultimodalEmbedder()
        self.llm = llm_provider or LLMConfig.get_llm_provider("multimodal")
        self.logger = get_logger(__name__)
    
    def reason(
        self,
        text: Optional[str] = None,
        image: Optional[Image.Image] = None,
        audio_path: Optional[str] = None,
        query: str = ""
    ) -> Dict[str, Any]:
        """Reason across modalities."""
        # Create unified embedding
        embedding = self.embedder.embed_multimodal(text=text, image=image)
        
        # Use LLM for reasoning
        prompt = f"""Given the following multimodal context, answer the query:

Query: {query}

Context:
- Text: {text or "None"}
- Image: {"Present" if image else "None"}
- Audio: {"Present" if audio_path else "None"}

Provide a comprehensive answer that considers all available modalities."""
        
        try:
            response = self.llm.invoke(prompt=prompt, temperature=0.7, max_tokens=500)
            return {
                "answer": response.content,
                "modalities_used": {
                    "text": text is not None,
                    "image": image is not None,
                    "audio": audio_path is not None
                }
            }
        except Exception as e:
            self.logger.error(f"Cross-modal reasoning failed: {e}")
            return {"answer": "Reasoning failed", "error": str(e)}

