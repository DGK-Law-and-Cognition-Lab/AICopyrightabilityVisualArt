# Figures

The two main-text figures and four Supplementary figures of the paper. Each is a PDF for the
manuscript and a PNG for checking by eye. Do not edit them by hand; rerun the script that writes
them.

| Figure | Files | Written by |
|---|---|---|
| 1 | `fig1_design.pdf`, `.png` | `tools/make_figures.py` |
| 2 | `fig2_results.pdf`, `.png` | `tools/make_figures.py` |
| Supplementary | `figS_other_ratings.pdf`, `.png` | `tools/make_figures.py` |
| Supplementary | `figS_study1_raincloud.pdf`, `.png` | `tools/make_figures.py` |
| Supplementary | `figS_study5_editing_time.pdf`, `.png` (exploratory) | `tools/make_figures.py` |
| Supplementary | `figS_pooled_penalty.pdf`, `.png` (exploratory) | `tools/make_figures.py` |

`plotted_values.csv`, written by the same script, lists every plotted value with its figure and
panel, its table, row and column, how it was derived if it was not copied, and the SHA-256
checksum (a fingerprint that changes if the file changes) of its table. The dots of the Study 1
raincloud are listed one per row, sorted by value within each label and rating, with no
participant identifier; no file the script writes contains one.

## How to redraw them

From the Final Paper folder, run `python3 tools/make_figures.py`. It needs Python 3.12 with
matplotlib and Pillow (tested with matplotlib 3.8.4 and Pillow 10.3.0). It reads only the
pipeline files named below and three stimulus images, and it finds the pipeline as
`tools/make_numbers.py` does (`PIPELINE_DIR` overrides the default; `FIGURES_DIR` writes the
figures elsewhere). Two runs on the same tables give byte-identical files.

