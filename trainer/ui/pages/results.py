# -*- coding: utf-8 -*-
"""结果页：本轮成绩展示与动画。"""
from __future__ import annotations

import tkinter as tk

from ..theme import BG, FG, CARD, GRAY, BORDER, SUCCESS, ERROR, SUBTLE
from ..widgets import PillButton, FlatButton, animate_number, ProgressBar, font
from ...music import MODE_LABELS


class ResultsPage(tk.Frame):
    def __init__(self, app):
        super().__init__(app.container, bg=BG)
        self.app = app
        self.mode = "easy"
        self.rounds = 5
        self.correct = 0
        self.total = 5
        self._build()

    def _build(self):
        tk.Label(self, text="训练完成", bg=BG, fg=FG, font=font(32, True)).pack(pady=(60, 6))
        self.mode_label = tk.Label(self, text="简单模式", bg=BG, fg=GRAY, font=font(14))
        self.mode_label.pack()

        self.score_label = tk.Label(self, text="", bg=BG, fg=FG, font=font(52, True))
        self.score_label.pack(pady=(30, 0))

        self.percent_label = tk.Label(self, text="0%", bg=BG, fg=FG, font=font(28, True))
        self.percent_label.pack(pady=(4, 10))

        self.result_bar = ProgressBar(self, width=440, height=7, fg=FG, track=BORDER)
        self.result_bar.pack(pady=(0, 24))

        stats = tk.Frame(self, bg=BG)
        stats.pack(pady=(0, 36))
        self.correct_label = tk.Label(stats, text="答对 0", bg=BG, fg=SUCCESS, font=font(14))
        self.correct_label.pack(side="left", padx=20)
        self.wrong_label = tk.Label(stats, text="答错 0", bg=BG, fg=ERROR, font=font(14))
        self.wrong_label.pack(side="left", padx=20)

        row = tk.Frame(self, bg=BG)
        row.pack()
        PillButton(row, text="再练一次", command=self._retry, width=180, height=52,
                   font_size=15, bold=True).pack(side="left", padx=8)
        PillButton(row, text="查看历史", command=lambda: self.app.show_page("history"),
                   width=160, height=52, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                   font_size=14).pack(side="left", padx=8)
        PillButton(row, text="返回主页", command=lambda: self.app.show_page("home"),
                   width=160, height=52, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                   font_size=14).pack(side="left", padx=8)

    def on_show(self, mode: str, rounds: int, correct: int, **kwargs):
        self.mode = mode
        self.rounds = rounds
        self.correct = correct
        self.total = rounds
        self.mode_label.config(text=MODE_LABELS[mode] + "模式")
        self.score_label.config(text=f"{correct}/{rounds}")
        percent = correct / rounds * 100.0
        self.correct_label.config(text=f"答对 {correct}")
        self.wrong_label.config(text=f"答错 {rounds - correct}")
        self.percent_label.config(text="0%")
        self.result_bar.set(0, animate=False)
        self.result_bar.set(percent / 100.0)
        animate_number(self.percent_label, percent, duration=900, suffix="%", decimals=0)

    def _retry(self):
        category = self.app.config.get("chord_category") if self.mode in ("hard", "hell") else "all"
        self.app.start_training(self.mode, category, self.rounds)
