#!/usr/bin/env python3
"""Write every number the paper prints into generated/numbers.tex.

What this script does
---------------------
The analysis pipeline deposits its results as CSV tables. This script reads
those tables, takes one cell for each number the paper may cite, rounds it by
the rule below, and writes one LaTeX macro per number to
``generated/numbers.tex``. Each macro is followed by a comment that names the
table, the row and the column the number came from. The script also writes
``generated/numbers_check.csv``: one line per macro with its source, the cell
exactly as stored, the printed value, and the SHA-256 checksum of the table it
was read from, so anyone can check a printed number against the table.

The paper takes numbers only from these macros. A number typed by hand into
the manuscript is a bug.

Where the pipeline is
---------------------
By default the pipeline folder is found from this file's own location:
``../../../../Analysis/R Analysis Pipeline`` (tools -> Final Paper -> Writing
-> Docs -> project root). To read another copy, set the environment variable
``PIPELINE_DIR`` to that copy's ``R Analysis Pipeline`` folder.

Rounding rule
-------------
Every number is rounded from the cell as stored, half away from zero.

* ``dec2``   two decimals: ratings, rating differences, their intervals and
             standard errors, and other quantities on the rating scale.
             Study 1's H3 equivalence bound, registered as 0.20, is printed
             this way.
* ``es``     two decimals: effect sizes (Cohen's d, correlations, AUC,
             variance ratios, log-odds, model weights, power).
* ``dec3``   three decimals: differences in AUC, in word overlap and in topic
             share, which are always well below 0.1; the 0.224 and 0.219
             equivalence bounds of Studies 2 to 5; and Study 1's 0.448
             creativity penalty that sets the 0.224 bound.
* ``stat``   two decimals: t, F, z and chi-square statistics.
* ``df``     degrees of freedom: a whole number when within 0.05 of one,
             otherwise one decimal.
* ``p``      p-values in APA style: three decimals with no leading zero,
             "< .001" below .001, and "> .999" when the value rounds to 1.000
             (for example a Holm-corrected p capped at 1). The macro carries
             its own sign, so write ``$p$~\\SOneHOneCreatP`` to print
             "p = .001", "p < .001" or "p > .999".
* ``p4``     the same, with four decimals, for a p-value whose three-decimal
             form would sit exactly on .050 and hide which side of .05 it
             lies (Study 4's refit: .0501).
* ``count``  whole numbers, with a comma every three digits.
* ``pct``    a proportion printed as a percentage with one decimal
             (0.625 prints as 62.5%).
* ``pts``    a difference already stored in percentage points (0 to 100
             scale), printed with one decimal and no percent sign.
* ``pp``     a difference between two shares stored as a proportion (0 to 1
             scale), printed in percentage points: times 100, one decimal,
             no percent sign (-0.0133 prints as -1.3).

Derived numbers
---------------
A few numbers are not one cell but are computed here from table cells: the
total sample, sums and counts of rows (for example how many of the 24
registered equivalence tests passed), and the smallest and largest cell size.
Each is written by ``derived()`` below, never typed. Its comment in
numbers.tex and its note in numbers_check.csv state the tables and the rule,
and its checksum column lists the checksum of every table it read.

Negative numbers print with a true minus sign. The macros work in running
text and inside math.

When it stops
-------------
The script stops, and writes nothing, if a table, a row or a column is
missing, if a row description matches no row or more than one row, or if the
chosen cell is empty, NA or not a number.

How to run
----------
    python3 tools/make_numbers.py

from the Final Paper folder (or from anywhere: paths are found from this
file). It needs only Python 3.8 or later and its standard library.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
DEFAULT_PIPELINE = HERE / ".." / ".." / ".." / ".." / "Analysis" / "R Analysis Pipeline"
PIPELINE = Path(os.environ.get("PIPELINE_DIR", str(DEFAULT_PIPELINE))).resolve()
OUT_DIR = PAPER / "generated"
OUT_TEX = OUT_DIR / "numbers.tex"
OUT_CSV = OUT_DIR / "numbers_check.csv"

MINUS = r"\ensuremath{-}"


class SourceError(Exception):
    """A table, row, column or cell the paper needs is missing or unusable."""


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------

def _decimal(cell: str, where: str) -> Decimal:
    text = (cell or "").strip()
    if text == "" or text.upper() in {"NA", "NAN", "INF", "-INF", "TRUE", "FALSE"}:
        raise SourceError(f"{where}: the cell is '{cell}', not a number")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise SourceError(f"{where}: the cell '{cell}' is not a number") from exc


def _fixed(value: Decimal, places: int) -> str:
    quantum = Decimal(1).scaleb(-places)
    rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    text = f"{abs(rounded):.{places}f}"
    return (MINUS + text) if rounded < 0 else text


def _count(value: Decimal) -> str:
    rounded = int(value.to_integral_value(rounding=ROUND_HALF_UP))
    text = f"{abs(rounded):,}".replace(",", "{,}")
    return (MINUS + text) if rounded < 0 else text


def _df(value: Decimal) -> str:
    whole = value.to_integral_value(rounding=ROUND_HALF_UP)
    if abs(value - whole) < Decimal("0.05"):
        return _count(whole)
    return _fixed(value, 1)


def _p(value: Decimal) -> str:
    if value < 0 or value > 1:
        raise SourceError(f"p-value {value} lies outside 0 to 1")
    if value < Decimal("0.001"):
        return r"\ensuremath{<} .001"
    rounded = value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    if rounded >= 1:
        return r"\ensuremath{>} .999"
    text = f"{rounded:.3f}"
    if text.startswith("0"):
        text = text[1:]
    return r"\ensuremath{=} " + text


def _p4(value: Decimal) -> str:
    if value < 0 or value > 1:
        raise SourceError(f"p-value {value} lies outside 0 to 1")
    if value < Decimal("0.0001"):
        return r"\ensuremath{<} .0001"
    rounded = value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if rounded >= 1:
        return r"\ensuremath{>} .9999"
    text = f"{rounded:.4f}"
    if text.startswith("0"):
        text = text[1:]
    return r"\ensuremath{=} " + text


def _pct(value: Decimal) -> str:
    return _fixed(value * 100, 1) + r"\%"


FORMATS = {
    "dec2": lambda v: _fixed(v, 2),
    "es": lambda v: _fixed(v, 2),
    "stat": lambda v: _fixed(v, 2),
    "dec3": lambda v: _fixed(v, 3),
    "df": _df,
    "p": _p,
    "p4": _p4,
    "count": _count,
    "pct": _pct,
    "pts": lambda v: _fixed(v, 1),
    "pp": lambda v: _fixed(v * 100, 1),
}


# --------------------------------------------------------------------------
# Reading tables
# --------------------------------------------------------------------------

_TABLES: dict[str, list[dict[str, str]]] = {}
_CHECKSUMS: dict[str, str] = {}


def _table(rel: str) -> list[dict[str, str]]:
    if rel not in _TABLES:
        path = PIPELINE / rel
        if not path.is_file():
            raise SourceError(f"table not found: {rel} (looked in {PIPELINE})")
        raw = path.read_bytes()
        _CHECKSUMS[rel] = hashlib.sha256(raw).hexdigest()
        _TABLES[rel] = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        if not _TABLES[rel]:
            raise SourceError(f"table has no rows: {rel}")
    return _TABLES[rel]


def _matches(cell: str, wanted: str) -> bool:
    """Exact match, '^text' for a prefix, '~text' for a substring."""
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


def read_cell(rel: str, row: dict[str, str], column: str) -> str:
    rows = _table(rel)
    for col in list(row) + [column]:
        if col not in rows[0]:
            raise SourceError(f"{rel}: no column '{col}'")
    hits = [r for r in rows if all(_matches(r[c], w) for c, w in row.items())]
    if len(hits) != 1:
        raise SourceError(f"{rel}: the row '{_describe(row)}' matches {len(hits)} rows, not 1")
    return hits[0][column]


# --------------------------------------------------------------------------
# The numbers
# --------------------------------------------------------------------------

SPECS: list[dict] = []


def add(macro: str, rel: str, row: dict[str, str], column: str, fmt: str, note: str = "") -> None:
    SPECS.append({"macro": macro, "file": rel, "row": row, "column": column,
                  "fmt": fmt, "note": note})


def derived(macro: str, sources: list[str], compute, fmt: str, note: str) -> None:
    """A number computed from table cells by ``compute``, a function of no arguments.

    ``sources`` lists every table ``compute`` reads; ``note`` states the rule.
    """
    SPECS.append({"macro": macro, "file": "(derived)", "row": {}, "column": "", "fmt": fmt,
                  "note": note, "compute": compute, "sources": sources})


def rows_where(rel: str, row: dict[str, str]) -> list[dict[str, str]]:
    """Every row of a table that matches ``row`` (any number of rows, possibly none)."""
    rows = _table(rel)
    for col in row:
        if col not in rows[0]:
            raise SourceError(f"{rel}: no column '{col}'")
    return [r for r in rows if all(_matches(r[c], w) for c, w in row.items())]


def _flag(rel: str, r: dict[str, str], column: str) -> bool:
    """A TRUE or FALSE cell, read strictly."""
    if column not in r:
        raise SourceError(f"{rel}: no column '{column}'")
    value = r[column].strip().upper()
    if value not in {"TRUE", "FALSE"}:
        raise SourceError(f"{rel}: column '{column}' holds '{r[column]}', not TRUE or FALSE")
    return value == "TRUE"


def count_rows(rel: str, row: dict[str, str], expected_rows: int,
               test=lambda r: True) -> Decimal:
    """How many of the rows matching ``row`` pass ``test``.

    The script stops if ``row`` does not match exactly ``expected_rows`` rows, so a
    renamed row or a changed table cannot quietly change a count.
    """
    hits = rows_where(rel, row)
    if len(hits) != expected_rows:
        raise SourceError(f"{rel}: the rows '{_describe(row)}' number {len(hits)}, "
                          f"not the {expected_rows} expected")
    return Decimal(sum(1 for r in hits if test(r)))


def column_values(rel: str, row: dict[str, str], column: str, expected_rows: int) -> list[Decimal]:
    """The numbers in one column over the rows matching ``row``."""
    hits = rows_where(rel, row)
    if len(hits) != expected_rows:
        raise SourceError(f"{rel}: the rows '{_describe(row)}' number {len(hits)}, "
                          f"not the {expected_rows} expected")
    if column not in hits[0]:
        raise SourceError(f"{rel}: no column '{column}'")
    return [_decimal(r[column], f"{rel} [{_describe(row)}] column {column}") for r in hits]


DIMS1 = [("creativity", "Creat"), ("effort", "Eff")]
MEASURES = [("transformativeness", "Trans"), ("essence_change", "Ess"), ("creativity", "Creat")]
LEVELS = ["None", "Slight", "Dramatic"]
SOURCES = ["Human", "AI"]
HOURS_S3 = [("under 1 hour", "UnderOneHour"), ("10 hours", "TenHours"), ("100 hours", "HundredHours")]
HOURS = [("less than 1 hour", "UnderOneHour"), ("10 hours", "TenHours"), ("100 hours", "HundredHours")]


def recoverability(prefix: str, rel: str, dim: str, tag: str) -> None:
    """The text check run in every study: words to rating, words to arm, words beyond the rating."""
    base = {"dimension": dim, "target": "rating", "predictors": "words"}
    add(f"{prefix}TextRecRating{tag}", rel, base, "estimate", "es")
    add(f"{prefix}TextRecRating{tag}Lo", rel, base, "ci_low", "es")
    add(f"{prefix}TextRecRating{tag}Hi", rel, base, "ci_high", "es")
    add(f"{prefix}TextRecRating{tag}Null", rel, base, "null_95th", "es")
    arm = {"dimension": dim, "target": "arm", "predictors": "words"}
    add(f"{prefix}TextRecArm{tag}", rel, arm, "estimate", "es")
    add(f"{prefix}TextRecArm{tag}Lo", rel, arm, "ci_low", "es")
    add(f"{prefix}TextRecArm{tag}Hi", rel, arm, "ci_high", "es")
    rating = {"dimension": dim, "target": "arm", "predictors": "rating"}
    add(f"{prefix}TextRecArmFromRating{tag}", rel, rating, "estimate", "es")
    inc = {"dimension": dim, "predictors": "^incremental AUC"}
    add(f"{prefix}TextRecIncr{tag}", rel, inc, "estimate", "dec3")
    add(f"{prefix}TextRecIncr{tag}Lo", rel, inc, "ci_low", "dec3")
    add(f"{prefix}TextRecIncr{tag}Hi", rel, inc, "ci_high", "dec3")


def overlap(prefix: str, rel: str, row: dict[str, str], tag: str) -> None:
    """The other text check run in every study: own-word reuse, AI minus Human."""
    add(f"{prefix}TextOverlap{tag}Diff", rel, row, "estimate", "dec3")
    add(f"{prefix}TextOverlap{tag}Lo", rel, row, "ci_lo", "dec3")
    add(f"{prefix}TextOverlap{tag}Hi", rel, row, "ci_hi", "dec3")
    add(f"{prefix}TextOverlap{tag}PHolm", rel, row, "p_holm", "p")


# ---- Study 1 --------------------------------------------------------------
S1 = "Study 1/tables/"
f = S1 + "study1_exclusion_flow.csv"
add("SOneNRecords", f, {"step": "^Initial records"}, "n", "count")
add("SOneNPreviewRemoved", f, {"step": "^After (0)"}, "n_dropped", "count")
add("SOneNUnfinishedRemoved", f, {"step": "^After (1)"}, "n_dropped", "count")
add("SOneNNotSeriousRemoved", f, {"step": "^After (2)"}, "n_dropped", "count")
add("SOneNAttentionRemoved", f, {"step": "^After (3)"}, "n_dropped", "count")
add("SOneN", f, {"step": "^After (3)"}, "n", "count")
f = S1 + "study1_text_join_check.csv"
add("SOneNHuman", f, {"quantity": "participants in Human arm"}, "value", "count")
add("SOneNAI", f, {"quantity": "participants in AI arm"}, "value", "count")
add("SOneNRatings", f, {"quantity": "rows after join"}, "value", "count")
f = S1 + "study1_demo_age.csv"
add("SOneAgeMean", f, {}, "mean_age", "dec2")
add("SOneAgeSD", f, {}, "sd_age", "dec2")
add("SOneAgeMin", f, {}, "min_age", "count")
add("SOneAgeMax", f, {}, "max_age", "count")
f = S1 + "study1_demo_gender.csv"
add("SOneNFemale", f, {"Gender": "Female"}, "n", "count")
add("SOneNMale", f, {"Gender": "Male"}, "n", "count")
add("SOneNGenderOther", f, {"Gender": "Other"}, "n", "count")

cf = S1 + "study1_confirmatory_family.csv"
rob = S1 + "study1_robustness_h1_contrast.csv"
for dim, D in DIMS1:
    row = {"hypothesis": "H1", "test": f"~{dim}"}
    add(f"SOneHOne{D}Diff", cf, row, "estimate", "dec2")
    add(f"SOneHOne{D}SE", cf, row, "se", "dec2")
    add(f"SOneHOne{D}Df", cf, row, "df", "df")
    add(f"SOneHOne{D}T", cf, row, "statistic", "stat")
    add(f"SOneHOne{D}P", cf, row, "p_raw", "p")
    add(f"SOneHOne{D}PHolm", cf, row, "p_holm", "p")
    ref = {"check": "primary model (reference)", "dimension": dim}
    add(f"SOneHOne{D}Lo", rob, ref, "ci_lo", "dec2")
    add(f"SOneHOne{D}Hi", rob, ref, "ci_hi", "dec2")
add("SOneHOneCreatDiffPrecise", cf, {"hypothesis": "H1", "test": "~creativity"}, "estimate", "dec3",
    "three decimals: the creativity penalty whose half sets the 0.224 bound")

f = S1 + "study1_bootstrap_d.csv"
for dim, D in DIMS1:
    add(f"SOneD{D}", f, {"dimension": dim}, "d", "es")
    add(f"SOneD{D}Lo", f, {"dimension": dim}, "ci_lo", "es")
    add(f"SOneD{D}Hi", f, {"dimension": dim}, "ci_hi", "es")
    add(f"SOneDModel{D}", f, {"dimension": dim}, "d_model_based", "es")

f = S1 + "study1_joint_model_contrast_of_contrasts.csv"
row = {"Type_pairwise": "Human - AI"}
add("SOneHTwoDiff", f, row, "estimate", "dec2")
add("SOneHTwoSE", f, row, "SE", "dec2")
add("SOneHTwoDf", f, row, "df", "df")
add("SOneHTwoT", f, row, "t.ratio", "stat")
add("SOneHTwoLo", f, row, "lower.CL", "dec2")
add("SOneHTwoHi", f, row, "upper.CL", "dec2")
add("SOneHTwoP", cf, {"hypothesis": "H2"}, "p_raw", "p")
add("SOneHTwoPHolm", cf, {"hypothesis": "H2"}, "p_holm", "p")
f = S1 + "study1_h2_ordinal.csv"
add("SOneHTwoOrdEst", f, {"version": "ordinal"}, "estimate", "es")
add("SOneHTwoOrdSE", f, {"version": "ordinal"}, "SE", "es")
add("SOneHTwoOrdZ", f, {"version": "ordinal"}, "statistic", "stat")
add("SOneHTwoOrdP", f, {"version": "ordinal"}, "p", "p")
f = S1 + "study1_marginal_means.csv"
for src in SOURCES:
    for dim, D in DIMS1:
        add(f"SOneMean{src}{D}", f, {"Type": src, "dimension": dim}, "mean", "dec2")

f = S1 + "study1_h3_equivalence.csv"
pw = S1 + "study1_h3_equivalence_power.csv"
add("SOneHThreeBound", f, {"dimension": "creativity", "random_structure": "^intercepts only",
                           "bound_role": "registered"}, "bound_hi", "dec2",
    "two decimals: Study 1's H3 bound is registered as plus or minus 0.20")
for dim, D in DIMS1:
    reg = {"dimension": dim, "random_structure": "^intercepts only", "bound_role": "registered"}
    add(f"SOneHThree{D}Est", f, reg, "estimate", "dec2")
    add(f"SOneHThree{D}SE", f, reg, "se", "dec2")
    add(f"SOneHThree{D}LoNinety", f, reg, "ci90_lo", "dec2")
    add(f"SOneHThree{D}HiNinety", f, reg, "ci90_hi", "dec2")
    add(f"SOneHThree{D}PTost", f, reg, "tost_p", "p")
    add(f"SOneHThree{D}P", f, reg, "nhst_p", "p")
    mx = {"dimension": dim, "random_structure": "^maximal", "bound_role": "registered"}
    add(f"SOneHThree{D}MaxLoNinety", f, mx, "ci90_lo", "dec2")
    add(f"SOneHThree{D}MaxHiNinety", f, mx, "ci90_hi", "dec2")
    add(f"SOneHThree{D}MaxPTost", f, mx, "tost_p", "p")
    wide = {"dimension": dim, "random_structure": "^intercepts only", "bound_hi": "0.3"}
    add(f"SOneHThree{D}PTostWide", f, wide, "tost_p", "p", "descriptive bound of plus or minus 0.30")
    add(f"SOneHThree{D}Power", pw, {"dimension": dim, "true_interaction": "0", "bound": "0.2"},
        "equivalence_power", "es")
    add(f"SOneHThree{D}PowerWide", pw, {"dimension": dim, "true_interaction": "0", "bound": "0.3"},
        "equivalence_power", "es")
    add(f"SOneHThree{D}PowerSmall", pw, {"dimension": dim, "true_interaction": "0.1", "bound": "0.2"},
        "equivalence_power", "es",
        "registered sensitivity: power at plus or minus 0.20 when the true interaction is 0.1")

f = S1 + "study1_h4_variance_test.csv"
for dim, D in DIMS1:
    row = {"dimension": dim}
    add(f"SOneHFour{D}RatioBetween", f, row, "ratio_between_AI_over_Human", "es")
    add(f"SOneHFour{D}RatioBetweenLo", f, row, "ci_low_between", "es")
    add(f"SOneHFour{D}RatioBetweenHi", f, row, "ci_high_between", "es")
    add(f"SOneHFour{D}RatioResidual", f, row, "ratio_residual_AI_over_Human", "es")
    add(f"SOneHFour{D}RatioResidualLo", f, row, "ci_low_residual", "es")
    add(f"SOneHFour{D}RatioResidualHi", f, row, "ci_high_residual", "es")
    add(f"SOneHFour{D}Chisq", f, row, "lrt_between_chisq", "stat")
    add(f"SOneHFour{D}P", f, row, "lrt_between_p", "p")
    add(f"SOneHFour{D}ResidualP", f, row, "lrt_residual_p", "p")
add("SOneHFourPHolm", cf, {"hypothesis": "H4"}, "p_holm", "p")
f = S1 + "study1_h4_resolution.csv"
for dim, D in DIMS1:
    obs = {"dimension": dim, "setting": "observed"}
    add(f"SOneHFour{D}ResolutionPowerPct", f, obs, "lrt_reject_rate", "pct",
        "share of simulated datasets in which the between-participant test rejects, if the observed ratio is true")
    add(f"SOneHFour{D}ResolutionRatioLo", f, obs, "ratio_q025", "es",
        "2.5th percentile of the simulated ratio estimates; a spread, not a confidence interval")
    add(f"SOneHFour{D}ResolutionRatioHi", f, obs, "ratio_q975", "es",
        "97.5th percentile of the simulated ratio estimates; a spread, not a confidence interval")
    add(f"SOneHFour{D}ResolutionNullPct", f, {"dimension": dim, "setting": "null_pooled"},
        "lrt_reject_rate", "pct", "false-positive rate of the between-participant test under equal variances")
add("SOneHFourResolutionRatioForEighty", f, {"dimension": "creativity", "setting": "observed"},
    "smallest_grid_ratio_at_80pct", "es", "smallest grid ratio with 80 percent power; the same on both ratings")
f = S1 + "study1_h4_descriptive.csv"
for dim, D in DIMS1:
    for src in SOURCES:
        row = {"Type": src, "dimension": dim}
        note = ("descriptive, not part of the H4 criterion: participants who gave one rating "
                "to 7 or more of the 10 images")
        add(f"SOneHFour{D}SameRating{src}N", f, row, "n_same_on_7_or_more", "count", note)
        add(f"SOneHFour{D}SameRating{src}Pct", f, row, "prop_same_on_7_or_more", "pct", note)

f = S1 + "study1_item_sensitivity.csv"
add("SOneItemHOneEff", f, {"hypothesis": "H1", "sample": "^1FigureEff"}, "estimate", "dec2")
add("SOneItemHTwo", f, {"hypothesis": "H2", "sample": "^1FigureEff"}, "estimate", "dec2")
add("SOneItemHTwoImage", f, {"hypothesis": "H2", "sample": "^Figure_1"}, "estimate", "dec2")
note = ("three decimals: change from the full-sample estimate, in rating points, when the "
        "differently anchored effort item (or its image) is dropped; registered sensitivity check")
add("SOneItemHOneEffShift", f, {"hypothesis": "H1", "sample": "^1FigureEff"}, "difference_from_full", "dec3", note)
add("SOneItemHTwoShift", f, {"hypothesis": "H2", "sample": "^1FigureEff"}, "difference_from_full", "dec3", note)
add("SOneItemHTwoImageShift", f, {"hypothesis": "H2", "sample": "^Figure_1"}, "difference_from_full", "dec3", note)

for dim, D in DIMS1:
    g = {"check": "Bayesian replication, Gaussian", "dimension": dim}
    add(f"SOneBayes{D}", rob, g, "estimate", "dec2")
    add(f"SOneBayes{D}Lo", rob, g, "ci_lo", "dec2")
    add(f"SOneBayes{D}Hi", rob, g, "ci_hi", "dec2")
    o = {"check": "Bayesian replication, cumulative ordinal", "dimension": dim}
    add(f"SOneBayesOrd{D}", rob, o, "estimate", "es")
    c = {"check": "^covariates", "dimension": dim}
    add(f"SOneCov{D}", rob, c, "estimate", "dec2")
f = S1 + "study1_lmm_fully_maximal.csv"
for dim, D in DIMS1:
    row = {"dimension": dim, "term": "^H1 marginal contrast"}
    add(f"SOneMaximal{D}Est", f, row, "est_maximal", "dec2", "registered fully maximal fit; singular but converged")
    add(f"SOneMaximal{D}SE", f, row, "se_maximal", "dec2")
    add(f"SOneMaximal{D}P", f, row, "p_maximal", "p")
f = S1 + "study1_specification_curve.csv"
for dim, D in DIMS1:
    row = {"dimension": dim, "inference": "CLMM", "random_fx": "intercepts_only", "covariates": "none"}
    note = "registered ordinal (cumulative-link) check of H1, log-odds scale"
    add(f"SOneOrd{D}Est", f, row, "estimate", "es", note)
    add(f"SOneOrd{D}SE", f, row, "se", "es", note)
    add(f"SOneOrd{D}Lo", f, row, "ci_lo", "es", note)
    add(f"SOneOrd{D}Hi", f, row, "ci_hi", "es", note)
    add(f"SOneOrd{D}P", f, row, "p", "p", note)
f = S1 + "study1_specification_curve_counts.csv"
add("SOneSpecN", f, {"dimension": "creativity"}, "n_specs", "count")
for dim, D in DIMS1:
    add(f"SOneSpec{D}Min", f, {"dimension": dim}, "rating_est_min", "dec2")
    add(f"SOneSpec{D}Max", f, {"dimension": dim}, "rating_est_max", "dec2")
derived("SOneSpecNTotal", [f],
        lambda f=f: sum(column_values(f, {}, "n_specs", 2)), "count",
        f"derived: sum of n_specs over the creativity and effort rows of {f} "
        "(specifications on both ratings together)")
derived("SOneSpecNSigTotal", [f],
        lambda f=f: sum(column_values(f, {}, "n_sig_p05", 2)), "count",
        f"derived: sum of n_sig_p05 over the creativity and effort rows of {f} "
        "(specifications with p below .05, both ratings; descriptive, not evidence)")
f = S1 + "study1_influence_summary.csv"
for dim, D in DIMS1:
    add(f"SOneInfluence{D}Person", f, {"dimension": dim, "unit": "id"}, "max_abs_delta", "dec2")
    add(f"SOneInfluence{D}Image", f, {"dimension": dim, "unit": "stimulus_id"}, "max_abs_delta", "dec2")

f = S1 + "study1_text_denotation_tests.csv"
for comp, C in [("detail vs time", "DetailVsTime"), ("detail vs skill", "DetailVsSkill"),
                ("concept vs execution", "ConceptVsExecution"), ("concept vs novelty", "ConceptVsNovelty"),
                ("^prompt talk", "PromptEffortVsCreat")]:
    add(f"SOneText{C}Est", f, {"comparison": comp}, "estimate_log_odds", "es")
    add(f"SOneText{C}SE", f, {"comparison": comp}, "se", "es")
    add(f"SOneText{C}P", f, {"comparison": comp}, "p_raw", "p")
    add(f"SOneText{C}PBH", f, {"comparison": comp}, "p_bh", "p")
f = S1 + "study1_text_effort_prevalence.csv"
for q, Q in [("detail", "Detail"), ("time", "Time"), ("skill", "Skill"), ("none_of_the_three", "NoneOfThree")]:
    add(f"SOneTextEffort{Q}Pct", f, {"quantity": q}, "estimate", "pct")
f = S1 + "study1_text_creativity_prevalence.csv"
for q, Q in [("concept", "Concept"), ("novelty_either", "Novelty"), ("execution", "Execution"),
             ("none_of_the_three", "NoneOfThree")]:
    add(f"SOneTextCreat{Q}Pct", f, {"quantity": q}, "estimate", "pct")
f = S1 + "study1_text_prompt_by_arm.csv"
for src in SOURCES:
    add(f"SOneTextPromptEffort{src}Pct", f, {"dimension": "effort", "arm": src}, "estimate", "pct")
f = S1 + "study1_text_prompt_gap_within_rating.csv"
for src in SOURCES:
    add(f"SOneTextPromptEffortRatingThree{src}Pct", f, {"rating": "3"}, f"rate_prompt_{src}", "pct",
        "descriptive: share of effort justifications mentioning prompting or machines, "
        "among those given with an effort rating of 3")
f = S1 + "study1_text_belief_audit_counts.csv"
add("SOneBeliefBroadN", f, {"set": "^broad"}, "n_participants_flagged", "count")
add("SOneBeliefNarrowN", f, {"set": "^narrow"}, "n_participants_flagged", "count")
add("SOneBeliefNHuman", f, {"set": "^narrow"}, "n_human_participants", "count")
f = S1 + "study1_text_belief_audit_rate_ci.csv"
for s, S in [("^broad", "Broad"), ("^narrow", "Narrow")]:
    add(f"SOneBelief{S}Pct", f, {"set": s}, "estimate", "pct")
    add(f"SOneBelief{S}LoPct", f, {"set": s}, "ci_lo", "pct", "95 percent interval from 2,000 participant resamples")
    add(f"SOneBelief{S}HiPct", f, {"set": s}, "ci_hi", "pct", "95 percent interval from 2,000 participant resamples")
f = S1 + "study1_text_belief_audit_exclusion_refit.csv"
for dim, D in DIMS1:
    row = {"set": "excluding the narrow set", "dimension": dim}
    add(f"SOneBeliefRefit{D}Diff", f, row, "lmm_estimate", "dec2")
    add(f"SOneBeliefRefit{D}D", f, row, "d", "es")
f = S1 + "study1_text_leakage_placebo.csv"
for dim, D in DIMS1:
    row = {"dimension": dim}
    note = "leakage placebo: 2,000 matched random removals of 25 Human-arm participants (descriptive)"
    add(f"SOnePlacebo{D}NullMedian", f, row, "null_median", "es", note)
    add(f"SOnePlacebo{D}NullLo", f, row, "null_ci_lo", "es", note)
    add(f"SOnePlacebo{D}NullHi", f, row, "null_ci_hi", "es", note)
    add(f"SOnePlacebo{D}PercentilePct", f, row, "observed_percentile", "pct", note)
    add(f"SOnePlacebo{D}P", f, row, "p_two_sided", "p",
        note + "; a stored 0 means no matched draw was as extreme, and prints as < .001")
f = S1 + "study1_text_novelty_within_between.csv"
for dim, D in DIMS1:
    for arm in SOURCES:
        row = {"dimension": dim, "arm": arm, "term": "asserted_within"}
        note = ("registered within-person association of calling a work familiar with the rating"
                if dim == "creativity" else "effort: the comparison the registration names, description")
        add(f"SOneFamiliar{D}{arm}Est", f, row, "estimate", "dec2", note)
        add(f"SOneFamiliar{D}{arm}Lo", f, row, "conf.low", "dec2", note)
        add(f"SOneFamiliar{D}{arm}Hi", f, row, "conf.high", "dec2", note)
        add(f"SOneFamiliar{D}{arm}P", f, row, "p.value", "p", note)
f = S1 + "study1_text_recoverability.csv"
for dim, D in DIMS1:
    recoverability("SOne", f, dim, D)
f = S1 + "study1_text_selfsimilarity_by_arm.csv"
for dim, D in DIMS1:
    overlap("SOne", f, {"dimension": dim, "role": "registered comparison"}, D)

# ---- Study 2 --------------------------------------------------------------
S2 = "Study 2/tables/"
f = S2 + "study2_exclusion_flow.csv"
add("STwoNRecords", f, {"step": "records in export"}, "n", "count")
add("STwoNUnfinishedRemoved", f, {"step": "unfinished sessions"}, "removed", "count")
add("STwoNNotSeriousRemoved", f, {"step": "^seriousness"}, "removed", "count")
add("STwoN", f, {"step": "no recorded condition"}, "n", "count")
f = S2 + "study2_sample_checks.csv"
add("STwoNHuman", f, {"quantity": "^participants in the Human"}, "observed", "count")
add("STwoNAI", f, {"quantity": "^participants in the AI"}, "observed", "count")
add("STwoNRatings", f, {"quantity": "ratings analysed"}, "observed", "count")
add("STwoNSixPointDropped", f, {"quantity": "^ratings on the two six-point"}, "observed", "count")
add("STwoNLackingOneTrial", f, {"quantity": "participants with 87 ratings"}, "observed", "count",
    "participants whose records lack one Slight trial (1FigureMin), so they rated 29 second works")
f = S2 + "study2_equivalence.csv"
add("SourceBound", f, {"measure": "creativity"}, "bound", "dec3",
    "the bound of Studies 2 to 5: half of Study 1's creativity penalty")

cf = S2 + "study2_confirmatory_family.csv"
eq = S2 + "study2_equivalence.csv"
sbm = S2 + "study2_source_by_modification.csv"
emm = S2 + "study2_emmeans.csv"
for meas, M in MEASURES:
    for test, name in [("1", "SlightMinusNone"), ("2", "DramaticMinusSlight")]:
        row = {"measure": meas, "test": test}
        add(f"STwo{M}{name}Est", cf, row, "estimate", "dec2")
        add(f"STwo{M}{name}Lo", cf, row, "ci95_lo", "dec2")
        add(f"STwo{M}{name}Hi", cf, row, "ci95_hi", "dec2")
        add(f"STwo{M}{name}T", cf, row, "statistic", "stat")
        add(f"STwo{M}{name}Df", cf, row, "df", "df")
        add(f"STwo{M}{name}PHolm", cf, row, "p_holm", "p")
    row = {"measure": meas, "test": "3"}
    add(f"STwo{M}PenaltyEst", cf, row, "estimate", "dec2")
    add(f"STwo{M}PenaltyLo", cf, row, "ci95_lo", "dec2")
    add(f"STwo{M}PenaltyHi", cf, row, "ci95_hi", "dec2")
    add(f"STwo{M}PenaltyP", cf, row, "p_two_sided", "p")
    add(f"STwo{M}PenaltyLoNinety", eq, {"measure": meas}, "ci90_lo", "dec2")
    add(f"STwo{M}PenaltyHiNinety", eq, {"measure": meas}, "ci90_hi", "dec2")
    add(f"STwo{M}PenaltyPTost", eq, {"measure": meas}, "p_tost", "p")
    add(f"STwo{M}PenaltyPHolm", eq, {"measure": meas}, "p_holm", "p")
    row = {"measure": meas, "test": "4"}
    add(f"STwo{M}PenaltyChangeEst", cf, row, "estimate", "dec2")
    add(f"STwo{M}PenaltyChangeLo", cf, row, "ci95_lo", "dec2")
    add(f"STwo{M}PenaltyChangeHi", cf, row, "ci95_hi", "dec2")
    add(f"STwo{M}PenaltyChangeP", cf, row, "p_two_sided", "p")
    add(f"STwo{M}PenaltyChangePHolm", cf, row, "p_holm", "p")
    for lev in LEVELS:
        row = {"measure": meas, "modification": lev}
        add(f"STwo{M}Penalty{lev}Est", sbm, row, "estimate", "dec2")
        add(f"STwo{M}Penalty{lev}Lo", sbm, row, "ci95_lo", "dec2")
        add(f"STwo{M}Penalty{lev}Hi", sbm, row, "ci95_hi", "dec2")
        add(f"STwo{M}Penalty{lev}P", sbm, row, "p_two_sided", "p")
        add(f"STwo{M}Mean{lev}", emm, {"measure": meas, "means_of": "modification", "modification": lev},
            "emmean", "dec2")
        for src in SOURCES:
            add(f"STwo{M}Mean{src}{lev}", emm,
                {"measure": meas, "means_of": "source by modification", "source": src, "modification": lev},
                "emmean", "dec2")
    for src in SOURCES:
        add(f"STwo{M}Mean{src}", emm, {"measure": meas, "means_of": "source", "source": src}, "emmean", "dec2")
# The registered cumulative-link (ordinal) check of tests 1, 2 and 4. Creativity is
# left out on purpose: that fit did not converge, so by the pipeline's rule it has no
# p-value and its estimates are description only.
cl = S2 + "study2_clmm_check.csv"
for meas, M in [("transformativeness", "Trans"), ("essence_change", "Ess")]:
    for test, name in [("1", "SlightMinusNone"), ("2", "DramaticMinusSlight"), ("4", "PenaltyChange")]:
        row = {"measure": meas, "test": test}
        note = "registered ordinal check, logit scale"
        add(f"STwo{M}{name}OrdEst", cl, row, "clmm_estimate", "es", note)
        add(f"STwo{M}{name}OrdSE", cl, row, "clmm_se", "es", note)
        add(f"STwo{M}{name}OrdZ", cl, row, "clmm_z", "stat", note)
        add(f"STwo{M}{name}OrdP", cl, row, "clmm_p", "p", note)
        add(f"STwo{M}{name}OrdPHolm", cl, row, "clmm_p_holm", "p", note)
recoverability("STwo", S2 + "study2_text_recoverability.csv", "creativity", "Creat")
overlap("STwo", S2 + "study2_text_selfsimilarity_by_arm.csv",
        {"dimension": "creativity", "quantity": "arm_difference_AI_minus_Human"}, "Creat")

# ---- Study 3 --------------------------------------------------------------
S3 = "Study 3/tables/"
f = S3 + "study3_exclusion_flow.csv"
add("SThreeNRecords", f, {"step": "records in export"}, "n", "count")
add("SThreeNPreviewRemoved", f, {"step": "^survey test runs"}, "removed", "count")
add("SThreeNUnfinishedRemoved", f, {"step": "unfinished records"}, "removed", "count")
add("SThreeNNotSeriousRemoved", f, {"step": "^seriousness"}, "removed", "count")
add("SThreeNArithmeticRemoved", f, {"step": "^wrong answer"}, "removed", "count")
add("SThreeN", f, {"step": "^wrong answer"}, "n", "count")
f = S3 + "study3_sample_checks.csv"
add("SThreeNHuman", f, {"quantity": "^participants in the Human"}, "observed", "count")
add("SThreeNAI", f, {"quantity": "^participants in the AI"}, "observed", "count")
add("SThreeNJustifications", f, {"quantity": "justifications"}, "observed", "count")
add("SThreeNRatings", f, {"quantity": "ratings"}, "observed", "count")

ft = S3 + "study3_lmm_ftests.csv"
cl = S3 + "study3_clmm_check.csv"
eq = S3 + "study3_equivalence.csv"
gbt = S3 + "study3_gap_by_time.csv"
tc = S3 + "study3_time_contrast.csv"
dec = S3 + "study3_decision.csv"
emc = S3 + "study3_emmeans_cells.csv"
for dim, D in DIMS1:
    for term, T in [("Type", "Source"), ("time", "Time"), ("Type:time", "SourceByTime")]:
        row = {"dimension": dim, "term": term}
        add(f"SThree{D}{T}F", ft, row, "F", "stat")
        add(f"SThree{D}{T}DfNum", ft, row, "num_df", "df")
        add(f"SThree{D}{T}DfDen", ft, row, "den_df", "df")
        add(f"SThree{D}{T}P", ft, row, "p_raw", "p")
        add(f"SThree{D}{T}PHolm", ft, row, "p_holm", "p")
        add(f"SThree{D}{T}OrdChisq", cl, row, "chisq", "stat")
        add(f"SThree{D}{T}OrdP", cl, row, "p_raw", "p")
        add(f"SThree{D}{T}OrdPHolm", cl, row, "p_holm", "p")
    reg = {"dimension": dim, "fit": "registered model"}
    add(f"SThree{D}GapHundredLoNinety", eq, reg, "ci90_low", "dec2")
    add(f"SThree{D}GapHundredHiNinety", eq, reg, "ci90_high", "dec2")
    add(f"SThree{D}GapHundredPTost", eq, reg, "tost_p", "p")
    slope = {"dimension": dim, "fit": "random-slope refit"}
    add(f"SThree{D}GapHundredSlopeEst", eq, slope, "gap_100", "dec2")
    add(f"SThree{D}GapHundredSlopeLoNinety", eq, slope, "ci90_low", "dec2")
    add(f"SThree{D}GapHundredSlopeHiNinety", eq, slope, "ci90_high", "dec2")
    for t, T in HOURS_S3:
        row = {"dimension": dim, "time": t}
        add(f"SThree{D}Gap{T}Est", gbt, row, "estimate", "dec2")
        add(f"SThree{D}Gap{T}Lo", gbt, row, "lower.CL", "dec2")
        add(f"SThree{D}Gap{T}Hi", gbt, row, "upper.CL", "dec2")
        add(f"SThree{D}Gap{T}P", gbt, row, "p.value", "p")
        for src in SOURCES:
            add(f"SThree{D}Mean{src}{T}", emc, {"dimension": dim, "Type": src, "time": t}, "emmean", "dec2")
    row = {"dimension": dim}
    add(f"SThree{D}TimeContrastEst", tc, row, "estimate", "dec2")
    add(f"SThree{D}TimeContrastSE", tc, row, "SE", "dec2")
    add(f"SThree{D}TimeContrastLo", tc, row, "lower.CL", "dec2")
    add(f"SThree{D}TimeContrastHi", tc, row, "upper.CL", "dec2")
    add(f"SThree{D}TimeContrastP", tc, row, "p.value", "p")
    add(f"SThree{D}GapUnderOneHourDecision", dec, row, "gap_under_1_hour", "dec2",
        "the same contrast as the gap at under 1 hour, as the decision table holds it")
add("SThreeTimeContrastPrecise", tc, {"dimension": "creativity"}, "estimate", "dec3",
    "three decimals: the contrast that sets Study 5's editing-time bound")
f = S3 + "study3_text_recoverability.csv"
for dim, D in DIMS1:
    recoverability("SThree", f, dim, D)
f = S3 + "study3_text_selfsimilarity_by_arm.csv"
for dim, D in DIMS1:
    overlap("SThree", f, {"dimension": dim, "role": "registered comparison"}, D)
f = S3 + "study3_text_wordlist_comparisons.csv"
for dim, D, wl, W in [("effort", "Eff", "says_detail", "Detail"), ("effort", "Eff", "says_prompt", "Prompt"),
                      ("creativity", "Creat", "says_prompt", "Prompt")]:
    row = {"dimension": dim, "word_list": wl, "comparison": "^AI minus Human"}
    note = ("exploratory, uncorrected: AI minus Human share of justifications the word list flags, "
            "pooled over stated time, in percentage points; 95 percent interval from 2,000 "
            "participant resamples")
    add(f"SThreeTextWord{D}{W}Diff", f, row, "estimate", "pts", note)
    add(f"SThreeTextWord{D}{W}Lo", f, row, "ci_lo", "pts", note)
    add(f"SThreeTextWord{D}{W}Hi", f, row, "ci_hi", "pts", note)

# ---- Study 4 --------------------------------------------------------------
S4 = "Study 4/tables/"
f = S4 + "study4_exclusion_flow.csv"
add("SFourNRecords", f, {"step": "records in export"}, "n", "count")
add("SFourNPreviewRemoved", f, {"step": "^preview records"}, "removed", "count")
add("SFourNUnfinishedRemoved", f, {"step": "unfinished records"}, "removed", "count")
add("SFourNNotSeriousRemoved", f, {"step": "^any seriousness"}, "removed", "count")
add("SFourNArithmeticRemoved", f, {"step": "^wrong answers"}, "removed", "count")
add("SFourNInvalidRemoved", f, {"step": "^records that are not"}, "removed", "count")
add("SFourN", f, {"step": "^records that are not"}, "n", "count")
f = S4 + "study4_sample_checks.csv"
add("SFourNHuman", f, {"quantity": "participants in the Human arm"}, "observed", "count")
add("SFourNAI", f, {"quantity": "participants in the AI arm"}, "observed", "count")
add("SFourNJustifications", f, {"quantity": "justifications"}, "observed", "count")
add("SFourNSixPointDropped", f, {"quantity": "^ratings on the two six-point"}, "observed", "count")
add("SFourNRatings", f, {"quantity": "analysed ratings"}, "observed", "count")

cf = S4 + "study4_confirmatory_family.csv"
an = S4 + "study4_lmm_anova.csv"
lbm = S4 + "study4_secondary_label_by_modification.csv"
lbt = S4 + "study4_secondary_label_by_source_time.csv"
te = S4 + "study4_secondary_time_equivalence.csv"
emm = S4 + "study4_emmeans_marginal.csv"
for meas, M in MEASURES:
    for test, name in [("1", "SlightMinusNone"), ("2", "DramaticMinusSlight")]:
        row = {"measure": meas, "test_number": test}
        add(f"SFour{M}{name}Est", cf, row, "estimate", "dec2")
        add(f"SFour{M}{name}SE", cf, row, "std_error", "dec2")
        add(f"SFour{M}{name}T", cf, row, "statistic", "stat")
        add(f"SFour{M}{name}Df", cf, row, "den_df", "df")
        add(f"SFour{M}{name}PHolm", cf, row, "p_holm", "p")
    row = {"measure": meas, "test_number": "3"}
    add(f"SFour{M}PenaltyEst", cf, row, "estimate", "dec2")
    add(f"SFour{M}PenaltySE", cf, row, "std_error", "dec2")
    add(f"SFour{M}PenaltyDf", cf, row, "den_df", "df")
    add(f"SFour{M}PenaltyLoNinety", cf, row, "ci90_low", "dec2")
    add(f"SFour{M}PenaltyHiNinety", cf, row, "ci90_high", "dec2")
    add(f"SFour{M}PenaltyPTost", cf, row, "p_raw", "p", "p_raw of test 3 is the equivalence (two one-sided tests) p")
    add(f"SFour{M}PenaltyPHolm", cf, row, "p_holm", "p")
    for test, name in [("4", "SourceTime"), ("5", "SourceTimeByMod")]:
        row = {"measure": meas, "test_number": test}
        add(f"SFour{M}{name}F", cf, row, "statistic", "stat")
        add(f"SFour{M}{name}DfNum", cf, row, "num_df", "df")
        add(f"SFour{M}{name}DfDen", cf, row, "den_df", "df")
        add(f"SFour{M}{name}P", cf, row, "p_raw", "p")
        add(f"SFour{M}{name}PHolm", cf, row, "p_holm", "p")
    for term, name in [("label", "Label"), ("label:modification", "LabelByMod")]:
        row = {"measure": meas, "term": term}
        add(f"SFour{M}{name}F", an, row, "F", "stat")
        add(f"SFour{M}{name}DfNum", an, row, "num_df", "df")
        add(f"SFour{M}{name}DfDen", an, row, "den_df", "df")
        add(f"SFour{M}{name}P", an, row, "p", "p")
    row = {"measure": meas, "source_time": "less than 1 hour"}
    add(f"SFour{M}LabelBySourceTimeF", lbt, row, "interaction_F", "stat")
    add(f"SFour{M}LabelBySourceTimeP", lbt, row, "interaction_p", "p")
    for lev in LEVELS:
        row = {"measure": meas, "modification": lev}
        add(f"SFour{M}Penalty{lev}Est", lbm, row, "estimate", "dec2")
        add(f"SFour{M}Penalty{lev}Lo", lbm, row, "ci95_low", "dec2")
        add(f"SFour{M}Penalty{lev}Hi", lbm, row, "ci95_high", "dec2")
        add(f"SFour{M}Penalty{lev}P", lbm, row, "p_two_sided", "p")
        add(f"SFour{M}Penalty{lev}LoNinety", lbm, row, "ci90_low", "dec2")
        add(f"SFour{M}Penalty{lev}HiNinety", lbm, row, "ci90_high", "dec2")
        add(f"SFour{M}Penalty{lev}PTost", lbm, row, "tost_p", "p")
        add(f"SFour{M}Mean{lev}", emm, {"measure": meas, "factor": "modification", "level": lev}, "emmean", "dec2")
    for src in SOURCES:
        add(f"SFour{M}Mean{src}", emm, {"measure": meas, "factor": "label", "level": src}, "emmean", "dec2")
    row = {"measure": meas}
    add(f"SFour{M}TimeContrastEst", te, row, "estimate", "dec2")
    add(f"SFour{M}TimeContrastLoNinety", te, row, "ci90_low", "dec2")
    add(f"SFour{M}TimeContrastHiNinety", te, row, "ci90_high", "dec2")
    add(f"SFour{M}TimeContrastPTost", te, row, "tost_p", "p")
# The registered cumulative-link (ordinal) check: tests 1 and 2 as Wald z tests,
# tests 4 and 5 as Wald chi-square tests, Holm-corrected in the family of fifteen.
cl = S4 + "study4_clmm_check.csv"
for meas, M in MEASURES:
    for test, name in [("1", "SlightMinusNone"), ("2", "DramaticMinusSlight")]:
        row = {"measure": meas, "test_number": test}
        note = "registered ordinal check, logit scale, Wald z test"
        add(f"SFour{M}{name}OrdEst", cl, row, "clmm_estimate", "es", note)
        add(f"SFour{M}{name}OrdZ", cl, row, "clmm_statistic", "stat", note)
        add(f"SFour{M}{name}OrdP", cl, row, "clmm_p_raw", "p", note)
        add(f"SFour{M}{name}OrdPHolm", cl, row, "clmm_p_holm", "p", note)
    for test, name in [("4", "SourceTime"), ("5", "SourceTimeByMod")]:
        row = {"measure": meas, "test_number": test}
        note = "registered ordinal check, Wald chi-square test"
        add(f"SFour{M}{name}OrdChisq", cl, row, "clmm_statistic", "stat", note)
        add(f"SFour{M}{name}OrdDf", cl, row, "clmm_df", "df", note)
        add(f"SFour{M}{name}OrdP", cl, row, "clmm_p_raw", "p", note)
        add(f"SFour{M}{name}OrdPHolm", cl, row, "clmm_p_holm", "p", note)
f = S4 + "study4_secondary_refit_machine_made.csv"
add("SFourEssPenaltyPHolmRefit", f, {"measure": "essence_change", "test_number": "3"}, "p_holm_refit", "p")
add("SFourEssPenaltyPHolmRefitPrecise", f, {"measure": "essence_change", "test_number": "3"},
    "p_holm_refit", "p4", "four decimals: at three decimals this p prints as .050 and hides that it lies above .05")
add("SFourNRefit", f, {"measure": "essence_change", "test_number": "3"}, "n_participants_refit", "count")
derived("SFourNRefitVerdicts", [f], lambda f=f: count_rows(f, {}, 15), "count",
        f"derived: rows of {f}, one per registered test refitted without the flagged Human-arm participants")
derived("SFourNRefitVerdictsChanged", [f],
        lambda f=f: count_rows(f, {}, 15, lambda r: not _flag(f, r, "verdict_unchanged")), "count",
        f"derived: rows of {f} whose verdict_unchanged is FALSE (registered verdicts that change in the refit)")
f = S4 + "study4_text_machine_made_count.csv"
row = {"scope": "all justifications"}
add("SFourMachineMadeN", f, row, "n_participants_asserting", "count")
add("SFourMachineMadeNHuman", f, row, "n_human_participants", "count")
add("SFourMachineMadeResponses", f, row, "n_responses_asserted", "count")
add("SFourMachineMadeNResponses", f, row, "n_human_responses", "count")
recoverability("SFour", S4 + "study4_text_recoverability.csv", "creativity", "Creat")
overlap("SFour", S4 + "study4_text_selfsimilarity_by_arm.csv",
        {"dimension": "creativity", "quantity": "arm_difference_AI_minus_Human"}, "Creat")

# ---- Study 5 --------------------------------------------------------------
S5 = "Study 5/tables/"
f = S5 + "study5_exclusion_flow_registered.csv"
add("SFiveNRecords", f, {"step": "records in export"}, "n", "count")
add("SFiveNUnfinishedRemoved", f, {"step": "^2."}, "removed", "count")
add("SFiveNNotSeriousRemoved", f, {"step": "^3."}, "removed", "count")
add("SFiveNArithmeticRemoved", f, {"step": "^4."}, "removed", "count")
add("SFiveNNoConditionRemoved", f, {"step": "^5."}, "removed", "count")
add("SFiveN", f, {"step": "^5."}, "n", "count")
f = S5 + "study5_cell_counts_registered.csv"
for src in SOURCES:
    for t, T in HOURS:
        add(f"SFiveN{src}{T}", f, {"source": src, "editing_time": t}, "n", "count")
derived("SFiveNCellMin", [f], lambda f=f: min(column_values(f, {}, "n", 6)), "count",
        f"derived: smallest n over the six label-by-editing-time cells of {f}")
derived("SFiveNCellMax", [f], lambda f=f: max(column_values(f, {}, "n", 6)), "count",
        f"derived: largest n over the six label-by-editing-time cells of {f}")
f = S5 + "study5_text_selfsimilarity_by_arm.csv"
add("SFiveNHuman", f, {"role": "registered comparison"}, "n_human", "count")
add("SFiveNAI", f, {"role": "registered comparison"}, "n_ai", "count")
f = "Cross-study/tables/crossstudy_input_checks.csv"
add("SFiveNRatings", f, {"study": "Study 5", "quantity": "analysed ratings in the primary analysis"},
    "observed", "count", "ratings analyzed, as STwoNRatings and SFourNRatings")
add("SFiveNRatingsAll", f, {"study": "Study 5", "quantity": "ratings in the file"}, "observed", "count",
    "every rating, the two six-point items included")
add("SFiveNSixPointDropped", f, {"study": "Study 5", "quantity": "^six-point ratings"}, "observed", "count",
    "ratings on the two six-point items, left out of the primary analysis")

cf = S5 + "study5_confirmatory_family.csv"
et = S5 + "study5_equivalence_editing_time.csv"
es = S5 + "study5_equivalence_source.csv"
ems = S5 + "study5_emmeans_source_by_modification.csv"
eme = S5 + "study5_emmeans_editing_time.csv"
add("SFiveEditTimeBound", et, {"rating": "creativity"}, "bound", "dec3",
    "Study 5's editing-time bound, read from Study 3's creativity time contrast")
derived("SFiveNConfirmatory", [cf], lambda cf=cf: count_rows(cf, {}, 6), "count",
        f"derived: rows of {cf}, one per registered confirmatory test")
derived("SFiveNConfirmatoryHolmSignificant", [cf],
        lambda cf=cf: count_rows(cf, {}, 6, lambda r: _flag(cf, r, "holm_significant")), "count",
        f"derived: rows of {cf} whose holm_significant is TRUE")
add("SFiveCreatPenaltyDramaticHiNinetyPrecise", es, {"rating": "creativity", "modification": "Dramatic"},
    "ci90_hi", "dec3", "three decimals: the upper end that misses the 0.224 bound, so the verdict is inconclusive")
f = S5 + "study5_lmm_anova.csv"
row = {"rating": "creativity", "term": "source:editing_time:modification"}
note = "exploratory: a term of the registered model that has no registered test; uncorrected"
add("SFiveCreatSourceByEditTimeByModF", f, row, "F", "stat", note)
add("SFiveCreatSourceByEditTimeByModDfNum", f, row, "num_df", "df", note)
add("SFiveCreatSourceByEditTimeByModDfDen", f, row, "den_df", "df", note)
add("SFiveCreatSourceByEditTimeByModP", f, row, "p", "p", note)
for meas, M in MEASURES:
    for term, name in [("editing_time", "EditTime"), ("source:editing_time", "SourceByEditTime")]:
        row = {"rating": meas, "term": term}
        add(f"SFive{M}{name}F", cf, row, "F", "stat")
        add(f"SFive{M}{name}DfNum", cf, row, "num_df", "df")
        add(f"SFive{M}{name}DfDen", cf, row, "den_df", "df")
        add(f"SFive{M}{name}P", cf, row, "p_raw", "p")
        add(f"SFive{M}{name}PHolm", cf, row, "p_holm", "p")
    row = {"rating": meas}
    add(f"SFive{M}EditTimeContrastEst", et, row, "estimate", "dec2")
    add(f"SFive{M}EditTimeContrastLoNinety", et, row, "ci90_lo", "dec2")
    add(f"SFive{M}EditTimeContrastHiNinety", et, row, "ci90_hi", "dec2")
    add(f"SFive{M}EditTimeContrastP", et, row, "p_contrast", "p")
    add(f"SFive{M}EditTimeContrastPTost", et, row, "tost_p", "p")
    for lev in LEVELS:
        row = {"rating": meas, "modification": lev}
        add(f"SFive{M}Penalty{lev}Est", es, row, "estimate", "dec2")
        add(f"SFive{M}Penalty{lev}LoNinety", es, row, "ci90_lo", "dec2")
        add(f"SFive{M}Penalty{lev}HiNinety", es, row, "ci90_hi", "dec2")
        add(f"SFive{M}Penalty{lev}P", es, row, "p_contrast", "p")
        add(f"SFive{M}Penalty{lev}PTost", es, row, "tost_p", "p")
        for src in SOURCES:
            add(f"SFive{M}Mean{src}{lev}", ems, {"rating": meas, "source": src, "modification": lev},
                "emmean", "dec2")
    for t, T in HOURS:
        add(f"SFive{M}Mean{T}", eme, {"rating": meas, "editing_time": t}, "emmean", "dec2")
f = S5 + "study5_clmm_holm_check.csv"
row = {"rating": "creativity", "term": "source:editing_time"}
add("SFiveCreatSourceByEditTimeOrdChisq", f, row, "clmm_chisq", "stat")
add("SFiveCreatSourceByEditTimeOrdP", f, row, "clmm_p_raw", "p")
add("SFiveCreatSourceByEditTimeOrdPHolm", f, row, "clmm_p_holm", "p")
# The registered second analysis: every item rescaled 0 to 1, the six Holm tests repeated.
f = S5 + "study5_rescaled_family.csv"
for meas, M in MEASURES:
    for term, name in [("editing_time", "EditTime"), ("source:editing_time", "SourceByEditTime")]:
        row = {"rating": meas, "term": term}
        note = "registered second analysis, all items rescaled 0 to 1"
        add(f"SFive{M}{name}RescaledF", f, row, "F", "stat", note)
        add(f"SFive{M}{name}RescaledDfNum", f, row, "num_df", "df", note)
        add(f"SFive{M}{name}RescaledDfDen", f, row, "den_df", "df", note)
        add(f"SFive{M}{name}RescaledP", f, row, "p_raw", "p", note)
        add(f"SFive{M}{name}RescaledPHolm", f, row, "p_holm", "p", note)
f = S5 + "study5_text_recoverability.csv"
base = {"target": "rating", "predictors": "words"}
add("SFiveTextRecRatingCreat", f, base, "estimate", "es")
add("SFiveTextRecRatingCreatLo", f, base, "ci_low", "es")
add("SFiveTextRecRatingCreatHi", f, base, "ci_high", "es")
add("SFiveTextRecRatingCreatNull", f, base, "null_95th", "es")
arm = {"target": "arm", "predictors": "words"}
add("SFiveTextRecArmCreat", f, arm, "estimate", "es")
add("SFiveTextRecArmCreatLo", f, arm, "ci_low", "es")
add("SFiveTextRecArmCreatHi", f, arm, "ci_high", "es")
add("SFiveTextRecArmFromRatingCreat", f, {"target": "arm", "predictors": "rating"}, "estimate", "es")
inc = {"predictors": "^incremental AUC"}
add("SFiveTextRecIncrCreat", f, inc, "estimate", "dec3")
add("SFiveTextRecIncrCreatLo", f, inc, "ci_low", "dec3")
add("SFiveTextRecIncrCreatHi", f, inc, "ci_high", "dec3")
overlap("SFive", S5 + "study5_text_selfsimilarity_by_arm.csv", {"role": "registered comparison"}, "Creat")
f = S5 + "study5_text_machine_made_count.csv"
row = {"scope": "all justifications"}
add("SFiveMachineMadeN", f, row, "n_participants_asserting", "count")
add("SFiveMachineMadeNHuman", f, row, "n_human_participants", "count")
add("SFiveMachineMadeResponses", f, row, "n_responses_asserted", "count")
add("SFiveMachineMadeNResponses", f, row, "n_human_responses", "count")

# ---- Cross-study (all exploratory) ----------------------------------------
XS = "Cross-study/tables/"
STUDIES = [("Study 2", "STwo"), ("Study 4", "SFour"), ("Study 5", "SFive")]
pbl = XS + "crossstudy_penalty_by_level.csv"
peq = XS + "crossstudy_penalty_equivalence.csv"
ptr = XS + "crossstudy_penalty_trend.csv"
mc = XS + "crossstudy_model_comparison.csv"
for meas, M in MEASURES:
    for lev in LEVELS:
        row = {"measure": meas, "scope": "pooled", "modification": lev}
        add(f"XS{M}Penalty{lev}Est", pbl, row, "estimate", "dec2")
        add(f"XS{M}Penalty{lev}Lo", pbl, row, "ci95_lo", "dec2")
        add(f"XS{M}Penalty{lev}Hi", pbl, row, "ci95_hi", "dec2")
        add(f"XS{M}Penalty{lev}P", pbl, row, "p_two_sided", "p")
        erow = {"measure": meas, "modification": lev}
        add(f"XS{M}Penalty{lev}LoNinety", peq, erow, "ci90_lo", "dec2")
        add(f"XS{M}Penalty{lev}HiNinety", peq, erow, "ci90_hi", "dec2")
        add(f"XS{M}Penalty{lev}PTost", peq, erow, "p_tost", "p")
        for study, SK in STUDIES:
            srow = {"measure": meas, "scope": "within study", "study": study, "modification": lev}
            add(f"XS{M}Penalty{SK}{lev}Est", pbl, srow, "estimate", "dec2")
            add(f"XS{M}Penalty{SK}{lev}P", pbl, srow, "p_two_sided", "p")
    for q, Q in [("slope", "Slope"), ("curvature", "Curvature")]:
        row = {"measure": meas, "scope": "pooled", "quantity": q}
        add(f"XS{M}{Q}Est", ptr, row, "estimate", "dec2")
        add(f"XS{M}{Q}Lo", ptr, row, "ci95_lo", "dec2")
        add(f"XS{M}{Q}Hi", ptr, row, "ci95_hi", "dec2")
        add(f"XS{M}{Q}P", ptr, row, "p_two_sided", "p")
        for study, SK in STUDIES:
            srow = {"measure": meas, "scope": "within study", "study": study, "quantity": q}
            add(f"XS{M}{Q}{SK}Est", ptr, srow, "estimate", "dec2")
            add(f"XS{M}{Q}{SK}P", ptr, srow, "p_two_sided", "p")
    for model, Mo in [("severance", "Severance"), ("taint", "Taint"), ("discounting", "Discounting"),
                      ("free", "FreeShape")]:
        row = {"measure": meas, "model": model}
        add(f"XS{M}{Mo}AICWeight", mc, row, "AIC_weight", "es")
        add(f"XS{M}{Mo}BICWeight", mc, row, "BIC_weight", "es")
        if model != "severance":
            add(f"XS{M}{Mo}LRTChisq", mc, row, "lrt_chisq", "stat")
            add(f"XS{M}{Mo}LRTP", mc, row, "lrt_p", "p")
# Study 5's creativity penalty in each editing-time cell, from the exploratory
# cross-study refit of Study 5's registered model. The XS prefix marks it as
# exploratory even though it describes one study.
f = XS + "crossstudy_time_check.csv"
for t, T in HOURS:
    for lev in LEVELS:
        row = {"study": "Study 5", "measure": "creativity", "time": t, "modification": lev}
        note = "exploratory refit of Study 5 (cross-study file)"
        add(f"XSTimeCheckSFiveCreatPenalty{T}{lev}Est", f, row, "estimate", "dec2", note)
        add(f"XSTimeCheckSFiveCreatPenalty{T}{lev}P", f, row, "p_two_sided", "p", note)
# The same cells on the other two measures, whose registered interactions were not significant.
for meas, M in [("transformativeness", "Trans"), ("essence_change", "Ess")]:
    for t, T in HOURS:
        for lev in LEVELS:
            row = {"study": "Study 5", "measure": meas, "time": t, "modification": lev}
            note = "exploratory refit of Study 5 (cross-study file); uncorrected"
            add(f"XSTimeCheckSFive{M}Penalty{T}{lev}Est", f, row, "estimate", "dec2", note)
            add(f"XSTimeCheckSFive{M}Penalty{T}{lev}P", f, row, "p_two_sided", "p", note)
# Study 4's penalty in each source-time cell, from the same exploratory refit: how many of
# its cells (3 stated times x 3 levels x 3 measures) have a 95 percent interval that excludes
# zero, and the one cell the Supplement names.
derived("XSTimeCheckSFourNCells", [f], lambda f=f: count_rows(f, {"study": "Study 4"}, 27), "count",
        f"derived: rows of {f} with study=Study 4 (exploratory refit of Study 4's registered model)")
derived("XSTimeCheckSFourNExcludeZero", [f],
        lambda f=f: count_rows(f, {"study": "Study 4"}, 27,
                               lambda r: _decimal(r["ci95_lo"], f) > 0 or _decimal(r["ci95_hi"], f) < 0),
        "count",
        f"derived: of those rows, the ones whose 95 percent interval (ci95_lo to ci95_hi) excludes zero; "
        "exploratory, uncorrected")
row = {"study": "Study 4", "measure": "essence_change", "time": "100 hours", "modification": "Dramatic"}
note = "exploratory refit of Study 4 (cross-study file); uncorrected"
add("XSTimeCheckSFourEssPenaltyHundredHoursDramaticEst", f, row, "estimate", "dec2", note)
add("XSTimeCheckSFourEssPenaltyHundredHoursDramaticLo", f, row, "ci95_lo", "dec2", note)
add("XSTimeCheckSFourEssPenaltyHundredHoursDramaticHi", f, row, "ci95_hi", "dec2", note)
# The pooled penalty with one study left out (exploratory robustness check of the pooled curve).
f = XS + "crossstudy_leave_one_study_out.csv"
for lev in LEVELS:
    row = {"measure": "creativity", "left_out": "Study 4", "modification": lev}
    note = "exploratory: pooled penalty with Study 4 left out; 90 percent interval for the 0.224 bound"
    add(f"XSCreatPenaltyWithoutSFour{lev}Est", f, row, "estimate", "dec2", note)
    add(f"XSCreatPenaltyWithoutSFour{lev}LoNinety", f, row, "ci90_lo", "dec2", note)
    add(f"XSCreatPenaltyWithoutSFour{lev}HiNinety", f, row, "ci90_hi", "dec2", note)
for meas, M in [("transformativeness", "Trans"), ("essence_change", "Ess")]:
    for left, SK in [("Study 2", "STwo"), ("Study 5", "SFive")]:
        row = {"measure": meas, "left_out": left, "modification": "Slight"}
        note = f"exploratory: pooled penalty at Slight with {left} left out"
        add(f"XS{M}PenaltyWithout{SK}SlightEst", f, row, "estimate", "dec2", note)
        add(f"XS{M}PenaltyWithout{SK}SlightHiNinety", f, row, "ci90_hi", "dec2", note)
f = XS + "crossstudy_originals_reference.csv"
add("XSOriginalsSOneEst", f, {"study": "Study 1"}, "estimate", "dec2")
add("XSOriginalsSOneLo", f, {"study": "Study 1"}, "ci95_lo", "dec2")
add("XSOriginalsSOneHi", f, {"study": "Study 1"}, "ci95_hi", "dec2")
add("XSOriginalsSThreeEst", f, {"study": "Study 3"}, "estimate", "dec2")
add("XSOriginalsSThreeLo", f, {"study": "Study 3"}, "ci95_lo", "dec2")
add("XSOriginalsSThreeHi", f, {"study": "Study 3"}, "ci95_hi", "dec2")
add("XSOriginalsSThreeP", f, {"study": "Study 3"}, "p_two_sided", "p")
f = "Cross-study/explanation_shift/tables/explanation_shift_models.csv"
for meas, M in MEASURES:
    for dist, Di in [("embedding", "Emb"), ("word", "Word")]:
        row = {"dimension": meas, "distance": dist, "scope": "^pooled"}
        add(f"XS{M}Shift{Di}Est", f, row, "estimate", "dec3")
        add(f"XS{M}Shift{Di}Lo", f, row, "ci_lo", "dec3")
        add(f"XS{M}Shift{Di}Hi", f, row, "ci_hi", "dec3")
        add(f"XS{M}Shift{Di}PPerm", f, row, "p_perm", "p")
derived("XSShiftNRows", [f], lambda f=f: count_rows(f, {}, 24), "count",
        f"derived: rows of {f} (3 measures x 2 distances x pooled and 3 studies)")
derived("XSShiftNRowsTaint", [f],
        lambda f=f: count_rows(f, {}, 24, lambda r: "as taint predicts" in r["reading"]), "count",
        f"derived: rows of {f} whose reading says the AI arm's explanations moved less, "
        "as taint predicts (exploratory, uncorrected)")
derived("XSShiftNPooled", [f], lambda f=f: count_rows(f, {"scope": "^pooled"}, 6), "count",
        f"derived: rows of {f} pooled over studies (3 measures x 2 distances)")
derived("XSShiftNPooledTaintLean", [f],
        lambda f=f: count_rows(f, {"scope": "^pooled"}, 6,
                               lambda r: _decimal(r["estimate"], f"{f} estimate") < 0), "count",
        f"derived: pooled rows of {f} whose point estimate is below zero, the side taint predicts "
        "(AI arm's explanations moved less); descriptive, whatever the interval")
# Origin talk: the share of explanations that mention prompting or a machine (exploratory).
f = "Cross-study/explanation_shift/tables/explanation_shift_origin_talk.csv"
prompt = "mentions prompting or a machine (says_prompt)"
for src in SOURCES:
    for lev in LEVELS:
        row = {"scope": "^pooled", "measure": prompt, "question": "all three questions",
               "quantity": "share of explanations", "arm": src, "level": lev}
        add(f"XSOriginTalk{src}{lev}Pct", f, row, "estimate", "pct",
            "exploratory: pooled over Studies 2, 4 and 5 with equal weight, all three questions")
row = {"scope": "^pooled", "measure": prompt, "question": "all three questions",
       "quantity": "difference in the change, AI minus Human"}
note = ("exploratory: AI minus Human in the None-to-Dramatic change in share, pooled, all three "
        "questions; 95 percent interval from 2,000 participant resamples")
add("XSOriginTalkChangeDiffPct", f, row, "estimate", "pct", note)
add("XSOriginTalkChangeDiffLoPct", f, row, "ci_lo", "pct", note)
add("XSOriginTalkChangeDiffHiPct", f, row, "ci_hi", "pct", note)
note_pp = ("exploratory: AI minus Human in the None-to-Dramatic change in share, pooled, all three "
           "questions, in percentage points (a difference between two shares); 95 percent interval from "
           "2,000 participant resamples")
add("XSOriginTalkChangeDiffPts", f, row, "estimate", "pp", note_pp)
add("XSOriginTalkChangeDiffLoPts", f, row, "ci_lo", "pp", note_pp)
add("XSOriginTalkChangeDiffHiPts", f, row, "ci_hi", "pp", note_pp)
for src in SOURCES:
    for lev in ["None", "Dramatic"]:
        row = {"scope": "Study 2", "measure": prompt, "question": "creativity",
               "quantity": "share of explanations", "arm": src, "level": lev}
        add(f"XSOriginTalkSTwoCreat{src}{lev}Pct", f, row, "estimate", "pct",
            "exploratory: Study 2, creativity explanations")
row = {"scope": "Study 2", "measure": prompt, "question": "creativity",
       "quantity": "difference in the change, AI minus Human"}
note = ("exploratory: Study 2 creativity explanations, AI minus Human in the None-to-Dramatic "
        "change in share; 95 percent interval from 2,000 participant resamples; uncorrected")
add("XSOriginTalkSTwoCreatChangeDiffPct", f, row, "estimate", "pct", note)
add("XSOriginTalkSTwoCreatChangeDiffLoPct", f, row, "ci_lo", "pct", note)
add("XSOriginTalkSTwoCreatChangeDiffHiPct", f, row, "ci_hi", "pct", note)
note_pp = ("exploratory: Study 2 creativity explanations, AI minus Human in the None-to-Dramatic "
           "change in share, in percentage points (a difference between two shares); 95 percent interval "
           "from 2,000 participant resamples; uncorrected")
add("XSOriginTalkSTwoCreatChangeDiffPts", f, row, "estimate", "pp", note_pp)
add("XSOriginTalkSTwoCreatChangeDiffLoPts", f, row, "ci_lo", "pp", note_pp)
add("XSOriginTalkSTwoCreatChangeDiffHiPts", f, row, "ci_hi", "pp", note_pp)
f = "Cross-study/structural_topics/tables/structural_topics_label_effects_by_level.csv"
for lev in LEVELS:
    row = {"question": "creativity", "topic": "7", "level": lev}
    add(f"XSTopicCreatSeven{lev}Est", f, row, "estimate", "dec3")
    add(f"XSTopicCreatSeven{lev}Lo", f, row, "ci95_lo", "dec3")
    add(f"XSTopicCreatSeven{lev}Hi", f, row, "ci95_hi", "dec3")
f = "Cross-study/structural_topics/tables/structural_topics_label_effects_averaged_and_change.csv"
row = {"question": "creativity", "topic": "7", "quantity": "Dramatic minus None"}
add("XSTopicCreatSevenChangeEst", f, row, "estimate", "dec3")
add("XSTopicCreatSevenChangeLo", f, row, "ci95_lo", "dec3")
add("XSTopicCreatSevenChangeHi", f, row, "ci95_hi", "dec3")
f = "Cross-study/image_check/tables/image_check_check3_ties.csv"
for meas_name, Mn in [("DINOv2", "DINO"), ("CLIP", "CLIP"), ("colour", "Colour")]:
    pre = "longer side 512" if meas_name == "colour" else "whole image"
    add(f"XSImageCheckThree{Mn}", f, {"measure": meas_name, "preprocessing": pre, "artwork": "1Figure",
                                       "version": "Slight"}, "count_own_original_first", "count")
# Check 2: artworks (of 10) whose Slight version is closer to the original than the Dramatic
# version. The count is stored on every row of a measure; the 1Figure row is read.
f = "Cross-study/image_check/tables/image_check_check2_steps.csv"
for meas_name, Mn in [("DINOv2", "DINO"), ("CLIP", "CLIP"), ("colour", "Colour")]:
    pre = "longer side 512" if meas_name == "colour" else "whole image"
    add(f"XSImageCheckTwo{Mn}", f, {"measure": meas_name, "preprocessing": pre, "artwork": "1Figure"},
        "count_slight_below_dramatic", "count", "exploratory image check 2")
f = "Cross-study/image_check/tables/image_check_stimuli.csv"


def _slight_reframed(rel: str = f) -> Decimal:
    """Artworks whose Slight image differs from the original in pixel width or height."""
    originals = rows_where(rel, {"version": "original"})
    slights = rows_where(rel, {"version": "Slight"})
    if len(originals) != 10 or len(slights) != 10:
        raise SourceError(f"{rel}: expected 10 originals and 10 Slight images")
    size = {r["artwork"]: (_decimal(r["pixel_width"], rel), _decimal(r["pixel_height"], rel))
            for r in originals}
    return Decimal(sum(1 for r in slights
                       if (_decimal(r["pixel_width"], rel), _decimal(r["pixel_height"], rel))
                       != size[r["artwork"]]))


derived("XSImageCheckSlightReframedN", [f], _slight_reframed, "count",
        f"derived: artworks in {f} whose Slight image's pixel width or height differs from its "
        "original's, that is, Slight edits that also cropped or resized the picture")

# Counts of registered verdicts across studies, made for the Results from the verdict
# columns of each study's tables (each study's own verdicts are unchanged).
s2h = "Study 2/tables/study2_hypothesis_readings.csv"
s4h = "Study 4/tables/study4_hypotheses.csv"
derived("NHTwoTestsSTwoSFour", [s2h, s4h],
        lambda: (count_rows(s2h, {"hypothesis": "H2"}, 4, lambda r: r["measure"] != "all three measures")
                 + count_rows(s4h, {"hypothesis": "H2"}, 4, lambda r: r["measure"] != "all three measures")),
        "count",
        f"derived: H2 rows for single measures in {s2h} and {s4h} (the registered study-by-measure "
        "tests of the label's average effect on second works)")
derived("NHTwoPassSTwoSFour", [s2h, s4h],
        lambda: (count_rows(s2h, {"hypothesis": "H2"}, 4,
                            lambda r: r["measure"] != "all three measures"
                            and r["reading"].startswith("small or absent"))
                 + count_rows(s4h, {"hypothesis": "H2"}, 4,
                              lambda r: r["measure"] != "all three measures"
                              and r["verdict"] == "inside the bound")),
        "count",
        f"derived: of those rows, the ones whose registered verdict says the effect lies inside "
        f"plus or minus 0.224 ('small or absent' in {s2h}, 'inside the bound' in {s4h})")
s2c = "Study 2/tables/study2_confirmatory_family.csv"
s4c = "Study 4/tables/study4_confirmatory_family.csv"
s4l = "Study 4/tables/study4_secondary_label_by_modification.csv"
s5e = "Study 5/tables/study5_equivalence_source.csv"
derived("NSourceEquivTests", [s2c, s4c, s4l, s5e],
        lambda: (count_rows(s2c, {"test": "3"}, 3) + count_rows(s4c, {"test_number": "3"}, 3)
                 + count_rows(s4l, {}, 9) + count_rows(s5e, {}, 9)),
        "count",
        "derived: every registered equivalence test of the label's effect on second works: "
        f"test 3 in {s2c} (3), test 3 in {s4c} (3), the rows of {s4l} (9) and of {s5e} (9)")
derived("NSourceEquivPass", [s2c, s4c, s4l, s5e],
        lambda: (count_rows(s2c, {"test": "3"}, 3, lambda r: _flag(s2c, r, "holm_significant"))
                 + count_rows(s4c, {"test_number": "3"}, 3, lambda r: _flag(s4c, r, "holm_significant"))
                 + count_rows(s4l, {}, 9, lambda r: _flag(s4l, r, "inside_bound"))
                 + count_rows(s5e, {}, 9, lambda r: _flag(s5e, r, "equivalent"))),
        "count",
        "derived: of those tests, the ones that showed the effect inside plus or minus 0.224 by "
        "their registered rule: holm_significant TRUE for the two confirmatory sets, inside_bound "
        "TRUE in Study 4's secondary rows, equivalent TRUE in Study 5's")

# ---- Numbers printed in the Methods ----------------------------------------
# The size of each study's registered confirmatory set (Study 5's is SFiveNConfirmatory,
# above), the Study 4 count that the CogSci 2025 paper reported as its sample, and the two
# kinds of missing rating in Study 3.
m1 = "Study 1/tables/study1_confirmatory_family.csv"
add("SOneNConfirmatory", m1, {"hypothesis": "H2"}, "family_size", "count",
    "the number of tests in Study 1's registered confirmatory set, corrected together by Holm")
m2 = "Study 2/tables/study2_confirmatory_family.csv"
derived("STwoNConfirmatory", [m2], lambda: count_rows(m2, {}, 12), "count",
        f"derived: rows of {m2}, the registered confirmatory tests corrected together by Holm")
m3 = "Study 3/tables/study3_lmm_ftests.csv"
derived("SThreeNConfirmatory", [m3], lambda: count_rows(m3, {}, 6), "count",
        f"derived: rows of {m3}, the registered confirmatory F tests corrected together by Holm")
m4 = "Study 4/tables/study4_confirmatory_family.csv"
derived("SFourNConfirmatory", [m4], lambda: count_rows(m4, {}, 15), "count",
        f"derived: rows of {m4}, the registered confirmatory tests corrected together by Holm")
add("SFourNBeforeValidity", "Study 4/tables/study4_exclusion_flow.csv",
    {"step": "^wrong answers to What does 8+7 equal?"}, "n", "count",
    "records left before the registered validity rule; the CogSci 2025 paper (p. 1670) "
    "reported this count as its Study 2 sample")
m3s = "Study 3/tables/study3_sample_checks.csv"
add("SThreeNLackingOneRating", m3s, {"quantity": "participants with 17 recorded ratings"},
    "observed", "count", "Study 3 participants with one of their 18 ratings not recorded")
add("SThreeNAbsentCode", m3s, {"quantity": "1FigureEff answers with an absent code"},
    "observed", "count",
    "Study 3 ratings whose answer code the final survey does not offer, treated as missing")

# ==== BEGIN sample description (Cross-study/sample_description) ===============
# Age and gender of each study's analyzed sample, and the number of different
# people across the five analyzed samples, from the descriptive step in
# Cross-study/sample_description/. It reads each study's analyzed sample from
# the long data file that study's real run wrote and applies no exclusion of
# its own. Gender groups: women are the answer Female, men the answer Male, and
# GenderOther is every other answer (Other, Prefer not to say, or none); the
# step's gender table keeps each answer separately.
# Study 1's age macros (SOneAgeMean, SOneAgeSD, SOneAgeMin, SOneAgeMax) and
# SOneNGenderOther are read above from Study 1's own tables, so they are not
# defined again here. The step stops unless its Study 1 numbers equal those
# tables exactly, and unless study1_demo_gender.csv holds no answer but Female,
# Male and Other, so the existing SOneNGenderOther is the whole other group.
SD = "Cross-study/sample_description/tables/"
f = SD + "sample_description_by_study.csv"
for S, label in [("SOne", "Study 1"), ("STwo", "Study 2"), ("SThree", "Study 3"),
                 ("SFour", "Study 4"), ("SFive", "Study 5")]:
    row = {"study": label}
    if S != "SOne":
        add(f"{S}AgeMean", f, row, "age_mean", "dec2", "descriptive: mean age of the analyzed sample")
        add(f"{S}AgeSD", f, row, "age_sd", "dec2", "descriptive: standard deviation of age")
        add(f"{S}AgeMin", f, row, "age_min", "count", "descriptive: youngest age")
        add(f"{S}AgeMax", f, row, "age_max", "count", "descriptive: oldest age")
    add(f"{S}NWomen", f, row, "n_women", "count", "descriptive: gender answer Female")
    add(f"{S}NMen", f, row, "n_men", "count", "descriptive: gender answer Male")
    if S != "SOne":
        add(f"{S}NGenderOther", f, row, "n_gender_other", "count",
            "descriptive: every other gender answer (Other, Prefer not to say, or none)")
f = SD + "sample_description_overlap.csv"
add("NPeople", f, {"quantity": "different people analyzed"}, "n", "count",
    "descriptive: different people across the five analyzed samples, linked by the "
    "subject-pool participant code")
add("NPeopleRepeat", f, {"quantity": "people analyzed in two or more studies"}, "n", "count",
    "descriptive: people analyzed in more than one study; the same table counts those "
    "analyzed in three or more and in each pair of studies")
# Percentage of each analyzed sample whose gender answer was Female, for the Methods.
for S, label in [("SOne", "Study 1"), ("STwo", "Study 2"), ("SThree", "Study 3"),
                 ("SFour", "Study 4"), ("SFive", "Study 5")]:
    f = SD + "sample_description_by_study.csv"
    derived(f"{S}PctFemale", [f],
            lambda f=f, label=label: Decimal(read_cell(f, {"study": label}, "n_women"))
            / Decimal(read_cell(f, {"study": label}, "n")), "pct",
            f"derived: n_women divided by n in the {label} row of {f} "
            "(descriptive: share of the analyzed sample whose gender answer was Female)")
# ==== END sample description =================================================

# Derived: the total analyzed sample, the sum of the five analyzed-sample cells
# above (Studies 1 to 5), printed as a count.
DERIVED = [("NTotal", ["SOneN", "STwoN", "SThreeN", "SFourN", "SFiveN"], "count",
            "sum of the five analyzed samples: SOneN + STwoN + SThreeN + SFourN + SFiveN")]


# --------------------------------------------------------------------------
# Build and write
# --------------------------------------------------------------------------

def build() -> list[dict]:
    seen: set[str] = set()
    out = []
    for spec in SPECS:
        name = spec["macro"]
        if not re.fullmatch(r"[A-Za-z]+", name):
            raise SourceError(f"macro name '{name}' must contain letters only")
        if name in seen:
            raise SourceError(f"macro name '{name}' is defined twice")
        seen.add(name)
        if "compute" in spec:
            for rel in spec["sources"]:
                _table(rel)
            value = Decimal(spec["compute"]())
            out.append({"macro": name, "file": "(derived)", "row": {}, "column": "",
                        "fmt": spec["fmt"], "note": spec["note"], "stored": str(value),
                        "printed": FORMATS[spec["fmt"]](value), "where": spec["note"],
                        "sha256": ";".join(_CHECKSUMS[rel] for rel in spec["sources"])})
            continue
        where = f"{spec['file']} [{_describe(spec['row'])}] column {spec['column']}"
        cell = read_cell(spec["file"], spec["row"], spec["column"])
        printed = FORMATS[spec["fmt"]](_decimal(cell, where))
        out.append({**spec, "stored": cell, "printed": printed, "where": where,
                    "sha256": _CHECKSUMS[spec["file"]]})
    by_name = {o["macro"]: o for o in out}
    for name, parts, fmt, note in DERIVED:
        if name in seen:
            raise SourceError(f"macro name '{name}' is defined twice")
        total = sum(_decimal(by_name[p]["stored"], by_name[p]["where"]) for p in parts)
        out.append({"macro": name, "file": "(derived)", "row": {}, "column": "", "fmt": fmt,
                    "note": note, "stored": str(total), "printed": FORMATS[fmt](total),
                    "where": note, "sha256": ""})
    return out


def write(results: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "% numbers.tex: written by tools/make_numbers.py. Do not edit by hand;",
        "% change the pipeline or the script and run it again.",
        "% Each macro prints one number from a pipeline table, rounded by the rule",
        "% stated in the script. The comment after it names the table (relative to",
        "% Analysis/R Analysis Pipeline), the row and the column, then any note on",
        "% the number's status. p-value macros carry their sign: write $p$~\\Macro.",
        "",
    ]
    section = None
    for r in results:
        prefix = re.match(r"(SOne|STwo|SThree|SFour|SFive|XS|Source|N)", r["macro"]).group(1)
        if prefix != section:
            section = prefix
            lines.append(f"% ---- {section} " + "-" * 60)
        comment = r["where"]
        if r["note"] and r["note"] != r["where"]:
            comment += f"; {r['note']}"
        lines.append(f"\\newcommand{{\\{r['macro']}}}{{{r['printed']}}}% {comment}")
    tmp_tex = OUT_TEX.with_suffix(".tex.tmp")
    tmp_tex.write_text("\n".join(lines) + "\n", encoding="utf-8")

    tmp_csv = OUT_CSV.with_suffix(".csv.tmp")
    with tmp_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["macro", "printed", "stored_value", "format", "file", "row", "column",
                    "file_sha256", "note"])
        for r in results:
            w.writerow([r["macro"], r["printed"], r["stored"], r["fmt"], r["file"],
                        _describe(r["row"]) if r["file"] != "(derived)" else "",
                        r["column"], r["sha256"], r["note"]])
    tmp_tex.replace(OUT_TEX)
    tmp_csv.replace(OUT_CSV)


def main() -> int:
    if not PIPELINE.is_dir():
        print(f"make_numbers.py: pipeline folder not found: {PIPELINE}\n"
              "Set PIPELINE_DIR to the 'R Analysis Pipeline' folder.", file=sys.stderr)
        return 1
    try:
        results = build()
    except SourceError as exc:
        print(f"make_numbers.py stopped: {exc}\nNothing was written.", file=sys.stderr)
        return 1
    write(results)
    print(f"Wrote {len(results)} macros from {len(_CHECKSUMS)} tables to "
          f"{OUT_TEX.relative_to(PAPER)} and {OUT_CSV.relative_to(PAPER)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
