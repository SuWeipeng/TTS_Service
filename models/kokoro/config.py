"""
Kokoro 模型配置

定义 Kokoro 模型的配置常量。
"""

from typing import List

# Kokoro 模型配置
KOKORO_REPO_ID = "kokoro_api"

# 双语音色列表（支持中英混合）
BILINGUAL_VOICES = ['af_maple', 'af_sol', 'bf_vale']

# OpenAI 音色到 Kokoro 音色的映射
DEFAULT_VOICE_MAPPING = {
    # OpenAI voices -> Kokoro voices
    "alloy": "bf_vale",
    "echo": "am_adam",
    "fable": "af_sol",
    "onyx": "am_michael",
    "nova": "af_sarah",
    "shimmer": "af_maple",

    # Extension voice names -> Kokoro voices
    "am_adam": "am_adam",
    "af_nicole": "af_nicole",
    "bf_emma": "bf_vale",
    "af_bella": "af_heart",
    "af_sarah": "af_sarah",
    "bm_george": "am_michael",
    "bf_isabella": "bf_vale",
    "am_michael": "am_michael",
    "af_sky": "af_maple",

    # Keep original Kokoro voices for backward compatibility
    "af_heart": "af_heart",
    "af_maple": "af_maple",
    "af_sol": "af_sol",
    "bf_vale": "bf_vale",
    "am_adam": "am_adam",
    "am_michael": "am_michael",
    "af_nicole": "af_nicole",
    "af_sarah": "af_sarah",
}

# 支持的音色列表
SUPPORTED_VOICES = [
    "af_heart",
    "af_maple",
    "af_nicole",
    "af_sarah",
    "af_sol",
    "am_adam",
    "am_michael",
    "bf_vale",
]

# OpenAI 兼容的音色列表
OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# 默认音色
DEFAULT_VOICE = "alloy"


def get_lang_code(voice: str) -> str:
    """
    根据音色获取语言代码

    Args:
        voice: 音色名称

    Returns:
        语言代码（'z' 表示中文/双语，其他表示首字母对应的语言）
    """
    if voice in BILINGUAL_VOICES:
        return 'z'
    else:
        return voice[0]


def is_bilingual_voice(voice: str) -> bool:
    """
    检查是否是双语音色

    Args:
        voice: 音色名称

    Returns:
        是否是双语音色
    """
    return voice in BILINGUAL_VOICES


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


def get_optimal_voice(user_voice: str, text: str) -> str:
    """
    根据文本语言选择最佳音色

    中文文本自动切换到双语音色，避免用纯英文音色读中文效果差。

    Args:
        user_voice: 用户指定的音色
        text: 要处理的文本

    Returns:
        最佳音色名称
    """
    # 检测文本是否包含中文
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)

    if has_chinese and user_voice not in BILINGUAL_VOICES:
        # 中文文本自动切换到默认双语音色
        return 'af_maple'

    return user_voice
