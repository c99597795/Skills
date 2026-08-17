---
name: stock-analysis
description: 對個股跑一輪多角色投資分析 — 技術面/基本面/新聞/情緒四位分析師,多空辯論,風控三方交鋒,最後給出五級評等與進出場計畫。支援台股(.TW/.TWO)、美股、港股等 Yahoo Finance 涵蓋的市場。當使用者要求分析某檔股票、評估要不要買、做投資決策、或追蹤觀察清單時使用。
---

# 個股多角色分析

這是 TradingAgents 多 agent 框架的流程移植版。原專案靠 LLM API 驅動 8 個 agent;
這裡由你(Claude Code)依序扮演全部角色,資料由純 Python 腳本取得。**不需要任何
LLM API 金鑰**。

## 為什麼要照流程走

價值來自**角色之間真正的對抗**,不是來自一份四平八穩的綜合報告。扮演多方時就
全力做多,扮演空方時就全力做空,不要預先幫下一個角色留退路。分析師階段先把
事實釘死,辯論階段才允許詮釋 — 順序顛倒的話,論點會去挑選事實。

角色設定全文在 `reference/agents.md`。開始前先讀它。

## 分工:一部分角色外包給 Codex

你一個人分飾全部角色時,前面角色的推理對後面角色一定是可見的,對抗性會被稀釋。
所以**對手方角色交給 Codex 跑**(透過 codex-plugin-cc),它只看得到寫進檔案的
內容,看不到你的思路 — 對抗就變回真的,而且是跨模型的。

| 階段 | 誰跑 | 為什麼 |
|---|---|---|
| Phase 1 四位分析師 | **Codex ×4 並行** | 彼此獨立、資料量大,並行最划算 |
| Phase 2 多方 | 你 | 你要親自建立論點才有東西被打 |
| Phase 2 空方 | **Codex** | 真正獨立的反方,不是你自己讓步 |
| Phase 3 研究經理 | 你 | 需要同時看見雙方 |
| Phase 4 交易員 | 你 | |
| Phase 5 激進派 / 保守派 | **Codex ×2 並行** | 兩個極端立場交給外部,壓力才夠 |
| Phase 5 中立派 | 你 | 你來收斂兩個極端 |
| Phase 6 投組經理 | 你 | 最終決策要交到使用者手上 |

指令一律是:

```bash
python3 $SKILL/scripts/delegate.py run <角色> <TICKER> <DATE> [--background] [--round N]
python3 $SKILL/scripts/delegate.py status [job-id] [--wait]
```

角色代號:`market` `fundamentals` `news` `sentiment` `bull` `bear`
`aggressive` `conservative` `neutral`。

所有報告集中在 `~/.stock-analysis/runs/<TICKER>_<DATE>/`。Codex 只讀得到該階段
之前的檔案(分析師只看資料包,辯論者才看得到分析報告)—— 這個隔離由
`delegate.py` 控制,不要繞過它直接餵檔案。

**你自己扮演的角色也要把成果寫進同一個資料夾**,否則 Codex 的後續角色讀不到:
`02_bull_r1.md`、`02_bull_r2.md`、`03_research_manager.md`、`04_trader.md`、
`05_neutral.md`、`06_portfolio_manager.md`。

Codex 沒裝或沒登入時,`delegate.py` 會直接報錯。這時退回你一人分飾全部角色,
但要在最後的交付裡註明「未使用外部對手方,對抗性較低」。

## 環境

腳本借用 TradingAgents 的資料層,必須用它的 venv 執行:

```bash
PY=~/TradingAgents/.venv/bin/python
SKILL=~/.claude/skills/stock-analysis
```

`delegate.py` 是例外 — 它不碰資料層,用系統 `python3` 跑就好。

若 `~/TradingAgents` 不存在,先 clone 並用 uv 建 venv(見本檔末「重建環境」)。

---

## Phase 0 — 取資料(純 Python,無 LLM)

```bash
$PY $SKILL/scripts/fetch_data.py <TICKER> --date <YYYY-MM-DD>
```

代碼用 Yahoo Finance 的交易所後綴:台股上市 `.TW`、上櫃 `.TWO`、美股無後綴、
港股 `.HK`、日股 `.T`、韓股 `.KS`。**上市上櫃搞混會直接 404** — 例如群聯是
`8299.TWO` 不是 `8299.TW`。

輸出寫到 `~/.stock-analysis/bundles/<TICKER>_<DATE>.md`,約 50KB。讀進來。

接著看有沒有過去的決策紀錄:

```bash
$PY $SKILL/scripts/memory.py review --ticker <TICKER>
```

有結果就帶進 Phase 6。

**資料包最後的「資料品質」區塊是硬約束。** 它列出哪些來源是空的。空的來源不
准腦補 — 缺什麼就在報告裡說缺什麼,並據此下修 confidence。

---

## Phase 1 — 四位分析師(外包給 Codex,並行)

四個角色互相獨立,一次全部丟出去:

```bash
for r in market fundamentals news sentiment; do
  python3 $SKILL/scripts/delegate.py run $r <TICKER> <DATE> --background
done
python3 $SKILL/scripts/delegate.py status
```

一份報告約 60–120 秒。四份並行的總時間接近最慢的那一份。等 `status` 顯示全部
completed(或四個 `01_*.md` 都出現)後,把四份讀進來。

各角色的職責與紀律要求在 `reference/agents.md`,`delegate.py` 會自動帶給 Codex:

1. **技術面** — 從指標清單挑至多 8 個互補指標。精確數值一律以「驗證快照」為準。
2. **基本面** — 財報、財務體質、估值、歷史趨勢。
3. **新聞** — 個股新聞 + 總體環境。每個論點都要對應到資料包裡的具體標題。
4. **情緒** — 情緒等級 + 0–10 分數 + 信心水準。

**讀完要驗收,不要照單全收**:抽查報告裡的關鍵數字是否真的出現在資料包的
「驗證快照」裡。對不上的數字直接在後續階段標為不可用,必要時重跑該角色。

> 跑台股時情緒這一路幾乎必然只有新聞可用(StockTwits 不收台股代碼、Reddit 討論
> 近乎零),信心水準標 `Low` 並說明原因。這不是失敗,是誠實標記。

---

## Phase 2 — 多空辯論(你 vs Codex)

**預設 2 輪**,嚴格照順序,因為每一輪都要看得到對方剛講完的話:

1. 你扮演多方寫第一輪 → 存成 `runs/<TICKER>_<DATE>/02_bull_r1.md`
2. `delegate.py run bear <TICKER> <DATE> --round 1`(前景等它跑完)
3. 讀 `02_bear_r1.md`,你扮演多方寫第二輪 → `02_bull_r2.md`,**必須逐點回應空方**
4. `delegate.py run bear <TICKER> <DATE> --round 2`

- 多方:成長潛力、競爭優勢、正面指標,並反駁空方。
- 空方:風險挑戰、競爭弱點、負面指標,並反駁多方。

用對話語氣直接交鋒,不要只條列數據。

> 空方是外部模型,它可能提出你沒想到的角度,也可能講錯。**講錯的地方要在
> Phase 3 明講哪裡錯**,不要因為它是「獨立意見」就照單全收 — 那等於把判斷
> 外包掉。

---

## Phase 3 — 研究經理(你)

評估辯論,產出五級評等(Buy / Overweight / Hold / Underweight / Sell)與投資計畫。

**只要有一方論點明顯較強就要表態。Hold 保留給真正勢均力敵的情況** — 不要用
Hold 迴避判斷。

寫進 `03_research_manager.md`。

---

## Phase 4 — 交易員(你)

把投資計畫轉成具體交易提案:Buy / Hold / Sell,加上進場價、停損價、部位大小。

寫進 `04_trader.md`。**這兩個檔案是 Phase 5 的輸入,沒寫檔 Codex 就看不到。**

---

## Phase 5 — 風控三方辯論

兩個極端立場並行外包,你收尾:

```bash
for r in aggressive conservative; do
  python3 $SKILL/scripts/delegate.py run $r <TICKER> <DATE> --background
done
python3 $SKILL/scripts/delegate.py status
```

兩份都回來後,你扮演中立派,實際回應兩邊的具體論點(不是各打五十大板),
寫進 `05_neutral.md`。**預設 1 輪。**

---

## Phase 6 — 投資組合經理(你)

綜合風控辯論,給出最終五級評等、摘要、投資論點、目標價、時間框架。
寫進 `06_portfolio_manager.md`。

若 Phase 0 有取得過去決策紀錄,必須納入:方向錯誤的要檢討當時論點哪裡站不住。

**這一步允許推翻交易員和研究經理的結論**,但要說明為什麼。

---

## Phase 7 — 記錄決策

```bash
$PY $SKILL/scripts/memory.py log <TICKER> \
  --date <YYYY-MM-DD> --rating <評級> \
  --thesis "<核心論點一句話>" --horizon "<時間框架>"
```

下次分析同一檔時,`review` 會回算實際報酬與相對大盤的 alpha,形成閉環。
台股/上櫃對 `^TWII`、韓股對 `^KS11`、美股對 `SPY`。

---

## 交付

過程中的各階段報告直接輸出給使用者。全部跑完後給一段收斂的結論:評等、核心
理由、具體進出場價位、以及**這次分析最不確定的地方**。

多檔標的時,最後補一張彙總表(標的 / 評等 / 一句話理由)。

## 批次跑觀察清單

清單維護在 `~/TradingAgents/watchlist.py` 的 `WATCHLIST`,分 `core` /
`memory_tw` / `memory_us` 三組。要看清單內容:

```bash
cd ~/TradingAgents && .venv/bin/python watchlist.py --list
```

批次分析時逐檔跑完整流程。**檔數多時先問使用者要跑哪一組** — 一檔完整流程
的產出量不小。

## 重建環境

```bash
git clone https://github.com/TauricResearch/TradingAgents.git ~/TradingAgents
cd ~/TradingAgents
curl -LsSf https://astral.sh/uv/install.sh | sh   # 若無 uv
~/.local/bin/uv venv --python 3.12 && ~/.local/bin/uv pip install .
```

系統 Python 3.14 缺 `ensurepip`,無法直接建 venv,所以走 uv。
本流程只用到 `tradingagents.dataflows`,不需要設定任何 LLM 金鑰。

外包角色需要 Codex plugin(用 ChatGPT 訂閱額度,不需 API key):

```
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/codex:setup          # 檢查 Codex 是否就緒;沒登入就 !codex login
```

`delegate.py` 直接呼叫 plugin 的 `codex-companion.mjs`,所以 plugin 只要「安裝在
本機」就能用,不需要每次 session 都載入。Node 需 18.18+;WSL 上 node 由 nvm 管理,
`delegate.py` 會自己去 `~/.nvm/versions/node/*/bin/node` 找。
