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
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625

  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };

  slide.addText("Data and Next Steps", {
    x: 0.35, y: 0.2, w: 9.3, h: 0.6, fontFace: FONT, fontSize: 30, bold: true,
    color: NAVY, isTextBox: true, margin: 0, valign: "middle",
  });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 0.85, w: 9.3, h: 0.18, fill: { color: NAVY }, line: { color: NAVY } });

  const TOP = 1.25, H = 4.0, HDR = 0.36;
  const boxes = [
    { x: 0.35, w: 4.35, title: "1. Data (inputs)" },
    { x: 5.3, w: 4.35, title: "2. Next steps" },
  ];
  for (const b of boxes) {
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: TOP, w: b.w, h: HDR, fill: { color: HEADER_BG }, line: { color: BORDER, width: 0.75 } });
    slide.addText(b.title, { x: b.x + 0.1, y: TOP, w: b.w - 0.2, h: HDR, fontFace: FONT, fontSize: 13, bold: true, color: "1F2A3A", isTextBox: true, margin: 0, valign: "middle" });
    slide.addShape(pres.shapes.RECTANGLE, { x: b.x, y: TOP + HDR, w: b.w, h: H - HDR, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 0.75 } });
  }
  // arrow between boxes
  slide.addShape(pres.shapes.RIGHT_ARROW, { x: 4.82, y: 3.05, w: 0.36, h: 0.4, fill: { color: NAVY }, line: { color: NAVY } });

  const dataRows = [
    { icon: fa.FaDatabase, label: "VOLARE", text: " (open, Feb 2026): daily realised variance from 5-min prices, 40 large US stocks, 2015-2026" },
    { icon: fa.FaDesktop, label: "Bloomberg", text: " (personal use only): daily returns, 30-day implied vol, VIX, earnings dates" },
    { icon: fa.FaBullseye, label: "Target", text: ": log realised variance, 1-day ahead (also 5 and 22 days)" },
    { icon: fa.FaCalendarAlt, label: "Sample and split", text: ": ~2,800 trading days per stock; train 2015-2022, validate 2023, test 2024-2026" },
    { icon: fa.FaChartLine, label: "Regimes covered", text: ": Covid 2020, 2022 rate shock, calm years" },
    { icon: fa.FaFilter, label: "Cleaning", text: ": overnight returns, missing 5-min bars, earnings days flagged" },
  ];
  const stepRows = [
    { icon: fa.FaLink, label: "Build dataset", text: ": merge VOLARE and Bloomberg, clean, align dates" },
    { icon: fa.FaWaveSquare, label: "Baselines", text: ": estimate GARCH(1,1), GJR-GARCH and HAR family" },
    { icon: fa.FaBrain, label: "Machine learning", text: ": LightGBM and neural net with HAR inputs, then extra inputs; hybrid with GARCH forecast as input" },
    { icon: fa.FaBalanceScale, label: "Evaluation", text: ": rolling window, MSE and QLIKE, Diebold-Mariano vs HAR" },
    { icon: fa.FaFileAlt, label: "Write-up", text: ": results by regime, interpretation, limitations" },
  ];

  async function fillRows(box, rows) {
    const innerTop = TOP + HDR + 0.15;
    const innerH = H - HDR - 0.3;
    const rowH = innerH / rows.length;
    const iconD = 0.42;
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];
      const yc = innerTop + rowH * i + rowH / 2;
      const ix = box.x + 0.2;
      slide.addShape(pres.shapes.OVAL, { x: ix, y: yc - iconD / 2, w: iconD, h: iconD, fill: { color: NAVY }, line: { color: NAVY } });
      const pad = iconD * 0.25;
      slide.addImage({ data: await iconPng(r.icon), x: ix + pad, y: yc - iconD / 2 + pad, w: iconD - 2 * pad, h: iconD - 2 * pad });
      const tx = ix + iconD + 0.2;
      slide.addText([
        { text: r.label, options: { bold: true } },
        { text: r.text },
      ], { x: tx, y: yc - rowH / 2, w: box.x + box.w - tx - 0.15, h: rowH, fontFace: FONT, fontSize: 10.5, color: "111111", isTextBox: true, margin: 0, valign: "middle" });
    }
  }
  await fillRows(boxes[0], dataRows);
  await fillRows(boxes[1], stepRows);

  slide.addText("2/3", { x: 0.35, y: 5.3, w: 1, h: 0.25, fontFace: FONT, fontSize: 10, color: "555555", isTextBox: true, margin: 0 });

  await pres.writeFile({ fileName: "Data_and_Next_Steps.pptx" });
  console.log("wrote");
})();
