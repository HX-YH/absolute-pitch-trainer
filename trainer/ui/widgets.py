# -*- coding: utf-8 -*-
"""Tkinter 通用控件与轻量动画。"""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from .theme import BG, CARD, FG, BORDER, GRAY, SUCCESS, ERROR

FONT_FAMILY = "Segoe UI"


def font(size: int, bold: bool = False) -> tuple:
    return (FONT_FAMILY, size, "bold" if bold else "normal")


class PillButton(tk.Canvas):
    """圆角按钮，支持 hover 颜色切换。"""

    def __init__(self, master, text: str, command: Optional[Callable] = None,
                 width: int = 180, height: int = 44, bg: str = BG, fg: str = FG,
                 active_bg: str = FG, active_fg: str = BG,
                 radius: int = 22, font_size: int = 13, bold: bool = False):
        super().__init__(master, width=width, height=height, bg=master.cget("bg"),
                         highlightthickness=0, cursor="hand2")
        self._text = text
        self._command = command
        self._bg = bg
        self._fg = fg
        self._active_bg = active_bg
        self._active_fg = active_fg
        self._radius = radius
        self._font = font(font_size, bold)
        self._enabled = True
        self._hover = False
        self._pressed = False
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Button-1>", self._on_click)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self) -> None:
        self.delete("all")
        w = int(self.cget("width"))
        h = int(self.cget("height"))
        active = self._hover or self._pressed
        fill = self._active_bg if active else self._bg
        outline = self._active_bg if active else BORDER
        fg = self._active_fg if active else self._fg
        self._rounded_rect(1, 1, w - 2, h - 2, self._radius, fill=fill, outline=outline, width=1)
        self.create_text(w / 2, h / 2, text=self._text, fill=fg, font=self._font)

    def set_text(self, text: str) -> None:
        self._text = text
        self._draw()

    def set_command(self, command: Optional[Callable]) -> None:
        self._command = command

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def _on_enter(self, _event) -> None:
        if self._enabled:
            self._hover = True
            self._draw()

    def _on_leave(self, _event) -> None:
        self._hover = False
        self._draw()

    def _on_click(self, _event) -> None:
        if self._enabled and self._command:
            self._command()

    def _on_press(self, _event) -> None:
        if self._enabled:
            self._pressed = True
            self._draw()

    def _on_release(self, _event) -> None:
        self._pressed = False
        self._draw()


class FlatButton(tk.Button):
    """极简扁平按钮，带悬停反馈。"""

    def __init__(self, master, text: str, command: Optional[Callable] = None,
                 bg: str = CARD, fg: str = FG, hover_bg: str = "#1c1c1e",
                 active_bg: str = FG, active_fg: str = BG,
                 font_size: int = 13, bold: bool = False, padx: int = 18, pady: int = 10):
        super().__init__(master, text=text, command=command, bg=bg, fg=fg,
                         activebackground=active_bg, activeforeground=active_fg,
                         relief="flat", bd=0, highlightthickness=0,
                         font=font(font_size, bold), padx=padx, pady=pady,
                         cursor="hand2", borderwidth=0)
        self._hover_bg = hover_bg
        self._bg = bg
        self._fg = fg
        self._active_bg = active_bg
        self._active_fg = active_fg
        self.bind("<Enter>", lambda _e: self.config(bg=self._hover_bg))
        self.bind("<Leave>", lambda _e: self.config(bg=self._bg))

    def set_style(self, bg=None, fg=None, hover_bg=None, active_bg=None, active_fg=None):
        if bg is not None:
            self._bg = bg
            self.config(bg=bg)
        if fg is not None:
            self._fg = fg
            self.config(fg=fg)
        if hover_bg is not None:
            self._hover_bg = hover_bg
        if active_bg is not None:
            self._active_bg = active_bg
            self.config(activebackground=active_bg)
        if active_fg is not None:
            self._active_fg = active_fg
            self.config(activeforeground=active_fg)


