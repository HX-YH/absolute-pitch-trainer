# -*- coding: utf-8 -*-
"""错题本：查看错题、弱项分析、一键重练错题。"""
from __future__ import annotations

import tkinter as tk

from ..theme import BG, FG, CARD, GRAY, BORDER
from ..widgets import FlatButton, PillButton, font
from ...music import MODE_LABELS, pc_name, SHARP_NAMES
from ...wrongbook import question_key


class WrongBookPage(tk.Frame):
    def __init__(self, app):
        super().__init__(app.container, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        FlatButton(top, text="‹ 返回", command=lambda: self.app.show_page("home"),
                   bg=BG, fg=GRAY, hover_bg="#1c1c1e", font_size=14).pack(side="left")
        tk.Label(top, text="错题本", bg=BG, fg=FG, font=font(24, True)).pack(side="left", padx=20)

        # 弱项摘要
        self.summary_label = tk.Label(self, text="", bg=BG, fg=GRAY, font=font(12), justify="left")
        self.summary_label.pack(pady=(14, 4))

        # 列表
        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=80, pady=(6, 10))
        self.listbox = tk.Listbox(list_frame, bg=CARD, fg=FG, selectbackground=FG,
                                  selectforeground=BG, relief="flat", highlightthickness=1,
                                  highlightbackground=BORDER, font=font(12), height=14)
        scroll = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview,
                              bg=BG, troughcolor=BG, activebackground=GRAY)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # 操作
        row = tk.Frame(self, bg=BG)
        row.pack(pady=(0, 20))
        PillButton(row, text="重练错题", command=self._practice,
                   width=180, height=48, font_size=14, bold=True).pack(side="left", padx=8)
        PillButton(row, text="清空错题", command=self._clear,
                   width=140, height=48, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                   font_size=13).pack(side="left", padx=8)

    def on_show(self, **kwargs):
        self._refresh()

    def _refresh(self):
        questions = self.app.wrongbook.questions()
        self.listbox.delete(0, "end")
        if not questions:
            self.listbox.insert("end", "暂无错题，继续保持！")
            self.summary_label.config(text="错题数：0")
            return

        for q in questions:
            entry = self.app.wrongbook.data.get(question_key(q), {})
            count = entry.get("wrong_count", 1)
            mode = MODE_LABELS.get(q.get("mode"), q.get("mode", ""))
            self.listbox.insert("end", f"[{mode}] {q.get('answer_name', '')}    错 {count} 次")

        # 弱项摘要
        weak_notes = self.app.wrongbook.weak_notes(5)
        weak_chords = self.app.wrongbook.weak_chord_qualities(5)
        parts = [f"错题数：{len(questions)}"]
        if weak_notes:
            note_str = "、".join(f"{SHARP_NAMES[pc]}" for pc, _ in weak_notes)
            parts.append(f"薄弱音：{note_str}")
        if weak_chords:
            chord_str = "、".join(f"{q}" for q, _ in weak_chords)
            parts.append(f"薄弱和弦：{chord_str}")
        self.summary_label.config(text="    ".join(parts))

    def _practice(self):
        questions = self.app.wrongbook.questions()
        if not questions:
            self.app.show_modal("提示", "当前没有错题")
            return
        qtypes = {q.get("type") for q in questions}
        if qtypes == {"note"}:
            mode = "easy"
        elif qtypes == {"chord"}:
            mode = "hard"
        elif qtypes == {"interval"}:
            mode = "interval"
        elif qtypes == {"melody"}:
            mode = "melody"
        else:
            # 混合题型：用第一个题目的类型对应的模式，训练页会按每题类型切换输入
            first_type = questions[0].get("type", "note")
            mode = {"note": "easy", "chord": "hard", "interval": "interval", "melody": "melody"}.get(first_type, "easy")
        self.app.start_training(mode, "all", len(questions), questions=questions)

    def _clear(self):
        self.app.wrongbook.clear()
        self._refresh()
