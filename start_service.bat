@echo off
REM TTS Service Startup Script
echo Starting TTS Service...

REM 切换到脚本所在目录
cd /d %~dp0

REM 激活 conda 环境
call conda activate melotts

REM 禁用 HuggingFace 联网检查，强制使用本地缓存（模型已在 ~/.cache/huggingface）
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

REM 启动服务（配置从 .env 文件读取）
python main.py
