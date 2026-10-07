@echo off
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (
    echo 未找到虚拟环境，请先运行 build.bat 或手动创建 venv。
    exit /b 1
)
call venv\Scripts\activate.bat
python main.py
