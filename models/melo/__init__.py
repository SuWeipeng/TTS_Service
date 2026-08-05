"""
MeloTTS 模型模块

导出 MeloTTS 模型实现。
"""

from .model import MeloModel
from .config import (
    detect_language,
    get_speaker_and_model_info,
    map_voice_to_speaker_id,
    get_voice_language,
    SUPPORTED_VOICES,
    DEFAULT_SPEAKER_MAPPING,
    OPENAI_VOICES,
    DEFAULT_VOICE,
    EN_ACCENT_MAPPING
)

__all__ = [
    "MeloModel",
    "detect_language",
    "get_speaker_and_model_info",
    "map_voice_to_speaker_id",
    "get_voice_language",
    "SUPPORTED_VOICES",
    "DEFAULT_SPEAKER_MAPPING",
    "OPENAI_VOICES",
    "DEFAULT_VOICE",
    "EN_ACCENT_MAPPING",
]
