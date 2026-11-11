#!/usr/bin/env python3
"""Draw the paper's main-text figures from the five studies' deposited long data files.

What this script does
---------------------
It reads each study's trial-level file (``Study N/studyN_long_with_text.csv``),
averages each participant's ratings within each condition, and draws seven main-text
figures, one per claim, and three Supplementary figures, each as a PDF and a PNG in
``output/``. Main-text file names carry the figure numbers; Supplementary ones start
``figS_``. Figures 4 and 7 read the text battery's table of what the written
explanations mentioned (``Cross-study/text_battery/tables/text_battery_prevalence.csv``);
the Supplementary figures read ``Cross-study/image_grounding/`` and
``Cross-study/label_from_meaning/``:

* ``fig1_stimuli``: three of the ten originals, each beside its Slight and
  Dramatic versions.
* ``fig2_study1``: Study 1, creativity and effort of the same images under the
  two labels.
* ``fig3_study2``: Study 2, creativity and effort of the originals at each
  stated time, under the two labels.
* ``fig4_explanations_originals``: Studies 1 and 2, the share of written
  explanations of each rating that mention prompting or a machine, under
  each label (bars with 95 percent intervals).
* ``fig5_secondary``: Studies 3, 4 and 5, ratings of the secondary works at
  each edit level, under the two labels: one row per rating (A creativity,
  B transformativeness, C essence change), one column per study.
* ``fig6_hours_secondary``: creativity of the secondary works by stated hours:
  Study 4, hours stated for making the original; Study 5, hours stated for
  making the secondary work.
* ``fig7_explanations_secondary``: as Figure 4, for the secondary works of
  Studies 3, 4 and 5, on the same 0 to 60 percent scale.
* ``figS_picture_match_originals`` (Supplementary): Studies 1 and 2, how often
  CLIP picked out the picture an explanation was written about, from the ten
  originals, under each label (chance is 1 in 10).
* ``figS_meaning_originals`` (Supplementary): Studies 1 and 2, for each rating,
  how often a model tells apart a pair of participants, one from each label,
  from their ratings, from what they wrote, and from what they wrote leaving out
  any mention of prompting or a machine (the AUC as a percentage; 50 is
  guessing). The bars start at 50.
* ``figS_meaning_secondary`` (Supplementary): as ``figS_meaning_originals``, for
  the three ratings of the secondary works in Studies 3 to 5. The grounding of
  secondary works gets no figure: the labels did not differ there.

The bar figures print no value above a bar; ``output/figure_values.csv`` holds
every plotted value.

The two labels are named on every figure by what they said about the original:
"Human-generated original" (Alex made it with design and sketching tools) and
"AI-generated original" (he made it by prompting an AI system). Figures 2, 3, 5 and 6
put the condition on the horizontal axis and the rating (1 to 5) on the
vertical axis. Each violin shows how the participants' mean ratings spread,
the small dots are those participants, and the large marker with its bar is the
group mean with its 95 percent confidence interval (mean plus or minus t times
the standard error of the participants' means). These are descriptive summaries
of the data; the paper reports the registered models' estimates in its text.
For each group mean that the pipeline's model tables also give, the script
writes the model's estimate beside it in ``output/figure_values.csv`` so the two
can be compared.

It also writes ``output/figure_values.csv``: every plotted group mean with its
figure, panel, study, rating, label, condition, number of participants,
standard deviation and interval. It writes no participant identifier anywhere.

Study numbers
-------------
The pipeline's folders use the order in which the studies were run. The paper
numbers them in the order it presents them, which swaps two: the pipeline's
Study 2 is the paper's Study 3, and its Study 3 is the paper's Study 2. This
script reads the pipeline's folders and prints the paper's numbers on every
figure and in ``figure_values.csv`` (``PAPER_STUDY`` below).

Which ratings are used
----------------------
The ratings the registered analyses used: rows with a rating, and, in Studies 4
and 5, only items with five answer options (the two six-option
transformativeness items are left out, as the registrations specify).

How to run
----------
From anywhere:

    python3 make_paper_figures.py

Paths are found from this file's location. It needs Python 3.12 with
matplotlib, numpy and Pillow at the versions in ``requirements.txt``. The
jitter of the dots uses a fixed seed and the files carry no creation date, so
two runs on the same data write identical files.

When it stops
-------------
It stops, and writes nothing, if a data file or a stimulus image is missing, a
stimulus image's checksum differs from ``image_check/stimuli/stimuli_manifest.csv``,
a condition has no ratings, or a study's number of participants differs from
its analyzed N.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patches  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from PIL import Image  # noqa: E402

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent.parent  # paper_figures -> Cross-study -> R Analysis Pipeline
OUT = Path(os.environ.get("PAPER_FIGURES_OUT", HERE / "output"))
STIMULI = PIPELINE / "Cross-study" / "image_check" / "stimuli"

PAPER_STUDY = {1: 1, 2: 3, 3: 2, 4: 4, 5: 5}  # pipeline number -> paper number
ANALYZED_N = {1: 111, 2: 235, 3: 85, 4: 117, 5: 197}  # by pipeline number; Study 5 less the 26 who had done an earlier study

HUMAN, AI = "Human", "AI"
COLOR = {HUMAN: "#1a1a1a", AI: "#1a1a1a"}  # marker and line color: near-black for both (grayscale)
VIOLIN_FACE = {HUMAN: "#9a9a9a", AI: "white"}  # Human: gray fill; AI: white fill
VIOLIN_EDGE = {HUMAN: "#6e6e6e", AI: "#6e6e6e"}
DOT = {HUMAN: "#4d4d4d", AI: "#9a9a9a"}  # participant dots: darker for Human, lighter for AI
LINESTYLE = {HUMAN: "-", AI: (0, (3, 2))}  # Human solid, AI dashed
MARKER = {HUMAN: "o", AI: "o"}  # same shape; the labels differ by fill (black vs white)
LABEL_TEXT = {HUMAN: "Human-generated original", AI: "AI-generated original"}  # wording chosen by K. J. Holyoak, 1 Nov 2026
LEVELS = ["None", "Slight", "Dramatic"]
LEVEL_TEXT = {"None": "None\n(unchanged)", "Slight": "Slight\nedit", "Dramatic": "Dramatic\nedit"}
MEASURE_TEXT = {"creativity": "Creativity", "effort": "Effort",
                "transformativeness": "Transformativeness", "essence_change": "Essence change"}
EXAMPLES = ["1Figure", "3Figure", "5NonFigure"]  # chosen by the lead author, 28 Oct 2026

MM = 1 / 25.4
WIDTH = 170 * MM  # full page width for Cognitive Science (Wiley)
SEED = 20261027

plt.rcParams.update({
    "font.family": "Times New Roman", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8.5, "mathtext.fontset": "stix",
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "pdf.fonttype": 42,
    "svg.hashsalt": "paper-figures",
})


def stop(msg: str) -> None:
    raise SystemExit(f"make_paper_figures.py stopped: {msg}")


def read_long(study: int) -> list[dict]:
    path = PIPELINE / f"Study {study}" / f"study{study}_long_with_text.csv"
    if not path.exists():
        stop(f"missing {path.relative_to(PIPELINE)}")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    keep = []
    for r in rows:
        if r.get("rating", "") == "":
            continue
        if "k_points" in r and r["k_points"] not in ("", "5"):
            continue
        r["rating"] = float(r["rating"])
        keep.append(r)
    n = len({r["id"] for r in keep})
    if n != ANALYZED_N[study]:
        stop(f"pipeline Study {study} has {n} participants, expected {ANALYZED_N[study]}")
    return keep


def participant_means(rows, keys, measure_col="dimension", measure=None):
    """Mean rating per participant within each combination of `keys`."""
    acc = defaultdict(list)
    for r in rows:
        if measure is not None and r[measure_col] != measure:
            continue
        acc[(r["id"],) + tuple(r[k] for k in keys)].append(r["rating"])
    cells = defaultdict(list)
    for k, v in acc.items():
        cells[k[1:]].append(sum(v) / len(v))
    return cells  # condition tuple -> list of participant means


def summarize(values):
    a = np.asarray(values, dtype=float)
    n = len(a)
    if n < 2:
        stop("a condition has fewer than two participants")
    m, sd = float(a.mean()), float(a.std(ddof=1))
    t = T975.get(n - 1) or t_quantile(n - 1)
    half = t * sd / math.sqrt(n)
    return n, m, sd, m - half, m + half


def t_quantile(df: int) -> float:
    """97.5th percentile of Student's t (Cornish-Fisher expansion; error < 1e-4 for df >= 20)."""
    z = 1.959963984540054
    g1 = (z ** 3 + z) / 4
    g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96
    g3 = (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / 384
    return z + g1 / df + g2 / df ** 2 + g3 / df ** 3


T975 = {}  # filled lazily by t_quantile; kept for clarity

VALUES: list[dict] = []
RNG = np.random.default_rng(SEED)


def paired_violins(ax, cells, conditions, labels_key_order, fig, panel, study, measure, cond_name, connect=False):
    """Draw Human and AI violins side by side at each condition."""
    offset = {HUMAN: -0.19, AI: 0.19}
    means = {HUMAN: [], AI: []}
    for i, cond in enumerate(conditions):
        for lab in (HUMAN, AI):
            key = labels_key_order(lab, cond)
            vals = cells.get(key)
            if not vals:
                stop(f"no ratings for {fig} {panel} {lab} {cond}")
            x = i + offset[lab]
            vp = ax.violinplot([vals], positions=[x], widths=0.34, showextrema=False, bw_method=0.35)
            for b in vp["bodies"]:
                b.set_facecolor(VIOLIN_FACE[lab]); b.set_alpha(0.35 if lab == HUMAN else 1.0)
                b.set_edgecolor(VIOLIN_EDGE[lab]); b.set_linewidth(0.6)
            jit = RNG.uniform(-0.07, 0.07, len(vals))
            ax.scatter(x + jit, vals, s=2.5, color=DOT[lab], alpha=0.6, linewidths=0, zorder=2)
            n, m, sd, lo, hi = summarize(vals)
            ax.plot([x, x], [lo, hi], color="black", lw=1.0, zorder=4)
            face = COLOR[lab] if lab == HUMAN else "white"
            ax.scatter([x], [m], s=26, marker=MARKER[lab], facecolor=face, edgecolor=COLOR[lab] if lab == HUMAN else COLOR[lab],
                       linewidths=1.2, zorder=5)
            means[lab].append((x, m))
            VALUES.append({"figure": fig, "panel": panel, "study_paper": study, "rating": measure,
                           "label": lab, cond_name: cond, "n_participants": n, "mean": round(m, 4),
                           "sd": round(sd, 4), "ci95_low": round(lo, 4), "ci95_high": round(hi, 4)})
    if connect:
        for lab in (HUMAN, AI):
            xs, ms = zip(*means[lab])
            ax.plot(xs, ms, color=COLOR[lab], lw=0.9, ls=LINESTYLE[lab], zorder=3)
    ax.set_xticks(range(len(conditions)))
    ax.set_xlim(-0.6, len(conditions) - 0.4)
    ax.set_ylim(0.8, 5.2)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.grid(axis="y", color="0.9", lw=0.5, zorder=0)
    ax.set_axisbelow(True)


def legend_handles():
    return [Line2D([0], [0], marker=MARKER[HUMAN], color=COLOR[HUMAN], ls=LINESTYLE[HUMAN], lw=0.9,
                   markerfacecolor=COLOR[HUMAN], markeredgecolor=COLOR[HUMAN], markersize=5.5,
                   label=LABEL_TEXT[HUMAN]),
            Line2D([0], [0], marker=MARKER[AI], color=COLOR[AI], ls=LINESTYLE[AI], lw=0.9,
                   markerfacecolor="white", markeredgecolor=COLOR[AI], markeredgewidth=1.2, markersize=5.5,
                   label=LABEL_TEXT[AI])]


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf", metadata={"CreationDate": None, "ModDate": None, "Creator": None, "Producer": None})
    fig.savefig(OUT / f"{name}.png", dpi=400, metadata={"Software": None})
    plt.close(fig)


def add_legend(fig, y=1.0, ncol=2):
    fig.legend(handles=legend_handles(), loc="upper center", ncol=ncol, frameon=False, bbox_to_anchor=(0.5, y),
               handlelength=2.6, handletextpad=0.4, columnspacing=1.6)


# ---------------------------------------------------------------- figures

def fig_stimuli():
    manifest = {}
    with (STIMULI / "stimuli_manifest.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            manifest[r["file"]] = r["file_sha256"]
    images = []
    for art in EXAMPLES:
        row = []
        for ver in ["original", "slight", "dramatic"]:
            files = sorted(STIMULI.glob(f"{art}_{ver}.*"))
            if len(files) != 1:
                stop(f"expected one image for {art} {ver}")
            f = files[0]
            if hashlib.sha256(f.read_bytes()).hexdigest() != manifest.get(f.name):
                stop(f"checksum of {f.name} differs from the manifest")
            row.append(Image.open(f).convert("RGB"))
        images.append(row)
    # Each row is as tall as its tallest image needs at the column width, so square and wide
    # sets sit together without cropping; an image shorter than its row is centered in it.
    ratios = [max(im.height / im.width for im in row) for row in images]
    gap, top_space = 1.5 * MM, 7 * MM
    col_w = (WIDTH - 2 * gap) / 3
    height = sum(ratios) * col_w + gap * (len(images) - 1) + top_space
    fig, axes = plt.subplots(len(images), 3, figsize=(WIDTH, height),
                             gridspec_kw={"height_ratios": ratios})
    for i, row in enumerate(images):
        for j, im in enumerate(row):
            ax = axes[i, j]
            ax.imshow(im)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
    fig.subplots_adjust(left=0, right=1, top=1 - top_space / height, bottom=0,
                        wspace=gap / col_w, hspace=gap / (col_w * sum(ratios) / len(ratios)))
    for j, title in enumerate(["Original", "Slight edit", "Dramatic edit"]):
        box = axes[0, j].get_position()  # same height for every column title, whatever the image's shape
        fig.text((box.x0 + box.x1) / 2, 1 - top_space / height / 2, title, ha="center", va="center",
                 fontsize=10)
    save(fig, "fig1_stimuli")


def fig_study1(rows):
    cells = participant_means(rows, ["Type", "dimension"])
    fig, ax = plt.subplots(figsize=(WIDTH * 0.55, 80 * MM))
    paired_violins(ax, cells, ["creativity", "effort"], lambda lab, c: (lab, c), "fig2_study1", "", 1, "", "rating_asked")
    for v in VALUES:
        if v["figure"] == "fig2_study1":
            v["rating"] = v.pop("rating_asked")
    ax.set_xticklabels(["Creativity", "Effort"])
    ax.set_ylabel("Mean rating (1 to 5)")
    add_legend(fig, 1.01, ncol=1)
    fig.subplots_adjust(left=0.14, right=0.98, top=0.80, bottom=0.11)
    save(fig, "fig2_study1")


def fig_study2(rows):
    times = ["under 1 hour", "10 hours", "100 hours"]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 72 * MM), sharey=True)
    for ax, measure, letter in zip(axes, ["creativity", "effort"], "AB"):
        cells = participant_means(rows, ["Type", "time"], measure=measure)
        paired_violins(ax, cells, times, lambda lab, c: (lab, c), "fig3_study2", letter, 2, measure,
                       "stated_hours", connect=True)
        ax.set_xticklabels(["Under 1 hour", "10 hours", "100 hours"])
        ax.set_xlabel("Stated hours to make original work")
        ax.set_title(MEASURE_TEXT[measure])
        ax.text(-0.16, 1.06, letter, transform=ax.transAxes, fontweight="bold", fontsize=10)
    axes[0].set_ylabel("Mean rating (1 to 5)")
    add_legend(fig, 1.01)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.80, bottom=0.17, wspace=0.12)
    save(fig, "fig3_study2")


