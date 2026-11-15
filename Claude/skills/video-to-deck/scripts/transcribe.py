#!/usr/bin/env python3
"""Fallback for videos WITHOUT burned-in subtitles: speech-to-text with faster-whisper.

Writes one "[mm:ss] text" line per segment (UTF-8). Runs on CPU; `small` is a reasonable
default (about 460 MB download on first use), `medium` is more accurate and slower.

  pip install faster-whisper          # into a venv, not the user's global Python
  python transcribe.py VIDEO OUT.txt [--model small] [--lang zh] [--model-dir DIR]
"""
import argparse
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default=None, help="e.g. zh, en; omit to auto-detect")
    ap.add_argument("--model-dir", default=None, help="where to cache the model (default: Hugging Face cache)")
    ap.add_argument("--max-seconds", type=float, default=None, help="stop after this many seconds (quick check)")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper is not installed: pip install faster-whisper (use a venv)")
    model = WhisperModel(a.model, device="cpu", compute_type="int8", download_root=a.model_dir)
    segments, info = model.transcribe(a.video, language=a.lang, vad_filter=True)
    n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        for s in segments:
            if a.max_seconds and s.start > a.max_seconds:
                break
            f.write(f"[{int(s.start // 60):02d}:{int(s.start % 60):02d}] {s.text.strip()}\n")
            n += 1
    print(f"language={info.language} segments={n} -> {a.out}")


if __name__ == "__main__":
    main()
