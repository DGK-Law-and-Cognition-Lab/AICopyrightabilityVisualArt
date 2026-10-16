# Study 3 analysis pipeline

Study 3 asks why the AI label lowers ratings of an artwork. Telling participants that the artist prompted an AI system could signal that little work went into the image, or people could discount the process itself. Only the first account predicts that stated hours shrink the gap between the Human and AI conditions until it is negligible at 100 hours. Each of 85 participants was told that the artist Alex either drew the works himself (Human) or prompted an AI system (AI), and rated nine of ten images on creativity and on effort, three images each at a stated time of under 1 hour, 10 hours and 100 hours, with a written justification beside every rating.

The registration, `Docs/Preregistration/AsPredicted/Study3_AsPredicted.md`, is the specification. It keeps the questions of the AsPredicted form, and it was registered on the Open Science Framework (OSF) on 8 October 2026, with the registrations of the other four studies, as one Open-Ended Registration in project https://osf.io/u3d69. Nothing this folder computes beyond it is presented as confirmatory.

## The files

| File | What it does |
|---|---|
| `Study3_01_Quant.Rmd` | Reads the two Qualtrics exports and the survey file, applies the registered exclusions, writes the long data file, and fits the registered models, tests, equivalence tests and decision rule on the ratings. |
| `Study3_02_Text.ipynb` | Measures the justifications with Study 1's eight word lists and writes the word, affect and topic tables, without reading the condition, the stated time or the rating. |
| `Study3_03_Integration.Rmd` | Joins the text measures to the ratings and the condition and runs the two registered text checks and the exploratory description the registration names. |
| `Final_-_AI_Copyright_-_Study_3.qsf` | The survey definition exported from Qualtrics, from which `Study3_01_Quant.Rmd` reads each item's answer options in the order they were shown. |
| `CHANGELOG.md` | The edit history of the source files, which carry none themselves. |

An R Markdown file (`.Rmd`) mixes R code with text and is knitted, that is, run from top to bottom into an HTML report. A Jupyter notebook (`.ipynb`) is a file of Python cells run in order.

The files use the shared helpers one folder up: `shared/R/qualtrics_import.R` (reading the exports, the exclusion flow, scoring by position), `shared/R/fit_status.R` (fit status, the run record, the participant shuffle), `shared/R/text_checks.R` (the two registered text checks) and `shared/python/study_text.py` (the text measurement). Each of those folders has a README.

## Run order

1. `Study3_01_Quant.Rmd`
2. `Study3_02_Text.ipynb`
3. `Study3_03_Integration.Rmd`

The notebook reads the long data file that the first file writes, and the integration file reads both. The integration file checks every input against the run manifest of the run that wrote it and stops if one is missing or differs.

## The blind switch

The registration says its analyses were written before any of them was run, so every run before it was filed was blind. A blind run is the whole analysis on shuffled labels: every model, table and check is produced and can be checked for errors, but no number describes the real conditions.

Both R Markdown files begin with

```r
UNBLIND <- as.logical(Sys.getenv("UNBLIND_STUDY3", "FALSE"))
```

so a run is blind unless the environment variable `UNBLIND_STUDY3` (a named setting the operating system passes to every program it starts) is set to `TRUE`. While it is blind:

- right after the data are built and before any summary or model, the source labels are shuffled across participants, so each condition keeps its 43 or 42 participants, and the stated-time labels are shuffled within each participant across that participant's nine images, so each participant keeps three images at each time. Stated time varies within each participant, so a shuffle across participants would leave the link between an image's stated time and its ratings in place;
- `Study3_03_Integration.Rmd` also shuffles the ratings, within each question across all its scored responses. Some of its analyses relate the words to the rating alone, with no label in them, and a label shuffle cannot blind those;
- every shuffle uses the registered seed, 20260421;
- every output goes to a `blind_run/` subfolder of the folder its real counterpart goes to: `blind_run/` for the long data file and the HTML reports, and `tables/blind_run/` for the tables. A blind run that would write its report anywhere else stops in its first chunk, before it writes anything, and so does an unblinded run that would write its report to `blind_run/`;
- each knitted report opens with a sentence saying what is shuffled and that nothing in it is a result;
- `tables/blind_run/study3_time_contrast_for_study5.csv` is marked not usable.

