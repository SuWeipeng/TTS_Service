"""
中间件配置

提供 CORS 和错误处理中间件。
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Callable
import logging

from core.exceptions import TTSError, openai_error_response
from config.settings import settings


def setup_cors(app: FastAPI) -> None:
    """
    设置 CORS 中间件

    Args:
        app: FastAPI 应用实例
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    设置错误处理器

    Args:
        app: FastAPI 应用实例
    """

    @app.exception_handler(TTSError)
    async def tts_error_handler(request: Request, exc: TTSError):
        """处理 TTS 自定义异常"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=openai_error_response(exc)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理 HTTP 异常"""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"message": exc.detail, "type": "http_error"}}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理通用异常"""
        logging.getLogger(__name__).error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "Internal server error",
                    "type": "server_error"
                }
            }
        )


def setup_middleware(app: FastAPI) -> None:
    """
    设置所有中间件

    Args:
        app: FastAPI 应用实例
    """
    setup_cors(app)
    setup_error_handlers(app)