def second_panels(data, measure, axes, fig_name, letters, show_xlabel=True):
    for ax, (pipe, rows, labcol), letter in zip(axes, data, letters):
        cells = participant_means(rows, [labcol, "modification"], measure=measure)
        paired_violins(ax, cells, LEVELS, lambda lab, c: (lab, c), fig_name, letter, PAPER_STUDY[pipe], measure,
                       "edit_level", connect=True)
        ax.set_xticklabels([LEVEL_TEXT[l] for l in LEVELS])
        ax.text(-0.2, 1.06, letter, transform=ax.transAxes, fontweight="bold", fontsize=10)


def fig_secondary(data):
    """One row per rating (A creativity, B transformativeness, C essence change), one column per study."""
    rows_spec = [("creativity", "A"), ("transformativeness", "B"), ("essence_change", "C")]
    fig, axes = plt.subplots(3, 3, figsize=(WIDTH, 200 * MM), sharey=True)
    for r, (measure, letter) in enumerate(rows_spec):
        for c, (pipe, rows, labcol) in enumerate(data):
            ax = axes[r, c]
            cells = participant_means(rows, [labcol, "modification"], measure=measure)
            paired_violins(ax, cells, LEVELS, lambda lab, cond: (lab, cond), "fig5_secondary", letter,
                           PAPER_STUDY[pipe], measure, "edit_level", connect=True)
            ax.set_xticklabels([LEVEL_TEXT[l] for l in LEVELS] if r == 2 else [])
            if r == 0:
                ax.set_title(f"Study {PAPER_STUDY[pipe]}")
        axes[r, 0].set_ylabel(f"{MEASURE_TEXT[measure]} (1 to 5)")
        axes[r, 0].text(-0.30, 1.04, letter, transform=axes[r, 0].transAxes, fontweight="bold", fontsize=11)
    axes[2, 1].set_xlabel("Edit level of the secondary work")
    add_legend(fig, 1.0)
    fig.subplots_adjust(left=0.10, right=0.99, top=0.92, bottom=0.08, wspace=0.12, hspace=0.18)
    save(fig, "fig5_secondary")


