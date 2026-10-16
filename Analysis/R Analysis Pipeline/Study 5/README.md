# Study 5 analysis pipeline

Study 5 asks whether the time Alex is said to have spent making a second work from a first artwork changes how people judge that second work. The registration calls that time editing time: less than 1 hour, 10 hours or 100 hours. It also asks whether editing time changes the source penalty, the lower rating a second work gets when its first artwork is attributed to AI. Two hundred and twenty-three participants each rated 18 second works on transformativeness, essence change and creativity, and wrote a justification after every rating.

The specification is the registration, `Docs/Preregistration/AsPredicted/Study5_AsPredicted.md`. It keeps the questions of the AsPredicted form, and it was registered on the Open Science Framework (OSF) on 8 October 2026, with the registrations of the other four studies, as one Open-Ended Registration in project https://osf.io/u3d69. The code implements what it names and nothing else.

Everything needed to run the analysis is in this folder, apart from three things it reads from elsewhere in the project: the two Qualtrics exports in `Data/Study 5/`, the shared helpers in `../shared/` (R in `shared/R/`, Python in `shared/python/`), and two files from Study 1 (its deposited rules, which the text notebook compares with its own, and the word norms in `Study 1/nlp/norms/`).

## The files

- `study5_build.py` builds the data from the two Qualtrics exports and the survey file, and writes `study5_long.csv` (one row per participant, second work and rating, 12,042 rows), `study5_wide.csv` and three tables in `tables/`.
- `Study5_01_Quant.Rmd` rebuilds the same data with the shared R helpers and checks it equals `study5_long.csv`, applies the five registered exclusion steps, fits the registered rating models and runs the registered tests.
- `Study5_02_Text.ipynb` measures the 12,042 justifications with Study 1's eight word lists, unchanged, without ever reading the condition or the rating.
- `Study5_03_Integration.Rmd` joins the text measures to the ratings and the source condition, and runs the two registered text checks and the four exploratory text descriptions.
- `Final_-_AI_Copyright_-_Study_5.qsf` is the survey file exported from Qualtrics; the build and `Study5_01_Quant.Rmd` read each rating item's answer options from it.

An `.Rmd` file is R Markdown: R code and text that is knitted, that is, run from top to bottom into an HTML report. An `.ipynb` file is a Jupyter notebook of Python cells run in order.

## Run order

1. `python3 study5_build.py` (already run; rerun it only if the exports change).
2. `Study5_01_Quant.Rmd`.
3. `Study5_02_Text.ipynb`, at any point after step 1, since it reads only `study5_long.csv`.
4. `Study5_03_Integration.Rmd`, after steps 2 and 3, and in the same mode as step 2.

Knit the two `.Rmd` files from the R console, with this folder as the working directory. A blind run (see "The blind switch" below) is

```r
rmarkdown::render("Study5_01_Quant.Rmd", output_dir = "blind_run")
rmarkdown::render("Study5_03_Integration.Rmd", output_dir = "blind_run")
```

or open each file in RStudio and press the Knit button, which does the same: the `knit:` line at the top of each file sends a blind run's HTML report to `blind_run/`. Without `output_dir = "blind_run"`, `rmarkdown::render()` puts a blind report beside the `.Rmd` file, outside `blind_run/`, where it replaces the report of the real run. The commands for an unblinded run are under "How to unblind".

Run the notebook from this folder with the Python 3.12 kernel:

```sh
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=python312 Study5_02_Text.ipynb
```

The random steps of the notebook, all in the topic model and its agreement check, start from 20260903, the seed the registration names for the text code; a seed is the number that starts a random-number generator. The R files use the seed it names for R, 20260421.

The seed alone does not make a rerun give the same numbers. The agreement check groups the sentence embeddings with k-means, a method that splits the responses into a set number of groups of similar embeddings, and compares that grouping with the topics through the adjusted Rand index, a measure of how well two groupings agree, where 0 is the agreement expected by chance and 1 is perfect agreement. The shared module runs the k-means step on one processor thread (one strand of computation), which `tables/study5_text_environment.csv` records. On several threads, k-means adds up its numbers in pieces, one per thread, and combines the pieces in the order the threads finish, which changes from run to run; since rounding depends on that order, its groups can differ between runs. The seed and the single thread together make a rerun give the same numbers. No other file reads the index in `tables/study5_text_topics_embedding_agreement.csv`.

