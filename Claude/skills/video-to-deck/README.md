# Video to Deck

一個給 Claude Code 用的 Skill:給它一部講解型影片(教學、技術講解、課程、演講),它會產出三樣互相對得上時間的東西。

1. **字幕文字檔** — 每句帶 `[mm:ss]` 時間戳;字幕語言和你的語言不同(簡↔繁)時再轉一份。
2. **教學型簡報 `.pptx`** — 照影片講解順序,每頁把「問題 → 原因 → 解法」講完整,備忘稿裡有講稿。
3. **逐頁講稿 `.txt`** — 每頁的對應影片時間 + 可直接照念的講稿。

## Included

- `SKILL.md` — 完整流程:探測 → 取得逐字內容 → 字幕檔 → 規劃內容(含覆蓋檢查)→ 建簡報與講稿 → 檢查 → 交付,以及踩過的坑。
- `scripts/video_sheets.py` — 探測畫面、抽出燒錄字幕的長條圖與關鍵畫面縮圖(ffmpeg + Pillow)。
- `scripts/transcribe.py` — 影片沒有燒錄字幕時,用 faster-whisper 語音轉文字(選用)。
- `scripts/convert_chinese.py` — 用 OpenCC 做簡繁轉換,含台灣用語(`s2twp`)。
- `scripts/deck_kit.js` — pptxgenjs 簡報零件:三種版型、因果鏈、標籤、箭頭,以及中文字型與配色修正。
- `scripts/example_build.js` — 可直接執行的範例,當新簡報的起點。
- `scripts/render_pptx.ps1` — 用 Windows 上已安裝的 PowerPoint 把投影片轉成 PNG,做視覺檢查。

## Install

```bash
cp -r Claude/skills/video-to-deck ~/.claude/skills/
```

需要:`ffmpeg`/`ffprobe`、Python 3 + Pillow、Node.js。簡報的設計規範與驗證依賴 Claude 內建的 `pptx` skill。`transcribe.py` 與 `convert_chinese.py` 需要另外在 venv 裡裝 `faster-whisper`、`opencc-python-reimplemented`。

## Use

直接講就好,Skill 會自己觸發:

```text
依據這部影片做一份 PPT:C:\Users\me\Downloads\lecture.mp4
把這部影片的字幕轉成文字檔,並告訴我每一頁 PPT 要怎麼講
```

## Notes

- 有燒錄字幕的影片最準(直接讀畫面上的字);沒有字幕才用語音轉文字,第一次要下載模型(`small` 約 460 MB)。
- 簡報偏向「教學、可以拿來講」而不是摘要:影片解釋過的原因都會放進簡報,密集的講解約每分鐘 2 頁。
- 簡報的檢查流程在 Windows 上需要 PowerPoint(`render_pptx.ps1`);其他平台請改用 pptx skill 的 LibreOffice 轉圖流程。
