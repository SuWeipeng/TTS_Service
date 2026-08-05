"""
音频处理工具

提供音频格式转换、采样率调整等功能。
"""

import io
import soundfile as sf
import numpy as np
import tempfile
import os
import subprocess
from typing import Tuple


class AudioConverter:
    """音频格式转换工具"""

    SAMPLE_RATE = 24000  # 固定 24kHz

    @staticmethod
    def numpy_to_wav(audio_array: np.ndarray) -> bytes:
        """
        numpy 数组转 WAV bytes

        Args:
            audio_array: numpy 音频数组

        Returns:
            WAV 格式的字节数据
        """
        buffer = io.BytesIO()
        sf.write(buffer, audio_array, AudioConverter.SAMPLE_RATE, format='WAV')
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def wav_to_mp3(wav_bytes: bytes) -> Tuple[bytes, str]:
        """
        WAV 转 MP3

        Args:
            wav_bytes: WAV 格式字节数据

        Returns:
            (mp3_bytes, "audio/mpeg") 元组
        """
        try:
            # 尝试直接用 soundfile
            buffer = io.BytesIO()
            audio_array, sr = sf.read(io.BytesIO(wav_bytes))
            sf.write(buffer, audio_array, sr, format='MP3')
            buffer.seek(0)
            return buffer.read(), "audio/mpeg"
        except Exception as e:
            # Fallback: 使用 ffmpeg
            try:
                return AudioConverter._ffmpeg_convert(wav_bytes, "mp3")
            except Exception as e2:
                # 最终 fallback：返回 WAV
                print(f"MP3 encoding failed: {e2}, returning WAV")
                return wav_bytes, "audio/wav"

    @staticmethod
    def _ffmpeg_convert(audio_bytes: bytes, target_format: str) -> Tuple[bytes, str]:
        """
        使用 ffmpeg 进行格式转换

        Args:
            audio_bytes: 原始音频字节数据
            target_format: 目标格式（"mp3" 或 "wav"）

        Returns:
            (converted_bytes, media_type) 元组
        """
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.write(audio_bytes)
        temp_wav.close()

        temp_out = tempfile.NamedTemporaryFile(suffix=f".{target_format}", delete=False)
        temp_out_path = temp_out.name
        temp_out.close()

        try:
            if target_format == 'mp3':
                codec = 'libmp3lame'
                media_type = "audio/mpeg"
            else:
                codec = 'pcm_s16le'
                media_type = "audio/wav"

            subprocess.run([
                'ffmpeg', '-y', '-i', temp_wav_path,
                '-acodec', codec,
                '-b:a', '64k' if target_format == 'mp3' else '192k',
                temp_out_path
            ], capture_output=True, check=True)

            with open(temp_out_path, 'rb') as f:
                result = f.read()

            return result, media_type
        finally:
            os.unlink(temp_wav_path)
            os.unlink(temp_out_path)

    @staticmethod
    def convert_to_target_format(
        wav_bytes: bytes,
        target_format: str
    ) -> Tuple[bytes, str]:
        """
        转换到目标格式

        Args:
            wav_bytes: WAV 格式字节数据
            target_format: 目标格式（"wav", "mp3", "mpeg"）

        Returns:
            (converted_bytes, media_type) 元组
        """
        if target_format.lower() in ["mp3", "mpeg"]:
            return AudioConverter.wav_to_mp3(wav_bytes)
        else:
            return wav_bytes, "audio/wav"

    @staticmethod
    def resample_audio(
        audio_array: np.ndarray,
        original_sr: int,
        target_sr: int = SAMPLE_RATE
    ) -> np.ndarray:
        """
        重采样音频

        Args:
            audio_array: 原始音频数组
            original_sr: 原始采样率
            target_sr: 目标采样率

        Returns:
            重采样后的音频数组
        """
        if original_sr == target_sr:
            return audio_array

        try:
            import scipy.signal
            ratio = target_sr / original_sr
            new_length = int(len(audio_array) * ratio)
            return scipy.signal.resample(audio_array, new_length)
        except ImportError:
            print("scipy not available, returning original audio")
            return audio_array

    @staticmethod
    def audio_file_to_bytes(file_path: str) -> bytes:
        """
        从文件读取音频数据为 bytes

        Args:
            file_path: 音频文件路径

        Returns:
            音频字节数据
        """
        with open(file_path, 'rb') as f:
            return f.read()

    @staticmethod
    def convert_audio_to_target_format(
        audio_bytes: bytes,
        target_sample_rate: int = SAMPLE_RATE,
        target_format: str = "wav"
    ) -> Tuple[bytes, str]:
        """
        将音频数据转换为目标格式和采样率

        Args:
            audio_bytes: 原始音频字节数据
            target_sample_rate: 目标采样率
            target_format: 目标格式（"wav" 或 "mp3"）

        Returns:
            (audio_bytes, media_type) 元组
        """
        # 读取音频数据
        audio_array, source_sr = sf.read(io.BytesIO(audio_bytes))

        # 如果采样率不同，进行重采样
        if source_sr != target_sample_rate:
            audio_array = AudioConverter.resample_audio(
                audio_array, source_sr, target_sample_rate
            )

        # 转换为指定格式
        buffer = io.BytesIO()
        if target_format.lower() in ["wav", "wave"]:
            sf.write(buffer, audio_array, target_sample_rate, format='WAV')
            media_type = "audio/wav"
        elif target_format.lower() in ["mp3", "mpeg"]:
            try:
                sf.write(buffer, audio_array, target_sample_rate, format='MP3')
                media_type = "audio/mpeg"
            except Exception:
                # Fallback to WAV
                sf.write(buffer, audio_array, target_sample_rate, format='WAV')
                media_type = "audio/wav"
        else:
            # 默认使用 WAV
            sf.write(buffer, audio_array, target_sample_rate, format='WAV')
            media_type = "audio/wav"

        buffer.seek(0)
        return buffer.read(), media_type
