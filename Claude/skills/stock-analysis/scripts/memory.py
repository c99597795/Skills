"""決策記錄與實際報酬回算 — 對應原專案的 reflection 層。

原專案在每次分析後把決策寫進 memory log,下次分析同一檔時回頭抓實際報酬
(含相對大盤的 alpha),再把過去的決策與結果注入 Portfolio Manager 的
context。這支腳本用純 Python 複製那個機制,不需要 LLM。

    log     記一筆新決策
    review  回算所有未結算決策的實際報酬,輸出可注入分析的 context

台股/上櫃對 ^TWII、韓股對 ^KS11、美股對 SPY — 原專案的 benchmark_map
沒有台灣,會錯拿 SPY 當台股基準,這裡補上。
"""

import argparse
import datetime
import json
import pathlib
import sys

LOG_PATH = pathlib.Path.home() / ".stock-analysis" / "decisions.jsonl"

BENCHMARKS = [
    (".TWO", "^TWII"),   # 上櫃,櫃買指數 Yahoo 無提供,退用加權
    (".TW", "^TWII"),
    (".KS", "^KS11"),
    (".HK", "^HSI"),
    (".T", "^N225"),
    (".SS", "000001.SS"),
    (".SZ", "399001.SZ"),
]
DEFAULT_BENCHMARK = "SPY"

VALID_RATINGS = {"Buy", "Overweight", "Hold", "Underweight", "Sell"}


def benchmark_for(ticker: str) -> str:
    t = ticker.upper()
    for suffix, bench in BENCHMARKS:
        if t.endswith(suffix):
            return bench
    return DEFAULT_BENCHMARK


def load() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    return [json.loads(line) for line in LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def cmd_log(args):
    if args.rating not in VALID_RATINGS:
        sys.exit(f"rating 必須是 {'/'.join(sorted(VALID_RATINGS))} 之一,收到 {args.rating!r}")

    entry = {
        "ticker": args.ticker.upper(),
        "date": args.date,
        "rating": args.rating,
        "thesis": args.thesis,
        "price_target": args.price_target,
        "horizon": args.horizon,
        "benchmark": benchmark_for(args.ticker),
        "logged_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "resolved": False,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"已記錄: {entry['ticker']} {entry['date']} {entry['rating']} (基準 {entry['benchmark']})")


def returns(ticker: str, start: str, holding_days: int):
    """抓 start 之後 holding_days 個交易日的報酬率。資料不足回 None。"""
    import warnings

    import yfinance as yf
    warnings.filterwarnings("ignore")

    begin = datetime.date.fromisoformat(start)
    # 多抓一些日曆天以涵蓋假日
    end = begin + datetime.timedelta(days=holding_days * 2 + 10)
    try:
        h = yf.Ticker(ticker).history(start=start, end=end.isoformat())
    except Exception:
        return None
    if h.empty or len(h) < 2:
        return None
    closes = h["Close"].tolist()
    entry = closes[0]
    exit_idx = min(holding_days, len(closes) - 1)
    if entry == 0:
        return None
    return (closes[exit_idx] - entry) / entry * 100, exit_idx


def cmd_review(args):
    entries = load()
    if not entries:
        print("尚無決策紀錄。")
        return

    target = [e for e in entries if not args.ticker or e["ticker"] == args.ticker.upper()]
    if not target:
        print(f"沒有 {args.ticker} 的紀錄。")
        return

    lines = []
    for e in target:
        r = returns(e["ticker"], e["date"], args.holding_days)
        b = returns(e["benchmark"], e["date"], args.holding_days)
        if r is None:
            lines.append(f"- {e['date']} {e['ticker']} **{e['rating']}** — 尚未有足夠交易日可結算")
            continue
        raw, days = r
        if b is None:
            lines.append(
                f"- {e['date']} {e['ticker']} **{e['rating']}** — {days} 個交易日後 {raw:+.2f}%"
                f" (基準 {e['benchmark']} 無資料)"
            )
            continue
        bench_raw, _ = b
        alpha = raw - bench_raw
        verdict = "✓ 方向正確" if _direction_ok(e["rating"], alpha) else "✗ 方向錯誤"
        lines.append(
            f"- {e['date']} {e['ticker']} **{e['rating']}** — {days} 個交易日後 {raw:+.2f}%,"
            f" 基準 {e['benchmark']} {bench_raw:+.2f}%, **alpha {alpha:+.2f}%** {verdict}\n"
            f"  - 當時論點: {e.get('thesis', '')[:200]}"
        )

    print("## 過去決策與實際結果\n")
    print("\n".join(lines))
    print(
        "\n把上面這段當作 Portfolio Manager 的 lessons context:方向錯誤的決策要檢討"
        "當時的論點哪裡站不住,方向正確的要確認是靠論點還是靠運氣。"
    )


def _direction_ok(rating: str, alpha: float) -> bool:
    """看漲類決策要正 alpha,看跌類要負 alpha,Hold 不評分。"""
    if rating in {"Buy", "Overweight"}:
        return alpha > 0
    if rating in {"Sell", "Underweight"}:
        return alpha < 0
    return True


def main():
    ap = argparse.ArgumentParser(description="決策記錄與回顧")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("log", help="記一筆決策")
    p.add_argument("ticker")
    p.add_argument("--date", required=True, help="決策日 YYYY-MM-DD")
    p.add_argument("--rating", required=True, help="Buy/Overweight/Hold/Underweight/Sell")
    p.add_argument("--thesis", default="", help="核心論點一句話")
    p.add_argument("--price-target", type=float, default=None)
    p.add_argument("--horizon", default="")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("review", help="回算實際報酬")
    p.add_argument("--ticker", help="只看單一標的")
    p.add_argument("--holding-days", type=int, default=5, help="持有交易日數,預設 5")
    p.set_defaults(func=cmd_review)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
