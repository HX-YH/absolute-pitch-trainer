# -*- coding: utf-8 -*-
"""配置与历史数据的本地持久化。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


APP_NAME = "AbsolutePitchTrainer"


def app_data_dir() -> Path:
    """用户目录下的应用数据目录（%APPDATA%/AbsolutePitchTrainer）。"""
    base = os.environ.get("APPDATA")
    if base:
        path = Path(base) / APP_NAME
    else:
        path = Path.home() / f".{APP_NAME}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def models_dir() -> Path:
    """模型目录：打包后放在 exe 旁，源码运行放在项目根目录。"""
    if getattr(sys, "frozen", False):
        path = Path(sys.executable).resolve().parent / "models"
    else:
        path = Path(__file__).resolve().parent.parent / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class Config:
    """应用设置：记住上次选择。"""

    DEFAULTS = {
        "mode": "easy",          # easy / normal / hard / hell / hell_note / interval / melody
        "chord_category": "all", # triad / power / seventh / all
        "rounds": 5,             # 5 / 10 / 20
        "ignore_octave": False,
        "random_inversions": False,
        "voice_lang": "auto",    # auto / cn / en
        "a4_freq": 442.0,
        "key": 0,                # 0=C, 1=C# ... 11=B
        "note_low": 48,          # C3
        "note_high": 84,         # C6
        "chord_low": 48,         # C3
        "chord_high": 72,        # C5
        "progressive": False,    # 渐进难度
        "strict_mode": False,    # 严格转位/严格音高判定
        "volume": 0.5,
        "timbre": "sine",        # sine / piano / soft
        "first_run": True,
    }

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "config.json")
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            if self.path.exists():
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    self.data.update({k: v for k, v in saved.items() if k in self.DEFAULTS})
        except Exception:
            # 配置损坏时回退默认值，不阻塞启动
            self.data = dict(self.DEFAULTS)

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def get(self, key: str):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key: str, value) -> None:
        self.data[key] = value
        self.save()
