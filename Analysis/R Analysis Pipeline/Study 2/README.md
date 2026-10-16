# Study 2 analysis pipeline

In Study 1, telling participants that the artist Alex made an artwork by prompting an AI system lowered its rated creativity. Study 2 asks whether that penalty reaches a second work that Alex makes by hand from the first. If an AI origin taints whatever is built on it, the penalty holds at every level of modification. If raters judge the second work partly by the first, the penalty is largest when the second work is the first unchanged and shrinks as Alex changes more. If they judge only what Alex added, it is absent. Each of 235 participants was told that Alex made the first works either with design software and digital sketching tools (Human) or by prompting an AI system (AI). Each then saw every one of ten source images at three levels of modification (None, Slight and Dramatic), rated each second work on transformativeness, essence change and creativity, and wrote a justification after every rating.

The specification is the registration, `Docs/Preregistration/AsPredicted/Study2_AsPredicted.md`, registered on OSF (the Open Science Framework) on 8 October 2026 as part of one Open-Ended Registration of the five studies, project https://osf.io/u3d69. The code implements what it names, and nothing it computes beyond it is presented as confirmatory.

## The files

| File | What it does |
|---|---|
| `Study2_01_Quant.Rmd` | Reads the two Qualtrics exports and the survey file, applies the five registered exclusion steps and checks every count the registration states, writes the long data file, and runs the registered models, the twelve registered tests with Holm's correction, the equivalence tests, the cumulative-link checks and the exploratory source contrast at each modification level. |
| `Study2_02_Text.ipynb` | Measures the 20,659 analysed justifications with Study 1's eight word lists, unchanged, and writes the word, tone and topic tables, without reading the condition, the modification label the models use or the rating. |
| `Study2_03_Integration.Rmd` | Joins the text measures to the ratings and the condition and runs the two registered text checks on the creativity justifications and the exploratory description the registration names. |
| `Final_-_AI_Copyright_-_Study_2.qsf` | The survey definition exported from Qualtrics, from which `Study2_01_Quant.Rmd` reads each item's answer options in the order they were shown. |
| `CHANGELOG.md` | The edit history of the source files, which carry none themselves. |

An R Markdown file (`.Rmd`) mixes R code with text and is knitted, that is, run from top to bottom into an HTML report. A Jupyter notebook (`.ipynb`) is a file of Python cells run in order.

The files use the shared helpers one folder up: `shared/R/qualtrics_import.R` (reading the exports, the exclusion flow, scoring by position, reshaping), `shared/R/fit_status.R` (fit status, the run record, the participant shuffle), `shared/R/text_checks.R` (the two registered text checks) and `shared/python/study_text.py` (the text measurement). Each of those folders has a README.

## Run order

1. `Study2_01_Quant.Rmd`
2. `Study2_02_Text.ipynb`
3. `Study2_03_Integration.Rmd`

The notebook reads the long data file that the first file writes, and the integration file reads both. The integration file checks every input against the run manifest of the run that wrote it and stops if one is missing or differs.

## The blind switch

A blind run is the whole analysis on shuffled labels: every model, table and check is produced and can be checked for errors, but no number describes the real conditions. Both R Markdown files begin with

```r
UNBLIND <- as.logical(Sys.getenv("UNBLIND_STUDY2", "FALSE"))
```

so a run is blind unless the environment variable `UNBLIND_STUDY2` (a named setting the operating system passes to every program it starts) is set to `TRUE`. While it is blind:

- `Study2_01_Quant.Rmd` shuffles three labels right after the data are built and before any summary or model. The source labels are dealt again across participants, so each condition keeps its 122 or 113 participants. Modification varies within each participant, so a shuffle across participants would leave its link to the ratings in place; its labels are dealt again among the versions of each source image that a participant saw, so every participant keeps the same number of works at each level. The ten image-kind labels are dealt again among the ten source images, five of each kind as before;
- `Study2_03_Integration.Rmd` shuffles the source labels again and shuffles the ratings within each question across all its responses, because some of its analyses relate the words to the rating alone, which a label shuffle cannot blind;
- every shuffle uses the registered seed, 20260421;
- every output goes to a `blind_run/` subfolder of the folder its real counterpart goes to: `blind_run/` for the long data file and the HTML reports, and `tables/blind_run/` for the tables. A blind run that would write its report anywhere else stops in its first chunk, before it writes anything, and so does an unblinded run that would write its report to `blind_run/`;
- each knitted report opens with a sentence saying what is shuffled and that nothing in it is a result.

