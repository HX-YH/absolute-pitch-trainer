# -*- coding: utf-8 -*-
"""错题本：保存答错的题目，支持只练错题与弱项分析。"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .config import app_data_dir

MAX_WRONG_QUESTIONS = 500


def question_key(q: dict) -> str:
    if q.get("type") == "note":
        return f"note:{q.get('midi')}"
    if q.get("type") == "chord":
        return f"chord:{q.get('root_pc')}:{q.get('quality')}"
    if q.get("type") == "interval":
        return f"interval:{q.get('midis')}"
    if q.get("type") == "melody":
        return f"melody:{'-'.join(str(m) for m in q.get('play_midis', []))}"
    return f"{q.get('type')}:{json.dumps(q, ensure_ascii=False, sort_keys=True)}"


class WrongBook:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "wrong_questions.json")
        self.data: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self.data = raw
        except Exception:
            self.data = {}

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def add(self, q: dict) -> None:
        key = question_key(q)
        entry = self.data.get(key)
        if entry is None:
            self.data[key] = {
                "q": q,
                "wrong_count": 1,
                "last_wrong_ts": time.time(),
            }
        else:
            entry["q"] = q
            entry["wrong_count"] = int(entry.get("wrong_count", 0)) + 1
            entry["last_wrong_ts"] = time.time()
        # 控制总量
        if len(self.data) > MAX_WRONG_QUESTIONS:
            oldest_key = min(self.data, key=lambda k: self.data[k].get("last_wrong_ts", 0))
            self.data.pop(oldest_key, None)
        self.save()

    def remove(self, q: dict) -> None:
        key = question_key(q)
        if key in self.data:
            self.data.pop(key, None)
            self.save()

    def has(self, q: dict) -> bool:
        return question_key(q) in self.data

    def questions(self) -> list[dict]:
        items = list(self.data.values())
        items.sort(key=lambda e: e.get("last_wrong_ts", 0), reverse=True)
        return [e["q"] for e in items]

    def count(self) -> int:
        return len(self.data)

    def clear(self) -> None:
        self.data = {}
        self.save()

    # ------------------------------------------------------------ 弱项分析

    def weak_notes(self, limit: int = 5) -> list[tuple[int, int]]:
        """返回 (音级, 错误次数) 降序列表。"""
        stats: dict[int, int] = {}
        for entry in self.data.values():
            q = entry["q"]
            if q.get("type") == "note":
                pc = q.get("root_pc")
                if pc is not None:
                    stats[pc] = stats.get(pc, 0) + int(entry.get("wrong_count", 1))
            elif q.get("type") == "chord":
                pc = q.get("root_pc")
                if pc is not None:
                    stats[pc] = stats.get(pc, 0) + int(entry.get("wrong_count", 1))
        return sorted(stats.items(), key=lambda x: x[1], reverse=True)[:limit]

    def weak_chord_qualities(self, limit: int = 5) -> list[tuple[str, int]]:
        stats: dict[str, int] = {}
        for entry in self.data.values():
            q = entry["q"]
            if q.get("type") == "chord":
                quality = q.get("quality")
                if quality:
                    stats[quality] = stats.get(quality, 0) + int(entry.get("wrong_count", 1))
        return sorted(stats.items(), key=lambda x: x[1], reverse=True)[:limit]
