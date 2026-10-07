# -*- coding: utf-8 -*-
"""历史成绩页：按模式展示列表与柱状图。"""
from __future__ import annotations

import datetime
import tkinter as tk

from ..theme import BG, FG, CARD, GRAY, BORDER, SUCCESS, ERROR
from ..widgets import FlatButton, SegmentedControl, font
from ...music import MODE_LABELS, SHARP_NAMES
from ...history import MAX_RECORDS_PER_MODE


class HistoryPage(tk.Frame):
    def __init__(self, app):
        super().__init__(app.container, bg=BG)
        self.app = app
        self.current_mode = "easy"
        self._chart_gen = 0
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        FlatButton(top, text="‹ 返回", command=lambda: self.app.show_page("home"),
                   bg=BG, fg=GRAY, hover_bg="#1c1c1e", font_size=14).pack(side="left")
        tk.Label(top, text="历史成绩", bg=BG, fg=FG, font=font(24, True)).pack(side="left", padx=20)

        # 模式选择
        all_modes = ("easy", "normal", "hard", "hell", "hell_note", "interval", "melody")
        self.mode_selector = SegmentedControl(
            self, [(k, MODE_LABELS[k]) for k in all_modes],
            selected=self.current_mode, on_select=self._set_mode, bg=BG,
        )
        self.mode_selector.pack(pady=(20, 10))

        # 汇总卡片
        self.summary_frame = tk.Frame(self, bg=BG)
        self.summary_frame.pack(fill="x", padx=60, pady=10)
        self.summary_labels: dict[str, tk.Label] = {}
        for key in ("count", "last", "avg", "today", "streak"):
            card = tk.Frame(self.summary_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", expand=True, fill="x", padx=5, pady=4)
            name = {"count": "训练次数", "last": "最近正确率", "avg": "平均正确率",
                    "today": "今日次数", "streak": "连续天数"}[key]
            tk.Label(card, text=name, bg=CARD, fg=GRAY, font=font(10)).pack(pady=(8, 2))
            self.summary_labels[key] = tk.Label(card, text="—", bg=CARD, fg=FG, font=font(15, True))
            self.summary_labels[key].pack(pady=(0, 8))

        # 柱状图
        self.chart_label = tk.Label(self, text="最近成绩趋势", bg=BG, fg=GRAY, font=font(12))
        self.chart_label.pack(pady=(8, 0))
        self.chart = tk.Canvas(self, width=760, height=180, bg=BG, highlightthickness=0)
        self.chart.pack(pady=6)

        # 弱项分析
        self.weak_label = tk.Label(self, text="", bg=BG, fg=GRAY, font=font(11))
        self.weak_label.pack(pady=(0, 4))

        # 列表
        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=80, pady=(4, 20))
        self.listbox = tk.Listbox(list_frame, bg=CARD, fg=FG, selectbackground=FG,
                                  selectforeground=BG, relief="flat", highlightthickness=1,
                                  highlightbackground=BORDER, font=font(12), height=8)
        scroll = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview,
                              bg=BG, troughcolor=BG, activebackground=GRAY)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def on_show(self, **kwargs):
        self.current_mode = self.app.config.get("mode")
        self.mode_selector.select(self.current_mode)
        self._refresh()

    def _set_mode(self, mode: str):
        self.current_mode = mode
        self._refresh()

    def _refresh(self):
        mode = self.current_mode
        summary = self.app.history.summary(mode)
        self.summary_labels["count"].config(text=str(summary["count"]))
        self.summary_labels["last"].config(
            text=f"{summary['last_accuracy'] * 100:.0f}%" if summary["last_accuracy"] is not None else "—"
        )
        self.summary_labels["avg"].config(
            text=f"{summary['avg_accuracy'] * 100:.0f}%" if summary["avg_accuracy"] is not None else "—"
        )
        self.summary_labels["today"].config(text=str(self.app.history.today_count(mode)))
        self.summary_labels["streak"].config(text=str(self.app.history.streak_days()))

        records = self.app.history.records(mode)[-20:]
        self._draw_chart(records)

        # 弱项分析
        weak_parts = []
        weak_notes = self.app.wrongbook.weak_notes(3)
        weak_chords = self.app.wrongbook.weak_chord_qualities(3)
        if weak_notes:
            weak_parts.append("薄弱音：" + "、".join(SHARP_NAMES[pc] for pc, _ in weak_notes))
        if weak_chords:
            weak_parts.append("薄弱和弦：" + "、".join(q for q, _ in weak_chords))
        self.weak_label.config(text="    ".join(weak_parts) if weak_parts else "暂无弱项数据，继续加油")

        self.listbox.delete(0, "end")
        if not records:
            self.listbox.insert("end", "暂无记录，去完成一次训练吧")
        for r in records:
            ts = datetime.datetime.fromtimestamp(r.get("ts", 0)).strftime("%m-%d %H:%M")
            self.listbox.insert(
                "end",
                f"{ts}    {r.get('correct')}/{r.get('total')}    {r.get('accuracy', 0) * 100:.0f}%",
            )

    def _draw_chart(self, records: list[dict]):
        self._chart_gen += 1
        gen = self._chart_gen
        self.chart.delete("all")
        if not records:
            self.chart.create_text(380, 90, text="暂无数据", fill=GRAY, font=font(13))
            return
        w = 760
        h = 180
        margin = 30
        n = len(records)
        step = (w - 2 * margin) / n
        max_acc = max(0.1, max(r.get("accuracy", 0) for r in records))
        base_y = h - margin
        points = []
        bars = []
        for i, r in enumerate(records):
            acc = r.get("accuracy", 0)
            x = margin + i * step + step / 2
            y = base_y - (h - 50) * acc / max_acc
            points.append((x, y))
            bar_w = min(24, step - 8)
            color = SUCCESS if acc >= 0.6 else (GRAY if acc >= 0.4 else ERROR)
            rect = self.chart.create_rectangle(x - bar_w / 2, base_y, x + bar_w / 2, base_y,
                                               fill=color, outline="")
            bars.append((rect, x - bar_w / 2, x + bar_w / 2, y))
            self.chart.create_text(x, base_y + 12, text=f"{acc * 100:.0f}", fill=FG, font=font(8))

        steps = 12

        def animate(k: int) -> None:
            if gen != self._chart_gen:
                return
            ratio = k / steps
            for rect, x1, x2, target_y in bars:
                y = base_y - (base_y - target_y) * ratio
                self.chart.coords(rect, x1, y, x2, base_y)
            if k < steps:
                self.chart.after(18, animate, k + 1)
            else:
                for i in range(1, len(points)):
                    self.chart.create_line(points[i - 1][0], points[i - 1][1],
                                           points[i][0], points[i][1], fill=FG, width=2)
                for x, y in points:
                    self.chart.create_oval(x - 3, y - 3, x + 3, y + 3, fill=FG, outline="")

        animate(0)
