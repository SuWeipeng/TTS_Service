# Kokoro TTS 部署指南

本文档详细介绍如何部署和使用 Kokoro TTS 模型。

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
- **存储**: 至少 5GB 可用空间
- **GPU**: NVIDIA GPU（可选，推荐用于加速）
  - CUDA 11.0+
  - 显存 4GB+

### 软件要求

- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.8 或更高版本
- **Conda**: Miniconda 或 Anaconda
- **CUDA**: 11.0+ （如果使用 GPU）

---

## 环境准备

### 1. 创建 Conda 环境

```bash
# 创建名为 kokoro 的环境
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

### 3. 安装 ffmpeg（用于 MP3 编码）

#### Windows

```bash
# 使用 conda
conda install ffmpeg -c conda-forge

# 或手动下载：https://ffmpeg.org/download.html
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

# 安装 Kokoro 专用依赖
pip install -r requirements-kokoro.txt

# 可选：安装 MP3 编码支持
pip install -r requirements-mp3.txt
```

### 3. 准备模型文件

Kokoro 需要以下文件：

#### 方式 1：使用符号链接（推荐）

```bash
# 创建符号链接到原始模型文件
cd models/kokoro
ln -s ../../../kokoro/models_zh models_zh
ln -s ../../../kokoro/voices voices
```

#### 方式 2：复制文件

```bash
# 复制模型文件（约 300MB+）
cp -r ../kokoro/models_zh models/kokoro/
cp -r ../kokoro/voices models/kokoro/
```

### 4. 验证文件结构

确保目录结构如下：

```
models/kokoro/
├── models_zh/
│   ├── config.json
│   └── kokoro-v1_1-zh.pth
├── voices/
│   ├── af_heart.pt
│   ├── af_maple.pt
│   ├── af_nicole.pt
│   ├── af_sarah.pt
│   ├── af_sol.pt
│   ├── am_adam.pt
│   ├── am_michael.pt
│   └── bf_vale.pt
└── voice_mapping.json
```

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
TTS_MODEL=kokoro

# 服务器设置
HOST=0.0.0.0
PORT=9880

# 音频设置
SAMPLE_RATE=24000
DEFAULT_AUDIO_FORMAT=mp3
ENABLE_MP3=true

# Kokoro 配置
KOKORO_REPO_ID=kokoro_api
KOKORO_CONFIG_PATH=models/kokoro/models_zh/config.json
KOKORO_MODEL_PATH=models/kokoro/models_zh/kokoro-v1_1-zh.pth
KOKORO_VOICES_DIR=models/kokoro/voices
KOKORO_VOICE_MAPPING=models/kokoro/voice_mapping.json

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

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TTS_MODEL` | 模型选择 | `kokoro` |
| `HOST` | 服务器地址 | `0.0.0.0` |
| `PORT` | 服务器端口 | `9880` |
| `SAMPLE_RATE` | 音频采样率 | `24000` |
| `DEFAULT_AUDIO_FORMAT` | 默认音频格式 | `mp3` |
| `ENABLE_MP3` | 启用 MP3 编码 | `true` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

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

成功启动后会看到类似输出：

```
Initializing kokoro model...
Initializing Kokoro model...
Using device: cuda
Found: models/kokoro/models_zh/config.json
Found: models/kokoro/models_zh/kokoro-v1_1-zh.pth
Kokoro model initialized successfully
kokoro model loaded successfully
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9880 (Press CTRL+C to quit)
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
  "model": "kokoro",
  "model_loaded": true
}
```

### 2. 获取音色列表

```bash
curl http://localhost:9880/v1/audio/voices
```

### 3. 测试 TTS 生成

```bash
# 测试 OpenAI 兼容接口
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, world!",
    "voice": "alloy"
  }' \
  --output test.mp3

# 检查生成的音频文件
ls -lh test.mp3
```

### 4. 测试中文文本

```bash
curl -X POST http://localhost:9880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "你好，世界！",
    "voice": "shimmer"
  }' \
  --output test_zh.mp3
```

### 5. 测试 WebSocket 流式

使用提供的测试脚本：

```bash
cd TTS_Service
python ../kokoro/test_websocket_simple.py
```

---

## 常见问题

### Q1: 模型加载失败

**错误信息**: `Model file not found: models/kokoro/models_zh/kokoro-v1_1-zh.pth`

**解决方案**:
```bash
# 检查文件是否存在
ls models/kokoro/models_zh/

# 如果不存在，重新创建符号链接
cd models/kokoro
ln -s ../../../kokoro/models_zh models_zh
```

### Q2: CUDA out of memory

**错误信息**: `CUDA out of memory`

**解决方案**:
1. 使用 CPU 模式
2. 或使用更小的批次大小
3. 或清理 GPU 缓存

```bash
# 设置使用 CPU
# 在 .env 中添加或修改
Cuda_VISIBLE_DEVICES=""
```

### Q3: MP3 编码失败

