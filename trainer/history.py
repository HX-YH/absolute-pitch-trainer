# -*- coding: utf-8 -*-
"""历史成绩记录：按模式保存最近 100 次，自动删除更早数据。"""
from __future__ import annotations

import datetime
import json
import time
from pathlib import Path

from .config import app_data_dir

MAX_RECORDS_PER_MODE = 100


class History:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "history.json")
        self.data: dict[str, list[dict]] = {}
        self.load()

    def load(self) -> None:
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self.data = {str(k): list(v) for k, v in raw.items() if isinstance(v, list)}
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

    @staticmethod
    def _trim(records: list[dict]) -> list[dict]:
        """只保留最近 MAX_RECORDS_PER_MODE 条（按时间戳升序存储时保留末尾）。"""
        records.sort(key=lambda r: r.get("ts", 0))
        if len(records) > MAX_RECORDS_PER_MODE:
            records = records[-MAX_RECORDS_PER_MODE:]
        return records

    def add(self, mode: str, rounds: int, correct: int, total: int,
            details: list[dict] | None = None) -> dict:
        record = {
            "ts": time.time(),
            "mode": mode,
            "rounds": rounds,
            "correct": correct,
            "total": total,
            "accuracy": round(correct / total, 4) if total else 0.0,
            "details": details or [],
        }
        records = self.data.setdefault(mode, [])
        records.append(record)
        self.data[mode] = self._trim(records)
        self.save()
        return record

    def records(self, mode: str | None = None) -> list[dict]:
        if mode is None:
            merged: list[dict] = []
            for recs in self.data.values():
                merged.extend(recs)
            merged.sort(key=lambda r: r.get("ts", 0))
            return merged
        return list(self.data.get(mode, []))

    def summary(self, mode: str | None = None) -> dict:
        recs = self.records(mode)
        if not recs:
            return {"count": 0, "last_accuracy": None, "avg_accuracy": None}
        accs = [r.get("accuracy", 0.0) for r in recs]
        return {
            "count": len(recs),
            "last_accuracy": accs[-1],
            "avg_accuracy": sum(accs) / len(accs),
        }

    def today_count(self, mode: str | None = None) -> int:
        today = datetime.date.today().isoformat()
        return sum(
            1 for r in self.records(mode)
            if datetime.date.fromtimestamp(r.get("ts", 0)).isoformat() == today
        )

    def streak_days(self) -> int:
        """连续练习天数：从今天或昨天开始往前数。"""
        days = {
            datetime.date.fromtimestamp(r.get("ts", 0))
            for r in self.records()
        }
        if not days:
            return 0
        streak = 0
        day = datetime.date.today()
        if day not in days:
            day = day - datetime.timedelta(days=1)
        while day in days:
            streak += 1
            day -= datetime.timedelta(days=1)
        return streak

    def clear(self, mode: str | None = None) -> None:
        if mode is None:
            self.data = {}
        else:
            self.data.pop(mode, None)
        self.save()
