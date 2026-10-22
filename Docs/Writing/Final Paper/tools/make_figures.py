#!/usr/bin/env python3
"""Draw the paper's figures from the pipeline's tables.

What this script does
---------------------
It reads the CSV tables that the analysis pipeline deposits, takes one cell for
each value it plots, and writes six figures, each as a PDF and a PNG, to
``figures/``:

Main text

* ``fig1_design``: (a) one of the ten originals with its Slight and Dramatic
  versions; (b) the five studies: what varied between and within
  participants, what they rated, and how many were analyzed.
* ``fig2_results``: the label's effect as dumbbells. Each row shows the mean
  rating under the Human label (filled circle) and under the AI label (open
  diamond) on the 1-to-5 scale, joined by a line; a second column redraws the
  gap between them (Human minus AI) with its 95 percent interval, beside a
  zero line, at the same millimeters per rating point. (a) Originals: Study 1's
  creativity and effort, and the effort gap minus the creativity gap (H2, in
  gray); Study 3's creativity and effort at each stated time, the 100-hour
  rows marked with a dagger. (b) Creativity of the second work, Studies 2, 4
  and 5 at None, Slight and Dramatic.

Supplementary Information

* ``figS_other_ratings``: the layout of Figure 2b for transformativeness (a)
  and essence change (b).
* ``figS_study1_raincloud``: Study 1's creativity and effort under each label:
  one dot per participant (the mean of that person's ratings), a half-violin
  (a smoothed outline of how the dots spread), the label means and the gap.
* ``figS_study5_editing_time``: Study 5's creativity gap at each level of
  modification, one panel per stated editing time (exploratory).
* ``figS_pooled_penalty``: the gap on second works pooled over Studies 2, 4
  and 5, and pooled without Study 4, one panel per rating (exploratory).

Every plotted value is read from one named cell, or computed from named cells
by a rule stated beside it. The comment beside each read names the table
(relative to ``Analysis/R Analysis Pipeline``), the row and the column. When
the script finishes it writes ``figures/plotted_values.csv``: every plotted
value with its figure and panel, table, row and column, how it was derived if
it was not copied, and the SHA-256 checksum (a fingerprint that changes if the
file changes) of its table. The participant dots of the Study 1 raincloud are
recorded there one per row, sorted by value within each label and rating, with
no participant identifier; the script never writes an identifier anywhere.

Every interval is a 95 percent interval. The script checks each one against
its table's own estimate, standard error and degrees of freedom (estimate plus
or minus t times the standard error, where t is the 97.5th percentile of the t
distribution with those degrees of freedom) and stops if they disagree, so an
interval at another level cannot slip in. One table gives no 95 percent
interval: ``Study 5/tables/study5_equivalence_source.csv`` holds a 90 percent
interval with its standard error and degrees of freedom. The script first
checks that the 90 percent interval is estimate plus or minus t(0.95, df)
times se, then derives the 95 percent interval as estimate plus or minus
t(0.975, df) times se. Those derived intervals are marked 'derived' in
``plotted_values.csv``.

Where the pipeline is
---------------------
By default the pipeline folder is found from this file's own location:
``../../../../Analysis/R Analysis Pipeline`` (tools -> Final Paper -> Writing
-> Docs -> project root), as in ``make_numbers.py``. To read another copy, set
the environment variable ``PIPELINE_DIR`` to that copy's ``R Analysis
Pipeline`` folder. To write the figures somewhere other than ``figures/``, set
``FIGURES_DIR``. The three stimulus images come from
``Cross-study/image_check/stimuli/`` inside the pipeline, and each is checked
against the SHA-256 checksum that ``stimuli_manifest.csv`` records for it.

When it stops
-------------
The script stops, and writes no figure, if

* a table, a row, a column or an image is missing, a row description matches
  no row or more than one row, or a cell is empty or not a number;
* an image's checksum differs from the manifest;
* a status cell does not say what the captions say (for example a 'role',
  'correction', 'analysis_status', 'survives_holm_at_05' or 'verdict' cell);
* a table states a registered bound other than Study 2's, or that bound is not
  half of Study 1's creativity gap;
* an interval does not match its estimate, standard error and degrees of
  freedom;
* a gap does not equal the Human-label mean minus the AI-label mean drawn
  beside it (to 1e-9), Study 1's means differ from its model's predicted means,
  H2 differs from the effort gap minus the creativity gap, or Study 3's
  registered decision does not rest on the 100-hour gap drawn;
* Study 1's participant means do not reproduce ``study1_marginal_means.csv``
  (count, mean and standard deviation in each cell) or the analyzed N;
* a fact a caption states about the data no longer holds: that Study 1's
  participant means spread more under the AI label on both ratings, more on
  effort than on creativity (raincloud); that Study 4's creativity gap lies
  below zero at every level with no p-value under .05, and that the pooled fits
  converged and are singular (pooled figure);
* the gap column is not drawn at the rating column's millimeters per point;
* any text is smaller than 7 pt, runs past the figure's edge, overlaps other
  text, or a row label runs into the plotting area;
* a title is not centered, or a bold text is neither a centered title, a
  panel letter at a panel's top-left nor a row-group heading.

How to run
----------
    python3 tools/make_figures.py

from the Final Paper folder (or from anywhere: paths are found from this
file). It needs Python 3.12 with matplotlib and Pillow (tested with
matplotlib 3.8.4 and Pillow 10.3.0) and uses no other package. Two runs on the
same tables write byte-identical files.

Style
-----
One style for every figure, set by the lead author on 21 October 2026. Sizes
follow Nature Communications: 183 mm wide (double column), Arial, no text
under 7 pt at that size. Text in a figure is only what a reader needs to
decode the marks, plus at most one short guard line where a misreading is
likely; every other word belongs in the caption. Titles are centered over
what they title, or absent; bold panel letters sit at each panel's top-left.
Okabe-Ito colors: the Human label is vermilion with a filled circle, the AI
label blue with an open diamond (drawn on top, so both show where the means
nearly coincide), so the figures also read in grayscale. Gaps are black
squares with black 95 percent interval lines; everything else is gray. Every
gap axis is drawn at 22 mm per rating point, the scale of the rating axis.
Figure 1 uses no study colors, because vermilion and blue mean the labels.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle  # noqa: E402
from matplotlib.text import Text  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402
from PIL import Image  # noqa: E402

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
DEFAULT_PIPELINE = HERE / ".." / ".." / ".." / ".." / "Analysis" / "R Analysis Pipeline"
PIPELINE = Path(os.environ.get("PIPELINE_DIR", str(DEFAULT_PIPELINE))).resolve()
STIMULI = PIPELINE / "Cross-study" / "image_check" / "stimuli"
OUT_DIR = Path(os.environ.get("FIGURES_DIR", str(PAPER / "figures"))).resolve()

# The artwork shown in Figure 1: its original and its two second works. Its
# Slight version keeps the original's frame (the image check found that seven
# of the ten Slight versions were also cropped or resized; this one was not).
# It is printed in color, because the Slight edit changes color and contrast.
ARTWORK = "3Figure"

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

MM = 1.0 / 25.4                         # inches per millimeter
W = 183.0                               # figure width, mm (Nature Communications double column)

FONTS = ["Arial", "Helvetica", "DejaVu Sans"]
PT_TEXT = 7.0                           # the smallest text in any figure, and most text
PT_TITLE = 7.5                          # centered titles (bold)
PT_LETTER = 8.0                         # panel letters (bold)

INK = "#1a1a1a"
INK_SOFT = "#555555"
GRID = "#dedede"
ROWLINE = "#ebebeb"
LINK = "#ababab"
ZERO = "#808080"
SHADE = "#f1f1f1"                       # band behind alternate studies
H2_INK = "#7a7a7a"                      # Study 1's tested difference of gaps (H2)
CARD_FILL = "#f4f4f4"
RULE = "#bdbdbd"
HUMAN_COLOR = "#D55E00"                 # Okabe-Ito vermilion
AI_COLOR = "#0072B2"                    # Okabe-Ito blue
HUMAN_CLOUD = "#F2C7A8"                 # vermilion mixed with white, for the filled half-violin
MINUS = chr(0x2212)                     # true minus sign
DAGGER = chr(0x2020)

# The two label marks. The AI diamond is open and drawn above the Human circle.
HUMAN = dict(marker="o", ms=4.6, mfc=HUMAN_COLOR, mec="white", mew=0.5)
AI = dict(marker="D", ms=4.4, mfc="none", mec=AI_COLOR, mew=1.1)
Z_HUMAN, Z_AI = 3, 4

LABELS = ("Human", "AI")
LEVELS = ["None", "Slight", "Dramatic"]
LEVEL_ROWS = [("None", "None"), ("Slight", "Slight"), ("Dramatic", "Dramatic")]
AI_MADE = "Every image was made with AI; only the label differed."
NOT_COMPARABLE = ("The rise across levels (within people) and the gap between labels "
                  "(between people) cannot be compared in size.")

# One scale for every rating axis and every gap axis: millimeters per rating point.
SCALE = 22.0
RATE_LIM = (0.8, 5.1)
GAP_LIM = (-0.5, 1.3)                   # Figure 2, Supplementary other ratings, raincloud
GAP_LIM_SUPP = (-0.5, 0.8)              # the two exploratory gap-only figures
RATE_TICKS = [1, 2, 3, 4, 5]
GAP_TICKS = [-0.5, 0.0, 0.5, 1.0]
GUTTER = 7.0                            # between the rating column and the gap column, mm
RIGHT_PAD = 3.0
LABEL_X = 1.5                           # left edge of row-group headings and panel letters, mm
ROW_INDENT = 3.5
SUB_INDENT = 7.0

plt.rcParams.update({
    "font.family": FONTS,
    "font.size": PT_TEXT,
    "axes.linewidth": 0.6,
    "axes.edgecolor": INK,
    "xtick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "xtick.major.pad": 1.8,
    "xtick.labelsize": PT_TEXT,
    "xtick.color": INK,
    "axes.unicode_minus": True,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 300,
})


class SourceError(Exception):
    """A table, row, column, cell or image the figures need is missing or unusable,
    or a check on it failed."""


# ---------------------------------------------------------------------------
# Reading tables
# ---------------------------------------------------------------------------

_TABLES: dict[str, list[dict[str, str]]] = {}
_CHECKSUMS: dict[str, str] = {}
PLOTTED: list[dict[str, str]] = []


def _table(rel: str) -> list[dict[str, str]]:
    if rel not in _TABLES:
        path = PIPELINE / rel
        if not path.is_file():
            raise SourceError(f"table not found: {rel} (looked in {PIPELINE})")
        raw = path.read_bytes()
        _CHECKSUMS[rel] = hashlib.sha256(raw).hexdigest()
        # The csv module keeps every cell as text, so a level named 'None'
        # stays 'None' and is never read as a missing value.
        _TABLES[rel] = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        if not _TABLES[rel]:
            raise SourceError(f"table has no rows: {rel}")
    return _TABLES[rel]


def _matches(cell: str, wanted: str) -> bool:
    """Exact match, '^text' for a prefix, '~text' for a substring (as in make_numbers.py)."""
    if wanted.startswith("^"):
        return cell.startswith(wanted[1:])
    if wanted.startswith("~"):
        return wanted[1:] in cell
    return cell == wanted


def _describe(row: dict[str, str]) -> str:
    parts = []
    for col, wanted in row.items():
        if wanted.startswith("^"):
            parts.append(f"{col} starts '{wanted[1:]}'")
        elif wanted.startswith("~"):
            parts.append(f"{col} contains '{wanted[1:]}'")
        else:
            parts.append(f"{col}={wanted}")
    return "; ".join(parts) if parts else "the only row"


def text_cell(rel: str, row: dict[str, str], column: str) -> str:
    rows = _table(rel)
    for col in list(row) + [column]:
        if col not in rows[0]:
            raise SourceError(f"{rel}: no column '{col}'")
    hits = [r for r in rows if all(_matches(r[c], w) for c, w in row.items())]
    if len(hits) != 1:
        raise SourceError(f"{rel}: the row '{_describe(row)}' matches {len(hits)} rows, not 1")
    return hits[0][column].strip()


def _float(rel: str, row: dict[str, str], column: str) -> tuple[float, str]:
    cell = text_cell(rel, row, column)
    where = f"{rel} [{_describe(row)}] column {column}"
    if cell == "" or cell.upper() in {"NA", "NAN", "INF", "-INF", "TRUE", "FALSE"}:
        raise SourceError(f"{where}: the cell is '{cell}', not a number")
    try:
        return float(cell), cell
    except ValueError as exc:
        raise SourceError(f"{where}: the cell '{cell}' is not a number") from exc


def record(figure: str, what: str, value: str, rel: str, row: str, column: str,
           derivation: str = "") -> None:
    PLOTTED.append({"figure": figure, "what": what, "value": value, "derivation": derivation,
                    "file": rel, "row": row, "column": column})


def num(figure: str, what: str, rel: str, row: dict[str, str], column: str) -> float:
    """Read one numeric cell and record it as a plotted value."""
    value, cell = _float(rel, row, column)
    record(figure, what, cell, rel, _describe(row), column)
    return value


def check_num(rel: str, row: dict[str, str], column: str) -> float:
    """Read one numeric cell used only for a check (not plotted, not recorded)."""
    return _float(rel, row, column)[0]


def expect(rel: str, row: dict[str, str], column: str, wanted: str) -> None:
    """Stop unless a text cell (a status, contrast or fit flag) says what the caption says."""
    cell = text_cell(rel, row, column)
    if not _matches(cell, wanted):
        raise SourceError(f"{rel} [{_describe(row)}] column {column}: expected "
                          f"'{wanted}', found '{cell}'")


def same(where: str, a: float, b: float, tol: float = 1e-9) -> None:
    """Stop unless two values that must agree do agree."""
    if abs(a - b) > tol:
        raise SourceError(f"{where}: {a!r} differs from {b!r} (tolerance {tol})")


# ---------------------------------------------------------------------------
# The t quantile (standard library only)
# ---------------------------------------------------------------------------

def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularized incomplete beta function (Lentz's method)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            return h
    raise SourceError("incomplete beta did not converge")


def _betainc(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    tail = 0.5 * _betainc(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


def t_quantile(p: float, df: float) -> float:
    """The p-th quantile (p above 0.5) of the t distribution, by bisection.

    Checked against scipy.stats.t.ppf(0.975, df) for df = 3, 19.5, 54, 55 and
    1000: the two agree to at least 12 significant digits.
    """
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def check_interval(where: str, est: float, se: float, df: float, lo: float, hi: float,
                   level: float) -> None:
    """Stop unless [lo, hi] is est plus or minus t((1 + level) / 2, df) times se."""
    half = t_quantile((1.0 + level) / 2.0, df) * se
    if abs((est - half) - lo) > 1e-6 or abs((est + half) - hi) > 1e-6:
        raise SourceError(f"{where}: the interval {lo} to {hi} is not the {level:.0%} interval "
                          f"from estimate {est}, se {se} and df {df}")


# ---------------------------------------------------------------------------
# Readers: gaps (Human minus AI) with their 95% intervals
# ---------------------------------------------------------------------------

def study1_h1(fid: str, dimension: str) -> tuple[float, float, float]:
    """Study 1's registered confirmatory H1 contrast (Human minus AI) on one rating
    (creativity or effort), with its 95% interval."""
    # Study 1/tables/study1_confirmatory_family.csv, row hypothesis=H1; test contains
    # '<dimension>', columns estimate, se and df: the same cell as \SOneHOneCreatDiff
    # (creativity) or \SOneHOneEffDiff (effort).
    fam = "Study 1/tables/study1_confirmatory_family.csv"
    fam_row = {"hypothesis": "H1", "test": f"~{dimension}"}
    expect(fam, fam_row, "survives_holm_at_05", "TRUE")
    what = f"Study 1 {dimension} gap on originals (H1)"
    est = num(fid, what, fam, fam_row, "estimate")
    # Study 1/tables/study1_robustness_h1_contrast.csv, row check=primary model
    # (reference); dimension=<dimension>, columns ci_lo and ci_hi: the same cells as
    # \SOneHOneCreatLo and \SOneHOneCreatHi, or \SOneHOneEffLo and \SOneHOneEffHi.
    # This row's estimate must equal the one above.
    rob = "Study 1/tables/study1_robustness_h1_contrast.csv"
    rob_row = {"check": "primary model (reference)", "dimension": dimension}
    expect(rob, rob_row, "interval", "^95% confidence interval")
    if abs(check_num(rob, rob_row, "estimate") - est) > 1e-9:
        raise SourceError(f"{rob}: the reference estimate for {dimension} differs from {fam}")
    lo = num(fid, f"{what}, 95% low", rob, rob_row, "ci_lo")
    hi = num(fid, f"{what}, 95% high", rob, rob_row, "ci_hi")
    check_interval(rob, est, check_num(rob, rob_row, "se"), check_num(rob, rob_row, "df"),
                   lo, hi, 0.95)
    return est, lo, hi


def study1_h2(fid: str, gap_creativity: float, gap_effort: float) -> tuple[float, float, float]:
    """Study 1's registered confirmatory H2: the effort gap minus the creativity gap."""
    # Study 1/tables/study1_joint_model_contrast_of_contrasts.csv, row
    # Type_pairwise=Human - AI, columns estimate, lower.CL and upper.CL: the cells of
    # \SOneHTwoDiff, \SOneHTwoLo and \SOneHTwoHi.
    rel = "Study 1/tables/study1_joint_model_contrast_of_contrasts.csv"
    row = {"Type_pairwise": "Human - AI"}
    expect(rel, row, "dimension_revpairwise", "effort - creativity")
    expect(rel, row, "converged", "TRUE")
    what = "Study 1 effort gap minus creativity gap (H2)"
    est = num(fid, what, rel, row, "estimate")
    lo = num(fid, f"{what}, 95% low", rel, row, "lower.CL")
    hi = num(fid, f"{what}, 95% high", rel, row, "upper.CL")
    se = check_num(rel, row, "SE")
    check_interval(rel, est, se, check_num(rel, row, "df"), lo, hi, 0.95)
    same(f"{rel}: H2 against the effort gap minus the creativity gap", est,
         gap_effort - gap_creativity, 1e-6)
    # Its status: the H2 row of the confirmatory family has the same estimate and
    # standard error and survives Holm's correction.
    fam = "Study 1/tables/study1_confirmatory_family.csv"
    frow = {"hypothesis": "H2"}
    same(f"{fam} H2 estimate", check_num(fam, frow, "estimate"), est)
    same(f"{fam} H2 standard error", check_num(fam, frow, "se"), se)
    expect(fam, frow, "survives_holm_at_05", "TRUE")
    return est, lo, hi