The exclusion flow, the registered counts and the item scales do not depend on the labels and are the same in both modes. The notebook reads no label and no rating, so it has no modes; it reads the unblinded long data file when one exists and the blind one otherwise, and writes to `nlp/` and `tables/` either way.

### How to run it blind

From the Study 2 folder, in a shell where `UNBLIND_STUDY2` is not set:

```sh
Rscript -e 'rmarkdown::render("Study2_01_Quant.Rmd", output_dir = "blind_run")'
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python312 Study2_02_Text.ipynb
Rscript -e 'rmarkdown::render("Study2_03_Integration.Rmd", output_dir = "blind_run")'
```

In RStudio, the Knit button does the same for each R Markdown file, through the `knit:` line at the top of the file, and the notebook runs cell by cell on the `python312` kernel.

### How to unblind

The registration is filed, and the real run was made on 8 October 2026 with the steps below.

1. Set the environment variable `UNBLIND_STUDY2` to `TRUE`: in the shell that runs R (`export UNBLIND_STUDY2=TRUE`), or, for RStudio's Knit button, by adding the line `UNBLIND_STUDY2=TRUE` to the file `~/.Renviron` and restarting R. Do not edit the first line of the R Markdown files instead: the `knit:` line that chooses the report folder reads the variable, not that line.
2. Knit `Study2_01_Quant.Rmd` and then `Study2_03_Integration.Rmd`.

From the Study 2 folder:

```sh
export UNBLIND_STUDY2=TRUE
Rscript -e 'rmarkdown::render("Study2_01_Quant.Rmd")'
Rscript -e 'rmarkdown::render("Study2_03_Integration.Rmd")'
```

The notebook need not run again. It reads no label and no rating, and the blind and the real long data files hold the same participants, second works, questions and text in the same order, so its tables are the same either way. An unblinded run writes its reports beside the R Markdown files, its tables to `tables/` and its long data file to this folder. The blind outputs in `blind_run/` and `tables/blind_run/` stay where they are and can be deleted.

## What each file writes

Paths are relative to this folder. In a blind run, read `blind_run/` for this folder and `tables/blind_run/` for `tables/` in the two R Markdown lists.

### `Study2_01_Quant.Rmd`

- `study2_long_with_text.csv`: one row per participant, second work and question (20,659 rows), with the condition, the source image (`image`), the second work (`work_id`, the source image and the level shown), the image kind and modification labels the models use, the rating scored by position, the justification and `label_mode` (`real` or `shuffled`). The two six-point items are not in it.
- In `tables/`:
  - `study2_exclusion_flow.csv` (the five registered steps, 275 records to 235, each beside its registered count), `study2_sample_checks.csv` (every count the registration states beside the count the data give), `study2_item_scales.csv` and `study2_cell_counts.csv`;
  - `study2_emmeans.csv`: the estimated marginal means of each measure by modification level, by source condition, and by both;
  - `study2_confirmatory_family.csv`: the four registered tests on each measure, twelve rows with Holm's correction over the twelve and the reading of each;
  - `study2_equivalence.csv`: the equivalence test of the Human minus AI difference on each measure, with its 90 percent interval, both one-sided p-values and the Holm verdict;
  - `study2_hypothesis_readings.csv`: H1, H2 and H3 read on each measure from the Holm family, and H1 and H2 read over the three measures, where each holds only when it holds on every measure;
  - `study2_clmm_check.csv`: the cumulative-link check of tests 1, 2 and 4 beside the linear model's verdicts;
  - `study2_source_by_modification.csv`: the exploratory Human minus AI contrast at each modification level, uncorrected;
  - `study2_fit_status.csv`, `study2_quant_run_inputs.csv`, `study2_quant_sessionInfo.txt`, `study2_quant_package_versions.csv` and, written last, `study2_quant_run_manifest.csv`. A blind run also writes a `BLIND_RUN.txt` note into each folder it writes to.

### `Study2_02_Text.ipynb`

