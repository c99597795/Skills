// deck_kit.js — pptxgenjs helpers for explanatory decks built from a video (16:9 wide, 13.333 x 7.5 in).
//
//   const kit = require("<skill>/scripts/deck_kit.js").createDeck({ title, font, theme, footer });
//   const s = kit.content("Part 1", "PART 1｜…", "Slide title", "speaker notes");
//   kit.chain(s, [["problem", "p"], ["fix", "s"], ["result", "r"]], 0.6, 1.95, 6.0);
//   await kit.save("deck.pptx");
//
// Run node from a folder whose node_modules has pptxgenjs (npm install pptxgenjs); the kit resolves
// it from the current directory and from the main script's folder, so it need not be copied.
// Everything here was learned the hard way — see the comments marked "why".
const fs = require("fs");

const DEFAULT_THEME = {
  name: "Deck Teal",
  colors: {
    dk1: "18292E", lt1: "FFFFFF", dk2: "0D3B42", lt2: "EDF3F2",
    accent1: "0F7B7F", accent2: "F3B12B", accent3: "C4513B", accent4: "4DB6A6",
    accent5: "5E7A82", accent6: "CFE5E1", hlink: "0F7B7F", folHlink: "5E7A82",
  },
};
const SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];

function resolveFrom(name) {
  const paths = [process.cwd(), ...(require.main ? require.main.paths : [])];
  try { return require.resolve(name, { paths }); } catch {
    throw new Error(`${name} not found from ${process.cwd()}. Run "npm install pptxgenjs" in the folder you run node from.`);
  }
}

