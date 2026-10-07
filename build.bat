@echo off
setlocal
cd /d "%~dp0"

echo === 绝对音准训练器 构建脚本 ===

if not exist venv (
    echo [1/5] 创建虚拟环境...
    py -m venv venv
)

echo [2/5] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || goto :error

echo [3/5] 下载语音识别模型（约 80MB，可跳过失败，应用内会重试）...
python -m trainer.download_models

echo [4/5] PyInstaller 打包...
pyinstaller --noconfirm --clean --name AbsolutePitchTrainer --onedir --windowed ^
  --collect-all vosk --collect-all sounddevice --collect-all pyttsx3 ^
  main.py || goto :error

echo [5/5] 复制模型到 exe 旁...
if exist models (
    xcopy /E /I /Y models dist\AbsolutePitchTrainer\models >nul
)

echo.
echo 构建完成：dist\AbsolutePitchTrainer\AbsolutePitchTrainer.exe
echo 直接双击 exe 即可运行。
goto :eof

:error
echo.
echo 构建失败，请查看上方错误信息。
exit /b 1
