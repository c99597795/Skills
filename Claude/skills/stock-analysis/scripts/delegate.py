"""把單一角色外包給 Codex 執行 — 透過 codex-plugin-cc 的 companion script。

原專案每個 agent 是獨立的 LLM 呼叫,彼此看不到對方的內部推理。Claude 一人分飾
全部角色時做不到這件事:前面角色的思路對後面角色一定可見,對抗性會被稀釋。
把「對手方」角色丟給 Codex 跑,對抗就變回真的 — 它只看得到寫進檔案的內容。

    python3 delegate.py run market 2330.TW 2026-08-12 [--background]
    python3 delegate.py run bear   2330.TW 2026-08-12 --round 2
    python3 delegate.py status [job-id] [--wait]

角色設定取自 reference/agents.md(單一來源,不重複維護)。
Codex 的工作目錄固定在 ~/.stock-analysis,報告寫進 runs/<TICKER>_<DATE>/。
"""

import argparse
import glob
import os
import pathlib
import shutil
import subprocess
import sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
AGENTS_MD = SKILL_DIR / "reference" / "agents.md"
WORKSPACE = pathlib.Path.home() / ".stock-analysis"

COMPANION_CANDIDATES = [
    pathlib.Path.home() / ".claude/plugins/marketplaces/openai-codex/plugins/codex/scripts/codex-companion.mjs",
    pathlib.Path.home() / ".claude/plugins/repos/openai-codex/plugins/codex/scripts/codex-companion.mjs",
]

# role -> (agents.md 章節標題前綴, 輸出檔名, 階段)
ROLES = {
    "market":       ("1. 技術面分析師", "01_market.md", "analyst"),
    "fundamentals": ("2. 基本面分析師", "01_fundamentals.md", "analyst"),
    "news":         ("3. 新聞分析師", "01_news.md", "analyst"),
    "sentiment":    ("4. 情緒分析師", "01_sentiment.md", "analyst"),
    "bull":         ("5. 多方研究員", "02_bull_r{round}.md", "debate"),
    "bear":         ("6. 空方研究員", "02_bear_r{round}.md", "debate"),
    "aggressive":   ("9a. 激進派", "05_aggressive.md", "risk"),
    "conservative": ("9b. 保守派", "05_conservative.md", "risk"),
    "neutral":      ("9c. 中立派", "05_neutral.md", "risk"),
}


def find_node() -> str:
    node = shutil.which("node")
    if node:
        return node
    # WSL 上 node 由 nvm 管理,非登入 shell 找不到。
    versions = sorted(glob.glob(str(pathlib.Path.home() / ".nvm/versions/node/*/bin/node")))
    if versions:
        return versions[-1]
    sys.exit("找不到 node。先 `source ~/.nvm/nvm.sh`,或安裝 Node 18.18+。")


def find_companion() -> pathlib.Path:
    for p in COMPANION_CANDIDATES:
        if p.exists():
            return p
    sys.exit(
        "找不到 codex plugin 的 codex-companion.mjs。\n"
        "先在 Claude Code 執行:/plugin marketplace add openai/codex-plugin-cc"
    )


def role_section(prefix: str) -> str:
    """從 agents.md 抽出某個角色的段落。標題是 `## <prefix> ...` 或 `### <prefix> ...`。"""
    text = AGENTS_MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = None
    depth = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip()
        if line.startswith("#") and stripped.startswith(prefix):
            start = i
            depth = len(line) - len(line.lstrip("#"))
            break
    if start is None:
        sys.exit(f"agents.md 裡找不到章節 {prefix!r}")

    out = [lines[start]]
    for line in lines[start + 1:]:
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= depth:
                break
        out.append(line)
    return "\n".join(out).strip()


def bundle_rel(ticker: str, date: str) -> str:
    p = WORKSPACE / "bundles" / f"{ticker}_{date}.md"
    if not p.exists():
        sys.exit(f"資料包不存在: {p}\n先跑 fetch_data.py {ticker} --date {date}")
    return str(p.relative_to(WORKSPACE))


def readable_files(run_rel: str, stage: str, self_name: str) -> list[str]:
    """列出這個角色可以讀的既有檔案 — 只給它該看的,不給它還沒發生的階段。"""
    run_dir = WORKSPACE / run_rel
    if not run_dir.exists():
        return []
    prefixes = {
        "analyst": (),                       # 分析師只看資料包
        "debate":  ("01_", "02_"),           # 辯論者看四份分析 + 已發生的交鋒
        "risk":    ("01_", "02_", "03_", "04_"),
    }[stage]
    if not prefixes:
        return []
    return sorted(
        f"{run_rel}/{f.name}"
        for f in run_dir.iterdir()
        if f.is_file() and f.name.startswith(prefixes) and f.name != self_name
    )


