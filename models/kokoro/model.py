"""
Kokoro TTS 模型实现

封装 kokoro-github 库，实现 TTS 模型接口。
"""

import os
import asyncio
import torch
from typing import AsyncIterator, Tuple, Dict, Any
from kokoro.pipeline import KPipeline
from kokoro.model import KModel
import numpy as np
import soundfile as sf
import io
import logging

from core.tts_interface import ModelLoadingStrategy
from models.base import BaseModel
from models.kokoro.config import (
    get_lang_code, is_bilingual_voice, is_chinese_dominant,
    get_optimal_voice, BILINGUAL_VOICES, SUPPORTED_VOICES
)
from text_processing import (
    MarkdownCleaner, SentenceSplitter, SpecialSymbolProcessor,
    NumberReplacer, is_chinese_dominant as text_is_chinese_dominant,
    replace_range_symbols
)
from utils.audio import AudioConverter
from utils.device import get_device
from config.settings import settings


class KokoroModel(BaseModel):
    """Kokoro TTS 模型实现"""

    def __init__(self):
        BaseModel.__init__(self)
        self.device = None
        self.kmodel = None
        self.lang_pipelines = {}
        self.en_pipeline = None
        self.en_callable = None

        # 文本处理器
        self.markdown_cleaner = MarkdownCleaner()
        self.sentence_splitter = SentenceSplitter()
        self.symbol_processor = SpecialSymbolProcessor()
        self.number_replacer = NumberReplacer()

        # 音色映射（从配置加载或使用默认）
        self.voice_mapping = self._load_voice_mapping()

    def _load_voice_mapping(self) -> Dict[str, str]:
        """加载音色映射配置"""
        try:
            import json
            mapping_file = settings.kokoro_voice_mapping
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("mappings", {})
        except Exception as e:
            self.logger.warning(f"Failed to load voice mapping from {settings.kokoro_voice_mapping}: {e}")

        # 使用默认映射
        from models.kokoro.config import DEFAULT_VOICE_MAPPING
        return DEFAULT_VOICE_MAPPING

    def get_model_name(self) -> str:
        """返回模型标识符"""
        return "kokoro"

    def get_supported_voices(self) -> list:
        """返回支持的音色列表"""
        return SUPPORTED_VOICES

    def map_voice(self, requested_voice: str, text: str) -> str:
        """
        将请求的音色映射到 Kokoro 特定的音色

        Args:
            requested_voice: 用户请求的音色（如 "alloy"）
            text: 要合成的文本

        Returns:
            Kokoro 特定的音色标识符
        """
        # 从映射表中获取
        mapped_voice = self.voice_mapping.get(requested_voice, requested_voice)

        # 根据文本语言优化音色选择
        optimal_voice = get_optimal_voice(mapped_voice, text)

        return optimal_voice

    def get_loading_strategy(self) -> ModelLoadingStrategy:
        """返回模型加载策略"""
        return ModelLoadingStrategy.EAGER

    def initialize_model(self) -> None:
        """初始化/加载模型"""
        if self.is_model_loaded():
            return

        try:
            self.logger.info("Initializing Kokoro model...")

            # 检测设备（自动检测最佳设备）
            self.device = get_device('auto')
            self.logger.info(f"Using device: {self.device}")

            # 检查模型文件
            config_path = settings.kokoro_config_path
            model_path = settings.kokoro_model_path

            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            # 加载模型
            self.kmodel = KModel(
                config=config_path,
                model=model_path,
                repo_id=settings.kokoro_repo_id
            ).to(self.device).eval()

            # 初始化英文 pipeline
            self.en_pipeline = KPipeline(lang_code='a', repo_id=settings.kokoro_repo_id, model=False)
            self.en_callable = self._create_en_callable()

            self.logger.info("Kokoro model initialized successfully")
            self.set_model_loaded(True)

        except Exception as e:
            self.logger.error(f"Failed to initialize Kokoro model: {e}")
            from core.exceptions import ModelInitializationError
            raise ModelInitializationError("kokoro", str(e))

    def _create_en_callable(self):
        """创建英文 callable"""
        def en_callable(text):
            if text == 'Kokoro':
                return 'kˈOkəɹO'
            elif text == 'Sol':
                return 'sˈOl'
            return next(self.en_pipeline(text)).phonemes
        return en_callable

    def _get_pipeline(self, lang_code: str):
        """获取指定语言的 pipeline"""
        if lang_code in self.lang_pipelines:
            return self.lang_pipelines[lang_code]

        pipe = KPipeline(
            lang_code=lang_code,
            model=self.kmodel,
            repo_id=settings.kokoro_repo_id,
            en_callable=self.en_callable
        )
        self.lang_pipelines[lang_code] = pipe
        return pipe

    def _process_text(self, text: str, input_format: str = "plain") -> str:
        """
        处理输入文本

        处理流程:
            1. 清洗 Markdown 格式 (如果 input_format="markdown")
            2. 特殊符号处理
            3. 数字处理逻辑（仅英文或中英混合）

        Args:
            text: 输入文本
            input_format: "plain" (纯文本) 或 "markdown" (Markdown格式)

        Returns:
            处理后的文本
        """
        # 1. 清洗 Markdown 格式（先清洗，再检测语言）
        if input_format == "markdown":
            text = self.markdown_cleaner.clean(text)

        # 2. 特殊符号处理
        text = self.symbol_processor.process(text)

        # 3. 数字处理逻辑
        if text_is_chinese_dominant(text):
            # 如果中文字符超过35%，只处理数字范围符号
            text = replace_range_symbols(text)
        else:
            # 如果中文字符不超过35%，则进行完整的处理
            text = self.number_replacer.replace_phone_numbers_with_words(text)
            text = self.number_replacer.replace_ip_addresses_with_words(text)
            text = self.number_replacer.clean_numbers_in_text(text)
            text = self.number_replacer.replace_numbers_with_words(text, year_mode=True)
            text = self.number_replacer.replace_list_number_with_words(text)

        return text

    async def generate_audio(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        **kwargs
    ) -> Tuple[bytes, str]:
        """
        生成完整音频

        Args:
            text: 输入文本
            voice: 音色（已映射的 Kokoro 音色）
            speed: 语速
            **kwargs: 其他参数（input_format, skip_processing）

        Returns:
            (audio_bytes, media_type) 元组
        """
        if not text.strip():
            from core.exceptions import InvalidInputError
            raise InvalidInputError("Text cannot be empty")

        input_format = kwargs.get('input_format', 'plain')
        skip_processing = kwargs.get('skip_processing', False)
        target_format = kwargs.get('target_format', 'mp3')

        # 处理文本（如果需要）
        processed_text = text if skip_processing else self._process_text(text, input_format)

        # 分句处理
        sentences = self.sentence_splitter.split(processed_text)

        if not sentences:
            from core.exceptions import TextProcessingError
            raise TextProcessingError("No sentences found after processing")

        # 获取语言代码
        lang_code = get_lang_code(voice)

        # 获取对应语言的 pipeline
        try:
            pipeline = self._get_pipeline(lang_code)
        except AssertionError:
            from core.exceptions import AudioGenerationError
            raise AudioGenerationError(f"Unsupported lang_code: {lang_code}")

        # 合成音频（逐句生成后合并）
        audios = []
        voice_path = os.path.join(settings.kokoro_voices_dir, voice + '.pt')

        for idx, sentence in enumerate(sentences):
            # 打印送入 TTS 的句子
            log_msg = f"[Sentence {idx + 1}/{len(sentences)}] Sending to TTS: '{sentence}' (voice: {voice})"
            self.logger.info(log_msg)
            print(log_msg)  # 后备方案，确保一定能看到

            # 每句独立选择音色
            optimal_voice = get_optimal_voice(voice, sentence)
            voice_path = os.path.join(settings.kokoro_voices_dir, optimal_voice + '.pt')

            for _, _, audio in pipeline(text=sentence, voice=voice_path, speed=speed):
                if audio is not None:
                    audios.append(audio.cpu().numpy())

        if not audios:
            from core.exceptions import AudioGenerationError
            raise AudioGenerationError("Generated audio is empty")

        # 合并音频片段
        full_audio = np.concatenate(audios)

        # 转换为 WAV
        wav_bytes = AudioConverter.numpy_to_wav(full_audio)

        # 转换到目标格式
        audio_bytes, media_type = AudioConverter.convert_to_target_format(
            wav_bytes, target_format
        )

        return audio_bytes, media_type

    async def generate_audio_stream(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        **kwargs
    ) -> AsyncIterator[Tuple[bytes, dict]]:
        """
        生成流式音频

        Args:
            text: 输入文本
            voice: 音色（已映射的 Kokoro 音色）
            speed: 语速
            **kwargs: 其他参数（input_format, skip_processing）

        Yields:
            (audio_chunk, metadata) 元组
        """
        if not text.strip():
            from core.exceptions import InvalidInputError
            raise InvalidInputError("Text cannot be empty")

        input_format = kwargs.get('input_format', 'plain')
        skip_processing = kwargs.get('skip_processing', False)

        # 处理文本（如果需要）
        processed_text = text if skip_processing else self._process_text(text, input_format)

        # 分句处理
        sentences = self.sentence_splitter.split(processed_text)

        if not sentences:
            from core.exceptions import TextProcessingError
            raise TextProcessingError("No sentences found after processing")

        # 获取语言代码
        lang_code = get_lang_code(voice)

        # 获取对应语言的 pipeline
        try:
            pipeline = self._get_pipeline(lang_code)
        except AssertionError:
            from core.exceptions import AudioGenerationError
            raise AudioGenerationError(f"Unsupported lang_code: {lang_code}")

        # 逐句生成并发送
        for idx, sentence in enumerate(sentences):
            # 每句独立选择音色
            optimal_voice = get_optimal_voice(voice, sentence)

            # 打印送入 TTS 的句子（同时使用 logger 和 print 确保输出）
            log_msg = f"[Sentence {idx + 1}/{len(sentences)}] Sending to TTS: '{sentence}' (voice: {optimal_voice})"
            self.logger.info(log_msg)
            print(log_msg)  # 后备方案，确保一定能看到

            # 发送句子开始标记
            yield b'', {
                "type": "sentence_start",
                "index": idx,
                "text": sentence,
                "voice": optimal_voice
            }

            # 生成音频
            voice_path = os.path.join(settings.kokoro_voices_dir, optimal_voice + '.pt')
            chunk_count = 0

            for _, _, audio in pipeline(text=sentence, voice=voice_path, speed=speed):
                if audio is not None:
                    chunk_count += 1
                    # 将每个chunk转换为WAV字节数据
                    audio_bytes = AudioConverter.numpy_to_wav(audio.cpu().numpy())

                    # 发送音频数据
                    yield audio_bytes, {
                        "type": "audio_chunk",
                        "index": idx,
                        "chunk": chunk_count
                    }

                    # 让出控制权，允许其他协程执行
                    await asyncio.sleep(0)

            # 发送句子结束标记
            yield b'', {
                "type": "sentence_end",
                "index": idx
            }

        # 发送完成标记
        yield b'', {
            "type": "done",
            "total_sentences": len(sentences)
        }

    def cleanup(self) -> None:
        """清理模型资源"""
        if self.kmodel is not None:
            del self.kmodel
            self.kmodel = None

        self.lang_pipelines.clear()

        if self.en_pipeline is not None:
            del self.en_pipeline
            self.en_pipeline = None

        self.en_callable = None

        # 清理设备缓存
        if self.device and self.device.startswith('cuda'):
            torch.cuda.empty_cache()

        self.set_model_loaded(False)
        self.logger.info("Kokoro model cleaned up")