def fig_hours_secondary(s4, s5):
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH * 0.8, 76 * MM), sharey=True)
    specs = [(axes[0], s4, "label", "source_time", 4, "Stated hours to make original work", "A"),
             (axes[1], s5, "source", "editing_time", 5, "Stated hours to make secondary work", "B")]
    times = ["less than 1 hour", "10 hours", "100 hours"]
    for ax, rows, labcol, timecol, study, xlabel, letter in specs:
        cells = participant_means(rows, [labcol, timecol], measure="creativity")
        paired_violins(ax, cells, times, lambda lab, c: (lab, c), "fig6_hours_secondary", letter, study, "creativity",
                       "stated_hours", connect=True)
        ax.set_xticklabels(["Under 1 hour", "10 hours", "100 hours"])
        ax.set_xlabel(xlabel)
        ax.set_title(f"Study {study}")
        ax.text(-0.2, 1.06, letter, transform=ax.transAxes, fontweight="bold", fontsize=10)
    axes[0].set_ylabel("Mean creativity rating (1 to 5)")
    add_legend(fig, 1.01)
    fig.subplots_adjust(left=0.10, right=0.99, top=0.80, bottom=0.18, wspace=0.12)
    save(fig, "fig6_hours_secondary")


def read_explanation_shares():
    """Share of explanations flagged as mentioning prompting or a machine, by study, rating and label,
    over all edit levels, with the text battery's participant-resampled 95 percent interval."""
    path = PIPELINE / "Cross-study" / "text_battery" / "tables" / "text_battery_prevalence.csv"
    if not path.exists():
        stop(f"missing {path.relative_to(PIPELINE)}")
    out = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["flag"] == "says_prompt" and r["level"] == "all levels" and r["label"] in (HUMAN, AI):
                out[(int(r["study_paper"]), r["measure"], r["label"])] = (
                    100 * float(r["estimate"]), 100 * float(r["ci_lo"]), 100 * float(r["ci_hi"]),
                    int(r["n_participants"]), int(r["n_explanations"]))
    return out