def study3_gap(fid: str, dimension: str, time: str) -> tuple[float, float, float]:
    """Study 3's registered gap (Human minus AI) at one stated time, with its 95% interval."""
    # Study 3/tables/study3_gap_by_time.csv, row dimension=<dimension>; time=<time>,
    # columns estimate, lower.CL and upper.CL: the cells of \SThree<...>Gap<time>Est,
    # Lo and Hi.
    rel = "Study 3/tables/study3_gap_by_time.csv"
    row = {"dimension": dimension, "time": time}
    expect(rel, row, "contrast", "Human minus AI")
    est = num(fid, f"Study 3 {dimension} gap, {time}", rel, row, "estimate")
    lo = num(fid, f"Study 3 {dimension} gap, {time}, 95% low", rel, row, "lower.CL")
    hi = num(fid, f"Study 3 {dimension} gap, {time}, 95% high", rel, row, "upper.CL")
    check_interval(rel, est, check_num(rel, row, "SE"), check_num(rel, row, "df"), lo, hi, 0.95)
    return est, lo, hi


def study3_decision(dimension: str, gap_100: float) -> None:
    """Stop unless Study 3's registered decision says the gap persists, on the
    100-hour gap the figure marks with a dagger."""
    # Study 3/tables/study3_decision.csv, row dimension=<dimension>, columns verdict
    # and gap_100_hours.
    rel = "Study 3/tables/study3_decision.csv"
    row = {"dimension": dimension}
    expect(rel, row, "verdict", "the gap persists")
    same(f"{rel} [{dimension}] gap_100_hours against the 100-hour gap drawn",
         check_num(rel, row, "gap_100_hours"), gap_100)


def study2_level(fid: str, measure: str, level: str) -> tuple[float, float, float]:
    """Study 2's label effect at one level: exploratory, uncorrected (its registration
    tested only the effect averaged over levels)."""
    # Study 2/tables/study2_source_by_modification.csv, row measure=<measure>;
    # modification=<level>, columns estimate, ci95_lo and ci95_hi.
    rel = "Study 2/tables/study2_source_by_modification.csv"
    row = {"measure": measure, "modification": level}
    expect(rel, row, "contrast", "Human minus AI")
    expect(rel, row, "role", "^exploratory")
    expect(rel, row, "converged", "TRUE")
    est = num(fid, f"Study 2 {measure} gap, {level}", rel, row, "estimate")
    lo = num(fid, f"Study 2 {measure} gap, {level}, 95% low", rel, row, "ci95_lo")
    hi = num(fid, f"Study 2 {measure} gap, {level}, 95% high", rel, row, "ci95_hi")
    check_interval(rel, est, check_num(rel, row, "se"), check_num(rel, row, "df"), lo, hi, 0.95)
    return est, lo, hi


