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

  slide.addText("Data: sources, checks and issues", { x: 0.35, y: 0.2, w: 9.3, h: 0.6, fontFace: FONT, fontSize: 30, bold: true, color: NAVY, isTextBox: true, margin: 0, valign: "middle" });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 0.85, w: 9.3, h: 0.18, fill: { color: NAVY }, line: { color: NAVY } });

  const HDR = 0.34;
  function box(b) {
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: b.y, w: b.w, h: HDR, fill: { color: HEADER_BG }, line: { color: BORDER, width: 0.75 } });
    slide.addText(b.title, { x: b.x + 0.1, y: b.y, w: b.w - 0.2, h: HDR, fontFace: FONT, fontSize: 12.5, bold: true, color: "1F2A3A", isTextBox: true, margin: 0, valign: "middle" });
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: b.y + HDR, w: b.w, h: b.h - HDR, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 0.75 } });
  }
  async function rows(b, items, fs, iconD) {
    const innerTop = b.y + HDR + 0.1, innerH = b.h - HDR - 0.2, rowH = innerH / items.length;
    for (let i = 0; i < items.length; i++) {
      const r = items[i], yc = innerTop + rowH * i + rowH / 2, ix = b.x + 0.15;
      slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
      const pad = iconD * 0.25;
      slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
      const tx = ix + iconD + 0.15;
      slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
        x: tx, y: yc - rowH / 2, w: b.x + b.w - tx - 0.12, h: rowH, fontFace: FONT, fontSize: fs, color: "111111", isTextBox: true, margin: 0, valign: "middle",
      });
    }
  }

  // ---- top row: sources | checks ----
  const TOP = 1.18, H = 2.45;
  const bA = { x: 0.35, y: TOP, w: 3.7, h: H, title: "1. Data sources" };
  const bB = { x: 4.35, y: TOP, w: 5.3, h: H, title: "2. Checks run in Python" };
  box(bA); box(bB);

  await rows(bA, [
    { icon: fa.FaDatabase, label: "VOLARE", text: " (open, CC BY 4.0): rv5, rq5, semivariances, bipower variation, OHLC, volume; 40 US stocks, 2 Jan 2015 - 31 Aug 2026; plus realised covariances" },
    { icon: fa.FaChartLine, label: "Yahoo Finance", text: " (yfinance): adjusted daily prices and returns for the 40 stocks, ^VIX, IVV" },
    { icon: fa.FaDesktop, label: "Bloomberg", text: " (pending): implied volatility, earnings dates, bid-ask spread" },
  ], 10, 0.38);

  const tblRows = [
    [{ text: "Check", options: { bold: true } }, { text: "Result", options: { bold: true } }],
    ["Stocks / days per stock", "40 / 2,932 each, identical calendar"],
    ["Missing values in rv5, rq5, rsp5, rsn5, bv5, OHLC", "0 rows"],
    ["Trading days Yahoo vs VOLARE", "identical, 0 missing either way"],
    ["Close Yahoo vs VOLARE (splits undone)", "median diff 0.00 %, 99th pct 0.5 %"],
    ["Largest daily |return| (adjusted)", "NFLX -43 % on 20 Apr 2022, no split artefacts"],
    ["Median annualised vol by year", "12-25 %, peaks 2020 and 2022; top days 12-19 Mar 2020"],
  ];
  slide.addTable(tblRows, {
    x: bB.x + 0.12, y: bB.y + HDR + 0.1, w: bB.w - 0.24, colW: [2.45, 2.61],
    fontFace: FONT, fontSize: 9, color: "111111", border: { type: "solid", color: "D5DFEC", pt: 0.5 },
    fill: { color: "FFFFFF" }, margin: 0.03, rowH: 0.27, valign: "middle",
  });

  // ---- bottom strip: issues and handling ----
  const bC = { x: 0.35, y: 3.82, w: 9.3, h: 1.33, title: "3. Issues found and how they are handled" };
  box(bC);
  const items = [
    { icon: fa.FaCut, label: "Splits and spin-offs", text: ": yfinance Close is split-adjusted, Adj Close also dividend-adjusted; 25 events (AMZN, GOOGL 20:1, NVDA 10:1, GE 1:8). Returns are computed from Adj Close" },
    { icon: fa.FaExclamationTriangle, label: "Where closes do not match", text: ": 459 days, all after-close earnings (AMZN 66, AMD 56, GOOGL 53). VOLARE runs to 16:05, so the jump lands in rv5 (5x median; bv5 unaffected). Use bv5 or flag these days" },
    { icon: fa.FaMoon, label: "Overnight", text: ": rv5 is open-to-close, returns are close-to-close. Add the squared overnight return from Yahoo open and close so target and return cover the same hours" },
  ];
  const colW = bC.w / 3, iconD = 0.36, yc = bC.y + HDR + (bC.h - HDR) / 2;
  for (let i = 0; i < items.length; i++) {
    const r = items[i], ix = bC.x + colW * i + 0.12;
    slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
    const pad = iconD * 0.25;
    slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
    const tx = ix + iconD + 0.12;
    slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
      x: tx, y: bC.y + HDR + 0.06, w: bC.x + colW * (i + 1) - tx - 0.1, h: bC.h - HDR - 0.12, fontFace: FONT, fontSize: 9, color: "111111", isTextBox: true, margin: 0, valign: "middle",
    });
  }

  slide.addText("Simon Gühring · Dissertation seminar · 16 Sep 2026 · 2/3", { x: 0.35, y: 5.27, w: 6, h: 0.25, fontFace: FONT, fontSize: 10, color: "555555", isTextBox: true, margin: 0 });

  await pres.writeFile({ fileName: "Data_specific.pptx" });
  console.log("wrote");
})();