`Study5_01_Quant.Rmd` takes one to three minutes and the notebook four to six. `Study5_03_Integration.Rmd` takes ten to fifteen minutes, because the first registered text check reruns its ridge regressions 400 times on 4,014 creativity justifications and the mixed model of each topic is refitted 200 times; the permutations run on up to eight processor cores.

## What each file writes

In an unblinded run the tables go to `tables/` and `study5_long_with_text.csv` to this folder. A blind run writes each into a `blind_run/` subfolder of the folder its real counterpart goes to: the tables into `tables/blind_run/`, and the long data and the HTML reports into `blind_run/`. The text notebook is blind by construction and always writes to `nlp/` and `tables/`.

`Study5_01_Quant.Rmd`:

- `study5_long_with_text.csv`: the long data with the justifications, the condition and the rating, for the integration file. A blind run writes the shuffled labels, and its `label_mode` column says `shuffled`.
- `study5_exclusion_flow_registered.csv` and `study5_cell_counts_registered.csv`: the five registered exclusion steps (259, 259, 242, 226, 225, 223) and the six cells (Human 37, 37, 38; AI 35, 38, 38).
- `study5_lmm_fit_status.csv` and `study5_lmm_anova.csv`: the status of every linear mixed model (error, convergence, singularity) and every F test.
- `study5_confirmatory_family.csv`: the six confirmatory tests with Holm's correction.
- `study5_emmeans_editing_time.csv` and `study5_emmeans_source_by_modification.csv`: the estimated marginal means.
- `study5_equivalence_editing_time.csv` and `study5_equivalence_source.csv`: the two registered equivalence tests and their verdicts.
- `study5_clmm_fit_status.csv` and `study5_clmm_holm_check.csv`: the cumulative-link models and whether they agree with each Holm verdict.
- `study5_rescaled_family.csv`: the six tests of the second analysis, with every item rescaled from 0 to 1.
- `study5_quant_run_inputs.csv`, `study5_quant_sessionInfo.txt`, `study5_quant_package_versions.csv` and, written last, `study5_quant_run_manifest.csv`. A blind run also writes a `BLIND_RUN.txt` note into each folder it writes to.

`Study5_02_Text.ipynb`:

- In `nlp/`: `study5_text_measures.csv`, `study5_text_wordcounts.csv`, `study5_text_vocabulary.csv`, `study5_text_tokens.csv`, `study5_text_affect.csv` and `study5_text_topics.csv`. None carries the condition, the rating or the text.
- In `tables/`: `study5_text_rules.txt`, `study5_text_rules.sha256`, `study5_text_rules_grounding.txt`, `study5_text_topics_top_words.csv`, `study5_text_topics_stability.csv`, `study5_text_topics_embedding_agreement.csv`, `study5_text_environment.csv` and, written last, `study5_text_run_manifest.csv`.

`Study5_03_Integration.Rmd`:

- `study5_text_join_check.csv`, `study5_text_recoverability.csv` and `study5_text_selfsimilarity_by_arm.csv`: the join and the two registered checks.
- `study5_text_machine_made_count.csv`, `study5_text_affect_by_arm.csv`, `study5_text_topics_by_arm.csv` and `study5_text_prediction_weights.csv`: the four exploratory descriptions.
- `study5_text_fit_log.csv`, `study5_integration_run_inputs.csv`, `study5_integration_sessionInfo.txt`, `study5_integration_package_versions.csv` and, written last, `study5_integration_run_manifest.csv`.

Each run manifest lists the outputs of its run with their SHA-256 checksums, 64-character fingerprints of the files' exact bytes. Each file deletes its earlier manifest when it starts, so a manifest on disk means the run reached its end. Knitting also writes an HTML report of each `.Rmd` file: into `blind_run/` in a blind run, and beside the `.Rmd` file in an unblinded run.

## The environment