The exclusion flow, the cell counts, the item scales and every table not split by condition or rating are the same in both modes. The notebook reads no label and no rating, so it has no modes; it reads the unblinded long data file when one exists and the blind one otherwise, and writes to `nlp/` and `tables/` either way.

### How to run it blind

Run these from the Study 3 folder, in a shell where `UNBLIND_STUDY3` is not set:

```sh
Rscript -e 'rmarkdown::render("Study3_01_Quant.Rmd", output_dir = "blind_run")'
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python312 Study3_02_Text.ipynb
Rscript -e 'rmarkdown::render("Study3_03_Integration.Rmd", output_dir = "blind_run")'
```

In RStudio, the Knit button does the same for each R Markdown file, through the `knit:` line at the top of the file, and the notebook runs cell by cell on the `python312` kernel.

### How to unblind

The registration is filed, so the switch may be set.

1. Set the environment variable `UNBLIND_STUDY3` to `TRUE`: in the shell that runs R (`export UNBLIND_STUDY3=TRUE`), or, for RStudio's Knit button, by adding the line `UNBLIND_STUDY3=TRUE` to the file `~/.Renviron` and restarting R. Do not edit the first line of the R Markdown files instead: the `knit:` line that chooses the report folder reads the variable, not that line.
2. Knit `Study3_01_Quant.Rmd`, run `Study3_02_Text.ipynb`, and knit `Study3_03_Integration.Rmd`, in that order.

From the Study 3 folder:

```sh
export UNBLIND_STUDY3=TRUE
Rscript -e 'rmarkdown::render("Study3_01_Quant.Rmd")'
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python312 Study3_02_Text.ipynb
Rscript -e 'rmarkdown::render("Study3_03_Integration.Rmd")'
```

An unblinded run writes its reports beside the R Markdown files and its tables to `tables/`. The real run was made on 8 October 2026, after the registration was filed: both R Markdown files were knitted with `UNBLIND_STUDY3` set to `TRUE`, and the notebook was not run again, because it reads no label and no rating. The blind outputs stay in `blind_run/` and `tables/blind_run/`, and none of them is a result.

## What each file writes

Paths are relative to this folder. In a blind run, read `blind_run/` for the folder and `tables/blind_run/` for `tables/` in the two R Markdown lists.

### `Study3_01_Quant.Rmd`

- `study3_long_with_text.csv`: one row per participant, image and rating (1,530 rows), with the condition, the stated time, the rating scored by position and the justification. The five ratings that have no score (three left blank, two with an answer code the final survey does not offer) are empty.
- In `tables/`:
  - `study3_exclusion_flow.csv` (the registered steps, 100 to 85 records, each beside its registered count), `study3_sample_checks.csv` (each count the registration states beside the count the data give), `study3_item_scales.csv`, `study3_unscored_answers.csv` and `study3_cell_counts.csv`;
  - `study3_lmm_ftests.csv`: the F tests of source, stated time and their interaction on each rating, with Satterthwaite degrees of freedom and the Holm correction over the six;
  - `study3_emmeans_cells.csv`, `study3_gap_by_time.csv` (the Human minus AI gap at each time) and `study3_time_contrast.csv` (100 hours minus under 1 hour, averaged over source);
  - `study3_equivalence.csv`: the 100-hour gap's 90 percent interval against plus or minus 0.224 rating points, in the registered model and in the random-slope refit, with whether that refit could estimate all its variance terms;
  - `study3_decision.csv`: the registered verdict on each rating (time closes the gap, the gap persists, or inconclusive) with every quantity it rests on;
  - `study3_time_contrast_for_study5.csv`: the creativity 100 hours minus under 1 hour contrast and its standard error, from which Study 5's editing-time bound is fixed;
  - `study3_clmm_check.csv`: the cumulative-link check of each Holm verdict;
  - `study3_fit_status.csv`, `study3_quant_run_inputs.csv`, `study3_quant_sessionInfo.txt` and `study3_quant_run_manifest.csv`.