function createDeck(opt = {}) {
  const pptxPath = resolveFrom("pptxgenjs");
  const pptxgen = require(pptxPath);
  const JSZip = require(require.resolve("jszip", { paths: [pptxPath] }));
  const THEME = opt.theme || DEFAULT_THEME;
  const FONT = opt.font || "Microsoft JhengHei"; // Traditional Chinese; "Microsoft YaHei" for Simplified, "Calibri" for Latin
  const LANG = opt.lang || "zh-TW";
  const FOOTER = opt.footer || "";

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  if (opt.title) pres.title = opt.title;
  if (opt.subject) pres.subject = opt.subject;
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  const C = pres.SchemeColor; // C.text1/text2 = dk1/dk2, C.background1/2 = lt1/lt2, C.accent1..6
  const SH = pres.shapes;
  let uid = 0;
  const nm = (s) => `${s} ${++uid}`;

  // ---- primitives ----
  // why margin is a single number everywhere: pptxgenjs reads a margin ARRAY as [left, right, bottom, top],
  // so [0, 8, 0, 8] pushes text down instead of padding the sides.
  function text(slide, t, o) {
    slide.addText(t, { isTextBox: true, lang: LANG, margin: 0, valign: "top", color: C.text1, fontSize: 14, ...o, objectName: o.objectName || nm("Text") });
  }
  function box(slide, x, y, w, h, o = {}) {
    slide.addShape(SH.ROUNDED_RECTANGLE, {
      x, y, w, h, rectRadius: o.r ?? 0.12,
      fill: { color: o.fill || C.background2, ...(o.transparency ? { transparency: o.transparency } : {}) },
      line: o.line ? { ...o.line } : { type: "none" }, objectName: o.name || nm("Card"),
    });
  }
  // A filled rounded label. `t` may be a string or an array of runs ({ text, options }).
  function chip(slide, t, x, y, w, h, o = {}) {
    slide.addText(t, {
      isTextBox: true, lang: LANG, shape: SH.ROUNDED_RECTANGLE, rectRadius: o.r ?? 0.1, x, y, w, h,
      fill: { color: o.fill || C.accent1, ...(o.transparency ? { transparency: o.transparency } : {}) },
      line: o.line ? { ...o.line } : { type: "none" },
      color: o.color || C.background1, fontSize: o.fontSize || 14, bold: o.bold ?? true, italic: o.italic || false,
      align: o.align || "center", valign: "middle", margin: o.margin ?? 3, objectName: o.name || nm("Chip"),
    });
  }
  function badge(slide, n, x, y, d, o = {}) {
    slide.addText(String(n), {
      isTextBox: true, shape: SH.OVAL, x, y, w: d, h: d, fill: { color: o.fill || C.accent2 }, line: { type: "none" },
      color: o.color || C.text2, fontSize: o.fontSize || 15, bold: true, align: "center", valign: "middle", margin: 0, objectName: nm("Step badge"),
    });
  }
  // Straight line from (x1,y1) to (x2,y2) in any direction; arrowhead at the end unless o.end === false.
  function line(slide, x1, y1, x2, y2, o = {}) {
    slide.addShape(SH.LINE, {
      x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1,
      line: {
        color: o.color || C.accent5, width: o.width || 1.5, dashType: o.dash || "solid",
        ...(o.end === false ? {} : { endArrowType: "triangle" }), ...(o.begin ? { beginArrowType: "triangle" } : {}),
      },
      objectName: nm(o.end === false ? "Connector" : "Arrow"),
    });
  }
  function flowArrow(slide, x, y, o = {}) {
    slide.addShape(SH.RIGHT_ARROW, { x, y, w: o.w || 0.24, h: o.h || 0.34, fill: { color: o.fill || C.accent4 }, line: { type: "none" }, objectName: nm("Flow arrow") });
  }
  function downArrow(slide, x, y, w, h, fill) {
    slide.addShape(SH.DOWN_ARROW, { x, y, w, h, fill: { color: fill || C.accent5 }, line: { type: "none" }, objectName: nm("Down arrow") });
  }

  // ---- cause → effect chain: the main device for "problem → reason → fix" ----
  // items: [text, tone, lines?]; tone p = problem (coral tint), n = neutral, s = solution (mint), r = result (dark).
  // Height is estimated from text length; pass `lines` (1, 2…) when the estimate is wrong after rendering.
  const TONE = {
    n: { fill: C.background2, color: C.text1 },
    p: { fill: C.accent3, transparency: 84, color: C.text1 },
    s: { fill: C.accent6, color: C.text2 },
    r: { fill: C.text2, color: C.background1 },
  };
  function chain(slide, items, x, y, w, o = {}) {
    const gap = o.gap ?? 0.22, fs = o.fontSize ?? 14, base = o.h ?? 0.46;
    const em = fs / 72, perLine = (w - 0.34) / em;
    let cy = y;
    items.forEach(([t, tone, fixed], i) => {
      const units = [...t].reduce((a, c) => a + (c.charCodeAt(0) < 0x2000 ? 0.55 : 1), 0);
      const lines = fixed || Math.max(1, Math.ceil(units / perLine));
      const h = base + (lines - 1) * em * 1.3;
      chip(slide, t, x, cy, w, h, { ...TONE[tone || "n"], bold: tone === "r", fontSize: fs, align: "left", margin: 8, name: nm("Chain step") });
      cy += h;
      if (i < items.length - 1) { downArrow(slide, x + 0.3, cy + 0.03, 0.22, gap - 0.06); cy += gap; }
    });
    return cy; // bottom edge, to place whatever comes next
  }
  function callout(slide, runs, x, y, w, h, o = {}) {
    chip(slide, runs, x, y, w, h, { fill: C.text2, fontSize: o.fontSize || 15, align: o.align || "center", margin: o.margin ?? 8, name: nm("Callout") });
  }
  function bullets(slide, items, o) {
    text(slide, items.map((b, i) => ({ text: b, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1 } })), { paraSpaceAfter: 8, ...o });
  }

  // ---- layouts ----
  // why align:"left" on every placeholder: pptxgenjs title placeholders inherit the master's centering otherwise.
  const ph = (name, type, o) => ({ placeholder: { options: { name, type, margin: 0, align: "left", ...o }, text: "" } });
  const foot = (color) => (FOOTER ? [{ text: { text: FOOTER, options: { x: 0.6, y: 7.0, w: 8.0, h: 0.3, fontSize: 10, color, margin: 0, valign: "middle" } } }] : []);
  pres.defineSlideMaster({
    title: "TITLE_DARK", background: { color: C.text2 },
    objects: [
      ph("kicker", "body", { x: 0.8, y: 1.5, w: 6.8, h: 0.4, fontSize: 14, bold: true, color: C.accent2, charSpacing: 2, valign: "middle" }),
      ph("title", "title", { x: 0.8, y: 2.0, w: 6.9, h: 2.3, fontSize: 40, bold: true, color: C.background1, valign: "top" }),
      ph("subtitle", "body", { x: 0.8, y: 4.5, w: 6.8, h: 0.5, fontSize: 18, color: C.accent6, valign: "top" }),
      ph("source", "body", { x: 0.8, y: 6.2, w: 6.6, h: 0.6, fontSize: 12, color: C.accent4, valign: "top" }),
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT", background: { color: C.background1 },
    objects: [
      ph("kicker", "body", { x: 0.6, y: 0.38, w: 9.0, h: 0.35, fontSize: 12, bold: true, color: C.accent1, charSpacing: 2, valign: "middle" }),
      ph("title", "title", { x: 0.6, y: 0.75, w: 12.13, h: 0.8, fontSize: 36, bold: true, color: C.text2, valign: "middle" }),
      ...foot(C.accent5),
    ],
    slideNumber: { x: 12.13, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: THEME.colors.accent5, align: "right" },
  });
  pres.defineSlideMaster({
    title: "CLOSING_DARK", background: { color: C.text2 },
    objects: [
      ph("kicker", "body", { x: 0.6, y: 0.38, w: 9.0, h: 0.35, fontSize: 12, bold: true, color: C.accent2, charSpacing: 2, valign: "middle" }),
      ph("title", "title", { x: 0.6, y: 0.75, w: 12.13, h: 0.8, fontSize: 36, bold: true, color: C.background1, valign: "middle" }),
      ...foot(C.accent4),
    ],
    slideNumber: { x: 12.13, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: THEME.colors.accent4, align: "right" },
  });

  let lastSection = null;
  function add(masterName, section) {
    if (section && section !== lastSection) { pres.addSection({ title: section }); lastSection = section; }
    return pres.addSlide({ masterName, sectionTitle: section || lastSection || undefined });
  }
  // Title slide. Free area for a visual: x 8.0–12.75, y 0.9–6.6.
  function titleSlide({ section, kicker, title, subtitle, source, notes }) {
    const s = add("TITLE_DARK", section);
    if (kicker) s.addText(kicker, { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    if (subtitle) s.addText(subtitle, { placeholder: "subtitle" });
    if (source) s.addText(source, { placeholder: "source" });
    if (notes) s.addNotes(notes);
    return s;
  }
  // Content slide. Free area: x 0.6–12.73, y 1.85–6.75.
  function content(section, kicker, title, notes) {
    const s = add("CONTENT", section);
    s.addText(kicker || " ", { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    if (notes) s.addNotes(notes);
    return s;
  }
  function closing(section, kicker, title, notes) {
    const s = add("CLOSING_DARK", section);
    s.addText(kicker || " ", { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    if (notes) s.addNotes(notes);
    return s;
  }

  // ---- save: write, then fix the theme inside the .pptx ----
  async function save(out) {
    await pres.writeFile({ fileName: out });
    const zip = await JSZip.loadAsync(fs.readFileSync(out));
    const part = "ppt/theme/theme1.xml";
    let xml = await zip.file(part).async("string");
    const name = String(THEME.name || "Deck").replace(/[&<>"]/g, "");
    for (const k of SLOTS) if (!/^[0-9A-Fa-f]{6}$/.test(String(THEME.colors[k]))) throw new Error(`theme.colors.${k} must be 6 hex digits`);
    const scheme = `<a:clrScheme name="${name}">` + SLOTS.map((k) => `<a:${k}><a:srgbClr val="${THEME.colors[k].toUpperCase()}"/></a:${k}>`).join("") + "</a:clrScheme>";
    xml = xml
      // why: pptxgenjs cannot write theme colors; without this every scheme color shows Office's stock palette.
      .replace(/<a:clrScheme\b[\s\S]*?<\/a:clrScheme>/, () => scheme)
      .replace(/(<a:(?:theme|fontScheme)\b[^>]*?\bname=")[^"]*"/g, (_, head) => `${head}${name}"`)
      // why: pptxgenjs leaves the East Asian theme font empty (and Hant = PMingLiU), so CJK text falls back to a serif.
      .replace(/<a:ea typeface=""\/>/g, `<a:ea typeface="${FONT}"/>`)
      .replace(/<a:font script="(Hant|Hans)" typeface="[^"]*"\/>/g, (_, sc) => `<a:font script="${sc}" typeface="${FONT}"/>`);
    zip.file(part, xml);
    for (const n of Object.keys(zip.files)) {
      if (zip.files[n].dir) { delete zip.files[n]; continue; } // folder entries break some cloud editors
      if (!n.endsWith(".xml")) continue;
      const bad = (await zip.file(n).async("string")).match(/<a:srgbClr val="((?![0-9A-Fa-f]{6}")[^"]*)"/);
      if (bad) throw new Error(`${n}: "${bad[1]}" is not a hex color — a scheme color was passed to a hex-only option (shadow.color, slideNumber.color…). Use THEME.colors.x there.`);
    }
    fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
    return out;
  }

  return { pres, C, SH, THEME, FONT, nm, text, box, chip, badge, line, flowArrow, downArrow, chain, callout, bullets, titleSlide, content, closing, save };
}

// Speaker-notes text for one script entry { time, script }.
const notesFor = (e) => `【對應影片 ${e.time}】\n${e.script}`;

// Write the per-slide speaking script as a text file (UTF-8 with BOM, CRLF: opens cleanly in Notepad).
// entries: [{ title, time, script }], in slide order. header: array of lines for the top of the file.
function writeScriptTxt(out, entries, header = []) {
  const bar = "=".repeat(60);
  const lines = [...header, ""];
  entries.forEach((e, i) => lines.push(bar, `第 ${i + 1} 頁｜${String(e.title).replace(/\n/g, " ")}`, `對應影片：${e.time}`, "-".repeat(60), e.script, ""));
  fs.writeFileSync(out, "﻿" + lines.join("\r\n"), "utf8");
  return out;
}

module.exports = { createDeck, notesFor, writeScriptTxt, DEFAULT_THEME };
