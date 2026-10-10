#!/usr/bin/env python3
"""Convenience launcher for the ASK reference interpreter."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "reference" / "ask.py"
    runpy.run_path(str(target), run_name="__main__")
