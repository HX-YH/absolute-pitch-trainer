#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""绝对音准训练器 - 桌面应用入口。"""

import sys
import os

# 保证以源码方式运行时能 import trainer 包
if __package__ is None and __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trainer.ui.app import App


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
