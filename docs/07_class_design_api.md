# API 类设计文档

本文档详细说明 API 层的类设计和实现细节。

## 📋 目录

- [FastAPI 应用工厂](#fastapi-应用工厂)
- [路由处理器](#路由处理器)
- [WebSocket 处理器](#websocket-处理器)
- [中间件](#中间件)
- [数据模型](#数据模型)
- [API 端点](#api-端点)
- [使用示例](#使用示例)

---

## FastAPI 应用工厂

### create_app() 函数

**文件**: `api/app.py`

```python
def create_app() -> FastAPI:
    """
    创建 FastAPI 应用

    Returns:
        FastAPI 应用实例
    """
```

### 处理流程

```
设置日志 → 创建 FastAPI 应用 → 设置中间件 → 创建模型和服务 → 配置路由 → 返回应用
```

### 关键步骤

#### 1. 设置日志

```python
def create_app() -> FastAPI:
    # 设置日志
    setup_logger("TTS_Service", level=settings.log_level)
```

**作用**: 配置全局日志记录器

#### 2. 创建 FastAPI 应用

```python
app = FastAPI(
    title="TTS Service API",
    description="Text-to-Speech service with OpenAI API compatibility",
    version="1.0.0"
)
```

**应用元数据**:
- `title`: "TTS Service API"
- `description`: "Text-to-Speech service with OpenAI API compatibility"
- `version`: "1.0.0"

#### 3. 设置中间件

```python
# 设置中间件
setup_middleware(app)
```

**中间件**:
- CORS 中间件
- 异常处理中间件
- 日志中间件

#### 4. 创建模型和服务

```python
# 创建模型和服务
model = create_model()
tts_service = create_tts_service(model)

# 将服务添加到应用状态
app.state.tts_service = tts_service
```

**应用状态**: `app.state.tts_service` 存储服务实例

#### 5. 配置路由

```python
# 创建路由
api_router = create_routes(tts_service)
app.include_router(api_router)

# 创建 WebSocket 路由
websocket_route = create_websocket_route(tts_service)
app.add_api_websocket_route("/ws/tts", websocket_route)
```

**路由配置**:
- HTTP 路由: 通过 `APIRouter` 添加
- WebSocket 路由: 通过 `add_api_websocket_route` 添加

#### 6. 根路由

```python
@app.get("/")
async def root():
    """根路径"""
    return JSONResponse({
        "name": "TTS Service API",
        "version": "1.0.0",
        "model": tts_service.get_model_name(),
        "endpoints": {
            "tts": "/v1/audio/speech",
            "voices": "/v1/audio/voices",
            "health": "/health",
            "websocket": "/ws/tts"
        }
    })
```

**响应示例**:
```json
{
  "name": "TTS Service API",
  "version": "1.0.0",
  "model": "kokoro",
  "endpoints": {
    "tts": "/v1/audio/speech",
    "voices": "/v1/audio/voices",
    "health": "/health",
    "websocket": "/ws/tts"
  }
}
```

### create_model() 函数

```python
def create_model():
    """
    根据配置创建模型实例

    Returns:
        TTS 模型实例
    """
    logger = logging.getLogger(__name__)
    model_type = settings.tts_model.lower()

    logger.info(f"Initializing {model_type} model...")

    # 使用 get_model_class 动态获取模型类
    ModelClass = get_model_class(model_type)
    model = ModelClass()

    # 初始化模型（如果是 eager loading）
    if model.get_loading_strategy().value == "eager":
        model.initialize_model()
        logger.info(f"{model.get_model_name()} model loaded successfully")
    else:
        logger.info(f"{model.get_model_name()} model configured with lazy loading")

    return model
```

**作用**: 根据配置动态创建和初始化模型

**支持模型**: `kokoro`, `melo`

---

## 路由处理器

### create_routes() 函数

**文件**: `api/routes.py`

```python
def create_routes(tts_service: TTSService) -> APIRouter:
    """
    创建 API 路由

    Args:
        tts_service: TTS 服务实例

    Returns:
        API 路由器
    """
    router = APIRouter()
    # ... 定义路由
    return router
```

### HTTP 端点

#### 1. create_speech()

**路径**: `POST /v1/audio/speech`

**作用**: OpenAI 兼容的 TTS 接口

```python
@router.post("/v1/audio/speech")
async def create_speech(request: OpenAITTSRequest):
    """
    OpenAI 兼容的 TTS 接口

    生成语音音频。

    Args:
        request: OpenAI TTS 请求

    Returns:
        音频流
    """
    try:
        logger.info(f"Received TTS request: voice={request.voice}, speed={request.speed}")

        # 验证语速范围
        if request.speed and (request.speed < 0.25 or request.speed > 4.0):
            raise InvalidInputError(
                "Speed must be between 0.25 and 4.0",
                param="speed"
            )

        # 生成音频
        audio_bytes, media_type = await tts_service.generate_audio(
            text=request.input,
            voice=request.voice,
            speed=request.speed or 1.0,
            input_format=request.input_format or "plain",
            target_format=request.response_format or "mp3"
        )

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=500, detail="Generated audio is empty.")

        logger.info(f"Generated audio size: {len(audio_bytes)} bytes, format: {media_type}")

        # 返回音频流
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error in create_speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
```

**请求格式** (OpenAITTSRequest):
```json
{
  "model": "tts-1",
  "input": "Hello, world!",
  "voice": "alloy",
  "response_format": "mp3",
  "speed": 1.0,
  "input_format": "plain"
}
```

**响应**:
- 成功: `200 OK` - 音频流
- 失败: `400 Bad Request` / `500 Internal Server Error` - 错误信息

**HTTP Headers**:
```
Content-Disposition: inline
Cache-Control: no-cache
Access-Control-Allow-Origin: *
Content-Type: audio/mpeg 或 audio/wav
```

#### 2. tts_get()

**路径**: `GET /tts`

**作用**: 原有的 GET 接口，兼容旧版 API

```python
@router.get("/tts")
async def tts_get(
    text: str = Query(..., description="要合成的文本内容"),
    voice: str = Query("alloy", description="音色名称"),
    speed: float = Query(1.0, description="语速调节，如 0.9 或 1.2")
):
    """
    原有的 GET 接口

    生成语音音频。

    Args:
        text: 要合成的文本内容
        voice: 音色名称
        speed: 语速

    Returns:
        音频流
    """
    try:
        audio_bytes, media_type = await tts_service.generate_audio(
            text=text,
            voice=voice,
            speed=speed
        )

        if len(audio_bytes) > 0:
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type=media_type,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        else:
            raise HTTPException(status_code=500, detail="Generated audio is empty.")

    except Exception as e:
        logger.error(f"Error in tts_get: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
```

**查询参数**:
- `text` (required): 要合成的文本
- `voice` (optional): 音色名称，默认 "alloy"
- `speed` (optional): 语速，默认 1.0

#### 3. tts_post()

**路径**: `POST /tts_post`

**作用**: 原有的 POST 接口，接收 JSON 格式

```python
@router.post("/tts_post")
async def tts_post(request: TTSRequest):
    """
    原有的 POST 接口

    接收 JSON 格式的文本、音色、语速，生成音频文件。

    Args:
        request: TTS 请求

    Returns:
        音频流
    """
    try:
        # 处理文本（支持 Markdown 清洗和特殊符号处理）
        audio_bytes, media_type = await tts_service.generate_audio(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            input_format=request.input_format or "plain"
        )

        if len(audio_bytes) > 0:
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type=media_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Content-Disposition": f"inline"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Generated audio is empty.")

    except Exception as e:
        logger.error(f"Error in tts_post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")
```

**请求格式** (TTSRequest):
```json
{
  "text": "要合成的文本",
  "voice": "alloy",
  "speed": 1.0,
  "input_format": "plain"
}
```

#### 4. list_voices()

**路径**: `GET /v1/audio/voices`

**作用**: 获取可用音色列表（OpenAI 兼容格式）

```python
@router.get("/v1/audio/voices", response_model=VoicesResponse)
async def list_voices():
    """
    获取可用声音列表的接口（OpenAI 兼容格式）

    Returns:
        音色列表
    """
    model_name = tts_service.get_model_name()

    if model_name == "kokoro":
        # Kokoro 音色列表
        return VoicesResponse(data=[
            VoiceInfo(id="alloy", name="Alloy", description="Female voice (bf_vale)"),
            VoiceInfo(id="echo", name="Echo", description="Male voice (am_adam)"),
            VoiceInfo(id="fable", name="Fable", description="Female voice (af_sol)"),
            VoiceInfo(id="onyx", name="Onyx", description="Male voice (am_michael)"),
            VoiceInfo(id="nova", name="Nova", description="Female voice (af_sarah)"),
            VoiceInfo(id="shimmer", name="Shimmer", description="Bilingual voice (af_maple)"),
        ])
    else:
        # MeloTTS 音色列表
        return VoicesResponse(data=[
            VoiceInfo(id="alloy", name="Alloy", description="🌏 Bilingual Chinese-English voice (中英双语)"),
            VoiceInfo(id="echo", name="Echo", description="English (US) voice"),
            VoiceInfo(id="fable", name="Fable", description="English (British) voice"),
            VoiceInfo(id="onyx", name="Onyx", description="English (Default) voice"),
            VoiceInfo(id="nova", name="Nova", description="English (US) voice"),
            VoiceInfo(id="shimmer", name="Shimmer", description="English (Australian) voice"),
        ])
```

**响应格式** (VoicesResponse):
```json
{
  "data": [
    {
      "id": "alloy",
      "name": "Alloy",
      "description": "Female voice (bf_vale)"
    },
    {
      "id": "echo",
      "name": "Echo",
      "description": "Male voice (am_adam)"
    }
  ]
}
```

#### 5. health_check()

**路径**: `GET /health`

**作用**: 健康检查接口

```python
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口

    Returns:
        健康状态
    """
    health_status = tts_service.get_health_status()
    return HealthResponse(
        status="ok",
        model=health_status["model"],
        model_loaded=health_status["model_loaded"],
        supported_voices=health_status.get("supported_voices"),
    )
```

**响应格式** (HealthResponse):
```json
{
  "status": "ok",
  "model": "kokoro",
  "model_loaded": true,
  "supported_voices": ["af_heart", "af_maple", ...]
}
```

#### 6. health_detail()

**路径**: `GET /health/detail`

**作用**: 详细健康检查接口

```python
@router.get("/health/detail")
async def health_detail():
    """
    详细健康检查接口

    Returns:
        详细健康状态
    """
    health_status = tts_service.get_health_status()
    from config.settings import settings

    # 检查 ffmpeg 是否可用
    ffmpeg_available = _check_ffmpeg_available() if settings.enable_mp3 else False

    return {
        "status": "ok",
        "model": health_status["model"],
        "model_loaded": health_status["model_loaded"],
        "supported_voices": health_status["supported_voices"],
        "audio_format": settings.default_audio_format,
        "sample_rate": settings.sample_rate,
        "mp3_enabled": settings.enable_mp3,
        "dependencies": {
            "ffmpeg": ffmpeg_available
        }
    }
```

**响应格式**:
```json
{
  "status": "ok",
  "model": "kokoro",
  "model_loaded": true,
  "supported_voices": ["af_heart", "af_maple", ...],
  "audio_format": "mp3",
  "sample_rate": 24000,
  "mp3_enabled": true,
  "dependencies": {
    "ffmpeg": true
  }
}
```

---

## WebSocket 处理器

### create_websocket_route() 函数

**文件**: `api/websocket.py`

```python
def create_websocket_route(tts_service: TTSService):
    """
    创建 WebSocket 路由

    Args:
        tts_service: TTS 服务实例

    Returns:
        WebSocket 路由函数
    """
    async def websocket_tts(websocket: WebSocket):
        # WebSocket 处理逻辑
        pass
    return websocket_tts
```

### websocket_tts() 函数

**路径**: `/ws/tts`

**作用**: 流式 TTS 接口

```python
async def websocket_tts(websocket: WebSocket):
    """
    WebSocket 流式 TTS 接口，用于实时语音合成

    请求格式：
    {
        "text": "要合成的文本",
        "voice": "alloy",     // 可选，默认 alloy
        "speed": 1.0,         // 可选，默认 1.0
        "input_format": "plain"  // 可选，"plain" 或 "markdown"
    }

    响应格式：
    - JSON: {"type": "sentence_start", "index": 0, "text": "...", "voice": "..."}
    - 二进制数据：WAV 音频块
    - JSON: {"type": "sentence_end", "index": 0}
    - JSON: {"type": "done", "total_sentences": N}
    - JSON: {"type": "error", "message": "错误信息"}
    """
    await websocket.accept()
    logger = logging.getLogger(__name__)
    logger.info("WebSocket connection established")

    try:
        while True:
            # 接收客户端发送的数据
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data[:100]}...")

            try:
                # 解析 JSON 数据
                request_data = json.loads(data)
                text = request_data.get("text", "")
                voice = request_data.get("voice", "alloy")
                speed = request_data.get("speed", 1.0)
                input_format = request_data.get("input_format", "plain")

                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Text cannot be empty"
                    })
                    continue

                logger.info(f"Processing TTS: voice={voice}, speed={speed}, input_format={input_format}")

                # 验证语速范围
                if speed < 0.25 or speed > 4.0:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Speed must be between 0.25 and 4.0"
                    })
                    continue

                # 生成流式音频
                total_chunks = 0
                total_bytes = 0

                async for audio_chunk, metadata in tts_service.generate_audio_stream(
                    text=text,
                    voice=voice,
                    speed=speed,
                    input_format=input_format
                ):
                    # 发送音频数据
                    if audio_chunk:
                        total_chunks += 1
                        total_bytes += len(audio_chunk)
                        await websocket.send_bytes(audio_chunk)

                        # 让出控制权，允许其他协程执行
                        await asyncio.sleep(0)

                    # 发送元数据
                    if metadata:
                        await websocket.send_json(metadata)

                logger.info(f"TTS completed: {total_chunks} chunks, {total_bytes} bytes")

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except InvalidInputError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": e.message
                })
            except Exception as e:
                logger.error(f"Error processing TTS request: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
```

### WebSocket 消息格式

#### 请求格式

```json
{
  "text": "要合成的文本",
  "voice": "alloy",
  "speed": 1.0,
  "input_format": "plain"
}
```

#### 响应格式

**句子开始元数据**:
```json
{
  "type": "sentence_start",
  "index": 0,
  "text": "要合成的句子",
  "voice": "alloy",
  "total_sentences": 3
}
```

**音频数据**: 二进制 WAV 音频块

**句子结束元数据**:
```json
{
  "type": "sentence_end",
  "index": 0
}
```

**完成消息**:
```json
{
  "type": "done",
  "total_sentences": 3
}
```

**错误消息**:
```json
{
  "type": "error",
  "message": "错误描述"
}
```

---

## 中间件

### setup_middleware() 函数

**文件**: `api/middleware.py`

```python
def setup_middleware(app: FastAPI):
    """
    设置 FastAPI 中间件

    Args:
        app: FastAPI 应用实例
    """
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 异常处理中间件
    @app.exception_handler(TTSError)
    async def tts_error_handler(request: Request, exc: TTSError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=openai_error_response(exc)
        )
```

### CORS 中间件

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 默认 ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**作用**: 允许跨域请求

**配置**:
```ini
# .env
CORS_ORIGINS=["*"]
```

### 异常处理中间件

```python
@app.exception_handler(TTSError)
async def tts_error_handler(request: Request, exc: TTSError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=openai_error_response(exc)
    )
```

**作用**: 统一处理 TTS 异常，返回 OpenAI 格式的错误响应

**错误响应格式**:
```json
{
  "error": {
    "message": "错误消息",
    "type": "invalid_request_error",
    "param": "voice",
    "code": "invalid_voice"
  }
}
```

---

## 数据模型

### Pydantic 模型

**文件**: `core/models.py`

#### OpenAITTSRequest

```python
class OpenAITTSRequest(BaseModel):
    model: str = "tts-1"
    input: str = Field(..., min_length=1, max_length=4096)
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    response_format: Optional[Literal["mp3", "wav"]] = "mp3"
    speed: Optional[float] = Field(default=1.0, ge=0.25, le=4.0)
    input_format: Optional[Literal["plain", "markdown"]] = "plain"
```

**验证规则**:
- 文本长度: 1-4096 字符
- 语速范围: 0.25-4.0
- 音色: 6 种预定义音色
- 响应格式: mp3 或 wav

#### TTSRequest

```python
class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    input_format: Optional[Literal["plain", "markdown"]] = "plain"
```

#### WebSocketRequest

```python
class WebSocketRequest(BaseModel):
    text: str
    voice: str = "alloy"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    input_format: Optional[Literal["plain", "markdown"]] = "plain"
```

#### VoiceInfo

```python
class VoiceInfo(BaseModel):
    id: str
    name: str
    description: str
```

#### VoicesResponse

```python
class VoicesResponse(BaseModel):
    data: List[VoiceInfo]
```

#### HealthResponse

```python
class HealthResponse(BaseModel):
    status: str
    model: str
    model_loaded: Optional[bool]
    supported_voices: Optional[list]
```

---

## API 端点

### HTTP 端点列表

| 路径 | 方法 | 描述 | 请求类型 | 响应类型 |
|------|------|------|----------|----------|
| `/` | GET | 根路径，API 信息 | - | JSON |
| `/v1/audio/speech` | POST | OpenAI 兼容 TTS 接口 | `OpenAITTSRequest` | 音频流 |
| `/tts` | GET | 旧版 GET 接口 | Query Params | 音频流 |
| `/tts_post` | POST | 旧版 POST 接口 | `TTSRequest` | 音频流 |
| `/v1/audio/voices` | GET | 获取音色列表 | - | `VoicesResponse` |
| `/health` | GET | 健康检查 | - | `HealthResponse` |
| `/health/detail` | GET | 详细健康检查 | - | JSON |

### WebSocket 端点

| 路径 | 描述 | 消息类型 |
|------|------|----------|
| `/ws/tts` | 流式 TTS 接口 | JSON / Binary |

---

## 使用示例

### HTTP API 使用

#### 1. OpenAI 兼容接口

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, world!",
    "voice": "alloy"
  }' \
  --output hello.mp3
```

#### 2. 旧版 GET 接口

```bash
curl "http://localhost:9880/tts?text=Hello,world!&voice=alloy&speed=1.0" \
  --output hello.mp3
```

#### 3. 旧版 POST 接口

```bash
curl -X POST http://localhost:9880/tts_post \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "voice": "alloy",
    "speed": 1.0
  }' \
  --output hello.mp3
```

#### 4. 获取音色列表

```bash
curl http://localhost:9880/v1/audio/voices
```

响应:
```json
{
  "data": [
    {"id": "alloy", "name": "Alloy", "description": "Female voice (bf_vale)"},
    {"id": "echo", "name": "Echo", "description": "Male voice (am_adam)"}
  ]
}
```

#### 5. 健康检查

```bash
curl http://localhost:9880/health
```

响应:
```json
{
  "status": "ok",
  "model": "kokoro",
  "model_loaded": true,
  "supported_voices": ["af_heart", "af_maple", ...]
}
```

### WebSocket API 使用

#### Python 客户端

```python
import asyncio
import websockets
import json

async def tts_websocket():
    uri = "ws://localhost:9880/ws/tts"

    async with websockets.connect(uri) as websocket:
        # 发送请求
        request = {
            "text": "Hello, this is a streaming test.",
            "voice": "alloy",
            "speed": 1.0
        }
        await websocket.send(json.dumps(request))

        # 接收音频流
        audio_chunks = []
        while True:
            message = await websocket.recv()

            # 元数据消息
            if isinstance(message, str):
                metadata = json.loads(message)
                print(f"Received: {metadata['type']}")

                if metadata.get("type") == "done":
                    break

            # 音频二进制数据
            elif isinstance(message, bytes):
                audio_chunks.append(message)

        # 合并音频
        complete_audio = b''.join(audio_chunks)

        # 保存到文件
        with open("streaming_output.mp3", "wb") as f:
            f.write(complete_audio)

asyncio.run(tts_websocket())
```

#### JavaScript 客户端

```javascript
const ttsWebSocket = async () => {
  const ws = new WebSocket('ws://localhost:9880/ws/tts');
  const audioChunks = [];

  ws.onopen = () => {
    console.log('WebSocket connected');

    // 发送请求
    ws.send(JSON.stringify({
      text: 'Hello from JavaScript',
      voice: 'alloy',
      speed: 1.0
    }));
  };

  ws.onmessage = (event) => {
    // 元数据消息
    if (typeof event.data === 'string') {
      const metadata = JSON.parse(event.data);
      console.log('Received:', metadata.type);

      if (metadata.type === 'done') {
        // 合并音频并播放
        const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
      }
    }
    // 音频二进制数据
    else {
      audioChunks.push(event.data);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket closed');
  };
};

ttsWebSocket();
```

---

## 错误处理

### HTTP 错误响应

#### 输入验证错误

**请求**:
```json
{
  "input": "",
  "voice": "alloy"
}
```

**响应** (400 Bad Request):
```json
{
  "error": {
    "message": "Input text cannot be empty",
    "type": "invalid_request_error",
    "param": "input"
  }
}
```

#### 音色无效错误

**请求**:
```json
{
  "input": "Hello",
  "voice": "invalid_voice"
}
```

**响应** (400 Bad Request):
```json
{
  "error": {
    "message": "Invalid voice 'invalid_voice'. Supported voices: alloy, echo, fable, onyx, nova, shimmer",
    "type": "invalid_request_error",
    "param": "voice",
    "code": "invalid_voice"
  }
}
```

#### 模型未加载错误

**响应** (500 Internal Server Error):
```json
{
  "error": {
    "message": "Model 'kokoro' is not loaded",
    "type": "model_not_loaded"
  }
}
```

### WebSocket 错误消息

#### JSON 格式错误

```json
{
  "type": "error",
  "message": "Invalid JSON format"
}
```

#### 文本为空错误

```json
{
  "type": "error",
  "message": "Text cannot be empty"
}
```

#### 语速范围错误

```json
{
  "type": "error",
  "message": "Speed must be between 0.25 and 4.0"
}
```

---

## 相关文档

- [核心类设计](04_class_design_core.md)
- [模型类设计](05_class_design_models.md)
- [服务类设计](06_class_design_services.md)
- [架构设计](03_architecture_design.md)