class SegmentedControl(tk.Frame):
    """分段选择器：一组选项，选中项白底黑字。"""

    def __init__(self, master, options: list[tuple[str, str]], selected: str,
                 on_select: Optional[Callable[[str], None]] = None,
                 bg: str = CARD):
        super().__init__(master, bg=bg)
        self._on_select = on_select
        self._buttons: dict[str, FlatButton] = {}
        for i, (key, label) in enumerate(options):
            btn = FlatButton(
                self, text=label, command=lambda k=key: self.select(k),
                bg=bg, fg=GRAY, hover_bg="#1c1c1e",
                active_bg=FG, active_fg=BG, font_size=12, bold=False,
                padx=16, pady=6,
            )
            btn.grid(row=0, column=i, padx=2)
            self._buttons[key] = btn
        self.select(selected, notify=False)

    def select(self, key: str, notify: bool = True) -> None:
        for k, btn in self._buttons.items():
            if k == key:
                btn.set_style(bg=FG, fg=BG, hover_bg=FG, active_bg=BG, active_fg=FG)
            else:
                btn.set_style(bg=CARD, fg=GRAY, hover_bg="#1c1c1e", active_bg=FG, active_fg=BG)
        if notify and self._on_select:
            self._on_select(key)

    def value(self) -> str:
        for k, btn in self._buttons.items():
            if btn.cget("bg") == FG:
                return k
        return ""


def animate_number(label: tk.Label, target: float, duration: int = 800,
                   suffix: str = "%", decimals: int = 0) -> None:
    """数字滚动动画。"""
    start = 0.0
    steps = max(1, duration // 30)
    delta = target / steps

    def tick(i: int) -> None:
        if i >= steps:
            label.config(text=f"{target:.{decimals}f}{suffix}")
            return
        value = start + delta * i
        label.config(text=f"{value:.{decimals}f}{suffix}")
        label.after(30, tick, i + 1)

    tick(0)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def animate_fg(label: tk.Label, target: str, duration: int = 260, steps: int = 8) -> None:
    """前景色渐变，用于正确/错误反馈的高级感动画。"""
    try:
        start_rgb = _hex_to_rgb(label.cget("fg"))
        end_rgb = _hex_to_rgb(target)
    except Exception:
        label.config(fg=target)
        return
    delay = max(16, duration // steps)

    def tick(i: int) -> None:
        if i >= steps:
            label.config(fg=target)
            return
        ratio = i / steps
        rgb = tuple(int(s + (e - s) * ratio) for s, e in zip(start_rgb, end_rgb))
        label.config(fg=_rgb_to_hex(rgb))
        label.after(delay, tick, i + 1)

    tick(0)


class ProgressBar(tk.Canvas):
    """极简圆角进度条，带平滑增长动画。"""

    def __init__(self, master, width: int = 420, height: int = 6,
                 bg: str = BG, fg: str = FG, track: str = BORDER):
        super().__init__(master, width=width, height=height, bg=master.cget("bg"),
                         highlightthickness=0)
        self._bar_w = width
        self._bar_h = height
        self._fg = fg
        self._track = track
        self._value = 0.0
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        r = self._bar_h / 2
        self.create_oval(0, 0, self._bar_h, self._bar_h, fill=self._track, outline="")
        self.create_oval(self._bar_w - self._bar_h, 0, self._bar_w, self._bar_h, fill=self._track, outline="")
        self.create_rectangle(r, 0, self._bar_w - r, self._bar_h, fill=self._track, outline="")
        fill_w = max(0, self._bar_w * self._value)
        if fill_w > 0:
            fg_r = min(r, fill_w / 2)
            self.create_oval(0, 0, self._bar_h, self._bar_h, fill=self._fg, outline="")
            if fill_w >= self._bar_w:
                self.create_oval(self._bar_w - self._bar_h, 0, self._bar_w, self._bar_h,
                                 fill=self._fg, outline="")
            self.create_rectangle(fg_r, 0, min(self._bar_w - fg_r, fill_w), self._bar_h,
                                  fill=self._fg, outline="")

    def set(self, value: float, animate: bool = True) -> None:
        value = max(0.0, min(1.0, float(value)))
        if not animate:
            self._value = value
            self._draw()
            return
        start = self._value
        steps = 14
        delay = 18

        def tick(i: int) -> None:
            if i >= steps:
                self._value = value
                self._draw()
                return
            self._value = start + (value - start) * i / steps
            self._draw()
            self.after(delay, tick, i + 1)

        tick(0)
