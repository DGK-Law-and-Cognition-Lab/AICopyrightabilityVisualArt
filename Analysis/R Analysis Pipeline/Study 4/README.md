# Study 4 analysis pipeline

Study 4 asks whether what people are told about a first artwork, the source, carries over to how they judge a second work Alex makes from it. Two things about the source vary: its label, which says Alex made it with graphic design and sketching tools (Human) or by prompting an AI system (AI), and its source time, the time Alex is said to have spent on it (less than 1 hour, 10 hours or 100 hours). One hundred and seventeen participants each rated 18 second works on transformativeness, essence change and creativity, and wrote a justification after every rating.

The specification is the registration, `Docs/Preregistration/AsPredicted/Study4_AsPredicted.md`. It keeps the nine questions of the AsPredicted form, and it was registered on the Open Science Framework (OSF) on 8 October 2026, as part of an Open-Ended Registration in project https://osf.io/u3d69. The code implements what the registration names and nothing else.

Everything needed to run the analysis is in this folder, apart from three things it reads from elsewhere in the project: the two Qualtrics exports in `Data/Study 4/`, the shared helpers in `../shared/` (R in `shared/R/`, Python in `shared/python/`), and two things from Study 1 (its deposited rules, which the text notebook compares with its own, and the word norms in `Study 1/nlp/norms/`).

## The files

- `Study4_01_Quant.Rmd` builds the data from the two Qualtrics exports with the shared R helpers, applies the registered exclusions and checks every count the registration states, writes the long data with the justifications, fits the registered rating models, runs the fifteen confirmatory tests with Holm's correction, checks each verdict with a cumulative-link model, and runs the secondary analyses.
- `Study4_02_Text.ipynb` measures the 6,318 justifications with Study 1's eight word lists, unchanged, without ever reading the label, the source time or the rating.
- `Study4_03_Integration.Rmd` joins the text measures to the ratings and the label, runs the two registered text checks on creativity, refits the registered model without the Human-arm participants who write that a machine made the work, and runs the three exploratory text descriptions.
- `Final_-_AI_Copyright_-_Study_4.qsf` is the survey file exported from Qualtrics; `Study4_01_Quant.Rmd` reads each rating item's answer options from it.

An `.Rmd` file is R Markdown: R code and text that is knitted, that is, run from top to bottom into an HTML report. An `.ipynb` file is a Jupyter notebook of Python cells run in order.

## Run order

1. `Study4_01_Quant.Rmd`.
2. `Study4_02_Text.ipynb`, after step 1, since it reads the long data that step 1 writes.
3. `Study4_03_Integration.Rmd`, after steps 1 and 2, and in the same mode as step 1.

Knit the two `.Rmd` files from the R console, with this folder as the working directory. A blind run (see "The blind switch" below) is

```r
rmarkdown::render("Study4_01_Quant.Rmd", output_dir = "blind_run")
rmarkdown::render("Study4_03_Integration.Rmd", output_dir = "blind_run")
```

or open each file in RStudio and press the Knit button, which does the same: the `knit:` line at the top of each file sends a blind run's HTML report to `blind_run/`. A blind run started with `rmarkdown::render()` and no `output_dir = "blind_run"` stops before it writes anything. The commands for an unblinded run are under "How to unblind".

