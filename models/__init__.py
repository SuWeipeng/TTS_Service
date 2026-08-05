"""
模型模块

导出所有模型实现。
"""

from .base import BaseModel

# 延迟导入模型类，只在需要时导入
# 避免在未安装对应包时出现导入错误

def get_model_class(model_type: str):
    """
    根据模型类型获取模型类

    Args:
        model_type: 模型类型 ("kokoro" 或 "melo")

    Returns:
        模型类
    """
    if model_type == "kokoro":
        from .kokoro import KokoroModel
        return KokoroModel
    elif model_type == "melo":
        from .melo import MeloModel
        return MeloModel
    else:
        raise ValueError(f"Unknown model type: {model_type}")

__all__ = [
    "BaseModel",
    "get_model_class",
]
