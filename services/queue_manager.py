"""
请求队列管理器

管理并发 TTS 请求，防止资源冲突。
"""

import asyncio
from collections import deque
from typing import Optional, Dict, Any
import logging

from core.exceptions import TTSError


class TTSQueueManager:
    """TTS 请求队列管理器"""

    def __init__(self, max_queue_size: int = 100):
        """
        初始化队列管理器

        Args:
            max_queue_size: 最大队列大小
        """
        self.queue = deque()
        self.processing = False
        self.max_queue_size = max_queue_size
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def add_request(self, request_data: Dict[str, Any]) -> bool:
        """
        添加请求到队列

        Args:
            request_data: 请求数据

        Returns:
            是否成功添加
        """
        async with self.lock:
            if len(self.queue) >= self.max_queue_size:
                self.logger.warning("Queue is full, rejecting request")
                return False
            self.queue.append(request_data)
            self.logger.info(f"Request added to queue. Queue size: {len(self.queue)}")
            return True

    async def get_next_request(self) -> Optional[Dict[str, Any]]:
        """
        获取队列中的下一个请求

        Returns:
            请求数据或 None
        """
        async with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None

    async def wait_for_request(self) -> Optional[Dict[str, Any]]:
        """
        等待下一个请求（阻塞）

        Returns:
            请求数据或 None
        """
        while True:
            request = await self.get_next_request()
            if request:
                return request
            await asyncio.sleep(0.1)

    def get_queue_size(self) -> int:
        """
        获取当前队列大小

        Returns:
            队列大小
        """
        return len(self.queue)

    def is_processing(self) -> bool:
        """
        检查是否正在处理请求

        Returns:
            是否正在处理
        """
        return self.processing

    def set_processing(self, processing: bool) -> None:
        """
        设置处理状态

        Args:
            processing: 处理状态
        """
        self.processing = processing

    async def clear(self) -> None:
        """清空队列"""
        async with self.lock:
            self.queue.clear()
            self.logger.info("Queue cleared")


# 全局队列管理器实例
_global_queue_manager: Optional[TTSQueueManager] = None


def get_queue_manager() -> TTSQueueManager:
    """
    获取全局队列管理器实例

    Returns:
        队列管理器实例
    """
    global _global_queue_manager
    if _global_queue_manager is None:
        _global_queue_manager = TTSQueueManager()
    return _global_queue_manager


def set_queue_manager(manager: TTSQueueManager) -> None:
    """
    设置全局队列管理器实例

    Args:
        manager: 队列管理器实例
    """
    global _global_queue_manager
    _global_queue_manager = manager
