"""
特殊符号处理模块

处理数学符号、单位符号、货币符号等特殊符号。
"""

import re
from typing import Optional


class SpecialSymbolProcessor:
    """特殊符号处理器，处理数学符号、单位符号、货币符号等"""

    def __init__(self, language: str = 'auto'):
        """
        初始化特殊符号处理器

        Args:
            language: 'zh' (中文), 'en' (英文), 'auto' (自动检测)
        """
        self.language = language

    def detect_language(self, text: str) -> str:
        """
        自动检测文本语言

        Args:
            text: 输入文本

        Returns:
            'zh' 或 'en'
        """
        if not text:
            return 'en'

        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)

        if total_chars > 0 and chinese_count / total_chars > 0.3:
            return 'zh'
        return 'en'

    def process(self, text: str) -> str:
        """
        处理文本中的所有特殊符号

        Args:
            text: 输入文本

        Returns:
            处理后的文本
        """
        if not text:
            return text

        # 自动检测语言
        lang = self.language if self.language != 'auto' else self.detect_language(text)

        # 按顺序处理
        text = self.process_currency_extended(text, lang)
        text = self.process_math_symbols(text, lang)
        text = self.process_unit_symbols(text, lang)

        return text

    def process_math_symbols(self, text: str, language: str = None) -> str:
        """
        数学符号转换
        ± → 正负号 / plus minus
        × → 乘以 / times
        ÷ → 除以 / divided by
        = → 等于 / equals
        ≠ → 不等于 / not equal to
        < → 小于 / less than
        > → 大于 / greater than
        ≤ → 小于等于 / less than or equal to
        ≥ → 大于等于 / greater than or equal to
        """
        if language is None:
            language = self.language if self.language != 'auto' else self.detect_language(text)

        # 数学符号映射
        if language == 'zh':
            mappings = [
                (r'(\d+)\s*×\s*(\d+)', r'\1乘以\2'),
                (r'(\d+)\s*÷\s*(\d+)', r'\1除以\2'),
                (r'±\s*(\d+)', r'正负\1'),
                (r'(\d+)\s*±', r'\1正负'),
                (r'≠', '不等于'),
                (r'≤', '小于等于'),
                (r'≥', '大于等于'),
                (r'(?<!\w)=(?!\w)', '等于'),
                (r'<', '小于'),
                (r'>', '大于'),
            ]
        else:  # English
            mappings = [
                (r'(\d+)\s*×\s*(\d+)', r'\1 times \2'),
                (r'(\d+)\s*÷\s*(\d+)', r'\1 divided by \2'),
                (r'±\s*(\d+)', r'plus minus \1'),
                (r'(\d+)\s*±', r'\1 plus minus'),
                (r'≠', 'not equal to'),
                (r'≤', 'less than or equal to'),
                (r'≥', 'greater than or equal to'),
                (r'(?<!\w)=(?!\w)', 'equals'),
                (r'<', 'less than'),
                (r'>', 'greater than'),
            ]

        for pattern, replacement in mappings:
            text = re.sub(pattern, replacement, text)

        return text

    def process_unit_symbols(self, text: str, language: str = None) -> str:
        """
        单位符号转换
        % → 百分之 / percent
        ° → 度 / degrees
        ℃ → 摄氏度 / degrees Celsius
        ℉ → 华氏度 / degrees Fahrenheit
        """
        if language is None:
            language = self.language if self.language != 'auto' else self.detect_language(text)

        # 单位符号映射
        if language == 'zh':
            mappings = [
                (r'(\d+)%', r'百分之\1'),
                (r'(\d+)\s*°', r'\1度'),
                (r'(\d+)℃', r'\1摄氏度'),
                (r'(\d+)°C', r'\1摄氏度'),
                (r'(\d+)°c', r'\1摄氏度'),
                (r'(\d+)℉', r'\1华氏度'),
                (r'(\d+)°F', r'\1华氏度'),
            ]
        else:  # English
            mappings = [
                (r'(\d+)%', r'\1 percent'),
                (r'(\d+)\s*°', r'\1 degrees'),
                (r'(\d+)℃', r'\1 degrees Celsius'),
                (r'(\d+)°C', r'\1 degrees Celsius'),
                (r'(\d+)°c', r'\1 degrees Celsius'),
                (r'(\d+)℉', r'\1 degrees Fahrenheit'),
                (r'(\d+)°F', r'\1 degrees Fahrenheit'),
            ]

        for pattern, replacement in mappings:
            text = re.sub(pattern, replacement, text)

        return text

    def process_currency_extended(self, text: str, language: str = None) -> str:
        """
        扩展货币符号处理
        新增: ₽卢布, ₹卢比, ₩韩元, ₿比特币
        """
        if language is None:
            language = self.language if self.language != 'auto' else self.detect_language(text)

        # 货币符号映射
        if language == 'zh':
            mappings = [
                (r'₽\s*(\d+(?:\.\d+)?)', r'\1卢布'),
                (r'(\d+(?:\.\d+)?)\s*₽', r'\1卢布'),
                (r'₹\s*(\d+(?:\.\d+)?)', r'\1卢比'),
                (r'(\d+(?:\.\d+)?)\s*₹', r'\1卢比'),
                (r'₩\s*(\d+(?:\.\d+)?)', r'\1韩元'),
                (r'(\d+(?:\.\d+)?)\s*₩', r'\1韩元'),
                (r'₿\s*(\d+(?:\.\d+)?)', r'\1比特币'),
                (r'(\d+(?:\.\d+)?)\s*₿', r'\1比特币'),
            ]
        else:  # English
            mappings = [
                (r'₽\s*(\d+(?:\.\d+)?)', r'\1 rubles'),
                (r'(\d+(?:\.\d+)?)\s*₽', r'\1 rubles'),
                (r'₹\s*(\d+(?:\.\d+)?)', r'\1 rupees'),
                (r'(\d+(?:\.\d+)?)\s*₹', r'\1 rupees'),
                (r'₩\s*(\d+(?:\.\d+)?)', r'\1 won'),
                (r'(\d+(?:\.\d+)?)\s*₩', r'\1 won'),
                (r'₿\s*(\d+(?:\.\d+)?)', r'\1 bitcoins'),
                (r'(\d+(?:\.\d+)?)\s*₿', r'\1 bitcoins'),
            ]

        for pattern, replacement in mappings:
            text = re.sub(pattern, replacement, text)

        return text
