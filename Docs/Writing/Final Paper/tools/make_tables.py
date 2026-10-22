#!/usr/bin/env python3
"""Write the paper's tables from generated/numbers.tex and the pipeline's verdict columns.

What this script writes
-----------------------
* ``tables/paper_table1_summary.tex``: Table 1 of the paper. One row per study: what
  it asked, the answer its registered tests gave, and when it was run relative to its
  registration. Normal type, portrait.
* ``supplement/tables/supp_table1_verdicts.tex``: Supplementary Table 1. Every
  registered test of the five studies, with its status, its registered verdict and what
  had been seen before registration.
* ``supplement/tables/supp_table2_label_effects.tex``: Supplementary Table 2. The AI
  label's effect on ratings of second works, by study, measure and level, with its 90%
  interval, its tests and its registered verdict.
* ``supplement/tables/s1_*.tex``: sixteen readable copies of the Study 1 tables that
  ``Study 1/Study1_Supplements.Rmd`` writes into ``supplement/tables/`` (``sup_table_*.tex``).
  Each is rebuilt from the CSV table its original came from, with plain headings, a caption
  that states each result's status, a note that defines every abbreviation, and type of at
  least 9 points. Each keeps its original's label, so cross-references are unchanged.
* ``supplement/tables/s1_sources.csv``: for each copy, the table it replaces and every
  pipeline CSV it was built from, with the SHA-256 checksum read.

Supplementary Tables 1 and 2 carry, unchanged, the content of the paper's earlier
Tables 1 and 2 (``tables/paper_table1_verdicts.tex`` and
``tables/paper_table2_label_effects.tex``, written by an earlier version of this script;
neither document should input them now). Only the layout changed: portrait instead of a rotated
page, small type instead of tiny, each study as a heading instead of a column, notes as a
list below the table, and references to the other table renamed for the Supplementary
Information.

Where the numbers and verdicts come from
----------------------------------------
In Table 1 and Supplementary Tables 1 and 2, every number is a macro from
``generated/numbers.tex``; run ``tools/make_numbers.py`` first. The Study 1 copies print
numbers read from the pipeline's CSV tables, rounded as ``make_numbers.py`` rounds them, and
wherever a macro prints the same cell the two must agree. Verdicts are worded as in ``notes/results_ledger.md``, and each verdict a table
states is checked against the verdict column of its pipeline table. The pipeline folder is
found as in ``make_numbers.py``: ``../../../../Analysis/R Analysis Pipeline`` from this
file, or the folder named by the environment variable ``PIPELINE_DIR``.

When it stops
-------------
The script stops, and writes nothing, if

* a macro it uses is not defined in ``generated/numbers.tex``;
* a digit appears in a table's text outside a short list of design facts (dates, study
  and hypothesis labels, the stated times, interval levels, the 1-to-5 scale, the .05
  level, the 0-to-1 rescaling and the numbers of the Supplementary Tables);
* a verdict the tables state disagrees with the verdict column of its pipeline table;
* a Study 1 CSV differs from the version that the last run of ``Study1_Supplements.Rmd`` read
  (its SHA-256 in ``Study 1/tables/study1_supplements_run_manifest.csv``) or from the version
  ``generated/numbers.tex`` was built from;
* a cell of a Study 1 copy that a macro also prints would print differently from the macro;
* a Study 1 copy would state a verdict, a count or a reading that its CSV does not support, or
  would print a code name, tiny type, British spelling or an em dash.

How to run
----------
    python3 tools/make_tables.py

from the Final Paper folder (or from anywhere: paths are found from this file). Python 3.8
or later, standard library only.
"""

from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
DEFAULT_PIPELINE = HERE / ".." / ".." / ".." / ".." / "Analysis" / "R Analysis Pipeline"
PIPELINE = Path(os.environ.get("PIPELINE_DIR", str(DEFAULT_PIPELINE))).resolve()
NUMBERS = (PAPER / "generated" / "numbers.tex").read_text(encoding="utf-8")
DEFINED = set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", NUMBERS))

OUT_SUMMARY = PAPER / "tables" / "paper_table1_summary.tex"
OUT_SUPP1 = PAPER / "supplement" / "tables" / "supp_table1_verdicts.tex"
OUT_SUPP2 = PAPER / "supplement" / "tables" / "supp_table2_label_effects.tex"

LATEX_OK = {
    "raggedright", "tabularnewline", "textbf", "emph", "pm", "ref", "addlinespace", "midrule",
    "toprule", "bottomrule", "multicolumn", "label", "caption", "centering", "small", "normalsize",
    "setlength", "tabcolsep", "par", "smallskip", "medskip", "begin", "end", "textit", "textwidth",
    "textsuperscript", "newline", "noindent", "item", "itemsep", "parsep", "topsep", "parskip",
    "dimexpr", "relax", "endfirsthead", "endhead", "endfoot", "endlastfoot", "LTcapwidth", "LTpre",
    "LTpost", "begingroup", "endgroup", "nopagebreak", "vspace", "medskipamount", "cite",
    "textperiodcentered",
}

# Design facts that may be typed: they are not results.
ALLOWED = [
    r"Studies 1, 3 and 4", r"Study~?\s?[1-5]", r"Studies [1-5] (to|and) [1-5]", r"Studies [1-5]",
    r"Studies~?1--5", r"H[1-4]",
    r"\b(4|21|23|25|27) to (9|2|3|5) (March|November|December|February)",
    r"\b(4|21|23|25|27)\b(?= (January|February|March|October|November))",
    r"\b(2|3|5|9)\b(?= (February|March|November|December))", r"\b8 October", r"\b20(24|25|26)\b",
    r"1-to-5", r"\b(90|95)\\%", r"\.05\b", r"0 to 1\b", r"under 1, 10 or 100 hours", r"under 1 hour",
    r"100 hours", r"100 minus under 1", r"CogSci 2025", r"tab:[a-z-]+", r"100-hour",
    r"Supplementary Tables?~?\s?[12]( and [12])?", r"\b[1-5] \((?= ;)",
]


def check(tex: str) -> None:
    """Stop if a macro is undefined or a digit is typed outside the design facts."""
    used = set(re.findall(r"\\([A-Za-z]+)", tex))
    unknown = sorted(u for u in used if u not in DEFINED and u not in LATEX_OK)
    if unknown:
        raise SystemExit(f"unknown macros: {unknown}")
    text = re.sub(r"(?<!\\)%.*", "", tex)                       # comments
    text = re.sub(r"\\cite\{[^}]*\}", " ", text)                # citation keys
    text = re.sub(r"\\multicolumn\{[0-9]+\}", " ", text)          # \multicolumn{n}
    text = re.sub(r"\{@\{\}[^\n]*?@\{\}\}", " ", text)          # column specs
    text = re.sub(r"\\[A-Za-z]+", " ", text)                    # macro names
    text = re.sub(r"[\[{][0-9.]+(cm|pt)[\]}]", " ", text)       # lengths
    for pat in ALLOWED:
        text = re.sub(pat, " ", text)
    left = re.findall(r".{0,40}[0-9].{0,40}", text)
    if left:
        raise SystemExit("typed digits remain:\n" + "\n".join(left))


def cell(text: str) -> str:
    return (r"\raggedright " + text) if text else ""


def colspec(widths, flex: int, gaps: int) -> str:
    """p columns of fixed widths (pt), one of them taking what is left of the text width."""
    fixed = sum(w for i, w in enumerate(widths) if i != flex)
    cols = []
    for i, w in enumerate(widths):
        if i == flex:
            cols.append(r"p{\dimexpr\textwidth-%dpt-%d\tabcolsep\relax}" % (fixed, gaps))
        else:
            cols.append("p{%dpt}" % w)
    return "{@{}" + "".join(cols) + "@{}}"


B = r"$\pm$"


# ---------------------------------------------------------------------------
# Pipeline verdict columns
# ---------------------------------------------------------------------------
def rows(rel: str):
    path = PIPELINE / rel
    if not path.exists():
        raise SystemExit(f"missing pipeline table: {path}")
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def expect(what: str, got, want) -> None:
    if got != want:
        raise SystemExit(f"verdict check failed for {what}: table says {want!r}, pipeline says {got!r}")


def label_effect_verdicts():
    """Each registered verdict of Supplementary Table 2, read from the verdict column of its table."""
    v = {}
    for r in rows("Study 2/tables/study2_hypothesis_readings.csv"):
        if r["hypothesis"] == "H2" and r["measure"] != "all three measures":
            v[("S2", r["measure"], "Averaged")] = r["reading"]
    for r in rows("Study 4/tables/study4_hypotheses.csv"):
        if r["hypothesis"] == "H2" and r["measure"] != "all three measures":
            v[("S4", r["measure"], "Averaged")] = r["verdict"]
    for r in rows("Study 4/tables/study4_secondary_label_by_modification.csv"):
        flag = r["inside_bound"]
        if flag not in {"TRUE", "FALSE"}:
            raise SystemExit(f"study4_secondary_label_by_modification.csv: inside_bound is {flag!r}")
        # The registration gives no wording for these rows; the ledger reads FALSE as
        # 'not shown inside the bound'.
        v[("S4", r["measure"], r["modification"])] = ("inside the bound" if flag == "TRUE"
                                                      else "not shown inside the bound")
    for r in rows("Study 5/tables/study5_equivalence_source.csv"):
        v[("S5", r["rating"], r["modification"])] = r["verdict"]
    return v


def check_summary_verdicts() -> None:
    """The verdicts Table 1 states, against the verdict columns of the pipeline tables."""
    # Study 1: H1 and H2 survive Holm; H3 by its own table; H4 needs both ratings.
    fam = rows("Study 1/tables/study1_confirmatory_family.csv")
    expect("Study 1 H1 and H2 survive Holm",
           sorted({r["survives_holm_at_05"] for r in fam if r["hypothesis"] in {"H1", "H2"}}), ["TRUE"])
    h3 = {r["dimension"]: r["h3_claim"] for r in rows("Study 1/tables/study1_h3_equivalence.csv")}
    expect("Study 1 H3 effort", h3["effort"], "supported")
    expect("Study 1 H3 creativity", h3["creativity"], "inconclusive: cannot separate no effect from a small one")
    h4 = {r["h4_supported_both_dimensions"] for r in rows("Study 1/tables/study1_h4_variance_test.csv")}
    expect("Study 1 H4 (not supported as registered)", h4, {"FALSE"})
    # Study 3: label and time survive Holm, their interaction does not; the decision.
    for r in rows("Study 3/tables/study3_lmm_ftests.csv"):
        want = "FALSE" if r["term"] == "Type:time" else "TRUE"
        expect(f"Study 3 {r['dimension']} {r['term']} survives Holm", r["survives_holm"], want)
    for r in rows("Study 3/tables/study3_decision.csv"):
        expect(f"Study 3 decision, {r['dimension']}", r["verdict"], "the gap persists")
    # Study 2: the hypothesis readings.
    s2 = {(r["measure"], r["hypothesis"]): r["reading"] for r in rows("Study 2/tables/study2_hypothesis_readings.csv")}
    expect("Study 2 H1", s2[("all three measures", "H1")], "holds on every measure")
    for m in ("transformativeness", "essence_change"):
        expect(f"Study 2 H2 {m}", s2[(m, "H2")], "small or absent: inside plus or minus 0.224")
    expect("Study 2 H2 creativity", s2[("creativity", "H2")], "not shown to be small")
    expect("Study 2 H2 over the three measures", s2[("all three measures", "H2")],
           "not shown to be small on every measure")
    for m in ("transformativeness", "essence_change", "creativity"):
        expect(f"Study 2 H3 {m}", s2[(m, "H3")], "not significant")
    # Study 4: the hypothesis verdicts and the refit.
    s4 = {}
    for r in rows("Study 4/tables/study4_hypotheses.csv"):
        s4.setdefault((r["measure"], r["hypothesis"]), set()).add(r["verdict"])
    expect("Study 4 H1", s4[("all three measures", "H1")], {"supported"})
    expect("Study 4 H2 over the three measures", s4[("all three measures", "H2")], {"not shown inside the bound"})
    expect("Study 4 H2 essence change", s4[("essence_change", "H2")], {"inside the bound"})
    for m in ("transformativeness", "creativity"):
        expect(f"Study 4 H2 {m}", s4[(m, "H2")], {"not shown inside the bound"})
    for m in ("transformativeness", "essence_change", "creativity"):
        expect(f"Study 4 H3 {m}", s4[(m, "H3")], {"not significant after Holm"})
    changed = [(r["measure"], r["test_number"]) for r in rows("Study 4/tables/study4_secondary_refit_machine_made.csv")
               if r["verdict_unchanged"] == "FALSE"]
    expect("Study 4 refit: the verdicts that change", changed, [("essence_change", "3")])
    # Study 5: the confirmatory family, the editing-time bound and the label's effect at each level.
    for r in rows("Study 5/tables/study5_confirmatory_family.csv"):
        want = "TRUE" if (r["term"], r["rating"]) == ("source:editing_time", "creativity") else "FALSE"
        expect(f"Study 5 {r['rating']} {r['term']} Holm", r["holm_significant"], want)
    for r in rows("Study 5/tables/study5_equivalence_editing_time.csv"):
        expect(f"Study 5 editing time, {r['rating']}", r["verdict"], "absent or small: inside the bound")
    lev = {}
    for r in rows("Study 5/tables/study5_equivalence_source.csv"):
        lev.setdefault(r["modification"], set()).add(r["verdict"])
        if r["modification"] == "Dramatic":
            # Table 1: at Dramatic, 'significant, not inside the bound' on transformativeness only.
            want = "TRUE" if r["rating"] == "transformativeness" else "FALSE"
            got = "TRUE" if r["verdict"] == "significant, not inside the bound" else "FALSE"
            expect(f"Study 5 label at Dramatic, {r['rating']} significant and not inside", got, want)
    expect("Study 5 label at None", lev["None"], {"absent or small: inside the bound"})
    expect("Study 5 label at Slight", lev["Slight"], {"significant, not inside the bound"})


