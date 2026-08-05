"""
全局配置设置

使用 Pydantic Settings 管理配置，支持从环境变量和 .env 文件读取。
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Literal, Optional
import os


class Settings(BaseSettings):
    """全局设置"""

    # 模型选择
    tts_model: Literal["kokoro", "melo"] = Field(
        default="kokoro",
        description="TTS 模型选择"
    )

    # 服务器设置
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8000, description="服务器端口")

    # 音频设置
    sample_rate: int = Field(default=24000, description="音频采样率（固定24kHz）")
    default_audio_format: Literal["wav", "mp3"] = Field(
        default="mp3",
        description="默认音频格式"
    )
    enable_mp3: bool = Field(
        default=True,
        description="启用 MP3 编码（需要 ffmpeg）"
    )

    # Kokoro 配置
    kokoro_repo_id: str = Field(
        default="kokoro_api",
        description="Kokoro repo ID"
    )
    kokoro_config_path: str = Field(
        default="models/kokoro/models_zh/config.json",
        description="Kokoro 配置文件路径"
    )
    kokoro_model_path: str = Field(
        default="models/kokoro/models_zh/kokoro-v1_1-zh.pth",
        description="Kokoro 模型文件路径"
    )
    kokoro_voices_dir: str = Field(
        default="models/kokoro/voices",
        description="Kokoro 音色文件目录"
    )
    kokoro_voice_mapping: str = Field(
        default="models/kokoro/voice_mapping.json",
        description="Kokoro 音色映射文件"
    )

    # MeloTTS 配置
    melo_device: str = Field(
        default="auto",
        description="MeloTTS 设备（auto, cuda:0, cpu, mps）"
    )
    melo_voice_mapping: str = Field(
        default="models/melo/voice_mapping.json",
        description="MeloTTS 音色映射文件"
    )

    # OpenAI API 兼容性
    strict_openai_compatibility: bool = Field(
        default=True,
        description="严格遵循 OpenAI API 规范"
    )
    max_text_length: int = Field(
        default=4096,
        description="OpenAI API 文本长度限制"
    )
    min_speed: float = Field(default=0.25, description="最小语速")
    max_speed: float = Field(default=4.0, description="最大语速")

    # CORS 设置
    cors_origins: list = Field(
        default=["*"],
        description="CORS 允许的来源"
    )

    # 日志设置
    log_level: str = Field(default="INFO", description="日志级别")

    # 队列管理设置
    max_queue_size: int = Field(
        default=100,
        description="最大队列大小"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取设置实例"""
    return settings
