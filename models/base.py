"""
模型基类

提供模型实现的通用功能，并实现 TTS 模型接口。
"""

from abc import ABC, abstractmethod
from typing import List, AsyncIterator, Tuple
from enum import Enum
import logging

from core.tts_interface import TTSModelInterface, ModelLoadingStrategy
from utils.logger import setup_logger


class BaseModel(TTSModelInterface, ABC):
    """模型基类 - 实现 TTS 模型接口"""

    def __init__(self):
        # 使用 setup_logger 来配置 logger，确保有处理器
        # force=True 确保即使已有配置也会重新配置
        self.logger = setup_logger(self.__class__.__name__, force=True)
        self._model_loaded = False

    # 以下方法由子类实现
    @abstractmethod
    def get_model_name(self) -> str:
        """返回模型名称"""
        pass

    @abstractmethod
    def get_supported_voices(self) -> List[str]:
        """返回支持的音色列表"""
        pass

    @abstractmethod
    def map_voice(self, requested_voice: str, text: str) -> str:
        """映射音色"""
        pass

    @abstractmethod
    def initialize_model(self) -> None:
        """初始化模型"""
        pass

    @abstractmethod
    async def generate_audio(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[bytes, str]:
        """生成音频"""
        pass

    @abstractmethod
    async def generate_audio_stream(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        **kwargs
    ) -> AsyncIterator[Tuple[bytes, dict]]:
        """生成流式音频"""
        pass

    @abstractmethod
    def get_loading_strategy(self) -> ModelLoadingStrategy:
        """返回模型加载策略"""
        pass

    # 以下方法提供默认实现
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model_loaded

    def set_model_loaded(self, loaded: bool) -> None:
        """设置模型加载状态"""
        self._model_loaded = loaded

    @abstractmethod
    def cleanup(self) -> None:
        """清理模型资源"""
        pass
