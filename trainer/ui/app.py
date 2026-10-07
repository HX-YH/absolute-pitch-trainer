# -*- coding: utf-8 -*-
"""应用主窗口与页面调度。"""
from __future__ import annotations

import threading
import tkinter as tk

from .theme import BG, FG, CARD, BORDER, GRAY
from .widgets import PillButton, FlatButton, font
from ..config import Config
from ..history import History
from ..wrongbook import WrongBook
from .. import audio


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("绝对音准训练")
        self.root.geometry("1120x780")
        self.root.minsize(980, 680)
        self.root.configure(bg=BG)

        self.config = Config()
        self.history = History()
        self.wrongbook = WrongBook()
        audio.configure_playback(volume=self.config.get("volume"), timbre=self.config.get("timbre"),
                                 a4_freq=self.config.get("a4_freq"))

        self.container = tk.Frame(self.root, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.pages: dict[str, tk.Frame] = {}
        self.current: tk.Frame | None = None
        self._slide_after_id: str | None = None

        self._init_pages()
        self.show_page("home")

    # ------------------------------------------------------------ 页面管理

    def _init_pages(self):
        from .pages.home import HomePage
        from .pages.training import TrainingPage
        from .pages.results import ResultsPage
        from .pages.history_page import HistoryPage
        from .pages.wrongbook_page import WrongBookPage
        self.pages["home"] = HomePage(self)
        self.pages["training"] = TrainingPage(self)
        self.pages["results"] = ResultsPage(self)
        self.pages["history"] = HistoryPage(self)
        self.pages["wrongbook"] = WrongBookPage(self)

    def show_page(self, name: str, **kwargs):
        page = self.pages.get(name)
        if page is None:
            return
        if hasattr(page, "on_show"):
            page.on_show(**kwargs)
        if self.current is page:
            return
        old = self.current
        self.current = page
        if old is not None and old is not page and hasattr(old, "on_hide"):
            old.on_hide()
        # 新页从右侧滑入
        page.place(in_=self.container, x=70, y=0, relwidth=1, relheight=1)
        page.lift()
        self._slide(page, from_x=70, to_x=0, duration=240, old=old)

    def _slide(self, page, from_x: int, to_x: int, duration: int, old=None):
        steps = 12
        delay = max(10, duration // steps)

        def step(i: int):
            x = from_x + (to_x - from_x) * i / steps
            page.place(x=int(x), y=0, relwidth=1, relheight=1)
            page.lift()
            if i < steps:
                self.root.after(delay, step, i + 1)
            else:
                if old is not None and old is not page:
                    try:
                        old.place_forget()
                    except Exception:
                        pass

        step(0)

    # ------------------------------------------------------------ 训练流程

    def start_training(self, mode: str, category: str, rounds: int, questions=None):
        self.show_page("training", mode=mode, category=category, rounds=rounds, questions=questions)

    def finish_training(self, mode: str, rounds: int, correct: int, details: list | None = None):
        self.history.add(mode, rounds, correct, rounds, details=details)
        self.show_page("results", mode=mode, rounds=rounds, correct=correct)

    # ------------------------------------------------------------ 语音

    def speak_async(self, text: str, lang: str = "zh"):
        threading.Thread(target=audio.speak, args=(text, lang), daemon=True).start()

    # ------------------------------------------------------------ 模态弹窗

    def show_modal(self, title: str, message: str, buttons: list[tuple[str, callable]] | None = None):
        modal = tk.Toplevel(self.root)
        modal.overrideredirect(True)
        modal.configure(bg=BG)
        modal.attributes("-topmost", True)
        modal.attributes("-alpha", 0.0)

        width, height = 440, 230
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        card = tk.Frame(modal, bg=CARD, highlightbackground=FG, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=2, pady=2)
        tk.Label(card, text=title, bg=CARD, fg=FG, font=font(18, True)).pack(pady=(28, 8))
        tk.Label(card, text=message, bg=CARD, fg=GRAY, font=font(12), wraplength=340,
                 justify="center").pack(pady=(0, 18), padx=20)

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(pady=(0, 24))
        for label, cb in (buttons or [("好的", lambda: None)]):
            btn = PillButton(btn_row, text=label, command=lambda m=modal, c=cb: (m.destroy(), c()),
                             width=120, height=40, font_size=13)
            btn.pack(side="left", padx=6)

        modal.grab_set()

        def geometry_for(scale: float) -> str:
            w = int(width * scale)
            h = int(height * scale)
            x = (screen_w - w) // 2
            y = (screen_h - h) // 2
            return f"{w}x{h}+{x}+{y}"

        modal.geometry(geometry_for(0.90))
        modal.attributes("-alpha", 0.0)

        def fade(i: int) -> None:
            steps = 14
            if i > steps:
                modal.geometry(geometry_for(1.0))
                modal.attributes("-alpha", 1.0)
                return
            ratio = i / steps
            scale = 0.90 + 0.10 * ratio
            modal.geometry(geometry_for(scale))
            modal.attributes("-alpha", 0.15 + 0.85 * ratio)
            modal.after(14, fade, i + 1)

        fade(0)

    def run(self):
        self.root.mainloop()
