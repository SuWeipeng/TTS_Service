"""
WebSocket 处理器

提供 WebSocket 流式 TTS 端点。
"""

import json
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any

from core.models import WebSocketRequest
from core.exceptions import InvalidInputError
from services import TTSService


def create_websocket_route(tts_service: TTSService):
    """
    创建 WebSocket 路由

    Args:
        tts_service: TTS 服务实例

    Returns:
        WebSocket 路由函数
    """

    async def websocket_tts(websocket: WebSocket):
        """
        WebSocket 流式 TTS 接口，用于实时语音合成

        请求格式：
        {
            "text": "要合成的文本",
            "voice": "alloy",     // 可选，默认 alloy
            "speed": 1.0,         // 可选，默认 1.0
            "input_format": "plain"  // 可选，"plain" 或 "markdown"
        }

        响应格式：
        - JSON: {"type": "sentence_start", "index": 0, "text": "...", "voice": "..."}
        - 二进制数据：WAV 音频块
        - JSON: {"type": "sentence_end", "index": 0}
        - JSON: {"type": "done", "total_sentences": N}
        - JSON: {"type": "error", "message": "错误信息"}
        """
        await websocket.accept()
        logger = logging.getLogger(__name__)
        logger.info("WebSocket connection established")

        try:
            while True:
                # 接收客户端发送的数据
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data[:100]}...")

                try:
                    # 解析 JSON 数据
                    request_data = json.loads(data)
                    text = request_data.get("text", "")
                    voice = request_data.get("voice", "alloy")
                    speed = request_data.get("speed", 1.0)
                    input_format = request_data.get("input_format", "plain")

                    if not text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Text cannot be empty"
                        })
                        continue

                    logger.info(f"Processing TTS: voice={voice}, speed={speed}, input_format={input_format}")

                    # 验证语速范围
                    if speed < 0.25 or speed > 4.0:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Speed must be between 0.25 and 4.0"
                        })
                        continue

                    # 生成流式音频
                    total_chunks = 0
                    total_bytes = 0

                    async for audio_chunk, metadata in tts_service.generate_audio_stream(
                        text=text,
                        voice=voice,
                        speed=speed,
                        input_format=input_format
                    ):
                        # 发送音频数据
                        if audio_chunk:
                            total_chunks += 1
                            total_bytes += len(audio_chunk)
                            await websocket.send_bytes(audio_chunk)

                            # 让出控制权，允许其他协程执行
                            await asyncio.sleep(0)

                        # 发送元数据
                        if metadata:
                            await websocket.send_json(metadata)

                    logger.info(f"TTS completed: {total_chunks} chunks, {total_bytes} bytes")

                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                except InvalidInputError as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": e.message
                    })
                except Exception as e:
                    logger.error(f"Error processing TTS request: {e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            try:
                await websocket.close()
            except:
                pass

    return websocket_tts
