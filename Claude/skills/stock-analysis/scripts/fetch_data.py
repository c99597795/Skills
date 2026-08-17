"""收集單一標的的全部分析資料,輸出成一份 markdown bundle。

純資料層,不呼叫任何 LLM。借用 TradingAgents 已安裝的 dataflows
(yfinance / stockstats / FRED),因此必須用它的 venv 執行:

    ~/TradingAgents/.venv/bin/python fetch_data.py 2330.TW --date 2026-08-12

輸出寫到 ~/.stock-analysis/bundles/<TICKER>_<DATE>.md。
"""

import argparse
import datetime
import io
import logging
import pathlib
import sys
from contextlib import redirect_stderr

# dataflows 的失敗都走 logging.warning,收進 buffer 後統一列在 bundle 的資料品質區塊,
# 讓分析階段看得到哪幾路是空的 — 這是判斷 confidence 的依據。
_LOG = io.StringIO()
logging.basicConfig(stream=_LOG, level=logging.WARNING, format="%(levelname)s %(message)s")

from tradingagents.dataflows.interface import route_to_vendor  # noqa: E402
# 驗證快照不走 vendor routing,是直接算的確定性函式。
from tradingagents.dataflows.market_data_validator import (  # noqa: E402
    build_verified_market_snapshot,
)

OUT_DIR = pathlib.Path.home() / ".stock-analysis" / "bundles"

# 對應 market_analyst 系統提示裡的指標清單。資料是免費的,全部抓下來,
# 由分析階段決定引用哪些,不必像原專案那樣為了省 token 先挑 8 個。
INDICATORS = [
    "close_10_ema", "close_50_sma", "close_200_sma",
    "macd", "macds", "macdh",
    "rsi", "atr",
    "boll", "boll_ub", "boll_lb",
    "vwma",
]


# 上游查無資料時不是回空字串,而是回一段人話。這些要算「空」,否則資料品質區塊
# 會報一切正常,分析師就失去了下修 confidence 的依據。ETF 幾乎必中這幾條。
NO_DATA_MARKERS = (
    "NO_DATA_AVAILABLE",
    "No news found",
    "No data available",
    "no usable market data",
)


def call(label, fn, *args):
    """呼叫一個 dataflow,把失敗轉成可見的佔位字串而不是中斷整份 bundle。"""
    try:
        out = fn(*args)
        if not out or not str(out).strip():
            return f"<{label} 無資料>", False
        text = str(out)
        head = text.strip()[:200].lower()
        if any(m.lower() in head for m in NO_DATA_MARKERS):
            return text, False
        return text, True
    except Exception as exc:
        return f"<{label} 取得失敗: {type(exc).__name__}: {exc}>", False


def section(title, body):
    return f"\n## {title}\n\n{body.strip()}\n"


def main():
    ap = argparse.ArgumentParser(description="收集標的分析資料 (無 LLM)")
    ap.add_argument("ticker", help="Yahoo Finance 代碼,例如 2330.TW / 8299.TWO / MU")
    ap.add_argument("--date", default=datetime.date.today().isoformat(),
                    help="分析基準日 YYYY-MM-DD,預設今天")
    ap.add_argument("--price-days", type=int, default=90, help="OHLCV 回溯天數")
    ap.add_argument("--indicator-days", type=int, default=30, help="指標回溯天數")
    ap.add_argument("--news-days", type=int, default=7, help="新聞回溯天數")
    ap.add_argument("--out", help="輸出路徑,預設 ~/.stock-analysis/bundles/")
    args = ap.parse_args()

    ticker = args.ticker.strip().upper()
    end = datetime.date.fromisoformat(args.date)
    price_start = (end - datetime.timedelta(days=args.price_days)).isoformat()
    news_start = (end - datetime.timedelta(days=args.news_days)).isoformat()
    date = end.isoformat()

    ok, failed = [], []

    def track(label, body, success):
        (ok if success else failed).append(label)
        return body

    parts = [
        f"# 資料包 — {ticker} @ {date}",
        "",
        f"產生時間: {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"價格區間: {price_start} → {date} | 指標回溯: {args.indicator_days} 天 "
        f"| 新聞回溯: {args.news_days} 天",
    ]

    # ── 價格 ────────────────────────────────────────────────────────────
    body, s = call("OHLCV", route_to_vendor, "get_stock_data", ticker, price_start, date)
    parts.append(section("OHLCV 日線", track("OHLCV", body, s)))

    # ── 技術指標 ────────────────────────────────────────────────────────
    ind_blocks = []
    for ind in INDICATORS:
        body, s = call(ind, route_to_vendor, "get_indicators", ticker, ind, date, args.indicator_days)
        ind_blocks.append(body)
        (ok if s else failed).append(f"指標:{ind}")
    parts.append(section("技術指標", "\n\n".join(ind_blocks)))

    # ── 驗證快照:任何精確價位/指標數值以此為準 ──────────────────────────
    body, s = call("驗證快照", build_verified_market_snapshot, ticker, date, args.indicator_days)
    parts.append(section("驗證快照 (精確數值的唯一真實來源)", track("驗證快照", body, s)))

    # ── 基本面 ──────────────────────────────────────────────────────────
    body, s = call("基本面總覽", route_to_vendor, "get_fundamentals", ticker, date)
    parts.append(section("基本面總覽", track("基本面總覽", body, s)))

    for label, method in [("損益表", "get_income_statement"),
                          ("資產負債表", "get_balance_sheet"),
                          ("現金流量表", "get_cashflow")]:
        body, s = call(label, route_to_vendor, method, ticker, "quarterly", date)
        parts.append(section(f"{label} (季)", track(label, body, s)))

    # ── 新聞 ────────────────────────────────────────────────────────────
    body, s = call("個股新聞", route_to_vendor, "get_news", ticker, news_start, date)
    parts.append(section("個股新聞", track("個股新聞", body, s)))

    body, s = call("總體新聞", route_to_vendor, "get_global_news", date, args.news_days, 10)
    parts.append(section("總體/宏觀新聞", track("總體新聞", body, s)))

    # ── 資料品質 ────────────────────────────────────────────────────────
    warnings = _LOG.getvalue().strip()
    quality = [
        f"**成功**: {len(ok)} 項 | **失敗/空**: {len(failed)} 項",
        "",
    ]
    if failed:
        quality.append("失敗或無資料的來源 — 分析時必須據此下修 confidence,不得腦補:")
        quality.extend(f"- {f}" for f in failed)
        quality.append("")
    if warnings:
        quality.append("底層警告:\n```\n" + warnings[:3000] + "\n```")
    parts.append(section("資料品質", "\n".join(quality)))

    out_path = pathlib.Path(args.out) if args.out else OUT_DIR / f"{ticker}_{date}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")

    print(f"bundle: {out_path}")
    print(f"大小: {out_path.stat().st_size:,} bytes")
    print(f"成功 {len(ok)} 項, 失敗/空 {len(failed)} 項")
    if failed:
        print("缺: " + ", ".join(failed))


if __name__ == "__main__":
    with redirect_stderr(_LOG):
        main()
