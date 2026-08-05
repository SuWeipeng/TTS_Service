"""
API 路由处理器

提供所有 HTTP 端点。
"""

import io
import logging
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse

from core.models import (
    OpenAITTSRequest,
    TTSRequest,
    VoicesResponse,
    VoiceInfo,
    HealthResponse
)
from core.exceptions import InvalidInputError
from services import TTSService


def create_routes(tts_service: TTSService) -> APIRouter:
    """
    创建 API 路由

    Args:
        tts_service: TTS 服务实例

    Returns:
        API 路由器
    """
    router = APIRouter()
    logger = logging.getLogger(__name__)

    @router.post("/v1/audio/speech")
    async def create_speech(request: OpenAITTSRequest):
        """
        OpenAI 兼容的 TTS 接口

        生成语音音频。

        Args:
            request: OpenAI TTS 请求

        Returns:
            音频流
        """
        try:
            logger.info(f"Received TTS request: voice={request.voice}, speed={request.speed}")

            # 验证语速范围
            if request.speed and (request.speed < 0.25 or request.speed > 4.0):
                raise InvalidInputError(
                    "Speed must be between 0.25 and 4.0",
                    param="speed"
                )

            # 生成音频
            audio_bytes, media_type = await tts_service.generate_audio(
                text=request.input,
                voice=request.voice,
                speed=request.speed or 1.0,
                input_format=request.input_format or "plain",
                target_format=request.response_format or "mp3"
            )

            if len(audio_bytes) == 0:
                raise HTTPException(status_code=500, detail="Generated audio is empty.")

            logger.info(f"Generated audio size: {len(audio_bytes)} bytes, format: {media_type}")

            # 返回音频流
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type=media_type,
                headers={
                    "Content-Disposition": "inline",
                    "Cache-Control": "no-cache",
                    "Access-Control-Allow-Origin": "*"
                }
            )

        except InvalidInputError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except Exception as e:
            logger.error(f"Error in create_speech: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

    @router.get("/tts")
    async def tts_get(
        text: str = Query(..., description="要合成的文本内容"),
        voice: str = Query("alloy", description="音色名称"),
        speed: float = Query(1.0, description="语速调节，如 0.9 或 1.2")
    ):
        """
        原有的 GET 接口

        生成语音音频。

        Args:
            text: 要合成的文本内容
            voice: 音色名称
            speed: 语速

        Returns:
            音频流
        """
        try:
            audio_bytes, media_type = await tts_service.generate_audio(
                text=text,
                voice=voice,
                speed=speed
            )

            if len(audio_bytes) > 0:
                return StreamingResponse(
                    io.BytesIO(audio_bytes),
                    media_type=media_type,
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            else:
                raise HTTPException(status_code=500, detail="Generated audio is empty.")

        except Exception as e:
            logger.error(f"Error in tts_get: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

    @router.post("/tts_post")
    async def tts_post(request: TTSRequest):
        """
        原有的 POST 接口

        接收 JSON 格式的文本、音色、语速，生成音频文件。

        Args:
            request: TTS 请求

        Returns:
            音频流
        """
        try:
            # 处理文本（支持 Markdown 清洗和特殊符号处理）
            audio_bytes, media_type = await tts_service.generate_audio(
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                input_format=request.input_format or "plain"
            )

            if len(audio_bytes) > 0:
                return StreamingResponse(
                    io.BytesIO(audio_bytes),
                    media_type=media_type,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Content-Disposition": f"inline"
                    }
                )
            else:
                raise HTTPException(status_code=500, detail="Generated audio is empty.")

        except Exception as e:
            logger.error(f"Error in tts_post: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

    @router.get("/v1/audio/voices", response_model=VoicesResponse)
    async def list_voices():
        """
        获取可用声音列表的接口（OpenAI 兼容格式）

        Returns:
            音色列表
        """
        model_name = tts_service.get_model_name()

        if model_name == "kokoro":
            # Kokoro 音色列表
            return VoicesResponse(data=[
                VoiceInfo(id="alloy", name="Alloy", description="Female voice (bf_vale)"),
                VoiceInfo(id="echo", name="Echo", description="Male voice (am_adam)"),
                VoiceInfo(id="fable", name="Fable", description="Female voice (af_sol)"),
                VoiceInfo(id="onyx", name="Onyx", description="Male voice (am_michael)"),
                VoiceInfo(id="nova", name="Nova", description="Female voice (af_sarah)"),
                VoiceInfo(id="shimmer", name="Shimmer", description="Bilingual voice (af_maple)"),
            ])
        else:
            # MeloTTS 音色列表
            return VoicesResponse(data=[
                VoiceInfo(id="alloy", name="Alloy", description="🌏 Bilingual Chinese-English voice (中英双语)"),
                VoiceInfo(id="echo", name="Echo", description="English (US) voice"),
                VoiceInfo(id="fable", name="Fable", description="English (British) voice"),
                VoiceInfo(id="onyx", name="Onyx", description="English (Default) voice"),
                VoiceInfo(id="nova", name="Nova", description="English (US) voice"),
                VoiceInfo(id="shimmer", name="Shimmer", description="English (Australian) voice"),
            ])

    @router.get("/health", response_model=HealthResponse)
    async def health_check():
        """
        健康检查接口

        Returns:
            健康状态
        """
        health_status = tts_service.get_health_status()
        return HealthResponse(
            status="ok",
            model=health_status["model"],
            model_loaded=health_status["model_loaded"],
            supported_voices=health_status.get("supported_voices"),
        )

    @router.get("/health/detail")
    async def health_detail():
        """
        详细健康检查接口

        Returns:
            详细健康状态
        """
        health_status = tts_service.get_health_status()
        from config.settings import settings

        # 检查 ffmpeg 是否可用
        ffmpeg_available = _check_ffmpeg_available() if settings.enable_mp3 else False

        return {
            "status": "ok",
            "model": health_status["model"],
            "model_loaded": health_status["model_loaded"],
            "supported_voices": health_status["supported_voices"],
            "audio_format": settings.default_audio_format,
            "sample_rate": settings.sample_rate,
            "mp3_enabled": settings.enable_mp3,
            "dependencies": {
                "ffmpeg": ffmpeg_available
            }
        }

    return router


def _check_ffmpeg_available() -> bool:
    """检查 ffmpeg 是否可用"""
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False
