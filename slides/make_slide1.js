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

  slide.addText("Research gap and research question", {
    x: 0.35, y: 0.2, w: 9.3, h: 0.6, fontFace: FONT, fontSize: 30, bold: true,
    color: NAVY, isTextBox: true, margin: 0, valign: "middle",
  });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 0.85, w: 9.3, h: 0.18, fill: { color: NAVY }, line: { color: NAVY } });

  const TOP = 1.25, H = 3.85, HDR = 0.36;
  const boxes = [
    { x: 0.35, w: 4.35, title: "Research gap" },
    { x: 5.3, w: 4.35, title: "Research question" },
  ];
  for (const b of boxes) {
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: TOP, w: b.w, h: HDR, fill: { color: HEADER_BG }, line: { color: BORDER, width: 0.75 } });
    slide.addText(b.title, { x: b.x + 0.1, y: TOP, w: b.w - 0.2, h: HDR, fontFace: FONT, fontSize: 13, bold: true, color: "1F2A3A", isTextBox: true, margin: 0, valign: "middle" });
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: TOP + HDR, w: b.w, h: H - HDR, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 0.75 } });
  }
  slide.addShape(pres.shapes.RIGHT_ARROW, { x: 4.82, y: 2.98, w: 0.36, h: 0.4, fill: { color: NAVY }, line: { color: NAVY } });

  // ---- Research gap rows ----
  const gapRows = [
    { icon: fa.FaChartLine, label: "Practice vs research", text: ": GARCH(1,1) is the practitioner standard; recent US studies show machine learning beats HAR (Christensen et al. 2023, Zhang et al. 2024)" },
    { icon: fa.FaCalendarTimes, label: "Limits", text: ": their data ends in 2017 / 2021, and they score accuracy only, not whether the forecast variance is large enough" },
    { icon: fa.FaExclamationTriangle, label: "M6 (Makridakis et al. 2023)", text: ": forecasters were overconfident and portfolio risk was under-forecast, but the models behind it could not be identified" },
  ];
  const b0 = boxes[0];
  const innerTop = TOP + HDR + 0.15, innerH = H - HDR - 0.3, rowH = innerH / gapRows.length, iconD = 0.42;
  for (let i = 0; i < gapRows.length; i++) {
    const r = gapRows[i], yc = innerTop + rowH * i + rowH / 2, ix = b0.x + 0.2;
    slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
    const pad = iconD * 0.25;
    slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
    const tx = ix + iconD + 0.2;
    slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
      x: tx, y: yc - rowH / 2, w: b0.x + b0.w - tx - 0.15, h: rowH, fontFace: FONT, fontSize: 11, color: "111111", isTextBox: true, margin: 0, valign: "middle",
    });
  }

  // ---- Research question box ----
  const b1 = boxes[1];
  const qx = b1.x + 0.25, qw = b1.w - 0.5;
  slide.addText("Which models get volatility right?", {
    x: qx, y: TOP + HDR + 0.3, w: qw, h: 0.75, fontFace: FONT, fontSize: 19, bold: true, color: NAVY, isTextBox: true, margin: 0, valign: "top",
  });
  slide.addText("Overconfidence in machine-learning and GARCH forecasts of stock return variance", {
    x: qx, y: TOP + HDR + 1.05, w: qw, h: 0.65, fontFace: FONT, fontSize: 12, italic: true, color: "3A4A66", isTextBox: true, margin: 0, valign: "top",
  });
  slide.addShape(pres.shapes.LINE, { x: qx, y: TOP + HDR + 1.8, w: qw, h: 0, line: { color: BORDER, width: 1 } });
  slide.addText("Do machine-learning models underestimate the variance of stock returns more than GARCH, and are their prediction intervals large enough to cover realised returns, for 40 large US stocks over 2015-2026?", {
    x: qx, y: TOP + HDR + 1.95, w: qw, h: 1.35, fontFace: FONT, fontSize: 11.5, color: "111111", isTextBox: true, margin: 0, valign: "top",
  });

  slide.addText("Simon Gühring · Dissertation seminar · 16 Sep 2026 · 1/3", {
    x: 0.35, y: 5.25, w: 6, h: 0.25, fontFace: FONT, fontSize: 10, color: "555555", isTextBox: true, margin: 0,
  });

  await pres.writeFile({ fileName: "Research_gap_and_question.pptx" });
  console.log("wrote");
})();
