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

  slide.addText("Models and evaluation", { x: 0.35, y: 0.2, w: 9.3, h: 0.6, fontFace: FONT, fontSize: 30, bold: true, color: NAVY, isTextBox: true, margin: 0, valign: "middle" });
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

  const TOP = 1.18, H = 2.75;
  const bA = { x: 0.35, y: TOP, w: 4.35, h: H, title: "1. Model set (fixed)" };
  const bB = { x: 5.3, y: TOP, w: 4.35, h: H, title: "2. Evaluation: the M-competition scores" };
  box(bA); box(bB);
  slide.addShape(pres.shapes.RIGHT_ARROW, { x: 4.82, y: TOP + H / 2 - 0.2, w: 0.36, h: 0.4, fill: { color: NAVY }, line: { color: NAVY } });

  await rows(bA, [
    { icon: fa.FaMinus, label: "Naive", text: ": rolling 22-day realised variance" },
    { icon: fa.FaChartLine, label: "Classic", text: ": GARCH(1,1), GJR-GARCH, Student-t errors, daily returns only" },
    { icon: fa.FaLayerGroup, label: "Benchmark", text: ": HAR, HARQ, semivariance HAR on VOLARE measures" },
    { icon: fa.FaBrain, label: "Machine learning", text: ": LightGBM and neural net with distributional output, pooled across stocks, HAR inputs + VIX, earnings, calendar" },
    { icon: fa.FaObjectGroup, label: "Combination", text: ": equal-weighted average of all models" },
  ], 10, 0.38);

  await rows(bB, [
    { icon: fa.FaBullseye, label: "Accuracy", text: ": QLIKE and MSE of the variance forecast against realised variance" },
    { icon: fa.FaArrowsAltH, label: "Calibration", text: ": coverage of 90 / 95 / 99 % intervals, MSIS (M4), pinball loss (M5), Kupiec and Christoffersen tests" },
    { icon: fa.FaSortNumericDown, label: "M6 forecasting task", text: ": RPS of 20-day quintile probabilities vs naive 0.16" },
    { icon: fa.FaBriefcase, label: "M6 investment task", text: ": information ratio of a risk-targeted portfolio vs equal weights" },
  ], 10, 0.38);

  const bC = { x: 0.35, y: 4.1, w: 9.3, h: 1.05, title: "3. Design" };
  box(bC);
  const items = [
    { icon: fa.FaRedo, label: "Rolling origins", text: ": re-estimate monthly, ~100 origins Jan 2018 - Aug 2026; 1-day and 20-day horizons" },
    { icon: fa.FaCloudRain, label: "By regime", text: ": calm years, Covid 2020, rate shock 2022; months beating the benchmark, as in M6" },
    { icon: fa.FaVial, label: "Tests", text: ": Diebold-Mariano vs naive and vs GARCH, Mincer-Zarnowitz slope for underestimation; Python, code on GitHub" },
  ];
  const colW = bC.w / 3, iconD = 0.36, yc = bC.y + HDR + (bC.h - HDR) / 2;
  for (let i = 0; i < items.length; i++) {
    const r = items[i], ix = bC.x + colW * i + 0.12;
    slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
    const pad = iconD * 0.25;
    slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
    const tx = ix + iconD + 0.12;
    slide.addText([{ text: r.label, options: { bold: true } }, { text: r.text }], {
      x: tx, y: bC.y + HDR + 0.05, w: bC.x + colW * (i + 1) - tx - 0.1, h: bC.h - HDR - 0.1, fontFace: FONT, fontSize: 9, color: "111111", isTextBox: true, margin: 0, valign: "middle",
    });
  }

  slide.addText("Simon Gühring · Dissertation seminar · 16 Sep 2026 · 3/3", { x: 0.35, y: 5.27, w: 6, h: 0.25, fontFace: FONT, fontSize: 10, color: "555555", isTextBox: true, margin: 0 });

  await pres.writeFile({ fileName: "Models_and_evaluation.pptx" });
  console.log("wrote");
})();