# ---------------------------------------------------------------------------
# Table 1: the five studies at a glance (main text).
# ---------------------------------------------------------------------------
SUMMARY_ROWS = [
    ("group", "Originals: the same AI-made images, rated for creativity and effort"),
    ("1", r"\SOneN",
     "Does the AI label lower both ratings (H1), effort more (H2), alike with or without a human "
     "figure (H3), and spread them more between people (H4)?",
     "H1 and H2: supported. H3: supported on effort, inconclusive on creativity. H4: not supported as "
     "registered.",
     "Ran third; registered after its analyses"),
    ("3", r"\SThreeN",
     "With under 1, 10 or 100 hours stated, does the gap (the penalty) close by 100 hours?",
     "Decision on both ratings: the gap persists. The AI label lowered ratings and stated time raised them "
     "(both supported); a change in the gap with time was not significant.",
     "Ran fourth; registered after an Apr. 2025 analysis and a Sept. 2025 talk"),
    ("group", "Second works: Alex's edits of each labeled original, at three levels"),
    ("2", r"\STwoN",
     "Do ratings of a second work rise with the level of edit (H1)? Is the label's effect small (H2), "
     "and does it shrink from None to Dramatic (H3)?",
     "H1 holds on every measure. H2, over the three measures: not shown to be small (small or absent on "
     "transformativeness and essence change; not shown to be small on creativity). H3: not significant.",
     r"Ran first; registered after a Feb. 2025 analysis\cite{kamper2025originalsin} and a Sept. 2025 talk"),
    ("4", r"\SFourN",
     "Study~2's H1 and H2 again, and do hours stated for the original change ratings of the second work "
     "(H3)?",
     r"H1 supported. H2, over the three measures: not shown inside the bound (inside it on essence change "
     r"only, a pass lost in the registered refit\textsuperscript{a}). H3: not significant.",
     r"Ran second; registered after a Feb. 2025 analysis\cite{kamper2025originalsin} and a Sept. 2025 talk"),
    ("5", r"\SFiveN",
     "Do hours stated for the edit change ratings of the second work, or the label's effect on them?",
     r"Editing hours: absent or small, inside " + B + r"\SFiveEditTimeBound. A change in the label's "
     r"effect with editing hours: significant on creativity only. The label's effect (secondary): "
     r"significant, not inside the bound, at Slight on every measure and at Dramatic on transformativeness.",
     "Ran last; registered before any rating was averaged or compared by label"),
]

SUMMARY_NOTE = (
    r"Every original was AI-made (OpenAI's DALL\textperiodcentered{}E, used through ChatGPT). Human label: "
    r"Alex used design and sketching tools; AI "
    r"label: he prompted an AI system. \emph{Penalty}: Human-label minus "
    r"AI-label mean rating on 1-to-5 scales (the gap, in Study~3's registration). \emph{None, Slight, "
    r"Dramatic}: the original shown again unchanged, a light edit, a heavy edit; the measures: "
    r"transformativeness, essence change, creativity. \emph{Supported}, \emph{holds}: passed by the "
    r"registration's rule. \emph{Significant}: $p$ below .05, after Holm's correction for confirmatory tests "
    r"(which holds the chance of any false positive in a study's confirmatory set at .05) and uncorrected for "
    r"\emph{secondary} tests outside that set. \emph{Small or absent}, \emph{inside the bound}: an equivalence "
    r"test placed the effect inside " + B + r"\SourceBound{} points, half of Study~1's creativity penalty "
    r"(" + B + r"\SFiveEditTimeBound, Study~3's creativity time effect, for editing hours); small, not zero. \emph{Not shown to be small}, "
    r"\emph{not shown inside}: that test failed, which does not show an effect. \emph{Inconclusive}: no "
    r"effect and a small one could not be told apart. \textsuperscript{a}Without the \SFourMachineMadeN{} "
    r"Human-label participants who wrote that a machine made the work. All five registrations were filed on 8 October 2026, after data "
    r"collection."
)


def summary_table() -> str:
    out = [
        "% Table 1: the five studies at a glance. One row per study: what it asked, the answer its",
        "% registered tests gave, and when it was run relative to its registration. Written by",
        "% tools/make_tables.py; do not edit by hand. Numbers come only from generated/numbers.tex;",
        "% verdicts follow notes/results_ledger.md and are checked against the pipeline tables.",
        "% Needs booktabs and caption, both loaded in main.tex.",
        r"\begin{table}[tbp]",
        r"\centering",
        r"\caption{\textbf{The five studies at a glance.} Supplementary Table~1 lists every registered test "
        r"and its verdict; Supplementary Table~2 gives the label's effect on second works, with intervals.}",
        r"\label{tab:summary}",
        r"\normalsize",
        r"\setlength{\tabcolsep}{5pt}",
        r"\begin{tabular}" + colspec([40, 128, 0, 82], flex=2, gaps=6),
        r"\toprule",
        r"Study & What it asked & Registered answer & Order run; registered\tabularnewline",
        r"\midrule",
    ]
    first = True
    for row in SUMMARY_ROWS:
        if row[0] == "group":
            if not first:
                out.append(r"\midrule")
            first = False
            out.append(r"\multicolumn{4}{@{}p{\textwidth}@{}}{\raggedright\textbf{" + row[1] + r"}}\\*")
            out.append(r"\addlinespace[2pt]")
            continue
        study, n, asked, answer, run = row
        out.append(" & ".join([r"\raggedright Study~%s\newline $N$~=~%s" % (study, n),
                               cell(asked), cell(answer), cell(run)]) + r"\tabularnewline")
        out.append(r"\addlinespace[3pt]")
    if out[-1].startswith(r"\addlinespace"):
        out.pop()
    out += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\smallskip",
        r"{\small\raggedright " + SUMMARY_NOTE + r"\par}",
        r"\end{table}",
    ]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Supplementary Table 1: every registered test, one row each; measures with the same
# verdict share a row. Content as in the former main-text Table 1.
# ---------------------------------------------------------------------------
S1_ROWS = [
    ("group", "Originals: the same AI-made images, rated for creativity and effort"),
    ("1", "H1: the AI label lowers ratings", "Creativity; effort", "Confirmatory",
     "Supported: AI lower on both; both survive Holm's correction", r"Both drops: \emph{t}-tests, talk"),
    ("", "H2: the drop is larger on effort", "Effort minus creativity", "Confirmatory",
     "Supported: survives Holm's correction; the ordinal model agrees", "Larger effort drop: talk"),
    ("", "H3: the same penalty, figure or not", "Creativity", "Own rule",
     "Inconclusive: cannot separate no effect from a small one", "Rule set after analysis"),
    ("", "", "Effort", "Own rule",
     r"Supported: not significant, and equivalent within " + B + r"\SOneHThreeBound", "As above"),
    ("", "H4: spread between vs within people", "Creativity; effort", "Confirmatory",
     "Not supported as registered: met on effort, not on creativity", "Quantity set after analysis"),
    ("3", r"Label ($F$~test)", "Creativity; effort", "Confirmatory",
     "Supported: significant after Holm's correction, AI lower", "Reported in the talk"),
    ("", r"Stated time ($F$~test)", "Creativity; effort", "Confirmatory",
     "Supported after Holm's correction; 100 hours above under 1 hour", "Reported in the talk"),
    ("", r"Label by time ($F$~test)", "Creativity; effort", "Confirmatory",
     "Does not survive Holm's correction", "Talk: on effort only"),
    ("", r"100-hour gap: equivalence, decision", "Creativity; effort", "Confirmatory",
     "Not equivalent. Decision: the gap persists", "Written knowing the talk"),
    ("", "100 hours minus under 1 hour", "Creativity; effort", "Secondary",
     r"Positive on both ratings (95\% intervals above zero)", "--"),
    ("group", "Second works: hand edits of a labeled original, rated for transformativeness, essence change "
              "and creativity"),
    ("2", "H1: ratings rise with the level", "All three", "Confirmatory",
     "Holds on every measure: both steps positive and significant", "Seen: large effects"),
    ("", r"H2: averaged label effect, " + B + r"\SourceBound", "Transformativeness", "Confirmatory",
     r"Small or absent: inside " + B + r"\SourceBound", "Bound set after Study 1"),
    ("", "", "Essence change", "Confirmatory", r"Small or absent: inside " + B + r"\SourceBound", "As above"),
    ("", "", "Creativity", "Confirmatory",
     r"Not shown to be small (interval inside; Holm $p$~\STwoCreatPenaltyPHolm)", "Seen: a creativity effect"),
    ("", "H3: label effect, None minus Dramatic", "All three", "Confirmatory", "Not significant",
     "Seen: none significant"),
    ("4", "H1: ratings rise with the level", "All three", "Confirmatory",
     "Supported on every measure", "Seen: large effects"),
    ("", r"H2: averaged label effect, " + B + r"\SourceBound", "Transformativeness", "Confirmatory",
     r"Not shown inside the bound (interval inside; Holm $p$~\SFourTransPenaltyPHolm)", "Seen: label not significant"),
    ("", "", "Essence change", "Confirmatory",
     r"Inside the bound (Holm $p$~\SFourEssPenaltyPHolm); not shown in the refit", "As above"),
    ("", "", "Creativity", "Confirmatory",
     "Not shown inside the bound (the estimate runs the other way)", "As above"),
    ("", r"H3: hours on the original ($F$~test)", "All three", "Confirmatory",
     "Not significant after Holm's correction", "Seen: a creativity effect"),
    ("", r"H3: those hours by level ($F$~test)", "All three", "Confirmatory",
     "Not significant after Holm's correction", "--"),
    ("", r"Label by those hours ($F$~test)", "All three", "Secondary",
     "Not significant (no correction applies)", "--"),
    ("", "Those hours: 100 minus under 1", "All three", "Secondary",
     "Inside the bound on all three measures", "--"),
    ("", r"Label effect at each level (Supplementary Table~\ref{tab:supp-labeleffects})", "All three", "Secondary",
     "Inside the bound or not shown inside it, by measure and level", "Seen: on essence, by level"),
    ("", "Refit without flagged participants", "All three", "Secondary",
     r"\SFourNRefitVerdictsChanged{} of \SFourNRefitVerdicts{} verdicts changes: essence change "
     r"(Holm $p$~\SFourEssPenaltyPHolmRefitPrecise)", "--"),
    ("5", r"Editing hours ($F$~test)", "All three", "Confirmatory",
     "Not significant after Holm's correction", "--"),
    ("", "Editing hours: 100 minus under 1", "All three", "Secondary",
     "Absent or small: inside the bound", "--"),
    ("", r"Label by editing hours ($F$~test)", "Transformativeness", "Confirmatory",
     "Not significant after Holm's correction; not shown to be absent", "--"),
    ("", "", "Essence change", "Confirmatory",
     "Not significant after Holm's correction; not shown to be absent", "--"),
    ("", "", "Creativity", "Confirmatory",
     r"Significant after Holm's correction (Holm $p$~\SFiveCreatSourceByEditTimePHolm); "
     r"\SFiveNConfirmatoryHolmSignificant{} of \SFiveNConfirmatory{} passed", "--"),
    ("", r"Label effect at each level (Supplementary Table~\ref{tab:supp-labeleffects})", "All three", "Secondary",
     "None: absent or small (all three). Slight: significant, not inside the bound (all three). "
     "Dramatic: transformativeness as at Slight; essence change absent or small; creativity inconclusive", "--"),
    ("rule", ""),
    ("1--5", "Text checks on the explanations", "Explanations", "Secondary",
     "Verdicts in the note below", "Study 1: partly known"),
]

