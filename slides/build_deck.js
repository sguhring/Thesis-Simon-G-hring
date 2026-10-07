const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fa = require("react-icons/fa");

const DARK = "0B1B33";      // title text + bar
const STRIP = "D9E6F5";     // box header strip
const BORDER = "BFD3EA";    // box border
const INK = "1A1A1A";
const MUTED = "666666";
const FONT = "Arial";

async function iconPng(Icon, color) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#" + color, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function title(slide, t) {
  slide.addText(t, { x: 0.5, y: 0.25, w: 9, h: 0.6, fontFace: FONT, fontSize: 26, bold: true, color: DARK, isTextBox: true, margin: 0, valign: "bottom" });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.9, w: 9, h: 0.18, fill: { color: DARK }, line: { color: DARK } });
}
function boxFrame(slide, x, y, w, h, label) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.32, fill: { color: STRIP }, line: { color: STRIP } });
  slide.addText(label, { x: x + 0.1, y, w: w - 0.2, h: 0.32, fontFace: FONT, fontSize: 11, bold: true, color: DARK, isTextBox: true, margin: 0, valign: "middle" });
  slide.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.32, w, h: h - 0.32, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 1 } });
}
function runsOf(p, fs, first) {
  return p.map((r, ri) => {
    const isObj = typeof r === "object";
    const o = { fontFace: FONT, fontSize: fs, color: INK, bold: isObj && r.b };
    if (p.bullet && ri === 0) o.bullet = { indent: 12 };
    return { text: isObj ? r.t : r, options: o };
  });
}
function box(slide, x, y, w, h, label, paras, fs) {
  boxFrame(slide, x, y, w, h, label);
  const runs = [];
  paras.forEach((p, pi) => {
    const rs = runsOf(p, fs || 12.5);
    if (pi < paras.length - 1) { rs[rs.length - 1].options.breakLine = true; rs[rs.length - 1].options.paraSpaceAfter = 6; }
    runs.push(...rs);
  });
  slide.addText(runs, { x: x + 0.12, y: y + 0.38, w: w - 0.24, h: h - 0.46, isTextBox: true, margin: 2, valign: "top" });
}
// icon rows inside a labelled box
function iconBox(slide, x, y, w, h, label, rows, fs) {
  boxFrame(slide, x, y, w, h, label);
  const rowH = (h - 0.42) / rows.length;
  rows.forEach((r, i) => {
    const ry = y + 0.38 + i * rowH;
    const d = 0.34;
    slide.addShape(pres.shapes.OVAL, { x: x + 0.18, y: ry + (rowH - d) / 2, w: d, h: d, fill: { color: DARK }, line: { color: DARK } });
    slide.addImage({ data: r.icon, x: x + 0.18 + d * 0.22, y: ry + (rowH - d) / 2 + d * 0.22, w: d * 0.56, h: d * 0.56 });
    slide.addText(runsOf(r.text, fs || 12.5), { x: x + 0.68, y: ry, w: w - 0.85, h: rowH, isTextBox: true, margin: 2, valign: "middle" });
  });
}
function B(t) { return { t, b: true }; }
function bl(arr) { arr.bullet = true; return arr; }

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625

