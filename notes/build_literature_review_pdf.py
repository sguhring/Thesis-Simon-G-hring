"""Build notes/literature_review_hypotheses.pdf: what the literature says about hypotheses H1 to H8.

The figures and the numbers quoted from them come from notes/lit_review_figures.py, so run that first:

    python notes/lit_review_figures.py
    python notes/build_literature_review_pdf.py

The text reports two research passes made on 12 and 13 October 2026; section 2 of the PDF says how each
statement was checked.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "notes" / "figures"
OUT = ROOT / "notes" / "literature_review_hypotheses.pdf"
N = json.loads((FIG / "lit_numbers.json").read_text(encoding="utf-8"))
TITLE = "The eight hypotheses and the literature"

# ---------- fonts (DejaVu ships with matplotlib and covers the symbols we need) ----------
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
for name, file in [("DejaVu", "DejaVuSans.ttf"), ("DejaVu-Bold", "DejaVuSans-Bold.ttf"),
                   ("DejaVu-Oblique", "DejaVuSans-Oblique.ttf"), ("DejaVu-BoldOblique", "DejaVuSans-BoldOblique.ttf"),
                   ("DejaVuMono", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique",
                              boldItalic="DejaVu-BoldOblique")

INK, MUTED, RULE, ACCENT, SOFT = "#1b2430", "#5b6672", "#d7dcd9", "#0f4c5c", "#eef3f4"
S = {
    "title": ParagraphStyle("title", fontName="DejaVu-Bold", fontSize=22, leading=27, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="DejaVu", fontSize=12, leading=16, textColor=MUTED, spaceAfter=16),
    "h1": ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=15, leading=19, textColor=ACCENT, spaceBefore=16, spaceAfter=8,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=11.5, leading=15, textColor=INK, spaceBefore=10, spaceAfter=4,
                         keepWithNext=1),
    "body": ParagraphStyle("body", fontName="DejaVu", fontSize=10, leading=14.5, textColor=INK, spaceAfter=7, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName="DejaVu", fontSize=10, leading=14.5, textColor=INK, leftIndent=14,
                             bulletIndent=2, spaceAfter=4),
    "caption": ParagraphStyle("caption", fontName="DejaVu-Oblique", fontSize=8.8, leading=12, textColor=MUTED, spaceBefore=3, spaceAfter=12),
    "box": ParagraphStyle("box", fontName="DejaVu", fontSize=10, leading=14.5, textColor=INK, backColor=SOFT,
                          borderPadding=(8, 10, 8, 10), spaceBefore=8, spaceAfter=14, leftIndent=10, rightIndent=10),
    "lead": ParagraphStyle("lead", fontName="DejaVu", fontSize=10, leading=14.5, textColor=INK, spaceAfter=7, keepWithNext=1),
    "quote": ParagraphStyle("quote", fontName="DejaVu-Oblique", fontSize=9.6, leading=14, textColor=INK, leftIndent=14,
                            rightIndent=14, spaceAfter=7),
    "cell": ParagraphStyle("cell", fontName="DejaVu", fontSize=8.6, leading=11.4, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="DejaVu-Bold", fontSize=8.6, leading=11.4, textColor=INK),
}

# how each statement was checked; the legend is in section 2
X3 = " <font size='7.5' color='#5b6672'>[×3]</font>"
X1 = " <font size='7.5' color='#5b6672'>[×1]</font>"
AB = " <font size='7.5' color='#5b6672'>[abstract]</font>"
OWN = " <font size='7.5' color='#5b6672'>[own]</font>"


def P(text, style="body"):
    return Paragraph(text, S[style])


def B(text):
    return Paragraph(text, S["bullet"], bulletText="•")


def figure(name, caption, width=15.5 * cm):
    path = FIG / name
    w, h = PILImage.open(path).size
    img = Image(str(path), width=width, height=width * h / w)
    return KeepTogether([img, P(caption, "caption")])


def table(rows, widths, header=True):
    data = [[Paragraph(c, S["cellb"] if header and i == 0 else S["cell"]) for c in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(RULE)), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SOFT)))
    t.setStyle(TableStyle(style))
    return t


def hypothesis(code, claim, test, new_page=True):
    return ([PageBreak()] if new_page else []) + [P(f"{code}. {claim}", "h1"), P(f"<b>Your test.</b> {test}", "quote")]


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(2 * cm, 1.2 * cm, TITLE)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"page {doc.page}")
    canvas.restoreState()


story = []
# ---------------------------------------------------------------- title
story += [
    P(TITLE, "title"),
    P("What is known, what is contested, and what the top M6 teams left open. Literature review for the "
      "volatility thesis. 13 October 2026.", "subtitle"),
    P("This document goes through hypotheses H1 to H8 one at a time and says, for each, what the published "
      "literature leads you to expect, how strong that evidence is, where your test as written would mislead, and what "
      "I would change. Two sections come first: what the M6 competition established, and what the best teams did, "
      "said and left open. Every statement carries a small label that says how it was checked; section 2 explains "
      "the labels."),
]

# ---------------------------------------------------------------- 1 short version
story += [P("1. The short version", "h1"),
          B("<b>M6 skill was knowing which assets are volatile, not which will rise.</b> The teams placed 4th, 5th and "
            "8th in the forecasting track say so in their papers. The code of ranks 1 and 2 is built mainly around each "
            "asset's dispersion, and your own rebuild of rank 3 with the mean set to zero matches its submissions. A "
            "constant forecast equal to each asset's historical quintile frequencies scored 0.1570 on a 2021 hold-out. "
            "The winner scored 0.15645. The benchmark is 0.16." + X3),
          B("<b>The overconfidence finding has never been taken apart.</b> The organisers worded it as a variance "
            "statement and tested it with one pooled reliability curve for the 38 teams that beat the benchmark. Nobody "
            "has since decomposed the M6 score, fitted a shrinkage factor, or separated errors of direction from errors "
            "of dispersion. No team published a check of its own calibration." + X1),
          B("<b>A common variance factor cannot do that separation in M6.</b> In a ranking, multiplying every variance "
            "by k gives exactly the same quintile probabilities as dividing every difference in means by √k. A model "
            "with no view on direction scores the same whether its variances are right, halved or doubled. So H1 as "
            "written measures oversold direction, and the level of variance can only be tested on VOLARE." + OWN),
          B("<b>Nobody has compared machine learning and GARCH on variance calibration.</b> The published comparisons "
            "rank models by loss. On loss, with the same realised-variance inputs, boosted trees are level with HAR or "
            "slightly worse in four studies, one of them on your 40 VOLARE stocks. On coverage the indirect evidence "
            "points both ways. The one paper that states H2 outright is an unrefereed working paper whose own table "
            "supports it for one commodity out of four. H2 is open." + X1),
          B("<b>High-volatility regimes hurt every model class, and the horizon decides how much.</b> For GARCH in "
            "autumn 2008 the loss was 25% higher than usual at one day and 3.3 times higher at one month. The error has "
            "two signs: too low at the onset, too high afterwards." + X1),
          B("<b>Three tests need a design change before they can give a clean answer:</b> H1 (identification), H5 (a "
            "fourth arm, and the level measured on VOLARE), and H6 (99% coverage, because at 95% a Student-t with the "
            "same variance is within 2% of the Gaussian)."),
          Spacer(1, 6),
          table([["", "What the literature leads you to expect", "Strength of the evidence", "What I would change in the test"],
                 ["H1", "A factor above one for every model that takes a view on direction, and no effect at all for models "
                  "that do not. The pattern comes from the arithmetic of ranks, not from the models.",
                  "M6 facts: strong. The identification point is my own derivation, confirmed by simulation.",
                  "Read k as oversold direction. Add a parameter for the spread of variances between assets. Test the "
                  "level of variance on VOLARE."],
                 ["H2", "Open. Random forests under-cover and boosted trees over-cover against HAR in one study; XGBoost's "
                  "VaR exceedances are no worse than HAR's in another.",
                  "Thin and indirect. No study reports bias, Mincer-Zarnowitz slopes or coverage for trees against GARCH.",
                  "Add the mean ratio of realised to forecast variance as the level measure. Read the slope as "
                  "reaction, not level. Same refit schedule and same back-transformation for every model."],
                 ["H3", "Supported for every model class. Small at one day, large at one month. Two-sided: too low at the "
                  "onset, too high afterwards.",
                  "Good for the size of losses, weak for the sign of the error.",
                  "Split onset from aftermath. Compare regimes with QLIKE, never MSE. Report 1-day and 20-day results "
                  "separately. Small-sample tests for short windows."],
                 ["H4", "Disagreement. M6 sees relative variance and oversold direction; VOLARE sees the level. The horizons "
                  "differ, and rankings flip between sample splits of one data set.",
                  "Reasoned from several sources. No direct test exists.",
                  "Compute an M6-style relative measure on VOLARE at 20 days, so that like is compared with like."],
                 ["H5", "The mechanism is certain: squared error on the log targets a value below the mean, by about 12% at "
                  "one day. Whether a new objective beats a correction applied after fitting is doubtful.",
                  "Theory strong. Size from one working paper. For neural networks QLIKE training helped in two studies "
                  "and hurt in one. No study with boosted trees.",
                  "Add a fourth arm: log target plus correction. Measure the effect on VOLARE; a common level shift is "
                  "invisible in M6."],
                 ["H6", "At 95% the test cannot show an effect. Fat tails matter at 99%. In the COVID window a fat-tailed "
                  "model still under-covered until its variance level was raised.",
                  "Arithmetic plus four empirical papers.",
                  "Test at 99% and with the shape of the PIT histogram. Use the unit-variance Student-t. Say whether "
                  "95% is two-sided."],
                 ["H7", "Coverage can be restored; the score is where a layer fails. Past-only recalibration lowered the "
                  "loss for all 17 models at 22 days and raised it for 7 of 17 at one day.",
                  "Several sources. The finance ones are preprints.",
                  "Judge by the proper score first, coverage second. Compare a two-parameter layer with isotonic and "
                  "conformal. Twelve M6 rounds are too few to fit a layer."],
                 ["H8", "Likely supported at one day and weaker at 20 days. With GARCH structure fixed, a realised measure "
                  "replaces the squared return entirely; with realised inputs, trees are level with HAR.",
                  "Good on each half. The three-arm design itself was not found anywhere.",
                  "Define the daily arm: returns only, or returns plus high-low range. Run both horizons. One overnight "
                  "treatment for every arm."]],
                [1.0 * cm, 6.0 * cm, 4.0 * cm, 6.0 * cm]),
          ]

# ---------------------------------------------------------------- 2 method
story += [PageBreak(), P("2. How this review was made, and how to read the labels", "h1"),
          P("Two research passes, both run with web access on 12 and 13 October 2026."),
          B("<b>First pass.</b> Five search angles, 22 sources fetched, 103 claims extracted. The 25 most central claims "
            "each went to three independent checkers who were told to try to refute them against the source. 24 were "
            "confirmed and one was refuted (appendix). Those 25 all came from the M6 papers and from calibration theory."),
          B("<b>Second pass.</b> Fourteen checkers, one per source or gap, for everything the first pass had extracted "
            "but not checked: the volatility, tails, intraday and VOLARE strands, and the three best M6 forecasting "
            "teams. Each read the full text where it could be reached, quoted it, and corrected the first-pass claims."),
          table([["label", "meaning"],
                 ["[×3]", "Three independent checkers tried to refute the statement against the source and none succeeded."],
                 ["[×1]", "One checker read the source in full (journal article, working paper or code) and confirmed or "
                  "corrected the statement."],
                 ["[abstract]", "Only the abstract, or another paper's report of the source, could be read. Do not cite a "
                  "number from it before reading the paper."],
                 ["[own]", "My own derivation or calculation, not a published result. Reproducible with "
                  "notes/lit_review_figures.py."]],
                [2.2 * cm, 14.8 * cm]),
          Spacer(1, 8),
          P("Three limits to keep in mind. First, several papers were read as working papers or arXiv versions, so "
            "quotes and table numbers must be checked against the journal version before they go into the thesis. "
            "Second, three recent sources are unrefereed and have changed or may change: Brini (2026) on VOLARE, whose "
            "code repository shows 37 corrective commits after the paper was posted; Kilic (2026), whose two versions "
            "name different winning models; and the conformal-prediction preprint of Aich and others, whose headline "
            "results reversed between versions. Third, 'not found' always means 'not found in a limited search'. "
            "Section 9 lists what could not be opened."),
          ]

# ---------------------------------------------------------------- 3 M6 facts
story += [P("3. What M6 established", "h1"),
          P("The task: every four weeks, for each of 100 assets, give five probabilities that its return will land in "
            "each fifth of the cross-section. The score is the Ranked Probability Score (RPS), lower is better. Saying "
            "0.2 for everything scores exactly 0.16."),
          table([["fact", "number"],
                 ["Teams that entered; teams on the global leaderboard", "226; 163"],
                 ["Teams whose forecasts differed from the benchmark at all", "138"],
                 ["Teams with an original submission at all 12 rounds", "26"],
                 ["Teams that beat RPS 0.16", "38 (23.3%)"],
                 ["Teams that beat it in all 12 months", "3"],
                 ["Improvement of those who beat it", "less than 2.5%"],
                 ["Best three scores", "0.15645, 0.15648, 0.15649"],
                 ["Top 5% of forecasters by method, as self-described", "4 time-series, 3 machine-learning, 1 judgment, 1 unspecified"]],
                [11.0 * cm, 6.0 * cm]),
          P("Source: Makridakis, Spiliotis, Hollyman, Petropoulos, Swanson and Gaba (2025)." + X3 +
            " The method counts are their Table 7, read in the copy in <font name='DejaVuMono'>literature/m6.txt</font>.",
            "caption"),
          P("How the overconfidence result was obtained", "h2"),
          P("The organisers stated their Hypothesis 7 before the competition:", "lead"),
          P("\"Teams will be measurably overconfident in the accuracy of their forecasts, on average. Namely, forecasts "
            "will be less dispersed and have smaller variance than observed in the data.\"", "quote"),
          P("The second sentence is a statement about variance. The test is not. It is a single reliability curve: "
            "stated probabilities are sorted into bins of width 0.05, and for each bin the share of cases that came true "
            "is plotted. Probabilities above about 0.3 came true less often than stated, and very low ones more often, so "
            "the hypothesis was accepted." + X3 + " Four features of that test matter for the thesis:"),
          B("It uses only the 38 teams that beat the benchmark. It says nothing about the 125 that did not, of which "
            "about 100 were strictly worse."),
          B("It pools all five quintiles. A 0.6 on the middle quintile (too little dispersion) and a 0.6 on the top "
            "quintile (a bet on direction) fall into the same bin."),
          B("It pools all assets and all 12 rounds. There is no split by team, asset class, round or volatility regime."),
          B("Binned reliability curves are unstable: in one published example 9, 10 or 11 bins give very different "
            "pictures of the same forecasts. A binning-free version exists (Dimitriadis, Gneiting and Jordan 2021)." + X1),
          P("The same paper uses the word overconfident a second time, in its section 5, for teams taking more "
            "portfolio risk than their forecast accuracy justified. That is a separate finding about investment "
            "decisions and should not be cited for forecast calibration."),
          ]

# ---------------------------------------------------------------- 4 teams
story += [P("4. What the top teams did, said and left open", "h1"),
          P("The first three places are separated by 0.00004 RPS, so their order carries no information. Only rank 1 "
            "has a paper in the special issue; ranks 2 and 3 are documented by code and, for rank 2, a blog post."),
          table([["rank", "team and method", "variance and distribution", "what they say or flag"],
                 ["1", "Weitzenfeld. Bayesian dynamic factor model on non-overlapping 20-day returns. Mean: seven "
                  "latent factors, a coefficient on the last five days' return, an asset intercept.",
                  "Scale per asset, driven by the last five days' standard deviation and an earnings dummy, pooled by "
                  "asset class. Student-t with its own degrees of freedom per asset.",
                  "Abstract lists strengths only (modular, handles missing data, hierarchical regularisation). Nothing "
                  "on calibration or limits in any source that could be opened." + X1],
                 ["2", "Pérez Michaus, 'FinQBoost'. One XGBoost model trained straight on the five quintile indicators, "
                  "weekly samples from 2007.",
                  "No variance model, no distribution. Inputs are nine rolling standard deviations of the asset's daily "
                  "cross-sectional rank, later one RSI ratio. Output rescaled so rows sum to one and columns average 0.2.",
                  "One dispersion feature was enough to beat the benchmark. No framework guarantees it generalises "
                  "across regimes; tuned to 2022; he does not know why it works; expects to lose to 0.2 about one "
                  "month in 24." + X1],
                 ["3", "Radlwimmer. Linear spline models for the weekly mean; three years of daily returns for the "
                  "covariance, bootstrapped; Monte Carlo; rank counting.",
                  "Multivariate t with 4 degrees of freedom, covariance passed in unscaled. That doubles the simulated "
                  "variance. Daily draws summed over 20 days are close to Gaussian again.",
                  "Method in four lines. No discussion of calibration, limits or future work." + X1],
                 ["4", "Staněk (1st in the duathlon). Neural network whose parameters are produced by a second network, "
                  "trained on the RPS directly, on M6 assets plus 900 others.",
                  "Five-way probability output; no explicit variance. Predicted P(top) and P(bottom) move together.",
                  "\"The good performance of the model in terms of RPS is entirely driven by predicting volatility.\" "
                  "Predictable ranks do not imply predictable returns. One year is too short to separate skill from "
                  "luck." + X3],
                 ["5", "de Vilmarest and Werge, 'AdaVol'. GARCH-type variance updated online; class-average means; "
                  "Monte Carlo under independence.",
                  "Gaussian. One asset (the volatility fund VXX) needed its empirical distribution instead, worth "
                  "0.0004 RPS.",
                  "\"It is easy to beat the uniform benchmark because the different assets are associated to different "
                  "risks.\" Future: multivariate AdaVol, combining versions, adapting GARCH coefficients." + X3],
                 ["8", "Vilar (5th overall). Average of the asset class's and the asset's own past quintile frequencies.",
                  "None. Probabilities only.",
                  "Gains \"arise from symmetric quintile distributions\" and are \"largely non-actionable\". Whether "
                  "rank forecasts can help investment decisions \"is an outstanding question\"." + X3]],
                [1.3 * cm, 5.0 * cm, 5.1 * cm, 5.6 * cm]),
          Spacer(1, 8),
          P("What the organisers and others raised for further research", "h2"),
          B("<b>Organisers, main paper.</b> Run live competitions; have participants submit code so that methods can "
            "be re-run over longer periods in a rolling-origin design; two to five years would be needed to cover "
            "economic cycles. They propose no remedy for the overconfidence they document." + X3),
          B("<b>Organisers, follow-up paper</b> (Makridakis, Spiliotis and Michailidis 2025, 'Avoiding overconfidence'). "
            "The abstract names price volatility as a key driver of forecast deterioration and says that assuming "
            "similar probabilities for symmetric quintiles improves accuracy and portfolio efficiency, even with simple "
            "base methods. The full text is paywalled. Not known: whether 'volatility' means volatile periods or "
            "volatile assets, the exact rule, the size of the gain, and their own research agenda." + AB +
            " This is the most important paper still to read; get it through the library."),
          B("<b>Staněk, second paper, on luck.</b> Do not study the top teams alone; study how factors affect "
            "performance across the whole leaderboard." + X1),
          B("<b>Samartzis.</b> Forecasts are better for funds and for assets with low idiosyncratic volatility; simple "
            "machine learning beats deep learning." + AB),
          P("What nobody did", "h2"),
          P("None of the team papers uses the words overconfidence or calibration. No team checked its own model over "
            "a longer period. Nobody has split the RPS of the submissions into a calibration part and a skill part, or "
            "fitted a shrinkage factor to them; one extended search and the full texts above found nothing, and that "
            "search should be repeated on Google Scholar against the two organisers' papers." + X1 + " The organisers' "
            "own call, to re-run submitted methods over longer periods with a rolling origin, is what the thesis does "
            "with the released team code. That is the cleanest way to state the contribution.", "box"),
          ]

# ---------------------------------------------------------------- H1
story += hypothesis("H1", "The M6 overconfidence was a variance problem",
                    "For each model, the RPS-optimal variance inflation factor. Supported if the factor is above one for "
                    "most models. Refuted if scaling the variance up never helps, which would point to bold mean forecasts.",
                    new_page=False)
story += [P("<b>In plain words.</b> When teams said 60%, it happened far less often. H1 says the reason is that the "
            "models' return distributions were too narrow."),
          P("What the literature says", "h2"),
          B("<b>The claim is untested.</b> See section 3: a variance wording, a reliability-curve test, best teams "
            "only, all quintiles pooled." + X3),
          B("<b>The legitimate gain is about dispersion.</b> Over 2015 to 2020, stocks landed in the two extreme "
            "quintiles 28.7% and 23.7% of the time and in the middle one 14.4%; equity funds landed in the middle 27.8%. "
            "A constant forecast built from such frequencies scored 0.1570 on the last nine months of 2021, and the "
            "authors note that the step from 0.16 to that constant is bigger than the step from the constant to the "
            "winner (de Vilmarest and Werge)." + X3 + " The 0.1570 is from 2021, not the competition year; recompute it "
            "on the twelve rounds."),
          B("<b>Why bold forecasts lose.</b> Vilar splits the expected RPS into three parts and shows that moving a "
            "probability away from its average pays only if the move's covariance with the outcome exceeds half its own "
            "variance. Under low predictability almost no move clears that bar." + X3),
          B("<b>The top teams also modelled direction.</b> Rank 1 has a recent-return coefficient and latent factors, "
            "rank 2 an RSI feature, rank 3 a stack of mean models, and rank 2 writes that relative performance \"implies "
            "directional forecast as well as volatility\". So 'variance only' describes ranks 4, 5 and 8, not the "
            "podium." + X1),
          B("<b>There is a precedent for the method.</b> In weather forecasting, raw ensembles are too narrow and the "
            "fix is a variance correction fitted on past data. One standard method raised the coverage of a nominal "
            "66.7% interval from 31.1% to 68.6% (Gneiting and others 2005). In one of its two applications the fitted "
            "correction was an added constant, not a multiplier; try an additive term next to k." + X3),
          B("<b>Too-narrow intervals are common in human forecasts, but not universal.</b> Finance chiefs' 80% "
            "intervals for the S&amp;P 500 contained the outcome 36.3% of the time (Ben-David, Graham and Harvey 2013). "
            "The Bank of England's fan charts of 1997 to 2003 erred the other way: too wide, because they were "
            "calibrated on a more volatile past (Wallis 2004)." + X1),
          B("<b>Low coverage alone does not prove the variance is too small.</b> Pooling cases where a forecast is "
            "biased low with cases where it is biased high gives the same picture as too little spread; the remedy is "
            "to look regime by regime (Hamill 2001)." + X1),
          P("The problem with the test as written", "h2"),
          P("Ranks do not change when every return is divided by the same number. A model that says "
            "<i>return = mean + √k · sigma · noise</i> therefore gives the same quintile probabilities as one that says "
            "<i>return = mean / √k + sigma · noise</i>. Inflating all variances by k and shrinking all mean differences "
            "by √k are one and the same operation. Three consequences, shown in Figure 1:" + OWN),
          B("An optimal k above one means the model oversells its view on direction. 'Variance too small' and 'bold "
            "means' are the same finding in M6, not rival explanations."),
          B("For a model with no view on direction, k changes nothing. Your refutation condition, 'scaling the variance "
            "up never helps', is met by exactly the models with the cleanest design, such as your zero-mean rebuild of "
            "rank 3."),
          B("A model can be wrong about variance and still be flat in k: the green line exaggerates the differences in "
            "variance between assets and has no mean forecast at all."),
          figure("lit_inflation_factor.png", width=13.0 * cm, caption=
                 f"Figure 1. Simulation: 100 assets, half volatile and half calm, small true differences in mean. Blue: "
                 f"right variances, no view on direction; halving or doubling all its variances gives the identical line. "
                 f"Green: exaggerates the spread of variances between assets. Orange: real information on direction, "
                 f"trusted too much; it scores {N['sim_bold_k1']:.4f} at k = 1 and {N['sim_bold_best']:.4f} at k = "
                 f"{N['sim_bold_best_k']:.0f}. Shrinking its means by √k instead gives the same probabilities exactly."),
          P("This is my derivation. No statement of it was found in the M6 or return-forecasting literature; the "
            "closest published result is the scale normalisation of discrete-choice models (Train 2009)." + X1 +
            " Your decisions log already has half of it: 'a common scale factor cannot change ranks'. The equivalence "
            "is exact only for one common factor; asset-specific factors are identified."),
          P("<b>What I would change.</b> (1) Keep k, and report it as the degree to which a model oversells direction. "
            "(2) Add a second M6 parameter that is about variance: pull each asset's log variance toward the "
            "cross-sectional average by an exponent c. An optimal c below one means the model exaggerates the "
            "differences in variance between assets, the form of a variance error that M6 can see. (3) Test the level "
            "of variance on VOLARE. (4) Split each model's RPS into a calibration part and a skill part before and "
            "after the adjustment. (5) Recompute the best-constant score on the competition rounds.", "box"),
          ]

# ---------------------------------------------------------------- H2
story += hypothesis("H2", "Machine-learning models underestimate variance more than GARCH-type models",
                    "Compare inflation factors in M6, and Mincer-Zarnowitz slopes and 95 percent coverage in VOLARE, model "
                    "by model. Supported if LightGBM shows the larger factor, the larger slope and the lower coverage.")
story += [P("<b>In plain words.</b> A tree model learns averages of what it has seen; GARCH is a formula for variance. "
            "H2 says the tree model ends up with forecasts that are too low."),
          P("What the literature says", "h2"),
          B("<b>No study answers the question.</b> None of the comparisons read here reports a signed forecast error, "
            "a Mincer-Zarnowitz regression for trees against GARCH, or interval coverage for variance forecasts. "
            "Christensen and others (2023), Zhang and others (2024), Audrino and Chassot (2024) and Kilic (2026) all "
            "rank by MSE or QLIKE, and none includes a GARCH model on daily returns." + X1),
          B("<b>On accuracy, with the same realised-variance inputs, boosted trees do not beat HAR.</b> One-day MSE "
            "relative to HAR: gradient boosting 1.054, random forest 1.020, neural networks 0.954 to 0.990 (29 Dow "
            "stocks). Boosting gets worse with horizon: 1.054, 1.164, 1.219 at a day, a week, a month. On 1,445 stocks "
            "in 2022 and 2023, boosted trees: QLIKE 0.350 against 0.314 for HAR. On your 40 VOLARE stocks, XGBoost's "
            "median MSFE is 1.35 times HAR's at one day (Kilic)." + X1),
          B("<b>On coverage, the two tree families err in opposite directions.</b> In a 5% Value-at-Risk test with HAR "
            "inputs, the exceedance rate was 5.3% for HAR, about 7% for bagging and random forest (coverage rejected "
            "for 20 of 29 stocks) and 4.0% for gradient boosting, the family LightGBM belongs to (Christensen and "
            "others, Table 8). At the 99% level on the S&amp;P 500, XGBoost's exceedance rate was 1.37% against 1.48% "
            "for HAR (Kilic, Table 7)." + X1 + " Both used filtered historical simulation, which takes the quantile "
            "from past standardised returns and therefore absorbs a constant scale error; neither is a clean test of "
            "variance level."),
          B("<b>One preprint does show an overconfident LightGBM.</b> A LightGBM quantile forecaster of daily returns "
            "covered 81.0% to 85.5% at a nominal 95%, while a GARCH with Student-t errors covered about 95%. The source "
            "is weak: unrefereed, each model fitted on 192 observations, results reversed between versions." + X3),
          B("<b>GARCH on daily returns is not well calibrated either.</b> Its forecasts respond slowly to changes in "
            "level and it over-predicts when volatility is low (Koopman, Jungbacker and Hol 2005). In Mincer-Zarnowitz "
            "regressions on exchange rates, the slope was 0.854 for GARCH and 0.618 for RiskMetrics against 0.987 for a "
            "realised-volatility model (Andersen and others 2003)." + X1),
          B("<b>In M6 itself the model class did not matter at the top.</b> Rank 2 is a boosted-tree model, ranks 1 "
            "and 3 are parametric, and the three are tied to four decimals." + X1),
          B("<b>The average error of realised-variance models is over-prediction.</b> On 27 Dow stocks, HAR and "
            "network models all over-predict on average, mostly on calm days, and under-predict on turbulent days. The "
            "linear HAR shares the pattern (Zhang, Pu, Cucuringu and Dong 2025)." + X1 + " The evidence is a set of box "
            "plots, and turbulent days are picked by the outcome."),
          B("<b>Two working papers address H2 directly; neither settles it.</b> Chung (2024) writes that "
            "machine-learning models 'tend to underpredict' and GARCH models 'tend to overpredict' on four energy "
            "commodities, but his table shows it for crude oil only, driven by one spike in April 2020." + X1 + " Khan "
            "(2026) runs GARCH, HAR, LightGBM and XGBoost on the S&amp;P 500 from 2022 to 2025: no model separates "
            "overall; in 2022, the M6 year, the GARCH family wins and LightGBM is last; from 2023 the trees lead and "
            "HAR is last." + AB + " Neither reports the sign of the error for equities."),
          P("Three reasons to expect a gap, and where they come from", "h2"),
          B("<b>The log target.</b> A model trained on log variance and exponentiated without correction forecasts "
            "about 12% too low at one day (H5). The standard log-HAR benchmark carries the correction; a default "
            "LightGBM pipeline does not." + X1),
          B("<b>The refit schedule.</b> Published comparisons train the machine-learning model once and re-estimate "
            "HAR every day. In Audrino and Chassot the trees were trained on 2016 to 2020 and never refitted through "
            "2022 and 2023." + X1),
          B("<b>The range of the training data.</b> \"Being based on trees, boosted trees and random forests cannot "
            "predict out-of-sample a value greater than the maximal in-sample value\", and this hurt forecasts of "
            "variables that left their historical range in 2020 (Goulet Coulombe, Marcellino and Stevanovic 2021, on "
            "UK macroeconomic data)." + X1 + " For random forests the bound is exact. For boosting it is not a theorem, "
            "but the forecast is flat outside the range of the training inputs. LightGBM's linear-leaf option removes "
            "the limit. No paper was found that ties this to equity volatility in March 2020, and the bound applies to "
            "whatever the trees are trained on, so a target defined relative to recent variance moves the ceiling."),
          P("<b>What I would change.</b> (1) The Mincer-Zarnowitz slope is not a measure of level. In a regression of "
            "realised on forecast variance, a slope below one means the forecasts move too much, not that they are too "
            "low; and noise in the forecast pushes the slope toward zero by itself. Put the mean ratio of realised to "
            "forecast variance next to it: that is the VOLARE counterpart of the inflation factor. (2) Run the "
            "regression in levels with weights (divide through by the forecast); the plain version is driven by a few "
            "high-volatility days, and the log version is distorted by proxy noise (Patton and Sheppard 2009). (3) "
            "State the direction you expect for each of the three measures before running anything. (4) Give LightGBM "
            "the same refit schedule and the same back-transformation as the benchmarks, otherwise H2 measures the "
            "pipeline.", "box"),
          ]

# ---------------------------------------------------------------- H3
story += hypothesis("H3", "Underestimation concentrates in high-volatility regimes",
                    "The VOLARE slopes and coverage by calendar regime and by VIX tercile. Supported if the gap widens in "
                    "2020, 2022 and 2025. Refuted if the gap is constant, which would mean a level error.")
story += [P("<b>In plain words.</b> Models are fine in calm markets and too optimistic when things break."),
          P("What the literature says", "h2"),
          B("<b>For GARCH the effect depends on the horizon.</b> On the S&amp;P 500, the QLIKE loss of a threshold GARCH "
            "in September to December 2008 against 2001 to 2008 was 0.304 against 0.243 at one day and 1.380 against "
            "0.415 at one month. Across 37 other assets, one-day losses were unchanged in the crisis and one-month "
            "losses rose by a factor of 1.5 to 1.7 (Brownlees, Engle and Kelly 2011)." + X1 + " The 20-day M6 horizon "
            "is the one where the damage was done."),
          B("<b>The authors' reading:</b> \"there is always a risk that the risk will change\". A one-day forecast "
            "conditions on yesterday; a one-month forecast made in calm conditions cannot see the regime shift coming. "
            "A forecast distribution that ignores the uncertainty of future variance is too narrow by construction."),
          B("<b>Every model class loses more in crises.</b> On the S&amp;P 500, losses in the 2008 and 2020 episodes "
            "were several times those of calmer episodes for all ten models in Kilic (2026). From his Table 4, the ratio "
            "of XGBoost's loss to HAR's at one day is 1.52 in 2008 and 1.89 in the COVID window, against 1.03 and 1.02 "
            "in the two calmer episodes." + X1 + " The ratios are my arithmetic, the paper does not test them, and in "
            "the COVID window all models sit inside the same confidence set."),
          B("<b>Coverage failures cluster in the same years.</b> Rejections of 99% VaR coverage occur mostly in 2007, "
            "2008 and 2020, with some in 2025; in calm years the exceedance rate is often near zero, meaning the "
            "forecasts are too cautious (Kilic)." + X1),
          B("<b>The error has two signs.</b> GARCH lagged the peak in late 2008 and then stayed too high (Shephard and "
            "Sheppard 2010). A fat-tailed EGARCH had 2.9 to 5.1 times the expected number of VaR violations in February "
            "to May 2020 (Castillo, León and Ñíguez 2021)." + X1),
          B("<b>The machine-learning edge shrinks when volatility is high.</b> In the top tenth of days by realised "
            "variance, the gain over HAR was only 7.38%, and the log-HAR model's advantage sits almost entirely in that "
            "top tenth (Christensen and others)." + X1 + " Daily squared returns as an input also lose most "
            "accuracy when volatility is high (Liu, Patton and Sheppard 2015)."),
          B("<b>Neural networks reverse on high-volatility days.</b> On 23 NASDAQ stocks, LSTM networks beat every "
            "HAR-type model on the roughly 90% of normal days and lost to the best HAR variant on the 10% of "
            "high-volatility days (Rahimikia and Poon)." + X1 + " Those days were selected by the outcome, which makes "
            "any forecast look low. Your split by VIX tercile uses information known in advance and avoids that."),
          B("<b>Humans show the same pattern.</b> The finance chiefs' 80% intervals contained the outcome 23.0% of "
            "the time in high-VIX quarters and 51.0% in low-VIX quarters." + X1),
          B("<b>A sceptical result to cite alongside.</b> Under the model's own assumptions, a four-month stretch with "
            "one-day losses as large as autumn 2008 had a historical probability of 54.5%; at 22 days it was 1.3%. The "
            "authors conclude the crisis was no rejection of GARCH at one day." + X1 + " The calculation is in-sample."),
          P("Little was found on 2022 or 2025, and nothing on a split by VIX tercile. Khan's abstract (see H2) is the "
            "only source that isolates 2022. The one study on VOLARE with a regime split cuts the sample once, at "
            "1 March 2020, and finds the ranking of models unchanged (Brini 2026)." + X1),
          P("<b>What I would change.</b> (1) Separate the onset of a high-volatility regime from its aftermath; a "
            "single 'high-VIX' bucket mixes forecasts that were too low with forecasts that were too high. (2) Compare "
            "regimes with QLIKE. With a noisy target, MSE carries a bias proportional to the squared variance, so MSE "
            "rises in a crisis even if forecast quality is unchanged; the QLIKE bias does not depend on the level "
            "(Brownlees, Engle and Kelly). (3) Report the sign of the error, not only the loss. (4) Report one-day and "
            "20-day results side by side; the literature predicts a small effect at one and a large one at the other. "
            "(5) Short windows need small-sample inference: with 81 days and a 1% level, 0.8 violations are expected, "
            "and the COVID study used simulated p-values for that reason. Your regime dates are already fixed in "
            "advance, which is the other safeguard.", "box"),
          ]

# ---------------------------------------------------------------- H4
story += hypothesis("H4", "The ranking of models by calibration is the same in both settings",
                    "Rank models by inflation factor in M6 and by slope in VOLARE, compare the two rankings. If they "
                    "disagree, the M6 result is about cross-sectional dispersion rather than absolute variance.")
story += [P("<b>In plain words.</b> If a model is overconfident, it should be overconfident everywhere."),
          P("The literature gives four reasons to expect the rankings to disagree, and none of them is about the "
            "models."),
          B("<b>The two settings measure different things.</b> M6 cannot see the level of variance (H1); VOLARE can. "
            "The M6 factor measures oversold direction, the VOLARE slope measures how forecasts react. A model can do "
            "well on one and badly on the other." + OWN),
          B("<b>The horizons differ.</b> M6 is 20 days, the main VOLARE test is one day. Calibration can reverse with "
            "horizon: professional forecasters' intervals were too narrow two years ahead and too wide one quarter "
            "ahead (Clements 2014). On VOLARE, the log-HAR slope is 1.04 at one day and 0.53 at 22 days, and the order "
            "of econometric and pretrained models flips between the two (Brini 2026)." + X1),
          B("<b>Rankings are unstable inside a single data set.</b> In Christensen and others, neural networks beat "
            "HAR in the main split, tie it when 2008 is in the test set, and lose in a third split; the paper calls "
            "this 'broadly in line'." + X1 + " Two robust losses can also rank the same pair of imperfect forecasts "
            "differently (Patton 2011)."),
          B("<b>The M6 yardstick is noisy.</b> Five teams separated by less than 0.0005 RPS over twelve rounds; Staněk's "
            "simulations suggest his own placing would likely not be repeated." + X3),
          P("<b>What I would change.</b> Present the comparison as 'what each setting can see' and decide in advance "
            "what agreement would look like. To compare like with like, compute an M6-style measure on VOLARE: at a "
            "20-day horizon, on each date, regress the log of realised variance on the log of forecast variance across "
            "the 40 stocks. The slope says whether a model exaggerates or understates the differences in variance "
            "between assets, which is what M6 rewards. If that ranking matches M6 and the level ranking does not, the "
            "'cross-sectional dispersion' reading is shown directly.", "box"),
          ]

# ---------------------------------------------------------------- H5
story += hypothesis("H5", "The training objective causes part of the gap",
                    "The same LightGBM trained with squared error on log variance, squared error on variance, and QLIKE. "
                    "Supported if the inflation factor falls toward one under QLIKE.")
story += [P("<b>In plain words.</b> What you ask a model to minimise decides what it aims at. Ask for the wrong thing "
            "and it aims low."),
          figure("lit_loss_asymmetry.png",
                 f"Figure 2. Three losses as a function of forecast over truth. QLIKE charges {N['qlike_half']:.2f} for a "
                 f"forecast of half the true variance and {N['qlike_double']:.2f} for double. Squared error on the "
                 f"variance does the reverse. Squared error on the log is symmetric in the ratio."),
          P("What the literature says", "h2"),
          B("<b>Squared error on the variance and QLIKE aim at the same thing: the mean of the variance.</b> Of nine "
            "common losses, they are the only two for which the best possible forecast is the true conditional variance "
            "(Patton 2011, Table 1 and 2)." + X1 + " So in a large sample those two arms should not differ in level. "
            "They differ in what they are sensitive to: squared error is driven by a few high-variance days, and QLIKE "
            "punishes a forecast that is too low more than one that is too high."),
          B("<b>Squared error on the log aims below the mean.</b> The best forecast under that loss is the exponential "
            "of the mean log, which is smaller than the mean. With measurement noise in five-minute realised variance "
            "alone the shortfall is 2%. When variance itself is uncertain it grows: in a simulation with a two-factor "
            "volatility process the log loss targets 0.41 of the true expected variance, while squared error and QLIKE "
            "stay at 1.00 (Patton and Sheppard 2009)." + X1),
          B("<b>How large is it in equity data?</b> A log-HAR fitted to daily five-minute realised variance has a "
            "residual standard deviation of about 0.50 (0.516 and 0.502 for two stocks; mean 0.497 across 40 stocks for "
            "a variant; Bekierman and Manner 2018). That gives a correction factor of exp(0.25/2) = 1.13. Without it "
            "the forecast is about 12% too low." + X1 + " The factor is my arithmetic from their numbers. No figure was "
            "found for the 20-day horizon; compute it from VOLARE."),
          table([["standard deviation of the log-variance forecast error", "0.3", "0.5", "0.7", "1.0"],
                 ["plain exponential is too low by", f"{100 * N['jensen_0.3']:.0f}%", f"{100 * N['jensen_0.5']:.0f}%",
                  f"{100 * N['jensen_0.7']:.0f}%", f"{100 * N['jensen_1.0']:.0f}%"]],
                [9.0 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm]),
          P("Shortfall of exp(mean log) below the mean when log errors are Gaussian: 1 − exp(−s²/2)." + OWN, "caption"),
          B("<b>Changing only the objective changes the ranking.</b> For HAR on 1,445 stocks, least squares puts the "
            "model in the best group for 22% of stocks under QLIKE, weighted least squares for 73%; under MSE the order "
            "reverses (Audrino and Chassot)." + X1 + " Weighted least squares improved HAR's QLIKE by 3 to 24% "
            "(Clements and Preve, working paper)." + X1),
          B("<b>But a correction after fitting may do most of the work.</b> Taylor (2026) reports that aligning the "
            "forecast with the loss it is scored on gives substantial gains, and that most of them come from a simple "
            "adjustment to an ordinary log regression; estimating directly under the loss adds 'only very limited "
            "additional benefits'." + AB),
          B("<b>And the correction does not always pay.</b> Demetrescu, Golosnoy and Titova (2020) find no correction "
            "method best everywhere and recommend skipping it for highly persistent series." + AB + " Two macroeconomic "
            "studies find the uncorrected forecast has lower squared error once estimation noise is counted." + AB +
            " Those results are about squared error on point forecasts; a 12% scale error matters more for coverage."),
          B("<b>For neural networks the evidence on a QLIKE objective is two to one in favour.</b> A convolutional "
            "network trained with QLIKE beat HAR on QLIKE, MAE and MSE, while training with MSE usually failed to "
            "improve even the MSE; but QLIKE training was unstable from a random start and needed to begin from the "
            "fitted HAR (Reisenhofer, Bayer and Hautsch 2022)." + X1 + " Graph networks trained with QLIKE "
            "under-predicted less in turbulent periods than the same networks trained with MSE (Zhang, Pu, Cucuringu "
            "and Dong 2025)." + X1 + " Against that, QLIKE training made LSTM forecasts worse, most of all on "
            "high-volatility days (Rahimikia and Poon)." + X1 + " A HAR estimated directly under QLIKE is reported to "
            "give large gains (Puke and Schweikert 2026)." + AB),
          B("<b>For boosted trees nobody has done it.</b> Five searches found no study that trains LightGBM or XGBoost "
            "on QLIKE, and none that compares your three objectives for one tree model. Every tree-based paper read "
            "here trains with squared error: Christensen and others on the variance level; Zhang and others, and "
            "Audrino and Chassot, on the log, exponentiated with no correction; Kilic on volatility." + X1 + " The "
            "closest precedent boosts the log variance with two-leaf trees under the Gaussian likelihood, on monthly "
            "data (Mittnik, Robinzonov and Spindler 2015)." + X1 + " Its loss is ½ [η + y² / exp(η)] with η the log "
            "variance, and its gradient is what a custom LightGBM objective would use."),
          P("<b>What I would change.</b> (1) Add a fourth arm: log target plus correction, once with the Gaussian "
            "factor exp(s²/2) and once with the distribution-free version (the average of the exponentiated residuals). "
            "If that arm closes the gap, the cause is the back-transformation and the practical message becomes a "
            "one-line fix. (2) Measure the effect on VOLARE through the level ratio. In M6 a factor common to all assets "
            "is invisible (H1); only differences in s between assets would show. (3) Expect the log arm to be lowest "
            "and the other two to be close; if squared error on the variance and QLIKE differ a lot, that is a "
            "finite-sample effect of the few extreme days and worth reporting as such. (4) Start the QLIKE-trained "
            "model from a sensible first guess (LightGBM's initial score set to a HAR forecast or to the average "
            "variance). The one study where QLIKE training failed started from random values. (5) Your decisions log "
            "already records each model's back-transformation in its name. Keep that; three of the four comparison "
            "papers do not say what they did.", "box"),
          ]

# ---------------------------------------------------------------- H6
story += hypothesis("H6", "The missing risk is in the tails, not the variance",
                    "Keep each model's variance, swap Gaussian for Student-t innovations in the simulation. Supported if "
                    "coverage improves while the inflation factor does not move.")
story += [P("<b>In plain words.</b> Perhaps the models have the right spread and the wrong shape: real returns have "
            "more extreme days than a bell curve allows."),
          figure("lit_student_t_width.png",
                 "Figure 3. Width of the central interval of a Student-t relative to a Gaussian with the same variance. "
                 "The 99% interval is much wider for fat tails. The 95% interval is within 2% for four or more degrees of "
                 "freedom. The 90% interval is narrower."),
          table([["half-width in standard deviations", "90%", "95%", "99%"],
                 ["Gaussian", f"{N['gauss_half_90']:.3f}", f"{N['gauss_half_95']:.3f}", f"{N['gauss_half_99']:.3f}"],
                 ["Student-t, 8 degrees of freedom", f"{N['t8_half_90']:.3f}", f"{N['t8_half_95']:.3f}", f"{N['t8_half_99']:.3f}"],
                 ["Student-t, 5 degrees of freedom", f"{N['t5_half_90']:.3f}", f"{N['t5_half_95']:.3f}", f"{N['t5_half_99']:.3f}"],
                 ["Student-t, 4 degrees of freedom", f"{N['t4_half_90']:.3f}", f"{N['t4_half_95']:.3f}", f"{N['t4_half_99']:.3f}"]],
                [8.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm]),
          P("Two-sided central intervals; every distribution has variance one." + OWN, "caption"),
          P("What the literature says", "h2"),
          B("<b>At 95% the swap does almost nothing.</b> If the truth is a unit-variance Student-t with 5 degrees of "
            f"freedom, a Gaussian 95% interval covers {100 * N['t5_cov_gauss_95']:.2f}% and a Gaussian 99% interval covers "
            f"{100 * N['t5_cov_gauss_99']:.2f}%." + OWN +
            " A published version of the point: with 7 degrees of freedom the 5% quantile is −1.60 against −1.65 for the "
            "Gaussian, and the authors conclude that Gaussian risk measures work at 95% only because of the level chosen "
            "(Pafka and Kondor 2001)." + X1),
          B("<b>Backtests agree.</b> On five series, a Gaussian GARCH was not rejected at the 95% quantile for three, "
            "and where it was rejected it had too few violations; at 99% it had too many in four of five. A GARCH with "
            "unit-variance Student-t errors passed all fifteen tests (McNeil and Frey 2000)." + X1 + " A Gaussian "
            "realised-volatility model passed at 2.5%, passed or was borderline at 5%, and failed at 1% and below (Giot "
            "and Laurent, working paper)." + X1 + " One second-hand report disagrees: on NASDAQ the Gaussian GARCH had 6.21% violations at "
            "5%, which a symmetric fat tail cannot explain." + AB),
          B("<b>Fat tails do not rescue a variance that is too low.</b> In February to May 2020, an EGARCH with skewed "
            "Student-t errors had 11.8 violations per index at the 5% level against 4.1 expected. Adding a shift in the "
            "variance level cut that to 8.4 (Castillo, León and Ñíguez)." + X1 + " For the one series they show, the "
            "model without the shift estimates fatter tails: part of what looks like tail risk is a variance level that "
            "was not allowed to move."),
          B("<b>The likelihood hardly moves the variance forecast.</b> Brownlees, Engle and Kelly find 'no systematic "
            "large gains' from a Student-t likelihood, and add that this is a statement about forecasting volatility, "
            "not about tail risk." + X1 + " That supports holding the variance fixed."),
          B("<b>The swap must use the unit-variance version.</b> An ordinary Student-t with 5 degrees of freedom has "
            f"variance 5/3. Used in place of a Gaussian it widens a 95% interval by {100 * N['raw_t5_widen_95']:.0f}%, of "
            f"which {100 * N['raw_t5_sd_excess']:.0f} points are variance and under 2 are shape." + OWN + " The GARCH-t model was defined with the standardised form from the start "
            "(Bollerslev 1987)." + X1 + " M6 rank 3 used the unscaled form with 4 degrees of freedom and thereby "
            "doubled its variance."),
          B("<b>In M6 the shape washes out.</b> Daily Student-t draws summed over 20 days are close to Gaussian. Rank 5 "
            "found one asset out of 100, the volatility fund, where a non-Gaussian distribution was needed." + X3),
          B("<b>What the tail error looks like.</b> Gaussian forecasts with the right variance for fat-tailed data give "
            "a 'butterfly' histogram of probability integral transforms: too many outcomes in the middle and in both "
            "tails (Diebold, Gunther and Tay 1998)." + X1),
          P("<b>What I would change.</b> (1) Run the coverage test at 99%, and say whether 95% and 99% are two-sided. "
            "With a one-sided 5% level the Student-t quantile is closer to zero than the Gaussian, so the swap lowers "
            "coverage. (2) Add a diagnostic for shape: the butterfly in the PIT histogram, or a score that weights the "
            "tails. (3) Change the support condition. 'Coverage improves at 95%' will fail by arithmetic and would be "
            "read as refuting H6 when it does no such thing. A fair version: supported if 99% coverage and the tail "
            "score improve while 95% coverage and the level ratio do not move. (4) If 95% coverage is clearly below "
            "nominal, that is already evidence for a variance problem, because a correctly scaled Gaussian does not "
            "produce it.", "box"),
          ]

# ---------------------------------------------------------------- H7
story += hypothesis("H7", "A calibration layer removes the overconfidence",
                    "A conformal or isotonic adjustment fitted on past rounds only. Supported if coverage reaches nominal "
                    "without hurting the RPS. This is the practical message for a risk manager.")
story += [P("<b>In plain words.</b> Leave the model alone and fix its output: learn from past misses how much to widen."),
          P("What the literature says", "h2"),
          B("<b>Coverage is the easy half.</b> Four forecasters with near-perfect coverage and flat PIT histograms had "
            "scores from 0.56 to 0.78 in a standard example; the uninformative one was calibrated too. The rule is to "
            "maximise sharpness subject to calibration, and a layer that reaches nominal coverage has shown nothing "
            "until the proper score is checked (Gneiting, Balabdaoui and Raftery 2007)." + X3),
          B("<b>The idea works where it was invented.</b> In weather forecasting a variance correction fitted on a "
            "sliding 40-day window brought coverage to nominal and lowered the score by 15 to 16%. Windows under 30 "
            "days left forecasts too narrow." + X3),
          B("<b>In finance the precedent is conditional.</b> Recalibrating with the distribution of past PIT values "
            "fixed Gaussian forecasts of exchange-rate returns out of sample, but only after the volatility dynamics "
            "had been repaired; the authors say the method 'is not universally applicable' (Diebold, Hahn and Tay "
            "1999)." + X1 + " A layer that corrects shape cannot repair a variance that is wrong in some regimes."),
          B("<b>Adaptive conformal inference guarantees long-run average coverage and nothing else.</b> No guarantee "
            "on width, on a given date, or within a regime. Its bound is empty over 12 rounds and becomes useful only "
            "on long daily samples. In the authors' own volatility example, a rolling layer with a fixed level swung "
            "between under- and over-coverage, including under-coverage around 2008 (Gibbs and Candès 2021)." + X3),
          B("<b>On VOLARE, a past-only recalibration helps badly scaled forecasts and hurts good ones.</b> A "
            "recursive Mincer-Zarnowitz correction lowered QLIKE for all 17 models at 22 days, for 16 at five days, and "
            "at one day lowered it for 9 and raised it for 7 (Brini 2026, Table 11)." + X1 + " The multi-day figures "
            "probably used targets not yet observed and are likely to shrink in a revision."),
          B("<b>The one direct LightGBM test restored coverage and lost on the score.</b> A rolling conformal layer "
            "took a LightGBM quantile forecaster from 81 to 85.5% up to about 95%, but its interval score was "
            "significantly worse than GARCH-type benchmarks in 42 of 52 comparisons and never better. GARCH with "
            "Student-t errors reached the same coverage with narrower intervals and no layer. In February to April 2020 "
            "the layer covered 80% on the S&amp;P 500." + X3 + " Weak source, see section 2."),
          B("<b>Isotonic recalibration assumes the future resembles the calibration sample.</b> Its guarantee is for "
            "independent data, and its authors note that results worsen under distribution shift (Kuleshov, Fenner and "
            "Ermon 2018)." + X1 + " A regime change is a distribution shift."),
          B("<b>In M6 the layer has a code precedent and no evaluation.</b> One team's notebook wraps LightGBM in an "
            "isotonic calibrator; no result with and without it is reported, and its cross-validation is not ordered in "
            "time (Mashlakov repository)." + X1 + " The organisers' symmetric-quintile rule is a fixed adjustment, not "
            "a fitted layer."),
          B("<b>A tool for measuring what a layer could gain.</b> Refit the forecasts by isotonic regression on the "
            "evaluation sample; the drop in score is the miscalibration term, and no monotone layer can gain more "
            "(Dimitriadis, Gneiting and Jordan 2021; Arnold and others 2024)." + X1 + " It is an upper bound, because "
            "it is fitted on the same data it is scored on."),
          P("<b>What I would change.</b> (1) Make the score the first condition and coverage the second. (2) Report "
            "three layers side by side: a two-parameter one (the mean-shrink and variance-spread parameters of H1 in "
            "M6, an intercept and slope on VOLARE), isotonic, and adaptive conformal. With little data the "
            "two-parameter layer is the one most likely to survive out of sample. (3) Twelve rounds cannot fit "
            "anything. Fit the M6 layer on rounds simulated from pre-2022 history, which the rolling-origin design "
            "already produces. (4) Report coverage by regime, not only on average; every source above warns that "
            "average coverage hides the failures. (5) Report the isotonic upper bound next to the realised gain, so the "
            "reader sees how much of the available improvement a past-only layer captures.", "box"),
          ]

# ---------------------------------------------------------------- H8
story += hypothesis("H8", "Access to intraday data, not model class, is what closes the gap",
                    "HAR on realised variance against LightGBM on daily inputs, then LightGBM given the same "
                    "realised-variance inputs. Supported if the gap shrinks once both see intraday data.")
story += [P("<b>In plain words.</b> HAR looks better than machine learning because it is fed a better measurement, "
            "not because it is a better model."),
          P("What the literature says", "h2"),
          B("<b>Hold the model fixed and change the input: a clear gain.</b> In a GARCH-type recursion that is offered "
            "both the squared daily return and a realised measure, the coefficient on the squared return is typically "
            "estimated at exactly zero. The realised-measure model weighs about a week of data, GARCH about a month "
            "(Shephard and Sheppard 2010)." + X1 + " A second model of the same kind improved the likelihood of returns "
            "over GARCH in all 29 series, which its authors attribute to the information set (Hansen, Huang and Shek "
            "2012)." + X1 + " On the S&amp;P 100, realised-volatility models cut the squared error by about 65% against "
            "GARCH (Koopman, Jungbacker and Hol 2005)." + X1),
          B("<b>Hold the input fixed and change the model: little or nothing.</b> With the three HAR lags as inputs, "
            "gradient boosting is 5% worse than HAR and random forest 2% worse; trees gain only when other predictors "
            "are added (Christensen and others)." + X1 + " With 21 daily lags, pooled XGBoost has QLIKE 0.192 against "
            "0.190 for HAR; stock-by-stock it is the worst of all models (Zhang and others)." + X1 + " Audrino and "
            "Chassot, and Kilic on the 40 VOLARE stocks, agree."),
          B("<b>Finer intraday inputs help trees more than HAR.</b> Replacing daily realised variance by intraday "
            "pieces lowered QLIKE from 0.190 to 0.185 for HAR and brought pooled XGBoost to about 0.175 (Zhang and "
            "others)." + X1 + " Pooling across stocks mattered as much as the model."),
          B("<b>The advantage of intraday data fades with horizon.</b> On 18 stock indices, models built on "
            "high-frequency data beat models built on daily open-high-low-close estimators only at short horizons; by "
            "one month the difference was statistically indistinguishable for most indices (Lyócsa, Molnár and Výrost "
            "2021)." + AB + " The benefit of a more precise realised measure also shrinks as the horizon grows (Liu, "
            "Patton and Sheppard 2015)." + X1),
          B("<b>The daily range is a middle ground.</b> The log high-low range has about a quarter of the measurement "
            "error of the absolute daily return (Alizadeh, Brandt and Diebold 2002)." + X1 + " A 'daily inputs' arm that "
            "includes the range is not a daily-returns arm."),
          B("<b>For coverage, intraday data did not help in one early study.</b> A realised-volatility model gave "
            "adequate VaR but did not improve on a well-specified daily model with skewed Student-t errors (Giot and "
            "Laurent)." + X1 + " That evaluation was in-sample."),
          B("<b>M6 points the same way as the 20-day evidence.</b> The winner's only volatility input is a five-day "
            "standard deviation of daily returns; nobody at the top used intraday data." + X1),
          P("No study with your three-arm design was found: none runs the same machine-learning model once on daily "
            "inputs and once on realised-variance inputs." + X1 + " The search on this point was short."),
          P("<b>What I would change.</b> (1) Define the daily arm precisely. Returns only is the cleanest contrast; "
            "returns plus range is the realistic one. Running both costs little and answers a question the literature "
            "leaves open. (2) Run the three arms at one day and at 20 days and expect different answers. (3) Use one "
            "overnight treatment for every arm (section 5). (4) Fit HAR properly, otherwise the first gap is "
            "overstated: daily re-estimation, a window of two and a half to four years, and weighted least squares or "
            "the log form with correction. (5) Note that the evidence above is about accuracy. Whether intraday inputs "
            "close a calibration gap has not been studied by anyone.", "box"),
          ]

# ---------------------------------------------------------------- 5 pitfalls
story += [P("5. Pitfalls that cut across the hypotheses", "h1"),
          table([["pitfall", "what the sources say", "what to do"],
                 ["Trading hours against the full day",
                  "VOLARE's realised variance runs 09:30 to 16:05 with no overnight return, on unadjusted prices. Index "
                  "volatility is about 16% from realised measures and 20% from daily returns; one model puts the "
                  "trading-hours share of SPY's variance at about 75%." + X1,
                  "Your decision 2 (add the squared overnight return) handles this. Cite Hansen and Lunde (2005) for the "
                  "alternatives. One abstract reports that for single stocks estimators without the overnight term were "
                  "more accurate (Ahoniemi and Lanne 2013); read it."],
                 ["MSE across regimes",
                  "With a noisy target the MSE bias grows with the square of the variance; the QLIKE bias does not depend "
                  "on the level." + X1,
                  "QLIKE for every comparison between calm and turbulent periods."],
                 ["What a Mincer-Zarnowitz slope means",
                  "Slope below one: forecasts move too much. Noise in the forecast lowers the slope by itself. R² cannot "
                  "see a level error: adding realised variance to GARCH raised R² from 0.41 to 0.61 while the squared "
                  "error did not fall." + X1,
                  "Report intercept, slope and the mean ratio. Levels with weights, not logs."],
                 ["VaR from filtered historical simulation",
                  "The quantile comes from past standardised returns, so a constant scale error in the variance is "
                  "absorbed." + X1,
                  "Do not use it as a test of variance level. Use parametric intervals for that."],
                 ["A weak benchmark",
                  "HAR by least squares in levels loses up to 24% in QLIKE to weighted least squares. GARCH: the "
                  "asymmetric version, the longest window, re-estimated at least weekly." + X1,
                  "Fit both benchmarks as their own literature recommends before comparing."],
                 ["Unequal refit schedules",
                  "The paper that shows refit frequency drives HAR's accuracy refits HAR daily and the trees never." + X1,
                  "Same origins and same refit rule for every model. Your monthly expanding window does this."],
                 ["Overlapping 20-day windows",
                  "For multi-step forecasts the PIT series is dependent; test non-overlapping sub-series." + X1,
                  "Monthly origins give non-overlapping windows at 20 days. Keep them."],
                 ["Preprint numbers",
                  "Brini's repository shows fixes to look-ahead in bounds and in the recalibration after posting; Kilic's "
                  "monthly ARFIMA losses equal its one-day losses to three decimals." + X1,
                  "Cite version numbers. Lean on HAR-against-ML comparisons, not on which exotic model won."]],
                [3.4 * cm, 7.6 * cm, 6.0 * cm]),
          ]

# ---------------------------------------------------------------- 6 gaps
story += [P("6. Where the thesis is new", "h1"),
          P("Each line is a gap that the searches did not fill. All are limited-search results."),
          B("A comparison of tree-based machine learning and GARCH on the calibration of variance forecasts: signed "
            "error, Mincer-Zarnowitz, interval coverage. Existing work ranks by loss and leaves GARCH out."),
          B("The three-arm test of H8: one model, daily inputs against realised inputs."),
          B("The training objective varied for one tree model, with the corrected log target as a fourth arm. Loss "
            "comparisons exist for neural networks only."),
          B("A calibration check of documented M6 methods over 2015 to 2026 with a rolling origin. The organisers "
            "asked for exactly this."),
          B("A decomposition or fitted recalibration of M6 forecasts, and the identification result of H1."),
          B("Density and interval evaluation on VOLARE. The two papers on that data set evaluate point forecasts only; "
            "one lists density evaluation as future work."),
          B("Regime results for 2022 and 2025 and by VIX tercile."),
          ]

# ---------------------------------------------------------------- 7 reading
story += [P("7. Reading order", "h1"),
          P("Twelve to read first, in this order. The first three are short."),
          table([["", "paper", "read for"],
                 ["1", "Vilar (2025), arXiv 2410.08009", "Equation 5 and the discussion. Why bold forecasts lose. Nine pages."],
                 ["2", "de Vilmarest and Werge (2025), arXiv 2303.01855", "Sections 2 and 3. The best-constant benchmark."],
                 ["3", "Makridakis and others (2025), in the repo", "Hypothesis 7 and section 7 only."],
                 ["4", "Gneiting, Balabdaoui and Raftery (2007)", "Sections 1 and 2 and the simulation example. Calibration against sharpness."],
                 ["5", "Patton (2011)", "Tables 1 and 2. Which losses aim at the mean."],
                 ["6", "Brownlees, Engle and Kelly (2011)", "All of it. Regimes, horizons, QLIKE, how to fit GARCH."],
                 ["7", "Christensen, Siggaard and Veliyev (2023), in the repo", "Tables 2 and 8, appendix A.1. Trees against HAR; coverage."],
                 ["8", "Chassot and Audrino (2026), arXiv 2406.08041", "Sections 2 and 5. How to fit HAR; the refit trap."],
                 ["9", "Kilic (2026), FEDS 2025-061r1", "Tables 4, 7, 10, 11. Your 40 stocks; episodes; VaR."],
                 ["10", "Brini (2026), arXiv 2607.05291", "Sections 6 and 7. Mincer-Zarnowitz and recalibration on VOLARE. Check for a revised version."],
                 ["11", "Shephard and Sheppard (2010)", "Sections 1 to 4. Same model, better input."],
                 ["12", "Dimitriadis, Gneiting and Jordan (2021)", "The method and the decomposition. Reliability without bins."]],
                [0.9 * cm, 6.6 * cm, 9.5 * cm]),
          Spacer(1, 8),
          P("<b>To get through the library</b>, because only the abstract could be read: Makridakis, Spiliotis and "
            "Michailidis (2025), 'Avoiding overconfidence'; Weitzenfeld (2025); Taylor (2026); Demetrescu, Golosnoy and "
            "Titova (2020); Kuester, Mittnik and Paolella (2006); Hansen and Lunde (2005 and 2006); the published "
            "Clements and Preve (2021); Ahoniemi and Lanne (2013); Lyócsa, Molnár and Výrost (2021).", "box"),
          ]

# ---------------------------------------------------------------- 8 sources
SRC = [
    ("M6", "Makridakis, Spiliotis, Hollyman, Petropoulos, Swanson, Gaba (2025). The M6 forecasting competition: Bridging the gap "
     "between forecasting and investment decisions. Int. J. Forecasting 41(4), 1315-1354. arXiv 2310.13357.", "full text, arXiv v1; ×3"),
    ("M6", "Makridakis, Spiliotis, Michailidis (2025). Avoiding overconfidence: Evidence from the M6 financial competition. "
     "Int. J. Forecasting 41(4), 1395-1403. doi 10.1016/j.ijforecast.2024.10.001.", "abstract only"),
    ("M6", "Weitzenfeld (2025). Probabilistic forecasting of cross-sectional returns: A Bayesian dynamic factor model with "
     "heteroskedasticity. Int. J. Forecasting 41(4), 1477-1484. Code: github.com/DanielWeitzenfeld/m6_public.", "abstract; code read"),
    ("M6", "Pérez Michaus (2023). FinQBoost: Machine Learning for Portfolio Forecasting. Medium, 20 February. Code: "
     "github.com/miguel-data-sc/FinQBoost.", "blog (archived copy) and code"),
    ("M6", "Radlwimmer (2023). github.com/sebrad/M6.", "README and code"),
    ("M6", "Staněk (2025). Designing time-series models with hypernetworks and adversarial portfolios. Int. J. Forecasting 41(4), "
     "1461-1476. arXiv 2407.20352.", "full text, arXiv; ×3"),
    ("M6", "Staněk (2025). M6 investment challenge: The role of luck and strategic considerations. Int. J. Forecasting 41(4), "
     "1413-1427. arXiv 2412.04490.", "full text, arXiv"),
    ("M6", "de Vilmarest, Werge (2025). An adaptive volatility method for probabilistic forecasting and its application to the M6 "
     "financial forecasting competition. Int. J. Forecasting 41(4), 1514-1520. arXiv 2303.01855.", "full text, arXiv v2; ×3"),
    ("M6", "Vilar (2025). Quasi-average predictions and regression to the trend. Int. J. Forecasting 41(4), 1505-1513. "
     "arXiv 2410.08009.", "full text, arXiv; ×3"),
    ("M6", "Samartzis (2025). Predicting the relative performance among financial assets. Int. J. Forecasting 41(4), 1428-1449.", "abstract only"),
    ("M6", "Mashlakov. github.com/aleksei-mashlakov/m6_competition, notebook LGBM_classification.", "code read"),
    ("Calibration", "Gneiting, Balabdaoui, Raftery (2007). Probabilistic forecasts, calibration and sharpness. J. Royal Statistical "
     "Society B 69(2), 243-268.", "full text; ×3"),
    ("Calibration", "Gneiting, Raftery, Westveld, Goldman (2005). Calibrated probabilistic forecasting using ensemble model output "
     "statistics and minimum CRPS estimation. Monthly Weather Review 133, 1098-1118.", "full text; ×3"),
    ("Calibration", "Gibbs, Candès (2021). Adaptive conformal inference under distribution shift. NeurIPS. arXiv 2106.00170.", "full text; ×3"),
    ("Calibration", "Aich, Aich, Jain (2026). Temporal Conformal Prediction. arXiv 2507.05470, version 7.", "full text; ×3; unrefereed"),
    ("Calibration", "Dimitriadis, Gneiting, Jordan (2021). Stable reliability diagrams for probabilistic classifiers. PNAS 118(8), "
     "e2016191118. arXiv 2008.03033.", "full text, arXiv v1"),
    ("Calibration", "Arnold, Walz, Ziegel, Gneiting (2024). Decompositions of the mean continuous ranked probability score. "
     "Electronic J. Statistics 18(2), 4992-5044. arXiv 2311.14122.", "full text, arXiv v1"),
    ("Calibration", "Diebold, Gunther, Tay (1998). Evaluating density forecasts with applications to financial risk management. "
     "Int. Economic Review 39(4), 863-883.", "full text (scan)"),
    ("Calibration", "Diebold, Hahn, Tay (1999). Multivariate density forecast evaluation and calibration in financial risk "
     "management. Review of Economics and Statistics 81(4), 661-673.", "NBER working paper 6845"),
    ("Calibration", "Kuleshov, Fenner, Ermon (2018). Accurate uncertainties for deep learning using calibrated regression. ICML. "
     "arXiv 1807.00263.", "full text"),
    ("Calibration", "Hamill (2001). Interpretation of rank histograms for verifying ensemble forecasts. Monthly Weather Review "
     "129(3), 550-560.", "full text"),
    ("Calibration", "Ben-David, Graham, Harvey (2013). Managerial miscalibration. Quarterly J. Economics 128(4), 1547-1584.", "full text"),
    ("Calibration", "Moore, Healy (2008). The trouble with overconfidence. Psychological Review 115(2), 502-517.", "full text"),
    ("Calibration", "Giordani, Söderlind (2003). Inflation forecast uncertainty. European Economic Review 47(6), 1037-1059. "
     "Clements (2014). Forecast uncertainty, ex ante and ex post. J. Business and Economic Statistics 32(2), 206-216.", "working papers"),
    ("Calibration", "Wallis (2004). An assessment of Bank of England and National Institute inflation forecast uncertainties. "
     "National Institute Economic Review 189, 64-71.", "author's draft"),
    ("Calibration", "Train (2009). Discrete Choice Methods with Simulation, 2nd ed., sections 2.5 and 3.2. Cambridge University Press.", "full text"),
    ("Volatility", "Patton (2011). Volatility forecast comparison using imperfect volatility proxies. J. Econometrics 160(1), 246-256.", "working paper, Dec 2008"),
    ("Volatility", "Patton, Sheppard (2009). Evaluating volatility and correlation forecasts. Handbook of Financial Time Series, 801-838.", "working paper, Oct 2007"),
    ("Volatility", "Andersen, Bollerslev, Meddahi (2005). Correcting the errors. Econometrica 73(1), 279-296. Andersen, Bollerslev "
     "(1998). Answering the skeptics. Int. Economic Review 39(4), 885-905.", "full text; part"),
    ("Volatility", "Brownlees, Engle, Kelly (2011). A practical guide to volatility forecasting through calm and storm. J. Risk "
     "14(2), 3-22.", "working paper, Sep 2011"),
    ("Volatility", "Taylor (2026). Loss-aware forecast construction for realized variance. J. Forecasting. doi 10.1002/for.70214.", "abstract only"),
    ("Volatility", "Demetrescu, Golosnoy, Titova (2020). Bias corrections for exponentially transformed forecasts: Are they worth "
     "the effort? Int. J. Forecasting 36(3), 761-780.", "abstract only"),
    ("Volatility", "Clements, Preve (2021). A practical guide to harnessing the HAR volatility model. J. Banking and Finance 133, 106285.", "working paper 2019; published abstract"),
    ("Volatility", "Bekierman, Manner (2018). Forecasting realized variance measures using time-varying coefficient models. "
     "Int. J. Forecasting 34(2), 276-287.", "working paper"),
    ("Volatility", "Corsi (2009). A simple approximate long-memory model of realized volatility. J. Financial Econometrics 7(2), 174-196.", "full text"),
    ("Models", "Christensen, Siggaard, Veliyev (2023). A machine learning approach to volatility forecasting. J. Financial "
     "Econometrics 21(5), 1680-1727.", "full text (copy in the repo)"),
    ("Models", "Zhang, Zhang, Cucuringu, Qian (2024). Volatility forecasting with machine learning and intraday commonality. "
     "J. Financial Econometrics 22(2), 492-530.", "full text (copy in the repo)"),
    ("Models", "Chassot, Audrino (2026). HARd to beat: The overlooked impact of rolling windows in the era of machine learning. "
     "Int. J. Forecasting 42(2), 330-343. arXiv 2406.08041.", "full text, arXiv v1"),
    ("Models", "Kilic (2026). Linear and nonlinear econometric models versus machine-learning models: Evidence from "
     "realized-volatility forecasting. FEDS 2025-061r1, Federal Reserve Board.", "full text; unrefereed"),
    ("Models", "Brini (2026). Forecasting realized volatility with time series foundation models. arXiv 2607.05291, version 1.", "full text; unrefereed"),
    ("Models", "Cipollini, Cruciani, Gallo, Insana, Otranto, Spagnolo (2026). VOLatility Archive for Realized Estimates (VOLARE). "
     "arXiv 2602.19732, version 1.", "full text; unrefereed"),
    ("Models", "Zhang, Pu, Cucuringu, Dong (2025). Forecasting realized volatility with spillover effects: Perspectives from "
     "graph neural networks. Int. J. Forecasting 41(1), 377-397. arXiv 2308.01419.", "full text, arXiv v1"),
    ("Models", "Reisenhofer, Bayer, Hautsch (2022). HARNet: A convolutional neural network for realized volatility forecasting. "
     "arXiv 2205.07719.", "full text; unrefereed"),
    ("Models", "Rahimikia, Poon. Machine learning for realised volatility forecasting. Essay 2 in Rahimikia (2023), PhD thesis, "
     "University of Manchester; SSRN 3707796.", "thesis version"),
    ("Models", "Mittnik, Robinzonov, Spindler (2015). Stock market volatility: Identifying major drivers and the nature of their "
     "impact. J. Banking and Finance 58, 1-14.", "working paper 2012"),
    ("Models", "Goulet Coulombe, Marcellino, Stevanovic (2021). Can machine learning catch the COVID-19 recession? National "
     "Institute Economic Review 256, 71-109. arXiv 2103.01201.", "full text, arXiv v1"),
    ("Models", "Chung (2024). Modelling and forecasting energy market volatility using GARCH and machine learning approach. "
     "arXiv 2405.19849.", "full text; unrefereed"),
    ("Models", "Khan (2026). Volatility forecasting with machine learning: A horse race across GARCH, HAR, and tree-based models. "
     "SSRN 6663418. Puke, Schweikert (2026). J. Forecasting 45(4), 1714-1729.", "abstracts only"),
    ("Tails", "Castillo, León, Ñíguez (2021). Backtesting VaR under the COVID-19 sudden changes in volatility. Finance Research "
     "Letters 43, 102024.", "full text"),
    ("Tails", "McNeil, Frey (2000). Estimation of tail-related risk measures for heteroscedastic financial time series. "
     "J. Empirical Finance 7(3-4), 271-300.", "authors' version"),
    ("Tails", "Giot, Laurent (2004). Modelling daily Value-at-Risk using realized volatility and ARCH type models. J. Empirical "
     "Finance 11(3), 379-398.", "working paper 2001"),
    ("Tails", "Pafka, Kondor (2001). Evaluating the RiskMetrics methodology. Physica A 299, 305-310. arXiv cond-mat/0103107. "
     "Bollerslev (1987). Review of Economics and Statistics 69(3), 542-547.", "full text"),
    ("Tails", "Kuester, Mittnik, Paolella (2006). Value-at-Risk prediction: A comparison of alternative strategies. J. Financial "
     "Econometrics 4(1), 53-89.", "abstract; numbers second-hand"),
    ("Intraday", "Andersen, Bollerslev, Diebold, Labys (2003). Modeling and forecasting realized volatility. Econometrica 71(2), 579-625.", "full text"),
    ("Intraday", "Koopman, Jungbacker, Hol (2005). Forecasting daily variability of the S&amp;P 100 stock index. J. Empirical Finance "
     "12(3), 445-475.", "discussion paper"),
    ("Intraday", "Shephard, Sheppard (2010). Realising the future: forecasting with high-frequency-based volatility (HEAVY) models. "
     "J. Applied Econometrics 25(2), 197-231.", "working paper"),
    ("Intraday", "Hansen, Huang, Shek (2012). Realized GARCH. J. Applied Econometrics 27(6), 877-906.", "working paper"),
    ("Intraday", "Liu, Patton, Sheppard (2015). Does anything beat 5-minute RV? J. Econometrics 187(1), 293-311. Alizadeh, Brandt, "
     "Diebold (2002). J. Finance 57(3), 1047-1091.", "working papers"),
    ("Intraday", "Lyócsa, Molnár, Výrost (2021). Stock market volatility forecasting: Do we need high-frequency data? "
     "Int. J. Forecasting 37(3), 1092-1110.", "abstract only"),
    ("Intraday", "Hansen, Lunde (2005). A realized variance for the whole day based on intermittent high-frequency data. "
     "J. Financial Econometrics 3(4), 525-554. Ahoniemi, Lanne (2013). Int. J. Forecasting 29(4), 592-604.", "abstract; discussion paper"),
]
story += [PageBreak(), P("8. Sources", "h1"),
          P("The right-hand column says which version was read. 'Working paper' means the quotes and numbers in this "
            "document come from that version and must be checked against the journal article before they are cited."),
          table([["strand", "reference", "version read"]] + [list(r) for r in SRC], [2.4 * cm, 11.0 * cm, 3.6 * cm]),
          ]

# ---------------------------------------------------------------- 9 appendix
story += [P("9. What was refuted, and what could not be opened", "h1"),
          P("<b>Refuted, 0 votes to 3.</b> The first pass extracted the claim that the shape of a PIT histogram is the "
            "standard way to tell a dispersion error from a location error (U-shaped means too narrow, triangle-shaped "
            "means biased), and that this settles H1's variance-against-mean question. All three checkers rejected it. "
            "The source hedges the U-shape with 'often', and Hamill (2001) shows that a U-shape also arises when "
            "forecasts biased in opposite directions are pooled, and when the outcome is measured with error. Do not use "
            "PIT shape alone as the test for H1."),
          P("<b>Not opened.</b> Full texts of the papers listed at the end of section 7; the editorial of the M6 "
            "special issue; Kilic's online appendix (yearly VaR tables, loss ratios under QLIKE); the technical appendix "
            "of Brownlees, Engle and Kelly; Epstein (1969) and Murphy (1971) on the RPS; Blair, Poon and Taylor (2001); "
            "Parkinson (1980) and Garman and Klass (1980)."),
          P("<b>Not searched, or searched once.</b> The literature on ranking models in psychometrics, where the "
            "identification result of H1 may already be stated; forward citations of the two organisers' papers; a "
            "formula for how far the RPS-optimal forecast shrinks toward 0.2 as predictability falls (candidates named "
            "by a checker but not verified: Kharin and Zwiers 2003; Weigel, Liniger and Appenzeller 2009)."),
          P("<b>A lead seen only in a search summary.</b> arXiv 2608.26115 reportedly finds a boosted-tree model "
            "over-predicting the size of returns under the March 2020 shift, the opposite direction to H3. Not opened; "
            "check it before the regime chapter is written."),
          ]

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                        title=TITLE, author="Simon Gühring")
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("wrote", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")
