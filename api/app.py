"""
FastAPI 应用工厂

创建和配置 FastAPI 应用。
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging

from config.settings import settings
from models import get_model_class
from services import create_tts_service
from api.middleware import setup_middleware
from api.routes import create_routes
from api.websocket import create_websocket_route
from utils.logger import setup_logger


def create_model():
    """
    根据配置创建模型实例

    Returns:
        TTS 模型实例
    """
    logger = logging.getLogger(__name__)
    model_type = settings.tts_model.lower()

    logger.info(f"Initializing {model_type} model...")

    # 使用 get_model_class 动态获取模型类
    ModelClass = get_model_class(model_type)
    model = ModelClass()

    # 初始化模型（如果是 eager loading）
    if model.get_loading_strategy().value == "eager":
        model.initialize_model()
        logger.info(f"{model.get_model_name()} model loaded successfully")
    else:
        logger.info(f"{model.get_model_name()} model configured with lazy loading")

    return model


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用

    Returns:
        FastAPI 应用实例
    """
    # 设置日志
    setup_logger("TTS_Service", level=settings.log_level)

    # 创建 FastAPI 应用
    app = FastAPI(
        title="TTS Service API",
        description="Text-to-Speech service with OpenAI API compatibility",
        version="1.0.0"
    )

    # 设置中间件
    setup_middleware(app)

    # 创建模型和服务
    model = create_model()
    tts_service = create_tts_service(model)

    # 将服务添加到应用状态
    app.state.tts_service = tts_service

    # 创建路由
    api_router = create_routes(tts_service)
    app.include_router(api_router)

    # 创建 WebSocket 路由
    websocket_route = create_websocket_route(tts_service)
    app.add_api_websocket_route("/ws/tts", websocket_route)

    # 根路由
    @app.get("/")
    async def root():
        """根路径"""
        return JSONResponse({
            "name": "TTS Service API",
            "version": "1.0.0",
            "model": tts_service.get_model_name(),
            "endpoints": {
                "tts": "/v1/audio/speech",
                "voices": "/v1/audio/voices",
                "health": "/health",
                "websocket": "/ws/tts"
            }
        })

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port
    )
