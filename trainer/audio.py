# -*- coding: utf-8 -*-
"""音频模块：正弦波生成/播放、录音、语音合成、Vosk 语音识别与模型下载。"""
from __future__ import annotations

import array
import io
import json
import math
import os
import sys
import tempfile
import threading
import time
import urllib.request
import wave
import zipfile
from pathlib import Path
from typing import Callable, Iterable, Optional

from .config import models_dir
from . import music

try:
    import winsound
except ImportError:  # 非 Windows 环境仅用于静态检查
    winsound = None

SAMPLE_RATE = 44100
RECORD_SAMPLE_RATE = 16000

PLAYBACK_VOLUME = 0.5
PLAYBACK_TIMBRE = "sine"
PLAYBACK_A4 = 442.0
_last_playback_ref = None


def configure_playback(volume: float | None = None, timbre: str | None = None,
                       a4_freq: float | None = None) -> None:
    global PLAYBACK_VOLUME, PLAYBACK_TIMBRE, PLAYBACK_A4
    if volume is not None:
        PLAYBACK_VOLUME = max(0.05, min(1.0, float(volume)))
    if timbre in ("sine", "piano", "soft"):
        PLAYBACK_TIMBRE = timbre
    if a4_freq is not None:
        PLAYBACK_A4 = float(a4_freq)

MODEL_URLS = {
    "en": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
    "cn": "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip",
}
MODEL_EXTRACT_NAMES = {
    "en": "vosk-model-small-en-us-0.15",
    "cn": "vosk-model-small-cn-0.22",
}

# ---------------------------------------------------------------- 合成/播放


def _tone_value(freq: float, i: int, sample_rate: int, timbre: str) -> float:
    t = i / sample_rate
    phase = 2.0 * math.pi * freq * t
    if timbre == "piano":
        return (
            0.70 * math.sin(phase)
            + 0.20 * math.sin(2.0 * phase) * math.exp(-2.0 * t)
            + 0.10 * math.sin(3.0 * phase) * math.exp(-3.0 * t)
        )
    if timbre == "soft":
        # 柔和：基音为主，带轻微二次谐波和更慢的起音
        return 0.92 * math.sin(phase) + 0.08 * math.sin(2.0 * phase) * math.exp(-1.5 * t)
    return math.sin(phase)


def _write_sine_into(buffer: array.array, start_sample: int, freq: float,
                     duration: float, sample_rate: int, volume: float,
                     timbre: str = "sine") -> None:
    """把一段带淡入淡出包络的波形叠加进 buffer。"""
    n = int(duration * sample_rate)
    attack = max(1, int(0.01 * sample_rate))
    release = max(1, int(0.08 * sample_rate))
    if timbre == "soft":
        attack = max(1, int(0.03 * sample_rate))
        release = max(1, int(0.12 * sample_rate))
    for i in range(n):
        idx = start_sample + i
        if idx < 0 or idx >= len(buffer):
            continue
        env = 1.0
        if i < attack:
            env = i / attack
        elif i > n - release:
            env = max(0.0, (n - i) / release)
        raw = volume * env * _tone_value(freq, i, sample_rate, timbre)
        sample = int(raw * 32767.0)
        buffer[idx] = max(-32767, min(32767, buffer[idx] + sample))