The script stops, and writes no figure, if a table, row, column or image is missing; if a row
description matches more or fewer than one row; if an image's checksum differs from the one the
image check recorded; if a status cell (for example `role`, `correction`, `analysis_status`,
`survives_holm_at_05` or Study 3's `verdict`) does not say what the captions say; if a table
states a bound other than the registered one, or the bound is not half of Study 1's creativity
gap; if any interval is not the 95 percent interval implied by its own estimate, standard error
and degrees of freedom; if a gap does not equal the Human-label mean minus the AI-label mean
drawn beside it; if Study 1's means differ from its model's predicted means, or H2 differs from
the effort gap minus the creativity gap; if Study 1's participant means do not reproduce
`study1_marginal_means.csv` and the analyzed N; if a fact a caption states no longer holds
(the AI-label spread in the raincloud, Study 4's creativity gaps below zero and none
significant, the pooled fits converged and singular); if a gap axis is not drawn at the rating axis's
millimeters per point; if any text is smaller than 7 pt, runs past the figure's edge, overlaps
other text or runs into a plotting area; or if a title is not centered.

Paths below are relative to `Analysis/R Analysis Pipeline`.

## Style

Set by the lead author on 21 October 2026. All six figures are 183 mm wide (the Nature
Communications double column), set in Arial, with no text smaller than 7 pt at that size.

* **Light text.** A figure carries only what a reader needs to decode its marks, plus at most one
  short guard line where a misreading is likely. Statuses, sample sizes, definitions and
  exact intervals are in the captions and tables.
* **Titles centered or absent.** Panel titles are centered over what they title; bold panel
  letters sit at each panel's top-left.
* **Labels.** The Human label is Okabe-Ito vermilion with a filled circle; the AI label is
  Okabe-Ito blue with an open diamond, drawn on top so both marks show where the two means nearly
  coincide. Shape and fill carry the distinction in grayscale. Each label figure has a
  two-entry legend and one gray line: "Every image was made with AI; only the label differed."
* **Gaps.** The gap is the Human-label mean minus the AI-label mean (the text's "penalty"). It is
  a black square with a black 95 percent interval, beside a gray zero line. Every rating axis and
  every gap axis is drawn at 22 mm per rating point, so a dumbbell's length equals its gap's
  distance from zero. Study 1's H2 row is gray.
* **Figure 1** uses no study colors, because vermilion and blue now mean the two labels.

## Figure 1: the design of the five studies

* **a. One original and its Slight and Dramatic versions** (artwork `3Figure`):
  `Cross-study/image_check/stimuli/3Figure_original.png`, `3Figure_slight.png` and
  `3Figure_dramatic.jpg`, each checked against `file_sha256` in
  `Cross-study/image_check/stimuli/stimuli_manifest.csv`. One gray line under the original says
  that the None second work is this image shown again unchanged.
* **b.** One card per study, grouped under "Rating originals" and "Rating second works" with what
  each group rated: what varied between and within participants, and the analyzed N. Each N is
  column `n` of the last row of the study's exclusion flow, the same cell as its macro (`\SOneN`
  to `\SFiveN`):
  * Study 1: `Study 1/tables/study1_exclusion_flow.csv`, step starts 'After (3)'.
  * Study 2: `Study 2/tables/study2_exclusion_flow.csv`, step 'no recorded condition'.
  * Study 3: `Study 3/tables/study3_exclusion_flow.csv`, step starts 'wrong answer'.
  * Study 4: `Study 4/tables/study4_exclusion_flow.csv`, step starts 'records that are not'.
  * Study 5: `Study 5/tables/study5_exclusion_flow_registered.csv`, step starts '5.'.

  The design facts on the cards come from the registrations and the ledger's design sections,
  one item per line. One gray line at the foot says that every image was made with AI and only
  the label differed; the caption says what the labels said and gives the stated times.

## Figure 2: mean ratings under the two labels, and the gap between them

Each row is a dumbbell: the Human-label and AI-label means on the 1-to-5 scale, joined by a gray
line; the right column draws the gap again with its 95 percent interval. The means carry no
intervals (no pipeline table gives them for Study 1, or for Study 4 by level, and a mean's
interval includes image-to-image differences that both labels share).

* **a. Originals.**
  * Study 1, creativity and effort. Means: `Study 1/tables/study1_marginal_means.csv`, rows
    `Type` Human or AI and `dimension`, column `mean` (`\SOneMean...`); the script checks that they
    equal the primary model's predicted means from `study1_lmm_fixed_effects.csv`. Gaps (H1):
    `Study 1/tables/study1_confirmatory_family.csv`, row hypothesis H1, test containing the rating,
    column `estimate`; intervals from `Study 1/tables/study1_robustness_h1_contrast.csv`, row check
    'primary model (reference)', columns `ci_lo`, `ci_hi`.
  * Study 1, the gray row: the effort gap minus the creativity gap (H2).
    `Study 1/tables/study1_joint_model_contrast_of_contrasts.csv`, row `Type_pairwise` 'Human - AI',
    columns `estimate`, `lower.CL`, `upper.CL`. The script checks that it equals the effort gap
    minus the creativity gap, that its interval is a 95 percent interval, and that the H2 row of
    the confirmatory family has the same estimate and standard error and survives Holm's
    correction.
  * Study 3, creativity and effort at under 1, 10 and 100 stated hours. Means:
    `Study 3/tables/study3_emmeans_cells.csv`, column `emmean`. Gaps:
    `Study 3/tables/study3_gap_by_time.csv`, columns `estimate`, `lower.CL`, `upper.CL`. The 100-hour
    rows carry a dagger; the script checks that `Study 3/tables/study3_decision.csv` gives the
    verdict 'the gap persists' on each rating and that its `gap_100_hours` is the gap drawn.
* **b. Creativity of the second work** at None, Slight and Dramatic.
  * Study 2 (exploratory): means `Study 2/tables/study2_emmeans.csv`, means_of 'source by
    modification', column `emmean`; gaps `Study 2/tables/study2_source_by_modification.csv`,
    columns `estimate`, `ci95_lo`, `ci95_hi` (the script checks that `role` begins 'exploratory').
  * Study 4 (registered secondary, uncorrected): gaps
    `Study 4/tables/study4_secondary_label_by_modification.csv`, columns `estimate`, `ci95_low`,
    `ci95_high`. **Derived:** each mean is the equal-weight mean of the three stated-time cells of
    `Study 4/tables/study4_emmeans_cells.csv` (column `emmean`), the averaging the registered
    contrast uses; its Human minus AI difference is checked against the gap.
  * Study 5 (registered secondary, uncorrected): means
    `Study 5/tables/study5_emmeans_source_by_modification.csv`, column `emmean`; gaps
    `Study 5/tables/study5_equivalence_source.csv`, columns `estimate`, `se`, `df`. This table holds
    only the 90 percent interval. **Derived:** the script checks that it equals estimate plus or
    minus t(0.95, df) times se, then draws estimate plus or minus t(0.975, df) times se.
  * The registered bound (`Study 2/tables/study2_equivalence.csv`, row creativity, column `bound`)
    is no longer drawn. The script still stops unless the Study 4 and Study 5 tables state the
    same bound and it is half of Study 1's creativity gap.

## Supplementary figure: transformativeness and essence change of the second work

The layout, scale and sources of Figure 2b, for transformativeness (a) and essence change (b).
Its one guard line, under panel b's title, gives the direction of essence change; the caption
carries Figure 2b's warning that the rise across levels and the gap cannot be compared in size.

## Supplementary figure: the Study 1 raincloud

Creativity and effort under each label. Each dot is one participant's mean of their non-missing
ratings in that cell, computed from `Study 1/study1_long_with_text.csv`, of which the script reads
only the columns `id`, `Type`, `dimension` and `rating` (the id only to group a person's
ratings; it is never recorded). The script stops unless the dots reproduce
`Study 1/tables/study1_marginal_means.csv` (count, mean and standard deviation in every cell) and
the analyzed N. Dots sit at their exact values and stack where values repeat. Each half-violin is
a Gaussian kernel density of the dots (smoothing width 0.15 points, reflected at 1 and 5 so it
stays inside the scale, not drawn where thinner than 0.15 mm); the four outlines share one height
scale. Large marks are the means and the right column the gaps, read as in Figure 2a. Rows are named
"Human label" and "AI label". The script also stops unless the standard deviations in
`study1_marginal_means.csv` are larger under the AI label on both ratings, more so on effort,
as the caption says.

## Supplementary figure: Study 5's creativity gap at each stated editing time (exploratory)

`Cross-study/tables/crossstudy_time_check.csv`, rows study 'Study 5', measure creativity,
time_factor 'editing time', each time and each modification, columns `estimate`, `ci95_lo`,
`ci95_hi`. The script stops unless every row's `analysis_status` is the same three-part cell
beginning 'exploratory' (the caption quotes it). The intervals are not corrected for the nine
comparisons. The gray line on the label manipulation sits under the axis title.

## Supplementary figure: the pooled gap on second works (exploratory)

* Pooled over Studies 2, 4 and 5, each study weighted equally (filled squares):
  `Cross-study/tables/crossstudy_penalty_by_level.csv`, rows scope 'pooled'.
* Pooled without Study 4 (open squares): `Cross-study/tables/crossstudy_leave_one_study_out.csv`,
  rows left_out 'Study 4'.
* Columns `estimate`, `ci95_lo`, `ci95_hi`. The script checks `scope`, `study`, `weighting`,
  `converged`, `singular` and `analysis_status` on every row: the fits converged but are
  singular, as the caption says. It also stops unless Study 4's own creativity gaps
  (`Study 4/tables/study4_secondary_label_by_modification.csv`, columns `estimate` and
  `p_two_sided`) lie below zero at every level with no p under .05, as the caption says.

## Other files in this folder

Every figure file that no `.tex` file of the manuscript or the Supplementary Information inputs
is kept in `_superseded/`, unchanged:

* `fig2_creativity_penalty.*` and `fig3_penalty_by_measure.*`: Figures 2 and 3 before
  21 October 2026. Figure 2 is now `fig2_results`; Figure 3 left the main text and is now the
  Supplementary figure `figS_other_ratings`.
* `fig1_design_2026-10-20.*`, `figS_study5_editing_time_2026-10-20.*` and
  `figS_pooled_penalty_2026-10-20.*`: the versions of 20 October 2026 (study colors, the gray
  band, left-aligned titles), replaced by the files of the same name above.
* `fig2_originals.*` and `fig3_second_works.*`: older versions of Figures 2 and 3.
* `crossstudy_fig1_creativity_penalty_curve.*` and `crossstudy_fig2_other_measures_penalty_curve.*`:
  written by `Cross-study/CrossStudy_Penalty_Curve.Rmd` in the pipeline; the pooled
  Supplementary figure replaces them.
* `study1_fig1_main.pdf`, `study1_fig1_ratings.*`, `study1_fig2_forest.pdf`,
  `study1_fig3_text_prevalence.pdf`, `study1_fig4_detail_vs_effort.pdf`,
  `study1_fig5_denotation_profiles.pdf`, `study1_specification_curve_creativity.pdf` and
  `study1_specification_curve_effort.pdf`: written by the Study 1 pipeline (the Final Paper
  `README.md` names the notebook behind each). The paper's figures replace them.

The pipeline notebooks that wrote the cross-study and Study 1 files write them to this folder
again whenever they are rerun. Nothing inputs them; move them to `_superseded/` again or delete
the new copies.

Supplementary Figure 5, the check of Study 1's Bayesian refit against the data, is `figS_study1_ppc`. Its curves come from `figS_study1_ppc_curves.csv`, which `tools/study1_ppc_data.R` computes from the pipeline's saved Gaussian brms fits (`Study 1/models/study1_brms_primary_{creativity,effort}.rds`, read only, never refitted): 100 posterior predictive draws with the seed 20260421, and the density of each draw and of the observed ratings on one grid. `figS_study1_ppc_sources.csv` records each fit's checksum, and `make_figures.py` stops if a fit has changed since. Run the R script before `make_figures.py` whenever the fits change: `DEVELOPER_DIR=/Library/Developer/CommandLineTools Rscript tools/study1_ppc_data.R` (R with brms and digest).