def study4_level(fid: str, measure: str, level: str, bound: float) -> tuple[float, float, float]:
    """Study 4's label effect at one level, averaged over source time: registered
    secondary, uncorrected."""
    # Study 4/tables/study4_secondary_label_by_modification.csv, row measure=<measure>;
    # modification=<level>, columns estimate, ci95_low and ci95_high.
    rel = "Study 4/tables/study4_secondary_label_by_modification.csv"
    row = {"measure": measure, "modification": level}
    expect(rel, row, "contrast", "Human minus AI")
    expect(rel, row, "correction", "none")
    expect(rel, row, "averaged_over", "source time, equal weights")
    if check_num(rel, row, "bound") != bound:
        raise SourceError(f"{rel} [{_describe(row)}]: bound differs from {bound}")
    est = num(fid, f"Study 4 {measure} gap, {level}", rel, row, "estimate")
    lo = num(fid, f"Study 4 {measure} gap, {level}, 95% low", rel, row, "ci95_low")
    hi = num(fid, f"Study 4 {measure} gap, {level}, 95% high", rel, row, "ci95_high")
    check_interval(rel, est, check_num(rel, row, "std_error"), check_num(rel, row, "df"),
                   lo, hi, 0.95)
    return est, lo, hi


def study5_level(fid: str, measure: str, level: str, bound: float) -> tuple[float, float, float]:
    """Study 5's label effect at one level, averaged over editing time: registered
    secondary, each test at .05 without correction. The table holds a 90% interval,
    so the 95% interval is derived from its standard error and degrees of freedom."""
    # Study 5/tables/study5_equivalence_source.csv, row rating=<measure>;
    # modification=<level>, columns estimate, se, df, ci90_lo and ci90_hi.
    rel = "Study 5/tables/study5_equivalence_source.csv"
    row = {"rating": measure, "modification": level}
    expect(rel, row, "contrast", "Human minus AI")
    if check_num(rel, row, "bound") != bound:
        raise SourceError(f"{rel} [{_describe(row)}]: bound differs from {bound}")
    est = num(fid, f"Study 5 {measure} gap, {level}", rel, row, "estimate")
    se = num(fid, f"Study 5 {measure} gap, {level}, standard error", rel, row, "se")
    df = num(fid, f"Study 5 {measure} gap, {level}, degrees of freedom", rel, row, "df")
    # The 90% interval in the table must be est +/- t(0.95, df) * se; this proves
    # that se and df are the ones behind the registered interval.
    check_interval(rel, est, se, df, check_num(rel, row, "ci90_lo"),
                   check_num(rel, row, "ci90_hi"), 0.90)
    t975 = t_quantile(0.975, df)
    lo, hi = est - t975 * se, est + t975 * se
    record(fid, f"Study 5 {measure} gap, {level}, 95% interval", f"{lo:.6f} to {hi:.6f}",
           rel, _describe(row), "estimate, se, df",
           derivation=f"derived: estimate -/+ t(0.975, df) * se, t = {t975:.6f}")
    return est, lo, hi


def registered_bound() -> float:
    """The registered bound for second works. No figure draws it any more; the
    script still checks that every table states it and that it is half of Study 1's
    creativity gap, as the text says."""
    # Study 2/tables/study2_equivalence.csv, row measure=creativity, column bound:
    # the same cell as \SourceBound in generated/numbers.tex.
    return check_num("Study 2/tables/study2_equivalence.csv", {"measure": "creativity"}, "bound")


# ---------------------------------------------------------------------------
# Readers: each label's mean rating (descriptive; no test attaches to a mean)
# ---------------------------------------------------------------------------

def study1_means(fid: str, dimension: str) -> dict[str, float]:
    """Study 1's mean rating under each label: the mean of participant means, which
    equals the primary model's predicted mean (checked here)."""
    # Study 1/tables/study1_marginal_means.csv, row Type=<label>; dimension=<dimension>,
    # column mean: the cells of \SOneMean<label><Creat|Eff>.
    rel = "Study 1/tables/study1_marginal_means.csv"
    means = {lab: num(fid, f"Study 1 {dimension} mean, {lab} label", rel,
                      {"Type": lab, "dimension": dimension}, "mean") for lab in LABELS}
    # The primary model has one fixed term per cell and every participant rated every
    # image, so its predicted means equal these means: (Intercept) + 0.5 x
    # stimulus_typeFigure under the Human label, plus TypeAI + 0.5 x
    # TypeAI:stimulus_typeFigure under the AI label (Study 1/tables/
    # study1_lmm_fixed_effects.csv, column estimate).
    fx = "Study 1/tables/study1_lmm_fixed_effects.csv"
    b = {t: check_num(fx, {"dimension": dimension, "effect": "fixed", "term": t}, "estimate")
         for t in ["(Intercept)", "TypeAI", "stimulus_typeFigure", "TypeAI:stimulus_typeFigure"]}
    emm_h = b["(Intercept)"] + 0.5 * b["stimulus_typeFigure"]
    emm_a = emm_h + b["TypeAI"] + 0.5 * b["TypeAI:stimulus_typeFigure"]
    same(f"Study 1 {dimension}: Human-label mean against the model", means["Human"], emm_h)
    same(f"Study 1 {dimension}: AI-label mean against the model", means["AI"], emm_a)
    return means


def study3_means(fid: str, dimension: str, time: str) -> dict[str, float]:
    # Study 3/tables/study3_emmeans_cells.csv, row dimension=<dimension>; Type=<label>;
    # time=<time>, column emmean.
    rel = "Study 3/tables/study3_emmeans_cells.csv"
    return {lab: num(fid, f"Study 3 {dimension} mean, {time}, {lab} label", rel,
                     {"dimension": dimension, "Type": lab, "time": time}, "emmean")
            for lab in LABELS}


def study2_means(fid: str, measure: str, level: str) -> dict[str, float]:
    # Study 2/tables/study2_emmeans.csv, row measure=<measure>; means_of=source by
    # modification; source=<label>; modification=<level>, column emmean (averaged with
    # equal weight over image kind, as the table's averaged_over column says).
    rel = "Study 2/tables/study2_emmeans.csv"
    return {lab: num(fid, f"Study 2 {measure} mean, {level}, {lab} label", rel,
                     {"measure": measure, "means_of": "source by modification", "source": lab,
                      "modification": level}, "emmean")
            for lab in LABELS}


S4_TIMES = ["less than 1 hour", "10 hours", "100 hours"]


def study4_means(fid: str, measure: str, level: str) -> dict[str, float]:
    """Study 4's mean at one level, averaged with equal weight over the three hours
    stated for the original, the averaging its registered contrast uses. No table
    holds this mean, so it is derived from the three cell means; it is exact for a
    model's predicted mean, and its Human minus AI difference is checked against the
    contrast table."""
    # Study 4/tables/study4_emmeans_cells.csv, rows measure=<measure>; label=<label>;
    # source_time=<each time>; modification=<level>, column emmean.
    rel = "Study 4/tables/study4_emmeans_cells.csv"
    out = {}
    for lab in LABELS:
        rows = [{"measure": measure, "label": lab, "source_time": t, "modification": level}
                for t in S4_TIMES]
        value = sum(check_num(rel, r, "emmean") for r in rows) / 3.0
        record(fid, f"Study 4 {measure} mean, {level}, {lab} label", repr(value), rel,
               " | ".join(_describe(r) for r in rows), "emmean (three rows)",
               derivation="derived: equal-weight mean of the three stated-time cells")
        out[lab] = value
    return out


def study5_means(fid: str, measure: str, level: str) -> dict[str, float]:
    # Study 5/tables/study5_emmeans_source_by_modification.csv, row rating=<measure>;
    # source=<label>; modification=<level>, column emmean (averaged over stated
    # editing time and image kind).
    rel = "Study 5/tables/study5_emmeans_source_by_modification.csv"
    return {lab: num(fid, f"Study 5 {measure} mean, {level}, {lab} label", rel,
                     {"rating": measure, "source": lab, "modification": level}, "emmean")
            for lab in LABELS}


def dumbbell(where: str, means: dict[str, float], gap: tuple[float, float, float],
             label: str) -> dict:
    """One dumbbell row; stops unless the gap equals Human minus AI of its two means."""
    same(f"{where}: gap against Human minus AI", means["Human"] - means["AI"], gap[0])
    return dict(kind="row", label=label, human=means["Human"], ai=means["AI"], gap=gap[0],
                lo=gap[1], hi=gap[2])


# ---------------------------------------------------------------------------
# Study 1's participant means (the raincloud's dots)
# ---------------------------------------------------------------------------

STUDY1_LONG = "Study 1/study1_long_with_text.csv"


def study1_participant_means(fid: str, n_analyzed: float) -> dict[tuple[str, str], list[float]]:
    """Each Study 1 participant's mean rating in each cell (label x rating).

    Reads only the columns id, Type, dimension and rating of the analyzed long file
    (the file Study1_01_Quant.Rmd writes and its descriptive table averages), and
    averages each participant's non-missing ratings, as that notebook does. The id
    is used only to group ratings; it is never recorded or written. Stops unless the
    dots reproduce Study 1/tables/study1_marginal_means.csv (count, mean and SD in
    every cell, to 1e-9) and the analyzed N.
    """
    path = PIPELINE / STUDY1_LONG
    if not path.is_file():
        raise SourceError(f"file not found: {STUDY1_LONG} (looked in {PIPELINE})")
    raw = path.read_bytes()
    _CHECKSUMS[STUDY1_LONG] = hashlib.sha256(raw).hexdigest()
    # newline='' keeps line breaks inside quoted free-text answers inside their cell.
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    for col in ("id", "Type", "dimension", "rating"):
        if col not in (reader.fieldnames or []):
            raise SourceError(f"{STUDY1_LONG}: no column '{col}'")
    sums: dict[tuple[str, str, str], list[float]] = {}
    for r in reader:
        cell = r["rating"].strip()
        if cell in ("", "NA"):
            continue
        key = (r["id"], r["Type"], r["dimension"])
        acc = sums.setdefault(key, [0.0, 0.0])
        acc[0] += float(cell)
        acc[1] += 1.0
    people = {k[0] for k in sums}
    if len(people) != int(n_analyzed):
        raise SourceError(f"{STUDY1_LONG}: {len(people)} participants, not the analyzed "
                          f"N of {n_analyzed:.0f}")
    cells: dict[tuple[str, str], list[float]] = {}
    for (_pid, lab, dim), (total, count) in sums.items():
        cells.setdefault((lab, dim), []).append(total / count)
    del sums, people                   # nothing linked to a participant survives this point
    mm = "Study 1/tables/study1_marginal_means.csv"
    out = {}
    for lab in LABELS:
        for dim in ("creativity", "effort"):
            dots = sorted(cells.get((lab, dim), []))
            row = {"Type": lab, "dimension": dim}
            n = len(dots)
            mean = sum(dots) / n
            sd = math.sqrt(sum((x - mean) ** 2 for x in dots) / (n - 1))
            same(f"{mm} [{_describe(row)}] n", n, check_num(mm, row, "n"), 0)
            same(f"{mm} [{_describe(row)}] mean of the dots", mean, check_num(mm, row, "mean"))
            same(f"{mm} [{_describe(row)}] SD of the dots", sd, check_num(mm, row, "sd"))
            for k, x in enumerate(dots, start=1):
                record(fid, f"Study 1 {dim}, {lab} label, participant mean {k} of {n} "
                            f"(sorted by value)", repr(x), STUDY1_LONG,
                       f"Type={lab}; dimension={dim}; one participant (identifier not recorded)",
                       "rating",
                       derivation="derived: mean of the participant's non-missing ratings "
                                  "in this cell; the dots reproduce study1_marginal_means.csv")
            out[(lab, dim)] = dots
    return out


