# -*- coding: utf-8 -*-
"""主页：模式选择、轮数、高级设置、错题本入口。"""
from __future__ import annotations

import tkinter as tk

from ..theme import BG, FG, CARD, CARD_ACTIVE, CARD_ACTIVE_FG, BORDER, GRAY, SUBTLE
from ..widgets import PillButton, FlatButton, SegmentedControl, font, animate_fg
from ... import audio
from ...music import MODE_LABELS, CATEGORY_LABELS, SHARP_NAMES, pc_name

MODE_INFO = {
    "easy": ("简单", "单音 · 无升降号 · 标准音 A"),
    "normal": ("普通", "单音 · 全部音 · 标准音 A"),
    "hard": ("困难", "和弦 · 自然音 · 标准音 A"),
    "hell": ("地狱", "和弦 · 全半音 · 无标准音"),
    "hell_note": ("地狱单音", "单音 · 全部音 · 无标准音"),
    "interval": ("音程", "听两音 · 判断音程"),
    "melody": ("旋律", "听短旋律 · 写出音高"),
}

KEY_OPTIONS = [(str(i), SHARP_NAMES[i]) for i in range(12)]


class ModeCard(tk.Frame):
    def __init__(self, master, key: str, title: str, desc: str, on_click):
        super().__init__(master, bg=CARD, highlightbackground=BORDER, highlightthickness=1, cursor="hand2")
        self.key = key
        self.title = title
        self.desc = desc
        self.on_click = on_click
        self.selected = False
        self._title_label = tk.Label(self, text=title, bg=CARD, fg=FG, font=font(15, True))
        self._desc_label = tk.Label(self, text=desc, bg=CARD, fg=GRAY, font=font(9), wraplength=150, justify="center")
        self._title_label.pack(fill="x", padx=8, pady=(14, 3))
        self._desc_label.pack(fill="x", padx=8, pady=(0, 14))
        self.bind("<Button-1>", self._clicked)
        for w in (self, self._title_label, self._desc_label):
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)
            w.bind("<Button-1>", self._clicked)

    def _enter(self, _e):
        if not self.selected:
            self.configure(bg="#1c1c1e", highlightbackground=FG)
            self._title_label.configure(bg="#1c1c1e")
            self._desc_label.configure(bg="#1c1c1e")

    def _leave(self, _e):
        if not self.selected:
            self.configure(bg=CARD, highlightbackground=BORDER)
            self._title_label.configure(bg=CARD)
            self._desc_label.configure(bg=CARD)

    def _clicked(self, _e):
        self.on_click(self.key)

    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.configure(bg=CARD_ACTIVE, highlightbackground=CARD_ACTIVE)
            self._title_label.configure(bg=CARD_ACTIVE, fg=CARD_ACTIVE_FG)
            self._desc_label.configure(bg=CARD_ACTIVE, fg="#3a3a3c")
        else:
            self.configure(bg=CARD, highlightbackground=BORDER)
            self._title_label.configure(bg=CARD, fg=FG)
            self._desc_label.configure(bg=CARD, fg=GRAY)


