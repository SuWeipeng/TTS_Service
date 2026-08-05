"""
服务模块

导出业务逻辑服务类。
"""

from .tts_service import TTSService, create_tts_service
from .queue_manager import (
    TTSQueueManager,
    get_queue_manager,
    set_queue_manager
)

__all__ = [
    "TTSService",
    "create_tts_service",
    "TTSQueueManager",
    "get_queue_manager",
    "set_queue_manager",
]