# ---------------------------------------------------------------------------
# Readers: exploratory cross-study gaps (Supplementary figures)
# ---------------------------------------------------------------------------

def editing_time_gap(fid: str, time: str, level: str) -> tuple[float, float, float, str]:
    """Study 5's creativity gap at one stated editing time and level (exploratory)."""
    # Cross-study/tables/crossstudy_time_check.csv, row study=Study 5;
    # measure=creativity; time=<time>; modification=<level>, columns estimate,
    # ci95_lo and ci95_hi: exploratory refit of Study 5's registered model.
    rel = "Cross-study/tables/crossstudy_time_check.csv"
    row = {"study": "Study 5", "measure": "creativity", "time": time, "modification": level}
    expect(rel, row, "analysis_status", "^exploratory")
    expect(rel, row, "time_factor", "editing time")
    expect(rel, row, "converged", "TRUE")
    what = f"Study 5 creativity gap, {time}, {level}"
    est = num(fid, what, rel, row, "estimate")
    lo = num(fid, f"{what}, 95% low", rel, row, "ci95_lo")
    hi = num(fid, f"{what}, 95% high", rel, row, "ci95_hi")
    check_interval(rel, est, check_num(rel, row, "se"), check_num(rel, row, "df"), lo, hi, 0.95)
    return est, lo, hi, text_cell(rel, row, "analysis_status")


def pooled(fid: str, measure: str, level: str, without_study4: bool):
    """A pooled estimate (each study weighted equally): (est, lo, hi, status)."""
    if without_study4:
        # Cross-study/tables/crossstudy_leave_one_study_out.csv, row measure=<measure>;
        # left_out=Study 4; modification=<level>, columns estimate, ci95_lo and ci95_hi.
        rel = "Cross-study/tables/crossstudy_leave_one_study_out.csv"
        row = {"measure": measure, "left_out": "Study 4", "modification": level}
        expect(rel, row, "study", "Study 2, Study 5")
        what = f"pooled without Study 4, {measure}, {level}"
    else:
        # Cross-study/tables/crossstudy_penalty_by_level.csv, row measure=<measure>;
        # scope=pooled; modification=<level>, columns estimate, ci95_lo and ci95_hi.
        rel = "Cross-study/tables/crossstudy_penalty_by_level.csv"
        row = {"measure": measure, "scope": "pooled", "modification": level}
        expect(rel, row, "study", "Study 2, Study 4, Study 5")
        what = f"pooled over Studies 2, 4 and 5, {measure}, {level}"
    expect(rel, row, "scope", "pooled")
    expect(rel, row, "contrast", "Human minus AI")
    expect(rel, row, "weighting", "each study weighted equally")
    expect(rel, row, "converged", "TRUE")
    # The caption says the fits converged but are singular.
    expect(rel, row, "singular", "TRUE")
    expect(rel, row, "analysis_status", "^exploratory")
    est = num(fid, what, rel, row, "estimate")
    lo = num(fid, f"{what}, 95% low", rel, row, "ci95_lo")
    hi = num(fid, f"{what}, 95% high", rel, row, "ci95_hi")
    check_interval(rel, est, check_num(rel, row, "se"), check_num(rel, row, "df"), lo, hi, 0.95)
    return est, lo, hi, text_cell(rel, row, "analysis_status")


def check_status(statuses: set[str], where: str) -> None:
    """The exploratory status cell must be one sentence of three parts, the first
    'exploratory', and the same on every plotted row (the caption quotes it)."""
    if len(statuses) != 1:
        raise SourceError(f"{where}: the plotted rows carry different analysis_status cells")
    parts = next(iter(statuses)).split("; ")
    if len(parts) != 3 or parts[0] != "exploratory":
        raise SourceError(f"{where}: unexpected analysis_status '{next(iter(statuses))}'")


# ---------------------------------------------------------------------------
# Laying out text in millimeters
# ---------------------------------------------------------------------------

_MEASURE = {}


def _measurer():
    if "fig" not in _MEASURE:
        fig = plt.figure(figsize=(W * MM, 50 * MM))
        _MEASURE["fig"] = fig
        _MEASURE["renderer"] = fig.canvas.get_renderer()
    return _MEASURE["fig"], _MEASURE["renderer"]


def width_mm(s: str, size: float = PT_TEXT, weight: str = "normal",
             style: str = "normal") -> float:
    fig, rend = _measurer()
    t = fig.text(0, 0, s, fontsize=size, fontweight=weight, fontstyle=style)
    w = t.get_window_extent(rend).width / fig.dpi * 25.4
    t.remove()
    return w


def wrap(s: str, max_mm: float, size: float = PT_TEXT, weight: str = "normal") -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and width_mm(trial, size, weight) > max_mm:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    return lines


class Page:
    """A figure laid out in millimeters measured from its top-left corner."""

    def __init__(self, height_mm: float):
        self.h = height_mm
        self.fig = plt.figure(figsize=(W * MM, height_mm * MM))

    def fx(self, x: float) -> float:
        return x / W

    def fy(self, y: float) -> float:
        return 1 - y / self.h

    def text(self, x: float, y: float, s: str, **kw):
        kw.setdefault("fontsize", PT_TEXT)
        kw.setdefault("color", INK)
        return self.fig.text(self.fx(x), self.fy(y), s, **kw)

    def title(self, x_center: float, y: float, s: str, size: float = PT_TITLE):
        """A bold title, centered on x_center (mm), baseline at y."""
        return self.text(x_center, y, s, fontsize=size, fontweight="bold", ha="center",
                         va="baseline", gid="title")

    def letter(self, x: float, y: float, s: str):
        """A bold panel letter at a panel's top-left, baseline at y."""
        return self.text(x, y, s, fontsize=PT_LETTER, fontweight="bold", ha="left",
                         va="baseline", gid="letter")

    def axes(self, x: float, y_top: float, w: float, h: float):
        ax = self.fig.add_axes([self.fx(x), self.fy(y_top + h), w / W, h / self.h])
        ax.set_facecolor("none")
        return ax

    def shade(self, y_top: float, y_bot: float, x0: float = 0.4, x1: float = W - 0.4):
        self.fig.add_artist(Rectangle((self.fx(x0), self.fy(y_bot)), (x1 - x0) / W,
                                      (y_bot - y_top) / self.h, transform=self.fig.transFigure,
                                      facecolor=SHADE, edgecolor="none", zorder=-5))

    def mark(self, x: float, y: float, spec: dict, zorder: float = 5):
        self.fig.add_artist(Line2D([self.fx(x)], [self.fy(y)], ls="none", zorder=zorder,
                                   transform=self.fig.transFigure, **spec))


def legend(page: Page, y: float, entries: list[tuple[dict, str]], note: str | None) -> float:
    """A centered legend row: one mark and a short name per entry; an optional gray
    line centered under it. Returns the y (mm) below the legend."""
    gap_mark, gap_entry, step = 3.0, 5.0, 1.6
    entries = [([spec] if isinstance(spec, dict) else spec, name) for spec, name in entries]
    widths = [gap_mark + step * (len(specs) - 1) + width_mm(name) for specs, name in entries]
    total = sum(widths) + gap_entry * (len(entries) - 1)
    x = (W - total) / 2.0
    for (specs, name), w in zip(entries, widths):
        for k, spec in enumerate(specs):
            page.mark(x + 1.2 + k * step, y, spec)
        page.text(x + gap_mark + step * (len(specs) - 1), y, name, va="center", ha="left")
        x += w + gap_entry
    if note:
        y += 3.6
        page.text(W / 2.0, y, note, va="center", ha="center", color=INK_SOFT)
    return y + 3.0


LABEL_ENTRIES = [(HUMAN, "Human label"), (AI, "AI label")]


# ---------------------------------------------------------------------------
# Figure 1: the design of the five studies
# ---------------------------------------------------------------------------

def stimulus(version: str) -> Image.Image:
    """Open one stimulus image after checking it against the image-check manifest."""
    manifest = "Cross-study/image_check/stimuli/stimuli_manifest.csv"
    rows = [r for r in _table(manifest)
            if r["artwork"] == ARTWORK and r["version"] == version]
    if len(rows) != 1:
        raise SourceError(f"{manifest}: artwork={ARTWORK}; version={version} matches "
                          f"{len(rows)} rows, not 1")
    path = STIMULI / rows[0]["file"]
    if not path.is_file():
        raise SourceError(f"image not found: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != rows[0]["file_sha256"]:
        raise SourceError(f"{path.name}: checksum {digest} differs from the manifest")
    record("Fig. 1a", f"image, {version}", path.name,
           f"Cross-study/image_check/stimuli/{path.name}",
           f"{manifest}: artwork={ARTWORK}; version={version}",
           f"file_sha256 {digest[:12]}... (matches)")
    img = Image.open(path).convert("RGB")
    # About 450 pixels per inch at the printed size: sharp in print, small on disk.
    longest = 600
    scale = longest / max(img.size)
    return img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)


