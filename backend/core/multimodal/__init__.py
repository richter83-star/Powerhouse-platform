"""
Multi-Modal Learning: Processing text, images, audio, and video.
"""

from core.multimodal.vision_language_model import VisionLanguageModel
from core.multimodal.multimodal_embedder import MultimodalEmbedder
from core.multimodal.audio_processor import AudioProcessor
from core.multimodal.cross_modal_reasoner import CrossModalReasoner

__all__ = [
    'VisionLanguageModel',
    'MultimodalEmbedder',
    'AudioProcessor',
    'CrossModalReasoner'
]

