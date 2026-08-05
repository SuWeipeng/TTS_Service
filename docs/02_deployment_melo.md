# MeloTTS 部署指南

本文档详细介绍如何部署和使用 MeloTTS 模型。

## 📋 目录

- [系统要求](#系统要求)
- [环境准备](#环境准备)
- [安装步骤](#安装步骤)
- [配置文件](#配置文件)
- [启动服务](#启动服务)
- [验证部署](#验证部署)
- [常见问题](#常见问题)
- [性能优化](#性能优化)

---

## 系统要求

### 硬件要求

- **CPU**: 4核心以上
- **内存**: 8GB RAM 以上（推荐 16GB）
- **存储**: 至少 2GB 可用空间
- **GPU**: NVIDIA GPU（可选，推荐用于加速）
  - CUDA 11.0+
  - 显存 2GB+

### 软件要求

- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.8 或更高版本
- **Conda**: Miniconda 或 Anaconda
- **CUDA**: 11.0+ （如果使用 GPU）

---

## 环境准备

### 1. 创建 Conda 环境

```bash
# 创建环境（可以复用 kokoro 环境或创建新环境）
conda create -n kokoro python=3.10 -y

# 激活环境
conda activate kokoro
```

### 2. 安装 PyTorch（根据你的硬件选择）

#### 使用 CUDA（GPU 加速）

```bash
# CUDA 11.8
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# 或 CUDA 12.1
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

#### 使用 CPU

```bash
conda install pytorch torchvision torchaudio cpuonly -c pytorch
```

#### Apple Silicon (MPS 支持)

```bash
# macOS with Apple Silicon
conda install pytorch torchvision torchaudio -c pytorch
```

### 3. 安装 ffmpeg（用于 MP3 编码）

#### Windows

```bash
conda install ffmpeg -c conda-forge
```

#### Linux

```bash
sudo apt install ffmpeg
```

#### macOS

```bash
brew install ffmpeg
```

---

## 安装步骤

### 1. 获取代码

```bash
cd D:\ttts\TTS_Service
```

### 2. 安装依赖

```bash
# 安装共享依赖
pip install -r requirements.txt

# 安装 MeloTTS 专用依赖
pip install -r requirements-melo.txt

# 可选：安装 MP3 编码支持
pip install -r requirements-mp3.txt
```

### 3. MeloTTS 模型自动下载

MeloTTS 使用 **延迟加载（Lazy Loading）策略**，模型会在首次使用时自动下载。无需手动准备模型文件。

首次启动时，MeloTTS 会自动下载以下文件：

- **中文模型**: ~400MB
- **英文模型**: ~400MB

下载位置：`~/.local/share/melo/` 或 `C:\Users\<用户>\App\Local\melo\`

### 4. 验证文件结构

```
models/melo/
├── config.py
├── model.py
├── __init__.py
└── voice_mapping.json
```

**注意**: MeloTTS 模型文件会自动下载到用户目录，无需手动管理。

---

## 配置文件

### 创建 `.env` 文件

```bash
# 复制示例配置
cp .env.example .env
```

### 编辑 `.env` 文件

```ini
# 模型选择
TTS_MODEL=melo

# 服务器设置
HOST=0.0.0.0
PORT=9880

# 音频设置
SAMPLE_RATE=24000
DEFAULT_AUDIO_FORMAT=mp3
ENABLE_MP3=true

# MeloTTS 配置
MELO_DEVICE=auto
MELO_VOICE_MAPPING=models/melo/voice_mapping.json

# OpenAI API 兼容性
STRICT_OPENAI_COMPATIBILITY=true
MAX_TEXT_LENGTH=4096
MIN_SPEED=0.25
MAX_SPEED=4.0

# CORS 设置
CORS_ORIGINS=["*"]

# 日志设置
LOG_LEVEL=INFO

# 队列管理设置
MAX_QUEUE_SIZE=100
```

### 环境变量说明

| 变量 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `TTS_MODEL` | 模型选择 | `melo` | `melo` |
| `MELO_DEVICE` | 设备选择 | `auto` | `auto`, `cuda:0`, `cpu`, `mps` |
| `HOST` | 服务器地址 | `0.0.0.0` | - |
| `PORT` | 服务器端口 | `9880` | - |

### 设备配置详解

#### 自动检测（推荐）
```ini
MELO_DEVICE=auto
```
自动选择最佳可用设备（CUDA > MPS > CPU）

#### 指定 GPU
```ini
MELO_DEVICE=cuda:0  # 使用第一块 GPU
MELO_DEVICE=cuda:1  # 使用第二块 GPU
```

#### 使用 CPU
```ini
MELO_DEVICE=cpu
```

#### Apple Silicon
```ini
MELO_DEVICE=mps
```

---

## 启动服务

### 方式 1：前台运行（显示日志）

```bash
# Windows
start_service.bat

# Linux/macOS
./start_service.sh
```

### 方式 2：后台运行

```bash
# Windows
start_service.vbs

# Linux
nohup python main.py > service.log 2>&1 &
```

### 方式 3：直接运行

```bash
# 激活环境
conda activate kokoro

# 启动服务
python main.py
```

### 启动日志

首次启动时会看到模型下载日志：

```
Initializing melo model...
MeloTTS will use device: auto
MeloTTS initialized with lazy loading strategy
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9880
```

首次请求时会触发模型下载：

```
Loading MeloTTS model (ZH)...
Downloading MeloTTS ZH model...
MeloTTS ZH model loaded. Speaker IDs: {...}
```

---

## 验证部署

### 1. 健康检查

```bash
curl http://localhost:9880/health
```

预期响应：
```json
{
  "status": "ok",
  "model": "melo",
  "model_loaded": false
}
```

**注意**: 由于 MeloTTS 使用延迟加载，`model_loaded` 初始为 `false`，首次请求后会变为 `true`。

### 2. 获取音色列表

```bash
curl http://localhost:9880/v1/audio/voices
```

### 3. 测试 TTS 生成

#### 测试英文文本

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, world!",
    "voice": "echo"
  }' \
  --output test.mp3
```

#### 测试中文文本

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "你好，世界！",
    "voice": "alloy"
  }' \
  --output test_zh.mp3
```

#### 测试中英混合文本

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello 你好, this is a test 这是一个测试",
    "voice": "alloy"
  }' \
  --output test_mix.mp3
```

### 4. 测试不同音色

```bash
# 美式英语
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "US English", "voice": "echo"}' \
  --output us_english.mp3

# 英式英语
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "British English", "voice": "fable"}' \
  --output british_english.mp3

# 澳大利亚英语
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Australian English", "voice": "shimmer"}' \
  --output aussie_english.mp3
```

---

## 常见问题

### Q1: 模型下载失败

**错误信息**: `Failed to download MeloTTS model`

**解决方案**:

```bash
# 手动设置国内镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或使用代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

### Q2: 中文文本发音为英文

**原因**: 文本语言检测错误

**解决方案**: 使用 `alloy` 音色，它支持中英混合：
```json
{
  "input": "中文文本",
  "voice": "alloy"
}
```

### Q3: 模型加载很慢

**原因**: MeloTTS 使用延迟加载，首次请求需要下载和加载模型

**解决方案**:
1. 预热请求：启动后立即发送一个测试请求
2. 或修改配置使用 eager loading（需要修改代码）

### Q4: CUDA out of memory

**解决方案**:
```bash
# 使用 CPU 模式
# 在 .env 中设置
MELO_DEVICE=cpu

# 或限制 GPU 内存
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
```

### Q5: 音色无效

**错误信息**: `Invalid voice 'xxx'`

**解决方案**: 查看支持的音色列表
```bash
curl http://localhost:9880/v1/audio/voices
```

MeloTTS 支持的 OpenAI 兼容音色：
- `alloy` - 中英双语
- `echo` - 美式英语
- `fable` - 英式英语
- `onyx` - 默认英语
- `nova` - 美式英语
- `shimmer` - 澳大利亚英语

---

## 性能优化

### GPU 加速

#### 1. 启用 CUDA

```ini
# 在 .env 中设置
MELO_DEVICE=cuda:0
```

#### 2. 多 GPU 支持

```bash
# 使用第二块 GPU
MELO_DEVICE=cuda:1
```

#### 3. 批量处理

MeloTTS 自动分句处理，长文本会逐句生成并合并。

### CPU 优化

#### 1. 设置线程数

```bash
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```

#### 2. 使用更快的 CPU

现代 CPU（支持 AVX2）会有更好的性能。

### Apple Silicon 优化

```ini
# 在 .env 中设置
MELO_DEVICE=mps
```

MPS (Metal Performance Shaders) 可以显著提升 Apple Silicon 上的性能。

### 网络优化

#### 1. 启用压缩

MeloTTS 生成的音频可以 gzip 压缩传输。

```nginx
gzip on;
gzip_types audio/mpeg audio/wav;
```

#### 2. 使用 CDN

缓存生成的音频文件到 CDN。

---

## MeloTTS 特有功能

### 1. 双语音色

`alloy` 音色是中英双语音色，可以无缝处理中英混合文本：

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello 你好, welcome to MeloTTS 欢迎使用MeloTTS",
    "voice": "alloy"
  }' \
  --output bilingual.mp3
```

### 2. 多种英语口音

MeloTTS 提供多种英语口音：

| 音色 | 口音 | 特点 |
|------|------|------|
| echo | 美式 | 标准美式发音 |
| fable | 英式 | 标准英式发音 |
| nova | 美式 | 美式发音（与 echo 不同） |
| shimmer | 澳大利亚 | 澳式发音 |
| onyx | 默认 | 通用英语发音 |

### 3. 自动语言检测

MeloTTS 会自动检测文本语言并选择合适的模型：

- **中文文本** → 使用 ZH 模型
- **英文文本** → 使用 EN 模型
- **混合文本** → 根据音色选择

### 4. 无需数字转换

与 Kokoro 不同，MeloTTS 可以直接处理数字：

```bash
# 直接使用数字，无需转换为单词
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "今天是2024年8月5日，温度25度", "voice": "alloy"}' \
  --output test.mp3
```

---

## 监控和日志

### 查看日志

```bash
# 前台运行
# 日志直接输出到控制台

# 后台运行
tail -f service.log
```

### 健康检查

```bash
# 基础健康检查
curl http://localhost:9880/health

# 详细健康检查
curl http://localhost:9880/health/detail
```

详细响应示例：
```json
{
  "status": "ok",
  "model": "melo",
  "model_loaded": true,
  "supported_voices": [
    "BILINGUAL",
    "EN-US",
    "EN-BR",
    "EN-Default",
    "EN-AU"
  ],
  "audio_format": "mp3",
  "sample_rate": 24000,
  "mp3_enabled": true,
  "dependencies": {
    "ffmpeg": true
  }
}
```

### 模型加载状态

首次请求后，模型状态会更新：

```bash
# 首次请求前
{"model_loaded": false}

# 首次请求后
{"model_loaded": true}
```

---

## 生产环境部署

### 使用 systemd（Linux）

创建 `/etc/systemd/system/tts-melo.service`:

```ini
[Unit]
Description=TTS Service (MeloTTS)
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/TTS_Service
Environment="PATH=/path/to/conda/envs/kokoro/bin"
Environment="TTS_MODEL=melo"
ExecStart=/path/to/conda/envs/kokoro/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tts-melo
sudo systemctl start tts-melo
sudo systemctl status tts-melo
```

### 使用 Docker

创建 `Dockerfile.melo`:

```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-melo.txt .
RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements-melo.txt

COPY . .

ENV TTS_MODEL=melo
EXPOSE 9880

CMD ["python3", "main.py"]
```

构建和运行：
```bash
docker build -f Dockerfile.melo -t tts-melo .
docker run -d -p 9880:9880 --gpus all tts-melo
```

### 使用 Nginx 反向代理

参考 Kokoro 部署文档中的 Nginx 配置。

---

## 升级和维护

### 升级 MeloTTS

```bash
# MeloTTS 会自动检查并更新模型
# 删除旧模型缓存以强制更新

# Linux/macOS
rm -rf ~/.local/share/melo/

# Windows
rd /s /q %APPDATA%\melo

# 重启服务，会自动下载最新模型
stop_service.bat
start_service.bat
```

### 清理缓存

```bash
# Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +

# MeloTTS 模型缓存（可选，节省空间）
# rm -rf ~/.local/share/melo/
```

---

## 附录

### A. Speaker ID 映射

查看 [models/melo/voice_mapping.json](../models/melo/voice_mapping.json) 了解完整的 speaker 映射。

### B. 支持的音色

MeloTTS 支持以下音色：

| OpenAI 音色 | Speaker ID | 语言 | 说明 |
|-------------|-----------|------|------|
| alloy | BILINGUAL | ZH | 中英双语 |
| echo | EN-US | EN | 美式英语 |
| fable | EN-BR | EN | 英式英语 |
| onyx | EN-Default | EN | 默认英语 |
| nova | EN-US | EN | 美式英语 |
| shimmer | EN-AU | EN | 澳大利亚英语 |

### C. 与 Kokoro 的区别

| 特性 | Kokoro | MeloTTS |
|------|--------|---------|
| 模型大小 | ~300MB | ~800MB (双模型) |
| 加载策略 | Eager（启动时加载） | Lazy（首次请求时加载） |
| 数字处理 | 需要转换 | 直接支持 |
| 双语支持 | 部分音色 | 完整支持 |
| 音色数量 | 8 种 | 5+ 种 |
| 启动速度 | 较慢 | 较快 |
| 首次请求 | 快 | 较慢（需加载模型） |

### D. 相关文档

- [架构设计文档](03_architecture_design.md)
- [类设计文档](04_class_design_core.md)
- [Kokoro 部署文档](01_deployment_kokoro.md)