BAR_FACE = {HUMAN: "#9a9a9a", AI: "white"}  # as the violins: Human gray, AI white


def explanation_bars(fig_name, studies, measures, width_frac):
    """One panel per study; in each, a pair of bars (Human, AI) per rating, on one 0-60 scale."""
    shares = read_explanation_shares()
    fig, axes = plt.subplots(1, len(studies), figsize=(WIDTH * width_frac, 66 * MM), sharey=True)
    for ax, study, letter in zip(axes, studies, "ABC"):
        for i, measure in enumerate(measures):
            for lab, dx in ((HUMAN, -0.19), (AI, 0.19)):
                key = (study, measure, lab)
                if key not in shares:
                    stop(f"no explanation share for Study {study} {measure} {lab}")
                m, lo, hi, n_p, n_e = shares[key]
                ax.bar(i + dx, m, width=0.36, color=BAR_FACE[lab], edgecolor="#4d4d4d", linewidth=0.7, zorder=3)
                ax.plot([i + dx, i + dx], [lo, hi], color="black", lw=0.8, zorder=4)
                VALUES.append({"figure": fig_name, "panel": letter, "study_paper": study, "rating": measure,
                               "label": lab, "n_participants": n_p, "mean": round(m, 4), "sd": "",
                               "ci95_low": round(lo, 4), "ci95_high": round(hi, 4)})
        ax.set_xticks(range(len(measures)))
        ax.set_xticklabels([MEASURE_SHORT[mm] for mm in measures])
        ax.set_xlim(-0.6, len(measures) - 0.4)
        ax.set_ylim(0, 65)
        ax.set_yticks(range(0, 61, 10))
        ax.grid(axis="y", color="0.9", lw=0.5, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(f"Study {study}")
        first = study == studies[0]
        ax.text((-0.18 if len(studies) == 2 else -0.24) if first else -0.06, 1.06, letter, transform=ax.transAxes,
                fontweight="bold", fontsize=10)
    axes[0].set_ylabel("Explanations mentioning\nprompting or a machine (%)")
    handles = [matplotlib.patches.Patch(facecolor=BAR_FACE[l], edgecolor="#4d4d4d", linewidth=0.7, label=LABEL_TEXT[l])
               for l in (HUMAN, AI)]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.4, columnspacing=1.6)
    fig.subplots_adjust(left=0.13 if len(studies) == 2 else 0.09, right=0.99, top=0.78, bottom=0.16, wspace=0.10)
    save(fig, fig_name)


