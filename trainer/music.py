# -*- coding: utf-8 -*-
"""乐理模块：音名、频率、和弦、题目生成、答案解析。"""
from __future__ import annotations

import re
import random
from dataclasses import dataclass, field
from typing import Iterable, Optional

# ---------------------------------------------------------------- 基本音高

A4_FREQ = 442.0
MIDI_A4 = 69

SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NATURAL_PCS = {0, 2, 4, 5, 7, 9, 11}

LETTER_TO_PC = {
    "c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11,
}
SOLFEGE_TO_PC = {
    "do": 0, "re": 2, "mi": 4, "fa": 5, "sol": 7, "so": 7, "la": 9, "si": 11, "ti": 11,
    "哆": 0, "来": 2, "咪": 4, "发": 5, "唆": 7, "嗦": 7, "拉": 9, "西": 11,
    "1": 0, "2": 2, "3": 4, "4": 5, "5": 7, "6": 9, "7": 11,
}

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "〇": 0, "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}


def midi_to_freq(midi: int, a4: float = A4_FREQ) -> float:
    return a4 * (2 ** ((midi - MIDI_A4) / 12.0))


def midi_to_name(midi: int, prefer_sharp: bool = True) -> str:
    pc = midi % 12
    octave = midi // 12 - 1
    names = SHARP_NAMES if prefer_sharp else FLAT_NAMES
    return f"{names[pc]}{octave}"


def pc_name(pc: int, prefer_sharp: bool = True) -> str:
    names = SHARP_NAMES if prefer_sharp else FLAT_NAMES
    return names[pc % 12]


def midi_from_parts(pc: int, octave: int) -> int:
    return (octave + 1) * 12 + (pc % 12)


# ---------------------------------------------------------------- 文本归一化

