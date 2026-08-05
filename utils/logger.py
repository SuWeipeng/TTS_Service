"""
日志配置工具

提供统一的日志配置。
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    force: bool = False
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称（默认使用调用模块名称）
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: 日志文件路径（可选，默认只输出到控制台）
        format_string: 日志格式字符串
        force: 是否强制重新配置（即使已有处理器）

    Returns:
        配置好的日志记录器
    """
    if name is None:
        # 自动获取调用模块的名称
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', 'root')

    logger = logging.getLogger(name)

    # 如果 force=True，清除现有处理器
    if force:
        logger.handlers.clear()

    # 避免重复添加处理器（除非 force=True）
    if logger.handlers and not force:
        return logger

    # 如果 logger 没有处理器，或者 force=True，则添加处理器
    if not logger.handlers or force:
        # 设置日志级别
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)

        # 防止传播到根 logger，避免重复日志
        logger.propagate = False

        # 默认格式
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        formatter = logging.Formatter(format_string)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 文件处理器（可选）
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已配置的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)
