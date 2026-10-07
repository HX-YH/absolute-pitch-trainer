# -*- coding: utf-8 -*-
"""命令行下载语音识别模型（打包/首次准备用）。"""
from __future__ import annotations

import sys

from . import audio


def main() -> None:
    print("准备 Vosk 语音识别模型...")
    ok = True
    for lang in ("en", "cn"):
        print(f"下载/检查 {lang} 模型...")
        path = audio.ensure_model(lang, progress_cb=lambda p: print(f"  {p * 100:.0f}%", end="\r"))
        if path:
            print(f"\n{lang} 模型就绪：{path}")
        else:
            print(f"\n{lang} 模型准备失败，应用首次语音输入时会再次尝试。")
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
