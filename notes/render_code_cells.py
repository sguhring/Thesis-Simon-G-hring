"""Render short code cells with their real output as PNG images for the slides.

Each cell below is executed against the panel; the printed output is captured and drawn under the
code, notebook-style. Images land in notes/figures/cell_*.png.
Run:  python notes/render_code_cells.py
"""
import contextlib
import io
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from thesis.paths import PANEL, ROOT

FIG = ROOT / "notes" / "figures"
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

# ---------- the namespace every cell runs in (same as the top of deck_numbers.py) ----------
ns = dict(np=np, pd=pd)
ns["p"] = pd.read_parquet(PANEL).sort_values(["symbol", "date"]).reset_index(drop=True)
ns["r2"] = ns["p"].ret ** 2
ns["on2"] = ns["p"].ret_overnight ** 2
ns["flag"] = ns["p"].earnings_afterclose
ns["ann_vol"] = lambda v: 100 * np.sqrt(252 * v)

CELLS = {
"a_noise": '''local = p.rv_target.groupby(p.symbol).transform(lambda s: s.rolling(22, center=True).median())
ok = local.notna() & (r2 > 0)                                   # the month's level of risk, per stock
spread = lambda m: np.exp(np.log(m[ok] / local[ok]).std())     # typical factor away from that level
print(f"typical deviation: squared return x{spread(r2):.0f}, realised variance x{spread(p.rv_target):.0f}")
yesterday = np.log(p.rv_target).groupby(p.symbol).shift(1)     # a naive forecast
r2_of = lambda y: pd.concat([y, yesterday], axis=1).dropna().corr().iloc[0, 1] ** 2
print(f"R^2 of that forecast: squared return {r2_of(np.log(r2.where(r2 > 0))):.2f}, "
      f"realised variance {r2_of(np.log(p.rv_target)):.2f}")
print(f"mean realised variance / mean squared return: {p.rv_target.mean() / r2.mean():.2f}")''',

"b_sizetest": '''truth_b = p.rv5_ss                 # (b) trading hours only
truth_a = p.rv5_ss + on2           # (a) with the squared overnight return
print(f"all stocks together: (b) {r2.mean()/truth_b.mean():.2f}   (a) {r2.mean()/truth_a.mean():.2f}")
by = p.assign(r2=r2, a=truth_a, b=truth_b).groupby("symbol")[["r2", "a", "b"]].mean()
ratio = pd.DataFrame({"(b) trading hours only": by.r2 / by.b, "(a) with the night": by.r2 / by.a})
print(ratio.describe().loc[["min", "50%", "max"]].round(2).to_string())''',

"c_cost": '''print(f"night's share of the truth: typical day {(on2 / truth_a).median():.0%}, "
      f"whole sample {on2.sum() / truth_a.sum():.0%}")
top1 = on2.nlargest(len(p) // 100).sum() / on2.sum()            # the 1% largest nights
print(f"largest 1% of nights hold {top1:.0%} of all overnight variance")
exdiv = p.dividend.fillna(0) > 0
raw_on2 = (np.log(p.open) - np.log(p.groupby("symbol")["close"].shift(1))) ** 2   # no dividend fix
print(f"ex-dividend nights ({exdiv.sum():,}): raw {raw_on2[exdiv].median():.1e}, "
      f"fixed {on2[exdiv].median():.1e}, ordinary night {on2[~exdiv].median():.1e}")''',

"d_flag": '''splits = p.split.fillna(0).replace(0, 1.0)                      # 10 on a 10-for-1 split day, else 1
later = splits.groupby(p.symbol).transform(lambda s: s[::-1].cumprod()[::-1].shift(-1).fillna(1.0))
official = p.close * later                                      # Yahoo's close in as-traded units
move = np.log(p.volare_close) - np.log(official)                # 16:00 -> 16:05
print(f"flagged days: {flag.sum()}    typical five-minute move: {move[flag].abs().median():.1%}")
ex = p[(p.symbol == "NFLX") & p.date.between("2022-04-18", "2022-04-20")]
t = pd.DataFrame({"official": official, "volare": p.volare_close, "move": move,
                  "next_on": p.ret_overnight.shift(-1)}).loc[ex.index].round(3)
for c in ["rv5_ss", "bv5_ss", "medrv5"]: t[c + "_vol%"] = ann_vol(ex[c]).round(0)
print(t.set_index(ex.date.dt.strftime("%Y-%m-%d").rename(None)).to_string())''',

"e_twice": '''nxt = p.ret_overnight.groupby(p.symbol).shift(-1)
x, y = move[flag], nxt[flag]     # 5-min move, next overnight
print(f"same sign: {(np.sign(x) == np.sign(y)).mean():.0%}")
print(f"correlation: {x.corr(y):.2f}")''',

"f_measure": '''normal = p.groupby("symbol")["rv5_ss"].transform("median")     # the stock's normal level
cands = {"keep rv5_ss": p.rv5_ss, "bv5_ss": p.bv5_ss, "medrv5": p.medrv5,
         "rv5_ss minus move^2": np.maximum(p.rv5_ss - move ** 2, p.medrv5)}
day0 = pd.Series({k: (v / normal)[flag].median() for k, v in cands.items()}, name="day 0, x normal")
print(day0.round(1).to_string())
rel = p.rv5_ss / normal
print(f"for comparison: day -1 {rel.groupby(p.symbol).shift(1)[flag].median():.1f}x, "
      f"day +1 {rel.groupby(p.symbol).shift(-1)[flag].median():.1f}x")
print(f"days where move^2 exceeds the whole day's rv5_ss: {int((move[flag] ** 2 > p.rv5_ss[flag]).sum())}")''',

"g_cost3": '''print(f"medrv5 / rv5_ss on ordinary days: {(p.medrv5 / p.rv5_ss)[~flag].median():.0%}   "
      f"replaced rows: {flag.sum()} of {len(p):,} ({flag.mean():.1%})")
print(f"final size check, mean squared return / mean truth: {r2.mean() / p.rv_target.mean():.3f}   "
      f"median stock-day: {ann_vol(p.rv_target.median()):.1f}% yearly volatility")
by_year = p.rv_target.groupby(p.date.dt.year).median().pipe(ann_vol).round(0).astype(int)
print(by_year.to_frame("median vol %").T.to_string())''',
}

