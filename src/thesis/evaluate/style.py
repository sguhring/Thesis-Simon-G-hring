"""One palette and one set of matplotlib settings for every manuscript figure.

The manuscript is printed, so only the light surface is used. Colours are the validated default
palette of the data-visualisation guidance: categorical slots 1 to 3 (blue, orange, aqua) pass the
colourblind-separation and lightness checks on this surface as an all-pairs set, which is the hard
case (scatter and line charts, where any two marks can sit side by side). Slot 3 sits just below the
3:1 contrast target, so every figure that uses it carries a legend, direct labels and the numbers in
`manuscript/tables/scores_volare.md`.

Text never wears a series colour: labels, values and axis text use the ink tokens, and identity comes
from the coloured mark beside them.
"""
from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb

SURFACE = "#fcfcfb"
INK = "#0b0b0b"          # primary
INK_2 = "#52514e"        # secondary: values and direct labels
MUTED = "#898781"        # axis labels, de-emphasised marks
GRID = "#e1e0d9"         # hairline gridline
AXIS = "#c3c2b7"         # baseline / reference rule

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]      # categorical slots 1-3, in fixed order
BLUE, ORANGE, AQUA = SERIES
BLUE_RAMP = {100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef", 300: "#6da7ec",
             350: "#5598e7", 400: "#3987e5", 450: "#2a78d6", 500: "#256abf", 550: "#1c5cab",
             600: "#184f95", 650: "#104281", 700: "#0d366b"}
RED_POLE = "#d03b3b"     # the documented warm pole of the diverging pair
NEUTRAL = "#f0efec"      # its neutral midpoint: must read as "nothing"

FIG_W = 6.3              # text width of the thesis page, in inches


def oklab_lightness(colour: str) -> float:
    """OKLab L of a colour, used to check that a ramp really is monotone in lightness."""
    r, g, b = to_rgb(colour)
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    m = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                  [0.2119034982, 0.6806995451, 0.1073969566],
                  [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(m @ np.array(lin))
    return float(np.array([0.2104542553, 0.7936177850, -0.0040720468]) @ lms)


def _oklab(colour: str) -> np.ndarray:
    r, g, b = to_rgb(colour)
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    m = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                  [0.2119034982, 0.6806995451, 0.1073969566],
                  [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(m @ np.array(lin))
    return np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                     [1.9779984951, -2.4285922050, 0.4505937099],
                     [0.0259040371, 0.7827717662, -0.8086757660]]) @ lms


def _from_oklab(lab: np.ndarray) -> tuple[float, float, float]:
    lms = (np.array([[1.0, 0.3963377774, 0.2158037573],
                     [1.0, -0.1055613458, -0.0638541728],
                     [1.0, -0.0894841775, -1.2914855480]]) @ lab) ** 3
    lin = np.array([[4.0767416621, -3.3077115913, 0.2309699292],
                    [-1.2684380046, 2.6097574011, -0.3413193965],
                    [-0.0041960863, -0.7034186147, 1.7076147010]]) @ lms
    srgb = [12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055 for c in lin]
    return tuple(float(np.clip(c, 0.0, 1.0)) for c in srgb)


def diverging_cmap(n_per_arm: int = 32) -> LinearSegmentedColormap:
    """Blue (better) to neutral to red (worse), interpolated in OKLab so each arm is monotone in
    lightness. The cool pole is the step of the documented blue ramp whose lightness matches the warm
    pole, so the two arms are balanced; both arms get the same number of steps. Checked, not eyeballed:
    the function raises if either arm is not monotone."""
    target = oklab_lightness(RED_POLE)
    cool = min(BLUE_RAMP.values(), key=lambda c: abs(oklab_lightness(c) - target))
    mid = _oklab(NEUTRAL)
    arms = []
    for pole in (cool, RED_POLE):
        a, b = _oklab(pole), mid
        steps = [a + (b - a) * t for t in np.linspace(0.0, 1.0, n_per_arm)]
        lightness = [s[0] for s in steps]
        if not np.all(np.diff(lightness) > 0):
            raise ValueError(f"the {pole} arm is not monotone in lightness")
        arms.append([_from_oklab(s) for s in steps])
    colours = arms[0] + arms[1][::-1][1:]
    return LinearSegmentedColormap.from_list("better_worse", colours)


def use_style() -> None:
    """Thin marks, recessive solid hairline grid, no top or right spine, ink-token text."""
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "legend.fontsize": 7.5,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK_2,
        "axes.titlecolor": INK, "axes.spines.top": False, "axes.spines.right": False,
        "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "lines.linewidth": 1.6, "lines.solid_capstyle": "round",
        "legend.frameon": False, "figure.dpi": 150, "savefig.dpi": 300,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def value_grid(ax, axis: str = "x") -> None:
    """Hairline grid on the value axis only, behind the marks."""
    ax.grid(True, axis=axis, zorder=0)
    ax.set_axisbelow(True)


def save(fig, name: str, figures_dir) -> list:
    """Write the figure as PDF (for the Quarto PDF) and PNG (for the docx output)."""
    out = []
    for ext in ("pdf", "png"):
        path = figures_dir / f"{name}.{ext}"
        fig.savefig(path)
        out.append(path)
    plt.close(fig)
    return out