# The note of the former Table 1, word for word, split at its headings into list items.
S1_NOTES = [
    r"\textbf{Studies} (analyzed participants; collection): 1 (\SOneN; 25 February to 3 March 2025); 2 "
    r"(\STwoN; 23 November to 5 December 2024); 3 (\SThreeN; 4 to 9 March 2025); 4 (\SFourN; 27 January to "
    r"2 February 2025); 5 (\SFiveN; 21 October to 2 November 2025).",
    r"\textbf{Registered} means written into a registration, not fixed before collection. All five were "
    r"filed on OSF on 8 October 2026, after collection: Study~1's after its analyses had been run, the "
    r"others before the analyses reported here.",
    r"\textbf{Seen before registration}: April 2025 \emph{t}-tests (Study~1); analyses of variance run by "
    r"February 2025 and reported in the 2025 proceedings of the Cognitive Science Society (CogSci 2025)"
    r"\cite{kamper2025originalsin} (Studies 2 and 4) or run in April 2025 (Study~3); a September "
    r"2025 talk on Studies 1 to 4 (`talk'). For Study~5 no rating had been summarized by condition, and both "
    r"bounds were fixed before any Study~5 model was fitted.",
    r"\textbf{Status}. \emph{Confirmatory}: decided by the registration's rule, usually after Holm's "
    r"correction, which raises each $p$-value in a set of tests so that the chance of any false positive in "
    r"the set stays at .05. \emph{Secondary}: outside that set, and uncorrected unless stated. \emph{Own "
    r"rule}: Study~1's H3, a significance test read with an equivalence test; its power on creativity was "
    r"\SOneHThreeCreatPower, so that failed equivalence test is uninformative.",
    r"An \textbf{equivalence test} asks whether an effect is shown to lie inside a bound. It passes when the "
    r"90\% confidence interval lies wholly inside, which means small, not zero. An $F$ test asks whether a "
    r"factor changes the mean rating.",
    r"Bounds in points on 1-to-5 scales: " + B + r"\SOneHThreeBound{} (Study~1's H3); " + B
    + r"\SourceBound, half of Study~1's creativity penalty of \SOneHOneCreatDiffPrecise{} (label effects and "
    r"Study~3's gap); " + B + r"\SFiveEditTimeBound, the size of Study~3's creativity time effect (editing "
    r"hours).",
    r"\textbf{Checks}. Ordinal refits, which treat the answers as ordered categories, agreed with every "
    r"verdict they re-tested in Studies 2 to 5, except Study~2's creativity refit, which did not converge "
    r"(not completed). Study~5's analysis with items rescaled from 0 to 1 gave the same verdicts. Study~3's "
    r"required refit with effects varying by person and image was singular (a variance at the edge of its "
    r"range), so that requirement was waived. Study~1's H4 needs both ratings; its between-person test "
    r"survives in the Holm set, which does not mean H4 passed. Flagged: Study~4's \SFourMachineMadeN{} "
    r"Human-label participants who wrote that a machine made the work.",
    r"\textbf{Text checks} on the explanations, each written after its rating. Word counts recover the "
    r"rating in every study: they predict it for people left out of the fit better than a shuffled "
    r"baseline. They recover the label in Study~1, for Study~3's effort and, barely, in Study~5, and are not "
    r"shown to do so elsewhere. They add to the rating in telling the labels apart in Studies 1 and 2 and are "
    r"inconclusive in Studies 3 to 5. Greater own-word reuse under the AI label is supported for Study~1's "
    r"effort only.",
]

S1_CAPTION = (r"\textbf{Registered tests and their verdicts.} One row per registered test; measures that "
              r"reached the same verdict share a row. Verdicts are worded by each registration's decision rule.")


def notes_list(items) -> list:
    return ([r"\begin{itemize}", r"\setlength{\itemsep}{1pt}", r"\setlength{\parskip}{0pt}"]
            + [r"\item " + it for it in items] + [r"\end{itemize}"])


def longtable_head(caption: str, label: str, spec: str, header: str, ncols: int, name: str) -> list:
    return [
        r"\setlength{\LTcapwidth}{\textwidth}",
        r"\begin{longtable}" + spec,
        r"\caption{" + caption + r"}\label{" + label + r"}\tabularnewline",
        r"\toprule",
        header + r"\tabularnewline",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{%d}{@{}l@{}}{\textit{%s, continued}}\tabularnewline" % (ncols, name),
        r"\toprule",
        header + r"\tabularnewline",
        r"\midrule",
        r"\endhead",
        r"\midrule",
        r"\multicolumn{%d}{r@{}}{\textit{Continued on the next page}}\tabularnewline" % ncols,
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
    ]