MEASURE_SHORT = {"creativity": "Creativity", "effort": "Effort",
                 "transformativeness": "Transforma-\ntiveness", "essence_change": "Essence\nchange"}


def fig_explanations_originals():
    explanation_bars("fig4_explanations_originals", [1, 2], ["creativity", "effort"], 0.72)


def fig_explanations_secondary():
    explanation_bars("fig7_explanations_secondary", [3, 4, 5], ["creativity", "transformativeness", "essence_change"], 1.0)


# ------------------------------------- the measures beyond the word lists (Supplement)

def _rows(rel):
    path = PIPELINE / rel
    if not path.exists():
        stop(f"missing {rel}")
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


ORIGINAL_CELLS = [(1, "creativity"), (1, "effort"), (2, "creativity"), (2, "effort")]
SECONDARY_CELLS = [(st, m) for st in (3, 4, 5) for m in ("creativity", "transformativeness", "essence_change")]


def _cell_axis(ax, cells, ylabel):
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels([MEASURE_SHORT[m] for _, m in cells])
    ax.set_xlim(-0.6, len(cells) - 0.4)
    studies = sorted({st for st, _ in cells})
    per = len(cells) // len(studies)
    for k, st in enumerate(studies):
        if k:
            ax.axvline(k * per - 0.5, color="0.6", lw=0.6, ls=(0, (2, 2)))
        ax.text(k * per + (per - 1) / 2, 1.0, f"Study {st}", transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=9.5)
    ax.grid(axis="y", color="0.9", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylabel(ylabel)


def _legend(fig, series, ncol):
    handles = [matplotlib.patches.Patch(facecolor=sr[3], hatch=sr[4], edgecolor="#4d4d4d", linewidth=0.7, label=sr[0])
               for sr in series]
    fig.legend(handles=handles, loc="upper center", ncol=ncol, frameon=False, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.6, columnspacing=1.4)


def fig_meaning(name, cells, width_frac):
    """AUC for predicting each participant's label, by study and rating; bars start at chance (0.5)."""
    rows = _rows("Cross-study/label_from_meaning/tables/label_from_meaning.csv")
    def get(st, m, predictors, explanations):
        hit = [r for r in rows if r["model"] == "all-mpnet-base-v2" and r["explanations"] == explanations
               and int(r["study_paper"]) == st and r["measure"] == m and r["predictors"] == predictors]
        if len(hit) != 1:
            stop(f"label_from_meaning: {len(hit)} rows for Study {st} {m} {predictors} {explanations}")
        r = hit[0]
        return float(r["estimate"]), float(r["ci95_low"]), float(r["ci95_high"]), int(r["participants"])
    series = [("From their ratings", "rating and length", "all", "#9a9a9a", None),
              ("From what they wrote", "meaning only", "all", "white", None),
              ("From what they wrote, leaving out any mention of prompting or a machine", "meaning only",
               "without mentions of prompting or a machine", "white", "////")]
    fig, ax = plt.subplots(figsize=(WIDTH * width_frac, 72 * MM))
    for i, (st, m) in enumerate(cells):
        for (label, pred, expl, face, hatch), dx in zip(series, (-0.26, 0, 0.26)):
            est, lo, hi, n = get(st, m, pred, expl)
            est, lo, hi = 100 * est, 100 * lo, 100 * hi
            ax.bar(i + dx, est - 50, bottom=50, width=0.24, color=face, hatch=hatch, edgecolor="#4d4d4d",
                   linewidth=0.7, zorder=3)
            ax.plot([i + dx, i + dx], [lo, hi], color="black", lw=0.8, zorder=4)
            VALUES.append({"figure": name, "panel": "", "study_paper": st, "rating": m, "label": label,
                           "n_participants": n, "mean": round(est, 4), "sd": "", "ci95_low": round(lo, 4),
                           "ci95_high": round(hi, 4)})
    ax.axhline(50, color="black", lw=0.8, zorder=5)
    ax.set_ylim(30, 100)
    ax.set_yticks([30, 40, 50, 60, 70, 80, 90, 100])
    ax.set_yticklabels(["30", "40", "guessing 50", "60", "70", "80", "90", "100"])
    _cell_axis(ax, cells, "Pairs told apart (%)")
    _legend(fig, series, 3 if width_frac == 1 else 1)
    fig.subplots_adjust(left=0.13 / width_frac, right=0.99, top=0.82 if width_frac == 1 else 0.70, bottom=0.17)
    save(fig, name)


def fig_picture_match_originals():
    """How often CLIP found the picture an explanation was written about, among the ten originals,
    under each label (Human gray, AI white, as in Figures 4 and 7)."""
    name = "figS_picture_match_originals"
    rows = _rows("Cross-study/image_grounding/tables/image_grounding_hits_by_label.csv")
    fig, ax = plt.subplots(figsize=(WIDTH * 0.72, 66 * MM))
    for i, (st, m) in enumerate(ORIGINAL_CELLS):
        for lab, dx in ((HUMAN, -0.19), (AI, 0.19)):
            hit = [r for r in rows if int(r["study_paper"]) == st and r["dimension"] == m and r["label"] == lab
                   and r["level"] == "original"]
            if len(hit) != 1:
                stop(f"image_grounding hits: {len(hit)} rows for Study {st} {m} {lab}")
            r = hit[0]
            est, lo, hi = 100 * float(r["hit_rate"]), 100 * float(r["ci_lo"]), 100 * float(r["ci_hi"])
            ax.bar(i + dx, est, width=0.36, color=BAR_FACE[lab], edgecolor="#4d4d4d", linewidth=0.7, zorder=3)
            ax.plot([i + dx, i + dx], [lo, hi], color="black", lw=0.8, zorder=4)
            VALUES.append({"figure": name, "panel": "", "study_paper": st, "rating": m, "label": lab,
                           "n_participants": int(r["participants"]), "mean": round(est, 4), "sd": "",
                           "ci95_low": round(lo, 4), "ci95_high": round(hi, 4)})
    ax.axhline(10, color="black", lw=0.8, ls=(0, (3, 2)), zorder=5)
    ax.set_ylim(0, 70)
    ax.set_yticks([0, 10, 20, 30, 40, 50, 60, 70])
    ax.set_yticklabels(["0", "chance 10", "20", "30", "40", "50", "60", "70"])
    _cell_axis(ax, ORIGINAL_CELLS, "Picture identified from\nthe explanation (%)")
    handles = [matplotlib.patches.Patch(facecolor=BAR_FACE[l], edgecolor="#4d4d4d", linewidth=0.7, label=LABEL_TEXT[l])
               for l in (HUMAN, AI)]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.4, columnspacing=1.6)
    fig.subplots_adjust(left=0.215, right=0.99, top=0.80, bottom=0.17)
    save(fig, name)


