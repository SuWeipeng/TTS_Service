"""
API 模块

导出 API 相关类和函数。
"""

from .app import create_app, app
from .middleware import setup_middleware, setup_cors, setup_error_handlers
from .routes import create_routes
from .websocket import create_websocket_route

__all__ = [
    "create_app",
    "app",
    "setup_middleware",
    "setup_cors",
    "setup_error_handlers",
    "create_routes",
    "create_websocket_route",
]
