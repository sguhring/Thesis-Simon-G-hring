"""Build notes/data_preparation_explained.pdf, the beginner's explainer for decisions 2 and 3.

Figures and the key numbers come from notebooks/data_preparation_tutorial.ipynb (it writes
notes/figures/*.png and notes/figures/data_prep_numbers.json), so run that notebook first:

    python -m nbconvert --to notebook --execute --inplace notebooks/data_preparation_tutorial.ipynb
    python notes/build_data_prep_pdf.py
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
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "notes" / "figures"
OUT = ROOT / "notes" / "data_preparation_explained.pdf"
N = json.loads((FIG / "data_prep_numbers.json").read_text(encoding="utf-8"))

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
    "subtitle": ParagraphStyle("subtitle", fontName="DejaVu", fontSize=12, leading=16, textColor=MUTED, spaceAfter=18),
    "h1": ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=15, leading=19, textColor=ACCENT, spaceBefore=16, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=11.5, leading=15, textColor=INK, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="DejaVu", fontSize=10, leading=14.5, textColor=INK, spaceAfter=7, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName="DejaVu", fontSize=10, leading=14.5, textColor=INK, leftIndent=14,
                             bulletIndent=2, spaceAfter=4),
    "caption": ParagraphStyle("caption", fontName="DejaVu-Oblique", fontSize=8.8, leading=12, textColor=MUTED, spaceBefore=3, spaceAfter=12),
    "box": ParagraphStyle("box", fontName="DejaVu", fontSize=10, leading=14.5, textColor=INK, backColor=SOFT,
                          borderPadding=(8, 10, 8, 10), spaceBefore=6, spaceAfter=12),
    "code": ParagraphStyle("code", fontName="DejaVuMono", fontSize=8.6, leading=11.5, textColor=INK, backColor=SOFT,
                           leftIndent=6, borderPadding=(6, 8, 6, 8), spaceBefore=4, spaceAfter=10),
    "cell": ParagraphStyle("cell", fontName="DejaVu", fontSize=8.8, leading=11.5, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="DejaVu-Bold", fontSize=8.8, leading=11.5, textColor=INK),
}


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
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(RULE)), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SOFT)))
    t.setStyle(TableStyle(style))
    return t


def pct(x, d=0):
    return f"{100 * x:.{d}f}%"


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(2 * cm, 1.2 * cm, "Preparing the data: what the truth is and why")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"page {doc.page}")
    canvas.restoreState()


story = []
# ---------------------------------------------------------------- title
story += [
    P("Preparing the data: what the truth is and why", "title"),
    P("A beginner's companion to decisions 2 and 3 of the volatility thesis. Companion notebook: "
      "<font name='DejaVuMono'>notebooks/data_preparation_tutorial.ipynb</font>. 12 October 2026.", "subtitle"),
    P("Every forecast in the thesis will be judged against one number per stock and day: the day's <b>true variance</b>. "
      "This document explains, from scratch, what that number is, where it comes from, and the two choices that define "
      "it. The explanation moves in five parts: the words you need, the two raw files, decision 2 (which hours), "
      "decision 3 (earnings nights), and the finished table. A glossary closes it. Every number quoted here is "
      "computed in the companion notebook, which you can run yourself."),
]

# ---------------------------------------------------------------- part 1
story += [P("1. The words you need", "h1")]
story += [P("Returns, and log returns", "h2"),
          P("A return is the change in price over a period. The thesis uses the <b>log return</b>, "
            "log(price today / price yesterday). For small moves it is almost the same as the percentage change, and it "
            "has two conveniences: returns over several days add up to the return over the whole stretch, and a rise of "
            "10 percent followed by a fall of 10 percent does not leave a spurious total."),
          P("Variance and volatility", "h2"),
          P("The <b>variance</b> of returns is the average of their squared deviations. It is the quantity the thesis "
            "forecasts. The <b>volatility</b> is its square root, which is in the same units as a return and easier to "
            "read. Daily volatility becomes yearly volatility when multiplied by the square root of 252, the number of "
            "trading days in a year. Apple on 2 January 2015 is a worked example:"),
          table([["quantity", "value", "meaning"],
                 ["rv5_ss", f"{N['aapl_rv']:.6f}", "the day's variance, measured from five-minute prices"],
                 ["square root", f"{N['aapl_vol_daily']:.2f}%", "the day's volatility"],
                 ["times sqrt(252)", f"{N['aapl_vol_ann']:.1f}%", "yearly volatility, the number traders quote"]],
                [3.3 * cm, 2.6 * cm, 9.6 * cm]),
          Spacer(1, 8),
          P("Why variance and not volatility? Because variances add. The variance of a day is the sum of the variances "
            "of its five-minute pieces, and the variance of twenty days is the sum of twenty daily variances. "
            "Volatilities do not add, so all the arithmetic happens in variance and only the headline numbers are "
            "converted to volatility."),
          P("Realised variance", "h2"),
          P("One daily return tells you very little about how much a stock moved that day: a stock can swing wildly and "
            "still close where it opened. Inside the day, however, there are 78 five-minute returns. Summing their squares "
            "gives the <b>realised variance</b>, a precise measurement of that day's variance rather than a guess. This is "
            "what VOLARE provides, and it is what makes the thesis possible: forecasts can be compared with a measured "
            "truth instead of a noisy proxy."),
          P("VOLARE ships several versions of the measurement. The suffix <font name='DejaVuMono'>_ss</font> means "
            "<i>subsampled</i>: the sum is averaged over several shifted five-minute grids, which removes some noise. "
            "<font name='DejaVuMono'>bv5_ss</font> is <i>bipower variation</i>, built from products of neighbouring absolute "
            "returns, so a lone jump is multiplied by a normal-sized neighbour and shrinks. "
            "<font name='DejaVuMono'>medrv5</font> is <i>median realised variance</i>, the median of each three neighbouring "
            "squared returns, so a lone jump is never the median and disappears. "
            "<font name='DejaVuMono'>rq5_ss</font>, the <i>realised quarticity</i>, measures how noisy the day's realised "
            "variance itself is; a later model (HARQ) uses it."),
          P("Adjusted prices", "h2"),
          P("When a company splits its shares ten for one, every share is suddenly worth a tenth and the raw price "
            "\"falls\" 90 percent although nobody lost anything. Yahoo's <font name='DejaVuMono'>close</font> is corrected "
            "for splits and its <font name='DejaVuMono'>adj_close</font> for splits and dividends, so returns are always "
            "computed from <font name='DejaVuMono'>adj_close</font>. VOLARE's prices are as traded on the day. NVIDIA's "
            f"split on 10 June 2024 shows the difference: as traded, the close went from {N['nvda_v7']:.2f} to "
            f"{N['nvda_v10']:.2f}, a \"price change\" of {pct(N['nvda_raw_ret'], 1)}; from adjusted prices the true change "
            f"was {pct(N['nvda_adj_ret'], 2)}. The 40 stocks have {N['n_splits']} split events and {N['n_exdiv']:,} "
            f"ex-dividend days ({pct(N['exdiv_pct'], 1)} of all rows) in the sample."),
          P("The two halves of a day", "h2"),
          P("A close-to-close return is the sum of an <b>overnight</b> part, from yesterday's close to today's open, and "
            "an <b>intraday</b> part, from today's open to today's close. VOLARE measures only the intraday hours. The "
            "notebook checks the identity over every row; the largest difference is "
            f"{N['identity_gap']:.0e}, which is rounding."),
          P("One trap: on an <i>ex-dividend day</i> the opening price is quoted after the dividend has left the share, so "
            "a 53-cent dividend looks like a 53-cent fall overnight. The real overnight move compares the open with "
            f"yesterday's close <i>minus</i> the dividend. For Coca-Cola on 13 March 2026 the raw overnight return is "
            f"{pct(N['ko_raw'], 2)}, which says the stock fell, while the correct figure is {pct(N['ko_adj'], 2)}: it rose."),
]

# ---------------------------------------------------------------- part 2
story += [P("2. The two files and how they are joined", "h1"),
          table([["file", "what one row is", "columns used"],
                 ["VOLARE realised measures", f"one stock on one trading day; {N['n_rows']:,} rows, {N['n_stocks']} stocks, "
                  f"{N['n_days']:,} days, {N['date_min']} to {N['date_max']}",
                  "open and close as traded, volume, trades, rv5_ss, bv5_ss, medrv5, rq5_ss, rsp5_ss, rsn5_ss"],
                 ["Yahoo Finance prices", f"one symbol on one day; {N['yahoo_rows']:,} rows, {N['yahoo_symbols']} symbols "
                  "(40 stocks, ^VIX, IVV), from December 2014", "open, close, adj_close, dividend, split"]],
                [3.6 * cm, 6.4 * cm, 5.5 * cm]),
          Spacer(1, 8),
          P("The two tables are joined on stock and date. Three checks follow. The result is <b>balanced</b>: all "
            f"{N['n_stocks']} stocks have all {N['n_days']:,} days. Nothing is missing in the returns or the realised "
            "measures. And the two sources agree on the price once Yahoo's split adjustment is undone: the median "
            f"difference between VOLARE's last price and the official close is {pct(N['close_med_diff'], 2)}, the 99th "
            f"percentile {pct(N['close_p99'], 2)}. On {N['n_close_diff']} days the difference exceeds 1 percent, and all of "
            "them turn out to be earnings nights. That is decision 3."),
]

# ---------------------------------------------------------------- part 3
story += [P("3. Decision 2: which hours should the truth cover?", "h1"),
          P("VOLARE's <font name='DejaVuMono'>rv5_ss</font> covers 09:30 to 16:05. The models forecast the variance of the "
            "close-to-close return, which also contains the night. Two candidate truths:"),
          B("<b>(a)</b> rv5_ss plus the squared overnight return: the same 24 hours as the forecast."),
          B("<b>(b)</b> rv5_ss alone: trading hours only, cleaner but shorter."),
          P("<b>The test.</b> Over a long sample the average squared daily return equals the average true variance if "
            "both cover the same hours. The ratio of the two should therefore be 1."),
          table([["candidate truth", "all stocks together", "by stock, lowest to highest"],
                 ["(b) trading hours only", f"{N['ratio_b']:.2f}", f"{N['ratio_b_min']:.2f} to {N['ratio_b_max']:.2f}"],
                 ["(a) with overnight", f"{N['ratio_a']:.2f}", f"{N['ratio_a_min']:.2f} to {N['ratio_a_max']:.2f} (median {N['ratio_a_med']:.2f})"]],
                [4.6 * cm, 4 * cm, 6.9 * cm]),
          Spacer(1, 8),
          figure("dec2_ratio_by_stock.png", "Figure 1. Mean squared daily return divided by the mean truth, one row per stock. "
                 "Orange is option (b), blue is option (a). Under (b) every stock's truth is 20 to almost 100 percent too small.",
                 width=12.5 * cm),
          P("<b>Why it matters.</b> The thesis asks whether models forecast too little variance. Under (b), a model that "
            "is exactly right about the close-to-close variance would look as if it forecast about 60 percent too much, "
            "and a model that under-forecasts by a third would look fine. The test would measure the missing hours, not "
            "the model."),
          P("<b>What (a) costs.</b> The overnight part is one squared return per day, so it is noisy. On a typical day it "
            f"is {pct(N['on_share_typical'])} of the truth and over the whole sample {pct(N['on_share_total'])}, but the "
            f"1 percent of days with the largest overnight moves hold {pct(N['top1_share'])} of all overnight variance. "
            f"The spread of the daily truth, measured as the standard deviation of its log, rises from {N['std_log_b']:.2f} "
            f"under (b) to {N['std_log_a']:.2f} under (a). Figure 2 shows what a single large gap does."),
          figure("dec2_meta_gap.png", f"Figure 2. Meta, early 2022, each day's truth shown as a yearly volatility. The overnight move "
                 f"of {pct(N['meta_overnight'])} on {N['meta_date']} (results published the evening before) dominates the day under "
                 "option (a) and is invisible under option (b)."),
          P("<b>The dividend refinement.</b> Measuring the overnight return from the ex-dividend close matters more than "
            f"it sounds. On the {N['n_exdiv_panel']:,} ex-dividend nights the median squared overnight move is "
            f"{N['exdiv_raw']:.1e} when measured naively and {N['exdiv_adj']:.1e} when measured correctly, against "
            f"{N['normal_night']:.1e} on an ordinary night: the naive figure makes every dividend look like a shock. The total "
            f"overnight variance changes by only {pct(N['total_on_change'], 2)}, so this is a matter of not planting a "
            "spurious pattern rather than of size."),
          P("<b>Decision 2: option (a).</b> The truth is rv5_ss plus the squared overnight return, with the overnight return "
            "measured from the ex-dividend close. Because the price is more noise, the thesis scores forecasts with losses "
            "that do not let a single huge day dominate (QLIKE and interval scores) and reports plain squared error only as "
            "a robustness check. In <font name='DejaVuMono'>config.yaml</font>: "
            "<font name='DejaVuMono'>add_overnight: true</font>, <font name='DejaVuMono'>dividend_adjust_overnight: true</font>.", "box"),
]

# ---------------------------------------------------------------- part 4
story += [P("4. Decision 3: the earnings-night problem", "h1"),
          P("The official close is at 16:00. VOLARE's window runs to 16:05. Many companies publish their results at 16:01, "
            "and the share price can jump 10 or 20 percent in those minutes. That jump lands in the last five-minute return "
            "of the day, and therefore in that day's rv5_ss, although the market was calm all day and the reaction really "
            "belongs to the next trading day."),
          P("<b>The flag.</b> A day is flagged when VOLARE's 16:05 price differs from the official 16:00 close by more than "
            f"1 percent. That gives {N['n_flag']} stock-days, and the typical five-minute move on them is "
            f"{pct(N['typical_5min_move'], 1)}. A further {N['n_border']} days sit within a hundredth of a percentage point of "
            "the line, where rounding in the official close decides; they are 1 percent moves, not earnings jumps, and the "
            "saved flag file settles them. Netflix on 19 April 2022 is the largest case."),
          table([["Netflix, 19 April 2022", "value"],
                 ["official close, 16:00", f"{N['nflx_official']:.2f}"],
                 ["VOLARE's last price, 16:05", f"{N['nflx_volare']:.2f}"],
                 ["move in those five minutes", pct(N['nflx_move'], 1)],
                 ["overnight move into 20 April", pct(N['nflx_next_on'], 1)],
                 ["rv5_ss of 19 April, as yearly volatility", f"{N['nflx_rv_ann']:.0f}%"],
                 ["bv5_ss of 19 April, as yearly volatility", f"{N['nflx_bv_ann']:.0f}%"],
                 ["medrv5 of 19 April, as yearly volatility", f"{N['nflx_med_ann']:.0f}%"]],
                [7 * cm, 3.5 * cm]),
          Spacer(1, 8),
          P("<b>Is the news counted twice?</b> The overnight return runs from the official 16:00 close to the next open, so "
            "it already contains whatever happened between 16:00 and 16:05. Figure 3 confirms it: the five-minute move "
            f"and the following overnight move have the same sign on {pct(N['same_sign'])} of the flagged days, with a "
            f"correlation of {N['corr_double']:.2f}. Under option (a) of decision 2 the jump therefore enters the truth twice, "
            "once on the flagged day through rv5_ss and once on the next day through the overnight return. The fix is to "
            "take it out of the flagged day."),
          figure("dec3_double_count.png", "Figure 3. One dot per flagged day: the move from 16:00 to 16:05 against the overnight "
                 "move into the next day. Most dots follow the diagonal: the same news is in both.", width=10.5 * cm),
          P("<b>Which measure takes it out?</b> Figure 4 lines up the eleven trading days around every flagged day and shows "
            "each of VOLARE's three measures relative to the stock's normal rv5_ss, so the three lines share one yardstick. "
            "The table adds a fourth candidate, simply subtracting the squared five-minute move from rv5_ss."),
          figure("dec3_window.png", "Figure 4. Median over the flagged days. Day 0 is the day the market was open before the "
                 "results. Day +1, the real reaction during trading hours, is high in every measure and is kept as it is."),
          table([["candidate for day 0", "day 0, multiple of normal"],
                 ["keep rv5_ss", f"{N['mult_rv']:.1f}"],
                 ["bv5_ss", f"{N['mult_bv']:.1f}"],
                 ["rv5_ss minus the squared five-minute move", f"{N['mult_strip']:.1f}"],
                 ["medrv5", f"{N['mult_med']:.1f}"],
                 [f"for comparison: day -2 and day -1 (traders waiting for results)", f"{N['mult_dm2']:.1f} and {N['mult_dm1']:.1f}"],
                 ["for comparison: day +1 (the reaction)", f"{N['mult_dp1']:.1f}"]],
                [9.5 * cm, 4.5 * cm]),
          Spacer(1, 8),
          P(f"Bipower variation still shows the day at about three times normal, so it does not remove the jump. Subtracting "
            f"the five-minute move is not well defined: on {N['n_over']} flagged days the squared move is larger than the "
            "whole day's rv5_ss, because the subsampled measure smears a jump across its neighbouring intervals. "
            f"medrv5 lands at {N['mult_med']:.1f} times normal, next to the {N['mult_dm1']:.1f} of the day before."),
          P("<b>Decision 3: medrv5 on the flagged days.</b> The jump then enters the truth once, on the day whose "
            f"close-to-close return actually contains it. The cost: on an ordinary day medrv5 is {pct(N['med_ratio_ordinary'])} "
            f"of rv5_ss, so the {N['n_flag']} replaced days run about 7 percent low; that is {N['n_flag']} of {N['n_rows']:,} rows. "
            "The flag itself is kept as a column, so models can use it as a feature and the results can be split by it. "
            "In <font name='DejaVuMono'>config.yaml</font>: <font name='DejaVuMono'>earnings_days: medrv5</font>; "
            "<font name='DejaVuMono'>keep</font> and <font name='DejaVuMono'>bv5</font> stay available for a robustness column.", "box"),
]

# ---------------------------------------------------------------- part 5
story += [P("5. The finished table", "h1"),
          P("With both decisions applied, the true variance of a stock-day is the intraday measure (rv5_ss, or medrv5 on a "
            "flagged day) plus the squared overnight return. The table also carries three market-wide columns: the VIX "
            "level, the return of the IVV fund as a stand-in for the S&P 500, and a market-wide realised variance, the "
            "typical rv5_ss across the 40 stocks on each day. The main columns:"),
          table([["column", "meaning"],
                 ["symbol, date", "the stock and the trading day; one row each"],
                 ["ret", "close-to-close log return from the adjusted close"],
                 ["ret_overnight, ret_intraday", "the two halves of ret; overnight is dividend-aware"],
                 ["rv5_ss, bv5_ss, medrv5", "VOLARE's three measures of the day's intraday variance"],
                 ["rq5_ss, rsp5_ss, rsn5_ss", "quarticity and the positive and negative semivariances, inputs for later models"],
                 ["earnings_afterclose", "True on the 459 after-close earnings days"],
                 ["rv_intraday_used", "which intraday measure went into the truth that day"],
                 ["rv_target, log_rv_target", "the true variance and its log; the number every forecast is scored against"],
                 ["vix, mkt_ret, mkt_rv", "VIX level, IVV return, market-wide realised variance"]],
                [4.6 * cm, 10.9 * cm]),
          Spacer(1, 8),
          P(f"The median true variance is {N['target_med']:.2e}, which is a yearly volatility of {N['target_ann']:.1f}%. "
            f"The size check passes: the mean squared return divided by the mean truth is {N['r2_over_target']:.3f}. "
            f"Figure 5 shows how the typical stock-day moved through the sample: about {N['vol_calm']:.0f}% in a calm "
            f"year like 2017, {N['vol_2020']:.0f}% in 2020 and {N['vol_2022']:.0f}% in 2022."),
          figure("panel_vol_by_year.png", "Figure 5. Median of the true variance over all 40 stocks in each year, shown as a "
                 "yearly volatility. 2026 covers January to August."),
          P("Features, and the rule that protects the whole thesis", "h2"),
          P("A forecast made at the end of day t may use only what was known by then. Every <b>feature</b> is therefore "
            "built from day t and earlier: for example the average log variance over the last 1, 5 and 22 days, which are "
            "the inputs of the HAR model. Every <b>target</b> is built from day t+1 onwards: y_h1 is the log of tomorrow's "
            "true variance, and y_h20 the log of the average true variance over the next 20 trading days. Mixing the two "
            "is called look-ahead, and it is the one mistake that would make every result in the thesis worthless. The "
            "notebook checks the shifted columns against the pipeline's feature table."),
          P("How to rebuild everything", "h2"),
          P("The notebook is for learning. The real dataset is built by two scripts that read the same settings from "
            "<font name='DejaVuMono'>config.yaml</font>:"),
          Preformatted("python -m thesis.data.build_panel     # data/processed/panel.parquet\n"
                       "python -m thesis.features             # data/processed/features.parquet\n"
                       "python -m pytest -q                   # scoring tests", S["code"]),
          P("The relevant settings and their current values:"),
          table([["key in config.yaml", "value", "decision"],
                 ["target: intraday_measure", "rv5_ss", "the subsampled realised variance is the intraday truth"],
                 ["target: add_overnight", "true", "decision 2, option (a)"],
                 ["target: dividend_adjust_overnight", "true", "decision 2, overnight measured from the ex-dividend close"],
                 ["target: earnings_days", "medrv5", "decision 3; keep and bv5 remain for robustness"],
                 ["target: log_target", "true", "models forecast the log of the variance"]],
                [5.2 * cm, 1.8 * cm, 8.5 * cm]),
]

# ---------------------------------------------------------------- glossary
story += [PageBreak(), P("Glossary", "h1"),
          table([["term", "meaning"],
                 ["Log return", "log(P today / P yesterday). Nearly the percentage change; adds up over days."],
                 ["Variance", "Average squared deviation of returns; the quantity the thesis forecasts."],
                 ["Volatility", "Square root of the variance, in the units of a return. Yearly = daily times sqrt(252)."],
                 ["Realised variance (RV)", "A day's variance measured from inside the day: the sum of squared five-minute returns."],
                 ["Subsampled (_ss)", "The measure averaged over several shifted five-minute grids; less noisy."],
                 ["Bipower variation (bv)", "Sum of products of neighbouring absolute returns; shrinks jumps."],
                 ["Median RV (medrv)", "Median of each three neighbouring squared returns; removes a lone jump."],
                 ["Realised quarticity (rq)", "How noisy the day's RV itself is; used by the HARQ model."],
                 ["Semivariances (rsp, rsn)", "RV from positive and from negative five-minute returns separately."],
                 ["Overnight / intraday", "The close-to-open and open-to-close parts of a daily return."],
                 ["Ex-dividend day", "The day a dividend leaves the share price; the open is quoted without it."],
                 ["Adjusted close", "Price corrected for splits and dividends; the right basis for returns."],
                 ["Panel", "A table with one row per (stock, day). Balanced means every stock has every day."],
                 ["Parquet", "A compact binary table format; faster and smaller than CSV."],
                 ["Look-ahead", "Using information from after the forecast date; the error to avoid."],
                 ["QLIKE", "A loss for variance forecasts that punishes under-forecasts more than over-forecasts."]],
                [4.2 * cm, 11.3 * cm]),
          ]

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                        title="Preparing the data: what the truth is and why", author="Simon Gühring")
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("wrote", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")
