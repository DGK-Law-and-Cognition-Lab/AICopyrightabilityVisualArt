# Final Paper

The manuscript of Paper One, *Beyond the Original Sin: Lay Evaluations of Creative
Contribution in AI-Assisted Artworks* (David G. Kamper, Alice Lin and Keith J. Holyoak;
UCLA and the University of Chicago Law School), written for Nature Communications, and its Supplementary Information.

## How to build

From this folder:

```
python3 tools/make_numbers.py
DEVELOPER_DIR=/Library/Developer/CommandLineTools Rscript tools/study1_ppc_data.R   # only when Study 1's Bayesian fits change
python3 tools/make_figures.py
python3 tools/make_tables.py
latexmk -pdf main.tex
latexmk -pdf supplement/supplement.tex
```

The first command reads the pipeline's result tables and writes `generated/numbers.tex`.
The second draws the figures in `figures/` from the same tables (see `figures/README.md`).
The third writes Table 1 (`tables/paper_table1_summary.tex`) and Supplementary Tables 1 and 2
(`supplement/tables/supp_table1_verdicts.tex`, `supplement/tables/supp_table2_label_effects.tex`);
every number in them is a macro, and it checks each verdict they state against the verdict
column of its pipeline table. It also writes readable copies of 16 of Study 1's pipeline tables
(`supplement/tables/s1_*.tex`), read from the same CSV files after checking each file's SHA-256
checksum, which it lists in `supplement/tables/s1_sources.csv`. The other two write `main.pdf` and `supplement.pdf` in this folder. `latexmk` with no file
name builds both documents (the settings are in `.latexmkrc`), and `latexmk -c` removes the
by-products (`.aux`, `.log` and the like) and keeps the PDFs.

Build the supplement from this folder, not from inside `supplement/`: the paths in
`supplement/supplement.tex` start here.

## Where the numbers come from

Every number the paper prints comes from `generated/numbers.tex`, and only from there. Do not
type a number into the text. Write its macro instead, for example
`$d$~=~\SOneDEff` for Study 1's effect size on effort.

`tools/make_numbers.py` builds that file. It reads the CSV tables that the analysis pipeline
deposits in `Analysis/R Analysis Pipeline`, takes one cell for each number, rounds it, and
writes one macro per number with a comment naming the table, the row and the column, followed
by any note on the number's status (for example 'exploratory refit'). It also
writes `generated/numbers_check.csv`, which lists every macro with its source, the cell as
stored, the printed value and the SHA-256 checksum (a fingerprint that changes if the file
changes) of the table it came from. To find the macro for a number, search that file.

The script stops, and writes nothing, if a table, row or column it needs is missing, if a row
description matches no row or more than one, or if a cell is empty or not a number. It finds
the pipeline from its own location (`../../../../Analysis/R Analysis Pipeline`); to read
another copy, set `PIPELINE_DIR` to that copy's `R Analysis Pipeline` folder. Run it again
whenever the pipeline is rerun.

**Rounding.** Ratings, rating differences and their intervals: two decimals. Effect sizes
(d, correlations, AUC, ratios, log-odds): two decimals. Test statistics (t, F, z,
chi-square): two decimals. Degrees of freedom: whole numbers, or one decimal when not close
to whole. Very small differences (in AUC, word overlap or topic share) and the 0.224 and 0.219
equivalence bounds of Studies 2 to 5: three decimals. Study 1's own H3 bound, registered as
plus or minus 0.20, prints with two decimals. Counts: whole numbers. Shares: percentages with
one decimal. p-values in APA style: three decimals with no leading zero, "< .001" below .001,
and "> .999" when the value rounds to 1.000 (for example a Holm-corrected p capped at 1). A
p-value macro carries its own sign, so write `$p$~\SOneHOneCreatPHolm`, which prints
"p = .001".

**Macro names** contain letters only and read left to right:

| Part | Meaning |
|---|---|
| `SOne` ... `SFive` | Study 1 to Study 5 |
| `XS` | exploratory cross-study analyses |
| `Creat`, `Eff`, `Trans`, `Ess` | creativity, effort, transformativeness, essence change |
| `None`, `Slight`, `Dramatic` | modification level of the second work |
| `UnderOneHour`, `TenHours`, `HundredHours` | stated time |
| `Est`, `Diff` | the estimate |
| `SE` | standard error |
| `Lo`, `Hi` | 95 percent interval |
| `LoNinety`, `HiNinety` | 90 percent interval (used by equivalence tests) |
| `T`, `F`, `Z`, `Chisq` | test statistic |
| `Df`, `DfNum`, `DfDen` | degrees of freedom |
| `P` | uncorrected p-value |
| `PHolm` | p-value after Holm's correction for a set of tests |
| `PTost` | equivalence-test p-value (the larger of the two one-sided tests) |
| `PBH` | p-value after the Benjamini-Hochberg correction |
| `PPerm` | p-value from label shuffles |
| `Ord` | the registered ordinal (cumulative-link) check; its estimates are on the log-odds scale |
| `Rescaled` | Study 5's registered second analysis, every item rescaled from 0 to 1 |
| `Pct` | a share, printed as a percentage |
| `N` | a count of people, records or ratings |
| `AgeMean`, `AgeSD`, `AgeMin`, `AgeMax` | age of a study's analyzed sample: mean, standard deviation, youngest and oldest |
| `NWomen`, `NMen`, `NGenderOther` | gender of a study's analyzed sample: the answers Female and Male, and every other answer or none |

For example, `\STwoCreatPenaltyPHolm` is Study 2's Human-minus-AI creativity difference, its
Holm-corrected equivalence p-value. A result of an exploratory cross-study analysis carries the
`XS` prefix even when it describes one study: `\XSTimeCheckSFiveCreatPenaltyTenHoursSlightEst`
is Study 5's creativity penalty in one editing-time cell, from the exploratory refit.
Three Study 5 counts, `\SFiveNRatings`, `\SFiveNRatingsAll` and `\SFiveNSixPointDropped`, are read from
`Cross-study/tables/crossstudy_input_checks.csv` because no Study 5 table holds them; they are counts, not
exploratory results, so they keep the `SFive` prefix. `\SFiveNRatings` is the ratings analyzed, like `\STwoNRatings` and `\SFourNRatings`;
`\SFiveNRatingsAll` counts every rating, the two six-point items included.