def supp_table1() -> str:
    spec = colspec([92, 85, 60, 0, 74], flex=3, gaps=8)
    header = (r"\raggedright Hypothesis or test & Measure & Status & Registered verdict & "
              r"\raggedright Known before registration")
    out = [
        "% Supplementary Table 1: every registered test of the five studies, with its status, its registered",
        "% verdict and what had been seen before registration. Written by tools/make_tables.py; do not",
        "% edit by hand. Numbers come only from generated/numbers.tex; verdicts follow notes/results_ledger.md.",
        "% Needs booktabs, longtable and caption, all loaded in supplement/supplement.tex.",
        r"\begingroup",
        r"\small",
        r"\setlength{\tabcolsep}{4pt}",
    ]
    out += longtable_head(S1_CAPTION, "tab:supp-verdicts", spec, header, 5, r"Supplementary Table~\ref{tab:supp-verdicts}")
    first = True
    for row in S1_ROWS:
        if row[0] == "rule":
            out.append(r"\midrule")
            continue
        if row[0] == "group":
            if not first:
                out.append(r"\midrule")
            first = False
            out.append(r"\multicolumn{5}{@{}p{\textwidth}@{}}{\raggedright\textbf{" + row[1] + r"}}\tabularnewline")
            continue
        study = row[0]
        if study:
            name = "Studies~1--5" if study == "1--5" else "Study~" + study
            if out[-1] not in (r"\midrule",) and not out[-1].startswith(r"\multicolumn"):
                out.append(r"\addlinespace[4pt]")
            out.append(r"\multicolumn{5}{@{}l@{}}{\textit{" + name + r"}}\\*")
        elif row[1]:
            out.append(r"\addlinespace[2pt]")    # a new test: a little space above it
        out.append(" & ".join(cell(x) for x in row[1:]) + r"\tabularnewline")
    out += [r"\end{longtable}"]
    out += [r"\vspace{-\medskipamount}", r"\noindent\textit{Notes to Supplementary Table~\ref{tab:supp-verdicts}.}"]
    out += notes_list(S1_NOTES)
    out += [r"\endgroup"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Supplementary Table 2: the label's effect on second works, by study, measure and level.
# Content as in the former main-text Table 2.
# ---------------------------------------------------------------------------
MEAS = [("Trans", "Transformativeness", "transformativeness"), ("Ess", "Essence change", "essence_change"),
        ("Creat", "Creativity", "creativity")]
LEVELS = ["None", "Slight", "Dramatic"]

S2_CAPTION = (
    r"\textbf{The AI label's effect on ratings of second works.} Each estimate is the "
    r"Human-label minus AI-label difference in the model's predicted mean rating, in points on the "
    r"1-to-5 scale; a positive value means the second work was rated lower when its original carried the "
    r"AI label. Studies 2 and 4 registered the effect averaged over levels as a confirmatory test; Study 4 "
    r"also registered it at each level, and Study 5 registered it only at each level, both as secondary "
    r"tests. Each row is a registered test of whether the effect lies inside " + B + r"\SourceBound{} "
    r"points."
)

# The note of the former Table 2, word for word, split into list items.
S2_NOTES = [
    r"\emph{Equivalence test}: two one-sided tests of whether the difference lies inside " + B
    + r"\SourceBound{} points, half of Study~1's label penalty on the creativity of originals "
    r"(\SOneHOneCreatDiffPrecise; 95\% confidence interval \SOneHOneCreatLo{} to \SOneHOneCreatHi). It "
    r"passes when the 90\% interval lies wholly inside the bound. A pass means the effect is small, not "
    r"that it is zero; a fail means only that it is not shown to be small.",
    r"\emph{Two-sided test}: whether the difference is zero.",
    r"\emph{Holm's correction} raises each $p$-value in a set of tests so that the chance of any false "
    r"positive in the set stays at .05.",
    r"None is the original shown again unchanged, where ratings sit near the floor of the scale. Editing "
    r"hours are the hours stated for the hand edit (Study~5).",
    r"Study~4's registration gives no wording for its tests at each level; `inside the bound' marks a "
    r"passed equivalence test.",
    r"\textsuperscript{a}Description only; Study~2's verdict rests on the equivalence test.",
    r"\textsuperscript{b}The label's $F$ test, a term outside Study~4's registered set of tests (it asks "
    r"whether the label changes the mean rating), shown as context.",
    r"\textsuperscript{c}Not shown in the registered refit without the \SFourMachineMadeN{} Human-label "
    r"participants who wrote that a machine made the work (Holm $p$~\SFourEssPenaltyPHolmRefitPrecise).",
    r"\textsuperscript{d}The interval's upper end is \SFiveCreatPenaltyDramaticHiNinetyPrecise, just "
    r"outside the bound.",
    r"In Study~5, `significant' means a two-sided $p$ below .05. Study~5's estimates average over editing "
    r"hours, across which the creativity penalty differed (Supplementary Table~\ref{tab:supp-verdicts}).",
]


def sentence_case(s: str) -> str:
    s = s.replace("plus or minus 0.224", B + r"\SourceBound")
    return s[0].upper() + s[1:]


def p(macro: str) -> str:
    return r"$p$~\%s" % macro


def supp_table2() -> str:
    v = label_effect_verdicts()
    spec = colspec([85, 42, 40, 62, 46, 54, 0], flex=6, gaps=12)
    header = (r"Measure & Level & Estimate & \raggedright 90\% interval & \raggedright Two-sided test & "
              r"\raggedright Equivalence test & \raggedright Registered verdict")
    out = [
        "% Supplementary Table 2: the AI label's effect on ratings of second works, by study, measure and level.",
        "% Written by tools/make_tables.py; do not edit by hand. Numbers come only from generated/numbers.tex;",
        "% verdicts are the verdict columns of the pipeline tables.",
        "% Needs booktabs, longtable and caption, all loaded in supplement/supplement.tex.",
        r"\begingroup",
        r"\small",
        r"\setlength{\tabcolsep}{3pt}",
    ]
    out += longtable_head(S2_CAPTION, "tab:supp-labeleffects", spec, header, 7,
                          r"Supplementary Table~\ref{tab:supp-labeleffects}")

    # Each block (a heading and its rows) is kept on one page: its rows end with
    # \tabularnewline*, which forbids a page break, except the block's last row.
    def end_block() -> None:
        if out[-1].endswith(r"\tabularnewline*"):
            out[-1] = out[-1][:-1]

    def head(text: str, first: bool = False) -> None:
        if not first:
            end_block()
            out.append(r"\addlinespace[4pt]")
        out.append(r"\multicolumn{7}{@{}p{\textwidth}@{}}{\raggedright\textit{" + text + r"}}\\*")

    def add(cells) -> None:
        if cells[0] and not out[-1].endswith(r"\\*"):
            out.append(r"\addlinespace[2pt]")    # a new measure: a little space above it
        out.append(" & ".join(cells) + r"\tabularnewline*")

    head(r"Study 2, averaged over levels (H2, confirmatory; equivalence $p$ after Holm's correction)", first=True)
    for M, label, key in MEAS:
        add([label, "Averaged", r"\STwo%sPenaltyEst" % M,
             r"\STwo%sPenaltyLoNinety{} to \STwo%sPenaltyHiNinety" % (M, M),
             p("STwo%sPenaltyP" % M) + r"\textsuperscript{a}", p("STwo%sPenaltyPHolm" % M),
             cell(sentence_case(v[("S2", key, "Averaged")]))])
    head(r"Study 4, averaged over levels and over the hours stated for the original (H2, confirmatory; "
         r"equivalence $p$ after Holm's correction)")
    for M, label, key in MEAS:
        add([label, "Averaged", r"\SFour%sPenaltyEst" % M,
             r"\SFour%sPenaltyLoNinety{} to \SFour%sPenaltyHiNinety" % (M, M),
             p("SFour%sLabelP" % M) + r"\textsuperscript{b}", p("SFour%sPenaltyPHolm" % M),
             cell(sentence_case(v[("S4", key, "Averaged")]) + (r"\textsuperscript{c}" if M == "Ess" else ""))])
    head("Study 4, each level, averaged over the hours stated for the original (secondary; uncorrected)")
    for M, label, key in MEAS:
        for i, lev in enumerate(LEVELS):
            add([label if i == 0 else "", lev, r"\SFour%sPenalty%sEst" % (M, lev),
                 r"\SFour%sPenalty%sLoNinety{} to \SFour%sPenalty%sHiNinety" % (M, lev, M, lev),
                 p("SFour%sPenalty%sP" % (M, lev)), p("SFour%sPenalty%sPTost" % (M, lev)),
                 cell(sentence_case(v[("S4", key, lev)]))])
    head("Study 5, each level, averaged over editing hours (secondary; each test judged at .05 without correction)")
    for M, label, key in MEAS:
        for i, lev in enumerate(LEVELS):
            mark = r"\textsuperscript{d}" if (M, lev) == ("Creat", "Dramatic") else ""
            add([label if i == 0 else "", lev, r"\SFive%sPenalty%sEst" % (M, lev),
                 r"\SFive%sPenalty%sLoNinety{} to \SFive%sPenalty%sHiNinety" % (M, lev, M, lev),
                 p("SFive%sPenalty%sP" % (M, lev)), p("SFive%sPenalty%sPTost" % (M, lev)),
                 cell(sentence_case(v[("S5", key, lev)]) + mark)])
    end_block()
    out += [r"\end{longtable}"]
    out += [r"\vspace{-\medskipamount}",
            r"\noindent\textit{Notes to Supplementary Table~\ref{tab:supp-labeleffects}.}"]
    out += notes_list(S2_NOTES)
    out += [r"\endgroup"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Study 1: readable copies of the pipeline's Supplementary tables (s1_*.tex)
#
# Study1_Supplements.Rmd writes Study 1's Supplementary tables (sup_table_*.tex) straight
# from the pipeline's CSV tables, with the CSV column names as headings, captions of up to
# 400 words, and wide tables shrunk to fit the page at 6 to 7 points. Each function below
# rebuilds one of them from the same CSV in the Supplement's style: plain headings, a
# caption that says what the table shows and the status of each result, a note that
# defines every abbreviation, and type of at least 9 points. Every CSV read here is first
# checked against the SHA-256 checksum that the run of Study1_Supplements.Rmd recorded for
# it (Study 1/tables/study1_supplements_run_manifest.csv), so each copy comes from the data
# its original came from, and against the checksum that tools/make_numbers.py recorded, so
# that the tables and the macros in the text come from the same files. Wherever a cell
# printed here is also printed by a macro, the two printed values must be identical.
# ---------------------------------------------------------------------------
S1 = "Study 1/tables/"
S1_MANIFEST = S1 + "study1_supplements_run_manifest.csv"
NUMBERS_CHECK = PAPER / "generated" / "numbers_check.csv"
OUT_S1_DIR = PAPER / "supplement" / "tables"
OUT_S1_SOURCES = OUT_S1_DIR / "s1_sources.csv"
MINUS = r"\ensuremath{-}"
RATINGS = [("creativity", "Creativity"), ("effort", "Effort")]

# Each readable copy, the pipeline table it replaces in the Supplement, and its label
# (the original's label, so that every cross-reference still resolves).
S1_COPIES = [
    ("s1_exclusions.tex", "sup_table_exclusions.tex", "tab:supp_exclusions"),
    ("s1_attrition.tex", "sup_table_attrition.tex", "tab:supp_attrition"),
    ("s1_demographics.tex", "sup_table_demographics.tex", "tab:supp_demographics"),
    ("s1_balance.tex", "sup_table_balance.tex", "tab:supp_balance"),
    ("s1_holm_family.tex", "sup_table_holm_family.tex", "tab:supp_holm_family"),
    ("s1_full_lmm.tex", "sup_table_full_lmm.tex", "tab:supp_lmm"),
    ("s1_robustness.tex", "sup_table_1_robustness.tex", "tab:supp_table_1"),
    ("s1_influence.tex", "sup_table_influence.tex", "tab:supp_influence"),
    ("s1_item_sensitivity.tex", "sup_table_item_sensitivity.tex", "tab:supp_item_sensitivity"),
    ("s1_bootstrap_d.tex", "sup_table_bootstrap_d.tex", "tab:supp_bootstrap_d"),
    ("s1_text_rates.tex", "sup_table_2_text_rates.tex", "tab:supp_table_2"),
    ("s1_prompt_talk.tex", "sup_table_3_prompt_talk.tex", "tab:supp_table_3"),
    ("s1_denotation_slope_sensitivity.tex", "sup_table_denotation_slope_sensitivity.tex",
     "tab:supp_denotation_slope_sensitivity"),
    ("s1_text_recoverability.tex", "sup_table_text_recoverability.tex", "tab:supp_text_recoverability"),
    ("s1_text_selfsimilarity.tex", "sup_table_text_selfsimilarity_by_arm.tex", "tab:supp_text_selfsimilarity"),
    ("s1_text_topics_stability.tex", "sup_table_text_topics_stability.tex", "tab:supp_text_topics_stability"),
]
S1_LABEL = {name: label for name, _orig, label in S1_COPIES}

_S1_DATA: dict = {}          # rel -> (rows, sha256)
_S1_CELLS: list = []         # (rel, row index, column, format, printed)
_S1_SOURCES: dict = {}       # output file -> list of rel
_MANIFEST: dict = {}


def _manifest_inputs() -> dict:
    """The SHA-256 of every CSV that the last run of Study1_Supplements.Rmd read."""
    path = PIPELINE / S1_MANIFEST
    if not path.is_file():
        raise SystemExit(f"missing the record of the Study 1 supplements run: {path}")
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["role"] == "input" and r["path"].endswith(".csv"):
                out[r["path"].replace("Analysis/R Analysis Pipeline/", "", 1)] = r["sha256"]
    return out


def s1_read(rel: str) -> list:
    """Read a Study 1 CSV once, after checking its checksum against the supplements run."""
    if rel not in _S1_DATA:
        if not _MANIFEST:
            _MANIFEST.update(_manifest_inputs())
        path = PIPELINE / rel
        if not path.is_file():
            raise SystemExit(f"missing pipeline table: {path}")
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        want = _MANIFEST.get(rel)
        if want is None:
            raise SystemExit(f"{rel} is not an input of the run recorded in {S1_MANIFEST}")
        if sha != want:
            raise SystemExit(f"{rel} has changed since Study1_Supplements.Rmd read it (SHA-256 {sha}; "
                             f"recorded {want}). Rerun the Study 1 pipeline, then this script.")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
        if not rows:
            raise SystemExit(f"{rel} has no rows")
        _S1_DATA[rel] = (rows, sha)
    return _S1_DATA[rel][0]


def _matches(cell: str, wanted: str) -> bool:
    """As in make_numbers.py: an exact match, '^text' for a prefix, '~text' for a substring."""
    if wanted.startswith("^"):
        return cell.startswith(wanted[1:])
    if wanted.startswith("~"):
        return wanted[1:] in cell
    return cell == wanted


def s1_row(rel: str, where: dict) -> tuple:
    """The one row that meets every condition; stops if no row or several rows do."""
    rows = s1_read(rel)
    hits = [i for i, r in enumerate(rows) if all(_matches(r.get(c, ""), w) for c, w in where.items())]
    if len(hits) != 1:
        raise SystemExit(f"{rel}: {len(hits)} rows match {where}, not one")
    return hits[0], rows[hits[0]]


def _number(cell: str, where: str) -> Decimal:
    text = (cell or "").strip()
    if text == "" or text.upper() in {"NA", "NAN", "INF", "-INF", "TRUE", "FALSE"}:
        raise SystemExit(f"{where}: the cell is '{cell}', not a number")
    try:
        return Decimal(text)
    except InvalidOperation:
        raise SystemExit(f"{where}: the cell '{cell}' is not a number")


# Rounding and printing as tools/make_numbers.py does them (half-up), so that a cell
# printed here and a macro printed in the text agree. Degrees of freedom never take a
# thousands separator.
def _fixed(value: Decimal, places: int) -> str:
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    text = f"{abs(rounded):.{places}f}"
    return (MINUS + text) if rounded < 0 else text


def _count(value: Decimal) -> str:
    rounded = int(value.to_integral_value(rounding=ROUND_HALF_UP))
    text = f"{abs(rounded):,}".replace(",", "{,}")
    return (MINUS + text) if rounded < 0 else text


def _df(value: Decimal) -> str:
    whole = value.to_integral_value(rounding=ROUND_HALF_UP)
    if abs(value - whole) < Decimal("0.05"):
        return str(int(whole))
    return _fixed(value, 1)


def _p(value: Decimal) -> str:
    if value < 0 or value > 1:
        raise SystemExit(f"p-value {value} lies outside 0 to 1")
    if value < Decimal("0.001"):
        return r"\ensuremath{<} .001"
    rounded = value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    if rounded >= 1:
        return r"\ensuremath{>} .999"
    return r"\ensuremath{=} " + f"{rounded:.3f}"[1:]


S1_FORMATS = {
    "dec2": lambda v: _fixed(v, 2), "es": lambda v: _fixed(v, 2), "stat": lambda v: _fixed(v, 2),
    "dec3": lambda v: _fixed(v, 3), "df": _df, "p": _p, "count": _count,
    "pct": lambda v: _fixed(v * 100, 1) + r"\%",
}


def val(rel: str, where: dict, column: str, fmt: str) -> str:
    """One cell, printed in the given format and recorded for the check against the macros."""
    i, row = s1_row(rel, where)
    if column not in row:
        raise SystemExit(f"{rel}: no column '{column}'")
    printed = S1_FORMATS[fmt](_number(row[column], f"{rel} {where} {column}"))
    _S1_CELLS.append((rel, i, column, fmt, printed))
    return printed


def num(rel: str, where: dict, column: str) -> Decimal:
    return _number(s1_row(rel, where)[1][column], f"{rel} {where} {column}")


def text_of(rel: str, where: dict, column: str) -> str:
    return s1_row(rel, where)[1][column]


def pval(rel: str, where: dict, column: str) -> str:
    """A printed p-value, with no line break between its sign and its value."""
    return r"$p$~" + val(rel, where, column, "p").replace("} ", "}~")


def span(rel: str, where: dict, lo: str, hi: str, fmt: str) -> str:
    return val(rel, where, lo, fmt) + " to " + val(rel, where, hi, fmt)


def require(what: str, ok: bool) -> None:
    if not ok:
        raise SystemExit(f"Study 1 table check failed: {what}")


def macro_stored(name: str) -> Decimal:
    """The stored value of a macro, from generated/numbers_check.csv."""
    with open(NUMBERS_CHECK, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["macro"] == name:
                return Decimal(r["stored_value"])
    raise SystemExit(f"macro {name} is not in {NUMBERS_CHECK}")


def P(width: str) -> str:
    """A ragged-right paragraph column of the given width."""
    return r">{\raggedright\arraybackslash}p{" + width + "}"


def s1_float(name: str, short: str, caption: str, spec: str, header: list, body: list,
             notes: str, sources: list, size: str = r"\small") -> str:
    """One table float in the Supplement's style: caption above, notes below."""
    for rel in sources:
        s1_read(rel)
    _S1_SOURCES[name] = list(sources)
    out = [
        "% " + short + ".",
        "% Written by tools/make_tables.py from the pipeline table(s) below (paths relative to",
        "% Analysis/R Analysis Pipeline, each with the SHA-256 it was read with); do not edit by hand.",
    ] + ["%   " + rel + "  " + _S1_DATA[rel][1] for rel in sources] + [
        r"\begin{table}[htbp]",
        r"\centering",
        size,
        r"\caption[" + short + r"]{" + caption + r"}\label{" + S1_LABEL[name] + r"}",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}" + spec + r"@{}}",
        r"\toprule",
    ] + header + [r"\midrule"] + body + [
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\smallskip",
        r"\begin{minipage}{\textwidth}\footnotesize\raggedright " + notes + r"\par\end{minipage}",
        r"\end{table}",
    ]
    return "\n".join(out) + "\n"


def group(text: str, ncols: int) -> str:
    """An italic heading over a group of rows."""
    return r"\multicolumn{%d}{@{}l}{\textit{%s}}\\" % (ncols, text)


# --- Exclusions --------------------------------------------------------------
def s1_exclusions() -> str:
    rel = S1 + "study1_exclusion_flow.csv"
    steps = [
        ("^Initial records", "Records in the survey export, test runs included"),
        ("^After (0)", "Survey previews (test runs by the researchers) removed"),
        ("^After (1)", "Unfinished records removed"),
        ("^After (2)", r"Any answer but `Yes, I did' to the seriousness question, a blank included, removed"),
        ("^After (3)", "Wrong answer to the task check removed"),
    ]
    rows = s1_read(rel)
    require("the exclusion flow has its five steps in order",
            len(rows) == len(steps) and all(r["step"].startswith(p[1:]) for r, (p, _) in zip(rows, steps)))
    require("the first row removes nothing", rows[0]["n_dropped"] == "NA")
    body = []
    for i, (pat, label) in enumerate(steps):
        removed = "--" if i == 0 else val(rel, {"step": pat}, "n_dropped", "count")
        body.append(r"%s & %s & %s\\" % (label, removed, val(rel, {"step": pat}, "n", "count")))
    caption = (r"\textbf{Study~1: exclusions.} The registered exclusion steps in the order they were applied, "
               r"with the records each step removed and the records left after it. A record is one session "
               r"in the survey export.")
    notes = (r"The task check asked `What is your task in this experiment?'. A wrong answer brought the "
             r"instructions back once and then let the participant continue, so this step removed no one. The "
             r"seriousness question asked `Did you complete this experiment seriously throughout (without "
             r"responding randomly)?'.")
    return s1_float("s1_exclusions.tex", "Study 1: exclusions", caption, P("11.4cm") + "rr",
                    [r"Step & Removed & Records left\\"], body, notes, [rel])


# --- Removals by label -------------------------------------------------------
def s1_attrition() -> str:
    rel = S1 + "study1_attrition_by_condition.csv"
    rows = s1_read(rel)
    order = [("0_retained", "Analyzed"), ("1_unfinished", "Removed as unfinished"),
             ("2_nonserious", "Removed by the seriousness question")]
    require("three rows, in the expected order", [r["dropped_at"] for r in rows] == [o for o, _ in order])
    require("every row counts the records left after survey previews were removed",
            {r["frame"] for r in rows} == {"after step 0 (all real respondents)"})
    require("no record lacks a label", {r["n_type_na"] for r in rows} == {"0"})
    require("each Fisher test is one value, repeated on every row",
            len({r["fisher_p_any_drop"] for r in rows}) == 1 and len({r["fisher_p_by_step"] for r in rows}) == 1)
    body = []
    for key, label in order:
        w = {"dropped_at": key}
        body.append(r"%s & %s & %s & %s\\" % (label, val(rel, w, "n_Human", "count"), val(rel, w, "n_AI", "count"),
                                             val(rel, w, "n_total", "count")))
    first = {"dropped_at": "0_retained"}
    caption = (r"\textbf{Study~1: removals by label.} The records left once survey previews had been removed, by "
               r"the label each participant had been shown: those analyzed and those removed at each later step "
               r"(descriptive).")
    notes = (r"Fisher's exact test, a test for counts in small tables, compared the two labels. Removed at any "
             r"step against analyzed: " + pval(rel, first, "fisher_p_any_drop") + r". The whole table of steps by "
             r"label: " + pval(rel, first, "fisher_p_by_step") + r". Every record carried a label.")
    return s1_float("s1_attrition.tex", "Study 1: removals by label", caption, "lrrr",
                    [r"Records & Human label & AI label & Total\\"], body, notes, [rel])


# --- The analyzed participants ------------------------------------------------
def s1_demographics() -> str:
    rels = {k: S1 + "study1_demo_%s.csv" % k for k in ("age", "gender", "race", "experience", "balance")}
    require("two label groups", len(s1_read(rels["balance"])) == 2)
    total = sum(int(num(rels["balance"], {"Type": t}, "n")) for t in ("Human", "AI"))
    require("the analyzed total is the one the text prints", Decimal(total) == macro_stored("SOneN"))
    n_age = int(num(rels["age"], {}, "n"))
    require("no more participants gave an age than were analyzed", n_age <= total)

    def share(n: int) -> str:
        return _fixed(Decimal(n) * 100 / Decimal(total), 1) + r"\%"

    def rows_for(rel: str, col: str, heading: str, rename=None) -> list:
        out, seen = [], 0
        for i, r in enumerate(s1_read(rel)):
            n = int(_number(r["n"], rel))
            seen += n
            answer = r[col] if rename is None else rename(r[col])
            out.append(r"%s & %s & %s (%s)\\" % (heading if i == 0 else "", answer,
                                                  val(rel, {col: r[col]}, "n", "count"), share(n)))
        require(f"{rel} counts no more people than were analyzed", seen <= total)
        return out

    a = rels["age"]
    age = r"Mean %s (SD %s); range %s to %s" % (val(a, {}, "mean_age", "dec2"), val(a, {}, "sd_age", "dec2"),
                                                 val(a, {}, "min_age", "count"), val(a, {}, "max_age", "count"))
    body = [r"Age in years & %s & %s (%s)\\" % (age, val(a, {}, "n", "count"), share(n_age)), r"\addlinespace[3pt]"]
    body += rows_for(rels["gender"], "Gender", "Gender") + [r"\addlinespace[3pt]"]
    body += rows_for(rels["race"], "Race", "Race",
                     rename=lambda s: "; ".join(part.strip() for part in s.split(",")))
    body += [r"\addlinespace[3pt]"]
    body += rows_for(rels["experience"], "Experience", "Formal artistic training") + [r"\addlinespace[3pt]"]
    body += rows_for(rels["balance"], "Type", "Label shown", rename=lambda s: s + " label")
    caption = (r"\textbf{Study~1: the analyzed participants.} Their ages, their answers to the background "
               r"questions at the end of the survey, and the label each was shown (descriptive).")
    notes = (r"SD, standard deviation, a measure of spread. Percentages are of all analyzed participants. "
             r"Answers are in the survey's own words. The gender question offered Male, Female, Other and "
             r"Prefer not to say. Participants could choose more than one race; a row that names several "
             r"answers, separated by semicolons, counts those who chose exactly that combination. Race was "
             r"self-reported, by choosing one or more of the survey's categories; it is reported to describe the "
             r"sample and to check that the label groups were alike (Supplementary Table~\ref{tab:supp_balance}), "
             r"and no analysis compared racial groups. The training "
             r"question asked for the level of `formal artistic training or experience, such as painting, "
             r"drawing, sculpture, ceramics, photography, and/or film-video'.")
    return s1_float("s1_demographics.tex", "Study 1: the analyzed participants", caption,
                    P("3.6cm") + P("8.9cm") + "r", [r"Question & Answer & Participants (\%)\\"], body, notes,
                    list(rels.values()))


# --- Background of the two label groups ---------------------------------------
def s1_balance() -> str:
    rel = S1 + "study1_balance.csv"
    rows = s1_read(rel)
    total = macro_stored("SOneN")
    require("four tests", len(rows) == 4)
    require("every test used every analyzed participant", {Decimal(r["n_used"]) for r in rows} == {total})
    race = {"variable": "^Race"}
    m = re.fullmatch(r"Fisher exact \(simulated p, B = ([0-9.e+]+)\)", text_of(rel, race, "test"))
    require("the race test names its number of simulated tables", m is not None)
    sims = _count(Decimal(str(float(m.group(1)))))
    require("race is tested on the four most common answers with all others pooled",
            len(text_of(rel, race, "levels").split("|")) == 5 and "collapsed" in text_of(rel, race, "levels"))
    age = {"variable": "Age", "test": "Welch t"}
    gen = {"variable": "Gender (Female/Male/Other)", "test": "Fisher exact"}
    exp_ = {"variable": "Artistic experience (ordinal 0-4)", "test": "Wilcoxon rank-sum"}
    require("the Wilcoxon statistic is a whole number", num(rel, exp_, "statistic") % 1 == 0)
    body = [
        r"Age & Welch's $t$ test & $t$(%s)~=~%s & %s\\" % (val(rel, age, "df", "df"),
                                                           val(rel, age, "statistic", "stat"), pval(rel, age, "p")),
        r"Gender (female, male, other) & Fisher's exact test & -- & %s\\" % pval(rel, gen, "p"),
        r"Formal artistic training (five ordered answers) & Wilcoxon rank-sum test & $W$~=~%s & %s\\"
        % (val(rel, exp_, "statistic", "count"), pval(rel, exp_, "p")),
        r"Race (the four most common answers; all others pooled) & Fisher's exact test & -- & %s\\"
        % pval(rel, race, "p"),
    ]
    caption = (r"\textbf{Study~1: did the two label groups differ in background?} Tests comparing the "
               r"participants shown the Human label with those shown the AI label, as a check that random "
               r"assignment produced similar groups (descriptive; the four tests are not corrected).")
    notes = (r"Welch's $t$ test compares two means without assuming that the two groups vary equally; its "
             r"degrees of freedom are in parentheses. Fisher's exact test is a test for counts in small tables; "
             r"for race, its $p$-value was simulated from " + sims + r" random tables. The Wilcoxon rank-sum "
             r"test compares two groups' ordered answers by their ranks; $W$ is its statistic. Every analyzed "
             r"participant enters every test.")
    return s1_float("s1_balance.tex", "Study 1: background of the two label groups", caption,
                    P("7.0cm") + P("4.0cm") + "ll", [r"Background measure & Test & Statistic & $p$\\"], body, notes,
                    [rel])


# --- The four confirmatory tests -----------------------------------------------
def s1_holm_family() -> str:
    rel = S1 + "study1_confirmatory_family.csv"
    anova = S1 + "study1_joint_model_anova.csv"
    h4file = S1 + "study1_h4_variance_test.csv"
    rows = s1_read(rel)
    require("four tests in the family", len(rows) == 4 and {r["family_size"] for r in rows} == {"4"})
    require("every fit converged", {r["fits_converged"] for r in rows} == {"TRUE"})
    require("all four pass after Holm's correction", {r["survives_holm_at_05"] for r in rows} == {"TRUE"})
    require("H4 as registered is not supported", {r["h4_supported_both_dimensions"] for r in s1_read(h4file)} == {"FALSE"})
    c, e = {"hypothesis": "H1", "test": "~creativity"}, {"hypothesis": "H1", "test": "~effort"}
    h2, h4 = {"hypothesis": "H2"}, {"hypothesis": "H4"}
    for w, kind in ((c, "t"), (e, "t"), (h2, "F"), (h4, "chi-square")):
        require(f"{w} reports a {kind} statistic", text_of(rel, w, "statistic_type") == kind)
    require("the H4 row is for creativity", "creativity" in text_of(rel, h4, "test"))
    # H2's F test is the joint model's label-by-rating term, whose table holds the denominator df.
    term = {"term": "Type:dimension"}
    require("the H2 F test is the joint model's label-by-rating term",
            abs(num(anova, term, "F value") - num(rel, h2, "statistic")) < Decimal("1e-9")
            and abs(num(anova, term, "Pr(>F)") - num(rel, h2, "p_raw")) < Decimal("1e-15")
            and num(anova, term, "NumDF") == num(rel, h2, "df"))

    def est_se(w):
        return "%s (%s)" % (val(rel, w, "estimate", "dec2"), val(rel, w, "se", "dec2"))

    def ps(w):
        return "%s & %s" % (pval(rel, w, "p_raw"), pval(rel, w, "p_holm"))

    body = [
        r"H1, creativity: the label's penalty & %s & $t$(%s)~=~%s & %s\\"
        % (est_se(c), val(rel, c, "df", "df"), val(rel, c, "statistic", "stat"), ps(c)),
        r"H1, effort: the label's penalty & %s & $t$(%s)~=~%s & %s\\"
        % (est_se(e), val(rel, e, "df", "df"), val(rel, e, "statistic", "stat"), ps(e)),
        r"H2: the penalty on effort minus the penalty on creativity & %s & $F$(%s,~%s)~=~%s & %s\\"
        % (est_se(h2), val(rel, h2, "df", "df"), val(anova, term, "DenDF", "df"), val(rel, h2, "statistic", "stat"),
           ps(h2)),
        r"H4, between-person part, creativity: AI-to-Human ratio of the variance between "
        r"people\textsuperscript{a} & %s & $\chi^2$(%s)~=~%s & %s\\"
        % (val(rel, h4, "estimate", "dec2"), val(rel, h4, "df", "df"), val(rel, h4, "statistic", "stat"), ps(h4)),
    ]
    caption = (r"\textbf{Study~1: the four confirmatory tests and Holm's correction.} The registration named "
               r"these four as its confirmatory tests and corrected them together by Holm's "
               r"method (registered confirmatory). All four pass after the correction. H1 and H2 are supported; "
               r"H4 is not, because it needed more than this one test (note a).")
    notes = (r"The penalty is the Human-label mean rating minus the AI-label mean rating, averaged with equal "
             r"weight over images with and without a human figure, in points on the 1-to-5 scale. SE, standard "
             r"error. Degrees of freedom are in parentheses. Holm's method orders the four $p$-values from "
             r"smallest to largest and compares each with a threshold that starts strict and relaxes as tests "
             r"pass, so that the chance of calling any of the four significant by mistake stays at .05; the "
             r"Holm $p$ is each $p$-value adjusted in that way. The H4 row is a likelihood-ratio test, which "
             r"compares a model in which the variance between people differs by label with one in which it does "
             r"not. It is shown for creativity, the weaker of the two ratings, and its estimate has no standard "
             r"error. \textsuperscript{a}This row is only the between-person part of H4. H4 as registered also "
             r"required a smaller variance within people under the AI label, with both ratios' resampled "
             r"intervals on the predicted side of 1, on both ratings. That held on effort and not on creativity, "
             r"so H4 was not supported (Supplementary Note~1).")
    return s1_float("s1_holm_family.tex", "Study 1: the four confirmatory tests", caption,
                    P("6.4cm") + "llll", [r"Test & Estimate (SE) & Statistic & $p$ & Holm $p$\\"], body, notes,
                    [rel, anova, h4file])


# --- Every estimate of the primary model ----------------------------------------
def s1_full_lmm() -> str:
    rel = S1 + "study1_lmm_fixed_effects.csv"
    rows = s1_read(rel)
    require("eight fixed effects from fits that converged and were not singular",
            len(rows) == 8 and {r["converged"] for r in rows} == {"TRUE"} and {r["singular"] for r in rows} == {"FALSE"})
    terms = [("(Intercept)", "Baseline: Human label, images without a figure"),
             ("TypeAI", "AI label, images without a figure (AI minus Human)"),
             ("stimulus_typeFigure", "Images with a figure, Human label (with minus without)"),
             ("TypeAI:stimulus_typeFigure", "Label by kind of image (the H3 quantity)")]
    body = []
    for dim, name in RATINGS:
        body.append(group(name, 4))
        for term, label in terms:
            w = {"dimension": dim, "term": term}
            body.append(r"%s & %s (%s) & %s & %s\\" % (label, val(rel, w, "estimate", "dec2"),
                                                       val(rel, w, "std.error", "dec2"),
                                                       span(rel, w, "conf.low", "conf.high", "dec2"),
                                                       pval(rel, w, "p.value")))
        body.append(r"\addlinespace[3pt]")
    body.pop()
    caption = (r"\textbf{Study~1: every estimate of the primary model of each rating.} The registered model, "
               r"fitted to each rating separately; its coefficients are descriptive. The registered H1 test is not "
               r"the AI-label row here, which is the effect for images without a figure only and runs AI minus "
               r"Human, but the penalty averaged over both kinds of image (Supplementary "
               r"Table~\ref{tab:supp_holm_family}).")
    notes = (r"Estimates are in points on the 1-to-5 scale. The model is a linear mixed model, which gives each "
             r"participant and each image a baseline of its own; the Human label and images without a human "
             r"figure are its reference levels. The label-by-kind-of-image row is how much the AI label's effect "
             r"changes when the image has a figure, the quantity H3 tests. SE, standard error; CI, confidence "
             r"interval. The $p$-values use Satterthwaite's approximation to the degrees of freedom.")
    return s1_float("s1_full_lmm.tex", "Study 1: every estimate of the primary model", caption,
                    P("8.8cm") + "lll", [r"Term & Estimate (SE) & 95\% CI & $p$\\"], body, notes, [rel])


# --- Robustness of the penalty --------------------------------------------------
def s1_robustness() -> str:
    fam = S1 + "study1_confirmatory_family.csv"
    spec = S1 + "study1_specification_curve.csv"
    gauss = S1 + "study1_brms_primary_fixed.csv"
    ordl = S1 + "study1_brms_cumulative_fixed.csv"
    lmm = S1 + "study1_lmm_fixed_effects.csv"
    eqv = S1 + "study1_equivalence_sensitivity.csv"
    cells = {"h1": [], "spec": [], "gauss": [], "ord": [], "eq": []}
    n_spec_total = 0
    for dim, _name in RATINGS:
        w = {"hypothesis": "H1", "test": "~" + dim}
        cells["h1"].append(r"%s (SE %s); $t$(%s)~=~%s, %s; Holm %s"
                           % (val(fam, w, "estimate", "dec2"), val(fam, w, "se", "dec2"), val(fam, w, "df", "df"),
                              val(fam, w, "statistic", "stat"), pval(fam, w, "p_raw"), pval(fam, w, "p_holm")))
        rows = [r for r in s1_read(spec) if r["dimension"] == dim]
        require(f"the specification curve for {dim} names one quantity, the H1 contrast",
                {r["estimand"] for r in rows} == {"H1 contrast: Human - AI, averaged over image kind"})
        ests = [Decimal(r["estimate"]) for r in rows if r["estimate"] not in ("", "NA")]
        ps = sorted(Decimal(r["p"]) for r in rows if r["p"] not in ("", "NA"))
        n_conv = sum(r["converged"] == "TRUE" for r in rows)
        n_spec_total += len(rows)
        mid = len(ps) // 2
        median_p = ps[mid] if len(ps) % 2 else (ps[mid - 1] + ps[mid]) / 2
        cells["spec"].append(
            r"%d of %d specifications estimated, %d recorded as converged; %d positive and %d negative; %d with "
            r"$p$ below .05; median $p$~%s" % (len(ests), len(rows), n_conv, sum(x > 0 for x in ests),
                                               sum(x < 0 for x in ests), sum(x < Decimal("0.05") for x in ps),
                                               _p(median_p).replace("} ", "}~")))
        g = {"dimension": dim, "term": "TypeAI"}
        require(f"the Gaussian refit of {dim} is usable", text_of(gauss, g, "fit_status") == "ok"
                and text_of(gauss, g, "n_divergent") == "0")
        diff = abs(num(gauss, g, "mean") - num(lmm, {"dimension": dim, "term": "TypeAI"}, "estimate"))
        cells["gauss"].append(r"Posterior mean %s (95\%% credible interval %s); %s points from the primary "
                              r"model's estimate" % (val(gauss, g, "mean", "dec2"),
                                                     span(gauss, g, "ci_lo", "ci_hi", "dec2"), _fixed(diff, 2)))
        o = {"dimension": dim + "_cumulative", "term": "TypeAI"}
        require(f"the ordinal refit of {dim} is usable", text_of(ordl, o, "fit_status") == "ok"
                and text_of(ordl, o, "n_divergent") == "0")
        cells["ord"].append(r"Posterior mean %s (95\%% credible interval %s)"
                            % (val(ordl, o, "mean", "es"), span(ordl, o, "ci_lo", "ci_hi", "es")))
        parts = []
        for bound in ("0.3", "0.5"):
            q = {"dimension": dim, "bound": bound, "method": "^two one-sided tests"}
            require("the wider bounds are not the registered one", text_of(eqv, q, "bound_is_registered") == "FALSE")
            reading = text_of(eqv, q, "reading")
            require(f"the reading at {bound} is one this table can state",
                    reading in ("the 90% interval lies inside this bound",))
            parts.append(r"inside $\pm$%s (%s)" % (val(eqv, q, "bound", "dec2"), pval(eqv, q, "tost_p")))
        q3 = {"dimension": dim, "bound": "0.3", "method": "^two one-sided tests"}
        q5 = {"dimension": dim, "bound": "0.5", "method": "^two one-sided tests"}
        require("both bounds test one estimate and one interval",
                all(num(eqv, q3, k) == num(eqv, q5, k) for k in ("estimate", "ci90_lo", "ci90_hi")))
        cells["eq"].append(r"%s (90\%% CI %s); %s and %s" % (val(eqv, q3, "estimate", "dec2"),
                                                              span(eqv, q3, "ci90_lo", "ci90_hi", "dec2"),
                                                              parts[0], parts[1]))
    require("the specification curve has the number of specifications the text prints",
            Decimal(n_spec_total) == macro_stored("SOneSpecNTotal"))
    labels = [
        ("h1", r"The H1 contrast, primary model", "registered confirmatory"),
        ("spec", r"Specification curve: the H1 contrast refitted under every combination of the registered "
                 r"analysis choices", "registered secondary; the registration calls it descriptive"),
        ("gauss", r"Bayesian refit, linear: the AI-label effect for images without a figure (AI minus Human)",
         "registered secondary"),
        ("ord", r"Bayesian refit, ordinal: the same effect, in log-odds", "registered secondary"),
        ("eq", r"Equivalence at wider bounds: the label-by-kind-of-image interaction, the H3 quantity",
         r"descriptive; no verdict on H3"),
    ]
    body = []
    for key, label, status in labels:
        body.append(r"%s \newline \textit{(%s)} & %s & %s\\" % (label, status, cells[key][0], cells[key][1]))
        body.append(r"\addlinespace[4pt]")
    body.pop()
    caption = (r"\textbf{Study~1: robustness checks on the label's penalty.} Each row refits or re-tests the "
               r"H1 contrast, or the related quantity the row names, under another analysis that the "
               r"registration lists. The status of each row is in parentheses; none of these checks carries a "
               r"verdict of its own.")
    notes = (r"The H1 contrast is the Human-label mean rating minus the AI-label mean rating, averaged with equal "
             r"weight over images with and without a human figure, in points on the 1-to-5 scale. SE, standard "
             r"error; CI, confidence interval; $\pm$, plus or minus, in rating points. The specification curve "
             r"crosses the registered choices of random effects, model family, covariates and level of "
             r"aggregation; its estimates are on each family's own scale, so only their signs are counted. A "
             r"Bayesian refit estimates the model by combining the data with prior assumptions and summarizes "
             r"each quantity as a distribution; the credible interval holds the middle 95\% of it. The two "
             r"Bayesian rows report the AI-label coefficient of Supplementary Table~\ref{tab:supp_lmm}, not the "
             r"H1 contrast; the text gives the H1 contrast from the same refits. An ordinal model treats the "
             r"five answers as ordered categories, and log-odds are the logarithm of the odds of a higher "
             r"answer. An equivalence test asks whether an effect is shown to lie inside a bound; its $p$ is the "
             r"larger of two one-sided tests. The last row applies such tests to the H3 quantity at wider "
             r"bounds than the registered one, as description, and carries no verdict on H3; the registered "
             r"test of H3, at $\pm$0.20, is in Supplementary Note~1.")
    return s1_float("s1_robustness.tex", "Study 1: robustness checks on the penalty", caption,
                    P("4.4cm") + P("5.15cm") + P("5.15cm"), [r"Check (status) & Creativity & Effort\\"], body,
                    notes, [fam, spec, gauss, ordl, lmm, eqv], size=r"\footnotesize")


# --- Leaving out one participant or one image -----------------------------------
def s1_influence() -> str:
    files = [(S1 + "study1_influence_lopo.csv", "Each participant"), (S1 + "study1_influence_loso.csv", "Each image")]
    body, all_positive = [], True
    for rel, unit in files:
        rows = s1_read(rel)
        require(f"{rel} tracks the H1 contrast", len({r["quantity"] for r in rows}) == 1
                and rows[0]["quantity"].startswith("H1"))
        for j, (dim, name) in enumerate(RATINGS):
            sub = [r for r in rows if r["dimension"] == dim]
            usable = [r for r in sub if r["delta"] not in ("", "NA")]
            deltas = [abs(Decimal(r["delta"])) for r in usable]
            all_positive = all_positive and all(Decimal(r["estimate"]) > 0 for r in usable)
            require(f"{rel} {dim} has refits", len(deltas) > 0)
            body.append(r"%s & %s & %s & %s & %s & %s\\"
                        % (unit if j == 0 else "", name, _count(Decimal(len(sub))), _count(Decimal(len(usable))),
                           _fixed(max(deltas), 2), _fixed(sum(deltas) / len(deltas), 2)))
        body.append(r"\addlinespace[3pt]")
    body.pop()
    require("every refit kept the penalty above zero", all_positive)
    caption = (r"\textbf{Study~1: does any one participant or image carry the penalty?} The primary model was "
               r"refitted once without each participant and once without each image (registered secondary). "
               r"The table gives the largest and the average size of the resulting change in the H1 contrast. "
               r"Every refit kept the penalty above zero.")
    notes = (r"The H1 contrast is the Human-label mean rating minus the AI-label mean rating, averaged with "
             r"equal weight over images with and without a human figure. Changes are in points on the 1-to-5 "
             r"scale, without regard to sign. A usable refit is one that converged without error. The analysis "
             r"tables \nolinkurl{study1_influence_lopo.csv} and \nolinkurl{study1_influence_loso.csv} give the "
             r"estimate from every refit.")
    return s1_float("s1_influence.tex", "Study 1: leaving out one participant or one image", caption, "llrrrr",
                    [r"Left out in turn & Rating & Refits & Usable & Largest change & Average change\\"], body, notes,
                    [rel for rel, _ in files])


# --- The differently worded effort item -----------------------------------------
def s1_item_sensitivity() -> str:
    rel = S1 + "study1_item_sensitivity.csv"
    rows = s1_read(rel)
    require("every refit converged and none was singular",
            {r["converged"] for r in rows} == {"TRUE"} and {r["singular"] for r in rows} == {"FALSE"})
    samples = [("full sample", "None"),
               ("1FigureEff removed (effort rating of Figure_1)", "The effort rating of the first image with a figure"),
               ("Figure_1 removed from both dimensions", "The first image with a figure, on both ratings")]
    body, shown = [], 0
    for hyp, label in (("H1", "H1: the penalty on effort"),
                       ("H2", "H2: the penalty on effort minus the penalty on creativity")):
        body.append(group(label, 3))
        for sample, plain in samples:
            w = {"hypothesis": hyp, "sample": sample}
            if not any(r["hypothesis"] == hyp and r["sample"] == sample for r in rows):
                continue
            body.append(r"%s & %s (%s) & %s\\" % (plain, val(rel, w, "estimate", "dec2"), val(rel, w, "se", "dec2"),
                                                  span(rel, w, "ci_low", "ci_high", "dec2")))
            shown += 1
        body.append(r"\addlinespace[3pt]")
    body.pop()
    require("five rows, all shown", len(rows) == 5 and shown == 5)
    caption = (r"\textbf{Study~1: the differently worded effort item set aside.} One effort item, for the first "
               r"image with a figure, labeled its top two answers differently from the other nine. The table gives "
               r"H1 on effort and H2 recomputed without that item's ratings, and H2 without that image on either "
               r"rating. The "
               r"registration names this as a sensitivity check, settled after the September 2026 estimates had "
               r"been read (registered secondary; no verdict).")
    notes = (r"Estimates are in points on the 1-to-5 scale, averaged with equal weight over images with and "
             r"without a human figure; the penalty is the Human-label mean minus the AI-label mean. SE, standard "
             r"error; CI, confidence interval. On that item the top two answers read `A lot of effort involved' "
             r"and `Significant effort involved'; on the other nine, `Significant effort involved' and `A great "
             r"deal of effort involved'. Every item is scored 1 to 5 by the position of the answer chosen.")
    return s1_float("s1_item_sensitivity.tex", "Study 1: the differently worded effort item set aside", caption,
                    P("10.2cm") + "ll", [r"Ratings left out & Estimate (SE) & 95\% CI\\"],
                    body, notes, [rel])


# --- Effect sizes ---------------------------------------------------------------
def s1_bootstrap_d() -> str:
    rel = S1 + "study1_bootstrap_d.csv"
    rows = s1_read(rel)
    require("one row per rating, with one sample, one number of resamples and one seed",
            len(rows) == 2 and len({(r["n_human"], r["n_ai"], r["B"], r["seed"]) for r in rows}) == 1)
    body = []
    for dim, name in RATINGS:
        w = {"dimension": dim}
        body.append(r"%s & %s & %s & %s\\" % (name, val(rel, w, "d", "es"), span(rel, w, "ci_lo", "ci_hi", "es"),
                                              val(rel, w, "d_model_based", "es")))
    w = {"dimension": "creativity"}
    caption = (r"\textbf{Study~1: effect sizes of the label's penalty.} The registered effect sizes (registered "
               r"secondary; no verdict). Averaging each person's ten ratings first removes much of the variation, "
               r"so $d$ on participants' mean ratings is larger than the model-based $d$ by construction and "
               r"cannot be read against the usual small, medium and large benchmarks. The model-based $d$ is the "
               r"one to compare with other studies.")
    notes = (r"Cohen's $d$ here is the Human-label mean minus the AI-label mean, divided by the pooled standard "
             r"deviation of participants' mean ratings (" + val(rel, w, "n_human", "count") + r" Human-label and "
             + val(rel, w, "n_ai", "count") + r" AI-label participants). Its 95\% confidence interval (CI) comes "
             r"from " + val(rel, w, "B", "count") + r" resamples of participants drawn within each label group. "
             r"The model-based $d$ divides the H1 contrast by the square root of the primary model's summed "
             r"variances (between participants, between images, and the rest), which puts it on the scale of a "
             r"single rating.")
    return s1_float("s1_bootstrap_d.tex", "Study 1: effect sizes", caption, "lccc",
                    [r"Rating & $d$ on participants' means & 95\% CI & Model-based $d$\\"], body, notes, [rel])


# --- What the Human-label group's explanations mentioned -------------------------
def s1_text_rates() -> str:
    eff = S1 + "study1_text_effort_prevalence.csv"
    cre = S1 + "study1_text_creativity_prevalence.csv"
    lists = [
        (eff, "Effort explanations", [("detail", "Visible detail in the picture"), ("time", "Time and industriousness"),
                                       ("skill", "Skill and training"),
                                       ("none_of_the_three", "None of these three")]),
        (cre, "Creativity explanations", [("concept", "The idea behind the work"),
                                           ("novelty_asserted", "Says the work looks familiar"),
                                           ("novelty_negated", "Says the work does not look familiar"),
                                           ("novelty_either", "Raises familiarity either way"),
                                           ("execution", "Visible detail and rendering"),
                                           ("none_of_the_three", "None of the idea, familiarity or detail")]),
    ]
    body, sizes = [], set()
    for rel, heading, items in lists:
        rows = s1_read(rel)
        require(f"{rel} holds the Human label's rows only", {r["arm"] for r in rows} == {"Human"})
        require(f"{rel} has the expected measures", [r["quantity"] for r in rows] == [q for q, _ in items])
        sizes |= {(r["n_responses"], r["n_participants"], r["B"], r["n_valid"]) for r in rows}
        body.append(group(heading, 3))
        for q, label in items:
            w = {"quantity": q}
            body.append(r"%s & %s & %s\\" % (label, val(rel, w, "estimate", "pct"), span(rel, w, "ci_lo", "ci_hi", "pct")))
        body.append(r"\addlinespace[3pt]")
    body.pop()
    require("every share has the same base and the same resampling", len(sizes) == 1)
    n_resp, n_part, boots, _ = sizes.pop()
    caption = (r"\textbf{Study~1: what the Human-label group's explanations mentioned.} The share of that "
               r"group's explanations of each rating that each word list flagged (descriptive). One explanation "
               r"can mention several things, so the shares need not sum to 100\%.")
    notes = (r"Each share is of the " + _count(Decimal(n_resp)) + r" explanations that the " + _count(Decimal(n_part))
             + r" Human-label participants wrote for that rating. CI, confidence interval, from "
             + _count(Decimal(boots)) + r" resamples of participants. A word list is a fixed list of words and "
             r"phrases, applied by a script that saw neither the label nor the rating (Section~\ref{sec:suppA-text}).")
    return s1_float("s1_text_rates.tex", "Study 1: what the Human-label explanations mentioned", caption,
                    P("8.6cm") + "rl", [r"Word list & Share & 95\% CI\\"], body, notes, [eff, cre])


# --- Prompting talk by label ----------------------------------------------------
def s1_prompt_talk() -> str:
    rel = S1 + "study1_text_prompt_by_arm.csv"
    rows = s1_read(rel)
    require("two rows, effort explanations only", len(rows) == 2 and {r["dimension"] for r in rows} == {"effort"})
    require("one number of resamples", len({(r["B"], r["n_valid"]) for r in rows}) == 1)
    body = [r"%s label & %s & %s\\" % (arm, val(rel, {"arm": arm}, "estimate", "pct"),
                                        span(rel, {"arm": arm}, "ci_lo", "ci_hi", "pct")) for arm in ("Human", "AI")]
    caption = (r"\textbf{Study~1: effort explanations that mention prompting or machines, by label} "
               r"(descriptive). Under the AI label such talk restates what participants were told. Under the "
               r"Human label a mention is not a rejection of the account, since it can compare, deny or wonder.")
    notes = (r"The share of each group's effort explanations that the prompting word list flagged: any mention "
             r"of a machine, a prompt or a generated image. CI, confidence interval, from "
             + _count(Decimal(rows[0]["B"])) + r" resamples of participants. The test of prompting talk on "
             r"effort against creativity, under the AI label, is in Supplementary Table~\ref{tab:suppA-denotation}.")
    return s1_float("s1_prompt_talk.tex", "Study 1: effort explanations that mention prompting or machines",
                    caption, "lrl", [r"Label & Share of effort explanations & 95\% CI\\"], body, notes, [rel])


# --- The word-meaning tests with a random slope -----------------------------------
def s1_denotation_slope() -> str:
    rel = S1 + "study1_text_denotation_slope_sensitivity.csv"
    rows = s1_read(rel)
    require("every refit converged and was not singular",
            {r["status"] for r in rows} == {"ok"} and all("converged; not singular" in r["note"] for r in rows))
    tests = [("detail vs time", "Effort, Human label", "Visible detail against time", "DetailVsTime"),
             ("detail vs skill", "Effort, Human label", "Visible detail against skill", "DetailVsSkill"),
             ("concept vs execution", "Creativity, Human label", "Concept against visible detail (execution)",
              "ConceptVsExecution"),
             ("concept vs novelty", "Creativity, Human label", "Concept against prior exposure (novelty)",
              "ConceptVsNovelty"),
             ("prompt talk, effort vs creativity", "AI label, effort against creativity", "Prompting or machines",
              "PromptEffortVsCreat")]
    require("five tests", len(rows) == len(tests))
    body = []
    for key, expl, comp, macro in tests:
        w = {"comparison": key}
        reg_est = val(rel, w, "registered_estimate_log_odds", "es")
        reg_se = val(rel, w, "registered_se", "es")
        # The registered estimate and its SE are the ones Supplementary Table~\ref{tab:suppA-denotation} prints.
        require(f"the registered estimate of {key} is the one the macros hold",
                num(rel, w, "registered_estimate_log_odds") == macro_stored("SOneText%sEst" % macro)
                and num(rel, w, "registered_se") == macro_stored("SOneText%sSE" % macro))
        body.append(r"%s & %s & %s (%s) & %s (%s) & %s & %s\\"
                    % (expl, comp, reg_est, reg_se, val(rel, w, "estimate_log_odds", "es"), val(rel, w, "se", "es"),
                       val(rel, w, "z", "stat"), pval(rel, w, "p_raw")))
    caption = (r"\textbf{Study~1: the five word-meaning tests with each person's difference free to vary.} The "
               r"registered model gives each participant a baseline of their own but one difference between the "
               r"two lists that all participants share; the refit lets that difference vary from person to person. "
               r"The registration names this refit as a sensitivity check that cannot change a reading (exploratory; "
               r"its $p$-values are uncorrected). Every estimate kept its sign.")
    notes = (r"Each cell gives an estimate with its standard error (SE) in parentheses, from the registered "
             r"model and from the refit. Estimates are differences in log-odds, the logarithm of the odds that "
             r"the first list flags an explanation rather than the second; a positive value is the predicted "
             r"direction. $z$ and $p$ test the refit's estimate against zero. Every refit converged and none was "
             r"singular (a variance or correlation estimated at the edge of its range). Supplementary "
             r"Table~\ref{tab:suppA-denotation} gives the registered tests with their corrected $p$-values.")
    require("every refit kept its sign", all((num(rel, {"comparison": k}, "estimate_log_odds") > 0)
                                           == (num(rel, {"comparison": k}, "registered_estimate_log_odds") > 0)
                                           for k, *_ in tests))
    return s1_float("s1_denotation_slope_sensitivity.tex", "Study 1: the word-meaning tests with a random slope",
                    caption, P("3.9cm") + P("5.0cm") + "llrl",
                    [r"Explanations & Comparison & Registered & Refit & $z$ & $p$\\"], body, notes, [rel],
                    size=r"\footnotesize")


# --- Recovering the rating and the label from the words --------------------------
def s1_text_recoverability() -> str:
    rel = S1 + "study1_text_recoverability.csv"
    rows = s1_read(rel)
    require("every fit has status ok", {r["status"] for r in rows} == {"ok"})
    require("one set of folds, shuffles and resamples",
            len({(r["n_folds"], r["n_boot"], r["n_valid"]) for r in rows}) == 1
            and {r["n_perm"] for r in rows if r["n_perm"] != "NA"} == {"200"})
    items = [({"target": "rating", "predictors": "words"}, "The rating, from the words", "$r$", True, "es"),
             ({"target": "arm", "predictors": "words"}, "The label, from the words", "AUC", True, "es"),
             ({"target": "arm", "predictors": "rating"}, "The label, from the rating", "AUC", True, "es"),
             ({"target": "arm", "predictors": "rating plus words"}, "The label, from the rating and the words", "AUC",
              False, "es"),
             ({"target": "arm", "predictors": "^incremental AUC"}, "What the words add: rating and words, minus "
              "rating alone", "AUC difference", False, "dec3")]
    body = []
    for dim, name in RATINGS:
        body.append(group(name + " explanations", 5))
        for where, label, stat, has_null, fmt in items:
            w = dict(where, dimension=dim)
            null = val(rel, w, "null_95th", "es") if has_null else "--"
            body.append(r"%s & %s & %s & %s & %s\\" % (label, stat, val(rel, w, "estimate", fmt),
                                                       span(rel, w, "ci_low", "ci_high", fmt), null))
        # The registered readings: recovery present (above the shuffled baseline, interval clear of
        # chance) and words that add to the rating (the difference's interval above zero).
        r_w = dict(items[0][0], dimension=dim)
        a_w = dict(items[1][0], dimension=dim)
        i_w = dict(items[4][0], dimension=dim)
        require(f"{dim}: the rating is recovered", num(rel, r_w, "estimate") > num(rel, r_w, "null_95th")
                and num(rel, r_w, "ci_low") > 0)
        require(f"{dim}: the label is recovered", num(rel, a_w, "estimate") > num(rel, a_w, "null_95th")
                and num(rel, a_w, "ci_low") > Decimal("0.5"))
        require(f"{dim}: the words add to the rating", num(rel, i_w, "ci_low") > 0)
        body.append(r"\addlinespace[3pt]")
    body.pop()
    first = {"dimension": "creativity", "target": "rating", "predictors": "words"}
    caption = (r"\textbf{Study~1: can the rating and the label be recovered from the words?} The first of the "
               r"two checks run in every study (registered secondary). Each model was fitted to some "
               r"participants' explanations and scored on the explanations of participants left out of the fit. "
               r"By the registered reading, both the rating and the label are recovered on both ratings, and the "
               r"words add to the rating in telling the two label groups apart.")
    notes = (r"$r$, the correlation between predicted and observed ratings (0, no relation; 1, a perfect one). "
             r"AUC, the chance that a randomly chosen AI-label explanation is scored as more AI-like than a "
             r"randomly chosen Human-label one (0.5 is chance; 1, perfect separation). The models are ridge "
             r"regressions, which shrink their many word weights toward zero, on counts of each explanation's "
             r"content words. Participants were split into " + val(rel, first, "n_folds", "count") + r" groups, and "
             r"each group in turn was left out of the fit and scored, so that no participant's explanations were "
             r"both fitted and scored. CI, confidence interval, from "
             + val(rel, first, "n_boot", "count") + r" resamples of participants. The shuffled baseline is the "
             r"95th percentile of the statistic over " + val(rel, first, "n_perm", "count") + r" reruns with the "
             r"outcome shuffled: the rating among each participant's own explanations, the label across "
             r"participants. An estimate above it is read as signal. Every explanation was written after its "
             r"rating, so recovering the rating is not evidence that the words produced it.")
    return s1_float("s1_text_recoverability.tex", "Study 1: the rating and the label recovered from the words",
                    caption, P("6.4cm") + "llll",
                    [r"What is predicted & Statistic & Estimate & 95\% CI & Shuffled baseline\\"], body, notes, [rel])


# --- Reuse of one's own words ---------------------------------------------------
def s1_text_selfsimilarity() -> str:
    rel = S1 + "study1_text_selfsimilarity_by_arm.csv"
    rows = s1_read(rel)
    require("every estimate has status ok", {r["status"] for r in rows} == {"ok"})
    require("one resampling scheme", len({(r["B"], r["n_valid"], r["seed"]) for r in rows}) == 1)
    measures = [("self_overlap", "Overlap among a person's own explanations", "dec3"),
                ("stranger_overlap", "Overlap with others' explanations of the same image", "dec3"),
                ("self_minus_stranger", "Own overlap minus others' overlap", "dec3"),
                ("mean_words", "Content words per explanation", "dec2")]
    readings = {"supported": "supported", "inconclusive": "inconclusive", "opposite direction": "opposite direction"}
    body = []
    for dim, name in RATINGS:
        body.append(group(name + " explanations", 3))
        for key, label, fmt in measures:
            cells = []
            for arm in ("Human", "AI"):
                w = {"dimension": dim, "quantity": "%s_%s" % (key, arm)}
                cells.append("%s (%s)" % (val(rel, w, "estimate", fmt), span(rel, w, "ci_lo", "ci_hi", fmt)))
            body.append(r"%s & %s & %s\\" % (label, cells[0], cells[1]))
        w = {"dimension": dim, "role": "registered comparison"}
        require("the comparison is AI minus Human", text_of(rel, w, "quantity") == "arm_difference_AI_minus_Human")
        reading = readings[text_of(rel, w, "reading")]
        body.append(r"\multicolumn{3}{@{}p{\textwidth}@{}}{\raggedright Registered comparison (AI minus Human in own "
                    r"minus others' overlap, at equal length): %s (95\%% CI %s); %s; Holm %s; %s.}\\"
                    % (val(rel, w, "estimate", "dec3"), span(rel, w, "ci_lo", "ci_hi", "dec3"), pval(rel, w, "p_raw"),
                       pval(rel, w, "p_holm"), reading))
        body.append(r"\addlinespace[3pt]")
    body.pop()
    require("the readings are supported on effort and inconclusive on creativity",
            text_of(rel, {"dimension": "effort", "role": "registered comparison"}, "reading") == "supported"
            and text_of(rel, {"dimension": "creativity", "role": "registered comparison"}, "reading") == "inconclusive")
    caption = (r"\textbf{Study~1: how much each person reused their own words, by label.} The second of the two "
               r"checks run in every study (registered secondary). It predicted that participants shown the AI "
               r"label would reuse their own words more. By the registered reading the prediction is "
               r"supported on effort and inconclusive on creativity, which is not evidence that the two groups "
               r"reuse their words equally.")
    notes = (r"Overlap is the share of content words that two explanations have in common: the words in both "
             r"divided by the words in either (0, none in common; 1, the same words). A person's own overlap is "
             r"averaged over all pairs of that person's explanations of one rating; others' overlap pairs each of "
             r"those explanations with other participants' explanations of the same image and rating. The "
             r"registered comparison is a regression of own minus others' overlap on the label, holding the mean "
             r"number of content words constant, because overlap falls as texts get longer. CI, confidence "
             r"interval, from " + _count(Decimal(rows[0]["B"])) + r" resamples of participants within each label "
             r"group, with others' overlap rebuilt each time. Holm's correction runs over the two ratings. "
             r"Supported means that the corrected test rejected no difference, in the predicted direction; "
             r"inconclusive, that it did not.")
    return s1_float("s1_text_selfsimilarity.tex", "Study 1: reuse of one's own words, by label", caption,
                    P("7.6cm") + "ll", [r"Measure & Human label (95\% CI) & AI label (95\% CI)\\"], body, notes, [rel])


# --- How the number of topics was chosen -----------------------------------------
def s1_text_topics_stability() -> str:
    rel = S1 + "text_topics_stability.csv"
    rows = s1_read(rel)
    ks = sorted({int(r["k"]) for r in rows})
    chosen = {}
    for dim, _ in RATINGS:
        sub = [r for r in rows if r["dimension"] == dim]
        require(f"{dim}: one chosen number of topics", sum(r["chosen"] == "True" for r in sub) == 1)
        best = max(sub, key=lambda r: (round(float(r["stability_mean"]), 3), -int(r["k"])))
        require(f"{dim}: the chosen number is the most stable, the smaller on a tie", best["chosen"] == "True")
        chosen[dim] = int(best["k"])
    body = []
    for k in ks:
        cells = []
        for dim, _ in RATINGS:
            w = {"dimension": dim, "k": str(k)}
            cell = "%s (%s)" % (val(rel, w, "stability_mean", "es"), val(rel, w, "stability_sd", "es"))
            cells.append(r"\textbf{%s}" % cell if chosen[dim] == k else cell)
        body.append(r"%d & %s & %s\\" % (k, cells[0], cells[1]))
    same = chosen["creativity"] == chosen["effort"]
    used = ("%d for both ratings" % chosen["creativity"]) if same else (
        "%d for creativity and %d for effort" % (chosen["creativity"], chosen["effort"]))
    caption = (r"\textbf{Study~1: how the number of topics was chosen.} For each number of topics from %d to %d, "
               r"how stable the topic model of each rating's explanations was (exploratory). The most stable "
               r"number was used: %s (in bold)." % (ks[0], ks[-1], used))
    notes = (r"A topic model (here non-negative matrix factorization) finds groups of words that tend to occur "
             r"together. At each number of topics it was refitted ten times, each time on a random 80\% of the "
             r"participants. The topics of two refits were matched one to one, and their agreement is the mean "
             r"cosine similarity of the matched topics' word weights (1 when two topics weight the same words in "
             r"the same proportions, 0 when they share no word). Stability is that agreement averaged over every "
             r"pair of refits; SD, its standard deviation. A tie at three decimals goes to the smaller number.")
    return s1_float("s1_text_topics_stability.tex", "Study 1: how the number of topics was chosen", caption, "lll",
                    [r"Number of topics & Creativity: stability (SD) & Effort: stability (SD)\\"], body, notes, [rel])


S1_BUILDERS = {
    "s1_exclusions.tex": s1_exclusions, "s1_attrition.tex": s1_attrition, "s1_demographics.tex": s1_demographics,
    "s1_balance.tex": s1_balance, "s1_holm_family.tex": s1_holm_family, "s1_full_lmm.tex": s1_full_lmm,
    "s1_robustness.tex": s1_robustness, "s1_influence.tex": s1_influence,
    "s1_item_sensitivity.tex": s1_item_sensitivity, "s1_bootstrap_d.tex": s1_bootstrap_d,
    "s1_text_rates.tex": s1_text_rates, "s1_prompt_talk.tex": s1_prompt_talk,
    "s1_denotation_slope_sensitivity.tex": s1_denotation_slope,
    "s1_text_recoverability.tex": s1_text_recoverability, "s1_text_selfsimilarity.tex": s1_text_selfsimilarity,
    "s1_text_topics_stability.tex": s1_text_topics_stability,
}

S1_LATEX_OK = {
    "begin", "end", "centering", "small", "footnotesize", "caption", "label", "setlength", "tabcolsep",
    "toprule", "midrule", "bottomrule", "addlinespace", "par", "smallskip", "textwidth", "raggedright",
    "arraybackslash", "multicolumn", "textit", "textbf", "textsuperscript", "ensuremath", "newline", "ref",
    "nolinkurl", "chi", "pm",
}
BRITISH = re.compile(r"(?i)\b\w*(randomis|summaris|memoris|recognis|organis|minimis|labell|colour|behaviour|"
                     r"favour|modell|centre|programme|analys(e|ed|ing)\b)")


def s1_text_check(name: str, tex: str) -> None:
    """Stop if a copy uses tiny type, a code name, British spelling or an em dash."""
    body = "\n".join(line for line in tex.splitlines() if not line.startswith("%"))
    for bad in (r"\resizebox", r"\scriptsize", r"\tiny", r"\fontsize", "---", "\u2014", "Midjourney"):
        require(f"{name} has no {bad!r}", bad not in body)
    plain = re.sub(r"\\(nolinkurl|label|ref)\{[^}]*\}", " ", body)
    require(f"{name} prints no code name (an underscore outside a file name)", "_" not in plain)
    unknown = sorted(set(re.findall(r"\\([A-Za-z]+)", body)) - S1_LATEX_OK)
    require(f"{name} uses only known LaTeX commands (not {unknown})", not unknown)
    m = BRITISH.search(re.sub(r"\\[A-Za-z]+", " ", plain))
    require(f"{name} uses American spelling (found {m.group(0) if m else ''!r})", m is None)


def _parse_row(desc: str):
    """Turn a row description of generated/numbers_check.csv back into conditions."""
    if desc in ("the only row", ""):
        return {}
    out = {}
    for part in desc.split("; "):
        m = re.fullmatch(r"(.+?) starts '(.*)'", part) or re.fullmatch(r"(.+?) contains '(.*)'", part)
        if m:
            out[m.group(1)] = ("^" if " starts '" in part else "~") + m.group(2)
            continue
        col, sep, wanted = part.partition("=")
        if not sep:
            raise SystemExit(f"cannot read the row description '{desc}' in {NUMBERS_CHECK}")
        out[col] = wanted
    return out


def s1_against_macros() -> tuple:
    """Every cell printed here that a macro also prints must print the same; and every
    table read here must be the version generated/numbers.tex was built from."""
    with open(NUMBERS_CHECK, encoding="utf-8-sig", newline="") as fh:
        entries = list(csv.DictReader(fh))
    mine = {}
    for rel, i, column, fmt, printed in _S1_CELLS:
        mine.setdefault((rel, i, column), {})[fmt] = printed
    same_cell = same_print = 0
    for e in entries:
        rel = e["file"]
        if rel not in _S1_DATA:
            continue
        rows, sha = _S1_DATA[rel]
        if e["file_sha256"] != sha:
            raise SystemExit(f"generated/numbers.tex was built from another version of {rel} "
                             f"(macro {e['macro']}); rerun tools/make_numbers.py")
        where = _parse_row(e["row"])
        hits = [i for i, r in enumerate(rows) if all(_matches(r.get(c, ""), w) for c, w in where.items())]
        if len(hits) != 1:
            raise SystemExit(f"{e['macro']}: its row '{e['row']}' matches {len(hits)} rows of {rel}")
        key = (rel, hits[0], e["column"])
        if key not in mine:
            continue
        same_cell += 1
        require(f"{e['macro']} was read from the cell this table prints",
                Decimal(rows[hits[0]][e["column"]]) == Decimal(e["stored_value"]))
        if e["format"] in mine[key]:
            require(f"{e['macro']} prints {e['printed']!r} where a Study 1 table prints {mine[key][e['format']]!r}",
                    mine[key][e["format"]] == e["printed"])
            same_print += 1
    return same_cell, same_print


def s1_sources_csv() -> str:
    """One row per source table of each readable copy: what the copy replaces and the
    checksum it was read with."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["copy", "label", "replaces", "source_table", "sha256"])
    for name, orig, label in S1_COPIES:
        for rel in _S1_SOURCES[name]:
            w.writerow(["supplement/tables/" + name, label, "supplement/tables/" + orig, rel, _S1_DATA[rel][1]])
    return buf.getvalue()


def study1_tables() -> dict:
    """Build every readable copy, check it, and return {path: text}."""
    built = {}
    for name, _orig, _label in S1_COPIES:
        tex = S1_BUILDERS[name]()
        s1_text_check(name, tex)
        built[OUT_S1_DIR / name] = tex
    same_cell, same_print = s1_against_macros()
    print(f"Study 1 tables: {len(built)} copies from {len(_S1_DATA)} pipeline tables, each matching the "
          f"checksum of the supplements run; {same_cell} printed cells are also macros, {same_print} of them "
          f"in the same format and printed identically")
    built[OUT_S1_SOURCES] = s1_sources_csv()
    return built


def main() -> None:
    check_summary_verdicts()
    built = {OUT_SUMMARY: summary_table(), OUT_SUPP1: supp_table1(), OUT_SUPP2: supp_table2()}
    for path, tex in built.items():
        check(tex)
    built.update(study1_tables())
    for path, tex in built.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tex, encoding="utf-8")
        print("wrote", path.relative_to(PAPER))


if __name__ == "__main__":
    sys.exit(main())
