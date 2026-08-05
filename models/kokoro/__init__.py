"""
Kokoro 模型模块

导出 Kokoro 模型实现。
"""

from .model import KokoroModel
from .config import (
    get_lang_code,
    is_bilingual_voice,
    is_chinese_dominant,
    get_optimal_voice,
    BILINGUAL_VOICES,
    SUPPORTED_VOICES,
    DEFAULT_VOICE,
    DEFAULT_VOICE_MAPPING,
    OPENAI_VOICES
)

__all__ = [
    "KokoroModel",
    "get_lang_code",
    "is_bilingual_voice",
    "is_chinese_dominant",
    "get_optimal_voice",
    "BILINGUAL_VOICES",
    "SUPPORTED_VOICES",
    "DEFAULT_VOICE",
    "DEFAULT_VOICE_MAPPING",
    "OPENAI_VOICES",
]
