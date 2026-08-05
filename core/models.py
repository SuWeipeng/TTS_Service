"""
Pydantic 数据模型

定义 API 请求/响应的数据结构。
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal


class OpenAITTSRequest(BaseModel):
    """OpenAI 兼容的 TTS 请求"""
    model: str = Field(default="tts-1", description="模型名称")
    input: str = Field(..., min_length=1, max_length=4096, description="输入文本")
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(
        default="alloy", description="音色"
    )
    response_format: Optional[Literal["mp3", "wav"]] = Field(
        default="mp3", description="音频格式"
    )
    speed: Optional[float] = Field(
        default=1.0, ge=0.25, le=4.0, description="语速"
    )
    input_format: Optional[Literal["plain", "markdown"]] = Field(
        default="plain", description="输入格式"
    )

    @validator('input')
    def validate_text_length(cls, v):
        if len(v) > 4096:
            raise ValueError("Text exceeds maximum length of 4096 characters")
        return v

    @validator('speed')
    def validate_speed(cls, v):
        if v is not None and (v < 0.25 or v > 4.0):
            raise ValueError("Speed must be between 0.25 and 4.0")
        return v


class TTSRequest(BaseModel):
    """通用 TTS 请求"""
    text: str = Field(..., min_length=1, description="要合成的文本内容")
    voice: str = Field(default="alloy", description="音色名称")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="语速调节")
    input_format: Optional[Literal["plain", "markdown"]] = Field(
        default="plain", description="输入格式"
    )


class VoiceInfo(BaseModel):
    """音色信息"""
    id: str = Field(..., description="音色ID")
    name: str = Field(..., description="音色名称")
    description: str = Field(..., description="音色描述")


class VoicesResponse(BaseModel):
    """音色列表响应"""
    data: list[VoiceInfo]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="健康状态")
    model: str = Field(..., description="当前使用的模型")
    model_loaded: Optional[bool] = Field(None, description="模型是否已加载")
    supported_voices: Optional[list] = Field(None, description="支持的音色列表")
    audio_format: Optional[str] = Field(None, description="默认音频格式")
    sample_rate: Optional[int] = Field(None, description="采样率")
    mp3_enabled: Optional[bool] = Field(None, description="是否启用MP3编码")


class WebSocketRequest(BaseModel):
    """WebSocket 请求"""
    text: str = Field(..., description="要合成的文本")
    voice: str = Field(default="alloy", description="音色")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="语速")
    input_format: Optional[Literal["plain", "markdown"]] = Field(
        default="plain", description="输入格式"
    )


class WebSocketMessage(BaseModel):
    """WebSocket 消息"""
    type: Literal["sentence_start", "sentence_end", "done", "error"] = Field(
        ..., description="消息类型"
    )
    index: Optional[int] = Field(None, description="句子索引")
    text: Optional[str] = Field(None, description="句子文本")
    voice: Optional[str] = Field(None, description="使用的音色")
    message: Optional[str] = Field(None, description="错误消息")
    total_sentences: Optional[int] = Field(None, description="总句子数")
    total_chunks: Optional[int] = Field(None, description="总音频块数")
    total_bytes: Optional[int] = Field(None, description="总字节数")