def generate_wav_bytes(midis: Iterable[int], duration: float = 1.4,
                       arpeggio: bool = False, volume: float | None = None,
                       timbre: str | None = None,
                       sample_rate: int = SAMPLE_RATE) -> bytes:
    """生成 WAV 字节。midis 为 MIDI 音高列表；arpeggio=True 时依次琶音。"""
    if volume is None:
        volume = PLAYBACK_VOLUME
    if timbre is None:
        timbre = PLAYBACK_TIMBRE
    midis = list(midis)
    if not midis:
        return b""
    if arpeggio:
        per_note = max(0.35, duration / max(1, len(midis)))
        total = int((per_note * len(midis) + 0.25) * sample_rate)
    else:
        total = int(duration * sample_rate)

    buffer = array.array("h", [0]) * total
    if arpeggio:
        gap = 0.12
        for i, midi in enumerate(midis):
            freq = music.midi_to_freq(midi, a4=PLAYBACK_A4)
            start = int(i * (per_note + gap) * sample_rate)
            _write_sine_into(buffer, start, freq, per_note, sample_rate, volume / max(1, len(midis)), timbre)
    else:
        freq_list = [music.midi_to_freq(m, a4=PLAYBACK_A4) for m in midis]
        for freq in freq_list:
            _write_sine_into(buffer, 0, freq, duration, sample_rate, volume / max(1, len(midis)), timbre)

    with io.BytesIO() as bio:
        with wave.open(bio, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(buffer.tobytes())
        return bio.getvalue()


def _play_sounddevice(data: bytes) -> bool:
    """尝试用 sounddevice+numpy 播放，成功返回 True。"""
    global _last_playback_ref
    try:
        import numpy as np
        import sounddevice as sd
        with wave.open(io.BytesIO(data), "rb") as w:
            frames = w.readframes(w.getnframes())
        arr = np.frombuffer(frames, dtype=np.int16)
        _last_playback_ref = arr  # 保持引用直到播放完成
        sd.play(arr, samplerate=SAMPLE_RATE)
        return True
    except Exception:
        return False


def play_midis(midis: Iterable[int], duration: float = 1.4, arpeggio: bool = False) -> bool:
    """异步播放。优先 sounddevice+numpy，失败时回退 winsound 临时文件。"""
    data = generate_wav_bytes(midis, duration=duration, arpeggio=arpeggio)
    if _play_sounddevice(data):
        return True

    if winsound is None:
        return False
    path = None
    try:
        fd, path = tempfile.mkstemp(prefix="apt_", suffix=".wav")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
        winsound.PlaySound(path, flags)
        # 预计播放完成后删除临时文件
        timer = threading.Timer(duration + 1.0, _cleanup_temp_wav, args=[path])
        timer.daemon = True
        timer.start()
        return True
    except Exception:
        if path:
            _cleanup_temp_wav(path)
        return False


def _cleanup_temp_wav(path: str) -> None:
    try:
        os.unlink(path)
    except Exception:
        pass


def play_question(q: dict, arpeggio: bool = False) -> bool:
    """播放一道题（单音/和弦/音程/旋律）。"""
    if q["type"] == "note":
        return play_midis(q["play_midis"], duration=1.2)
    if q["type"] in ("interval", "melody"):
        # 音程/旋律用依次播放的方式呈现
        return play_midis(q["play_midis"], duration=2.0, arpeggio=True)
    duration = 1.8 if len(q["play_midis"]) > 2 else 1.4
    return play_midis(q["play_midis"], duration=duration, arpeggio=arpeggio)


# ---------------------------------------------------------------- TTS

_tts_lock = threading.Lock()
_tts_engine = None
_tts_voice_map: dict[str, str] = {}


def _get_tts_engine():
    global _tts_engine, _tts_voice_map
    with _tts_lock:
        if _tts_engine is None:
            import pyttsx3
            engine = pyttsx3.init()
            for v in engine.getProperty("voices"):
                ident = str(getattr(v, "id", "") or "").lower()
                name = str(getattr(v, "name", "") or "").lower()
                if "huihui" in ident or "huihui" in name or "zh" in ident:
                    _tts_voice_map.setdefault("zh", ident or name)
                if "zira" in ident or "zira" in name or "en" in ident:
                    _tts_voice_map.setdefault("en", ident or name)
            _tts_engine = engine
        return _tts_engine


def speak(text: str, lang: str = "zh") -> None:
    """文本转语音（阻塞，请在后台线程调用）。"""
    try:
        engine = _get_tts_engine()
        with _tts_lock:
            voice = _tts_voice_map.get(lang)
            if voice:
                engine.setProperty("voice", voice)
            engine.setProperty("rate", 175)
            engine.say(text)
            engine.runAndWait()
    except Exception:
        pass


# ---------------------------------------------------------------- 录音

def _rms(data: bytes) -> float:
    if not data:
        return 0.0
    a = array.array("h")
    a.frombytes(data)
    if not a:
        return 0.0
    s = sum(x * x for x in a)
    return math.sqrt(s / len(a))


def record_until_silence(max_seconds: float = 6.0,
                         silence_threshold: float = 300.0,
                         silence_duration: float = 0.8,
                         sample_rate: int = RECORD_SAMPLE_RATE,
                         stop_event=None) -> Optional[bytes]:
    """录音直到静音自动结束；未检测到声音则录满 max_seconds。

    stop_event 提供手动停止：设置后会在当前块结束后立即返回已录到的数据。
    """
    try:
        import sounddevice as sd
    except Exception:
        return None

    blocksize = int(sample_rate * 0.1)  # 100ms
    chunks: list[bytes] = []
    silent_chunks = 0
    started = False
    total_seconds = 0.0
    block_duration = blocksize / sample_rate

    try:
        with sd.RawInputStream(samplerate=sample_rate, blocksize=blocksize,
                               channels=1, dtype="int16") as stream:
            while total_seconds < max_seconds:
                if stop_event is not None and stop_event.is_set():
                    break
                data, _ = stream.read(blocksize)
                chunks.append(data)
                total_seconds += block_duration
                rms = _rms(data)
                if rms > silence_threshold:
                    started = True
                    silent_chunks = 0
                elif started:
                    silent_chunks += 1
                if started and silent_chunks * block_duration >= silence_duration:
                    break
    except Exception:
        return None
    return b"".join(chunks)


# ---------------------------------------------------------------- Vosk

_model_cache: dict[str, object] = {}
_model_lock = threading.Lock()


def model_path(lang: str) -> Optional[Path]:
    name = MODEL_EXTRACT_NAMES.get(lang)
    if not name:
        return None
    path = models_dir() / name
    return path if path.exists() else None


def _download_with_progress(url: str, target: Path, progress_cb: Optional[Callable[[float], None]] = None) -> None:
    tmp = target.with_suffix(".zip.tmp")
    req = urllib.request.Request(url, headers={"User-Agent": "AbsolutePitchTrainer/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb and total:
                    progress_cb(min(1.0, downloaded / total))
    tmp.replace(target)


def ensure_model(lang: str, progress_cb: Optional[Callable[[float], None]] = None) -> Optional[Path]:
    """确保指定语言模型存在；不存在则下载并解压。"""
    existing = model_path(lang)
    if existing:
        return existing
    url = MODEL_URLS.get(lang)
    if not url:
        return None
    models = models_dir()
    zip_path = models / f"{MODEL_EXTRACT_NAMES[lang]}.zip"
    try:
        if not zip_path.exists():
            _download_with_progress(url, zip_path, progress_cb)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(models)
        # 解压后清理 zip
        try:
            zip_path.unlink()
        except Exception:
            pass
        return model_path(lang)
    except Exception:
        return None


def _get_model(lang: str) -> object:
    from vosk import Model
    with _model_lock:
        if lang in _model_cache:
            return _model_cache[lang]
        path = model_path(lang)
        if not path:
            raise FileNotFoundError(f"Vosk model for '{lang}' not found")
        model = Model(str(path))
        _model_cache[lang] = model
        return model


def recognize_bytes(data: bytes, lang: str) -> str:
    """用指定 Vosk 模型识别 PCM int16 16k mono 字节流，返回文本。"""
    if not data:
        return ""
    from vosk import KaldiRecognizer
    model = _get_model(lang)
    rec = KaldiRecognizer(model, RECORD_SAMPLE_RATE)
    rec.SetWords(False)
    chunk_size = 4000
    for i in range(0, len(data), chunk_size):
        rec.AcceptWaveform(data[i:i + chunk_size])
    result = json.loads(rec.FinalResult())
    return str(result.get("text", "")).strip()


def _domain_score(text: str) -> int:
    t = text.lower()
    score = 0
    if music.parse_note(t) or music.parse_chord(t):
        score += 3
    if any(ch in t for ch in "abcdefg") or any(ch in t for ch in "哆来咪发唆嗦拉西"):
        score += 1
    if any(k in t for k in ("sharp", "flat", "升", "降", "major", "minor", "dim", "aug", "power", "七", "三", "五")):
        score += 1
    return score


def recognize_voice(data: bytes, prefer_lang: str = "auto") -> str:
    """识别语音，auto 时同时跑中英文模型，选领域匹配度更高的结果。"""
    langs = ["en", "cn"] if prefer_lang == "auto" else [prefer_lang]
    best = ""
    best_score = -1
    for lang in langs:
        try:
            text = recognize_bytes(data, lang)
        except Exception:
            text = ""
        if not text:
            continue
        score = _domain_score(text)
        if score > best_score:
            best = text
            best_score = score
        if best_score >= 3:
            break
    return best