R 4.5.2 with readr 2.2.0, dplyr 1.2.1, tidyr 1.3.2, tibble 3.3.1, purrr 1.2.2, jsonlite 2.0.0, Matrix 1.7-5, lme4 2.0-1, lmerTest 3.2-1, emmeans 2.0.3, ordinal 2025.12-29, glmnet 5.0, rmarkdown 2.31 and knitr 1.51, with pandoc for knitting. Each knit records its versions in its `sessionInfo` and `package_versions` files.

Python 3.12 through the Jupyter kernel named `python312`, with pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.5.2, SciPy 1.13.0, sentence-transformers 3.3.1 and PyTorch 2.5.1, and the files of the all-mpnet-base-v2 sentence-embedding model already in the local Hugging Face cache. The notebook never downloads the model. Each run records its versions in `tables/study5_text_environment.csv`.

Paths start from each file's own folder. These environment variables (named settings the shell passes to R or Python when it starts) name other folders:

| Variable | What it names |
|---|---|
| `STUDY5_DIR` | the Study 5 folder |
| `STUDY5_PROJECT_ROOT` | the project root, the folder that holds `Data` and `Analysis` |
| `STUDY5_OUTPUT_DIR` | the folder the R files write their outputs under (the Study 5 folder by default) |
| `STUDY_SHARED_R`, `STUDY_SHARED_PYTHON` | the shared R and Python helpers |
| `STUDY1_DIR`, `STUDY3_DIR` | the Study 1 and Study 3 folders |

## The blind switch

The registration says its analyses were written before any of them was run. Until it was filed, every run was blind: no outcome model was fitted on the real labels and no rating was summarised by condition.

Each R file begins with

```r
UNBLIND <- as.logical(Sys.getenv("UNBLIND_STUDY5", "FALSE"))
```

While `UNBLIND` is FALSE, `Study5_01_Quant.Rmd` shuffles the condition labels across participants right after the data are built and before any summary or model, with seed 20260421. Source and editing time move together, as one unit, because together they are one between-participant cell, so every cell keeps its size. Every output goes to a `blind_run/` folder, and each knitted report opens with a sentence saying that the labels are shuffled and nothing in it is a result. A blind run shows that the code runs, that the fits converge and that the tables have the right shape. Its numbers describe no real condition. The exclusion flow, the cell counts and the item scales do not depend on the labels and are the same in both modes.

The editing-time equivalence bound comes from Study 3: the absolute size of its registered creativity contrast, 100 hours minus less than 1 hour, read from `Study 3/tables/study3_time_contrast_for_study5.csv`, which an unblinded run of `Study3_01_Quant.Rmd` writes. The file gives a bound only when its creativity row says `blind_run` FALSE and `usable` TRUE. A blind run that cannot find such a file uses a placeholder bound, labelled as a placeholder in its table. An unblinded run stops with a message saying that Study 3 must be unblinded and run first.

## How to unblind

The registration is filed, so the switch may be set.

1. Unblind and run Study 3, so that `Study 3/tables/study3_time_contrast_for_study5.csv` holds its registered creativity contrast.
2. Set the switch to TRUE and knit in order, `Study5_01_Quant.Rmd` and then `Study5_03_Integration.Rmd`. From the R console, with this folder as the working directory:

   ```r
   Sys.setenv(UNBLIND_STUDY5 = "TRUE")
   rmarkdown::render("Study5_01_Quant.Rmd")
   rmarkdown::render("Study5_03_Integration.Rmd")
   ```

   To use RStudio's Knit button instead, add the line `UNBLIND_STUDY5=TRUE` to the file `~/.Renviron` and restart R. Do not edit the files themselves: the `knit:` line that chooses the report folder and the first chunk that sets `UNBLIND` both read the variable, so setting it once switches both. Remove the line from `~/.Renviron` afterwards.
3. The text notebook does not need to run again, because it never reads the labels.

The real outputs then go to `tables/` and `study5_long_with_text.csv` to this folder. Study 5's blind runs wrote their outputs to a scratch folder outside this one, as `CHANGELOG.md` records, so this folder has no `blind_run/` and no `tables/blind_run/`.

The real run was made on 8 October 2026, after the registration was filed and after Study 3's real run. `Study5_01_Quant.Rmd` read its editing-time bound from Study 3's contrast file, whose creativity row says `blind_run` FALSE and `usable` TRUE, and `Study5_03_Integration.Rmd` followed. The notebook was not run again.