def analyzed_n(fid: str) -> dict[str, float]:
    # Each N is column n of the last row of the study's exclusion flow, the same
    # cell as \SOneN ... \SFiveN in generated/numbers.tex.
    return {
        # Study 1/tables/study1_exclusion_flow.csv, row step starts 'After (3)', column n
        "Study 1": num(fid, "Study 1 analyzed N", "Study 1/tables/study1_exclusion_flow.csv",
                       {"step": "^After (3)"}, "n"),
        # Study 2/tables/study2_exclusion_flow.csv, row step=no recorded condition, column n
        "Study 2": num(fid, "Study 2 analyzed N", "Study 2/tables/study2_exclusion_flow.csv",
                       {"step": "no recorded condition"}, "n"),
        # Study 3/tables/study3_exclusion_flow.csv, row step starts 'wrong answer', column n
        "Study 3": num(fid, "Study 3 analyzed N", "Study 3/tables/study3_exclusion_flow.csv",
                       {"step": "^wrong answer"}, "n"),
        # Study 4/tables/study4_exclusion_flow.csv, row step starts 'records that are not', column n
        "Study 4": num(fid, "Study 4 analyzed N", "Study 4/tables/study4_exclusion_flow.csv",
                       {"step": "^records that are not"}, "n"),
        # Study 5/tables/study5_exclusion_flow_registered.csv, row step starts '5.', column n
        "Study 5": num(fid, "Study 5 analyzed N",
                       "Study 5/tables/study5_exclusion_flow_registered.csv", {"step": "^5."}, "n"),
    }


# What each study varied and what participants rated: design facts from the five
# registrations and the ledger's design sections, not results. Short on purpose:
# each cell is a list of items, one item per line, with no lists inside a line.
# The caption says the rest (what the labels said, the stated times and what
# they meant under each label, that Study 5 stated but did not record a time for
# the original, run order, registrations).
FIG1_GROUPS = [
    ("Rating originals", "Creativity and effort of the original", ["Study 1", "Study 3"]),
    ("Rating second works", "Transformativeness, essence change and creativity of the "
                            "second work", ["Study 2", "Study 4", "Study 5"]),
]
FIG1_CELLS = {
    "Study 1": (["Label"], ["10 originals"]),
    "Study 3": (["Label"], ["Stated hours", "9 originals"]),
    "Study 2": (["Label of the original"], ["Edit level", "10 originals"]),
    "Study 4": (["Label of the original"],
                ["Edit level", "Stated hours for the original", "6 originals"]),
    "Study 5": (["Label of the original", "Stated editing hours"], ["Edit level", "6 originals"]),
}
FIG1_ROWS = ["Between people", "Within people"]
ITEM_GAP = 0.9                                   # extra space between items in a cell, mm
NONE_NOTE = "None: this image shown again unchanged"


def figure1():
    fid = "Fig. 1b"
    n = analyzed_n(fid)
    images = [stimulus("original"), stimulus("Slight"), stimulus("Dramatic")]
    line = PT_TEXT * 1.25 * 25.4 / 72.0          # line pitch of 7-pt text, mm

    # ---- geometry of b, measured before the figure exists ----------------------
    row_col = 22.0                               # row labels
    gap_in, gap_between = 2.0, 4.0               # between cards in a group; between groups
    x0 = LABEL_X + row_col
    card_w = (W - 1.0 - x0 - gap_in * 3 - gap_between) / 5.0
    xs, x = {}, x0
    for _title, _rated, studies in FIG1_GROUPS:
        for s in studies:
            xs[s] = x
            x += card_w + gap_in
        x += gap_between - gap_in
    pad = 1.6
    # wrapped[study][row] is a list of items, each a list of wrapped lines.
    wrapped = {s: [[wrap(item, card_w - 2 * pad) for item in cell] for cell in FIG1_CELLS[s]]
               for s in FIG1_CELLS}

    def cell_h(items) -> float:
        return sum(len(lines) for lines in items) * line + ITEM_GAP * (len(items) - 1)

    row_h = [max(cell_h(wrapped[s][k]) for s in FIG1_CELLS) + 1.6 for k in range(2)]

    # ---- heights ---------------------------------------------------------------
    side = 33.5                                  # image side, mm
    top_a = 3.0
    img_top = top_a + 6.5
    note_y = img_top + side + 3.4
    top_b = note_y + 6.0
    group_y = top_b + 3.0                        # group title baseline
    rated_y = group_y + 3.4                      # what the group rated
    card_top = rated_y + 2.4
    head_h = 7.4                                 # card header: study name and N
    card_h = head_h + sum(row_h) + 0.8
    key_y = card_top + card_h + 4.0
    height = key_y + 2.6

    page = Page(height)
    fig = page.fig

    # ---- a: one original and its Slight and Dramatic versions -------------------
    page.letter(LABEL_X, top_a, "a")
    img_gap = 15.0
    ix0 = (W - 3 * side - 2 * img_gap) / 2.0
    for i, (img, name) in enumerate(zip(images, ["Original", "Slight", "Dramatic"])):
        xi = ix0 + i * (side + img_gap)
        page.title(xi + side / 2.0, img_top - 1.6, name)
        ax = page.axes(xi, img_top, side, side)
        ax.imshow(img, interpolation="lanczos")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)
        if i == 0:
            # The one guard line: the None second work is this image again.
            page.text(xi + side / 2.0, note_y, NONE_NOTE, ha="center", va="center",
                      color=INK_SOFT)

    # ---- b: the five studies ------------------------------------------------------
    page.letter(LABEL_X, top_b, "b")
    for gtitle, rated, studies in FIG1_GROUPS:
        left, right = xs[studies[0]], xs[studies[-1]] + card_w
        page.title((left + right) / 2.0, group_y, gtitle)
        page.text((left + right) / 2.0, rated_y, rated, ha="center", va="baseline")
    for k, label in enumerate(FIG1_ROWS):
        y = card_top + head_h + sum(row_h[:k]) + 0.4
        page.text(LABEL_X, y, label, va="top", ha="left", fontweight="bold", color=INK_SOFT,
                  gid="heading")
    for s in FIG1_CELLS:
        x = xs[s]
        fig.add_artist(FancyBboxPatch(
            (page.fx(x), page.fy(card_top + card_h)), card_w / W, card_h / height,
            transform=fig.transFigure, boxstyle="round,pad=0,rounding_size=0.004",
            facecolor=CARD_FILL, edgecolor=RULE, linewidth=0.5, zorder=0))
        page.title(x + card_w / 2.0, card_top + 3.2, s)
        page.text(x + card_w / 2.0, card_top + 6.2, f"N = {n[s]:.0f}", ha="center",
                  va="baseline", color=INK_SOFT)
        for k in range(2):
            y = card_top + head_h + sum(row_h[:k]) + 0.4
            for lines in wrapped[s][k]:
                page.text(x + pad, y, "\n".join(lines), va="top", ha="left", linespacing=1.25)
                y += len(lines) * line + ITEM_GAP
    # The one line every figure carries: what the label manipulation was.
    page.text(W / 2.0, key_y, AI_MADE, ha="center", va="baseline", color=INK_SOFT)
    return page, {}


# ---------------------------------------------------------------------------
# The dumbbell figures: Figure 2 and the Supplementary figure of other ratings
# ---------------------------------------------------------------------------

ROW = 3.9               # row pitch, mm
HEAD = 4.4              # row-group heading
SUB = 3.6               # Study 3's rating sub-headings
BLOCK_PAD = 0.8         # below a group's last row, inside its shading
BLOCK_GAP = 0.9         # white space between groups
AXIS_H = 9.5            # ticks, tick labels and axis title under a panel
PANEL_GAP = 4.0         # white space between panels
TITLE_H = 5.0           # panel letter and title row
GUARD_H = 3.6           # one guard line under a title

H2_LABEL = f"Effort gap {MINUS} creativity gap"
RATE_AXIS = "Mean rating"
GAP_AXIS = f"Gap, Human {MINUS} AI (95% CI)"


class Columns:
    """The horizontal layout shared by every dumbbell and raincloud panel: a rating
    column and a gap column at the same millimeters per point, the gap column ending
    RIGHT_PAD from the right edge."""

    def __init__(self, gap_lim=GAP_LIM):
        self.gap_lim = gap_lim
        self.rate_w = (RATE_LIM[1] - RATE_LIM[0]) * SCALE
        self.gap_w = (gap_lim[1] - gap_lim[0]) * SCALE
        self.gap_l = W - RIGHT_PAD - self.gap_w
        self.plot_l = self.gap_l - GUTTER - self.rate_w


def block_height(items) -> float:
    h = HEAD
    for it in items:
        h += SUB if it["kind"] == "sub" else ROW
    return h + BLOCK_PAD


def body_height(blocks) -> float:
    return sum(block_height(items) for _name, items in blocks) + BLOCK_GAP * (len(blocks) - 1)


def panel_height(blocks, guard: str | None) -> float:
    return TITLE_H + (GUARD_H if guard else 0.0) + 2.0 + body_height(blocks) + AXIS_H


def style_axes(ax, xlim, ticks, labels, body_h, xlabel):
    ax.set_ylim(body_h, 0)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(*xlim)
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.spines["bottom"].set_bounds(ticks[0], ticks[-1])
    ax.set_xlabel(xlabel, labelpad=2.0, fontsize=PT_TEXT)


def signed(v: float) -> str:
    return "0" if abs(v) < 1e-9 else f"{v:g}".replace("-", MINUS)


def draw_link(ax, human: float, ai: float, y: float) -> None:
    """The gray line joining the two means, stopped short of the open diamond so it
    does not run into its center."""
    trim = (AI["ms"] / 2.0) / 72.0 * 25.4 / SCALE         # half the diamond, in points
    if abs(human - ai) <= trim:
        return
    end = ai + trim if human > ai else ai - trim
    ax.plot([human, end], [y, y], color=LINK, lw=1.2, zorder=1, solid_capstyle="butt")


def draw_gap(gx, y: float, est: float, lo: float, hi: float, ink: str = INK,
             face: str | None = None) -> None:
    gx.plot([lo, hi], [y, y], color=ink, lw=0.9, zorder=2, solid_capstyle="butt")
    gx.plot([est], [y], ls="none", marker="s", ms=3.2, mfc=face or ink, mec=ink if face else "white",
            mew=0.6 if face else 0.4, zorder=3)


