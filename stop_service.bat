@echo off
REM TTS Service Stop Script

echo Stopping TTS Service...

REM 查找并关闭占用9880端口的进程（Kokoro）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9880 ^| findstr LISTENING') do (
    echo Stopping Kokoro service (PID: %%a)...
    taskkill //F //PID %%a
)

REM 查找并关闭占用9889端口的进程（MeloTTS）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9889 ^| findstr LISTENING') do (
    echo Stopping MeloTTS service (PID: %%a)...
    taskkill //F //PID %%a
)

echo TTS Service stopped.
