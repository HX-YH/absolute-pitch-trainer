# -*- coding: utf-8 -*-
"""训练页：播放、作答、语音输入、反馈。"""
from __future__ import annotations

import threading

import tkinter as tk

from ..theme import BG, FG, CARD, CARD_ACTIVE, CARD_ACTIVE_FG, BORDER, GRAY, SUBTLE, SUCCESS, ERROR
from ..widgets import PillButton, FlatButton, SegmentedControl, ProgressBar, font, animate_fg
from ... import audio, music

NOTE_LABELS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
OCTAVE_LABELS = ["3", "4", "5", "6"]


class TrainingPage(tk.Frame):
    def __init__(self, app):
        super().__init__(app.container, bg=BG)
        self.app = app
        self.mode = "easy"
        self.category = "all"
        self.rounds = 5
        self.questions = []
        self.index = 0
        self.correct_count = 0
        self.answered = False
        self.recording = False
        self.voice_enabled = True
        self._after_ids: list[str] = []
        self._stop_event = None
        self._submitted_play_midis: list[int] | None = None
        self._details: list[dict] = []
        self._from_wrongbook = False
        self._key_funcid = None
        self._note_pc = 0
        self._octave = 4
        self._build()

    # ------------------------------------------------------------ UI 构建

    def _build(self):
        # 顶栏
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        FlatButton(top, text="‹ 返回", command=self._quit, bg=BG, fg=GRAY,
                   hover_bg="#1c1c1e", font_size=14).pack(side="left")
        self.title_label = tk.Label(top, text="简单模式", bg=BG, fg=FG, font=font(20, True))
        self.title_label.pack(side="left", padx=20)
        self.progress_label = tk.Label(top, text="第 1/5 题", bg=BG, fg=GRAY, font=font(13))
        self.progress_label.pack(side="right")
        self.voice_toggle_btn = FlatButton(top, text="🔊 语音播报", command=self._toggle_voice,
                                           bg=BG, fg=GRAY, hover_bg="#1c1c1e", font_size=12)
        self.voice_toggle_btn.pack(side="right", padx=10)

        # 轮次进度条
        self.progress_bar = ProgressBar(self, width=560, height=5, fg=FG, track=BORDER)
        self.progress_bar.pack(pady=(14, 0))

        # 标准音 A 与播放区
        self.standard_frame = tk.Frame(self, bg=BG)
        self.standard_frame.pack(pady=(24, 0))
        self.standard_btn = PillButton(self.standard_frame, text="♩ 标准音 A", command=self._play_standard_a,
                                       width=150, height=40, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                                       font_size=13)
        self.standard_btn.pack(side="left", padx=6)

        self.play_btn = PillButton(self, text="▶ 播放题目", command=self._play_current,
                                   width=260, height=64, font_size=18, bold=True)
        self.play_btn.pack(pady=(26, 0))

        # 答题区
        self.answer_card = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        self.answer_card.pack(fill="x", padx=80, pady=28)

        # 单音输入
        self.note_input = tk.Frame(self.answer_card, bg=CARD)
        tk.Label(self.note_input, text="音名", bg=CARD, fg=GRAY, font=font(12)).pack(pady=(12, 4))
        self.note_entry_var = tk.StringVar()
        self.note_entry = tk.Entry(self.note_input, textvariable=self.note_entry_var, bg=BG, fg=FG,
                                   insertbackground=FG, relief="flat", font=font(20, True),
                                   justify="center", width=10)
        self.note_entry.pack(pady=(0, 10))
        self.note_entry.bind("<Return>", lambda _e: self._submit())
        note_btn_row = tk.Frame(self.note_input, bg=CARD)
        note_btn_row.pack(pady=(0, 8))
        self._note_buttons: dict[str, FlatButton] = {}
        for label in NOTE_LABELS:
            btn = FlatButton(note_btn_row, text=label, command=lambda l=label: self._select_note(l),
                             bg=BG, fg=FG, hover_bg="#1c1c1e", active_bg=FG, active_fg=BG,
                             font_size=11, padx=10, pady=6)
            btn.pack(side="left", padx=2)
            self._note_buttons[label] = btn
        octave_row = tk.Frame(self.note_input, bg=CARD)
        octave_row.pack(pady=(0, 16))
        tk.Label(octave_row, text="八度", bg=CARD, fg=GRAY, font=font(12)).pack(side="left", padx=(0, 8))
        for label in OCTAVE_LABELS:
            btn = FlatButton(octave_row, text=label, command=lambda l=label: self._select_octave(int(l)),
                             bg=BG, fg=FG, hover_bg="#1c1c1e", active_bg=FG, active_fg=BG,
                             font_size=12, padx=12, pady=6)
            btn.pack(side="left", padx=2)

        # 和弦/音程/旋律共用文本输入
        self.chord_input = tk.Frame(self.answer_card, bg=CARD)
        self.chord_input_label = tk.Label(self.chord_input, text="和弦符号（如 Cmaj7 / C 大三和弦）", bg=CARD, fg=GRAY,
                                          font=font(12))
        self.chord_input_label.pack(pady=(16, 6))
        self.chord_entry_var = tk.StringVar()
        self.chord_entry = tk.Entry(self.chord_input, textvariable=self.chord_entry_var, bg=BG, fg=FG,
                                    insertbackground=FG, relief="flat", font=font(18, True),
                                    justify="center", width=28)
        self.chord_entry.pack(pady=(0, 16))
        self.chord_entry.bind("<Return>", lambda _e: self._submit())

        # 提交/语音/重听
        action_row = tk.Frame(self, bg=BG)
        action_row.pack(pady=(0, 20))
        self.submit_btn = PillButton(action_row, text="提交答案", command=self._submit,
                                     width=170, height=48, font_size=15, bold=True)
        self.submit_btn.pack(side="left", padx=8)
        self.voice_btn = PillButton(action_row, text="🎤 语音输入", command=self._start_voice,
                                    width=170, height=48, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                                    font_size=15)
        self.voice_btn.pack(side="left", padx=8)
        self.replay_btn = PillButton(action_row, text="↻ 重听", command=self._replay,
                                     width=120, height=48, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                                     font_size=14)
        self.replay_btn.pack(side="left", padx=8)
        self.arpeggio_btn = PillButton(action_row, text="🎹 琶音重听", command=self._replay_arpeggio,
                                       width=140, height=48, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                                       font_size=14)
        self.arpeggio_btn.pack(side="left", padx=8)
        self.answer_play_btn = PillButton(action_row, text="▶ 播放所填答案", command=self._play_submitted_answer,
                                          width=150, height=48, bg=CARD, fg=FG, active_bg=FG, active_fg=BG,
                                          font_size=13)
        self.answer_play_btn.pack(side="left", padx=8)
        self.answer_play_btn.set_enabled(False)

        # 反馈
        self.feedback_label = tk.Label(self, text="", bg=BG, fg=FG, font=font(16, True), wraplength=700)
        self.feedback_label.pack(pady=(4, 8))
        self.next_btn = PillButton(self, text="下一题", command=self._next,
                                   width=180, height=48, font_size=15, bold=True)
        self.next_btn.pack()

        # 初始状态
        self._set_input_visible("note")
        self.next_btn.pack_forget()

    def _schedule(self, ms: int, func):
        after_id = self.app.root.after(ms, func)
        self._after_ids.append(after_id)
        return after_id

    def on_hide(self):
        if self._key_funcid is not None:
            try:
                self.app.root.unbind("<KeyPress-space>", self._key_funcid)
            except Exception:
                pass
            self._key_funcid = None
        for after_id in self._after_ids:
            try:
                self.app.root.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids.clear()

    # ------------------------------------------------------------ 生命周期

    def on_show(self, mode: str, category: str, rounds: int, questions=None, **kwargs):
        self.mode = mode
        self.category = category
        self.rounds = rounds
        self._from_wrongbook = questions is not None
        if questions is not None:
            self.questions = questions
            self.rounds = len(questions)
        else:
            # 简单模式固定 C 大调自然音：只包含 1/2/3/4/5/6/7，不出现升降号
            gen_key = 0 if mode == "easy" else int(self.app.config.get("key"))
            self.questions = music.generate_questions(
                mode, category, rounds,
                random_inversions=self.app.config.get("random_inversions"),
                key=gen_key,
                note_low=int(self.app.config.get("note_low")),
                note_high=int(self.app.config.get("note_high")),
                chord_low=int(self.app.config.get("chord_low")),
                chord_high=int(self.app.config.get("chord_high")),
                progressive=bool(self.app.config.get("progressive")),
                strict_mode=bool(self.app.config.get("strict_mode")),
            )
        self.index = 0
        self.correct_count = 0
        self.answered = False
        self.recording = False
        self._details = []
        self.title_label.config(text=music.MODE_LABELS[mode] + "模式")
        self._set_input_visible(self._input_kind_for_mode(mode))
        self._show_standard(mode not in ("hell", "hell_note"))
        self._reset_question()
        self._schedule(350, self._play_current)
        if self._key_funcid is None:
            self._key_funcid = self.app.root.bind("<KeyPress-space>", self._on_space, add="+")
        if self.voice_enabled:
            self.app.speak_async("请听题", "zh")

    def _on_space(self, _event=None):
        """空格重听当前题目。"""
        if not self.answered and self.index < len(self.questions):
            self._replay()
            return "break"
        return None

    def _quit(self):
        self.app.show_page("home")

    def _toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        self.voice_toggle_btn.config(
            text="🔊 语音播报" if self.voice_enabled else "🔇 已静音",
            fg=FG if self.voice_enabled else GRAY,
        )

    def _reset_question(self):
        self.answered = False
        self.recording = False
        self._stop_event = None
        self._submitted_play_midis = None
        self.answer_play_btn.set_enabled(False)
        self.answer_play_btn.set_text("▶ 播放所填答案")
        self.voice_btn.set_command(self._start_voice)
        self.voice_btn.set_text("🎤 语音输入")
        # 根据当前题目类型切换输入区（支持错题本混合题型）
        qtype = self.questions[self.index]["type"] if self.index < len(self.questions) else "note"
        self._set_input_visible(self._input_kind_for_type(qtype))
        self._configure_note_buttons_for_easy()
        self.progress_label.config(text=f"第 {self.index + 1}/{self.rounds} 题")
        self.progress_bar.set((self.index + 1) / max(1, self.rounds))
        self.feedback_label.config(text="", bg=BG)
        self.next_btn.pack_forget()
        self.play_btn.set_text("▶ 播放题目")
        self.play_btn.set_enabled(True)
        self.submit_btn.set_enabled(True)
        self.voice_btn.set_enabled(True)
        self.replay_btn.set_enabled(True)
        self.arpeggio_btn.set_enabled(True)
        if self.mode in ("easy", "normal", "hell_note"):
            self.note_entry_var.set("")
            self._select_note("C")
            self._select_octave(4)
            self.note_entry.config(state="normal")
            self.note_entry.focus_set()
        else:
            self.chord_entry_var.set("")
            self.chord_entry.config(state="normal")
            self.chord_entry.focus_set()

    # ------------------------------------------------------------ 显示切换

    def _input_kind_for_mode(self, mode: str) -> str:
        if mode in ("easy", "normal", "hell_note"):
            return "note"
        if mode == "interval":
            return "interval"
        if mode == "melody":
            return "melody"
        return "chord"

    @staticmethod
    def _input_kind_for_type(qtype: str) -> str:
        if qtype == "note":
            return "note"
        if qtype == "interval":
            return "interval"
        if qtype == "melody":
            return "melody"
        return "chord"

    def _set_input_visible(self, kind: str):
        if kind == "note":
            self.chord_input.pack_forget()
            self.note_input.pack(fill="x", padx=24, pady=16)
            self.arpeggio_btn.pack_forget()
        else:
            self.note_input.pack_forget()
            self.chord_input.pack(fill="x", padx=24, pady=16)
            if kind == "chord":
                self.chord_input_label.config(text="和弦符号（如 Cmaj7 / C 大三和弦）")
                self.arpeggio_btn.pack(side="left", padx=8)
            elif kind == "interval":
                self.chord_input_label.config(text="音程（如 纯五度 / P5 / major third）")
                self.arpeggio_btn.pack_forget()
            elif kind == "melody":
                self.chord_input_label.config(text="旋律音（空格或逗号分隔，如 C4 E4 G4）")
                self.arpeggio_btn.pack_forget()

    def _show_standard(self, visible: bool):
        if visible:
            self.standard_frame.pack(pady=(24, 0))
        else:
            self.standard_frame.pack_forget()

    def _configure_note_buttons_for_easy(self):
        """简单模式只有 1-7 自然音，禁用所有带升降号的音名按钮。"""
        easy = self.mode == "easy"
        for label, btn in self._note_buttons.items():
            if "#" not in label:
                continue
            if easy:
                btn.set_style(bg=BG, fg=SUBTLE, hover_bg=BG, active_bg=BG, active_fg=SUBTLE)
                btn.config(state="disabled", cursor="arrow")
            else:
                btn.set_style(bg=BG, fg=FG, hover_bg="#1c1c1e", active_bg=FG, active_fg=BG)
                btn.config(state="normal", cursor="hand2")

    # ------------------------------------------------------------ 输入

    def _select_note(self, label: str):
        # 简单模式只允许自然音；但用户仍可输入升降号，这里不做硬限制
        self._note_pc = NOTE_LABELS.index(label)
        self.note_entry_var.set(f"{label}{self._octave}")

    def _select_octave(self, octave: int):
        self._octave = octave
        label = NOTE_LABELS[self._note_pc]
        self.note_entry_var.set(f"{label}{octave}")

    def _current_text(self) -> str:
        if self.mode in ("easy", "normal", "hell_note"):
            return self.note_entry_var.get().strip()
        return self.chord_entry_var.get().strip()

    # ------------------------------------------------------------ 播放

    def _play_standard_a(self):
        a4 = music.midi_from_parts(9, 4)  # A4 = 442Hz
        audio.play_midis([a4], duration=1.2)

    def _play_current(self):
        if self.index < len(self.questions):
            audio.play_question(self.questions[self.index])

    def _replay(self):
        q = self.questions[self.index]
        if q["type"] == "chord":
            # 先柱式，再提供琶音重听
            audio.play_question(q, arpeggio=False)
        else:
            audio.play_question(q)

    def _replay_arpeggio(self):
        q = self.questions[self.index]
        if q["type"] == "chord":
            audio.play_question(q, arpeggio=True)

    def _play_submitted_answer(self):
        """播放用户所填答案对应的音高/和弦。"""
        if self._submitted_play_midis:
            q = self.questions[self.index] if self.index < len(self.questions) else None
            use_arpeggio = bool(q and q["type"] in ("interval", "melody"))
            duration = 1.8 if len(self._submitted_play_midis) > 2 else 1.2
            audio.play_midis(self._submitted_play_midis, duration=duration, arpeggio=use_arpeggio)

    def _set_feedback(self, text: str, color: str):
        self.feedback_label.config(text=text, bg=BG)
        animate_fg(self.feedback_label, color)

    # ------------------------------------------------------------ 作答

    def _submit(self):
        if self.answered:
            return
        text = self._current_text()
        if not text:
            self.feedback_label.config(text="请输入答案", fg=ERROR, bg=BG)
            return

        q = self.questions[self.index]
        self._submitted_play_midis = None

        if q["type"] == "note":
            parsed = music.parse_note(text)
            if parsed is None:
                self.feedback_label.config(text="无法识别该音名，请用 C4、C#4、升C 等格式", fg=ERROR, bg=BG)
                return
            pc, octave = parsed
            if self.mode == "easy" and pc not in music.NATURAL_PCS:
                self.feedback_label.config(text="简单模式只包含 1/2/3/4/5/6/7 自然音，不能使用升降号",
                                           fg=ERROR, bg=BG)
                return
            if octave is None:
                # 未给八度时使用界面当前八度
                octave = self._octave
            self._submitted_play_midis = [music.midi_from_parts(pc, octave)]
            correct = (pc == q["root_pc"]) and (self.app.config.get("ignore_octave") or octave == q["octave"])
        elif q["type"] == "chord":
            answer = music.parse_chord(text)
            if answer is None:
                self.feedback_label.config(text="无法识别该和弦，请用 Cmaj7、C 大三和弦、C major 等格式", fg=ERROR, bg=BG)
                return
            root_midi = music.midi_from_parts(answer.root_pc, answer.root_octave or 4)
            self._submitted_play_midis = music.chord_play_midis(root_midi, answer.quality, 0)
            correct = music.chord_answer_is_correct(answer, q["root_pc"], q["quality"])
            # 严格模式：随机转位题必须同时答出转位
            if correct and self.app.config.get("strict_mode") and q.get("inversion", 0) != 0:
                inv = music.parse_chord_inversion(text)
                if inv is None or inv != q["inversion"]:
                    correct = False
        elif q["type"] == "interval":
            parsed = music.parse_interval(text)
            if parsed is None:
                self.feedback_label.config(text="无法识别该音程，请用 纯五度、P5、major third 等格式", fg=ERROR, bg=BG)
                return
            self._submitted_play_midis = q["play_midis"]
            correct = music.interval_answer_is_correct(parsed, q["semitones"])
        elif q["type"] == "melody":
            parsed_midis = music.parse_melody(text)
            if parsed_midis is None:
                self.feedback_label.config(text="无法识别旋律，请用空格或逗号分隔音名，如 C4 E4 G4", fg=ERROR, bg=BG)
                return
            self._submitted_play_midis = parsed_midis
            correct = music.melody_answer_is_correct(parsed_midis, q["play_midis"],
                                                     ignore_octave=self.app.config.get("ignore_octave"))
        else:
            self.feedback_label.config(text="暂不支持该题型", fg=ERROR, bg=BG)
            return

        self.answered = True
        if self._submitted_play_midis:
            self.answer_play_btn.set_enabled(True)
        if correct:
            self.correct_count += 1
            self._set_feedback("✓ 正确", SUCCESS)
            if self._from_wrongbook:
                self.app.wrongbook.remove(q)
            if self.voice_enabled:
                self.app.speak_async("正确", "zh")
        else:
            self.app.wrongbook.add(q)
            self._set_feedback(f"✗ 错误    正确答案：{q['answer_name']}", ERROR)
            if self.voice_enabled:
                self.app.speak_async(f"错误，正确答案是 {q['answer_name']}", "zh")
            # 组合反馈：稍后自动播放正确音高
            self._schedule(1400, lambda q=q: audio.play_question(q))

        self._details.append({
            "type": q["type"],
            "question": q["answer_name"],
            "user_answer": text,
            "correct": correct,
        })

        self.submit_btn.set_enabled(False)
        self.voice_btn.set_enabled(False)
        self.replay_btn.set_enabled(True)
        if q["type"] == "note":
            self.note_entry.config(state="disabled")
        else:
            self.chord_entry.config(state="disabled")
        self.next_btn.set_command(self._next)
        self.next_btn.pack(pady=(0, 20))

    def _next(self):
        if self.index + 1 >= self.rounds:
            self.app.finish_training(self.mode, self.rounds, self.correct_count, details=self._details)
            return
        self.index += 1
        self._reset_question()
        self._schedule(250, self._play_current)

    # ------------------------------------------------------------ 语音

    def _start_voice(self):
        if self.answered or self.recording:
            return
        self.recording = True
        self._stop_event = threading.Event()
        self.voice_btn.set_command(self._stop_voice)
        self.voice_btn.set_text("■ 停止录音")
        self.voice_btn.set_enabled(True)
        threading.Thread(target=self._voice_worker, daemon=True).start()

    def _stop_voice(self):
        """手动停止录音：设置停止事件，录音线程会在当前块结束后返回。"""
        if not self.recording:
            return
        if self._stop_event is not None:
            self._stop_event.set()
        self.voice_btn.set_text("识别中…")
        self.voice_btn.set_enabled(False)

    def _set_download_progress(self, lang: str, p: float):
        spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        idx = int(max(0.0, min(1.0, p)) * 100) % len(spinner)
        self.voice_btn.set_text(f"{spinner[idx]} 下载{lang} {p * 100:.0f}%")

    def _voice_worker(self):
        # 首次使用语音：自动下载缺失的 Vosk 小模型
        prefer = self.app.config.get("voice_lang")
        langs = ["en", "cn"] if prefer == "auto" else [prefer]
        missing = [lang for lang in langs if audio.model_path(lang) is None]
        if missing:
            for lang in missing:
                def _progress(p, lang=lang):
                    self.app.root.after(0, lambda p=p, lang=lang: self._set_download_progress(lang, p))
                audio.ensure_model(lang, progress_cb=_progress)
            still_missing = [lang for lang in langs if audio.model_path(lang) is None]
            if still_missing:
                self.app.root.after(0, self._on_voice_error)
                return

        data = audio.record_until_silence(stop_event=self._stop_event)
        if not data:
            self.app.root.after(0, self._on_voice_result, "")
            return
        text = audio.recognize_voice(data, prefer_lang=prefer)
        self.app.root.after(0, self._on_voice_result, text)

    def _on_voice_error(self):
        self.recording = False
        self._stop_event = None
        self.voice_btn.set_command(self._start_voice)
        self.voice_btn.set_text("🎤 语音输入")
        self.voice_btn.set_enabled(True)
        self.feedback_label.config(
            text="语音模型下载失败，请检查网络后重试，或手动运行 python -m trainer.download_models",
            fg=ERROR, bg=BG,
        )

    def _on_voice_result(self, text: str):
        self.recording = False
        self._stop_event = None
        self.voice_btn.set_command(self._start_voice)
        self.voice_btn.set_text("🎤 语音输入")
        self.voice_btn.set_enabled(True)
        if not text:
            self.feedback_label.config(text="没有听清，请重试或手动输入", fg=ERROR, bg=BG)
            return
        q = self.questions[self.index]
        if q["type"] == "note":
            self.note_entry_var.set(text)
        else:
            self.chord_entry_var.set(text)
        # 能解析就自动提交，避免多余点击
        if q["type"] == "note":
            parsed_ok = music.parse_note(text) is not None
        elif q["type"] == "chord":
            parsed_ok = music.parse_chord(text) is not None
        elif q["type"] == "interval":
            parsed_ok = music.parse_interval(text) is not None
        elif q["type"] == "melody":
            parsed_ok = music.parse_melody(text) is not None
        else:
            parsed_ok = False
        if parsed_ok:
            self._submit()
        else:
            self.feedback_label.config(text=f"识别到：{text}，请确认后提交", fg=GRAY, bg=BG)
