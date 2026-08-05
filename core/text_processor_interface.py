"""
文本处理器抽象接口

定义文本处理的标准接口，用于预处理 TTS 输入文本。
"""

from abc import ABC, abstractmethod
from typing import List


class TextProcessorInterface(ABC):
    """文本处理器抽象接口"""

    @abstractmethod
    def process(self, text: str, input_format: str = "plain") -> str:
        """
        处理输入文本

        Args:
            text: 原始文本
            input_format: 输入格式（"plain" 或 "markdown"）

        Returns:
            处理后的文本
        """
        pass

    @abstractmethod
    def split_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子

        Args:
            text: 输入文本

        Returns:
            句子列表
        """
        pass

    @abstractmethod
    def clean_markdown(self, text: str) -> str:
        """
        清洗 Markdown 格式

        Args:
            text: Markdown 文本

        Returns:
            纯文本
        """
        pass