(async () => {
  const icChart = await iconPng(Fa.FaChartLine, "FFFFFF");
  const icClock = await iconPng(Fa.FaRegClock, "FFFFFF");
  const icBan = await iconPng(Fa.FaBan, "FFFFFF");
  const icShield = await iconPng(Fa.FaShieldAlt, "FFFFFF");
  const icDb = await iconPng(Fa.FaDatabase, "FFFFFF");
  const icTerminal = await iconPng(Fa.FaDesktop, "FFFFFF");
  const icCoins = await iconPng(Fa.FaCoins, "FFFFFF");
  const icLayers = await iconPng(Fa.FaLayerGroup, "FFFFFF");
  const icBrain = await iconPng(Fa.FaBrain, "FFFFFF");
  const icLink = await iconPng(Fa.FaLink, "FFFFFF");
  const icCalendar = await iconPng(Fa.FaCalendarAlt, "FFFFFF");
  const icScale = await iconPng(Fa.FaBalanceScale, "FFFFFF");
  const icBolt = await iconPng(Fa.FaBolt, "FFFFFF");
  const icDownload = await iconPng(Fa.FaDownload, "FFFFFF");

  // ---------- Slide 1 ----------
  {
    const s = pres.addSlide();
    title(s, "Research gap and research question");
    iconBox(s, 0.5, 1.3, 9, 2.25, "Research gap", [
      { icon: icChart, text: [B("GARCH(1,1)"), " is the practitioner standard, ", B("HAR"), " the academic benchmark; recent US studies show ", B("machine learning beats HAR"), " (Christensen et al. 2023, Zhang et al. 2024)"] },
      { icon: icClock, text: ["Their data ", B("ends in 2017 / 2021"), ": no 2022 rate shock, no 2025 tariff shock"] },
      { icon: icBan, text: [B("GARCH is left out"), " of the comparison, and the studies rely on ", B("expensive proprietary data")] },
      { icon: icShield, text: ["Nobody tests whether the ML gain ", B("survives crises"), " or improves ", B("actual risk numbers (VaR)")] },
    ], 11.5);
    s.addShape(pres.shapes.DOWN_ARROW, { x: 4.74, y: 3.62, w: 0.52, h: 0.38, fill: { color: DARK }, line: { color: DARK } });
    box(s, 0.5, 4.06, 9, 1.15, "Research question", [
      ["Do ", B("machine-learning models"), " forecast the ", B("volatility of large US stocks"), " more accurately than ", B("GARCH and HAR"), " over ", B("2015-2026"),
       ", and does the gain hold in ", B("crisis periods"), " and translate into ", B("better Value-at-Risk"), "?"],
    ], 13);
    s.addText("Simon Gühring · Dissertation seminar · 9 Sep 2026 · 1/3", { x: 0.5, y: 5.3, w: 9, h: 0.22, fontFace: FONT, fontSize: 8, color: MUTED, isTextBox: true, margin: 0 });
  }

  // ---------- Slide 2 ----------
  {
    const s = pres.addSlide();
    title(s, "Data and method");
    const bw = 2.72, aw = 0.42, y = 1.35, h = 3.75;
    const x1 = 0.5, x2 = x1 + bw + aw, x3 = x2 + bw + aw;
    iconBox(s, x1, y, bw, h, "1. Data (inputs)", [
      { icon: icDb, text: [B("VOLARE"), " (open, Feb 2026): daily realised vol from 5-min prices, 40 large US stocks, 2015-2026"] },
      { icon: icTerminal, text: [B("Bloomberg"), ": daily returns, implied volatility, VIX, earnings dates"] },
      { icon: icDownload, text: [B("How I get it"), ": bulk CSV from volare.unime.it (tested this week); Bloomberg Excel add-in at the Católica terminal"] },
      { icon: icCoins, text: ["Data cost: ", B("zero")] },
    ], 10.5);
    iconBox(s, x2, y, bw, h, "2. Models", [
      { icon: icChart, text: [B("Classic"), ": GARCH(1,1), GJR-GARCH"] },
      { icon: icLayers, text: [B("Benchmark"), ": HAR family"] },
      { icon: icBrain, text: [B("Machine learning"), ": LightGBM and neural net, with HAR inputs, then extra inputs"] },
      { icon: icLink, text: [B("Hybrid"), ": GARCH forecast as ML input"] },
    ], 10.5);
    iconBox(s, x3, y, bw, h, "3. Comparison", [
      { icon: icCalendar, text: [B("1, 5, 22 days"), " ahead; rolling out-of-sample 2020-2026, re-fit yearly"] },
      { icon: icScale, text: [B("QLIKE loss"), " + Diebold-Mariano and Model Confidence Set tests"] },
      { icon: icBolt, text: ["Split ", B("calm vs crisis"), " periods"] },
      { icon: icShield, text: ["Forecasts into ", B("1-day VaR"), ", backtested"] },
    ], 10.5);
    [x1 + bw, x2 + bw].forEach(ax => {
      s.addShape(pres.shapes.RIGHT_ARROW, { x: ax + 0.04, y: y + h / 2 - 0.2, w: aw - 0.08, h: 0.4, fill: { color: DARK }, line: { color: DARK } });
    });
    s.addText("2/3", { x: 0.5, y: 5.3, w: 9, h: 0.2, fontFace: FONT, fontSize: 8, color: MUTED, isTextBox: true, margin: 0 });
  }

  // ---------- Slide 3 ----------
  {
    const s = pres.addSlide();
    title(s, "Hypotheses, backup option and questions");
    box(s, 0.5, 1.3, 9, 1.55, "Hypotheses", [
      bl(["ML beats GARCH and HAR mainly at ", B("5-22 day horizons"), ", not at 1 day"]),
      bl(["The ML edge ", B("shrinks or disappears in crises")]),
      bl(["Most of the edge comes from ", B("extra information"), " (implied vol, earnings), not from the algorithm"]),
      bl(["Better forecasts give ", B("better VaR coverage")]),
    ], 12);
    box(s, 0.5, 3.0, 4.4, 2.1, "Backup research question", [
      ["Is ", B("GARCH(1,1) still unbeatable on exchange rates"), " 20 years after Hansen & Lunde (2005)? Same models and tests on ",
       B("5 FX pairs"), " (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD) from VOLARE, ", B("2009-2026"), ". Same data source, so no extra data risk."],
      ["If VOLARE fails: Bloomberg daily OHLC with a ", B("range-based volatility"), " target (Parkinson, Garman-Klass)."],
    ], 11);
    box(s, 5.1, 3.0, 4.4, 2.1, "Questions for the group", [
      bl(["Is this a ", B("sufficient contribution"), ", or should I narrow to one hypothesis?"]),
      bl([B("US stocks only"), ", or add the FX sample as a second chapter?"]),
      bl(["Is a ", B("neural net"), " worth it, or are tree models enough?"]),
    ], 11.5);
    s.addText("3/3", { x: 0.5, y: 5.3, w: 9, h: 0.2, fontFace: FONT, fontSize: 8, color: MUTED, isTextBox: true, margin: 0 });
  }

  const f = await pres.writeFile({ fileName: process.argv[2] || "Dissertation_Ideas_Volatility_ML_vs_GARCH.pptx" });
  console.log("wrote", f);
})();
