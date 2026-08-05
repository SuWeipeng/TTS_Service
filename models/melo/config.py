"""
MeloTTS 模型配置

定义 MeloTTS 模型的配置常量。
"""

from typing import Dict, Any, List

# MeloTTS speaker_id 映射
# 中文音色和英文音色的映射关系
# 注意：alloy 是双语音色，始终使用 ZH 模型
DEFAULT_SPEAKER_MAPPING = {
    # 双语音色（始终使用 ZH 模型）
    "alloy": {"speaker_id": "BILINGUAL", "language": "ZH"},

    # 英文音色（根据口音选择）
    "echo": {"speaker_id": "EN-US", "language": "EN"},
    "fable": {"speaker_id": "EN-BR", "language": "EN"},
    "onyx": {"speaker_id": "EN-Default", "language": "EN"},
    "nova": {"speaker_id": "EN-US", "language": "EN"},
    "shimmer": {"speaker_id": "EN-AU", "language": "EN"},
}

# 英文口音映射
EN_ACCENT_MAPPING = {
    "EN-US": "EN-US",    # 美式英语
    "EN-BR": "EN-BR",    # 英式英语
    "EN_INDIA": "EN_INDIA",  # 印度英语
    "EN-AU": "EN-AU",    # 澳大利亚英语
    "EN-Default": "EN-Default",  # 默认英语
}

# 支持的音色列表
SUPPORTED_VOICES = [
    "BILINGUAL",     # 中英双语
    "EN-US",        # 美式英语
    "EN-BR",        # 英式英语
    "EN-Default",   # 默认英语
    "EN-AU",        # 澳大利亚英语
]

# OpenAI 兼容的音色列表
OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# 默认音色
DEFAULT_VOICE = "alloy"


def detect_language(text: str) -> str:
    """
    检测文本语言
    如果包含中文字符返回 'ZH'，否则返回 'EN'

    Args:
        text: 输入文本

    Returns:
        'ZH' 或 'EN'
    """
    if not text:
        return 'EN'

    # 检查中文字符
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return 'ZH'

    return 'EN'


def get_speaker_and_model_info(voice: str, text: str, speaker_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据音色和文本语言获取对应的 MeloTTS 模型信息

    双语音色（alloy）始终使用 ZH 模型，支持中英文混合文本。

    Args:
        voice: 音色名称
        text: 要合成的文本
        speaker_mapping: speaker_id 映射配置

    Returns:
        {
            "speaker_id": str,  # speaker_id（用于后续转换为整数ID）
            "language": str,    # 语言代码（'ZH' 或 'EN'）
            "is_bilingual": bool  # 是否是双语音色
        }
    """
    # 检测文本语言
    language = detect_language(text)

    # 检查是否是双语音色
    voice_info = speaker_mapping.get(voice, speaker_mapping.get("onyx"))  # fallback to onyx
    speaker_id = voice_info.get("speaker_id", "BILINGUAL")

    # 检查是否是双语音色
    is_bilingual = (speaker_id == "BILINGUAL")

    # 双语音色始终使用 ZH 模型
    if is_bilingual:
        return {
            "speaker_id": speaker_id,
            "language": "ZH",
            "is_bilingual": True
        }

    # 根据语言选择 speaker
    if language == 'ZH':
        # 中文文本使用 ZH 模型
        return {
            "speaker_id": "ZH",
            "language": "ZH",
            "is_bilingual": False
        }
    else:
        # 英文文本使用英文音色
        return {
            "speaker_id": speaker_id,
            "language": "EN",
            "is_bilingual": False
        }


def map_voice_to_speaker_id(voice: str, speaker_mapping: Dict[str, Any]) -> str:
    """
    将音色名称映射到 speaker_id

    Args:
        voice: 音色名称
        speaker_mapping: speaker_id 映射配置

    Returns:
        speaker_id 字符串
    """
    voice_info = speaker_mapping.get(voice, speaker_mapping.get("onyx"))
    return voice_info.get("speaker_id", "BILINGUAL")


def get_voice_language(voice: str, speaker_mapping: Dict[str, Any]) -> str:
    """
    获取音色对应的语言

    Args:
        voice: 音色名称
        speaker_mapping: speaker_id 映射配置

    Returns:
        语言代码（'ZH' 或 'EN'）
    """
    voice_info = speaker_mapping.get(voice, speaker_mapping.get("onyx"))
    return voice_info.get("language", "EN")
