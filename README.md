# 绝对音准训练器（Absolute Pitch Trainer）

![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
![Python](https://img.shields.io/badge/python-3.13-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)
![Offline](https://img.shields.io/badge/voice-offline-orange)

简介：这是一个用于培养绝对音准的 Windows 桌面应用。<br>使用方式：播放单音/和弦/音程/旋律，用户通过语音或文字反馈听到的音高，程序自动判断对错，并给出即时反馈与历史统计。<br>项目灵感来源：我在练习乐器时，为了确保自己的音准无误，需要时刻盯着调音器，这会使我的注意力分散，无法全心全意放在对技术的磨练之中。因此我需要训练自己的耳朵，使它能够灵敏地听出来我演奏的每个音的音准是否正确。因此我想到了开发一个绝对音准训练程序来提升我的音高识别能力。<br>注：该项目为使用AI辅助进行编程学习的项目。

## 功能特性

- **共7 种训练模式**
  - 简单：C 大调自然音 C–B（无半音）
  - 普通：全部 12 音单音
  - 困难：自然音和弦（三/五/七/通用可选）
  - 地狱：不给标准音 + 全半音和弦
  - 地狱单音：不给标准音 + 全部 12 音单音
  - 音程：听两个音，判断音程
  - 旋律：听短旋律，写出音高序列
- **人性化功能**
  - 错题本：自动记录错题，可一键“只练错题”
  - 弱项分析：统计薄弱音高/和弦性质
  - 渐进难度：前一半简单、后一半加难
  - 严格模式：转位和弦要求答出转位
- **自定义设置**
  - 标准音 A 频率：438/440/442/443Hz
  - 调性（12 个调）
  - 单音范围、和弦根音范围
  - 音量、音色（正弦/钢琴/柔和）
- **答题方式**
  - 单音：文本框、音名快捷按钮 + 八度选择、语音输入
  - 和弦：专业符号 / 中文写法 / 英文拼写
  - 音程：纯五度、P5、major third 等
  - 旋律：`C4 E4 G4` 空格/逗号分隔
- **反馈与统计**
  - 每题即时对错，答错显示正确答案
  - 答错后播放所填答案音高，并自动补播正确音高
  - 历史正确率按模式保存最近 100 次
  - 柱状图 + 趋势折线、今日次数、连续打卡天数
- **语音能力**
  - 完全离线：Windows SAPI 语音输出 + Vosk 本地识别（中/英小模型）
  - 语音输入支持“■ 停止录音”手动结束
  - 模型缺失时自动下载并显示进度

## 环境要求

- Windows 10/11
- Python 3.13+
- 麦克风与扬声器（语音输入/音频播放可选）

## 快速开始

```bat
py -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python -m trainer.download_models
python main.py
```

也可以直接运行：

```bat
run.bat
```

> 首次使用语音输入时，如果 `models/` 为空，程序会自动下载中/英 Vosk 小模型。

## 打包 exe

```bat
build.bat
```

产物：

```text
dist\AbsolutePitchTrainer\AbsolutePitchTrainer.exe
```

模型会放在 exe 同目录的 `models\` 下；`build.bat` 会尝试自动下载并复制。

## 语音输入说明

- 点击“🎤 语音输入”后开始录音；录音中按钮变为“■ 停止录音”，可手动点击结束，也可静音自动结束。
- 单音可以说：`C4`、`C sharp four`、`升C4`、`do#4` 等。
- 和弦可以说：`C major`、`C major seventh`、`C 大三和弦`、`C 属七` 等。
- 识别引擎为 Vosk 小模型（en + zh-CN），完全离线。

## 项目结构

```text
absolute-pitch-trainer/
├─ main.py                    入口
├─ run.bat                    源码运行
├─ build.bat                  打包 exe
├─ requirements.txt           依赖
├─ LICENSE
├─ CHANGELOG.md
├─ CONTRIBUTING.md
├─ models/
│  └─ README.md               模型目录说明
└─ trainer/
   ├─ config.py               设置持久化
   ├─ history.py              历史成绩
   ├─ wrongbook.py            错题本与弱项分析
   ├─ music.py                乐理、题目生成、答案解析
   ├─ audio.py                音频合成/播放/录音/TTS/Vosk
   ├─ download_models.py      模型下载
   └─ ui/
      ├─ app.py               主窗口与页面调度
      ├─ theme.py             黑/白主题
      ├─ widgets.py           通用控件与动画
      └─ pages/               主页/训练/结果/历史/错题本
```

## 数据存储

- 设置与历史数据保存在 `%APPDATA%\AbsolutePitchTrainer\`
- 历史成绩按模式保留最近 100 次，更早数据自动删除
- 模型保存在项目或 exe 旁的 `models\` 目录



## 参与贡献

欢迎提交 Issue 和 PR，详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

本项目使用 [MIT License](LICENSE)。
