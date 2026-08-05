"""
自定义异常类

定义 TTS 服务的异常层次结构。
"""

from typing import Optional, Dict, Any


class TTSError(Exception):
    """TTS 服务基础异常"""

    def __init__(
        self,
        message: str,
        error_type: str = "tts_error",
        param: Optional[str] = None,
        code: Optional[str] = None
    ):
        self.message = message
        self.error_type = error_type
        self.param = param
        self.code = code or error_type.replace("_", " ")
        super().__init__(message)


class InvalidVoiceError(TTSError):
    """无效音色异常"""

    def __init__(self, voice: str, supported_voices: list):
        message = f"Invalid voice '{voice}'. Supported voices: {', '.join(supported_voices)}"
        super().__init__(
            message=message,
            error_type="invalid_request_error",
            param="voice",
            code="invalid_voice"
        )


class ModelNotLoadedError(TTSError):
    """模型未加载异常"""

    def __init__(self, model_name: str):
        message = f"Model '{model_name}' is not loaded"
        super().__init__(
            message=message,
            error_type="model_not_loaded",
            code="model_not_loaded"
        )


class ModelInitializationError(TTSError):
    """模型初始化失败异常"""

    def __init__(self, model_name: str, reason: str):
        message = f"Failed to initialize model '{model_name}': {reason}"
        super().__init__(
            message=message,
            error_type="model_initialization_error",
            code="model_initialization_failed"
        )


class TextProcessingError(TTSError):
    """文本处理异常"""

    def __init__(self, reason: str):
        message = f"Text processing failed: {reason}"
        super().__init__(
            message=message,
            error_type="text_processing_error",
            code="text_processing_failed"
        )


class AudioGenerationError(TTSError):
    """音频生成异常"""

    def __init__(self, reason: str):
        message = f"Audio generation failed: {reason}"
        super().__init__(
            message=message,
            error_type="audio_generation_error",
            code="audio_generation_failed"
        )


class InvalidInputError(TTSError):
    """无效输入异常"""

    def __init__(self, reason: str, param: Optional[str] = None):
        message = f"Invalid input: {reason}"
        super().__init__(
            message=message,
            error_type="invalid_request_error",
            param=param,
            code="invalid_input"
        )


def openai_error_response(error: TTSError) -> Dict[str, Any]:
    """
    生成 OpenAI 格式的错误响应

    Args:
        error: TTSError 异常对象

    Returns:
        OpenAI 格式的错误字典
    """
    result = {
        "error": {
            "message": error.message,
            "type": error.error_type,
            "code": error.code
        }
    }

    if error.param:
        result["error"]["param"] = error.param

    return result