Two macros stand alone: `\SourceBound` is the plus or minus 0.224 bound used for source
effects in Studies 2 to 5, and `\NTotal` is the total analyzed sample, the one number the
script adds up (from the five study samples) rather than copies. `\NTotal` counts participations
(one person's session in one study), not people: `\NPeople` is the number of different people
behind them and `\NPeopleRepeat` the number analyzed in two studies, both read from
`Cross-study/sample_description/tables/sample_description_overlap.csv`.

## What is in this folder

| Path | What it is |
|---|---|
| `main.tex` | The manuscript, in Nature Communications order. Each section is an `\input` of a file in `sections/`. |
| `sections/` | One file per section of the manuscript. |
| `supplement/supplement.tex`, `supplement/sections/` | The Supplementary Information, built the same way. |
| `supplement/tables/suppA_*.tex`, `supplement/tables/suppB_*.tex` | Tables written by hand for the Supplementary Information's sections on the registrations, Studies 1 to 5, the text measures and the cross-study analyses. Four `suppA_` files are copies of pipeline tables with layout or wording changes only; every number in the others is a macro. `README_suppA.md` and `README_suppB.md` in that folder give each table's source. |
| `supplement/tables/s1_*.tex` | Readable copies of Study 1's pipeline tables (Supplementary Tables 5 to 22 apart from Supplementary Tables 11 and 18, which are `suppA_` tables), written by `tools/make_tables.py` from the pipeline's CSV files. Do not edit. |
| `references.bib` | The bibliography (BibTeX). BibTeX runs once this file has entries. |
| `generated/` | `numbers.tex` and `numbers_check.csv`, written by `tools/make_numbers.py`. Do not edit. |
| `tools/make_numbers.py` | Builds `generated/`. Python 3.8 or later, standard library only. |
| `tools/make_tables.py` | Writes Table 1 and Supplementary Tables 1 and 2 from `generated/numbers.tex`, and the Study 1 copies `supplement/tables/s1_*.tex` from the pipeline's CSV files. Run it after `make_numbers.py`. Python 3.8 or later, standard library only. |
| `tools/study1_ppc_data.R` | Computes the curves of Supplementary Figure 5 from Study 1's saved Bayesian fits (read only) into `figures/figS_study1_ppc_curves.csv`. R with brms and digest; run before `make_figures.py` when the fits change. |
| `tools/make_figures.py` | Draws Figures 1 and 2 and Supplementary Figures 1 to 5 in `figures/`, and writes `figures/plotted_values.csv`. Python 3.12 with matplotlib and Pillow. |
| `notes/results_ledger.md` | The working reference for drafting: every result, its status (registered confirmatory, registered secondary, exploratory or descriptive), its verdict, its caveats and its source table. It is not part of the paper. |
| `figures/`, `tables/`, `supplement/figures/`, `supplement/tables/` | Written by the pipeline; see below. |
| `.latexmkrc` | Build settings for `latexmk`. |

## Files the pipeline writes here

These are outputs of the analysis code. Do not edit them by hand; rerun the code instead. No document
inputs the `study1_*` and `crossstudy_*` figures listed below; they were moved to
`figures/_superseded/` on 20 October 2026, and a rerun of the pipeline writes them back into
`figures/`. The pipeline's `supplement/tables/sup_table_*.tex` are no longer input either: the
Supplement inputs the `s1_*.tex` copies instead, and of the pipeline's three Supplement figures
only `supplement/figures/sup_fig_2_brms_ppc.pdf` (Supplementary Figure 5, placed as two clipped panels without the pipeline's titles).

* `figures/study1_fig1_main.pdf`, `figures/study1_fig2_forest.pdf`: `Study 1/Study1_01_Quant.Rmd`.
* `figures/study1_fig3_text_prevalence.pdf`, `figures/study1_fig4_detail_vs_effort.pdf`,
  `figures/study1_fig5_denotation_profiles.pdf`: `Study 1/Study1_03_Integration.Rmd`.
* `figures/study1_specification_curve_creativity.pdf`,
  `figures/study1_specification_curve_effort.pdf`: `Study 1/Study1_04_Robustness.Rmd`.
* `figures/study1_fig1_ratings.pdf` and `.png`, `tables/study1_inline.tex`:
  `Study 1/Study1_Figures.Rmd`.
* `supplement/tables/sup_table_*.tex` (29 tables) and `supplement/figures/` (3 figures):
  `Study 1/Study1_Supplements.Rmd`.
* `tables/paper_table1_summary.tex`, `supplement/tables/supp_table1_verdicts.tex` and
  `supplement/tables/supp_table2_label_effects.tex`: `tools/make_tables.py` (in this folder, not
  the pipeline). `tables/paper_table1_verdicts.tex` and `tables/paper_table2_label_effects.tex`
  are the earlier main-text Tables 1 and 2, written by an earlier version of that script; their
  content is now Supplementary Tables 1 and 2, so neither document should input them.
* `figures/crossstudy_fig1_creativity_penalty_curve.pdf` and `.png`,
  `figures/crossstudy_fig2_other_measures_penalty_curve.pdf` and `.png`:
  `Cross-study/CrossStudy_Penalty_Curve.Rmd` (exploratory).

**Never `\input` `tables/study1_inline.tex`**, in `main.tex`, in the supplement or in any file
they input. Its macros have names close to those in `generated/numbers.tex` but follow other
rounding rules: `\SoneEffortDetail` prints "62\% (95\% CI [56, 69])" where `\SOneTextEffortDetailPct` prints
"62.5%", and it writes "< 0.001" with a leading zero. Every number in the paper comes from
`generated/numbers.tex`.

## How to build from a fresh copy

1. Install Python 3.8 or later. The script uses only the standard library.
2. Install a TeX distribution with `pdflatex`, `bibtex` and `latexmk` (TeX Live 2024 was used),
   including the packages `lmodern`, `geometry`, `amsmath`, `graphicx`, `booktabs`, `array`,
   `multirow`, `longtable`, `float`, `caption`, `natbib`, `setspace`, `lineno`, `hyperref` and `xurl`,
   and the bibliography style `naturemag.bst`.
3. Put the analysis pipeline at `../../../../Analysis/R Analysis Pipeline` relative to `tools/`,
   or set `PIPELINE_DIR` to wherever it is.
4. Install matplotlib and Pillow for Python 3.12 (tested with matplotlib 3.8.4 and Pillow 10.3.0).
5. From this folder, run the four commands under *How to build*.

## Earlier draft

The April 2026 draft of this folder (its `.tex` files, `references.bib` and
`tables/study1_lmm_table.tex`) is in `../_archive/Final_Paper_draft_2026-04/`. It described an
analysis pipeline that has since been retired, so do not reuse its text or numbers without
checking them against `notes/results_ledger.md` and `generated/numbers.tex`.
