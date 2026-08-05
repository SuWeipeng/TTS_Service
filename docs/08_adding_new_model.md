# 添加新的 TTS 模型指南

本文档详细说明如何在当前的 TTS 服务架构下添加一个新的 TTS 模型。

## 目录

1. [概述](#概述)
2. [前置条件](#前置条件)
3. [步骤1：创建模型目录结构](#步骤1创建模型目录结构)
4. [步骤2：实现模型类](#步骤2实现模型类)
5. [步骤3：创建配置文件](#步骤3创建配置文件)
6. [步骤4：注册模型](#步骤4注册模型)
7. [步骤5：更新设置](#步骤5更新设置)
8. [步骤6：测试](#步骤6测试)
9. [完整示例](#完整示例)
10. [最佳实践](#最佳实践)

## 概述

本 TTS 服务采用可插拔架构，所有模型都需要实现 `TTSModelInterface` 接口。添加新模型的核心步骤包括：

1. 创建模型目录和文件
2. 实现模型类（继承 `BaseModel`）
3. 创建音色映射配置
4. 在工厂函数中注册模型
5. 更新全局设置
6. 测试功能

## 前置条件

- 了解目标 TTS 模型的 API 和使用方法
- 准备好模型文件（如果有本地模型文件）
- 了解模型支持的音色/说话人列表
- 了解模型的加载策略（启动时加载 vs 延迟加载）

## 步骤1：创建模型目录结构

在 `models/` 目录下创建新的模型目录：

```bash
models/
├── __init__.py
├── base.py
├── kokoro/
├── melo/
└── your_model/          # 新模型目录
    ├── __init__.py
    ├── model.py          # 模型实现
    ├── config.py         # 配置常量
    ├── voice_mapping.json  # 音色映射
    └── model_files/      # 模型文件目录（可选）
```

创建基础文件：

```bash
mkdir models/your_model
touch models/your_model/__init__.py
touch models/your_model/model.py
touch models/your_model/config.py
touch models/your_model/voice_mapping.json
```

## 步骤2：实现模型类

### 2.1 创建配置常量（config.py）

定义模型特定的常量：

```python
# models/your_model/config.py

# 模型名称
MODEL_NAME = "your_model"

# 支持的采样率
SAMPLE_RATE = 24000

# 支持的音色列表
SUPPORTED_VOICES = [
    "voice1",
    "voice2",
    "voice3",
]

# 默认音色
DEFAULT_VOICE = "voice1"

# 语言支持
LANGUAGE = "zh"  # 或 "en", "multilingual"

# 模型文件路径（如果有本地文件）
MODEL_PATH = "models/your_model/model_files/model.bin"
VOICE_PATH = "models/your_model/model_files/voices/"
```

### 2.2 实现模型类（model.py）

这是核心部分，需要实现 `TTSModelInterface` 接口的所有方法。

```python
# models/your_model/model.py

from core.tts_interface import TTSModelInterface, LoadingStrategy
from core.exceptions import (
    InvalidVoiceError,
    ModelNotLoadedError,
    AudioGenerationError,
    ModelInitializationError
)
from models.base import BaseModel
from text_processing.markdown_cleaner import MarkdownCleaner
from text_processing.sentence_splitter import SentenceSplitter
from text_processing.symbol_processor import SpecialSymbolProcessor
from text_processing.number_processor import NumberReplacer
from utils.logger import get_logger
from utils.device import get_device
import json
import io

# 导入目标 TTS 库
# import your_tts_library

logger = get_logger(__name__)


class YourModel(BaseModel):
    """你的 TTS 模型实现"""

    def __init__(self):
        super().__init__()
        self.device = None
        self.model = None  # TTS 模型实例
        self.voice_mapping = {}
        self.markdown_cleaner = MarkdownCleaner()
        self.sentence_splitter = SentenceSplitter()
        self.symbol_processor = SpecialSymbolProcessor()
        # 根据模型需要选择文本处理器
        self.number_replacer = NumberReplacer()

    def get_model_name(self) -> str:
        """返回模型名称"""
        from .config import MODEL_NAME
        return MODEL_NAME

    def get_supported_voices(self) -> list[str]:
        """返回支持的音色列表"""
        from .config import SUPPORTED_VOICES
        return SUPPORTED_VOICES

    def get_loading_strategy(self) -> LoadingStrategy:
        """
        返回模型加载策略

        - EAGER: 启动时加载（适合大模型，加载时间长）
        - LAZY: 延迟加载（首次使用时加载，适合轻量级模型）
        """
        return LoadingStrategy.EAGER  # 或 LoadingStrategy.LAZY

    def initialize_model(self):
        """初始化模型（在启动时或首次使用时调用）"""
        try:
            self.device = get_device()
            logger.info(f"Initializing {self.get_model_name()} on {self.device}")

            # 加载音色映射
            self._load_voice_mapping()

            # 初始化你的 TTS 模型
            # self.model = your_tts_library.load_model(device=self.device)

            self._model_loaded = True
            logger.info(f"{self.get_model_name()} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize {self.get_model_name()}: {e}")
            raise ModelInitializationError(f"Model initialization failed: {e}")

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model_loaded

    def _load_voice_mapping(self):
        """加载音色映射配置"""
        from .config import VOICE_MAPPING_PATH
        try:
            with open(VOICE_MAPPING_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.voice_mapping = config.get('mappings', {})
        except Exception as e:
            logger.warning(f"Failed to load voice mapping: {e}")
            self.voice_mapping = {}

    def map_voice(self, requested_voice: str, text: str = None) -> any:
        """
        将请求的音色映射到模型特定的音色标识符

        Args:
            requested_voice: 用户请求的音色名称（如 "alloy"）
            text: 待合成的文本（可选，某些模型根据文本语言选择音色）

        Returns:
            模型特定的音色标识符
        """
        from .config import DEFAULT_VOICE

        # 如果请求的音色在映射中，返回映射后的音色
        if requested_voice in self.voice_mapping:
            return self.voice_mapping[requested_voice]

        # 如果请求的音色直接被支持，返回原值
        if requested_voice in self.get_supported_voices():
            return requested_voice

        # 否则返回默认音色
        logger.warning(
            f"Voice '{requested_voice}' not found, using default '{DEFAULT_VOICE}'"
        )
        return DEFAULT_VOICE

    def _preprocess_text(self, text: str, input_format: str = "plain") -> str:
        """
        预处理文本

        流程：
        1. 如果是 markdown 格式，清洗 Markdown 符号
        2. 处理特殊符号
        3. （可选）数字转文本
        """
        # 1. 清洗 Markdown
        if input_format == "markdown":
            text = self.markdown_cleaner.clean(text)

        # 2. 处理特殊符号
        text = self.symbol_processor.process(text)

        # 3. （可选）数字转换
        # text = self.number_replacer.replace_numbers(text, language="zh")

        return text

    def generate_audio(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        input_format: str = "plain"
    ) -> tuple[bytes, str]:
        """
        生成完整音频

        Args:
            text: 待合成文本
            voice: 音色名称
            speed: 语速倍率
            input_format: 输入格式（plain/markdown）

        Returns:
            (audio_bytes, format) - 音频数据和格式
        """
        if not self.is_model_loaded():
            if self.get_loading_strategy() == LoadingStrategy.LAZY:
                self.initialize_model()
            else:
                raise ModelNotLoadedError("Model not loaded")

        if not (0.25 <= speed <= 4.0):
            raise ValueError("Speed must be between 0.25 and 4.0")

        try:
            # 1. 预处理文本
            processed_text = self._preprocess_text(text, input_format)

            # 2. 映射音色
            model_voice = self.map_voice(voice, processed_text)

            # 3. 生成音频
            # audio_data = self.model.synthesize(
            #     text=processed_text,
            #     voice=model_voice,
            #     speed=speed
            # )

            # 4. 转换为字节流
            # audio_bytes = self._convert_to_bytes(audio_data)

            # 示例：返回 MP3 格式
            # return audio_bytes, "mp3"

            raise NotImplementedError("Implement audio generation")

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise AudioGenerationError(f"Failed to generate audio: {e}")

    async def generate_audio_stream(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        input_format: str = "plain"
    ):
        """
        生成流式音频（WebSocket）

        分句处理，逐步返回音频块

        Yields:
            音频块（bytes）
        """
        # 1. 预处理文本
        processed_text = self._preprocess_text(text, input_format)

        # 2. 分句处理
        sentences = self.sentence_splitter.split(processed_text)

        # 3. 逐句生成音频
        for sentence in sentences:
            if not sentence.strip():
                continue

            try:
                audio_bytes, _ = self.generate_audio(
                    text=sentence,
                    voice=voice,
                    speed=speed,
                    input_format="plain"  # 已经预处理过，这里是 plain
                )
                yield audio_bytes

            except Exception as e:
                logger.error(f"Failed to generate audio for sentence: {e}")
                raise

    def cleanup(self):
        """清理模型资源"""
        if self.model:
            # 释放模型资源
            # self.model.release()
            self.model = None
        self._model_loaded = False
        logger.info(f"{self.get_model_name()} cleaned up")
```

### 2.3 创建模块导出（__init__.py）

```python
# models/your_model/__init__.py

from .model import YourModel

__all__ = ['YourModel']
```

## 步骤3：创建配置文件

### 3.1 音色映射文件（voice_mapping.json）

将通用音色名称（OpenAI 风格）映射到模型特定的音色：

```json
{
  "mappings": {
    "alloy": "model_voice_1",
    "echo": "model_voice_2",
    "fable": "model_voice_3",
    "onyx": "model_voice_4",
    "nova": "model_voice_5",
    "shimmer": "model_voice_6"
  },
  "metadata": {
    "description": "Voice mapping for YourModel",
    "language": "zh"
  }
}
```

**映射原则**：
- 尽量保持与 OpenAI 兼容的音色名称
- 根据模型音色特征选择合适的映射
- 可以自定义额外的音色名称

## 步骤4：注册模型

在 `models/__init__.py` 中注册新模型：

```python
# models/__init__.py

def get_model_class(model_type: str):
    """根据模型类型返回对应的模型类"""
    if model_type == "kokoro":
        from .kokoro import KokoroModel
        return KokoroModel
    elif model_type == "melo":
        from .melo import MeloModel
    elif model_type == "your_model":  # 新增
        from .your_model import YourModel
        return YourModel
    else:
        raise ValueError(
            f"Unknown model type: {model_type}. "
            f"Supported types: kokoro, melo, your_model"
        )
```

## 步骤5：更新设置

在 `config/settings.py` 中添加模型配置：

```python
# config/settings.py

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # 现有配置...

    # 模型选择（新增选项）
    tts_model: Literal["kokoro", "melo", "your_model"] = "kokoro"

    # === YourModel 配置 ===
    # 模型文件路径
    your_model_path: str = "models/your_model/model_files/model.bin"
    your_model_config: str = "models/your_model/model_files/config.json"

    # 音色配置
    your_model_voices_dir: str = "models/your_model/model_files/voices/"
    your_model_voice_mapping: str = "models/your_model/voice_mapping.json"

    # 模型参数
    your_model_device: str = "auto"  # auto, cuda, cpu
    your_model_sample_rate: int = 24000
```

## 步骤6：测试

### 6.1 单元测试

创建测试文件 `tests/test_your_model.py`：

```python
# tests/test_your_model.py

import pytest
from models.your_model import YourModel


class TestYourModel:
    """YourModel 单元测试"""

    @pytest.fixture
    def model(self):
        """创建模型实例"""
        return YourModel()

    def test_model_name(self, model):
        """测试模型名称"""
        assert model.get_model_name() == "your_model"

    def test_supported_voices(self, model):
        """测试支持的音色"""
        voices = model.get_supported_voices()
        assert isinstance(voices, list)
        assert len(voices) > 0

    def test_loading_strategy(self, model):
        """测试加载策略"""
        strategy = model.get_loading_strategy()
        assert strategy.value in ["eager", "lazy"]

    def test_voice_mapping(self, model):
        """测试音色映射"""
        # 测试已知音色
        mapped = model.map_voice("alloy")
        assert mapped is not None

        # 测试未知音色（应返回默认音色）
        default_mapped = model.map_voice("unknown_voice")
        assert default_mapped is not None

    def test_text_preprocessing(self, model):
        """测试文本预处理"""
        text = "Hello, world!"
        processed = model._preprocess_text(text)
        assert isinstance(processed, str)

    @pytest.mark.asyncio
    async def test_audio_generation(self, model):
        """测试音频生成"""
        # 如果是 LAZY 加载，需要先初始化
        if model.get_loading_strategy().value == "lazy":
            model.initialize_model()

        text = "测试文本"
        audio_bytes, format = model.generate_audio(
            text=text,
            voice="alloy",
            speed=1.0
        )

        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
        assert format in ["mp3", "wav", "pcm"]
```

### 6.2 集成测试

启动服务并测试 API：

```bash
# 设置环境变量
export TTS_MODEL=your_model

# 启动服务
python main.py

# 测试健康检查
curl http://localhost:8000/health/detail

# 测试音色列表
curl http://localhost:8000/v1/audio/voices

# 测试 TTS 生成
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "你好，这是一个测试。",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output test.mp3
```

### 6.3 WebSocket 测试

```python
# tests/test_websocket.py

import asyncio
import websockets
import json


async def test_websocket_tts():
    uri = "ws://localhost:8000/ws/tts"
    request = {
        "text": "测试流式语音合成",
        "voice": "alloy",
        "speed": 1.0,
        "input_format": "plain"
    }

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(request))

        while True:
            message = await websocket.recv()
            # 处理消息（音频块或元数据）
            print(f"Received chunk: {len(message)} bytes")


if __name__ == "__main__":
    asyncio.run(test_websocket_tts())
```

## 完整示例

假设我们要添加一个基于 **Edge TTS** 的新模型，以下是简化版实现：

### 1. 目录结构

```
models/
└── edge/
    ├── __init__.py
    ├── model.py
    ├── config.py
    └── voice_mapping.json
```

### 2. config.py

```python
MODEL_NAME = "edge"
SAMPLE_RATE = 24000
SUPPORTED_VOICES = [
    "en-US-AriaNeural",
    "en-US-GuyNeural",
    "zh-CN-XiaoxiaoNeural",
]
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
VOICE_MAPPING_PATH = "models/edge/voice_mapping.json"
```

### 3. voice_mapping.json

```json
{
  "mappings": {
    "alloy": "en-US-AriaNeural",
    "echo": "en-US-GuyNeural",
    "nova": "zh-CN-XiaoxiaoNeural"
  }
}
```

### 4. model.py（核心部分）

```python
import edge_tts
from core.tts_interface import TTSModelInterface, LoadingStrategy
from models.base import BaseModel

class EdgeModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.voice_mapping = {}

    def get_model_name(self) -> str:
        return "edge"

    def get_supported_voices(self) -> list[str]:
        from .config import SUPPORTED_VOICES
        return SUPPORTED_VOICES

    def get_loading_strategy(self) -> LoadingStrategy:
        return LoadingStrategy.LAZY  # Edge TTS 不需要预加载

    def initialize_model(self):
        """Edge TTS 不需要初始化，直接标记为已加载"""
        self._load_voice_mapping()
        self._model_loaded = True

    async def generate_audio(self, text: str, voice: str = "alloy", speed: float = 1.0):
        model_voice = self.map_voice(voice)
        communicate = edge_tts.Communicate(text, model_voice)
        audio_data = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        return audio_data, "mp3"
```

### 5. 注册模型

```python
# models/__init__.py
def get_model_class(model_type: str):
    if model_type == "edge":
        from .edge import EdgeModel
        return EdgeModel
    # ...
```

### 6. 更新设置

```python
# config/settings.py
class Settings(BaseSettings):
    tts_model: Literal["kokoro", "melo", "edge"] = "kokoro"
    edge_voice_mapping: str = "models/edge/voice_mapping.json"
```

## 最佳实践

### 1. 错误处理

- 使用自定义异常（在 `core/exceptions.py` 中定义）
- 记录详细的错误日志
- 提供有意义的错误消息

### 2. 文本处理

- 根据模型需求选择合适的文本处理器
- 某些模型可能不需要数字转换（如 MeloTTS）
- 某些模型可能需要特殊的文本格式

### 3. 性能优化

- **LAZY 加载**：适合轻量级模型或按需加载
- **EAGER 加载**：适合大模型，避免首次请求延迟
- 考虑使用缓存（如音色映射、语言 Pipeline）

### 4. 音色管理

- 提供清晰的音色映射文档
- 支持模型原生音色名称
- 考虑添加音色预览功能

### 5. 日志记录

- 在关键步骤记录日志（初始化、音频生成、错误）
- 使用统一的日志格式
- 避免记录敏感信息

### 6. 配置管理

- 将所有可配置参数放在 `config.py` 中
- 支持环境变量覆盖
- 提供默认值

### 7. 测试覆盖

- 单元测试：测试核心方法
- 集成测试：测试 API 端点
- 性能测试：测试并发请求和流式处理

### 8. 文档

- 更新 README.md 添加新模型说明
- 在 docs 目录添加部署指南（如 `04_deployment_your_model.md`）
- 更新架构设计文档

## 常见问题

### Q1: 如何选择加载策略？

**A**:
- **EAGER**：模型加载时间长（>1秒），需要预热
- **LAZY**：模型加载快（<1秒），或内存敏感

### Q2: 如何处理多语言模型？

**A**:
- 在 `map_voice` 方法中根据文本语言选择音色
- 为每种语言维护单独的音色映射
- 考虑添加自动语言检测功能

### Q3: 如何支持流式输出？

**A**:
- 实现 `generate_audio_stream` 方法
- 使用 `sentence_splitter` 分句处理
- 逐句生成并 yield 音频块

### Q4: 模型文件很大怎么办？

**A**:
- 使用 LAZY 加载策略
- 考虑模型量化或压缩
- 支持从远程服务器加载模型

### Q5: 如何调试音频生成问题？

**A**:
- 检查文本预处理结果
- 验证音色映射是否正确
- 记录模型输入输出
- 使用中间音频文件调试

## 总结

添加新模型的核心是实现 `TTSModelInterface` 接口，关键步骤包括：

1. ✅ 创建模型目录和文件
2. ✅ 实现所有接口方法
3. ✅ 配置音色映射
4. ✅ 在工厂函数中注册
5. ✅ 更新全局设置
6. ✅ 编写测试
7. ✅ 更新文档

遵循本文档的步骤和最佳实践，可以轻松地将任何 TTS 模型集成到现有架构中。

---

**参考文档**:
- [架构设计文档](./03_architecture_design.md)
- [核心类设计](./04_class_design_core.md)
- [模型类设计](./05_class_design_models.md)
- [服务类设计](./06_class_design_services.md)
