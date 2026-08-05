"""
配置模块

导出配置管理类。
"""

from .settings import Settings, settings, get_settings
from .model_config import ModelConfig, VoiceMappingConfig, load_kokoro_config, load_melo_config

__all__ = [
    "Settings",
    "settings",
    "get_settings",
    "ModelConfig",
    "VoiceMappingConfig",
    "load_kokoro_config",
    "load_melo_config",
]