def dumbbell_panel(page: Page, cols: Columns, top: float, letter: str, title: str,
                   guard: str | None, blocks) -> float:
    """Draw one panel from `top` (mm); return its bottom. blocks: [(heading, items)]."""
    page.letter(LABEL_X, top + 3.4, letter)
    page.title(W / 2.0, top + 3.4, title)
    y = top + TITLE_H
    if guard:
        page.text(W / 2.0, y + 1.6, guard, ha="center", va="center", color=INK)
        y += GUARD_H
    y0 = y + 2.0
    body_h = body_height(blocks)
    ax = page.axes(cols.plot_l, y0, cols.rate_w, body_h)
    gx = page.axes(cols.gap_l, y0, cols.gap_w, body_h)
    style_axes(ax, RATE_LIM, RATE_TICKS, [str(t) for t in RATE_TICKS], body_h, RATE_AXIS)
    gticks = [t for t in GAP_TICKS if cols.gap_lim[0] - 1e-9 <= t <= cols.gap_lim[1] + 1e-9]
    style_axes(gx, cols.gap_lim, gticks, [signed(t) for t in gticks], body_h, GAP_AXIS)
    gx.spines["bottom"].set_bounds(*cols.gap_lim)
    fig_y = blended_transform_factory(page.fig.transFigure, ax.transData)
    yy = 0.0
    for k, (heading, items) in enumerate(blocks):
        bh = block_height(items)
        if k % 2 == 0:
            page.shade(y0 + yy, y0 + yy + bh)
        # A heading is a study name, optionally with a short gray note after it.
        name, note = heading if isinstance(heading, tuple) else (heading, "")
        ax.text(page.fx(LABEL_X), yy + HEAD * 0.56, name, transform=fig_y, fontweight="bold",
                va="center", ha="left", fontsize=PT_TEXT, color=INK, gid="heading")
        if note:
            ax.text(page.fx(LABEL_X + width_mm(name, weight="bold") + 1.6), yy + HEAD * 0.56,
                    note, transform=fig_y, va="center", ha="left", fontsize=PT_TEXT,
                    color=INK_SOFT, gid="rowlabel")
        yy += HEAD
        rows_top = yy
        for it in items:
            if it["kind"] == "sub":
                ax.text(page.fx(LABEL_X + ROW_INDENT), yy + SUB * 0.55, it["label"],
                        transform=fig_y, va="center", ha="left", fontsize=PT_TEXT, color=INK,
                        fontstyle="italic", gid="rowlabel")
                yy += SUB
                continue
            yc = yy + ROW / 2.0
            ink = H2_INK if it["kind"] == "h2" else INK
            ax.text(page.fx(LABEL_X + it.get("indent", ROW_INDENT)), yc, it["label"],
                    transform=fig_y, va="center", ha="left", fontsize=PT_TEXT, color=ink,
                    gid="rowlabel")
            gx.plot(cols.gap_lim, [yc, yc], color=ROWLINE, lw=0.5, zorder=0,
                    solid_capstyle="butt")
            if it["kind"] == "row":
                ax.plot([1, 5], [yc, yc], color=ROWLINE, lw=0.5, zorder=0, solid_capstyle="butt")
                draw_link(ax, it["human"], it["ai"], yc)
                ax.plot([it["human"]], [yc], ls="none", zorder=Z_HUMAN, **HUMAN)
                ax.plot([it["ai"]], [yc], ls="none", zorder=Z_AI, **AI)
            draw_gap(gx, yc, it["gap"], it["lo"], it["hi"], ink=ink)
            yy += ROW
        for v in RATE_TICKS:
            ax.plot([v, v], [rows_top, yy], color=GRID, lw=0.5, zorder=0)
        gx.plot([0, 0], [rows_top, yy], color=ZERO, lw=0.7, zorder=0)
        yy += BLOCK_PAD + BLOCK_GAP
    page.fig._dumbbell_axes = getattr(page.fig, "_dumbbell_axes", []) + [(ax, gx, cols)]
    return y0 + body_h + AXIS_H


def second_work_blocks(fid: str, measure: str, bound: float):
    blocks = []
    for study, gap_fn, mean_fn in (("Study 2", study2_level, study2_means),
                                   ("Study 4", study4_level, study4_means),
                                   ("Study 5", study5_level, study5_means)):
        items = []
        for level, label in LEVEL_ROWS:
            gap = gap_fn(fid, measure, level) if study == "Study 2" else \
                gap_fn(fid, measure, level, bound)
            items.append(dumbbell(f"{study} {measure} {level}", mean_fn(fid, measure, level),
                                  gap, label))
        blocks.append((study, items))
    return blocks


STUDY3_TIMES = [("under 1 hour", "under 1 h"), ("10 hours", "10 h"), ("100 hours", "100 h")]


def originals_blocks(fid: str):
    gaps = {d: study1_h1(fid, d) for d in ("creativity", "effort")}
    s1 = [dumbbell(f"Study 1 {d}", study1_means(fid, d), gaps[d], d.capitalize())
          for d in ("creativity", "effort")]
    h2 = study1_h2(fid, gaps["creativity"][0], gaps["effort"][0])
    s1.append(dict(kind="h2", label=H2_LABEL, gap=h2[0], lo=h2[1], hi=h2[2]))
    s3 = []
    for d in ("creativity", "effort"):
        s3.append(dict(kind="sub", label=d.capitalize()))
        for time, short in STUDY3_TIMES:
            gap = study3_gap(fid, d, time)
            label = f"{short} {DAGGER}" if time == "100 hours" else short
            row = dumbbell(f"Study 3 {d} {time}", study3_means(fid, d, time), gap, label)
            row["indent"] = SUB_INDENT
            s3.append(row)
            if time == "100 hours":
                study3_decision(d, gap[0])
    return [("Study 1", s1), (("Study 3", "stated hours"), s3)], gaps["creativity"][0]


def dumbbell_figure(panels, legend_note: str | None = AI_MADE):
    """panels: [(letter, title, guard, blocks)], drawn one under another."""
    cols = Columns()
    legend_h = 10.0 if legend_note else 6.4
    height = legend_h + sum(panel_height(b, g) for _l, _t, g, b in panels) \
        + PANEL_GAP * (len(panels) - 1)
    page = Page(height)
    legend(page, 2.8, LABEL_ENTRIES, legend_note)
    y = legend_h
    for letter, title, guard, blocks in panels:
        y = dumbbell_panel(page, cols, y, letter, title, guard, blocks) + PANEL_GAP
    return page


def figure2():
    bound = registered_bound()
    a_blocks, s1_creativity = originals_blocks("Fig. 2a")
    # The text calls the bound half of Study 1's creativity gap; stop if the two
    # cells disagree at the precision printed.
    if f"{s1_creativity / 2.0:.3f}" != f"{bound:.3f}":
        raise SourceError(f"the registered bound {bound} is not half of Study 1's creativity "
                          f"gap {s1_creativity}")
    b_blocks = second_work_blocks("Fig. 2b", "creativity", bound)
    page = dumbbell_figure([
        ("a", "Originals", None, a_blocks),
        ("b", "Creativity of the second work", NOT_COMPARABLE, b_blocks),
    ])
    return page, {"rowlabels": True}


def figure_s_other_ratings():
    """One guard line only, the direction of essence change, which no other figure
    states; the caption carries Fig. 2b's warning on comparing sizes."""
    bound = registered_bound()
    page = dumbbell_figure([
        ("a", "Transformativeness of the second work", None,
         second_work_blocks("Fig. S other ratings a", "transformativeness", bound)),
        ("b", "Essence change of the second work",
         "Right of zero: the AI-label group judged the edit to change the original less.",
         second_work_blocks("Fig. S other ratings b", "essence_change", bound)),
    ])
    return page, {"rowlabels": True}


# ---------------------------------------------------------------------------
# Supplementary figure: Study 1 raincloud
# ---------------------------------------------------------------------------

BANDWIDTH = 0.15        # points; the smoothing width of the half-violins
CLOUD_H = 5.0           # height of the tallest half-violin, mm
CLOUD_MIN = 0.15        # the outline is not drawn where it is thinner than this, mm
DOT_TOP = 1.1           # first row of dots below the baseline, mm
DOT_STEP = 0.62         # vertical step between stacked dots, mm
RC_ROW = 12.4           # one label's row, mm
SMALL_HUMAN = dict(marker="o", ms=1.9, mfc=HUMAN_COLOR, mec="none", mew=0.0)
SMALL_AI = dict(marker="o", ms=1.9, mfc="none", mec=AI_COLOR, mew=0.5)


def density(dots: list[float], xs: list[float]) -> list[float]:
    """Gaussian kernel density of the dots at xs, reflected at 1 and 5 so it never
    runs past the scale."""
    n = len(dots)
    c = 1.0 / (n * BANDWIDTH * math.sqrt(2.0 * math.pi))
    out = []
    for x in xs:
        s = 0.0
        for d in dots:
            for m in (d, 2.0 - d, 10.0 - d):
                z = (x - m) / BANDWIDTH
                s += math.exp(-0.5 * z * z)
        out.append(c * s)
    return out


def raincloud_spread_check() -> None:
    """The caption says the participant means spread more under the AI label on both
    ratings, more on effort than on creativity. Stop unless the standard deviations
    in Study 1/tables/study1_marginal_means.csv (column sd) say so, both as a ratio
    (AI over Human) and as a difference (AI minus Human)."""
    mm = "Study 1/tables/study1_marginal_means.csv"
    sd = {(lab, d): check_num(mm, {"Type": lab, "dimension": d}, "sd")
          for lab in LABELS for d in ("creativity", "effort")}
    for d in ("creativity", "effort"):
        if not sd[("AI", d)] > sd[("Human", d)]:
            raise SourceError(f"{mm}: the {d} SD is not larger under the AI label, as the "
                              "raincloud caption says")
    ratio = {d: sd[("AI", d)] / sd[("Human", d)] for d in ("creativity", "effort")}
    diff = {d: sd[("AI", d)] - sd[("Human", d)] for d in ("creativity", "effort")}
    if not (ratio["effort"] > ratio["creativity"] and diff["effort"] > diff["creativity"]):
        raise SourceError(f"{mm}: the extra spread under the AI label is not larger on effort "
                          "than on creativity, as the raincloud caption says")


