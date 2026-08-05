"""
TTS 服务编排

封装 TTS 模型实例，提供统一的音频生成接口。
"""

import logging
from typing import AsyncIterator, Tuple, Dict, Any, Optional

from core.tts_interface import TTSModelInterface
from core.exceptions import InvalidVoiceError, ModelNotLoadedError, TTSError


class TTSService:
    """TTS 服务编排器"""

    def __init__(self, model: TTSModelInterface):
        """
        初始化 TTS 服务

        Args:
            model: TTS 模型实例
        """
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_model(self) -> TTSModelInterface:
        """
        获取底层模型实例

        Returns:
            TTS 模型实例
        """
        return self.model

    def get_model_name(self) -> str:
        """
        获取模型名称

        Returns:
            模型名称
        """
        return self.model.get_model_name()

    def get_supported_voices(self) -> list:
        """
        获取支持的音色列表

        Returns:
            音色列表
        """
        return self.model.get_supported_voices()

    def map_voice(self, requested_voice: str, text: str) -> str:
        """
        映射音色

        Args:
            requested_voice: 请求的音色
            text: 文本（用于语言检测和音色优化）

        Returns:
            映射后的音色
        """
        # 检查音色是否有效
        supported_voices = self.model.get_supported_voices()
        openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

        if requested_voice not in supported_voices and requested_voice not in openai_voices:
            raise InvalidVoiceError(requested_voice, supported_voices + openai_voices)

        return self.model.map_voice(requested_voice, text)

    async def generate_audio(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[bytes, str]:
        """
        生成音频

        Args:
            text: 输入文本
            voice: 音色
            speed: 语速
            **kwargs: 其他参数

        Returns:
            (audio_bytes, media_type) 元组

        Raises:
            InvalidVoiceError: 音色无效
            ModelNotLoadedError: 模型未加载
            TTSError: 其他错误
        """
        # 检查模型加载策略
        from core.tts_interface import ModelLoadingStrategy

        # 对于 EAGER 加载策略的模型，检查是否已加载
        if self.model.get_loading_strategy() == ModelLoadingStrategy.EAGER:
            if not self.model.is_model_loaded():
                raise ModelNotLoadedError(self.model.get_model_name())

        # 映射音色
        mapped_voice = self.map_voice(voice, text)

        try:
            return await self.model.generate_audio(
                text=text,
                voice=mapped_voice,
                speed=speed,
                **kwargs
            )
        except TTSError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to generate audio: {e}")
            from core.exceptions import AudioGenerationError
            raise AudioGenerationError(str(e))

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
            voice: 音色
            speed: 语速
            **kwargs: 其他参数

        Yields:
            (audio_chunk, metadata) 元组

        Raises:
            InvalidVoiceError: 音色无效
            ModelNotLoadedError: 模型未加载
            TTSError: 其他错误
        """
        # 检查模型加载策略
        from core.tts_interface import ModelLoadingStrategy

        # 对于 EAGER 加载策略的模型，检查是否已加载
        if self.model.get_loading_strategy() == ModelLoadingStrategy.EAGER:
            if not self.model.is_model_loaded():
                raise ModelNotLoadedError(self.model.get_model_name())

        # 映射音色
        mapped_voice = self.map_voice(voice, text)

        try:
            async for chunk, metadata in self.model.generate_audio_stream(
                text=text,
                voice=mapped_voice,
                speed=speed,
                **kwargs
            ):
                yield chunk, metadata
        except TTSError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to generate audio stream: {e}")
            from core.exceptions import AudioGenerationError
            raise AudioGenerationError(str(e))

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态

        Returns:
            健康状态字典
        """
        return {
            "model": self.model.get_model_name(),
            "model_loaded": self.model.is_model_loaded(),
            "supported_voices": self.model.get_supported_voices(),
        }


def create_tts_service(model: TTSModelInterface) -> TTSService:
    """
    创建 TTS 服务实例

    Args:
        model: TTS 模型实例

    Returns:
        TTS 服务实例
    """
    return TTSService(model)
