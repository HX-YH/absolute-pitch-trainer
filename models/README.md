# 语音模型目录

本目录用于存放 Vosk 离线语音识别模型。

- 首次点击“语音输入”时，程序会自动下载中/英小模型到这里。
- 也可以提前手动下载：

```bat
venv\Scripts\python.exe -m trainer.download_models
```

- 模型文件较大，不会提交到 Git 仓库。
- 打包 exe 时，`build.bat` 会把本目录复制到 `dist\AbsolutePitchTrainer\models\`。