def figure_s_raincloud():
    fid = "Fig. S Study 1 raincloud"
    # Study 1/tables/study1_exclusion_flow.csv, row step starts 'After (3)', column n:
    # the analyzed N, used only to check the count of participants (not plotted).
    n = check_num("Study 1/tables/study1_exclusion_flow.csv", {"step": "^After (3)"}, "n")
    dots = study1_participant_means(fid, n)
    raincloud_spread_check()
    gaps = {d: study1_h1(fid, d) for d in ("creativity", "effort")}
    means = {d: study1_means(fid, d) for d in ("creativity", "effort")}
    for d in gaps:
        same(f"Study 1 {d}: gap against Human minus AI", means[d]["Human"] - means[d]["AI"],
             gaps[d][0])
    cols = Columns()
    legend_h = 10.0
    group_h = HEAD + 2 * RC_ROW + BLOCK_PAD
    body_h = 2 * group_h + BLOCK_GAP
    height = legend_h + 2.0 + body_h + AXIS_H
    page = Page(height)
    legend(page, 2.8, LABEL_ENTRIES + [([SMALL_HUMAN, SMALL_AI], "participants")],
           f"Large marks: means. {AI_MADE}")
    y0 = legend_h + 2.0
    ax = page.axes(cols.plot_l, y0, cols.rate_w, body_h)
    gx = page.axes(cols.gap_l, y0, cols.gap_w, body_h)
    style_axes(ax, RATE_LIM, RATE_TICKS, [str(t) for t in RATE_TICKS], body_h, RATE_AXIS)
    style_axes(gx, GAP_LIM, GAP_TICKS, [signed(t) for t in GAP_TICKS], body_h, GAP_AXIS)
    gx.spines["bottom"].set_bounds(*GAP_LIM)
    fig_y = blended_transform_factory(page.fig.transFigure, ax.transData)
    xs = [1.0 + 4.0 * i / 400.0 for i in range(401)]
    dens = {k: density(v, xs) for k, v in dots.items()}
    peak = max(max(v) for v in dens.values())
    yy = 0.0
    for k, dim in enumerate(("creativity", "effort")):
        if k % 2 == 0:
            page.shade(y0 + yy, y0 + yy + group_h)
        ax.text(page.fx(LABEL_X), yy + HEAD * 0.56, dim.capitalize(), transform=fig_y,
                fontweight="bold", va="center", ha="left", fontsize=PT_TEXT, color=INK,
                gid="heading")
        yy += HEAD
        rows_top = yy
        bases = []
        for lab in LABELS:
            base = yy + 0.6 + CLOUD_H
            bases.append(base)
            # "Human label", not "Human": the dots are ratings under a label, not of
            # human-made art.
            ax.text(page.fx(LABEL_X + ROW_INDENT), base, f"{lab} label", transform=fig_y,
                    va="center", ha="left", fontsize=PT_TEXT, color=INK, gid="rowlabel")
            v = dots[(lab, dim)]
            # The outline is drawn where it is at least CLOUD_MIN mm tall, so no thin
            # stalk runs along the baseline into the tails.
            tall = [i for i, dv in enumerate(dens[(lab, dim)]) if CLOUD_H * dv / peak >= CLOUD_MIN]
            pts = [(xs[i], base - CLOUD_H * dens[(lab, dim)][i] / peak)
                   for i in range(tall[0], tall[-1] + 1)]
            poly = [(pts[0][0], base)] + pts + [(pts[-1][0], base)]
            if lab == "Human":
                ax.add_patch(Polygon(poly, closed=True, facecolor=HUMAN_CLOUD,
                                     edgecolor=HUMAN_COLOR, lw=0.6, zorder=1))
            else:
                ax.add_patch(Polygon(poly, closed=True, facecolor="none", edgecolor=AI_COLOR,
                                     lw=0.8, zorder=1))
            # Dots at their exact values, stacked downward where values repeat.
            stack: dict[float, int] = {}
            spec = SMALL_HUMAN if lab == "Human" else SMALL_AI
            for x in v:
                key = round(x, 9)
                i = stack.get(key, 0)
                stack[key] = i + 1
                ax.plot([x], [base + DOT_TOP + i * DOT_STEP], ls="none", zorder=2, **spec)
            big = HUMAN if lab == "Human" else AI
            ax.plot([means[dim][lab]], [base], ls="none",
                    zorder=Z_HUMAN + 2 if lab == "Human" else Z_AI + 2, **big)
            yy += RC_ROW
        for v in RATE_TICKS:
            ax.plot([v, v], [rows_top, yy], color=GRID, lw=0.5, zorder=0)
        gy = sum(bases) / 2.0
        gx.plot(GAP_LIM, [gy, gy], color=ROWLINE, lw=0.5, zorder=0, solid_capstyle="butt")
        draw_gap(gx, gy, *gaps[dim])
        gx.plot([0, 0], [rows_top, yy], color=ZERO, lw=0.7, zorder=0)
        yy += BLOCK_PAD + BLOCK_GAP
    page.fig._dumbbell_axes = [(ax, gx, cols)]
    for d in ("creativity", "effort"):
        record(fid, f"Study 1 {d} half-violins (both labels)", "drawn from the dots above",
               STUDY1_LONG, f"dimension={d}", "rating",
               derivation=f"derived: Gaussian kernel density of the participant means, "
                          f"bandwidth {BANDWIDTH} points, reflected at 1 and 5, drawn where at "
                          f"least {CLOUD_MIN} mm tall; heights share one scale across the "
                          f"four outlines")
    return page, {"rowlabels": True}


# ---------------------------------------------------------------------------
# Supplementary Figure 5: Study 1's posterior predictive check
# ---------------------------------------------------------------------------

PPC_CURVES = "figures/figS_study1_ppc_curves.csv"    # written by tools/study1_ppc_data.R
PPC_SOURCES = "figures/figS_study1_ppc_sources.csv"
PPC_DRAW = "#b3b3b3"                    # the simulated data sets: gray, since color means a label
PPC_OBS = INK


