"""
MeloTTS TTS 模型实现

封装 melo-tts 库，实现 TTS 模型接口。
"""

import os
import asyncio
import tempfile
import torch
import numpy as np
from io import BytesIO
from typing import AsyncIterator, Tuple, Dict, Any
from melo.api import TTS
from scipy.io import wavfile
import logging

from core.tts_interface import ModelLoadingStrategy
from models.base import BaseModel
from models.melo.config import (
    detect_language, get_speaker_and_model_info,
    map_voice_to_speaker_id, get_voice_language,
    SUPPORTED_VOICES, DEFAULT_SPEAKER_MAPPING
)
from text_processing import MarkdownCleaner, SentenceSplitter, SpecialSymbolProcessor
from utils.audio import AudioConverter
from utils.device import get_device, clear_device_cache
from config.settings import settings


class MeloModel(BaseModel):
    """MeloTTS TTS 模型实现"""

    def __init__(self):
        BaseModel.__init__(self)
        self.device = None
        self.tts_models = {}  # {language: TTS instance}
        self.speaker_ids_map = {}  # {language: {speaker_name: speaker_id}}

        # 文本处理器（注意：MeloTTS ZH 模型可以直接处理中英文混合，不需要数字转英文）
        self.markdown_cleaner = MarkdownCleaner()
        self.sentence_splitter = SentenceSplitter()
        self.symbol_processor = SpecialSymbolProcessor()

        # 音色映射（从配置加载或使用默认）
        self.speaker_mapping = self._load_speaker_mapping()

    def _load_speaker_mapping(self) -> Dict[str, Any]:
        """加载 speaker 映射配置"""
        try:
            import json
            mapping_file = settings.melo_voice_mapping
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("mappings", {})
        except Exception as e:
            self.logger.warning(f"Failed to load speaker mapping from {settings.melo_voice_mapping}: {e}")

        # 使用默认映射
        return DEFAULT_SPEAKER_MAPPING

    def get_model_name(self) -> str:
        """返回模型标识符"""
        return "melo"

    def get_supported_voices(self) -> list:
        """返回支持的音色列表"""
        return SUPPORTED_VOICES

    def map_voice(self, requested_voice: str, text: str) -> str:
        """
        将请求的音色映射到 MeloTTS 特定的 speaker_id

        Args:
            requested_voice: 用户请求的音色（如 "alloy"）
            text: 要合成的文本

        Returns:
            MeloTTS speaker_id 字符串
        """
        return map_voice_to_speaker_id(requested_voice, self.speaker_mapping)

    def get_loading_strategy(self) -> ModelLoadingStrategy:
        """返回模型加载策略"""
        return ModelLoadingStrategy.LAZY

    def initialize_model(self) -> None:
        """初始化模型（MeloTTS 使用延迟加载）"""
        # MeloTTS 使用延迟加载策略，这里只做设备检测
        if self.device is None:
            try:
                self.device = get_device(settings.melo_device)
                self.logger.info(f"MeloTTS will use device: {self.device}")

                # 验证设备参数
                if self.device is None:
                    self.logger.warning("get_device returned None, defaulting to cpu")
                    self.device = 'cpu'
                elif not isinstance(self.device, str) or not self.device:
                    self.logger.warning(f"Invalid device value: {self.device}, defaulting to cpu")
                    self.device = 'cpu'
            except Exception as e:
                self.logger.error(f"Failed to detect device: {e}, defaulting to cpu")
                self.device = 'cpu'

        # 不立即加载模型，标记为未加载
        self.set_model_loaded(False)
        self.logger.info("MeloTTS initialized with lazy loading strategy")

    def _load_melo_model(self, language: str = 'ZH') -> Tuple[TTS, Dict[str, int]]:
        """
        延迟加载 MeloTTS 模型（支持 ZH 和 EN）

        Args:
            language: 语言代码（'ZH' 或 'EN'）

        Returns:
            (TTS instance, speaker_ids_map) 元组
        """
        if language not in self.tts_models:
            self.logger.info(f"Loading MeloTTS model ({language})...")

            # 确保 device 是有效值
            device = self.device if self.device else 'cpu'
            self.logger.info(f"Using device: {device}")

            try:
                # 使用 device 参数直接指定设备（参考工作的代码）
                tts_instance = TTS(language=language, device=device)
                speaker_ids_map = dict(tts_instance.hps.data.spk2id)
                self.tts_models[language] = tts_instance
                self.speaker_ids_map[language] = speaker_ids_map
                self.logger.info(f"MeloTTS {language} model loaded. Speaker IDs: {speaker_ids_map}")

                # 标记模型已加载
                self.set_model_loaded(True)
            except NotImplementedError as e:
                if "meta tensor" in str(e):
                    self.logger.warning(f"Meta tensor issue detected, retrying with device reset...")
                    # 清理 CUDA 缓存后重试
                    clear_device_cache(device)
                    tts_instance = TTS(language=language, device=device)
                    speaker_ids_map = dict(tts_instance.hps.data.spk2id)
                    self.tts_models[language] = tts_instance
                    self.speaker_ids_map[language] = speaker_ids_map
                    self.logger.info(f"MeloTTS {language} model loaded (retry). Speaker IDs: {speaker_ids_map}")

                    # 标记模型已加载
                    self.set_model_loaded(True)
                else:
                    raise
            except Exception as e:
                from core.exceptions import ModelInitializationError
                raise ModelInitializationError(f"melo-{language}", str(e))

        return self.tts_models[language], self.speaker_ids_map[language]

    def _process_text(self, text: str, input_format: str = "plain") -> str:
        """
        处理输入文本

        处理流程:
            1. 清洗 Markdown 格式 (如果 input_format="markdown")
            2. 特殊符号处理
            3. 注意：不再执行数字转英文逻辑，因为 MeloTTS ZH 模型可以直接处理中英文混合

        Args:
            text: 输入文本
            input_format: "plain" (纯文本) 或 "markdown" (Markdown格式)

        Returns:
            处理后的文本
        """
        # 1. 清洗 Markdown 格式
        if input_format == "markdown":
            text = self.markdown_cleaner.clean(text)

        # 2. 特殊符号处理（保留中英文版本）
        text = self.symbol_processor.process(text)

        # 3. 不再执行数字转英文逻辑，MeloTTS ZH 模型可以直接处理中英文混合文本

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
            voice: speaker_id（已映射）
            speed: 语速
            **kwargs: 其他参数（input_format, skip_processing, target_format, target_sample_rate）

        Returns:
            (audio_bytes, media_type) 元组
        """
        if not text.strip():
            from core.exceptions import InvalidInputError
            raise InvalidInputError("Text cannot be empty")

        input_format = kwargs.get('input_format', 'plain')
        skip_processing = kwargs.get('skip_processing', False)
        target_format = kwargs.get('target_format', 'mp3')
        target_sample_rate = kwargs.get('target_sample_rate', 24000)

        # 处理文本（如果需要）
        processed_text = text if skip_processing else self._process_text(text, input_format)

        # 分句处理
        sentences = self.sentence_splitter.split(processed_text)

        if not sentences:
            from core.exceptions import TextProcessingError
            raise TextProcessingError("No sentences found after processing")

        # 检测语言并加载对应模型
        language = detect_language(processed_text)
        model, spk_ids = self._load_melo_model(language)

        # 转换 speaker_id 为整数
        speaker_id = int(voice) if voice.isdigit() else spk_ids.get(voice, 1)

        # 逐句生成音频并合并
        all_audio_bytes = []

        for idx, sentence in enumerate(sentences):
            # 打印每个句子
            log_msg = f"[Sentence {idx + 1}/{len(sentences)}] Sending to TTS: '{sentence}' (speaker_id: {speaker_id})"
            self.logger.info(log_msg)
            print(log_msg)  # 后备方案，确保能看到

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_path = temp_file.name
            temp_file.close()

            try:
                # 生成音频到文件
                model.tts_to_file(sentence, speaker_id, temp_path, speed=speed)

                # 读取文件数据
                audio_bytes = AudioConverter.audio_file_to_bytes(temp_path)
                all_audio_bytes.append(audio_bytes)

            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_path)
                except:
                    pass

        # 合并所有音频片段
        # 合并 WAV 数据
        merged_audio_data = []
        for audio_bytes in all_audio_bytes:
            # 从 WAV 字节数据中提取音频数据
            audio_buffer = BytesIO(audio_bytes)
            sample_rate, audio_data = wavfile.read(audio_buffer)
            merged_audio_data.append(audio_data)

        # 合并音频数组
        if merged_audio_data:
            full_audio = np.concatenate(merged_audio_data)

            # 转换回 WAV 字节
            output_buffer = BytesIO()
            wavfile.write(output_buffer, sample_rate, full_audio)
            merged_wav_bytes = output_buffer.getvalue()
        else:
            from core.exceptions import AudioGenerationError
            raise AudioGenerationError("Generated audio is empty")

        # 转换格式
        audio_bytes, media_type = AudioConverter.convert_audio_to_target_format(
            merged_wav_bytes, target_sample_rate, target_format
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

        由于 MeloTTS 不支持真正的流式输出，采用句子级流式：
        1. 将文本分句
        2. 对每句调用 tts_to_file 生成完整音频
        3. 生成完成后立即发送该句音频

        Args:
            text: 输入文本
            voice: speaker_id（已映射）
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

        # 检测语言并加载对应模型
        language = detect_language(processed_text)
        model, spk_ids = self._load_melo_model(language)

        # 转换 speaker_id 为整数
        speaker_id = int(voice) if voice.isdigit() else spk_ids.get(voice, 1)

        # 分句处理
        sentences = self.sentence_splitter.split(processed_text)
        self.logger.info(f"Split into {len(sentences)} sentences")

        if not sentences:
            from core.exceptions import TextProcessingError
            raise TextProcessingError("No sentences found after processing")

        # 逐句生成并发送
        for idx, sentence in enumerate(sentences):
            # 发送句子开始标记
            yield b'', {
                "type": "sentence_start",
                "index": idx,
                "text": sentence,
                "voice": voice
            }

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_path = temp_file.name
            temp_file.close()

            try:
                # 生成音频到文件
                model.tts_to_file(sentence, speaker_id, temp_path, speed=speed)
                self.logger.info(f"Generated sentence {idx}: {sentence[:50]}...")

                # 读取文件数据
                audio_bytes = AudioConverter.audio_file_to_bytes(temp_path)

                # 发送音频数据
                yield audio_bytes, {
                    "type": "audio_chunk",
                    "index": idx,
                    "chunk": 1
                }

                # 让出控制权，允许其他协程执行
                await asyncio.sleep(0)

            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_path)
                except:
                    pass

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
        # 清理所有已加载的模型
        for language, model in list(self.tts_models.items()):
            del model
            self.logger.info(f"Cleaned up MeloTTS {language} model")

        self.tts_models.clear()
        self.speaker_ids_map.clear()

        # 清理设备缓存
        if self.device:
            clear_device_cache(self.device)

        self.set_model_loaded(False)
        self.logger.info("MeloTTS models cleaned up")
