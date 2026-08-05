"""
数字处理模块（Kokoro 专用）

将数字转换为英文单词，专门用于 Kokoro TTS 模型。
Kokoro 模型需要将数字转换为英文单词才能正确发音。
"""

import re


class NumberReplacer:
    """数字替换器（Kokoro 专用）"""

    # 数字映射表
    num_to_word_ones = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }
    num_to_word_teens = {str(k): v for k, v in enumerate([
        'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
        'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'
    ], 10)}
    num_to_word_tens = {str(k): v for k, v in enumerate([
        'twenty', 'thirty', 'forty', 'fifty',
        'sixty', 'seventy', 'eighty', 'ninety'
    ], 2)}

    def __init__(self):
        pass

    # 辅助方法
    def _two_digit(self, n):
        if n < 10:
            return self.num_to_word_ones[str(n)]
        elif 10 <= n < 20:
            return self.num_to_word_teens[str(n)]
        else:
            ten_digit = n // 10
            one_digit = n % 10
            word = self.num_to_word_tens[str(ten_digit)]
            if one_digit != 0:
                word += ' ' + self.num_to_word_ones[str(one_digit)]

            return word

    def _three_digit(self, n):
        return ' '.join(filter(None, [
            f"{self.num_to_word_ones[str(n//100)]} hundred" if n//100 else None,
            self._two_digit(n%100) if n%100 else None
        ]))

    def _two_digit_word(self, n_str):
        """专门用于处理两位数字的单词转换"""
        n = int(n_str)
        if n < 10:
            return self.num_to_word_ones[str(n)]
        elif 10 <= n < 20:
            return self.num_to_word_teens[n_str]
        else:
            ten = n_str[0]
            one = n_str[1]
            word = self.num_to_word_tens[ten]
            if one != '0':
                word += ' ' + self.num_to_word_ones[one]
            return word

    def number_to_words(self, num_str):
        try:
            num = float(num_str)
        except ValueError:
            return num_str

        is_negative = num < 0
        if is_negative:
            num = abs(num)

        int_part, dec_part = str(num).split('.')
        int_words = self._int_number_to_words(int(int_part))

        result = ("negative " if is_negative else "") + int_words

        if dec_part != '0':
            result += " point " + " ".join(self.num_to_word_ones[d] for d in dec_part)

        return result.strip()

    def _int_number_to_words(self, n):
        if n == 0:
            return self.num_to_word_ones['0']

        words = []
        for unit, name in [(1_000_000, 'million'), (1_000, 'thousand')]:
            if n // unit:
                words.append(f"{self._three_digit(n//unit)} {name}")
                n %= unit

        if n:
            words.append(self._three_digit(n))

        return " ".join(words)

    def replace_phone_numbers_with_words(self, text):
        def replace_digits(match):
            digits = ''.join(filter(str.isdigit, match.group(0)))
            if not digits:
                return match.group(0)
            words = ' '.join(self.num_to_word_ones[d] for d in digits)
            return words

        # 支持格式如：
        # 123-456-7890
        # (010) 1234 5678
        # +86 138 1234 5678
        phone_pattern = r'(?<![$€£¥¢])(?:(?:\+\d{1,3}[ -])|(?:\(\d{2,4}\)[ -]?)|(?:\d{3,4}[ -]))\d{3,8}'

        return re.sub(phone_pattern, replace_digits, text)

    def replace_ip_addresses_with_words(self, text):
        """
        匹配并替换文本中的 IP 地址为单词形式
        支持 IPv4 格式：xxx.xxx.xxx.xxx (0-255.0-255.0-255.0-255)
        """
        def replace_ip(match):
            ip = match.group(0)
            parts = ip.split('.')

            # 验证是否为有效的 IPv4 地址
            try:
                for part in parts:
                    if not (0 <= int(part) <= 255):
                        return ip  # 如果不是有效 IP，返回原文
            except ValueError:
                return ip

            # 将每个部分转换为单词
            word_parts = []
            for part in parts:
                # 处理前导零的情况
                if part.startswith('0') and len(part) > 1:
                    # 如果有前导零，逐位读出
                    word_parts.append(' '.join(self.num_to_word_ones[d] for d in part))
                else:
                    word_parts.append(self.number_to_words(part))

            return ' dot '.join(word_parts)

        # IPv4 地址的正则表达式
        # 匹配 0-255.0-255.0-255.0-255 格式
        ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b'

        return re.sub(ipv4_pattern, replace_ip, text)

    def format_year(self, year_str):
        if len(year_str) != 4:
            return self.number_to_words(year_str)
        year_num = int(year_str)
        if 1000 <= year_num <= 1999:
            first_two = year_str[:2]
            last_two = year_str[2:]

            # 特殊处理如 1900 → nineteen hundred
            if last_two == '00':
                return f"{self._two_digit_word(first_two)} hundred"
            else:
                if int(last_two) < 10:
                    return f"{self._two_digit_word(first_two)} oh {self._two_digit_word(last_two)}"
                else:
                    return f"{self._two_digit_word(first_two)} {self._two_digit_word(last_two)}"
        elif 2000 <= year_num <= 2099:
            if year_num == 2000:
                return "two thousand"
            else:
                return f"two thousand {self.number_to_words(year_str[2:])}"
        else:
            return self.replace_each_digit_with_words(year_str)

    def remove_thousand_separators(self, num_str):
        """
        只有当逗号为合法的千分位格式时才移除
        示例：
            - '1,000' → '1000'
            - '-12,345.67' → '-12345.67'
            - '1,00,000'（印度格式） → '100000'
            - 其他情况（如句中逗号）不处理
        """
        # 匹配合法的千分位数字格式
        thousand_pattern = r'^(-)?\d{1,3}(,\d{3})*(\.\d+)?$'

        if re.match(thousand_pattern, num_str):
            return num_str.replace(',', '')
        else:
            return num_str

    def clean_numbers_in_text(self, text):
        """
        遍历文本中的所有数字（支持负数、小数、千分位格式），清理合法的千分位逗号。
        """

        def clean_match(match):
            num_str = match.group(0)
            return self.remove_thousand_separators(num_str)

        # 匹配所有可能带千分位逗号的数字
        return re.sub(r'-?\d{1,3}(?:,\d{3})*(?:\.\d+)?', clean_match, text)

    def replace_list_number_with_words(self, text):
        # 匹配带标点的编号格式（支持 . , ) ] } 等）
        def replace(match):
            num_str = match.group(1)
            suffix = match.group(2)
            words = self.number_to_words(num_str)
            return f"{words}{suffix}"

        # 支持格式如：1., 2), 3], 4}, 5
        return re.sub(r'(\d+)([.\)\]\}\s]+)', replace, text)

    def replace_numbers_with_words(self, text, year_mode=False):
        def replace_match(match):
            result = None
            num_str = match.group(0)

            is_negative = num_str.startswith('-')
            if is_negative:
                num_str = num_str[1:]

            if year_mode and num_str.isdigit() and 1000 <= int(num_str) <= 9999:
                result = self.format_year(num_str)
            else:
                result = ("negative " if is_negative else "") + self.number_to_words(num_str)
            return result

        # 替换货币符号
        text = re.sub(
            r'(?<![\w.,:])\s*(-?)\s*([\$€£¥USD EUR GBP CNY])\s*(\d+(?:\.\d+)?)(?=\b|[\s,.;:?!]|$)',
            self._replace_money_with_words,
            text
        )

        # 更精确的数字匹配正则（支持负数和小数）
        text = re.sub(
            r'(?<![\d.])-?\d+(?:\.\d+)?(?!\d)',
            replace_match,
            text
        )

        return ' '.join(text.split())

    def _replace_money_with_words(self, match):
        sign = match.group(1)  # 负号或空
        currency_symbol = match.group(2).strip('$')  # 货币符号
        amount_str = match.group(3)  # 数字部分

        try:
            amount_value = float(amount_str)
        except ValueError:
            return match.group(0)

        # 添加负号
        if sign:
            amount_value = -amount_value
            amount_str = str(amount_value)
        else:
            amount_str = str(amount_value)

        amount_words = self.number_to_words(amount_str)

        if amount_str.endswith('.0'):
            amount_words = amount_words.replace(' point zero', '')

        currency = {
            '$': 'dollar', 'USD': 'dollar', '€': 'euro',
            'EUR': 'euro', '£': 'pound', 'GBP': 'pound',
            '¥': 'yen', 'CNY': 'yuan'
        }.get(currency_symbol, 'dollar')

        plural_suffix = 's' if abs(amount_value) != 1 else ''

        if amount_value < 0:
            abs_amount_words = amount_words.replace('minus ', '').strip()
            return f"a loss of {abs_amount_words} {currency}{plural_suffix}"
        else:
            return f"{amount_words} {currency}{plural_suffix}"

    def replace_single_digits_with_words(self, text):
        return re.sub(r'\b\d\b', lambda m: self.num_to_word_ones[m.group(0)], text)

    def replace_each_digit_with_words(self, text):
        return re.sub(r'\d', lambda m: self.num_to_word_ones[m.group(0)] + ' ', text).rstrip()


def is_chinese_dominant(text: str) -> bool:
    """
    检查文本中中文字符是否超过35%

    Args:
        text: 输入文本

    Returns:
        是否中文占主导
    """
    if not text:
        return False

    chinese_count = 0
    total_chars = len(text)

    for char in text:
        # 检查是否为中文字符（包括中文标点符号）
        if '\u4e00' <= char <= '\u9fff' or '\u3000' <= char <= '\u303f' or '\uff00' <= char <= '\uffef':
            chinese_count += 1

    res = chinese_count / total_chars
    return res > 0.35


def replace_range_symbols(text: str) -> str:
    """
    将数字之间的-或~替换为'到'

    Args:
        text: 输入文本

    Returns:
        处理后的文本
    """
    # 匹配数字-数字或数字~数字的模式
    pattern = r'(\d+)\s*[-~]\s*(\d+)'

    def replace_func(match):
        return f"{match.group(1)}到{match.group(2)}"

    return re.sub(pattern, replace_func, text)
