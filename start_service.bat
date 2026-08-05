@echo off
REM TTS Service Startup Script
echo Starting TTS Service...

REM 切换到脚本所在目录
cd /d %~dp0

REM 激活 conda 环境
call conda activate kokoro

REM 启动服务（配置从 .env 文件读取）
python main.py
