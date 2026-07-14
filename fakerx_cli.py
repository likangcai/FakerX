#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FakerX 命令行工具 - 兼容入口

此文件为兼容 v0.2.0 的入口点，实际功能委托给增强版 CLI (fakerx/cli.py)
"""
import sys


def main():
    """委托给增强版 CLI"""
    from fakerx.cli import main as enhanced_main
    sys.exit(enhanced_main())


if __name__ == '__main__':
    main()
