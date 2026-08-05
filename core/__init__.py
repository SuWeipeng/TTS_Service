"""
核心模块

导出核心接口和类。
"""

from .tts_interface import TTSModelInterface, ModelLoadingStrategy
from .text_processor_interface import TextProcessorInterface
from .models import (
    OpenAITTSRequest,
    TTSRequest,
    VoiceInfo,
    VoicesResponse,
    HealthResponse,
    WebSocketRequest,
    WebSocketMessage
)
from .exceptions import (
    TTSError,
    InvalidVoiceError,
    ModelNotLoadedError,
    ModelInitializationError,
    TextProcessingError,
    AudioGenerationError,
    InvalidInputError,
    openai_error_response
)

__all__ = [
    # Interfaces
    "TTSModelInterface",
    "ModelLoadingStrategy",
    "TextProcessorInterface",

    # Models
    "OpenAITTSRequest",
    "TTSRequest",
    "VoiceInfo",
    "VoicesResponse",
    "HealthResponse",
    "WebSocketRequest",
    "WebSocketMessage",

    # Exceptions
    "TTSError",
    "InvalidVoiceError",
    "ModelNotLoadedError",
    "ModelInitializationError",
    "TextProcessingError",
    "AudioGenerationError",
    "InvalidInputError",
    "openai_error_response",
]
