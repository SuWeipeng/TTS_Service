"""
设备检测工具

自动检测最佳可用设备（CUDA/MPS/CPU）。
"""

import torch
import os
from typing import Optional


def check_device() -> str:
    """
    自动检测最佳可用设备

    优先级: CUDA > MPS > CPU

    Returns:
        设备字符串（"cuda:0", "mps", "cpu"）
    """
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        device_count = torch.cuda.device_count()
        print(f"CUDA available: {device_name}")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {device_count}")
        return 'cuda:0'
    elif torch.backends.mps.is_available():
        # macOS MPS 支持
        print("MPS (Apple Silicon) available")
        return 'mps'
    else:
        print("Using CPU")
        return 'cpu'


def get_device(device_override: Optional[str] = None) -> str:
    """
    获取设备，支持覆盖自动检测

    Args:
        device_override: 手动指定设备（"auto", "cuda:0", "cuda:1", "cpu", "mps"）

    Returns:
        设备字符串
    """
    if device_override is None:
        device_override = os.environ.get('TTS_DEVICE', 'auto')

    if device_override == 'auto':
        return check_device()
    else:
        # 验证设备是否可用
        if device_override.startswith('cuda'):
            if not torch.cuda.is_available():
                print(f"CUDA requested but not available, falling back to CPU")
                return 'cpu'
            # 验证特定的 CUDA 设备
            device_idx = int(device_override.split(':')[1]) if ':' in device_override else 0
            if device_idx >= torch.cuda.device_count():
                print(f"CUDA device {device_idx} not available, falling back to cuda:0")
                return 'cuda:0'
        elif device_override == 'mps':
            if not torch.backends.mps.is_available():
                print(f"MPS requested but not available, falling back to CPU")
                return 'cpu'
        elif device_override == 'cpu':
            pass  # CPU always available
        else:
            print(f"Unknown device '{device_override}', falling back to CPU")
            return 'cpu'

        return device_override


def get_device_info(device: str) -> dict:
    """
    获取设备详细信息

    Args:
        device: 设备字符串

    Returns:
        设备信息字典
    """
    info = {
        "device": device,
        "type": "unknown"
    }

    if device.startswith('cuda'):
        info["type"] = "cuda"
        info["available"] = torch.cuda.is_available()
        if info["available"]:
            info["device_count"] = torch.cuda.device_count()
            info["device_name"] = torch.cuda.get_device_name(0)
            info["cuda_version"] = torch.version.cuda
    elif device == 'mps':
        info["type"] = "mps"
        info["available"] = torch.backends.mps.is_available()
    elif device == 'cpu':
        info["type"] = "cpu"
        info["available"] = True

    return info


def clear_device_cache(device: str) -> None:
    """
    清理设备缓存

    Args:
        device: 设备字符串
    """
    if device.startswith('cuda') and torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        print(f"Cleared CUDA cache")
    elif device == 'mps':
        # MPS doesn't have explicit cache clearing
        pass
    else:
        # CPU doesn't need cache clearing
        pass