class HomePage(tk.Frame):
    def __init__(self, app):
        super().__init__(app.container, bg=BG)
        self.app = app
        self.mode_cards: dict[str, ModeCard] = {}
        self._build()

    def _build(self):
        self.title_label = tk.Label(self, text="绝对音准训练", bg=BG, fg=FG, font=font(32, True))
        self.title_label.pack(pady=(24, 2))
        self.sub_label = tk.Label(self, text="训练你的耳朵 · 听见每一个音高", bg=BG, fg=GRAY, font=font(13))
        self.sub_label.pack(pady=(0, 18))

        # 模式卡片（两行，每行 4 个，等宽）
        card_row = tk.Frame(self, bg=BG)
        card_row.pack(padx=40, fill="x")
        for c in range(4):
            card_row.grid_columnconfigure(c, weight=1, uniform="mode")
        for idx, (key, (title_text, desc)) in enumerate(MODE_INFO.items()):
            card = ModeCard(card_row, key, title_text, desc, self._select_mode)
            card.grid(row=idx // 4, column=idx % 4, padx=6, pady=5, sticky="nsew")
            self.mode_cards[key] = card

        # 分隔线
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=60, pady=(14, 0))

        # 和弦类型（困难/地狱）
        self.category_frame = tk.Frame(self, bg=BG)
        tk.Label(self.category_frame, text="和弦类型", bg=BG, fg=GRAY, font=font(11)).pack(pady=(10, 4))
        self.category = SegmentedControl(
            self.category_frame,
            [(k, CATEGORY_LABELS[k]) for k in ("triad", "power", "seventh", "all")],
            selected=self.app.config.get("chord_category"),
            on_select=lambda k: self.app.config.set("chord_category", k),
            bg=BG,
        )
        self.category.pack()

        # 轮数
        rounds_frame = tk.Frame(self, bg=BG)
        rounds_frame.pack(pady=(12, 4))
        tk.Label(rounds_frame, text="训练轮数", bg=BG, fg=GRAY, font=font(11)).pack(side="left", padx=(0, 10))
        self.rounds = SegmentedControl(
            rounds_frame,
            [("5", "5 轮"), ("10", "10 轮"), ("20", "20 轮")],
            selected=str(self.app.config.get("rounds")),
            on_select=lambda v: self.app.config.set("rounds", int(v)),
            bg=BG,
        )
        self.rounds.pack(side="left")

        # 高级设置折叠
        self.settings_btn = FlatButton(self, text="⚙ 高级设置", command=self._toggle_settings,
                                       bg=CARD, fg=GRAY, hover_bg="#1c1c1e", font_size=12)
        self.settings_btn.pack(pady=(10, 0))
        self.settings_frame = tk.Frame(self, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        self._build_settings()

        # 操作按钮
        action_row = tk.Frame(self, bg=BG)
        action_row.pack(pady=(12, 0))
        PillButton(action_row, text="进入训练", command=self._start,
                   width=200, height=50, font_size=16, bold=True).pack(side="left", padx=8)
        PillButton(action_row, text="历史成绩", command=lambda: self.app.show_page("history"),
                   width=150, height=50, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                   font_size=14).pack(side="left", padx=8)
        PillButton(action_row, text="错题本", command=lambda: self.app.show_page("wrongbook"),
                   width=130, height=50, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                   font_size=14).pack(side="left", padx=8)

        self._select_mode(self.app.config.get("mode"), save=False)
        self._refresh_toggles()

    # ------------------------------------------------------------ 设置面板

    def _build_settings(self):
        grid = tk.Frame(self.settings_frame, bg=BG)
        grid.pack(padx=30, pady=8)

        # 标准音频率
        tk.Label(grid, text="标准音", bg=BG, fg=GRAY, font=font(11)).grid(row=0, column=0, sticky="e", padx=6, pady=3)
        self.freq = SegmentedControl(
            grid, [("438", "438"), ("440", "440"), ("442", "442"), ("443", "443")],
            selected=str(int(self.app.config.get("a4_freq"))),
            on_select=lambda v: (self.app.config.set("a4_freq", float(v)), audio.configure_playback(volume=self.app.config.get("volume"), timbre=self.app.config.get("timbre"), a4_freq=float(v))),
            bg=BG,
        )
        self.freq.grid(row=0, column=1, columnspan=2, sticky="w", pady=3)

        # 调性
        tk.Label(grid, text="调性", bg=BG, fg=GRAY, font=font(11)).grid(row=1, column=0, sticky="e", padx=6, pady=3)
        self.key_var = tk.StringVar(value=SHARP_NAMES[int(self.app.config.get("key"))])
        key_menu = tk.OptionMenu(grid, self.key_var, *SHARP_NAMES, command=self._set_key)
        key_menu.configure(bg=BG, fg=FG, activebackground=BG, activeforeground=FG, relief="flat",
                           highlightthickness=0, font=font(11), bd=0)
        key_menu["menu"].configure(bg=CARD, fg=FG, bd=0)
        key_menu.grid(row=1, column=1, sticky="w", pady=3)

        # 单音范围
        tk.Label(grid, text="单音范围", bg=BG, fg=GRAY, font=font(11)).grid(row=2, column=0, sticky="e", padx=6, pady=3)
        range_row = tk.Frame(grid, bg=BG)
        range_row.grid(row=2, column=1, columnspan=2, sticky="w", pady=3)
        self.note_low_var = tk.StringVar(value=str(self.app.config.get("note_low") // 12 - 1))
        self.note_high_var = tk.StringVar(value=str(self.app.config.get("note_high") // 12 - 1))
        tk.OptionMenu(range_row, self.note_low_var, "3", "4", "5", "6", command=self._set_note_range).configure(
            bg=BG, fg=FG, activebackground=BG, activeforeground=FG, relief="flat", highlightthickness=0, font=font(10), bd=0)
        tk.Label(range_row, text="—", bg=BG, fg=GRAY, font=font(10)).pack(side="left", padx=4)
        tk.OptionMenu(range_row, self.note_high_var, "3", "4", "5", "6", command=self._set_note_range).configure(
            bg=BG, fg=FG, activebackground=BG, activeforeground=FG, relief="flat", highlightthickness=0, font=font(10), bd=0)

        # 和弦范围
        tk.Label(grid, text="和弦根音范围", bg=BG, fg=GRAY, font=font(11)).grid(row=3, column=0, sticky="e", padx=6, pady=3)
        chord_range_row = tk.Frame(grid, bg=BG)
        chord_range_row.grid(row=3, column=1, columnspan=2, sticky="w", pady=3)
        self.chord_low_var = tk.StringVar(value=str(self.app.config.get("chord_low") // 12 - 1))
        self.chord_high_var = tk.StringVar(value=str(self.app.config.get("chord_high") // 12 - 1))
        tk.OptionMenu(chord_range_row, self.chord_low_var, "3", "4", "5", command=self._set_chord_range).configure(
            bg=BG, fg=FG, activebackground=BG, activeforeground=FG, relief="flat", highlightthickness=0, font=font(10), bd=0)
        tk.Label(chord_range_row, text="—", bg=BG, fg=GRAY, font=font(10)).pack(side="left", padx=4)
        tk.OptionMenu(chord_range_row, self.chord_high_var, "3", "4", "5", command=self._set_chord_range).configure(
            bg=BG, fg=FG, activebackground=BG, activeforeground=FG, relief="flat", highlightthickness=0, font=font(10), bd=0)

        # 音量
        tk.Label(grid, text="音量", bg=BG, fg=GRAY, font=font(11)).grid(row=4, column=0, sticky="e", padx=6, pady=3)
        self.volume_scale = tk.Scale(grid, from_=5, to=100, orient="horizontal", bg=BG, fg=FG,
                                     troughcolor=CARD, highlightthickness=0, bd=0, font=font(9),
                                     command=self._set_volume, length=180)
        self.volume_scale.set(int(float(self.app.config.get("volume")) * 100))
        self.volume_scale.grid(row=4, column=1, columnspan=2, sticky="w", pady=3)

        # 音色
        tk.Label(grid, text="音色", bg=BG, fg=GRAY, font=font(11)).grid(row=5, column=0, sticky="e", padx=6, pady=3)
        self.timbre = SegmentedControl(
            grid, [("sine", "正弦"), ("piano", "钢琴"), ("soft", "柔和")],
            selected=self.app.config.get("timbre"),
            on_select=lambda v: (self.app.config.set("timbre", v), audio.configure_playback(volume=self.app.config.get("volume"), timbre=v, a4_freq=self.app.config.get("a4_freq"))),
            bg=BG,
        )
        self.timbre.grid(row=5, column=1, columnspan=2, sticky="w", pady=3)

        # 开关组
        toggles = tk.Frame(self.settings_frame, bg=BG)
        toggles.pack(pady=(0, 10))
        self.ignore_btn = FlatButton(toggles, text="忽略八度", command=self._toggle_ignore,
                                     bg=CARD, fg=GRAY, hover_bg="#1c1c1e", font_size=10, padx=10, pady=5)
        self.ignore_btn.pack(side="left", padx=4)
        self.inversion_btn = FlatButton(toggles, text="随机转位", command=self._toggle_inversion,
                                        bg=CARD, fg=GRAY, hover_bg="#1c1c1e", font_size=10, padx=10, pady=5)
        self.inversion_btn.pack(side="left", padx=4)
        self.progressive_btn = FlatButton(toggles, text="渐进难度", command=self._toggle_progressive,
                                          bg=CARD, fg=GRAY, hover_bg="#1c1c1e", font_size=10, padx=10, pady=5)
        self.progressive_btn.pack(side="left", padx=4)
        self.strict_btn = FlatButton(toggles, text="严格模式", command=self._toggle_strict,
                                     bg=CARD, fg=GRAY, hover_bg="#1c1c1e", font_size=10, padx=10, pady=5)
        self.strict_btn.pack(side="left", padx=4)

    # ------------------------------------------------------------ 生命周期

    def on_show(self, **kwargs):
        self._select_mode(self.app.config.get("mode"), save=False)
        self._refresh_toggles()
        # 标题轻微淡入，增加高级感
        self.title_label.config(fg=GRAY)
        self.sub_label.config(fg=SUBTLE)
        animate_fg(self.title_label, FG, duration=300)
        animate_fg(self.sub_label, GRAY, duration=300)

    def _toggle_settings(self):
        if self.settings_frame.winfo_ismapped():
            self.settings_frame.pack_forget()
            self.settings_btn.config(text="⚙ 高级设置")
        else:
            self.settings_frame.pack(padx=60, pady=(10, 0), fill="x")
            self.settings_btn.config(text="⚙ 收起设置")

    # ------------------------------------------------------------ 设置回调

    def _set_key(self, value: str):
        key = SHARP_NAMES.index(value)
        self.app.config.set("key", key)

    def _set_note_range(self, _v=None):
        low = int(self.note_low_var.get())
        high = int(self.note_high_var.get())
        if low > high:
            low, high = high, low
            self.note_low_var.set(str(low))
            self.note_high_var.set(str(high))
        self.app.config.set("note_low", (low + 1) * 12)
        self.app.config.set("note_high", (high + 1) * 12)

    def _set_chord_range(self, _v=None):
        low = int(self.chord_low_var.get())
        high = int(self.chord_high_var.get())
        if low > high:
            low, high = high, low
            self.chord_low_var.set(str(low))
            self.chord_high_var.set(str(high))
        self.app.config.set("chord_low", (low + 1) * 12)
        self.app.config.set("chord_high", (high + 1) * 12)

    def _set_volume(self, value: str):
        vol = int(float(value)) / 100.0
        self.app.config.set("volume", vol)
        audio.configure_playback(volume=vol, timbre=self.app.config.get("timbre"), a4_freq=self.app.config.get("a4_freq"))

    def _toggle_ignore(self):
        cur = self.app.config.get("ignore_octave")
        self.app.config.set("ignore_octave", not cur)
        self._refresh_toggles()

    def _toggle_inversion(self):
        cur = self.app.config.get("random_inversions")
        self.app.config.set("random_inversions", not cur)
        self._refresh_toggles()

    def _toggle_progressive(self):
        cur = self.app.config.get("progressive")
        self.app.config.set("progressive", not cur)
        self._refresh_toggles()

    def _toggle_strict(self):
        cur = self.app.config.get("strict_mode")
        self.app.config.set("strict_mode", not cur)
        self._refresh_toggles()

    # ------------------------------------------------------------ 状态刷新

    def _select_mode(self, key: str, save: bool = True):
        for k, card in self.mode_cards.items():
            card.set_selected(k == key)
        if save:
            self.app.config.set("mode", key)
        if key in ("hard", "hell"):
            self.category_frame.pack()
        else:
            self.category_frame.pack_forget()
        self._refresh_toggles()

    def _refresh_toggles(self):
        def style(btn, on, enabled=True):
            btn.set_style(
                bg=FG if (on and enabled) else CARD,
                fg=BG if (on and enabled) else GRAY,
                hover_bg=FG if (on and enabled) else "#1c1c1e",
                active_bg=BG if (on and enabled) else FG,
                active_fg=FG if (on and enabled) else BG,
            )
            btn.config(state="normal" if enabled else "disabled")

        style(self.ignore_btn, self.app.config.get("ignore_octave"))
        mode = self.app.config.get("mode")
        chord_mode = mode in ("hard", "hell")
        style(self.inversion_btn, self.app.config.get("random_inversions"), chord_mode)
        style(self.progressive_btn, self.app.config.get("progressive"))
        style(self.strict_btn, self.app.config.get("strict_mode"))

    # ------------------------------------------------------------ 开始训练

    def _start(self):
        mode = self.app.config.get("mode")
        if mode in ("hard", "hell"):
            category = self.app.config.get("chord_category")
        else:
            category = "all"
        rounds = int(self.app.config.get("rounds"))
        self.app.start_training(mode, category, rounds)
