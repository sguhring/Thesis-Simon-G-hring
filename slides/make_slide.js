const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in

const NAVY = "0E1E3A";
const HEADER_BG = "DCE7F5";
const BORDER = "9DB9DC";
const FONT = "Arial";

const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

// Title
slide.addText("Clarifications and Alternatives", {
  x: 0.35, y: 0.2, w: 9.3, h: 0.6,
  fontFace: FONT, fontSize: 30, bold: true, color: NAVY,
  isTextBox: true, margin: 0, valign: "middle",
});
// Navy bar under title (matches user's existing slide style)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.35, y: 0.85, w: 9.3, h: 0.18, fill: { color: NAVY }, line: { color: NAVY },
});

function box(y, h, header, bodyItems) {
  // header
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y, w: 9.3, h: 0.36,
    fill: { color: HEADER_BG }, line: { color: BORDER, width: 0.75 },
  });
  slide.addText(header, {
    x: 0.45, y, w: 9.1, h: 0.36,
    fontFace: FONT, fontSize: 13, bold: true, color: "1F2A3A",
    isTextBox: true, margin: 0, valign: "middle",
  });
  // body
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: y + 0.36, w: 9.3, h: h - 0.36,
    fill: { color: "FFFFFF" }, line: { color: BORDER, width: 0.75 },
  });
  slide.addText(bodyItems, {
    x: 0.5, y: y + 0.46, w: 8.95, h: h - 0.56,
    fontFace: FONT, fontSize: 13, color: "111111",
    isTextBox: true, margin: 0, valign: "top", paraSpaceAfter: 6,
  });
}

box(1.25, 1.7, "Clarifications", [
  { text: "Bloomberg raw dataset: personal use only", options: { bullet: true, breakLine: true } },
  { text: "Main research question restated: Can macroeconomic data, combined with Bayesian and machine learning methods, forecast government bond returns, and which macroeconomic factors matter most?", options: { bullet: true } },
]);

box(3.2, 1.9, "Backup research question", [
  { text: "Which macroeconomic variables explain the variation in government bond returns?", options: { bullet: false } },
]);

pres.writeFile({ fileName: "Clarifications_and_Alternatives.pptx" }).then(f => console.log("wrote", f));
