"""
TTS 模型抽象接口

所有 TTS 模型必须实现此接口，以确保模型可插拔性。
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Tuple, Optional
from enum import Enum


class ModelLoadingStrategy(Enum):
    """模型加载策略"""
    EAGER = "eager"   # 启动时加载
    LAZY = "lazy"     # 延迟加载


class TTSModelInterface(ABC):
    """TTS 模型抽象接口"""

    @abstractmethod
    def get_model_name(self) -> str:
        """返回模型标识符"""
        pass

    @abstractmethod
    def get_supported_voices(self) -> list:
        """返回支持的音色列表"""
        pass

    @abstractmethod
    def map_voice(self, requested_voice: str, text: str) -> str:
        """
        将请求的音色映射到模型特定的音色/说话人

        Args:
            requested_voice: 用户请求的音色（如 "alloy"）
            text: 要合成的文本（用于语言检测和音色优化）

        Returns:
            映射后的模型特定音色标识符
        """
        pass

    @abstractmethod
    async def generate_audio(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[bytes, str]:
        """
        生成完整音频

        Args:
            text: 输入文本
            voice: 音色（已映射的模型特定音色）
            speed: 语速
            **kwargs: 模型特定参数

        Returns:
            (audio_bytes, media_type) 元组
            - audio_bytes: 音频数据
            - media_type: 媒体类型（如 "audio/wav", "audio/mpeg"）
        """
        pass

    @abstractmethod
    async def generate_audio_stream(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        **kwargs
    ) -> AsyncIterator[Tuple[bytes, dict]]:
        """
        生成流式音频

        Args:
            text: 输入文本
            voice: 音色（已映射的模型特定音色）
            speed: 语速
            **kwargs: 模型特定参数

        Yields:
            (audio_chunk, metadata) 元组
            - audio_chunk: 音频数据块
            - metadata: 元数据字典
              {
                  "type": "sentence_start|sentence_end|done",
                  "index": int,
                  "text": str,
                  "voice": str,
                  "total_sentences": int,
                  "total_chunks": int,
                  "total_bytes": int
              }
        """
        pass

    @abstractmethod
    def get_loading_strategy(self) -> ModelLoadingStrategy:
        """返回模型加载策略"""
        pass

    @abstractmethod
    def initialize_model(self) -> None:
        """初始化/加载模型"""
        pass

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理模型资源"""
        pass