**错误信息**: `MP3 encoding failed, returning WAV`

**解决方案**:
```bash
# 检查 ffmpeg 是否可用
ffmpeg -version

# 如果不可用，安装 ffmpeg
conda install ffmpeg -c conda-forge

# 或禁用 MP3，使用 WAV 格式
# 在 .env 中设置
ENABLE_MP3=false
DEFAULT_AUDIO_FORMAT=wav
```

### Q4: 端口被占用

**错误信息**: `Error while attempting to bind on address ('0.0.0.0', 9880)`

**解决方案**:
```bash
# Windows - 查找并关闭占用端口的进程
netstat -ano | findstr :9880
taskkill //F //PID <进程ID>

# 或使用停止脚本
stop_service.bat
```

### Q5: 中文文本发音不自然

**原因**: Kokoro 模型对英文数字的处理需要特殊转换

**解决方案**: 已内置数字处理逻辑，会自动将：
- 电话号码转换为单词
- IP 地址转换为单词格式
- 数字范围转换为"到"
- 货币符号转换为单词

如果仍有问题，可以检查 `text_processing/number_processor.py` 中的处理逻辑。

---

## 性能优化

### GPU 加速

#### 1. 使用正确的 CUDA 版本

```bash
# 检查 CUDA 版本
nvcc --version

# 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"
```

#### 2. 批量处理

Kokoro 支持自动分句处理，长文本会被自动分割成句子并逐个生成。

#### 3. 预加载模型

Kokoro 使用 Eager Loading 策略，模型在启动时加载，首次请求不需要等待。

### CPU 优化

#### 1. 设置线程数

```bash
# 在启动脚本中设置
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```

#### 2. 使用更快的 CPU

Kokoro 在 CPU 上也能良好运行，但现代 CPU（支持 AVX2）会有更好的性能。

### 网络优化

#### 1. 启用压缩

```nginx
# 在 nginx 配置中
gzip on;
gzip_types audio/mpeg audio/wav;
```

#### 2. 使用 CDN

将生成的音频文件缓存到 CDN，减轻服务器压力。

---

## 监控和日志

### 查看日志

```bash
# 前台运行时，日志会直接输出到控制台

# 后台运行时，查看日志文件
tail -f service.log
```

### 健康检查端点

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
  "model": "kokoro",
  "model_loaded": true,
  "supported_voices": [
    "af_heart",
    "af_maple",
    "af_nicole",
    "af_sarah",
    "af_sol",
    "am_adam",
    "am_michael",
    "bf_vale"
  ],
  "audio_format": "mp3",
  "sample_rate": 24000,
  "mp3_enabled": true,
  "dependencies": {
    "ffmpeg": true
  }
}
```

---

## 生产环境部署

### 使用 systemd（Linux）

创建 `/etc/systemd/system/tts-service.service`:

```ini
[Unit]
Description=TTS Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/TTS_Service
Environment="PATH=/path/to/conda/envs/kokoro/bin"
ExecStart=/path/to/conda/envs/kokoro/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tts-service
sudo systemctl start tts-service
sudo systemctl status tts-service
```

### 使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-kokoro.txt .
RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements-kokoro.txt

COPY . .

EXPOSE 9880

CMD ["python3", "main.py"]
```

构建和运行：
```bash
docker build -t tts-kokoro .
docker run -d -p 9880:9880 --gpus all tts-kokoro
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name tts.example.com;

    location / {
        proxy_pass http://localhost:9880;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 升级和维护

### 升级 Kokoro 模型

```bash
# 1. 备份当前模型
cp -r models/kokoro models/kokoro.backup

# 2. 下载新模型
# 将新的模型文件放到 models/kokoro/models_zh/

# 3. 更新配置（如有需要）
# 编辑 .env 文件

# 4. 重启服务
stop_service.bat
start_service.bat
```

### 清理缓存

```bash
# Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +

# 临时文件
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
```

---

## 附录

### A. 音色映射表

查看 [models/kokoro/voice_mapping.json](../models/kokoro/voice_mapping.json) 了解完整的音色映射配置。

### B. 支持的音色

Kokoro 支持 8 种内置音色：

| 音色 ID | 语言 | 性别 | 说明 |
|---------|------|------|------|
| af_heart | 中文/英文 | 女 | 柔和女声 |
| af_maple | 中文/英文 | 女 | 双语女声 |
| af_nicole | 英文 | 女 | Nicole 女声 |
| af_sarah | 英文 | 女 | Sarah 女声 |
| af_sol | 中文/英文 | 女 | 双语女声 |
| am_adam | 英文 | 男 | Adam 男声 |
| am_michael | 英文 | 男 | Michael 男声 |
| bf_vale | 中文/英文 | 中性 | 双语中性音 |

### C. 相关文档

- [架构设计文档](03_architecture_design.md)
- [类设计文档](04_class_design_core.md)
- [MeloTTS 部署文档](02_deployment_melo.md)
