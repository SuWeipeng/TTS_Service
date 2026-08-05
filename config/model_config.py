"""
模型配置管理

管理模型特定的配置和音色映射。
"""

import json
import os
from typing import Dict, Any, Optional
from core.exceptions import ModelInitializationError


class ModelConfig:
    """模型配置基类"""

    def __init__(self, config_path: str):
        """
        加载模型配置

        Args:
            config_path: 配置文件路径（JSON 格式）
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise ModelInitializationError(
                self.config_path,
                f"Configuration file not found: {self.config_path}"
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ModelInitializationError(
                self.config_path,
                f"Invalid JSON format: {str(e)}"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def get_mappings(self) -> Dict[str, Any]:
        """获取音色映射"""
        return self.config.get("mappings", {})

    def get_supported_voices(self) -> list:
        """获取支持的音色列表"""
        return self.config.get("supported_voices", [])

    def get_default_voice(self) -> str:
        """获取默认音色"""
        return self.config.get("default_voice", "alloy")

    def get_openai_voices(self) -> list:
        """获取 OpenAI 兼容的音色列表"""
        return self.config.get("openai_voices", [])

    def map_voice(self, requested_voice: str) -> Any:
        """
        映射音色

        Args:
            requested_voice: 请求的音色

        Returns:
            映射后的音色配置（可能是字符串或字典）
        """
        mappings = self.get_mappings()
        return mappings.get(requested_voice, self.get_default_voice())


class VoiceMappingConfig(ModelConfig):
    """音色映射配置"""

    def get_speaker_id(self, voice: str) -> Optional[int]:
        """
        获取 speaker ID（用于 MeloTTS）

        Args:
            voice: 音色名称

        Returns:
            speaker ID 或 None
        """
        mapping = self.map_voice(voice)
        if isinstance(mapping, dict):
            return mapping.get("speaker_id")
        return None

    def get_language(self, voice: str) -> Optional[str]:
        """
        获取语言代码（用于 MeloTTS）

        Args:
            voice: 音色名称

        Returns:
            语言代码或 None
        """
        mapping = self.map_voice(voice)
        if isinstance(mapping, dict):
            return mapping.get("language")
        return None

    def get_voice_file(self, voice: str) -> Optional[str]:
        """
        获取音色文件路径（用于 Kokoro）

        Args:
            voice: 音色名称

        Returns:
            音色文件名或 None
        """
        mapping = self.map_voice(voice)
        if isinstance(mapping, str):
            return f"{mapping}.pt"
        return None


def load_kokoro_config() -> VoiceMappingConfig:
    """加载 Kokoro 配置"""
    from config.settings import settings
    return VoiceMappingConfig(settings.kokoro_voice_mapping)


def load_melo_config() -> VoiceMappingConfig:
    """加载 MeloTTS 配置"""
    from config.settings import settings
    return VoiceMappingConfig(settings.melo_voice_mapping)
