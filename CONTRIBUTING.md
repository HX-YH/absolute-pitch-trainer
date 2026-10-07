# 参与贡献

感谢你对本项目的兴趣！

## 开发环境

- Windows 10/11
- Python 3.13+

```bat
py -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python -m trainer.download_models
python main.py
```

## 提交规范

1. Fork 本仓库并创建分支：`git checkout -b feature/your-feature`
2. 保持代码风格与现有文件一致（4 空格缩进、UTF-8、类型注解）。
3. 提交前确保代码可编译：

```bat
python -m compileall trainer main.py
```

4. 提交 PR，并说明改动内容与验证方式。

## 目录说明

- `trainer/music.py`：乐理、题目生成、答案解析
- `trainer/audio.py`：音频合成、播放、录音、TTS、Vosk
- `trainer/history.py`：历史成绩
- `trainer/wrongbook.py`：错题本与弱项分析
- `trainer/ui/`：Tkinter 界面与页面