- In `nlp/`, six data files, none of which carries the condition, a model label or the rating: `study2_text_measures.csv`, `study2_text_wordcounts.csv`, `study2_text_vocabulary.csv`, `study2_text_tokens.csv`, `study2_text_affect.csv` and `study2_text_topics.csv`.
- In `tables/`: `study2_text_rules.txt` (every rule in full), `study2_text_rules.sha256` (its checksum, which `shasum -a 256 -c study2_text_rules.sha256` checks from `tables/`), `study2_text_rules_grounding.txt`, `study2_text_topics_top_words.csv`, `study2_text_topics_stability.csv`, `study2_text_topics_embedding_agreement.csv`, `study2_text_environment.csv` and, written last, `study2_text_run_manifest.csv`.

The notebook checks that the shared module's rules, written out for Study 1, equal Study 1's deposited `tables/text_rules.txt` and its checksum, which shows the word lists are unchanged. The registration says resampling uses the Study 1 seed, 20260421, and the stability rule of the topic model resamples participants, so the notebook sets that seed for every random step of the topic model and its agreement check: the ten stability refits use 20260421 to 20260430, and the final topic fit and the grouping use 20260421. `tables/study2_text_environment.csv` records them. The seed alone does not make a rerun give the same numbers. The grouping, made by k-means, a method that splits the responses into a set number of groups of similar embeddings, runs on one processor thread (one strand of computation), and the environment table records that too. On several threads, k-means adds up its numbers in pieces, one per thread, and combines the pieces in the order the threads finish, which changes from run to run; since rounding depends on that order, its groups, and with them the agreement index in `tables/study2_text_topics_embedding_agreement.csv`, can differ between runs. The seed and the single thread together make a rerun give the same numbers.

### `Study2_03_Integration.Rmd`

- In `tables/`:
  - `study2_text_join_check.csv` and `study2_text_wordcount_check.csv`;
  - the first registered check, on creativity: `study2_text_recoverability.csv`, with the reading of each row;
  - the second registered check, on creativity: `study2_text_selfsimilarity_by_arm.csv` and `study2_text_selfsimilarity_per_person.csv`;
  - the exploratory description: `study2_text_recoverability_other_measures.csv` and `study2_text_selfsimilarity_other_measures.csv` (the same two checks on transformativeness and essence change), `study2_text_affect_by_arm.csv`, `study2_text_topics_by_arm.csv` and `study2_text_prediction_weights.csv` (the words the first check leans on most, from a lasso model of the rating and one of the source condition with the rating held in it, on each measure);
  - `study2_text_fit_log.csv`, `study2_integration_run_inputs.csv`, `study2_integration_sessionInfo.txt`, `study2_integration_package_versions.csv` and, written last, `study2_integration_run_manifest.csv`.

Every run manifest lists the outputs of its run with their SHA-256 checksums (a 64-character fingerprint of a file's exact bytes). Each file deletes its earlier manifest when it starts and writes the new one last, so a manifest on disk means the run reached its end.

## Environment

- R 4.5.2 with readr 2.2.0, dplyr 1.2.1, tidyr 1.3.2, tibble 3.3.1, jsonlite 2.0.0, Matrix 1.7.5, lme4 2.0.1, lmerTest 3.2.1, emmeans 2.0.3, ordinal 2025.12.29, glmnet 5.0, rmarkdown 2.31 and knitr 1.51, with pandoc for knitting. Each R Markdown file records its session and package versions in `tables/`.
- Python 3.12 for the notebook, run on the Jupyter kernel named `python312`, with pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.5.2, SciPy 1.13.0, sentence-transformers 3.3.1 and PyTorch 2.5.1. The notebook records its versions in `tables/study2_text_environment.csv`. The sentence-embedding model all-mpnet-base-v2 is loaded only from the local Hugging Face cache, and nothing is downloaded; the shared Python README says how to fetch it once.

Paths are found from each file's own folder. These environment variables name other folders: `STUDY2_DIR` (this folder), `STUDY2_PROJECT_ROOT` (the folder that holds `Data` and `Analysis`), `STUDY_SHARED_R` and `STUDY_SHARED_PYTHON` (the shared helpers) and `STUDY1_DIR` (the Study 1 folder whose rules the notebook compares). Printed paths are relative, so no report names a folder particular to one machine.

On a twelve-core machine shared with another run, the first file took under two minutes, the notebook about seven minutes and the integration file about 53 minutes. Most of that time goes to the permutations of the two text checks, which the integration file runs on all three measures, eight of them at once.