def _norm_text(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("＃", "#").replace("♯", "#").replace("♭", "b").replace("·", " ")
    text = text.replace("，", " ").replace("。", " ").replace("、", " ").replace("；", " ")
    text = text.replace("升", " 升 ").replace("降", " 降 ")
    text = re.sub(r"\s+", " ", text)
    return text


def _replace_number_words(text: str) -> str:
    for word, num in NUMBER_WORDS.items():
        text = re.sub(rf"\b{re.escape(word)}\b", str(num), text, flags=re.IGNORECASE)
    # 中文数字已在上面处理；再处理直接粘连形式如“四”
    return text


def _replace_voice_aliases(text: str) -> str:
    """处理语音识别常见的英文音名误听。"""
    text = text.lower()
    text = re.sub(r"\b(see|cee|sea)\b", "c", text)
    text = re.sub(r"\b(dee)\b", "d", text)
    text = re.sub(r"\b(ee|ease)\b", "e", text)
    text = re.sub(r"\b(eff)\b", "f", text)
    text = re.sub(r"\b(gee)\b", "g", text)
    text = re.sub(r"\b(ay|aye)\b", "a", text)
    text = re.sub(r"\b(bee|be)\b", "b", text)
    text = text.replace("sharp", "#").replace("flat", "b")
    text = text.replace("s h a r p", "#").replace("f l a t", "b")
    return text


def _extract_pc_and_accidental(text: str) -> tuple[Optional[int], int, int]:
    """从文本中提取第一个音名/唱名，返回 (pc, 结束位置, 升降记号半音数)。

    返回的结束位置用于判断后面的八度/和弦后缀。
    """
    text = _replace_voice_aliases(_norm_text(text))
    # 中文升降号写在前面：升C / 降B
    m = re.search(r"升\s*([a-g]|[哆来咪发唆嗦拉西])", text)
    if m:
        token = m.group(1)
        pc = LETTER_TO_PC.get(token)
        if pc is None:
            pc = SOLFEGE_TO_PC.get(token)
        return pc, m.end(), 1
    m = re.search(r"降\s*([a-g]|[哆来咪发唆嗦拉西])", text)
    if m:
        token = m.group(1)
        pc = LETTER_TO_PC.get(token)
        if pc is None:
            pc = SOLFEGE_TO_PC.get(token)
        return pc, m.end(), -1

    # 拼音/中文唱名优先，避免把 do 里的 d、re 里的 r 误当成英文字母音名
    # 同时用词边界排除 minor/diminished 里的 mi 等子串
    m = re.search(r"(?<![a-z])(do|re|mi|fa|sol|so|la|si|ti)(?![a-z])|(哆|来|咪|发|唆|嗦|拉|西)", text)
    if m:
        token = m.group(1) or m.group(2)
        pc = SOLFEGE_TO_PC[token]
        end = m.end()
        acc = 0
        rest = text[end:].lstrip()
        if rest.startswith("#"):
            acc = 1
            end += (len(text[end:]) - len(rest)) + 1
        elif rest.startswith("b"):
            acc = -1
            end += (len(text[end:]) - len(rest)) + 1
        return pc, end, acc

    # 英文/拼音音名：C, C#, Db, do, re, sol ...
    m = re.search(r"([a-g])", text)
    if m:
        pc = LETTER_TO_PC[m.group(1)]
        end = m.end()
        acc = 0
        rest = text[end:].lstrip()
        if rest.startswith("#"):
            acc = 1
            end += (len(text[end:]) - len(rest)) + 1
        elif rest.startswith("b"):
            acc = -1
            end += (len(text[end:]) - len(rest)) + 1
        return pc, end, acc

    return None, 0, 0


def parse_note(text: str) -> Optional[tuple[int, Optional[int]]]:
    """解析单音答案。

    返回 (pitch_class, octave 或 None)，无法解析返回 None。
    例如：C4 / C#4 / Db4 / 升C4 / C sharp 4 / do#4 / 拉3。
    """
    if not text or not text.strip():
        return None
    text = _replace_number_words(_replace_voice_aliases(_norm_text(text)))
    pc, end, acc = _extract_pc_and_accidental(text)
    if pc is None:
        return None
    pc = (pc + acc) % 12

    # 找紧跟音名后面的数字作为八度（也可能是中文数字已替换为阿拉伯数字）
    rest = text[end:]
    m = re.search(r"(\d+)", rest)
    octave = None
    if m:
        octave = int(m.group(1))
    return pc, octave


# ---------------------------------------------------------------- 和弦

@dataclass(frozen=True)
class ChordType:
    quality: str
    symbol: str
    intervals: tuple[int, ...]
    label_zh: str
    aliases: tuple[str, ...]
    category: str


CHORD_TYPES: dict[str, ChordType] = {
    "major": ChordType("major", "", (0, 4, 7), "大三和弦", ("major", "maj", "大三", "大三和弦", "大和弦"), "triad"),
    "minor": ChordType("minor", "m", (0, 3, 7), "小三和弦", ("minor", "min", "m", "小三", "小三和弦", "小和弦"), "triad"),
    "dim": ChordType("dim", "dim", (0, 3, 6), "减三和弦", ("dim", "diminished", "dimin", "减", "减三", "减三和弦", "o", "°"), "triad"),
    "aug": ChordType("aug", "aug", (0, 4, 8), "增三和弦", ("aug", "augmented", "+", "增", "增三", "增三和弦"), "triad"),
    "power": ChordType("power", "5", (0, 7), "强力和弦", ("power", "5", "五", "五和弦", "强力和弦", "强力"), "power"),
    "maj7": ChordType("maj7", "maj7", (0, 4, 7, 11), "大七和弦", ("maj7", "major7", "major seventh", "maj", "大七", "大七和弦", "maj7th"), "seventh"),
    "dom7": ChordType("dom7", "7", (0, 4, 7, 10), "属七和弦", ("7", "dom7", "dominant7", "dominant seventh", "属七", "属七和弦", "大小七"), "seventh"),
    "min7": ChordType("min7", "m7", (0, 3, 7, 10), "小七和弦", ("m7", "min7", "minor7", "minor seventh", "小七", "小七和弦"), "seventh"),
    "halfdim7": ChordType("halfdim7", "m7b5", (0, 3, 6, 10), "半减七和弦", ("m7b5", "half diminished seventh", "half-diminished", "half dim", "半减七", "半减七和弦", "ø7", "m7-5"), "seventh"),
    "dim7": ChordType("dim7", "dim7", (0, 3, 6, 9), "减七和弦", ("dim7", "diminished seventh", "减七", "减七和弦", "o7", "°7"), "seventh"),
}

CATEGORY_CHORD_KEYS: dict[str, list[str]] = {
    "triad": ["major", "minor", "dim", "aug"],
    "power": ["power"],
    "seventh": ["maj7", "dom7", "min7", "halfdim7", "dim7"],
    "all": ["major", "minor", "dim", "aug", "power", "maj7", "dom7", "min7", "halfdim7", "dim7"],
}

# 困难模式：C 大调自然音内允许的 (根音 pc, 性质)
NATURAL_CHORD_TEMPLATES: dict[str, list[tuple[int, str]]] = {
    "triad": [(0, "major"), (2, "minor"), (4, "minor"), (5, "major"), (7, "major"), (9, "minor"), (11, "dim")],
    "power": [(pc, "power") for pc in sorted(NATURAL_PCS)],
    "seventh": [(0, "maj7"), (2, "min7"), (4, "min7"), (5, "maj7"), (7, "dom7"), (9, "min7"), (11, "halfdim7")],
}
NATURAL_CHORD_TEMPLATES["all"] = (
    NATURAL_CHORD_TEMPLATES["triad"] + NATURAL_CHORD_TEMPLATES["power"] + NATURAL_CHORD_TEMPLATES["seventh"]
)


def chord_symbol(root_pc: int, quality: str) -> str:
    ct = CHORD_TYPES[quality]
    return f"{pc_name(root_pc)}{ct.symbol}"


def chord_notes(root_pc: int, quality: str) -> tuple[int, ...]:
    ct = CHORD_TYPES[quality]
    return tuple((root_pc + i) % 12 for i in ct.intervals)


def chord_play_midis(root_midi: int, quality: str, inversion: int = 0) -> list[int]:
    """根据根音 MIDI、性质和转位生成实际播放的 MIDI 音高列表。"""
    ct = CHORD_TYPES[quality]
    intervals = list(ct.intervals)
    if quality == "power":
        inversion = 0
    if inversion:
        if inversion >= len(intervals):
            inversion = 0
        # 把前 inversion 个音高八度上移，形成转位
        intervals = intervals[inversion:] + [i + 12 for i in intervals[:inversion]]
    return [root_midi + i for i in intervals]


# ---------------------------------------------------------------- 答案解析

def match_quality(suffix: str) -> Optional[str]:
    suffix = _replace_voice_aliases(_norm_text(suffix)).strip()
    if not suffix:
        return "major"
    # 先匹配更长/更特殊的别名
    for quality in ("halfdim7", "dim7", "maj7", "min7", "dom7"):
        for alias in CHORD_TYPES[quality].aliases:
            if re.search(rf"(^|\s){re.escape(alias)}(\s|$)", suffix) or suffix == alias:
                return quality
    for quality in ("major", "minor", "dim", "aug", "power"):
        for alias in CHORD_TYPES[quality].aliases:
            if re.search(rf"(^|\s){re.escape(alias)}(\s|$)", suffix) or suffix == alias:
                return quality
    # 纯数字后缀
    if suffix in ("7", "5", "m7", "m7b5", "dim7"):
        return {"7": "dom7", "5": "power", "m7": "min7", "m7b5": "halfdim7", "dim7": "dim7"}[suffix]
    return None


def _extract_note_pcs(text: str) -> set[int]:
    """从文本中找出所有音名/唱名的音级集合（用于校验和弦组成音）。"""
    pcs: set[int] = set()
    text = _replace_voice_aliases(_norm_text(text))
    # 英文音名：独立字母，避免把 major 里的 a、diminished 里的 d 误认为音名
    for m in re.finditer(r"(?<![a-z])([a-g])([#b]?)(?![a-z])", text):
        pc = LETTER_TO_PC[m.group(1)]
        acc = 1 if m.group(2) == "#" else (-1 if m.group(2) == "b" else 0)
        pcs.add((pc + acc) % 12)
    # 中文/拼音唱名（拉丁唱名用词边界，避免 minor/diminished 里的 mi 被误抓）
    for m in re.finditer(r"(?<![a-z])(do|re|mi|fa|sol|so|la|si|ti)(?![a-z])|(哆|来|咪|发|唆|嗦|拉|西)([#b]?)", text):
        if m.group(1):
            pc = SOLFEGE_TO_PC[m.group(1)]
            acc = 1 if m.group(2) == "#" else (-1 if m.group(2) == "b" else 0)
        else:
            pc = SOLFEGE_TO_PC[m.group(3)]
            acc = 1 if m.group(4) == "#" else (-1 if m.group(4) == "b" else 0)
        pcs.add((pc + acc) % 12)
    return pcs


@dataclass
class ChordAnswer:
    root_pc: int
    quality: str
    root_octave: Optional[int] = None
    note_pcs: Optional[set[int]] = None


def parse_chord(text: str) -> Optional[ChordAnswer]:
    """解析和弦答案。

    接受：
      C / Cm / Cdim / Caug / C5 / Cmaj7 / C7 / Cm7 / Cm7b5 / Cdim7
      C 大三和弦 / C 大七 / C 属七 / C 半减七 / C 强力和弦
      C major / C minor seventh / C half diminished seventh
      C E G 大三和弦（可带八度，如 C4 E4 G4）
    """
    if not text or not text.strip():
        return None
    text = _replace_number_words(_replace_voice_aliases(_norm_text(text)))
    pc, end, acc = _extract_pc_and_accidental(text)
    if pc is None:
        return None
    root_pc = (pc + acc) % 12

    # 去掉根音后的部分作为性质后缀；但保留全部文本用于提取组成音
    suffix = text[end:]
    # 如果根音后直接跟八度数字且后面还有性质/组成音，尽量忽略它作八度（和弦符号的 5/7 不当作八度）
    m = re.match(r"(\d+)", suffix)
    root_octave = None
    if m:
        # 若是 5 或 7 且后面没有更多内容，视为和弦性质而不是八度
        if m.group(1) in ("5", "7") and len(suffix.strip()) <= 2:
            pass
        else:
            root_octave = int(m.group(1))
            suffix = suffix[m.end():]

    quality = match_quality(suffix)
    if quality is None:
        # 兼容“C 第一转位”这类省略性质、只带转位的写法（默认大三和弦）
        quality_suffix = re.sub(
            r"(原位|根音位置|第一转位|第二转位|第三转位|root position|first inversion|second inversion|third inversion)",
            " ", suffix,
        )
        quality = match_quality(quality_suffix)
    if quality is None:
        return None

    note_pcs = _extract_note_pcs(text)
    return ChordAnswer(root_pc=root_pc, quality=quality, root_octave=root_octave, note_pcs=note_pcs)


def chord_answer_is_correct(answer: ChordAnswer, root_pc: int, quality: str) -> bool:
    if answer.root_pc != root_pc % 12:
        return False
    if answer.quality != quality:
        return False
    if answer.note_pcs is not None and len(answer.note_pcs) > 1:
        expected = set(chord_notes(root_pc, quality))
        if answer.note_pcs != expected:
            return False
    return True


def parse_chord_inversion(text: str) -> Optional[int]:
    """解析和弦转位标记；未识别返回 None。

    支持：原位/根音位置/第一转位/第二转位/第三转位/root position/first inversion 等。
    """
    if not text or not text.strip():
        return None
    t = _replace_voice_aliases(_norm_text(text))
    mapping = [
        (0, ("原位", "根音位置", "root position", "root", "fundamental")),
        (1, ("第一转位", "一转位", "first inversion", "1st inversion")),
        (2, ("第二转位", "二转位", "second inversion", "2nd inversion")),
        (3, ("第三转位", "三转位", "third inversion", "3rd inversion")),
    ]
    for inv, aliases in mapping:
        for alias in aliases:
            if re.search(rf"(^|\s){re.escape(alias)}(\s|$)", t) or t == alias:
                return inv
    return None


# ---------------------------------------------------------------- 音程/旋律解析

def parse_interval(text: str) -> Optional[int]:
    """解析音程答案，返回半音数（0-12），无法解析返回 None。

    支持：纯五度、大三度、P5、M3、perfect fifth、tritone 等。
    """
    if not text or not text.strip():
        return None
    t = _replace_voice_aliases(_norm_text(text))
    for semitones, aliases in INTERVAL_ALIASES.items():
        for alias in aliases:
            if re.search(rf"(^|\s){re.escape(alias)}(\s|$)", t) or t == alias:
                return semitones
    # 纯数字如 "5" 视为纯五度（仅在单独输入时）
    if re.fullmatch(r"\d+", t):
        n = int(t)
        if 0 <= n <= 12:
            return n
    return None


def parse_melody(text: str) -> Optional[list[int]]:
    """解析旋律答案，返回 MIDI 音高列表。

    支持逗号/空格分隔的音名，如：C4 E4 G4 或 C4,E4,G4。
    """
    if not text or not text.strip():
        return None
    parts = re.split(r"[,，\s]+", text.strip())
    midis: list[int] = []
    last_octave = 4
    for part in parts:
        parsed = parse_note(part)
        if parsed is None:
            return None
        pc, octave = parsed
        if octave is None:
            octave = last_octave
        midis.append(midi_from_parts(pc, octave))
        last_octave = octave
    return midis or None


def interval_answer_is_correct(answer_semitones: int, question_semitones: int) -> bool:
    return answer_semitones % 12 == question_semitones % 12


def melody_answer_is_correct(answer_midis: list[int], question_midis: list[int],
                             ignore_octave: bool = False) -> bool:
    if len(answer_midis) != len(question_midis):
        return False
    if ignore_octave:
        return [m % 12 for m in answer_midis] == [m % 12 for m in question_midis]
    return answer_midis == question_midis


# ---------------------------------------------------------------- 题目生成

MODE_LABELS = {
    "easy": "简单",
    "normal": "普通",
    "hard": "困难",
    "hell": "地狱",
    "hell_note": "地狱单音",
    "interval": "音程",
    "melody": "旋律",
}

CATEGORY_LABELS = {
    "triad": "三和弦",
    "power": "五和弦",
    "seventh": "七和弦",
    "all": "通用",
}

INTERVAL_LABELS = {
    0: "纯一度",
    1: "小二度",
    2: "大二度",
    3: "小三度",
    4: "大三度",
    5: "纯四度",
    6: "增四度/三全音",
    7: "纯五度",
    8: "小六度",
    9: "大六度",
    10: "小七度",
    11: "大七度",
    12: "纯八度",
}

INTERVAL_ALIASES = {
    0: ("unison", "perfect unison", "p1", "纯一度", "一度", "同度"),
    1: ("minor second", "min 2", "m2", "小二度", "小二"),
    2: ("major second", "maj 2", "m2", "大二度", "大二", "whole tone", "whole step"),
    3: ("minor third", "min 3", "m3", "小三度", "小三"),
    4: ("major third", "maj 3", "M3", "大三度", "大三"),
    5: ("perfect fourth", "p4", "纯四度", "纯四", "perfect 4th"),
    6: ("tritone", "augmented fourth", "diminished fifth", "tt", "增四度", "减五度", "三全音"),
    7: ("perfect fifth", "p5", "纯五度", "纯五", "perfect 5th"),
    8: ("minor sixth", "min 6", "m6", "小六度", "小六"),
    9: ("major sixth", "maj 6", "M6", "大六度", "大六"),
    10: ("minor seventh", "min 7", "m7", "小七度", "小七"),
    11: ("major seventh", "maj 7", "M7", "大七度", "大七"),
    12: ("octave", "perfect octave", "p8", "纯八度", "八度"),
}


def key_scale_pcs(key: int) -> set[int]:
    """指定调（0=C）的自然音级集合。"""
    return {(pc + key) % 12 for pc in NATURAL_PCS}


def natural_chord_templates_for_key(key: int) -> dict[str, list[tuple[int, str]]]:
    result: dict[str, list[tuple[int, str]]] = {}
    for cat, templates in NATURAL_CHORD_TEMPLATES.items():
        result[cat] = [((pc + key) % 12, quality) for pc, quality in templates]
    return result


def _build_chord_pool(mode: str, category: str, key: int = 0,
                      low: int = 48, high: int = 72) -> list[tuple[int, int, str]]:
    """返回 (根音 pc, 根音 MIDI, 性质) 列表。"""
    pool: list[tuple[int, int, str]] = []
    if mode == "hard":
        templates = natural_chord_templates_for_key(key)[category]
        for root_pc, quality in templates:
            for root_midi in range(low, high + 1):
                if root_midi % 12 == root_pc:
                    pool.append((root_pc, root_midi, quality))
    else:  # hell
        for root_pc in range(12):
            for quality in CATEGORY_CHORD_KEYS[category]:
                for root_midi in range(low, high + 1):
                    if root_midi % 12 == root_pc:
                        pool.append((root_pc, root_midi, quality))
    return pool


def _sample_pool(pool: list, count: int, rng: random.Random) -> list:
    rng.shuffle(pool)
    selected = []
    while len(selected) < count:
        selected.extend(pool[: max(0, count - len(selected))])
        rng.shuffle(pool)
    return selected


def generate_questions(
    mode: str,
    category: str = "all",
    count: int = 5,
    random_inversions: bool = False,
    seed: Optional[int] = None,
    key: int = 0,
    note_low: int = 48,
    note_high: int = 84,
    chord_low: int = 48,
    chord_high: int = 72,
    progressive: bool = False,
    strict_mode: bool = False,
) -> list[dict]:
    rng = random.Random(seed)
    if count <= 0:
        return []

    # 单音模式：easy / normal / hell_note
    if mode in ("easy", "normal", "hell_note"):
        all_pool = [midi for midi in range(note_low, note_high + 1)]
        if mode == "easy":
            all_pool = [midi for midi in all_pool if midi % 12 in key_scale_pcs(key)]
        questions = []
        if progressive and count > 1:
            mid = note_low + (note_high - note_low) // 2
            if mode == "easy":
                first_pool = [m for m in all_pool if mid - 6 <= m <= mid + 6] or all_pool
            else:
                first_pool = [m for m in all_pool if m % 12 in key_scale_pcs(key)] or all_pool
            first_count = count // 2
            second_count = count - first_count
            first_selected = _sample_pool(first_pool, first_count, rng)
            second_selected = _sample_pool(all_pool, second_count, rng)
            selected = first_selected + second_selected
        else:
            selected = _sample_pool(all_pool, count, rng)
        for midi in selected:
            questions.append({
                "type": "note",
                "mode": mode,
                "midi": midi,
                "answer_name": midi_to_name(midi),
                "play_midis": [midi],
                "root_pc": midi % 12,
                "octave": midi // 12 - 1,
            })
        return questions

    # 和弦模式：hard / hell
    if mode in ("hard", "hell"):
        full_pool = _build_chord_pool(mode, category, key=key, low=chord_low, high=chord_high)
        if not full_pool:
            return []
        if progressive and count > 1:
            simple_pool = [item for item in full_pool if item[2] in ("major", "minor", "power")]
            if not simple_pool:
                simple_pool = full_pool
            first_count = count // 2
            second_count = count - first_count
            first_selected = _sample_pool(simple_pool, first_count, rng)
            second_selected = _sample_pool(full_pool, second_count, rng)
            selected_pool = first_selected + second_selected
        else:
            selected_pool = _sample_pool(full_pool, count, rng)

        questions = []
        for i, (root_pc, root_midi, quality) in enumerate(selected_pool):
            inversion = 0
            if random_inversions:
                ct = CHORD_TYPES[quality]
                max_inv = 2 if quality in ("major", "minor", "dim", "aug") else (3 if quality in ("maj7", "dom7", "min7", "halfdim7", "dim7") else 0)
                # 渐进难度下前半部分保持原位
                if not (progressive and i < count // 2):
                    inversion = rng.randint(0, max_inv) if max_inv else 0
            play = chord_play_midis(root_midi, quality, inversion)
            ct = CHORD_TYPES[quality]
            note_names = [pc_name(p) for p in chord_notes(root_pc, quality)]
            questions.append({
                "type": "chord",
                "mode": mode,
                "root_pc": root_pc,
                "root_midi": root_midi,
                "quality": quality,
                "symbol": chord_symbol(root_pc, quality),
                "label_zh": ct.label_zh,
                "note_names": note_names,
                "play_midis": play,
                "inversion": inversion,
                "answer_name": f"{chord_symbol(root_pc, quality)}（{' '.join(note_names)}）",
            })
        return questions

    # 音程模式
    if mode == "interval":
        intervals = list(range(1, 13))
        pool = []
        for interval in intervals:
            for root in range(note_low, note_high + 1):
                if root + interval <= note_high:
                    pool.append((root, interval))
        selected = _sample_pool(pool, count, rng)
        questions = []
        for root, interval in selected:
            second = root + interval
            questions.append({
                "type": "interval",
                "mode": mode,
                "midis": [root, second],
                "play_midis": [root, second],
                "semitones": interval,
                "answer_name": INTERVAL_LABELS[interval],
            })
        return questions

    # 旋律模式
    if mode == "melody":
        questions = []
        scale = sorted(key_scale_pcs(key))
        for _ in range(count):
            length = rng.randint(3, 5)
            melody = _random_melody(rng, scale, note_low, note_high, length)
            questions.append({
                "type": "melody",
                "mode": mode,
                "midis": melody,
                "play_midis": melody,
                "answer_name": " ".join(midi_to_name(m) for m in melody),
            })
        return questions

    return []


def _random_melody(rng: random.Random, scale: list[int], low: int, high: int, length: int) -> list[int]:
    candidates = [m for m in range(low, high + 1) if m % 12 in scale]
    if not candidates:
        return list(range(low, min(high, low + length - 1) + 1))
    melody = [rng.choice(candidates)]
    for _ in range(length - 1):
        prev = melody[-1]
        options = [
            m for m in candidates
            if abs(m - prev) in (1, 2) and m not in melody[-3:]
        ]
        if not options:
            options = [m for m in candidates if abs(m - prev) <= 3]
        if not options:
            options = candidates
        melody.append(rng.choice(options))
    return melody