# ------------------------------------------------- compare with the models

def model_estimates():
    """Model estimates the pipeline's tables give for cells drawn here (pipeline paths)."""
    out = {}
    def rd(p):
        with (PIPELINE / p).open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    for r in rd("Study 3/tables/study3_emmeans_cells.csv"):
        out[("fig3_study2", r["dimension"], r["Type"], r["time"])] = float(r["emmean"])
    for r in rd("Study 2/tables/study2_emmeans.csv"):
        if r["means_of"] == "source:modification" or (r["source"] not in ("NA", "") and r["modification"] not in ("NA", "")):
            out[("second", 3, r["measure"], r["source"], r["modification"])] = float(r["emmean"])
    acc = defaultdict(list)
    for r in rd("Study 4/tables/study4_emmeans_cells.csv"):
        acc[(r["measure"], r["label"], r["modification"])].append(float(r["emmean"]))
    for k, v in acc.items():
        out[("second", 4) + k] = sum(v) / len(v)
    for r in rd("Study 5/tables/study5_emmeans_source_by_modification.csv"):
        out[("second", 5, r["rating"], r["source"], r["modification"])] = float(r["emmean"])
    return out


def write_values():
    est = model_estimates()
    for v in VALUES:
        key = None
        if v["figure"] == "fig3_study2":
            key = ("fig3_study2", v["rating"], v["label"], v["stated_hours"])
        elif v["figure"] == "fig5_secondary":
            key = ("second", v["study_paper"], v["rating"], v["label"], v["edit_level"])
        v["model_estimate"] = round(est[key], 4) if key in est else ""
    cols = ["figure", "panel", "study_paper", "rating", "label", "rating_asked", "stated_hours", "edit_level",
            "n_participants", "mean", "sd", "ci95_low", "ci95_high", "model_estimate"]
    with (OUT / "figure_values.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for v in VALUES:
            w.writerow(v)


def main():
    data = {s: read_long(s) for s in (1, 2, 3, 4, 5)}
    fig_stimuli()
    fig_study1(data[1])
    fig_study2(data[3])
    second = [(2, data[2], "source"), (4, data[4], "label"), (5, data[5], "source")]
    fig_explanations_originals()
    fig_secondary(second)
    fig_hours_secondary(data[4], data[5])
    fig_explanations_secondary()
    fig_meaning("figS_meaning_originals", ORIGINAL_CELLS, 0.72)
    fig_picture_match_originals()
    fig_meaning("figS_meaning_secondary", SECONDARY_CELLS, 1.0)
    write_values()
    print(f"wrote 7 main-text figures, 3 Supplementary figures and figure_values.csv to {OUT}")


if __name__ == "__main__":
    main()
