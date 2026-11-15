#!/usr/bin/env python3
"""Turn a video into contact sheets a model can read: burned-in subtitles and key frames.

  probe   : a few evenly spaced full frames with a % ruler, to see whether the video has
            burned-in subtitles and which horizontal band they sit in.
  extract : (1) subtitle strips, de-duplicated, stacked into sheets with mm:ss labels;
            (2) full frames, de-duplicated, tiled into grids with mm:ss labels.

Needs ffmpeg/ffprobe on PATH and Pillow. Paths are passed as arguments (non-ASCII is fine).

  python video_sheets.py probe   VIDEO OUTDIR [--n 6]
  python video_sheets.py extract VIDEO OUTDIR [--band 0.82,0.95] [--xpad 0.08]
                                 [--sub-fps 2] [--frame-every 2] [--no-subs]
"""
import argparse
import glob
import json
import os
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageStat


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd[:3])} ...\n{r.stderr[-800:]}")
    return r.stdout


def info(video):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
               "stream=width,height:format=duration", "-of", "json", video])
    j = json.loads(out)
    st = j["streams"][0]
    return int(st["width"]), int(st["height"]), float(j["format"]["duration"])


def fmt(t):
    t = max(0, t)
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def diff(a, b):
    return ImageStat.Stat(ImageChops.difference(a.convert("L"), b.convert("L"))).mean[0]


def probe(args):
    w, h, dur = info(args.video)
    os.makedirs(args.outdir, exist_ok=True)
    n = args.n
    tw = 640
    th = round(tw * h / w)
    sheet = Image.new("RGB", (tw * 2, (th + 20) * ((n + 1) // 2)), "white")
    d = ImageDraw.Draw(sheet)
    for i in range(n):
        t = dur * (i + 0.5) / n
        p = os.path.join(args.outdir, f"probe_{i}.jpg")
        run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", args.video, "-frames:v", "1",
             "-vf", f"scale={tw}:-2", "-y", p])
        im = Image.open(p).resize((tw, th))
        x, y = (i % 2) * tw, (i // 2) * (th + 20)
        sheet.paste(im, (x, y + 20))
        d.text((x + 4, y + 4), fmt(t), fill="red")
        for pct in range(10, 100, 10):  # ruler: fraction of frame height
            yy = y + 20 + th * pct // 100
            d.line([(x, yy), (x + 26, yy)], fill="red", width=1)
            d.text((x + 28, yy - 6), f".{pct // 10}", fill="red")
        os.remove(p)
    out = os.path.join(args.outdir, "probe.jpg")
    sheet.save(out, quality=88)
    print(json.dumps({"width": w, "height": h, "duration_s": round(dur, 1), "duration": fmt(dur), "probe_sheet": out}, ensure_ascii=False))


def extract(args):
    w, h, dur = info(args.video)
    out = args.outdir
    sub_dir, full_dir, sheets = (os.path.join(out, x) for x in ("sub", "full", "sheets"))
    for p in (sub_dir, full_dir, sheets):
        os.makedirs(p, exist_ok=True)
    for p in glob.glob(os.path.join(sub_dir, "*.jpg")) + glob.glob(os.path.join(full_dir, "*.jpg")) + glob.glob(os.path.join(sheets, "*.jpg")):
        os.remove(p)
    result = {"duration": fmt(dur), "sheets_dir": sheets}

    if not args.no_subs:
        y0, y1 = (float(v) for v in args.band.split(","))
        cw, ch = int(w * (1 - 2 * args.xpad)) // 2 * 2, int(h * (y1 - y0)) // 2 * 2
        cx, cy = int(w * args.xpad), int(h * y0)
        run(["ffmpeg", "-v", "error", "-i", args.video, "-vf",
             f"fps={args.sub_fps},crop={cw}:{ch}:{cx}:{cy},scale=800:-2", "-q:v", "3",
             os.path.join(sub_dir, "s_%05d.jpg")])
        kept, prev = [], None
        for i, p in enumerate(sorted(glob.glob(os.path.join(sub_dir, "s_*.jpg")))):
            im = Image.open(p)
            if prev is None or diff(im, prev) > args.sub_thresh:
                kept.append((i / args.sub_fps, im))
                prev = im
        per, W = 36, 800
        H = max(40, round(W * ch / cw))
        files = []
        for s in range(0, len(kept), per):
            chunk = kept[s:s + per]
            sheet = Image.new("RGB", (W + 70, H * len(chunk)), "white")
            d = ImageDraw.Draw(sheet)
            for j, (t, im) in enumerate(chunk):
                sheet.paste(im.resize((W, H)), (70, j * H))
                d.text((4, j * H + H // 2 - 6), fmt(t), fill="red")
            f = os.path.join(sheets, f"sub_{s // per:02d}.jpg")
            sheet.save(f, quality=85)
            files.append(f)
        result["subtitle_strips"] = len(kept)
        result["subtitle_sheets"] = files

    step = args.frame_every
    run(["ffmpeg", "-v", "error", "-i", args.video, "-vf", f"fps=1/{step},scale=640:-2", "-q:v", "4",
         os.path.join(full_dir, "f_%05d.jpg")])
    keptf, prev = [], None
    for i, p in enumerate(sorted(glob.glob(os.path.join(full_dir, "f_*.jpg")))):
        im = Image.open(p)
        if prev is None or diff(im, prev) > args.frame_thresh:
            keptf.append((i * step + step / 2, im))
            prev = im
    cols, rows, tw = 4, 4, 400
    th = round(tw * h / w)
    files = []
    for s in range(0, len(keptf), cols * rows):
        chunk = keptf[s:s + cols * rows]
        sheet = Image.new("RGB", (cols * tw, -(-len(chunk) // cols) * (th + 18)), "white")
        d = ImageDraw.Draw(sheet)
        for j, (t, im) in enumerate(chunk):
            x, y = (j % cols) * tw, (j // cols) * (th + 18)
            sheet.paste(im.resize((tw - 4, th)), (x, y + 18))
            d.text((x + 4, y + 3), fmt(t), fill="red")
        f = os.path.join(sheets, f"full_{s // (cols * rows):02d}.jpg")
        sheet.save(f, quality=85)
        files.append(f)
    result["key_frames"] = len(keptf)
    result["frame_sheets"] = files
    print(json.dumps(result, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("video"); p.add_argument("outdir"); p.add_argument("--n", type=int, default=6)
    p.set_defaults(fn=probe)
    e = sub.add_parser("extract")
    e.add_argument("video"); e.add_argument("outdir")
    e.add_argument("--band", default="0.82,0.95", help="subtitle band as top,bottom fractions of frame height")
    e.add_argument("--xpad", type=float, default=0.08, help="fraction cropped from each side")
    e.add_argument("--sub-fps", type=float, default=2)
    e.add_argument("--sub-thresh", type=float, default=6, help="mean pixel difference that counts as a new subtitle")
    e.add_argument("--frame-every", type=float, default=2, help="seconds between sampled full frames")
    e.add_argument("--frame-thresh", type=float, default=10)
    e.add_argument("--no-subs", action="store_true", help="video has no burned-in subtitles: only key frames")
    e.set_defaults(fn=extract)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
