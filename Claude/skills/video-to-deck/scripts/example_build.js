// example_build.js — a runnable template: copy it to your work folder as build.js and replace the content.
//
//   node example_build.js OUT.pptx [SCRIPT.txt]
//
// Pattern worth keeping: ONE source object (SCRIPT) holds each slide's title, video time range and
// speaking script. The deck's titles, its speaker notes and the script .txt are all generated from it,
// so they can never drift apart.
const path = require("path");
const { createDeck, notesFor, writeScriptTxt } = require(path.join(__dirname, "deck_kit.js"));

const SCRIPT = {
  title: { title: "範例影片：快取是什麼？", time: "00:00–00:05", script: "今天用三頁說明快取：為什麼需要、怎麼運作、有什麼代價。" },
  why: { title: "為什麼需要快取", time: "00:05–01:10", script: "每次查詢都打到資料庫，資料庫壓力大、回應慢。大部分查詢其實重複，所以把結果先存在記憶體，下次直接回傳。" },
  flow: { title: "讀取流程：先查快取，再查資料庫", time: "01:10–02:00", script: "請求先查快取；命中就直接回傳，沒命中才查資料庫，並把結果寫回快取。" },
  recap: { title: "重點回顧", time: "02:00–02:20", script: "快取用記憶體換速度；流程是先快取、後資料庫、再回填。" },
};
const ORDER = ["title", "why", "flow", "recap"];

const kit = createDeck({ title: "快取入門", footer: "資料來源：範例影片", font: "Microsoft JhengHei" });
const { C, text, box, chip, badge, flowArrow, chain, callout, titleSlide, content, closing } = kit;
const N = (k) => notesFor(SCRIPT[k]);

// 1. title slide: nested boxes on the right as the "map" of the talk
{
  const e = SCRIPT.title;
  const s = titleSlide({ section: "開場", kicker: "CACHE 101", title: e.title, subtitle: "從問題出發，三頁看懂", source: "內容整理自範例影片", notes: N("title") });
  box(s, 8.0, 1.6, 4.75, 4.2, { fill: C.accent1, transparency: 60, r: 0.18 });
  text(s, "應用程式", { x: 8.2, y: 1.7, w: 4.3, h: 0.4, fontSize: 13, bold: true, color: C.background1, valign: "middle" });
  ["快取（記憶體）", "資料庫（磁碟）"].forEach((t, i) => chip(s, t, 8.4, 2.5 + i * 1.3, 3.95, 0.9, { fill: i ? C.accent4 : C.accent2, color: C.text2, fontSize: 16 }));
}

// 2. cause → effect chain on the left, a picture of the same idea on the right
{
  const s = content("內容", "PART 1｜為什麼", SCRIPT.why.title, N("why"));
  chain(s, [
    ["每次查詢都打到資料庫", "p"],
    ["資料庫壓力大、回應慢", "p"],
    ["觀察：大部分查詢其實是重複的", "n"],
    ["把查過的結果先存在記憶體", "s"],
    ["下次相同查詢直接回傳，不必再查資料庫", "r"],
  ], 0.6, 1.95, 6.0);
  box(s, 7.1, 1.95, 5.63, 2.1, { fill: C.accent3, transparency: 88 });
  text(s, "沒有快取：全部打到資料庫", { x: 7.3, y: 2.02, w: 5.2, h: 0.36, fontSize: 13, bold: true, color: C.accent3, valign: "middle" });
  chip(s, "資料庫：壓力大", 8.6, 2.75, 2.6, 0.75, { fill: C.accent3 });
  box(s, 7.1, 4.25, 5.63, 2.45);
  text(s, "有快取：重複查詢由記憶體回應", { x: 7.3, y: 4.33, w: 5.2, h: 0.36, fontSize: 13, bold: true, color: C.accent1, valign: "middle" });
  chip(s, "快取", 7.6, 5.1, 2.2, 0.75, {});
  chip(s, "資料庫", 10.0, 5.1, 2.2, 0.75, { fill: C.accent6, color: C.text2 });
}

// 3. numbered process flow
{
  const s = content("內容", "PART 2｜怎麼運作", SCRIPT.flow.title, N("flow"));
  const steps = [["查快取", "請求先到快取查詢"], ["命中？", "命中就直接回傳結果"], ["查資料庫", "沒命中才查資料庫"], ["回填", "把結果寫回快取，再回傳"]];
  steps.forEach(([h, b], i) => {
    const x = 0.6 + i * 3.11;
    box(s, x, 1.9, 2.8, 2.6);
    badge(s, i + 1, x + 0.25, 2.15, 0.5);
    text(s, h, { x: x + 0.25, y: 2.8, w: 2.35, h: 0.5, fontSize: 17, bold: true, color: C.text2, valign: "middle" });
    text(s, b, { x: x + 0.25, y: 3.35, w: 2.35, h: 1.0, fontSize: 14 });
    if (i < 3) flowArrow(s, x + 2.835, 3.03);
  });
  callout(s, [{ text: "先快取、後資料庫、再回填", options: { bold: true } }], 0.6, 4.9, 12.13, 0.75, { fontSize: 18 });
}

// 4. dark closing slide
{
  const s = closing("總結", "重點回顧", SCRIPT.recap.title, N("recap"));
  [["為什麼", "重複查詢很多，資料庫又慢"], ["怎麼做", "把結果存進記憶體"], ["流程", "先快取、後資料庫、再回填"]].forEach(([h, b], i) => {
    const x = 0.6 + i * 4.15;
    box(s, x, 1.9, 3.83, 2.2, { fill: C.background1, transparency: 91 });
    text(s, h, { x: x + 0.3, y: 2.1, w: 3.2, h: 0.45, fontSize: 18, bold: true, color: C.accent2, valign: "middle" });
    text(s, b, { x: x + 0.3, y: 2.7, w: 3.25, h: 1.2, fontSize: 14, color: C.accent6 });
  });
}

(async () => {
  const out = process.argv[2] || "example.pptx";
  await kit.save(out);
  console.log("wrote", out);
  if (process.argv[3]) console.log("wrote", writeScriptTxt(process.argv[3], ORDER.map((k) => SCRIPT[k]), ["範例｜逐頁講稿", "對應簡報：" + path.basename(out)]));
})().catch((e) => { console.error(e); process.exit(1); });
