# Study 1 analysis pipeline

Study 1 asks whether telling people that an artwork was made by an image generator, rather than by a human artist, changes how creative and how effortful they judge it to be. One hundred and eleven participants each rated the same ten artworks on creativity and on effort and wrote a short justification beside every rating; half were told a human made the works and half were told an image generator did. This folder holds the code that turns the survey export into the numbers, tables and figures in the paper, together with the outputs of the last run.

Six source files do all the work. Five are R Markdown files (`.Rmd`: a text file that mixes R code with explanatory prose and is "knitted" into an HTML report by running the code top to bottom). One is a Jupyter notebook (`.ipynb`: a file of Python cells run in order).

## The six source files

- `Study1_01_Quant.Rmd` reads the two Qualtrics exports, applies the exclusion rules, fits the mixed-effects models on the ratings (a mixed-effects model is a regression that gives each participant and each image its own baseline, so that a participant's ten ratings are not treated as ten independent observations), runs the registered tests on those ratings, and writes the long-format data file (one row per participant, image and rating dimension) that every other file reads.
- `Study1_02_Text.ipynb` reads that data file and applies a fixed set of search patterns (written-down word lists) to the written justifications, producing one true/false or three-way flag per response, and writes those flags to `nlp/study1_text_measures.csv` without ever seeing which condition a response came from or what rating it accompanied. On the same blind footing it writes the word tables for the two checks run in every study, and a general description of the text: scores from published word norms (average ratings other laboratories collected for single English words) and the weights of a topic model (a method that finds groups of words that tend to occur together).
- `Study1_03_Integration.Rmd` joins the text measures back to the ratings and runs every statistical model of the text program: what people meant by "effort" and by "creativity", how many participants in the human-attribution arm wrote that the work looked machine-made, the two checks run in every study, and the general description by arm.
- `Study1_04_Robustness.Rmd` checks that the ratings results hold up under other reasonable choices: a Bayesian replication (a fit that expresses its uncertainty as a full distribution rather than a single estimate and interval), equivalence tests at wider bounds (an equivalence test asks whether an effect sits inside a stated bound rather than whether it differs from zero), power by simulation, demographic and response-length covariates, and a specification curve (every defensible way of fitting the model, run in full and plotted side by side).
- `Study1_Supplements.Rmd` builds the supplementary tables and figures as LaTeX fragments (small text files the manuscript pulls in with `\input{}`) from tables already on disk; it refits nothing.
- `Study1_Figures.Rmd` draws the main-text ratings figure and writes `tables/study1_inline.tex`, the file of LaTeX macros that puts each statistic into the manuscript text; it refits nothing.

## Run order

1. `Study1_01_Quant.Rmd`
2. `Study1_02_Text.ipynb`
3. `Study1_03_Integration.Rmd`
4. `Study1_04_Robustness.Rmd`
5. `Study1_Supplements.Rmd`
6. `Study1_Figures.Rmd`

The order follows what each file reads. The notebook needs `study1_long_with_text.csv`, which `Study1_01_Quant.Rmd` writes, so on a clean folder the ratings file runs first; once that data file exists the notebook can be re-run on its own at any time. `Study1_03_Integration.Rmd` needs the notebook's `nlp/study1_text_measures.csv`, its five other data files in `nlp/` (`study1_text_wordcounts.csv`, `study1_text_vocabulary.csv`, `study1_text_tokens.csv`, `study1_text_affect.csv` and `study1_text_topics.csv`) and `tables/text_topics_top_words.csv`, and stops with a message naming the notebook if any of them is missing. `Study1_04_Robustness.Rmd` needs the two fitted models and the long data file from `Study1_01_Quant.Rmd`, and reads the `n_words` column of the notebook's flags file for one length check. The last two files read only tables already on disk; each of them skips a section whose input is absent, or whose producing file's run manifest lists it as not written, and prints a line naming the file that writes it, so they can be knitted at any point and re-knitted after any upstream change.

Knit an `.Rmd` file in RStudio with the Knit button, or from R with `rmarkdown::render("Study1_01_Quant.Rmd")`.

### Running the notebook

The notebook needs Python 3.12 with pandas, NumPy, scikit-learn, SciPy and sentence-transformers (which installs PyTorch with it), and the files of the all-mpnet-base-v2 sentence-embedding model already on the machine. The 2026-10-07 run used Python 3.12.3, pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.5.2, SciPy 1.13.0, sentence-transformers 3.3.1 and PyTorch 2.5.1. Every run records its own versions in `tables/study1_text_environment.csv`.

The notebook never downloads the model. It loads it from the Hugging Face cache, the folder where these Python libraries keep downloaded models (by default `~/.cache/huggingface/hub/`), so the model has to be fetched there once beforehand, on a machine with a network connection:

    python3.12 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"

Jupyter runs a notebook through a kernel, a named entry that tells it which Python to start. The notebook's metadata names the generic kernel `python3`, which can point to a different Python on each machine, so the command below names a Python 3.12 kernel, `python312`, explicitly. If no kernel of that name exists, register one once with `python3.12 -m ipykernel install --user --name python312`. Then, from this folder:

    jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=python312 Study1_02_Text.ipynb

The command runs every cell in order and saves the outputs into the notebook; the whole run takes about a minute. The notebook can also be opened in Jupyter and run cell by cell on the same kernel, or run in Google Colab. Its first code cell looks for the Study 1 folder in this order: the folder the environment variable `STUDY1_DIR` names, when it is set; the two places where Colab shows Google Drive, which it attaches first when it runs in Colab; the folder the notebook runs from; and the folder above that. It says where it looked if it cannot find the data file. A fresh Colab session does not have the model files, so there the check that uses the model records that it did not run, and the rest of the notebook carries on. The paths the notebook prints are relative to the Study 1 folder.

## Where the inputs come from

- The two Qualtrics exports (Qualtrics is the survey platform) live in `Data/Study 1/` at the top of the project, one folder tree away from here: `Study1_Values.csv`, the numeric-coded export that supplies the ratings, and `Study1_Labels.csv`, the label-coded export that supplies the written justifications and the demographics. `Study1_01_Quant.Rmd` reads both and stops with a clear message if either is missing.
- Every `.Rmd` file finds the project through a single `PROJECT_ROOT`, set in the paths chunk of its section 1: the first folder at or above the file's own folder that holds both `Data` and `Analysis`. The files therefore run unchanged wherever the project is copied, and every other path derives from that one. Setting the environment variable `STUDY1_PROJECT_ROOT` names the root instead, for a run from somewhere else, such as a Colab runtime.
- `qualtrics/Final_-_AI_Copyright_-_Study_1.qsf` is the survey definition file exported from Qualtrics (a `.qsf` file records every question, its wording and its options). It documents the instrument and is not read by any source file.
- `nlp/norms/` holds two published word-norm datasets (concreteness ratings, and valence, arousal and dominance ratings, for English words) with their own README recording their sources and checksums. They are not redistributed. Section 11 of the notebook reads both and stops with a message naming the folder's README if either is missing.
- `models/` holds the four Bayesian model fits that `Study1_04_Robustness.Rmd` loads when they are present and brms finds no change in the data, formula, priors or Stan code; on a folder without them the file refits the models, which takes considerably longer.

## What each file writes

The `.Rmd` files derive every output path from `PROJECT_ROOT`, and the notebook from the Study 1 folder its first cell finds. Files written into this folder go to `tables/`, `figures/`, `models/` and `nlp/`; paper-ready copies go to `Docs/Writing/Final Paper/` under `figures/`, `tables/` and `supplement/`. In the lists below, braces stand for alternatives: `study1_lmm_{creativity,effort}.rds` means the two files `study1_lmm_creativity.rds` and `study1_lmm_effort.rds`.

Every file also writes a run manifest in `tables/`, named `study1_<stage>_run_manifest.csv`: a list of the files the run wrote, and in the R Markdown files the files it read, each with its SHA-256 checksum (a 64-character fingerprint computed from a file's exact bytes, which changes if a single byte changes). All six files delete their earlier manifest when they start and write the new one last, so a manifest on disk means the run reached its end. The five R Markdown files record beside each output whether this run wrote it. The notebook records the run identifier and the checksum of its input beside every output, and a file whose checksum differs from its row there was not written by the run the manifest records.

Knitting an `.Rmd` file also writes its HTML report into this folder (`Study1_01_Quant.html` and so on). Knitting `Study1_04_Robustness.Rmd` also writes `Study1_04_Robustness_files/`, the figure folder of knitr (the R package that runs a knit), and `Study1_04_Robustness_cache/`, where knitr keeps the results of the file's four cached chunks (code blocks whose results are reused on the next knit while their code and the files they depend on are unchanged).

### `Study1_01_Quant.Rmd`

Its section 13 lists every output by name.

- In this folder: `study1_long_with_text.csv`, the long-format data file every other source file reads; and `study1_sessionInfo.txt` and `study1_package_versions.csv`, which record the R environment (section 12).
- In `tables/`:
  - the run record (section 1.2): `study1_quant_run_inputs.csv`, the run identifier with the checksum and size of each Qualtrics export;
  - exclusions and demographics (section 3): `study1_exclusion_flow.csv`, `study1_attrition_by_condition.csv`, `study1_demo_{age,gender,race,experience,balance,language}.csv`, `study1_balance.csv` and `study1_balance_descriptives.csv`;
  - descriptives and reliability (sections 5 and 6): `study1_cell_means.csv`, `study1_marginal_means.csv`, `study1_reliability.csv` and `study1_reliability_by_condition.csv`;
  - the mixed-effects models and their diagnostics (sections 7.3 to 7.7): `study1_lmm_fixed_effects.csv`, `study1_lmm_anova.csv`, `study1_random_effects_comparison.csv`, `study1_lmm_fully_maximal.csv`, `study1_joint_model_{anova,fixed,contrast_of_contrasts,simple_effects}.csv`, `study1_h2_ordinal.csv`, `study1_heteroscedasticity.csv`, `study1_lmm_convergence.csv`, `study1_influence_{lopo,loso,summary}.csv` and `study1_hetero_varident.csv`;
  - H4, the confirmatory family, H3 and the item check (sections 7.8 to 7.11): `study1_h4_variance_partition.csv`, `study1_h4_variance_test.csv`, `study1_h4_descriptive.csv`, `study1_confirmatory_family.csv`, `study1_h3_equivalence.csv` and `study1_item_sensitivity.csv` (the registered contrasts refitted without the one effort item whose top two scale labels differ);
  - the ordinal models, the Welch *t*-tests, the registered effect size and the per-image contrasts (sections 8 to 10): `study1_clmm_by_dimension.csv` (the ordinal model of each dimension, with each fit's convergence status), `study1_welch_ttests.csv`, `study1_bootstrap_d.csv` and `study1_per_stimulus_contrasts.csv`;
  - `study1_quant_run_manifest.csv` (section 13.1).
- In `models/`, as `.rds` files (R's saved-object format): `study1_lmm_{creativity,effort}.rds`, `study1_lmm_{creativity,effort}_maximal.rds`, `study1_lmm_{creativity,effort}_fullymaximal.rds`, `study1_lmm_joint.rds`, `study1_clmm_joint.rds` and `study1_clmm_{creativity,effort}.rds`.
- In `figures/`: `study1_fig1_main.{pdf,png}`, `study1_fig2_forest.{pdf,png}` and `study1_diagnostics.pdf`; copies of `study1_fig1_main.pdf` and `study1_fig2_forest.pdf` go to `Docs/Writing/Final Paper/figures/`.

### `Study1_02_Text.ipynb`

Its section 13 lists every output by name.

- In `nlp/`, six data files, none of which carries the condition or the rating:
  - `study1_text_measures.csv`: one row per response, the flags only, nineteen columns;
  - for the two checks run in every study, `study1_text_wordcounts.csv` (one row per response and content word, with the count, for every word that appears in at least two responses), `study1_text_vocabulary.csv` (those words and the number of responses each appears in) and `study1_text_tokens.csv` (one row per response, its distinct content words, from which the integration file computes the word overlaps);
  - for the general description, `study1_text_affect.csv` (one row per response: its number of content words, how many of them each norm file contains, and their mean valence, arousal, dominance and concreteness) and `study1_text_topics.csv` (one row per response and topic: the response's weight on that topic).
- In `tables/`:
  - the rules: `text_rules.txt` (every search pattern in full), `text_rules.sha256` (its checksum) and `text_rules_grounding.txt` (the grounding note on each rule);
  - what the rules matched: `text_audit_matches.txt` (matched and unmatched responses for every rule) and `text_candidate_words.txt` (words that behave like a rule's words without being on its list);
  - `text_keyness_{effort,creativity}.csv` (which words are distinctive of high against low ratings) and `text_corpus_summary.csv`;
  - the three topic tables: `text_topics_top_words.csv`, `text_topics_stability.csv` and `text_topics_embedding_agreement.csv`;
  - `study1_text_environment.csv` (the Python and package versions of the run) and `study1_text_run_manifest.csv`.

### `Study1_03_Integration.Rmd`

Its section 11 lists every output by name.

- In this folder: `study1_text_sessionInfo.txt` and `study1_text_package_versions.csv`, which record the R environment of the run.
- In `tables/`:
  - the join and the corpus (section 2): `study1_text_join_check.csv`, `study1_text_corpus_check.csv` and `study1_text_corpus_by_dimension.csv`;
  - what "effort" meant (section 3): `study1_text_effort_prevalence.csv`, `study1_text_effort_polarity_shares.csv`, `study1_text_effort_{detail,other,polarity}_lmm.csv`, `study1_text_image_detail_effort.csv` and `study1_text_effort_image_corr{,_rank}.csv`;
  - what "creativity" meant (section 4): `study1_text_creativity_prevalence.csv`, `study1_text_creativity_polarity_shares.csv`, `study1_text_polarity_shares_both.csv`, `study1_text_creativity_{concept,execution,polarity}_lmm.csv`, `study1_text_novelty_means.csv`, `study1_text_novelty_contrast{,_effort,_both}.csv`, `study1_text_novelty_by_arm.csv`, `study1_text_novelty_lmm.csv`, `study1_text_novelty_emmeans.csv`, `study1_text_novelty_within_between.csv`, `study1_text_image_concept_creativity.csv` and `study1_text_creativity_image_corr{,_rank}.csv`;
  - machine talk in the human-attribution arm (section 5): `study1_text_leakage_count.csv`, `study1_text_leakage_per_participant.csv`, `study1_text_belief_audit_counts.csv`, `study1_text_belief_audit_rate_ci.csv`, `study1_text_belief_audit_exclusion_refit.csv` and `study1_text_leakage_placebo.csv`;
  - prompt talk by arm (section 6): `study1_text_prompt_by_arm.csv`, `study1_text_prompt_by_arm_within_rating.csv` and `study1_text_prompt_gap_within_rating.csv`;
  - the five text tests (section 7): `study1_text_denotation_tests.csv` and `study1_text_denotation_slope_sensitivity.csv`;
  - the two checks run in every study (section 8): `study1_text_recoverability.csv` (how closely the words track the rating and the arm) and `study1_text_selfsimilarity_by_arm.csv` (within-person word overlap by arm);
  - the general description by arm (section 9): `study1_text_affect_by_arm.csv`, `study1_text_topics_by_arm.csv` and `study1_text_prediction_weights.csv`;
  - the run record (section 11): `study1_text_model_log.csv` (one row per step), `study1_text_fit_log.csv` (one row per mixed model, with its status), `study1_text_manifest.csv` and `study1_integration_run_manifest.csv`.
- In `models/`: `study1_text_effort_detail.rds`, `study1_text_creativity_concept.rds`, `study1_text_novelty_{creativity,effort}.rds`, `study1_text_novelty_by_arm_fits.rds` and `study1_text_denotation_glmm_fits.rds`. Section 5.5 also keeps a working file there, `study1_belief_audit_matched_cache_rule.rds`, which it rewrites only when its inputs have changed; it is not a result, and the manifest does not list it.
- In `figures/` (section 10): `study1_fig3_text_prevalence.{pdf,png}`, `study1_fig4_detail_vs_effort.{pdf,png}` and `study1_fig5_denotation_profiles.{pdf,png}`; the three PDFs are copied to `Docs/Writing/Final Paper/figures/`.

### `Study1_04_Robustness.Rmd`

Its section 9 lists every output by name.

- In `tables/`:
  - the Bayesian replication (section 2): `study1_brms_primary_fixed.csv` and `study1_brms_cumulative_fixed.csv`, and `study1_brms_prior_sensitivity.csv` only when the switch `RUN_PRIOR_SENSITIVITY` is TRUE;
  - the equivalence tests at wider bounds (section 3): `study1_equivalence_sensitivity.csv`;
  - what the design can detect and resolve (section 4): `study1_sensitivity_power.csv`, `study1_sensitivity_power_80pct.csv`, `study1_h3_equivalence_power.csv` and `study1_h4_resolution.csv`;
  - the covariate, length, engagement and stimulus-as-fixed refits (sections 5 to 7): `study1_covariate_robustness.csv`, `study1_length_covariate.csv`, `study1_engagement_{by_condition,trimmed_fits,per_participant}.csv` and `study1_stimulus_as_fixed.csv`;
  - the specification curve (section 8): `study1_specification_curve{,_failures,_counts}.csv`, and `study1_robustness_h1_contrast.csv` (the H1 contrast from every check beside the coefficient of the same model);
  - `study1_robustness_run_manifest.csv` (section 9.1).
- In `models/`: the Bayesian fits `study1_brms_primary_{creativity,effort}.rds` and `study1_brms_cumulative_{creativity,effort}.rds`, written when a fit is first made or has to be refitted and otherwise reused, and `study1_brms_primary_{creativity,effort}_priorwide.rds` only when `RUN_PRIOR_SENSITIVITY` is TRUE.
- In `figures/`: `study1_brms_ppc.pdf` (the posterior predictive check) and `study1_specification_curve_{creativity,effort}.pdf`, with copies of the latter two in `Docs/Writing/Final Paper/figures/`.

### `Study1_Supplements.Rmd`

- In `Docs/Writing/Final Paper/supplement/tables/`, one LaTeX fragment per supplementary table: `sup_table_1_robustness.tex`, `sup_table_2_text_rates.tex`, `sup_table_3_prompt_talk.tex`, `sup_table_attrition.tex`, `sup_table_balance.tex`, `sup_table_bootstrap_d.tex`, `sup_table_demographics.tex`, `sup_table_denotation_tests.tex`, `sup_table_denotation_slope_sensitivity.tex`, `sup_table_exclusions.tex`, `sup_table_full_lmm.tex`, `sup_table_fully_maximal.tex`, `sup_table_h2_ordinal.tex`, `sup_table_h3_equivalence.tex`, `sup_table_h3_equivalence_power.tex`, `sup_table_h4_resolution.tex`, `sup_table_h4_variance.tex`, `sup_table_holm_family.tex`, `sup_table_influence.tex`, `sup_table_item_sensitivity.tex`, `sup_table_joint_model.tex`, `sup_table_text_affect_by_arm.tex`, `sup_table_text_novelty_within_between.tex`, `sup_table_text_prediction_weights.tex`, `sup_table_text_recoverability.tex`, `sup_table_text_selfsimilarity_by_arm.tex`, `sup_table_text_topics_by_arm.tex`, `sup_table_text_topics_embedding_agreement.tex` and `sup_table_text_topics_stability.tex`.
- In `Docs/Writing/Final Paper/supplement/figures/`: `sup_fig_1a_specification_creativity.pdf`, `sup_fig_1b_specification_effort.pdf` and `sup_fig_2_brms_ppc.pdf`, copied unchanged from `figures/`.
- In `tables/`: `study1_supplements_run_manifest.csv`.

### `Study1_Figures.Rmd`

- `figures/study1_fig1_ratings.{pdf,png}`, copied to `Docs/Writing/Final Paper/figures/`.
- `tables/study1_inline.tex`, copied to `Docs/Writing/Final Paper/tables/`. This is the only file that writes `study1_inline.tex`.
- `tables/study1_figures_run_manifest.csv`.

## Other files and folders here

- `CHANGELOG.md` holds the edit history of the six source files. The source files themselves carry no edit history; anything of that kind lives there.
- `study1_sessionInfo.txt`, `study1_package_versions.csv`, `study1_text_sessionInfo.txt` and `study1_text_package_versions.csv` record the R version and package versions of the last run.
- `_internal_notes/`, `_retired_2026-09-03/`, `_backup_2026-09-01_pre-audit-edits/` and `_backup_2026-10-06_pre-review-edits/` hold working notes, files retired from the pipeline, and earlier copies of the source files. Each has a README. Nothing in them is needed to run the pipeline, and `.gitignore` keeps them out of version control.
- `_retired_outputs_2026-09-04/` holds an unchanged copy of the outputs of the 2026-09-04 run (tables, figures, models, the data files in `nlp/`, the knitted reports and the Study 1 files in the paper folder), made before the 2026-10-07 run wrote over them. `CHANGELOG.md` says what it contains; `.gitignore` keeps it out of version control.
- `.gitignore` also excludes the knitted HTML reports, knitr's cache and figure folders, and stray plot files, all of which are regenerated by a knit.
- `nlp/agency_rule_candidates/` holds side work on a candidate text measure, a rule for whether the artist, the tool or no one is the grammatical subject of the verb that describes how the work was made. It is kept outside the published pipeline: no file of the pipeline reads it, the public copy of the project leaves it out, and section 12 of `Study1_03_Integration.Rmd` says why the rule is not used.

## Software

R (version recorded in `study1_sessionInfo.txt`) with the packages each `.Rmd` file loads in its first code chunk; the main ones are `tidyverse`, `lme4` and `lmerTest` for the mixed-effects models, `emmeans` for contrasts, `ordinal` for the ordinal models, and, for the robustness file, `brms` for the Bayesian fits and `simr` for power by simulation; the integration file uses `glmnet` for its penalised regressions. Python 3.12 for the notebook, with `pandas` and `numpy` throughout, `scikit-learn` and `scipy` for the topic model, and `sentence-transformers` with the local files of the all-mpnet-base-v2 model for the check on the topics in section 11. When the package or the model files are missing, that check records that it did not run and the rest of the notebook carries on. "Running the notebook" above gives the versions of the 2026-10-07 run and the command that runs the notebook on a named kernel.