# ---------- rendering ----------
S = 2                                     # render scale: 2x for crisp slides
BG_CODE, BG_OUT, INK, MUTED, COMMENT, TEAL, CORAL = "#f3f4f1", "#ffffff", "#1b2430", "#5b6672", "#6b7a86", "#0f4c5c", "#c8642b"


def render(name: str, code: str, width: int = 1664, font_px: int = 24) -> Path:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(code, ns)
    out_lines = buf.getvalue().rstrip("\n").split("\n")
    code_lines = code.split("\n")

    mono = ImageFont.truetype(str(FONT_DIR / "DejaVuSansMono.ttf"), font_px * S)
    label = ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), 20 * S)
    lh = int(font_px * 1.38 * S)
    pad, gap, bar = 26 * S, 16 * S, 6 * S
    W = width * S
    h_code = pad * 2 + lh * len(code_lines)
    h_out = pad * 2 + lh * len(out_lines)
    H = 30 * S + h_code + gap + 30 * S + h_out
    img = Image.new("RGB", (W, H), BG_OUT)
    d = ImageDraw.Draw(img)

    y = 0
    d.text((bar + 12 * S, y + 4 * S), "code", font=label, fill=MUTED); y += 30 * S
    d.rectangle([0, y, W, y + h_code], fill=BG_CODE); d.rectangle([0, y, bar, y + h_code], fill=TEAL)
    for i, line in enumerate(code_lines):
        ty = y + pad + i * lh
        k = line.find("#") if not line.lstrip().startswith("print") else -1
        if k > 0 and line[k - 1] == " ":
            d.text((bar + 18 * S, ty), line[:k], font=mono, fill=INK)
            d.text((bar + 18 * S + d.textlength(line[:k], font=mono), ty), line[k:], font=mono, fill=COMMENT)
        else:
            d.text((bar + 18 * S, ty), line, font=mono, fill=INK)
    y += h_code + gap
    d.text((bar + 12 * S, y + 4 * S), "output", font=label, fill=MUTED); y += 30 * S
    d.rectangle([0, y, bar, y + h_out], fill=CORAL)
    for i, line in enumerate(out_lines):
        d.text((bar + 18 * S, y + pad + i * lh), line, font=mono, fill=INK)

    path = FIG / f"cell_{name}.png"
    img.save(path, optimize=True)
    longest = max(d.textlength(l, font=mono) for l in code_lines + out_lines) / S
    print(f"{path.name}: {len(code_lines)} code + {len(out_lines)} output lines, {H // S}px tall, longest line {longest:.0f}px of {width}")
    for l in out_lines:
        print("   ", l)
    return path


if __name__ == "__main__":
    for name, code in CELLS.items():
        render(name, code, width=1004 if name == "e_twice" else 1664)