def build_prompt(role: str, ticker: str, date: str, rnd: int, extra: str) -> tuple[str, str]:
    prefix, out_tpl, stage = ROLES[role]
    out_name = out_tpl.format(round=rnd)
    run_rel = f"runs/{ticker}_{date}"
    bundle = bundle_rel(ticker, date)
    inputs = readable_files(run_rel, stage, out_name)

    read_list = [f"- `{bundle}` — 資料包,所有數字與新聞的唯一來源"]
    read_list += [f"- `{f}`" for f in inputs]

    round_note = ""
    if stage == "debate":
        round_note = (
            f"\n這是第 {rnd} 輪。"
            + ("第一輪先立論。\n" if rnd == 1 else
               "**必須實際回應對手前一輪講的話**,逐點反駁,不要重講第一輪的內容。\n")
        )

    # 第一行會變成 `status` 表格裡的 Summary,多個角色並行時靠它辨識。
    prompt = f"""【{role} | {ticker} @ {date} → {out_name}】

你是 {ticker} 個股分析流程中的一個角色。標的 {ticker},分析基準日 {date}。

嚴格照角色設定行事。**不要越權做其他角色的工作** — 不要下最終評等(除非你的角色
就是要下),不要幫後面的角色先總結。這套流程的價值來自角色之間真正的對抗。

---

{role_section(prefix)}

---

## 可讀的檔案(路徑相對於目前工作目錄)

{chr(10).join(read_list)}
{round_note}
## 硬約束

- 所有數字、價位、指標值、新聞標題必須來自資料包。**資料包裡沒有的,一律不准寫。**
- 資料包末尾的「資料品質」區塊列出哪些來源是空的。空的來源不准腦補,缺什麼就說缺什麼,並據此下修 confidence。
- 精確的 OHLCV / 指標數值一律以資料包的「驗證快照」為準;其他區塊與它衝突時標示矛盾,不要自行調和。
- 全文用繁體中文。
- 只寫你自己的那一份檔案,不要修改資料包,也不要動 `runs/` 底下其他角色的檔案。
{extra}
## 交付

把報告完整寫進 `{run_rel}/{out_name}`(不存在就建立)。
寫完後在回覆裡只給一行摘要,不要把全文貼回 stdout。
"""
    return prompt, out_name


def cmd_run(args):
    if args.role not in ROLES:
        sys.exit(f"未知角色 {args.role!r}。可用:{', '.join(ROLES)}")

    ticker = args.ticker.upper()
    extra = f"- {args.extra}\n" if args.extra else ""
    prompt, out_name = build_prompt(args.role, ticker, args.date, args.round, extra)

    run_dir = WORKSPACE / "runs" / f"{ticker}_{args.date}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / f".prompt_{out_name}"
    prompt_path.write_text(prompt, encoding="utf-8")

    cmd = [
        find_node(), str(find_companion()), "task",
        "--cwd", str(WORKSPACE),
        "--write",                                   # 要能寫報告檔
        "--fresh",                                   # 每個角色都是獨立 thread
        "--prompt-file", str(prompt_path.relative_to(WORKSPACE)),
    ]
    if args.background:
        cmd.append("--background")
    if args.model:
        cmd += ["--model", args.model]
    if args.effort:
        cmd += ["--effort", args.effort]

    print(f"[delegate] {args.role} → {run_dir.name}/{out_name}", file=sys.stderr)
    proc = subprocess.run(cmd, cwd=WORKSPACE, env={**os.environ, "PATH": os.environ.get("PATH", "")})
    sys.exit(proc.returncode)


def cmd_status(args):
    cmd = [find_node(), str(find_companion()), "status", "--cwd", str(WORKSPACE)]
    if args.job_id:
        cmd.append(args.job_id)
    if args.wait:
        cmd.append("--wait")
    if args.all:
        cmd.append("--all")
    sys.exit(subprocess.run(cmd, cwd=WORKSPACE).returncode)


def main():
    ap = argparse.ArgumentParser(description="把個股分析的單一角色外包給 Codex")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="跑一個角色")
    p.add_argument("role", help=", ".join(ROLES))
    p.add_argument("ticker")
    p.add_argument("date", help="YYYY-MM-DD,要跟資料包同一天")
    p.add_argument("--round", type=int, default=1, help="辯論輪次,預設 1")
    p.add_argument("--background", action="store_true", help="背景跑,立刻回傳 job id")
    p.add_argument("--model", help="預設用 Codex 當前預設模型")
    p.add_argument("--effort", choices=["none", "minimal", "low", "medium", "high", "xhigh"])
    p.add_argument("--extra", help="附加一條額外指示")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("status", help="查 Codex job 狀態")
    p.add_argument("job_id", nargs="?")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
