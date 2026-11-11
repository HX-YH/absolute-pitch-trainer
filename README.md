# Absolute Pitch Trainer

![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
![Python](https://img.shields.io/badge/python-3.13-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)
![Offline](https://img.shields.io/badge/voice-offline-orange)

**English** | [中文](#中文)

This is a small Windows desktop app I built to practice absolute pitch, often called perfect pitch. It plays a note, a chord, an interval, or a short melody, and you tell it what you heard by typing or speaking. The app checks your answer and gives you instant feedback.

I'm still learning programming, so this is also a learning project. I tried to keep the code readable and the interface simple. It's not a commercial product, and there are probably still a few rough edges, but it does what I need it to do.

## What it can do

**Seven practice modes**

- Easy: a reference A plus natural notes from the C major scale (1–7, no sharps or flats)
- Normal: a reference A plus all 12 notes
- Hard: a reference A plus chords built from natural notes (triads, power chords, seventh chords, or all of them)
- Hell: no reference note, chromatic chords
- Hell single note: no reference note, all 12 notes
- Interval: listen to two notes and name the interval
- Melody: listen to a short melody and write down the notes

**Smart practice**

- Mistake notebook: wrong answers are saved automatically, and you can practice only those questions
- Weak-spot stats: see which notes or chord types you miss most
- Progressive difficulty: the first half is easier, the second half is harder
- Strict mode: when a chord is played in an inversion, you also need to name the inversion

**Make it yours**

- Reference pitch: 438 / 440 / 442 / 443 Hz
- Key: all 12 keys
- Note range and chord root range
- Volume and tone (sine, piano, soft)

**How you answer**

- Single notes: text box, note buttons with octave selection, or voice
- Chords: standard symbols, Chinese names, or English spellings
- Intervals: "perfect fifth", "P5", "major third", and so on
- Melody: notes separated by spaces or commas, like `C4 E4 G4`

**Feedback and progress**

- Instant right/wrong feedback, with the correct answer shown after a mistake
- After a wrong answer, you can play what you entered, and the app also plays the correct pitch
- Accuracy history keeps the latest 100 sessions for each mode
- Bar chart, trend line, today's practice count, and streak days

**Voice**

- Fully offline: Windows SAPI for speech output and Vosk for speech recognition (small English and Chinese models)
- You can stop recording manually with the "■ Stop recording" button
- If the models are missing, the app downloads them and shows progress

**Interface**

- Simple black-and-white look inspired by Apple's minimal style
- Page transitions, number rolling, chart animation, and popup scaling

## Requirements

- Windows 10 or 11
- Python 3.13 or newer
- A microphone and speakers (optional, but needed for voice input and audio playback)

## Getting started

```bat
py -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python -m trainer.download_models
python main.py
```

Or just run:

```bat
run.bat
```

> If `models/` is empty when you first use voice input, the app will download the small English and Chinese Vosk models automatically.

## Build the exe

```bat
build.bat
```

The output goes here:

```text
dist\AbsolutePitchTrainer\AbsolutePitchTrainer.exe
```

The models are placed in a `models\` folder next to the exe. `build.bat` will try to download and copy them for you.

## Voice input tips

- Click "🎤 Voice input" to start recording. While recording, the button changes to "■ Stop recording". You can stop it yourself, or just stop speaking and let the app finish automatically.
- For single notes, you can say things like `C4`, `C sharp four`, `升C4`, or `do#4`.
- For chords, you can say things like `C major`, `C major seventh`, `C 大三和弦`, or `C 属七`.
- Speech recognition uses the small Vosk models (English and zh-CN) and works fully offline.

## Project layout

```text
absolute-pitch-trainer/
├─ main.py                    entry point
├─ run.bat                    run from source
├─ build.bat                  build the exe
├─ requirements.txt           dependencies
├─ LICENSE
├─ CHANGELOG.md
├─ CONTRIBUTING.md
├─ models/
│  └─ README.md               notes about the model folder
└─ trainer/
   ├─ config.py               saves user settings
   ├─ history.py              practice history
   ├─ wrongbook.py            mistake notebook and weak-spot stats
   ├─ music.py                music theory, question generation, answer parsing
   ├─ audio.py                audio synthesis, playback, recording, TTS, Vosk
   ├─ download_models.py      model downloader
   └─ ui/
      ├─ app.py               main window and page navigation
      ├─ theme.py             black-and-white theme
      ├─ widgets.py           shared widgets and animations
      └─ pages/               home, training, results, history, mistake notebook
```

## Where your data lives

- Settings and practice data are stored in `%APPDATA%\AbsolutePitchTrainer\`
- Each mode keeps the latest 100 practice sessions, and older ones are removed automatically
- Models live in the `models\` folder next to the project or the exe

## FAQ

**Why are there no sharps or flats in Easy mode?**
Easy mode stays in C major and uses only the natural notes 1–7. It's meant to be the simplest starting point.

**Why is the first voice input so slow?**
The app needs to download the small English and Chinese Vosk models, about 80 MB in total. After that, voice input works offline.

**What if I hear no sound?**
The app tries `sounddevice + numpy` first and falls back to Windows `winsound` if needed. Check your default playback device and system volume.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

This project is licensed under the [MIT License](LICENSE).

---

<a id="中文"></a>
# 绝对音准训练器（Absolute Pitch Trainer）

一个 Windows 桌面应用，用于培养绝对音准。播放单音/和弦/音程/旋律，用户通过语音或文字反馈听到的音高，程序自动判断对错，并给出即时反馈与历史统计。

## 功能特性

- **7 种训练模式**
  - 简单：标准音 A + C 大调自然音 1–7（无升降号）
  - 普通：标准音 A + 全部 12 音单音
  - 困难：标准音 A + 自然音内和弦（三/五/七/通用可选）
  - 地狱：无标准音 + 全半音和弦
  - 地狱单音：无标准音 + 全部 12 音单音
  - 音程：听两个音，判断音程
  - 旋律：听短旋律，写出音高序列
- **智能训练**
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
- **界面**
  - 黑/白极简苹果风，页面切换、数字滚动、图表生长、弹窗缩放等动画

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

## 常见问题

**Q：为什么简单模式没有升降号？**
A：简单模式固定为 C 大调自然音 1–7，用于建立最基础的音高概念。

**Q：为什么第一次语音输入很慢？**
A：需要下载 Vosk 中/英小模型，约 80MB，下载完成后完全离线可用。

**Q：没有声音怎么办？**
A：程序优先使用 `sounddevice + numpy` 播放，失败时自动回退到 Windows `winsound`。请检查系统默认播放设备和音量。

## 参与贡献

欢迎提交 Issue 和 PR，详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

本项目使用 [MIT License](LICENSE)。
