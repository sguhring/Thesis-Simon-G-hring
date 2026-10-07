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

  slide.addText("Data", { x: 0.35, y: 0.2, w: 9.3, h: 0.6, fontFace: FONT, fontSize: 30, bold: true, color: NAVY, isTextBox: true, margin: 0, valign: "middle" });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 0.85, w: 9.3, h: 0.18, fill: { color: NAVY }, line: { color: NAVY } });

  const TOP = 1.25, H = 3.85, HDR = 0.36;
  const boxes = [
    { x: 0.35, w: 4.35, title: "1. Data sources" },
    { x: 5.3, w: 4.35, title: "2. Status today" },
  ];
  for (const b of boxes) {
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: TOP, w: b.w, h: HDR, fill: { color: HEADER_BG }, line: { color: BORDER, width: 0.75 } });
    slide.addText(b.title, { x: b.x + 0.1, y: TOP, w: b.w - 0.2, h: HDR, fontFace: FONT, fontSize: 13, bold: true, color: "1F2A3A", isTextBox: true, margin: 0, valign: "middle" });
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: TOP + HDR, w: b.w, h: H - HDR, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 0.75 } });
  }
  slide.addShape(pres.shapes.RIGHT_ARROW, { x: 4.82, y: TOP + H / 2 - 0.2, w: 0.36, h: 0.4, fill: { color: NAVY }, line: { color: NAVY } });

  async function rows(b, items) {
    const innerTop = TOP + HDR + 0.15, innerH = H - HDR - 0.3, rowH = innerH / items.length, iconD = 0.44;
    for (let i = 0; i < items.length; i++) {
      const r = items[i], yc = innerTop + rowH * i + rowH / 2, ix = b.x + 0.2;
      slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
      const pad = iconD * 0.25;
      slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
      const tx = ix + iconD + 0.2;
      slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
        x: tx, y: yc - rowH / 2, w: b.x + b.w - tx - 0.15, h: rowH, fontFace: FONT, fontSize: 12, color: "111111", isTextBox: true, margin: 0, valign: "middle",
      });
    }
  }

  await rows(boxes[0], [
    { icon: fa.FaDatabase, label: "VOLARE", text: " (open): daily realised variance from 5-min prices, 40 large US stocks, 2015-2026" },
    { icon: fa.FaChartLine, label: "Yahoo Finance", text: ": daily returns, VIX, S&P 500 ETF" },
    { icon: fa.FaDesktop, label: "Bloomberg", text: " (pending): implied volatility, earnings dates" },
  ]);
  await rows(boxes[1], [
    { icon: fa.FaCheckCircle, label: "VOLARE downloaded", text: ": 40 stocks, 2,932 days each, no gaps" },
    { icon: fa.FaCheckCircle, label: "Yahoo downloaded", text: ": prices match VOLARE, calendars aligned" },
    { icon: fa.FaHourglassHalf, label: "Bloomberg", text: ": access requested, fallback in place" },
  ]);

  slide.addText("Simon Gühring · Dissertation seminar · 16 Sep 2026 · 2/3", { x: 0.35, y: 5.25, w: 6, h: 0.25, fontFace: FONT, fontSize: 10, color: "555555", isTextBox: true, margin: 0 });

  await pres.writeFile({ fileName: "Data_general.pptx" });
  console.log("wrote");
})();
