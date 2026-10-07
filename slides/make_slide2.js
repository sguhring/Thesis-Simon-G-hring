const pptxgen = require("pptxgenjs");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const NAVY = "0E1E3A";
const HEADER_BG = "DCE7F5";
const BORDER = "9DB9DC";
const FONT = "Arial";

async function iconPng(Icon) {
  const svg = renderToStaticMarkup(React.createElement(Icon, { color: "#FFFFFF", size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };

  slide.addText("Data: status and collection strategy", {
    x: 0.35, y: 0.2, w: 9.3, h: 0.6, fontFace: FONT, fontSize: 30, bold: true,
    color: NAVY, isTextBox: true, margin: 0, valign: "middle",
  });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 0.85, w: 9.3, h: 0.18, fill: { color: NAVY }, line: { color: NAVY } });

  const HDR = 0.36;
  function box(b) {
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: b.y, w: b.w, h: HDR, fill: { color: HEADER_BG }, line: { color: BORDER, width: 0.75 } });
    slide.addText(b.title, { x: b.x + 0.1, y: b.y, w: b.w - 0.2, h: HDR, fontFace: FONT, fontSize: 13, bold: true, color: "1F2A3A", isTextBox: true, margin: 0, valign: "middle" });
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: b.y + HDR, w: b.w, h: b.h - HDR, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 0.75 } });
  }
  async function rows(b, items, fontSize) {
    const innerTop = b.y + HDR + 0.12, innerH = b.h - HDR - 0.24, rowH = innerH / items.length, iconD = 0.4;
    for (let i = 0; i < items.length; i++) {
      const r = items[i], yc = innerTop + rowH * i + rowH / 2, ix = b.x + 0.18;
      slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
      const pad = iconD * 0.25;
      slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
      const tx = ix + iconD + 0.18;
      slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
        x: tx, y: yc - rowH / 2, w: b.x + b.w - tx - 0.12, h: rowH, fontFace: FONT, fontSize, color: "111111", isTextBox: true, margin: 0, valign: "middle",
      });
    }
  }

  const TOP = 1.22, H = 2.6;
  const bA = { x: 0.35, y: TOP, w: 4.35, h: H, title: "1. Data sources" };
  const bB = { x: 5.3, y: TOP, w: 4.35, h: H, title: "2. Status today" };
  box(bA); box(bB);
  slide.addShape(pres.shapes.RIGHT_ARROW, { x: 4.82, y: TOP + H / 2 - 0.2, w: 0.36, h: 0.4, fill: { color: NAVY }, line: { color: NAVY } });

  await rows(bA, [
    { icon: fa.FaDatabase, label: "VOLARE", text: " (open, CC BY 4.0): daily realised measures from 5-min prices: rv5, rq5, semivariances, bipower variation, realised kernel, OHLC; plus realised covariances. 40 US stocks, Jan 2015 - Jan 2026" },
    { icon: fa.FaChartLine, label: "Prices and returns", text: ": adjusted daily OHLCV for the 40 stocks, S&P 500 ETF and VIX. Yahoo Finance now, Bloomberg when available" },
    { icon: fa.FaDesktop, label: "Bloomberg", text: " (personal use, pending): 30-day implied volatility, earnings dates, bid-ask spread" },
  ], 10.5);

  await rows(bB, [
    { icon: fa.FaCheckCircle, label: "VOLARE", text: ": account active; Stocks Variances and Stocks Covariances ZIP downloaded (Parquet). Coverage check per stock: start, end, number of days" },
    { icon: fa.FaCheckCircle, label: "Yahoo Finance", text: ": download script tested for the 40 tickers, ^VIX and IVV; returns cross-checked against VOLARE closes" },
    { icon: fa.FaHourglassHalf, label: "Bloomberg", text: ": terminal access requested; one-stock field test scheduled, fields verified via FLDS before the full pull" },
  ], 10.5);

  const bC = { x: 0.35, y: 4.0, w: 9.3, h: 1.12, title: "3. Risks and fallbacks" };
  box(bC);
  const items = [
    { icon: fa.FaExclamationTriangle, label: "No implied vol", text: ": run all models without it first; add as an extra feature block if Bloomberg arrives" },
    { icon: fa.FaCalendarAlt, label: "Earnings dates", text: ": SEC EDGAR 10-Q / 10-K filing dates as free substitute" },
    { icon: fa.FaMoon, label: "Overnight variance", text: ": add squared overnight return from open and close; fixed before Milestone 1 (week of 5 Oct)" },
  ];
  const colW = bC.w / 3, iconD = 0.38, yc = bC.y + HDR + (bC.h - HDR) / 2;
  for (let i = 0; i < items.length; i++) {
    const r = items[i], ix = bC.x + colW * i + 0.15;
    slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
    const pad = iconD * 0.25;
    slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
    const tx = ix + iconD + 0.15;
    slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
      x: tx, y: bC.y + HDR + 0.08, w: colW - (tx - (bC.x + colW * i)) - 0.12, h: bC.h - HDR - 0.16, fontFace: FONT, fontSize: 10, color: "111111", isTextBox: true, margin: 0, valign: "middle",
    });
  }

  slide.addText("Simon Gühring · Dissertation seminar · 16 Sep 2026 · 2/3", {
    x: 0.35, y: 5.25, w: 6, h: 0.25, fontFace: FONT, fontSize: 10, color: "555555", isTextBox: true, margin: 0,
  });

  await pres.writeFile({ fileName: "Data_status_and_strategy.pptx" });
  console.log("wrote");
})();