### `Study3_02_Text.ipynb`

- In `nlp/`, six data files, none of which carries the condition, the stated time or the rating: `study3_text_measures.csv`, `study3_text_wordcounts.csv`, `study3_text_vocabulary.csv`, `study3_text_tokens.csv`, `study3_text_affect.csv` and `study3_text_topics.csv`.
- In `tables/`: `study3_text_rules.txt` (every rule in full), `study3_text_rules.sha256` (its checksum, which `shasum -a 256 -c study3_text_rules.sha256` checks from `tables/`), `study3_text_rules_grounding.txt`, `study3_text_topics_top_words.csv`, `study3_text_topics_stability.csv`, `study3_text_topics_embedding_agreement.csv`, `study3_text_environment.csv` and `study3_text_run_manifest.csv`.

The notebook also checks that the shared module's rules, written out for Study 1, equal Study 1's deposited `tables/text_rules.txt` and its checksum, which shows the word lists are unchanged. It sets the registered seed, 20260421, for every random step of the topic model and its agreement check: the ten stability refits use 20260421 to 20260430, and the final topic fit and the grouping use 20260421. `tables/study3_text_environment.csv` records them.

### `Study3_03_Integration.Rmd`

- In `tables/`:
  - `study3_text_join_check.csv` and `study3_text_wordcount_check.csv`;
  - the first registered check: `study3_text_recoverability.csv` and `study3_text_recoverability_readings.csv`;
  - the second registered check: `study3_text_selfsimilarity_by_arm.csv` (with the Holm correction across the two ratings) and `study3_text_selfsimilarity_per_person.csv`;
  - the exploratory description: `study3_text_wordlist_prevalence.csv`, `study3_text_wordlist_comparisons.csv`, `study3_text_affect_by_arm.csv`, `study3_text_topics_by_arm.csv` and `study3_text_prediction_weights.csv`;
  - `study3_text_fit_log.csv`, `study3_integration_run_inputs.csv`, `study3_integration_sessionInfo.txt` and `study3_integration_run_manifest.csv`.

Every run manifest lists the outputs of its run with their SHA-256 checksums (a 64-character fingerprint of a file's exact bytes). Each file deletes its earlier manifest when it starts and writes the new one last, so a manifest on disk means the run reached its end.

## Environment

- R 4.5.2 with dplyr 1.2.1, tidyr 1.3.2, tibble 3.3.1, readr 2.2.0, jsonlite 2.0.0, lme4 2.0.1, lmerTest 3.2.1, emmeans 2.0.3, ordinal 2025.12.29, glmnet 5.0, Matrix 1.7.5, rmarkdown 2.31 and knitr 1.51. Each R Markdown file records its session in `tables/`.
- Python 3.12 for the notebook, run on the Jupyter kernel named `python312`, with pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.5.2, SciPy 1.13.0, sentence-transformers 3.3.1 and PyTorch 2.5.1. The notebook records its versions in `tables/study3_text_environment.csv`. The sentence-embedding model all-mpnet-base-v2 is loaded only from the local Hugging Face cache, and nothing is downloaded; the shared Python README says how to fetch it once.

Paths are found from each file's own folder. These environment variables name other folders: `STUDY3_DIR` (this folder), `STUDY3_PROJECT_ROOT` (the folder that holds `Data` and `Analysis`), `STUDY_SHARED_R` and `STUDY_SHARED_PYTHON` (the shared helpers) and `STUDY1_DIR` (the Study 1 folder whose rules the notebook compares). Printed paths are relative, so no report names a folder particular to one machine.

On an eight-core run the first file takes under a minute, the notebook about four minutes and the integration file about twelve minutes, most of it in the permutation tests of the recoverability check and the topic comparison.
