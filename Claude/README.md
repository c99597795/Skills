# Claude Stock Analysis

一個給 Claude Code 用的 Skill,把 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 的多 agent 投資分析流程移植成「Claude 自己扮演角色 + 純 Python 取資料」的版本。**不需要任何 LLM API 金鑰。**

## Included

- `skills/stock-analysis/SKILL.md` — 六個 Phase 的完整流程:四位分析師 → 多空辯論 → 研究經理 → 交易員 → 風控三方交鋒 → 投組經理。
- `skills/stock-analysis/reference/agents.md` — 九個角色的人設與紀律要求,`delegate.py` 會自動帶給外包角色。
- `skills/stock-analysis/scripts/fetch_data.py` — 取價量、財報、新聞、情緒,輸出一份資料包 Markdown。
- `skills/stock-analysis/scripts/delegate.py` — 把對手方角色外包給 Codex 跑,並控制每個階段看得到哪些檔案。
- `skills/stock-analysis/scripts/memory.py` — 記錄過去決策,下次分析同一檔時回算實際報酬與相對大盤的 alpha。

支援 Yahoo Finance 涵蓋的市場:台股上市 `.TW`、上櫃 `.TWO`、美股無後綴、港股 `.HK`、日股 `.T`、韓股 `.KS`。

## Install

```bash
cp -r Claude/skills/stock-analysis ~/.claude/skills/
```

### 資料層

腳本借用 TradingAgents 的 `tradingagents.dataflows`,必須用它的 venv 執行:

```bash
git clone https://github.com/TauricResearch/TradingAgents.git ~/TradingAgents
cd ~/TradingAgents
curl -LsSf https://astral.sh/uv/install.sh | sh   # 若無 uv
~/.local/bin/uv venv --python 3.12 && ~/.local/bin/uv pip install .
```

走 uv 是因為系統 Python 3.14 缺 `ensurepip`,無法直接建 venv。這個流程只用到 `dataflows`,不需要設定任何 LLM 金鑰。

### 外包角色(選用)

對手方角色交給 Codex 跑,它只看得到寫進檔案的內容、看不到 Claude 的思路,對抗性才是真的。用 ChatGPT 訂閱額度,不需 API key:

```
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/codex:setup          # 檢查 Codex 是否就緒;沒登入就 !codex login
```

Node 需 18.18+。WSL 上 node 由 nvm 管理時,`delegate.py` 會自己去 `~/.nvm/versions/node/*/bin/node` 找。

沒裝 Codex 也能跑 — Claude 一人分飾全部角色,但交付時會註明「未使用外部對手方,對抗性較低」。

## Use

直接講就好,Skill 會自己觸發:

```text
幫我分析 2330.TW
8299.TWO 現在可以進場嗎?
```

## Validate a run

單獨取一次資料包,確認資料層是通的:

```bash
~/TradingAgents/.venv/bin/python ~/.claude/skills/stock-analysis/scripts/fetch_data.py 2330.TW --date 2026-08-18
```

輸出寫到 `~/.stock-analysis/bundles/<TICKER>_<DATE>.md`,約 50KB。資料包最後的「資料品質」區塊會列出哪些來源是空的 — 空的來源不准腦補,缺什麼就在報告裡說缺什麼。

檢查外包管線:

```bash
python3 ~/.claude/skills/stock-analysis/scripts/delegate.py status
```

分析報告集中在 `~/.stock-analysis/runs/<TICKER>_<DATE>/`。

## Disclaimer

這是一套分析流程,不是投資建議。輸出的評等與進出場價位來自公開資料與模型推理,可能有錯。實際下單前請自行查證。
