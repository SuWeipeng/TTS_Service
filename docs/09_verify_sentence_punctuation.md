# 验证句子标点自动添加功能

本文档说明如何查看 Kokoro 模型中每次送入 TTS 引擎的句子，以验证句子分割器是否正确添加了标点符号。

## 日志输出位置

### 1. 非流式请求 (POST /v1/audio/speech)

在 `models/kokoro/model.py` 的 `generate_audio()` 方法中，会打印处理后的完整文本：

```
INFO: [Non-streaming] Sending to TTS: 'Hello world. This is a test.' (voice: bf_vale)
```

### 2. 流式请求 (WebSocket /ws/tts)

在 `models/kokoro/model.py` 的 `generate_audio_stream()` 方法中，会打印每个分割后的句子：

```
INFO: [Sentence 1/3] Sending to TTS: 'Hello world.' (voice: bf_vale)
INFO: [Sentence 2/3] Sending to TTS: 'This is a test.' (voice: bf_vale)
INFO: [Sentence 3/3] Sending to TTS: 'Another sentence.' (voice: bf_vale)
```

## 测试示例

### 测试1：无标点的句子

**输入文本**:
```
Hello world
```

**预期日志输出**:
```
INFO: [Sentence 1/1] Sending to TTS: 'Hello world.' (voice: bf_vale)
```
✅ 注意自动添加的句点 `.`

### 测试2：已有标点的句子

**输入文本**:
```
Hello world. How are you?
```

**预期日志输出**:
```
INFO: [Sentence 1/2] Sending to TTS: 'Hello world.' (voice: bf_vale)
INFO: [Sentence 2/2] Sending to TTS: 'How are you?' (voice: bf_vale)
```
✅ 保持原有标点不变

### 测试3：混合场景（部分有标点，部分没有）

**输入文本**:
```
First sentence. Second sentence
```

**预期日志输出**:
```
INFO: [Sentence 1/2] Sending to TTS: 'First sentence.' (voice: bf_vale)
INFO: [Sentence 2/2] Sending to TTS: 'Second sentence.' (voice: bf_vale)
```
✅ 第一个句子保持原样，第二个句子自动添加句点

### 测试4：中英混合

**输入文本**:
```
这是第一句话 This is second sentence
```

**预期日志输出**:
```
INFO: [Sentence 1/1] Sending to TTS: '这是第一句话 This is second sentence.' (voice: bf_vale)
```
✅ 自动添加英文句点

## 如何运行测试

### 方法1：使用 curl（非流式）

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello world",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output test.mp3
```

查看控制台日志，应该看到：
```
INFO: [Non-streaming] Sending to TTS: 'Hello world.' (voice: bf_vale)
```

### 方法2：使用 WebSocket（流式）

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:9880/ws/tts"
    async with websockets.connect(uri) as websocket:
        request = {
            "text": "Hello world. This is a test",
            "voice": "alloy",
            "speed": 1.0
        }
        await websocket.send(json.dumps(request))

        while True:
            try:
                message = await websocket.recv()
                if isinstance(message, bytes):
                    print(f"收到音频数据: {len(message)} bytes")
                else:
                    data = json.loads(message)
                    print(f"收到元数据: {data}")
                    if data.get("type") == "done":
                        break
            except websockets.exceptions.ConnectionClosed:
                break

asyncio.run(test_websocket())
```

查看控制台日志，应该看到：
```
INFO: [Sentence 1/2] Sending to TTS: 'Hello world.' (voice: bf_vale)
INFO: [Sentence 2/2] Sending to TTS: 'This is a test.' (voice: bf_vale)
```

## 实现代码位置

### 1. 日志输出代码（流式）

**文件**: `models/kokoro/model.py:319`

```python
# 打印送入 TTS 的句子
self.logger.info(f"[Sentence {idx + 1}/{len(sentences)}] Sending to TTS: '{sentence}' (voice: {optimal_voice})")
```

### 2. 日志输出代码（非流式）

**文件**: `models/kokoro/model.py:233`

```python
# 打印送入 TTS 的文本
self.logger.info(f"[Non-streaming] Sending to TTS: '{processed_text}' (voice: {voice})")
```

### 3. 句子分割逻辑

**文件**: `text_processing/sentence_splitter.py:101-111`

```python
# 处理每个句子，确保末尾有标点符号
result = []
for s in sentences:
    s = s.strip()
    if s:
        # 如果句子末尾没有标点符号，添加英文句点
        if not self._ends_with_punctuation(s):
            s += "."
        result.append(s)

return result
```

### 4. 标点检查方法

**文件**: `text_processing/sentence_splitter.py:141-160`

```python
def _ends_with_punctuation(self, text: str) -> bool:
    """检查文本是否以标点符号结尾"""
    if not text:
        return False

    # 定义结尾标点符号
    punctuation_chars = '。！？；，、.!?;,'
    return text.rstrip()[-1] in punctuation_chars if text.rstrip() else False
```

## 对比 MeloTTS 模型

MeloTTS 模型中也有类似的打印功能，可以在 `models/melo/model.py` 中看到类似的日志输出。

## 注意事项

1. **日志级别**: 需要确保日志级别设置为 `INFO` 或更低（在 `.env` 中设置 `LOG_LEVEL=INFO`）
2. **前台运行**: 前台运行服务时，日志会直接输出到控制台
3. **后台运行**: 后台运行时，日志会输出到日志文件

## 故障排查

### 问题：看不到日志输出

**解决方案**:
1. 检查日志级别设置：`LOG_LEVEL=INFO`
2. 确保前台运行服务以查看实时日志
3. 检查日志文件（如果后台运行）

### 问题：句子没有添加标点

**解决方案**:
1. 检查 `text_processing/sentence_splitter.py` 是否正确修改
2. 查看日志中的句子内容
3. 确认 `_ends_with_punctuation()` 方法正常工作

## 总结

通过这些日志输出，你可以清楚地看到：
- ✅ 句子分割器如何分割文本
- ✅ 每个句子是否正确添加了标点符号
- ✅ 送入 TTS 引擎的最终文本是什么

这对于验证和调试句子处理功能非常有帮助！
