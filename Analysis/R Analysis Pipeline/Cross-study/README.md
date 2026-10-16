# Cross-study: the source penalty across modification levels

**This analysis is exploratory. None of the five registrations in `Docs/Preregistration/AsPredicted/` contains a pooled model across studies. It was specified on 9 October 2026, after the registered results were known (Study 1 on 7 October 2026; Studies 2 to 5 on 8 October 2026), and nothing in it changes a registered verdict.**

In Study 1, telling participants that the artist Alex made an artwork by prompting an AI system lowered its rated creativity by 0.448 points on a five-point scale. Studies 2, 4 and 5 showed participants second works that Alex made by hand from such a first artwork, at three levels of modification: None (the first work shown again unchanged), Slight (colour and contrast adjustments) and Dramatic (substantial changes by hand). This folder pools the three studies to ask how large the source penalty, the Human minus AI difference in ratings of the second work, is at each level, and what shape it takes across the levels. Three accounts predict different shapes. Taint: the penalty is the same at every level. Severance: there is no penalty at any level. Discounting: the penalty is largest at None and shrinks as modification grows. The comparison was proposed as an exploratory "propagation curve" in the program memorandum of 4 September 2026 (`Docs/Study 2/AI_Art_Copyright_Program_Memorandum.md`, Part IV.D).

## The files

| File | What it does |
|---|---|
| `CrossStudy_Penalty_Curve.Rmd` | Reads the five studies' deposited long data files, checks them, fits the pooled models, compares the three accounts, sets the originals of Studies 1 and 3 beside the second works, draws the two figures and runs the robustness checks. |
| `README.md` | This file. |
| `CHANGELOG.md` | The edit history of the source file, which carries none itself. |
| `tables/` | Every table the R Markdown file writes. |
| `figures/` | The two figures, as PDF and PNG. |
| `explanation_shift/` | A separate exploratory analysis of the written justifications, with its own README. |
| `structural_topics/` | A separate exploratory structural topic model of the written justifications of Studies 2, 4 and 5, with its own README. |
| `image_check/` | A separate check of the 30 stimulus images, specified on 10 October 2026: three measures of the distance between images, three checks of what the design assumes about the pictures, and the distances beside the ratings as description only, with its own README. |

An R Markdown file (`.Rmd`) mixes R code with text and is knitted, that is, run from top to bottom into an HTML report, here `CrossStudy_Penalty_Curve.html` beside the `.Rmd` file.

## How to run it

From this folder:

```sh
Rscript -e 'rmarkdown::render("CrossStudy_Penalty_Curve.Rmd")'
```

or open the file in RStudio and press Knit. The run needs no blind switch, the setting with which each study's pipeline can run on shuffled condition labels: it reads only long data files that each study's own real run wrote, and checks that it does. It took about a minute and a half on a twelve-core Mac, most of it in the ordinal model of section 10.1.

Each study's pipeline must have been run first, on its real labels; this file rebuilds nothing from the Qualtrics exports. It reads, from each study folder:

- `study1_long_with_text.csv` to `study5_long_with_text.csv`, the long data files, one row per participant, item and measure, with each study's own exclusions and scoring already applied;
- each study's `tables/studyN_quant_run_manifest.csv`, the record its real run wrote, to check that each long data file is the one that run wrote;
- `Study 1/tables/study1_confirmatory_family.csv`, for Study 1's registered creativity penalty on originals;
- `Study 3/tables/study3_lmm_ftests.csv`, to check the Study 3 contrast recomputed here;
- `Study 2/tables/study2_source_by_modification.csv`, `Study 4/tables/study4_secondary_label_by_modification.csv` and `Study 5/tables/study5_equivalence_source.csv`, each study's own penalty at each level, for the check of section 10.3;
- `Study 4/tables/study4_confirmatory_family.csv` and `Study 5/tables/study5_confirmatory_family.csv`, for the registered tests of the time factors;
- the survey files of Studies 2, 4 and 5 (`Final_-_AI_Copyright_-_Study_N.qsf`), to check that the three studies showed the same images.

It uses `shared/R/fit_status.R` for the fit status of every model and for the run record.

## What it checks before it models anything

The run stops unless every input agrees with its study's registered analysed sample:

- each long data file has the SHA-256 checksum (a 64-character fingerprint of a file's exact bytes) listed in the run manifest in its study's `tables/` folder, which only a real run writes, and Study 1's confirmatory table matches its manifest too;
- in Studies 2, 4 and 5 the column `label_mode` says `real` on every row;
- the counts are those registered: Study 1, 111 participants; Study 2, 235 participants and 20,659 analysed ratings; Study 3, 85 participants; Study 4, 117 participants and 6,178 analysed ratings, with 140 six-point ratings left out; Study 5, 223 participants and 12,042 ratings, of which 274 are on the six-point items and 11,768 are analysed;
- the same questions display the same image files in the three surveys of Studies 2, 4 and 5, and the ten source images carry the same names in their three long data files, so the pooled model can give each image one baseline across studies.

## The analysis

Creativity comes first and is the primary measure, because it is the one measure rated for original artworks and second works alike. Transformativeness and essence change follow. The two six-point transformativeness items are dropped, as each study's primary analysis drops them.

1. **The pooled model.** A linear mixed model, a regression that gives each participant and each image its own baseline, on each measure: `rating ~ source * modification * study + (1 | study:id) + (1 | image) + (1 | image:modification)`. Every factor uses sum-to-zero contrasts, a coding in which a factor's effects add to zero across its levels. It is fitted by restricted maximum likelihood (REML, the usual estimator of the variances in a mixed model) with the bobyqa optimizer, the numerical routine that searches for the estimates, as each study is. Degrees of freedom are Satterthwaite's, an approximation for mixed models. The penalty at each level is a contrast of estimated marginal means, the model's predicted cell means, given pooled over the three studies with equal weight and within each study, with 95 percent intervals. Studies 4 and 5 are averaged over their time factors, which the model leaves out.
2. **The trend.** The slope of the penalty across None, Slight and Dramatic, coded -1, 0 and 1, which is the change in the penalty per step, and its curvature, the Slight penalty minus the mean of the other two.
3. **Equivalence.** The pooled penalty at each level is tested against plus or minus 0.224 rating points, the bound Studies 2, 4 and 5 registered, by two one-sided tests on its 90 percent interval. The reading uses Study 5's registered wording: "absent or small: inside the bound" when the equivalence test passes and the two-sided test does not, "significant and inside the bound" when both pass, "significant, not inside the bound" and "inconclusive" otherwise. A pass means that less than half of Study 1's creativity penalty reaches the second work; it does not mean the penalty is zero.
4. **The three accounts as models.** Four models are fitted by maximum likelihood, which, unlike REML, lets models with different fixed terms be compared, on the same rows. Severance has no source term. Taint has one penalty per study, the same at every level. Discounting lets each study's penalty change in a straight line across the levels. The free shape lets each study's penalty take any value at each level; it is the pooled model, and the run checks that the two give the same likelihood. Each adds three parameters to the one before, so likelihood-ratio tests compare each with the next simpler one. AIC and BIC score each model's fit with a charge for each parameter, BIC's much heavier; the table also gives each criterion's weights, a share of support among the four models, and glosses each difference by the rough conventions of Burnham and Anderson (2002) for AIC, whose bands leave gaps between 2 and 4 and between 7 and 10 that are filled here, and Raftery (1995) for BIC. The memorandum proposed scoring the nested models by leave-one-out cross-validation, which asks how well a model predicts each observation from a fit that leaves that observation out; AIC approximates that score in large samples. A comparison on three studies describes which shape the data sit closest to and tests no registered prediction.
5. **The originals.** Study 1's registered H1 creativity contrast, the Human minus AI difference averaged over image kind (whether the artwork shows a human or humanoid figure), 0.448, is read from its table, with a 95 percent interval computed from the standard error and degrees of freedom there. Study 3's Human minus AI creativity difference, averaged over stated time, is recomputed from its registered model (`rating ~ Type * time + (1 | id) + (1 | stimulus_id)`, the same contrasts and optimizer) and labelled as recomputed, since Study 3 registered F tests, which ask whether a factor's levels differ at all, and an equivalence test at 100 hours rather than this contrast. The run checks that the square of its t statistic equals Study 3's registered F test of source, as it must for a factor with two levels.
6. **Robustness.** A cumulative-link mixed model (`ordinal::clmm`), which treats the five answers as ordered categories, refits the pooled creativity model. A fit counts as converged when its optimizer returns code 0 and no warning about convergence or about the Hessian (the matrix of second derivatives the standard errors come from) is raised, as in Studies 1, 4 and 5; a fit that does not converge keeps its estimates as description only, with no p-value or interval. The pooled penalties are recomputed with each study left out in turn. Each study's penalty from the pooled model is set beside the one in its own registered table, and each study is also fitted on its own with the pooled model's terms, which splits each difference into the part the terms make (a baseline added for each second work; image kind and the time factors left out) and the part the variances shared across studies make. Each study's registered model of Studies 4 and 5 is refitted to give the penalty at each time and level; averaged over time, the refits reproduce each study's registered penalties, and the run checks that they do.

## What it writes

In `tables/`, each table with a last column, `analysis_status`, that says it is exploratory (the session information file says so in its first line):

- `crossstudy_input_checks.csv`: every check above, with the expected and observed value;
- `crossstudy_penalty_by_level.csv`: the penalty at each level, pooled and within each study, with the Human and AI cell means, 95 and 90 percent intervals and uncorrected p-values;
- `crossstudy_penalty_trend.csv`: the slope and curvature, pooled and within each study;
- `crossstudy_penalty_equivalence.csv`: the equivalence reading of the pooled penalty at each level;
- `crossstudy_model_comparison.csv`: the four models on each measure, with log-likelihood, AIC, BIC, their differences and weights, the likelihood-ratio tests and a gloss of each in words;
- `crossstudy_originals_reference.csv`: the creativity penalty on originals from Studies 1 and 3;
- `crossstudy_ordinal_check.csv`: the cumulative-link penalties, on the underlying scale and as expected ratings, beside the linear model's;
- `crossstudy_leave_one_study_out.csv`: the pooled penalties with each study left out, and whether each 90 percent interval stays inside the bound;
- `crossstudy_registered_reconciliation.csv`: each study's penalty from the pooled model beside its registered estimate and beside the study fitted on its own with the pooled model's terms, with the difference split into the part the terms make and the part the shared variances make;
- `crossstudy_time_check.csv`: the penalty at each source time (Study 4) or editing time (Study 5) and level, from each study's registered model;
- `crossstudy_fit_status.csv`: every model fitted, with whether it stopped with an error, converged or is singular (a variance estimated at zero);
- `crossstudy_run_inputs.csv`, `crossstudy_sessionInfo.txt`, `crossstudy_package_versions.csv` and, written last, `crossstudy_run_manifest.csv`. The manifest lists every output with its checksum; the file deletes the old manifest when it starts, so a manifest on disk means the run reached its end.

In `figures/`, each as PDF and PNG, in the greyscale style of Study 1's figures, each with a line at its foot saying it is exploratory, and copied to `Docs/Writing/Final Paper/figures/`:

- `crossstudy_fig1_creativity_penalty_curve`: the creativity penalty on originals (Studies 1 and 3) and on second works at None, Slight and Dramatic (each derivative study and the pooled estimate), with 95 percent intervals, a dashed line at zero and a shaded band at plus or minus 0.224;
- `crossstudy_fig2_other_measures_penalty_curve`: the same for transformativeness and essence change, second works only.

## Limits

- Study 2's creativity item carried no definition, while Studies 4 and 5 used Study 1's. Study 2's registration says that creativity comparisons across studies are exploratory for that reason.
- At None the second work is the first unchanged. Ratings there sit near the bottom of the scale, which leaves little room for a penalty to show, so the None level discriminates among the accounts less sharply than the memorandum assumed. Study 2's registration names the oddness of that level as a known problem.
- The pooled model leaves out Study 4's source time and Study 5's editing time. None of Study 4's six registered time tests survived Holm's correction, the adjustment each study registered for running several tests at once. In Study 5 the editing-time effect did not survive on any measure, but the source by editing-time interaction on creativity did, so the Study 5 creativity penalty differs across editing times and the pooled curve averages over that difference. `crossstudy_time_check.csv` shows the penalty at each time.
- Each study counts once in a pooled estimate, whatever its size, and the pooled model shares its variances across the three studies.
- In every pooled fit the variance of the source images is estimated at zero once each second work has its own baseline, so the fits are singular. A singular fit that converged keeps its numbers.
- The pooled curve hides disagreement among the studies on creativity. Study 2's penalty grows from None to Dramatic, Study 4's lies below zero at every level, and the bend at Slight comes from Studies 4 and 5. Section 12 of the report gives the numbers.

## Environment

R 4.5.2 with readr, dplyr, tidyr, tibble, jsonlite, Matrix, lme4, lmerTest, emmeans, ordinal, ggplot2, rmarkdown and knitr; `tables/crossstudy_package_versions.csv` records the versions of a run. Paths are found from this file's own folder. These environment variables, named settings the shell passes to R when it starts, name other folders:

| Variable | What it names |
|---|---|
| `CROSS_STUDY_DIR` | this folder |
| `PIPELINE_DIR` | the analysis pipeline folder, one level up |
| `STUDY_SHARED_R` | the shared R helpers |
| `STUDY1_DIR` to `STUDY5_DIR` | the five study folders |
| `CROSS_STUDY_PROJECT_ROOT` | the project root, the folder that holds `Data` and `Analysis` |
| `PAPER_FIGURES_DIR` | the manuscript's figures folder |

Printed paths are relative to the project root, so no report names a folder particular to one machine.
