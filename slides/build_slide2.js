const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fa = require("react-icons/fa");

const DARK = "0B1B33", STRIP = "D9E6F5", BORDER = "BFD3EA", INK = "1A1A1A", MUTED = "666666", FONT = "Arial";

async function iconPng(Icon) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: "#FFFFFF", size: 256 }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";

function title(slide, t) {
  slide.addText(t, { x: 0.5, y: 0.25, w: 9, h: 0.6, fontFace: FONT, fontSize: 26, bold: true, color: DARK, isTextBox: true, margin: 0, valign: "bottom" });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.9, w: 9, h: 0.18, fill: { color: DARK }, line: { color: DARK } });
}
function boxFrame(slide, x, y, w, h, label) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.32, fill: { color: STRIP }, line: { color: STRIP } });
  slide.addText(label, { x: x + 0.1, y, w: w - 0.2, h: 0.32, fontFace: FONT, fontSize: 11, bold: true, color: DARK, isTextBox: true, margin: 0, valign: "middle" });
  slide.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.32, w, h: h - 0.32, fill: { color: "FFFFFF" }, line: { color: BORDER, width: 1 } });
}
function runsOf(p, fs) {
  return p.map(r => ({ text: typeof r === "object" ? r.t : r, options: { fontFace: FONT, fontSize: fs, color: INK, bold: typeof r === "object" && r.b } }));
}
function iconBox(slide, x, y, w, h, label, rows, fs) {
  boxFrame(slide, x, y, w, h, label);
  const rowH = (h - 0.42) / rows.length, d = 0.34;
  rows.forEach((r, i) => {
    const ry = y + 0.38 + i * rowH;
    slide.addShape(pres.shapes.OVAL, { x: x + 0.18, y: ry + (rowH - d) / 2, w: d, h: d, fill: { color: DARK }, line: { color: DARK } });
    slide.addImage({ data: r.icon, x: x + 0.18 + d * 0.22, y: ry + (rowH - d) / 2 + d * 0.22, w: d * 0.56, h: d * 0.56 });
    slide.addText(runsOf(r.text, fs), { x: x + 0.68, y: ry, w: w - 0.85, h: rowH, isTextBox: true, margin: 2, valign: "middle" });
  });
}
const B = t => ({ t, b: true });

(async () => {
  const ic = {};
  for (const [k, I] of Object.entries({ db: Fa.FaDatabase, desk: Fa.FaDesktop, calc: Fa.FaCalculator, list: Fa.FaListUl, book: Fa.FaBookOpen, down: Fa.FaDownload, flag: Fa.FaFlagCheckered }))
    ic[k] = await iconPng(I);

  const s = pres.addSlide();
  title(s, "Data and next steps");
  const y = 1.3, h = 3.85, bw = 4.25, aw = 0.5;
  iconBox(s, 0.5, y, bw, h, "1. Data (inputs)", [
    { icon: ic.db, text: [B("VOLARE"), " (open library, Feb 2026): daily realised volatility from 5-min prices, 40 large US stocks, 2015-2026"] },
    { icon: ic.desk, text: [B("Bloomberg"), ": daily returns, implied volatility, VIX, earnings dates, volume, relative spread"] },
    { icon: ic.calc, text: [B("Derived"), ": day-of-week and month-end dummies, jumps (RV minus bipower variation), GARCH forecast as a feature"] },
  ], 11.5);
  s.addShape(pres.shapes.RIGHT_ARROW, { x: 0.5 + bw + 0.04, y: y + h / 2 - 0.2, w: aw - 0.08, h: 0.4, fill: { color: DARK }, line: { color: DARK } });
  iconBox(s, 0.5 + bw + aw, y, bw, h, "2. Next steps", [
    { icon: ic.list, text: [B("Decide the input variables"), ": HAR lags, quarticity, semivariances, implied vol, VIX, earnings, calendar"] },
    { icon: ic.book, text: [B("Read the HAR literature"), ": Corsi (2009, JFEC); HARQ, Bollerslev, Patton & Quaedvlieg (2016)"] },
    { icon: ic.down, text: [B("Download VOLARE"), " for the 40 stocks; check rv5, rq, semivariances and coverage to 2026"] },
    { icon: ic.desk, text: [B("Bloomberg test"), ": download all fields for one stock, check the monthly limit"] },
    { icon: ic.flag, text: [B("Session 2, 16 Sep"), ": final research question, feature list and model set fixed"] },
  ], 11);
  s.addText("2/3", { x: 0.5, y: 5.3, w: 9, h: 0.2, fontFace: FONT, fontSize: 8, color: MUTED, isTextBox: true, margin: 0 });

  console.log("wrote", await pres.writeFile({ fileName: process.argv[2] || "Slide_Data_and_Next_Steps.pptx" }));
})();
