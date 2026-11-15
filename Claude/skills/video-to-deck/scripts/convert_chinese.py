#!/usr/bin/env python3
"""Convert a UTF-8 text file between Simplified and Traditional Chinese with OpenCC.

  pip install opencc-python-reimplemented     # into a venv
  python convert_chinese.py IN.txt OUT.txt [--config s2twp]

Configs: s2twp (Simplified -> Taiwan Traditional with Taiwan wording, e.g. 内存 -> 記憶體),
s2t, t2s, tw2sp. OpenCC leaves a few ambiguous characters alone (里 -> 裡 is the usual one):
grep the output for them afterwards.
"""
import argparse
import re
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--config", default="s2twp")
    a = ap.parse_args()
    try:
        from opencc import OpenCC
    except ImportError:
        sys.exit("OpenCC is not installed: pip install opencc-python-reimplemented (use a venv)")
    text = OpenCC(a.config).convert(open(a.src, encoding="utf-8", newline="").read())
    if a.config.startswith("s2t"):
        # 里 as "inside" after a noun; OpenCC keeps it because 里 is also a valid Traditional character.
        text = re.sub(r"(?<=[一-鿿A-Za-z])里(?=[含有的面頭，。、\s]|$)", "裡", text, flags=re.M)
    open(a.dst, "w", encoding="utf-8", newline="").write(text)
    left = sorted(set(re.findall(r".{0,4}里.{0,4}", text)))
    print(f"wrote {a.dst}" + (f"; check these 里: {left[:10]}" if left else ""))


if __name__ == "__main__":
    main()