Run the notebook from this folder with the Python 3.12 kernel:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python312 Study4_02_Text.ipynb
```

The random steps of the notebook, all in the topic model and its agreement check, start from 20260903, the seed the registration names for the text code; a seed is the number that starts a random-number generator. The R files use the seed it names for R, 20260421. The seed alone does not make a rerun give the same numbers. The agreement check groups the sentence embeddings with k-means, a method that splits the responses into a set number of groups of similar embeddings, and the shared module runs that step on one processor thread (one strand of computation), which `tables/study4_text_environment.csv` records. On several threads, k-means adds up its numbers in pieces, one per thread, and combines the pieces in the order the threads finish, which changes from run to run; since rounding depends on that order, its groups can differ between runs. The seed and the single thread together make a rerun give the same numbers. The agreement index for essence change in `tables/study4_text_topics_embedding_agreement.csv` (the adjusted Rand index, where 0 is the agreement expected by chance and 1 is perfect agreement) is 0.1125.

On a Mac with twelve processor cores, `Study4_01_Quant.Rmd` took under half a minute and the notebook about three minutes. `Study4_03_Integration.Rmd` took about five minutes, because the first registered text check reruns its ridge regressions 400 times on the 2,106 creativity justifications and the mixed model of each topic is refitted 200 times; the permutations run on up to eight processor cores.

## What each file writes

In an unblinded run the tables go to `tables/` and `study4_long_with_text.csv` to this folder. A blind run writes each into a `blind_run/` subfolder of the folder its real counterpart goes to: the tables into `tables/blind_run/`, and the long data and the HTML reports into `blind_run/`. The text notebook is blind by construction and always writes to `nlp/` and `tables/`.

`Study4_01_Quant.Rmd`:

- `study4_long_with_text.csv`: one row per participant, second work and measure (6,318 rows), with the label, the source time, the modification level, the rating, the justification and `label_mode`, which says whether the labels are real or shuffled.
- `study4_exclusion_flow.csv`, `study4_validity_check.csv` and `study4_sample_checks.csv`: the records left after each exclusion step beside the registered counts, the two records the validity rule removes and why, and the registered sample counts beside the observed ones.
- `study4_item_scales.csv` and `study4_cell_counts.csv`: each rating item's answer options and stem, and the number of participants, responses and analysed ratings in each cell.
- `study4_lmm_anova.csv`, `study4_confirmatory_family.csv` and `study4_hypotheses.csv`: the F test of every term of each registered model, the fifteen confirmatory tests with their Holm-corrected p-values, and the registered reading of H1, H2 and H3 on each measure, with H1 and H2 also read over all three measures.
- `study4_emmeans_cells.csv` and `study4_emmeans_marginal.csv`: the estimated marginal means, the model's predicted means, of every cell and of each level of each factor.
- `study4_clmm_check.csv`: each verdict of the twelve difference tests checked with a cumulative-link model.
- `study4_secondary_label_by_modification.csv`, `study4_secondary_label_by_source_time.csv` and `study4_secondary_time_equivalence.csv`: the three secondary analyses of registration question 8 that need only the ratings.
- `study4_fit_status.csv`, `study4_quant_run_inputs.csv`, `study4_quant_sessionInfo.txt`, `study4_quant_package_versions.csv` and, written last, `study4_quant_run_manifest.csv`.

`Study4_02_Text.ipynb`:

- `nlp/study4_text_measures.csv`, `study4_text_wordcounts.csv`, `study4_text_vocabulary.csv`, `study4_text_tokens.csv`, `study4_text_affect.csv` and `study4_text_topics.csv`: the measures of each response, the word tables of the two registered checks, the tone and concreteness scores, and each response's weight on each topic.
- `tables/study4_text_rules.txt`, `study4_text_rules.sha256` and `study4_text_rules_grounding.txt`: the rules in full, their checksum and their grounding notes.
- `tables/study4_text_topics_top_words.csv`, `study4_text_topics_stability.csv` and `study4_text_topics_embedding_agreement.csv`: the topic model's heaviest words, its stability rule and its agreement with the sentence-embedding grouping.
- `tables/study4_text_environment.csv` and, written last, `tables/study4_text_run_manifest.csv`.

`Study4_03_Integration.Rmd`:

- `study4_text_join_check.csv` and `study4_text_wordcount_check.csv`: the join of the measures to the ratings, and the consistency of the word tables.
- `study4_text_recoverability.csv`, `study4_text_selfsimilarity_by_arm.csv` and `study4_text_selfsimilarity_per_person.csv`: the two registered checks.
- `study4_text_machine_made_count.csv` and `study4_secondary_refit_machine_made.csv`: the Human-arm participants who write that a machine made the work, and the registered tests refitted without them.
- `study4_text_affect_by_arm.csv`, `study4_text_topics_by_arm.csv` and `study4_text_prediction_weights.csv`: the three exploratory descriptions.
- `study4_text_fit_log.csv`, `study4_integration_run_inputs.csv`, `study4_integration_sessionInfo.txt`, `study4_integration_package_versions.csv` and, written last, `study4_integration_run_manifest.csv`.

Each run manifest lists the outputs of its run with their SHA-256 checksums, 64-character fingerprints of the files' exact bytes. Each file deletes its earlier manifest when it starts, so a manifest on disk means the run reached its end. `Study4_03_Integration.Rmd` refuses to run unless the long data, the confirmatory table and every text table match the checksums their producing runs recorded.

## How the code reads the registration

Where the registration leaves a choice of method open, the code takes these readings.

- The validity rule of question 6. A record is a valid completion when its six image slots name six different sources, the sources it rated are exactly those six, and two of the six slots state each source time. A blank arithmetic answer passes, as question 6 says; none of the 119 records reaching that step is blank.
- H1 holds on a measure when Slight minus None and Dramatic minus Slight are both positive and both have a Holm-corrected p-value below .05, each from a two-sided t test.
- H2 holds on a measure when the larger one-sided p-value of the equivalence test, after the Holm correction over the fifteen tests, is below .05. The table also says whether the uncorrected 90 percent interval lies inside plus or minus 0.224.
- Question 2 states H1 and H2 for every measure, so each also has one reading over the three measures: it holds when it holds on all three and fails when it fails on any one.
- The cumulative-link check refits each registered model with the answers treated as ordered categories and repeats the twelve difference tests as Wald tests (an estimate weighed against its standard error). The three equivalence tests are not repeated, because their bound is in rating points and the ordered-category scale has none. The twelve p-values are corrected by Holm as members of the family of fifteen.
- Of the secondary analyses, the label effect at each modification level and the 100 hours against less than 1 hour contrast are each tested for equivalence with the same bound of plus or minus 0.224. "Whether time changes it" is the label by source time F test, with the label effect at each source time beside it. No secondary p-value is corrected.
- The secondary refit leaves out every Human-arm participant with at least one justification, on any measure, whose machine-made reading is "asserted", and repeats the fifteen registered tests with the same Holm correction.
- The overlap check compares each participant with "others writing about the same pair", the source and the second work made from it. The stimulus of both text checks is therefore the second work, named by `work_id`, such as `3NonFigure_Slight`. The text notebook reads that name, which carries the modification level, as the key of every response; it reads no label, source time or rating.

## The environment

R 4.5.2 with readr 2.2.0, dplyr 1.2.1, tidyr 1.3.2, tibble 3.3.1, jsonlite 2.0.0, Matrix 1.7-5, lme4 2.0-1, lmerTest 3.2-1, emmeans 2.0.3, ordinal 2025.12-29, glmnet 5.0, rmarkdown 2.31 and knitr 1.51, with pandoc for knitting. Each knit records its versions in its `sessionInfo` and `package_versions` files.

Python 3.12 through the Jupyter kernel named `python312`, with pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.5.2, SciPy 1.13.0, sentence-transformers 3.3.1 and PyTorch 2.5.1, and the files of the all-mpnet-base-v2 sentence-embedding model already in the local Hugging Face cache, the folder where these libraries keep downloaded models. The notebook never downloads the model. Each run records its versions in `tables/study4_text_environment.csv`.

Paths start from each file's own folder. These environment variables (named settings the shell passes to R or Python when it starts) name other folders:

| Variable | What it names |
|---|---|
| `STUDY4_DIR` | the Study 4 folder |
| `STUDY4_PROJECT_ROOT` | the project root, the folder that holds `Data` and `Analysis` |
| `STUDY_SHARED_R`, `STUDY_SHARED_PYTHON` | the shared R and Python helpers |
| `STUDY1_DIR` | the Study 1 folder |

## The blind switch

Each R file begins with

```r
UNBLIND <- as.logical(Sys.getenv("UNBLIND_STUDY4", "FALSE"))
```

While `UNBLIND` is FALSE, `Study4_01_Quant.Rmd` shuffles three labels right after the data are built and before any summary or model, each with seed 20260421:

- the Human and AI label across participants, so each arm keeps its 62 or 55 participants;
- the source times across each participant's six sources, so every participant keeps two sources at each time;
- the modification levels across the three second works made from each source, so every source keeps one work at each level.

The column `work_id` still names the second work each participant saw and wrote about, because it keys the text tables; the models read the shuffled `modification` column. `Study4_03_Integration.Rmd` reads the blind long data and also shuffles the ratings within each question before it relates any word to a rating, so the rating-from-words check and the word weights are not real results either. Every output goes to a `blind_run/` folder, and each knitted report opens with a sentence saying that the labels are shuffled and nothing in it is a result. A blind run shows that the code runs, that the fits converge and that the tables have the right shape. Its numbers describe no real condition. The exclusion flow, the sample counts and the item scales do not depend on the labels and are the same in both modes.

## How to unblind

The registration is filed, so the switch may be set. Set it to TRUE and knit in order, `Study4_01_Quant.Rmd` and then `Study4_03_Integration.Rmd`. From the R console, with this folder as the working directory:

```r
Sys.setenv(UNBLIND_STUDY4 = "TRUE")
rmarkdown::render("Study4_01_Quant.Rmd")
rmarkdown::render("Study4_03_Integration.Rmd")
```

To use RStudio's Knit button instead, add the line `UNBLIND_STUDY4=TRUE` to the file `~/.Renviron` and restart R. Do not edit the files themselves: the `knit:` line that chooses the report folder and the first chunk that sets `UNBLIND` both read the variable, so setting it once switches both. Remove the line from `~/.Renviron` afterwards.

The text notebook does not need to run again, because the columns it reads are the same in the blind and the real long data. The real outputs then go to `tables/` and `study4_long_with_text.csv` to this folder. The blind outputs in `tables/blind_run/` and `blind_run/` stay where they are and can be deleted.