def _paper_csv(rel: str) -> list[dict[str, str]]:
    """Read a table that a paper tool wrote under the Final Paper folder; record its checksum."""
    path = PAPER / rel
    if not path.is_file():
        raise SourceError(f"{rel} not found; run tools/study1_ppc_data.R first")
    data = path.read_bytes()
    _CHECKSUMS[rel] = hashlib.sha256(data).hexdigest()
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def figure_s_ppc():
    fid = "Fig. S Study 1 posterior predictive check"
    # The curves must come from the fits now in the pipeline: stop if a fit changed since
    # tools/study1_ppc_data.R read it.
    # The fits are not in the public repository (they hold participant numbers); there the
    # committed curves, with the checksums of the fits they came from, are the record.
    for src in _paper_csv(PPC_SOURCES):
        fit = PIPELINE / src["file"]
        if not fit.is_file():
            continue
        if hashlib.sha256(fit.read_bytes()).hexdigest() != src["sha256"]:
            raise SourceError(f"{src['file']} changed since {PPC_CURVES} was written; rerun "
                              "tools/study1_ppc_data.R")
        if src["family"] != "gaussian" or src["ndraws"] != "100":
            raise SourceError(f"{PPC_SOURCES}: expected a Gaussian fit and 100 draws")
    rows = _paper_csv(PPC_CURVES)
    curves: dict[tuple[str, str], tuple[list[float], list[float]]] = {}
    for r in rows:
        xs, ys = curves.setdefault((r["rating"], r["curve"]), ([], []))
        xs.append(float(r["x"]))
        ys.append(float(r["density"]))
    dims = ("creativity", "effort")
    for d in dims:
        n_draws = sum(1 for (dd, c) in curves if dd == d and c.startswith("draw_"))
        if (d, "observed") not in curves or n_draws != 100:
            raise SourceError(f"{PPC_CURVES}: {d} needs one observed curve and 100 draws")
    legend_h = 8.0
    panel_h = 46.0
    height = legend_h + 6.0 + panel_h + 11.0
    page = Page(height)
    obs_spec = dict(marker="_", ms=6, mec=PPC_OBS, mew=1.4)
    draw_spec = dict(marker="_", ms=6, mec=PPC_DRAW, mew=1.0)
    legend(page, 3.0, [(obs_spec, "Observed ratings"),
                       (draw_spec, "100 data sets simulated from the model")], None)
    left, gap, right = 14.0, 14.0, RIGHT_PAD + 2.0
    pw = (W - left - gap - right) / 2.0
    top = legend_h + 6.0
    ymax = max(max(ys) for (_d, _c), (_xs, ys) in curves.items()) * 1.05
    for k, d in enumerate(dims):
        x0 = left + k * (pw + gap)
        page.letter(LABEL_X if k == 0 else x0 - 8.0, top - 2.0, "ab"[k])
        page.title(x0 + pw / 2.0, top - 2.0, d.capitalize())
        ax = page.axes(x0, top, pw, panel_h)
        for (dd, c), (xs, ys) in sorted(curves.items()):
            if dd == d and c.startswith("draw_"):
                ax.plot(xs, ys, color=PPC_DRAW, lw=0.35, alpha=0.6, zorder=1)
        xs, ys = curves[(d, "observed")]
        ax.plot(xs, ys, color=PPC_OBS, lw=1.2, zorder=3)
        lo = min(xs)
        hi = max(xs)
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, ymax)
        ax.set_xticks([t for t in range(int(math.ceil(lo)), int(math.floor(hi)) + 1)])
        ax.set_xlabel("Rating", fontsize=PT_TEXT, color=INK, labelpad=2)
        ax.set_ylabel("Density" if k == 0 else "", fontsize=PT_TEXT, color=INK, labelpad=2)
        ax.tick_params(axis="both", labelsize=PT_TEXT, colors=INK, length=2.5, width=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        record(fid, f"Study 1 {d}: observed rating density", "drawn as one curve", PPC_CURVES,
               f"rating={d}, curve=observed", "density",
               derivation="Gaussian kernel density (bandwidth rule nrd0) of the observed ratings, "
                          "by tools/study1_ppc_data.R")
        record(fid, f"Study 1 {d}: 100 simulated rating densities", "drawn as 100 curves",
               PPC_CURVES, f"rating={d}, curve=draw_001 to draw_100", "density",
               derivation="posterior_predict on the saved Gaussian brms fit, 100 draws, seed "
                          "20260421, each draw's density as for the observed ratings")
    return page, {}


# ---------------------------------------------------------------------------
# The exploratory gap-only Supplementary figures
# ---------------------------------------------------------------------------

POOLED_ROW = 5.2        # row pitch of the pooled figure, which draws two marks per row, mm
POOLED_ALL = dict(marker="s", ms=3.4, mfc=INK, mec="white", mew=0.4)
POOLED_NO4 = dict(marker="s", ms=3.4, mfc="white", mec=INK, mew=0.7)


def gap_panels(page: Page, top: float, panels, series, row_labels: list[str],
               axis_label: str, group_title: str | None, row: float = ROW):
    """Side-by-side gap panels sharing the rows None, Slight and Dramatic.

    panels: [(letter, title, {series key: [(est, lo, hi) per level]})]; series:
    [(key, spec, offset_mm)]. Returns the bottom (mm)."""
    gap_w = (GAP_LIM_SUPP[1] - GAP_LIM_SUPP[0]) * SCALE
    label_w = max(width_mm(s) for s in row_labels) + 4.0
    spacing = 18.0
    block_w = label_w + len(panels) * gap_w + (len(panels) - 1) * spacing
    x0 = (W - block_w) / 2.0
    y = top
    if group_title:
        page.title(x0 + label_w + (len(panels) * gap_w + (len(panels) - 1) * spacing) / 2.0,
                   y + 3.4, group_title)
        y += TITLE_H
    title_y = y + 3.4
    y0 = y + TITLE_H + 1.0
    body_h = row * len(row_labels) + 2.0
    axes = []
    for j, (letter, title, values) in enumerate(panels):
        xl = x0 + label_w + j * (gap_w + spacing)
        page.letter(x0 if j == 0 else xl - 4.0, title_y, letter)
        page.title(xl + gap_w / 2.0, title_y, title)
        gx = page.axes(xl, y0, gap_w, body_h)
        gticks = [t for t in GAP_TICKS if GAP_LIM_SUPP[0] - 1e-9 <= t <= GAP_LIM_SUPP[1] + 1e-9]
        style_axes(gx, GAP_LIM_SUPP, gticks, [signed(t) for t in gticks], body_h,
                   axis_label if j == len(panels) // 2 else "")
        gx.spines["bottom"].set_bounds(*GAP_LIM_SUPP)
        fig_y = blended_transform_factory(page.fig.transFigure, gx.transData)
        gx.plot([0, 0], [0, body_h], color=ZERO, lw=0.7, zorder=0)
        for i, lab in enumerate(row_labels):
            yc = 1.0 + row * i + row / 2.0
            gx.plot(GAP_LIM_SUPP, [yc, yc], color=ROWLINE, lw=0.5, zorder=0,
                    solid_capstyle="butt")
            if j == 0:
                gx.text(page.fx(x0), yc, lab, transform=fig_y, va="center", ha="left",
                        fontsize=PT_TEXT, color=INK, gid="rowlabel")
            for key, spec, off in series:
                est, lo, hi = values[key][i]
                gx.plot([lo, hi], [yc + off, yc + off], color=INK, lw=0.9, zorder=2,
                        solid_capstyle="butt")
                gx.plot([est], [yc + off], ls="none", zorder=3, **spec)
        axes.append(gx)
    page.fig._gap_axes = axes
    return y0 + body_h + AXIS_H, x0


S5_TIMES = [("less than 1 hour", "under 1 h"), ("10 hours", "10 h"), ("100 hours", "100 h")]


def figure_s_editing_time():
    statuses: set[str] = set()
    panels = []
    for j, (time, title) in enumerate(S5_TIMES):
        fid = f"Fig. S editing time {'abc'[j]}"
        vals = []
        for level in LEVELS:
            *g, status = editing_time_gap(fid, time, level)
            statuses.add(status)
            vals.append(tuple(g))
        panels.append(("abc"[j], title, {"gap": vals}))
    check_status(statuses, "Cross-study/tables/crossstudy_time_check.csv")
    top = 1.0
    height = top + TITLE_H + TITLE_H + 1.0 + ROW * 3 + 2.0 + AXIS_H + 4.4
    page = Page(height)
    bottom, _x0 = gap_panels(page, top, panels,
                             [("gap", dict(marker="s", ms=3.2, mfc=INK, mec="white",
                                           mew=0.4), 0.0)],
                             [lab for _l, lab in LEVEL_ROWS],
                             f"Creativity gap, Human {MINUS} AI (95% CI)", "Stated editing time")
    # The line on the label manipulation goes under the axis title, so the figure
    # reads title first.
    page.text(W / 2.0, bottom + 1.6, AI_MADE, ha="center", va="center", color=INK_SOFT)
    return page, {"rowlabels": False}


POOLED_MEASURES = [("transformativeness", "Transformativeness"),
                   ("essence_change", "Essence change"), ("creativity", "Creativity")]


def study4_creativity_check() -> None:
    """The pooled caption says Study 4's creativity estimates lay below zero at every
    level, none significantly. Stop unless its registered secondary contrasts say so."""
    # Study 4/tables/study4_secondary_label_by_modification.csv, rows
    # measure=creativity; modification=<level>, columns estimate and p_two_sided.
    rel = "Study 4/tables/study4_secondary_label_by_modification.csv"
    for level in LEVELS:
        row = {"measure": "creativity", "modification": level}
        expect(rel, row, "contrast", "Human minus AI")
        if not check_num(rel, row, "estimate") < 0:
            raise SourceError(f"{rel} [{_describe(row)}]: the estimate is not below zero, as "
                              "the pooled caption says")
        if not check_num(rel, row, "p_two_sided") >= 0.05:
            raise SourceError(f"{rel} [{_describe(row)}]: p is below .05, but the pooled "
                              "caption says none is significant")


def figure_s_pooled():
    study4_creativity_check()
    statuses: set[str] = set()
    panels = []
    for j, (measure, title) in enumerate(POOLED_MEASURES):
        fid = f"Fig. S pooled {'abc'[j]}"
        all3, no4 = [], []
        for level in LEVELS:
            *a, sa = pooled(fid, measure, level, False)
            *b, sb = pooled(fid, measure, level, True)
            statuses.update({sa, sb})
            all3.append(tuple(a))
            no4.append(tuple(b))
        panels.append(("abc"[j], title, {"all": all3, "no4": no4}))
    check_status(statuses, "Cross-study/tables/crossstudy_penalty_by_level.csv and "
                           "crossstudy_leave_one_study_out.csv")
    height = 10.0 + TITLE_H + 1.0 + POOLED_ROW * 3 + 2.0 + AXIS_H
    page = Page(height)
    legend(page, 2.8, [(POOLED_ALL, "Studies 2, 4 and 5"), (POOLED_NO4, "Studies 2 and 5")],
           AI_MADE)
    gap_panels(page, 10.0, panels, [("all", POOLED_ALL, -1.0), ("no4", POOLED_NO4, 1.0)],
               [lab for _l, lab in LEVEL_ROWS], GAP_AXIS, None, row=POOLED_ROW)
    return page, {"rowlabels": False}


# ---------------------------------------------------------------------------
# Checks on the drawn figure, and writing
# ---------------------------------------------------------------------------

def check_text_sizes(fig) -> None:
    """Stop if any visible text in the figure is smaller than PT_TEXT points."""
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text().strip() and t.get_fontsize() < PT_TEXT - 1e-9:
            raise SourceError(f"text '{t.get_text()[:40]}' is {t.get_fontsize()} pt, "
                              f"below the {PT_TEXT} pt minimum")


def check_text_layout(fig) -> None:
    """Stop if any visible text runs past the figure's edges or overlaps other text."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.bbox.width, fig.bbox.height
    boxes = [(t.get_text(), t.get_window_extent(renderer)) for t in fig.findobj(Text)
             if t.get_visible() and t.get_text().strip()]
    for text, box in boxes:
        if box.x0 < -0.5 or box.y0 < -0.5 or box.x1 > width + 0.5 or box.y1 > height + 0.5:
            raise SourceError(f"text '{text[:40]}' runs past the edge of the figure")
    for i, (text_i, box_i) in enumerate(boxes):
        for text_j, box_j in boxes[i + 1:]:
            if box_i.overlaps(box_j):
                raise SourceError(f"text '{text_i[:40]}' overlaps text '{text_j[:40]}'")


def check_titles(fig) -> None:
    """Titles centered or absent: every bold text is a centered title, a panel letter
    at the left of its panel, or a row-group heading; every title is centered."""
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        gid = t.get_gid()
        bold = t.get_fontweight() in ("bold", 700, "heavy", "black")
        if gid == "title" and t.get_horizontalalignment() != "center":
            raise SourceError(f"title '{t.get_text()[:40]}' is not centered")
        if bold and gid not in ("title", "letter", "heading"):
            raise SourceError(f"bold text '{t.get_text()[:40]}' is not a centered title, a "
                              "panel letter or a row-group heading")
        if gid == "letter" and (t.get_text() not in "abcdef" or len(t.get_text()) != 1):
            raise SourceError(f"panel letter '{t.get_text()}' is not one lowercase letter")


def check_scale_and_labels(fig, rowlabels: bool) -> None:
    """Every rating and gap axis at SCALE mm per point; row labels clear of the plots."""
    fig.canvas.draw()
    px_per_mm = fig.dpi / 25.4
    axes = []
    for ax, gx, _cols in getattr(fig, "_dumbbell_axes", []):
        axes += [ax, gx]
    axes += getattr(fig, "_gap_axes", [])
    for a in axes:
        x0, x1 = a.get_xlim()
        mm = a.get_window_extent().width / px_per_mm
        same(f"axis {a.get_xlabel() or '(unlabeled)'} mm per point", mm / (x1 - x0), SCALE, 1e-6)
    if rowlabels:
        rend = fig.canvas.get_renderer()
        limit = min(a.get_window_extent().x0 for a in axes) / px_per_mm
        for t in fig.findobj(Text):
            if t.get_gid() in ("rowlabel", "heading") and t.get_text().strip():
                right = t.get_window_extent(rend).x1 / px_per_mm
                if right > limit - 1.0:
                    raise SourceError(f"row label '{t.get_text()}' runs into the plotting area")


def render(page_and_opts) -> tuple[bytes, bytes]:
    page, opts = page_and_opts
    fig = page.fig
    check_text_sizes(fig)
    check_text_layout(fig)
    check_titles(fig)
    check_scale_and_labels(fig, opts.get("rowlabels", False))
    pdf, png = io.BytesIO(), io.BytesIO()
    fig.savefig(pdf, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(png, format="png", dpi=300, metadata={"Software": None})
    plt.close(fig)
    return pdf.getvalue(), png.getvalue()


def plotted_csv() -> bytes:
    out = io.StringIO()
    cols = ["figure", "what", "value", "derivation", "file", "row", "column", "file_sha256"]
    writer = csv.DictWriter(out, fieldnames=cols, lineterminator="\n")
    writer.writeheader()
    for p in PLOTTED:
        writer.writerow({**p, "file_sha256": _CHECKSUMS.get(p["file"], "")})
    return out.getvalue().encode("utf-8")


def main() -> int:
    if not PIPELINE.is_dir():
        print(f"make_figures.py: pipeline folder not found: {PIPELINE}\n"
              "Set PIPELINE_DIR to the 'R Analysis Pipeline' folder.", file=sys.stderr)
        return 1
    try:
        outputs = {
            "fig1_design": render(figure1()),
            "fig2_results": render(figure2()),
            "figS_other_ratings": render(figure_s_other_ratings()),
            "figS_study1_raincloud": render(figure_s_raincloud()),
            "figS_study5_editing_time": render(figure_s_editing_time()),
            "figS_pooled_penalty": render(figure_s_pooled()),
            "figS_study1_ppc": render(figure_s_ppc()),
        }
    except SourceError as exc:
        print(f"make_figures.py stopped: {exc}\nNo figure was written.", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (pdf, png) in outputs.items():
        (OUT_DIR / f"{name}.pdf").write_bytes(pdf)
        (OUT_DIR / f"{name}.png").write_bytes(png)
    (OUT_DIR / "plotted_values.csv").write_bytes(plotted_csv())
    print("table\tsha256")
    for rel, digest in sorted(_CHECKSUMS.items()):
        print(f"{rel}\t{digest}")
    print(f"\nWrote {len(outputs)} figures (PDF and PNG) from {len(_CHECKSUMS)} files, and "
          f"{len(PLOTTED)} plotted values to plotted_values.csv, in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
