const pptxgen = require("pptxgenjs");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const NAVY = "0E1E3A", HEADER_BG = "DCE7F5", BORDER = "9DB9DC", FONT = "Arial";

async function iconPng(Icon) {
  const svg = renderToStaticMarkup(React.createElement(Icon, { color: "#FFFFFF", size: 256 }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };

  slide.addText("Two settings: own study and M6 replication", { x: 0.35, y: 0.2, w: 9.3, h: 0.6, fontFace: FONT, fontSize: 28, bold: true, color: NAVY, isTextBox: true, margin: 0, valign: "middle" });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 0.85, w: 9.3, h: 0.18, fill: { color: NAVY }, line: { color: NAVY } });

  const HDR = 0.34;
  function box(b) {
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: b.y, w: b.w, h: HDR, fill: { color: HEADER_BG }, line: { color: BORDER, width: 0.75 } });
    slide.addText(b.title, { x: b.x + 0.1, y: b.y, w: b.w - 0.2, h: HDR, fontFace: FONT, fontSize: 12.5, bold: true, color: "1F2A3A", isTextBox: true, margin: 0, valign: "middle" });
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: b.y + HDR, w: b.w, h: b.h - HDR, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 0.75 } });
  }
  async function rows(b, items, fs, iconD) {
    const innerTop = b.y + HDR + 0.08, innerH = b.h - HDR - 0.16, rowH = innerH / items.length;
    for (let i = 0; i < items.length; i++) {
      const r = items[i], yc = innerTop + rowH * i + rowH / 2, ix = b.x + 0.15;
      slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: r.color || NAVY }, line: { color: r.color || NAVY } });
      const pad = iconD * 0.25;
      slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
      const tx = ix + iconD + 0.15;
      slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
        x: tx, y: yc - rowH / 2, w: b.x + b.w - tx - 0.12, h: rowH, fontFace: FONT, fontSize: fs, color: "111111", isTextBox: true, margin: 0, valign: "middle",
      });
    }
  }

  const TOP = 1.18, H = 2.95;
  const bA = { x: 0.35, y: TOP, w: 4.5, h: H, title: "A. Own study: 40 stocks, 2015-2026 (main)" };
  const bB = { x: 5.15, y: TOP, w: 4.5, h: H, title: "B. M6 replication: 100 assets, 2022-23 (chapter 7)" };
  box(bA); box(bB);

  const GREEN = "2E7D5B", RED = "A63D40";
  await rows(bA, [
    { icon: fa.FaDatabase, label: "Data", text: ": VOLARE intraday realised variance + Yahoo returns; ~100 monthly origins" },
    { icon: fa.FaCogs, label: "Models", text: ": all of them: GARCH, HAR family, ML, combination" },
    { icon: fa.FaPlus, label: "Strength", color: GREEN, text: ": 11 years and three regimes; enough origins for Diebold-Mariano and calibration tests; model behind every forecast known" },
    { icon: fa.FaMinus, label: "Limit", color: RED, text: ": no external yardstick; I set the benchmark myself" },
  ], 9.5, 0.36);

  await rows(bB, [
    { icon: fa.FaDatabase, label: "Data", text: ": official assets_m6.csv and submissions.csv; 12 fixed windows Mar 2022 - Feb 2023; daily prices only" },
    { icon: fa.FaCogs, label: "Models", text: ": daily-data models only: GARCH, GJR, ML on daily inputs; no HAR" },
    { icon: fa.FaPlus, label: "Strength", color: GREEN, text: ": scored with the organisers' code against 163 real teams; overconfidence curve (Hypothesis7.R) redrawn with my models added" },
    { icon: fa.FaMinus, label: "Limit", color: RED, text: ": one year, no significance tests; hindsight risk, so model design frozen before Mar 2022" },
  ], 9.5, 0.36);

  const bC = { x: 0.35, y: 4.3, w: 9.3, h: 0.85, title: "Verdict" };
  box(bC);
  slide.addText([
    { text: "A answers the research question", options: { bold: true } },
    { text: ": which models underestimate volatility, and when. " },
    { text: "B shows it matters", options: { bold: true } },
    { text: ": the same overconfidence the organisers found, tested on their own task and leaderboard. Both use the same scores (RPS, IR, MSIS, coverage), so results are directly comparable. B is one chapter, not the core, and is dropped first if time runs short." },
  ], { x: bC.x + 0.15, y: bC.y + HDR + 0.04, w: bC.w - 0.3, h: bC.h - HDR - 0.08, fontFace: FONT, fontSize: 9.5, color: "111111", isTextBox: true, margin: 0, valign: "middle" });

  slide.addText("Simon Gühring · Dissertation seminar · 16 Sep 2026", { x: 0.35, y: 5.27, w: 6, h: 0.25, fontFace: FONT, fontSize: 10, color: "555555", isTextBox: true, margin: 0 });

  await pres.writeFile({ fileName: "Own_study_vs_M6.pptx" });
  console.log("wrote");
})();
