# Study 5 changelog

The edit history of the Study 5 source files. The source files themselves carry none.

## 2026-10-08

Checked every commitment of the registration against the code: each model term, test, correction, bound, decision rule, exclusion step and count, scoring rule, text check, exploratory item and seed. The changes below close the gaps found.

- `Study5_01_Quant.Rmd`: the two equivalence bounds are set once, in section 1.3, before the data are read and before any model is fitted, as the registration requires of the editing-time bound. When Study 3's contrast file gives that bound, the run record lists the file as an input. Section 9 held a second copy of the bound code, which is removed; section 9 now prints the two bounds it uses. Section 4 checks the within-participant design of registration question 4: every participant saw 6 of the 10 source images, 3 with a figure and 3 without, each at the three modification levels, which makes 18 second works.
- `Study5_02_Text.ipynb`: the random steps start from 20260903, the seed the registration names for the text code. They are the ten refits by which the stability rule chooses the number of topics, the final topic fit, and the k-means step of the agreement check, which splits the responses into as many groups of similar responses as there are topics. The notebook sets the seed through `set_text_seed()` in `shared/python/study_text.py`, and the ten refits use 20260903 to 20260912. The notebook was run again in place with the `python312` kernel. Every file in `nlp/` and every `study5_text_` file in `tables/` now comes from that run, and `tables/study5_text_environment.csv` records the seeds. The word measures, the word tables, the tone scores and the rules are byte for byte the same as before; the topic files changed, because their seeds did.
- `README.md`: the knitting commands send a blind run's HTML report to `blind_run/`. The unblinding steps give the console commands, and say that with the Knit button `"FALSE"` becomes `"TRUE"` both in the `knit:` line and in the first chunk of each file.

Checked in blind mode only, by knitting copies in a scratch folder with the outputs sent there, through the files' own knit line. `Study5_01_Quant.Rmd` reproduced the registered exclusion counts and cell sizes, rebuilt `study5_long.csv` exactly, passed the design check, and found all six trial-time fields blank. All six linear mixed models and all three cumulative-link models converged, none singular, and every registered table was written with the expected rows. `Study5_03_Integration.Rmd` matched every text file to the notebook's new run manifest and joined all 12,042 responses one to one. Both registered checks ran with status ok, all 33 mixed models of the exploratory section converged (one singular), every topic permutation null has its 200 refits, and the lasso fits (penalised regressions that keep only the words carrying the rating prediction) ran with status ok. Neither knit wrote into the Study 5 folder. No estimate from a blind run is reported anywhere.

## 2026-10-07

Added the analysis pipeline, built to the registration `Docs/Preregistration/AsPredicted/Study5_AsPredicted.md`.

- `Study5_01_Quant.Rmd`: rebuilds the long data from the exports with the shared R helpers (`read_item_scales()`, `score_by_position()` through `reshape_ratings_long()`) and checks it equals `study5_long.csv` row for row; applies the five exclusion steps of registration question 6; writes `study5_long_with_text.csv`; fits the registered linear mixed model on each rating; runs the six confirmatory F tests with Holm's correction, the estimated marginal means, the two registered equivalence tests with their decision rules, the cumulative-link check of each Holm verdict, and the second analysis on items rescaled from 0 to 1; records fit status and a run manifest.
- `Study5_02_Text.ipynb`: measures the justifications with the shared module `shared/python/study_text.py` on a slice that holds no condition and no rating, and checks that the module's rules equal Study 1's deposited `tables/text_rules.txt` and its SHA-256.
- `Study5_03_Integration.Rmd`: joins the text measures to the ratings and the source condition, runs the two registered creativity checks with `shared/R/text_checks.R`, and the four exploratory descriptions the registration names.
- `README.md` and this file.

The blind switch (`UNBLIND_STUDY5`, FALSE by default) shuffles source and editing time across participants as one unit, with seed 20260421, before any summary or model. A blind run writes its tables to `tables/blind_run/`, and its long data and Knit-button reports to `blind_run/`. The editing-time bound is read from the file `Study3_01_Quant.Rmd` writes, and only when that file says it comes from an unblinded run with a usable fit.

Checked in blind mode only, by knitting copies in a scratch folder with the outputs sent there, through the files' own knit line.

- `Study5_01_Quant.Rmd` reproduced the registered exclusion counts (259, 259, 242, 226, 225, 223) and cell sizes (Human 37, 37, 38; AI 35, 38, 38) and rebuilt `study5_long.csv` exactly. All six linear mixed models and all three cumulative-link models converged, none singular. Every registered table was written with the expected rows, and the report opens with the blind sentence. The editing-time equivalence test ran on the placeholder bound, because Study 3's contrast file does not exist yet.
- `Study5_03_Integration.Rmd` joined all 12,042 responses one to one, after checking each text file against the notebook's run manifest. Both registered checks ran with status ok. All 34 mixed models of the exploratory section converged, three of them singular, and every topic permutation null has its 200 refits.
- `Study5_02_Text.ipynb` ran in place. The rules equal Study 1's and match its checksum, the contract checks passed on all six data files, and it wrote only its listed outputs.

No estimate from a blind run is reported anywhere.

## 2026-10-08

- `study5_start.R` moved to `_retired_2026-10-08/`. It fitted models on the real condition labels with no blind switch and had never been run.
- `README.md`: one way to unblind with the Knit button, the same as Study 3: set `UNBLIND_STUDY5=TRUE` in `~/.Renviron`, with no edits to the files.

## 2026-10-08: registration readings settled

- The author confirmed the readings the code had taken where the registration left a choice open, and `Docs/Preregistration/AsPredicted/Study5_AsPredicted.md` now states them, with its Word copy rebuilt. Question 1 also now says the code was checked on condition labels shuffled at random across participants, which yields no result. No code changed.

## 2026-10-08: unblinding

- The five registrations, which keep the questions of the AsPredicted form, were registered together on the Open Science Framework (OSF) on 8 October 2026, as one Open-Ended Registration in project https://osf.io/u3d69. Study 5 was then run with the real labels after Study 3, whose registered creativity contrast fixes the editing-time bound. `Study5_01_Quant.Rmd` was knitted with `UNBLIND_STUDY5=TRUE` and read `Study 3/tables/study3_time_contrast_for_study5.csv`, whose creativity row says `blind_run` FALSE and `usable` TRUE; `Study5_03_Integration.Rmd` followed. The text notebook was not run again, because it reads no label or rating. `study5_long_with_text.csv` says `real` in `label_mode` on all 12,042 rows, both reports open with the sentence that the labels are the real ones, and each run manifest lists every output as written by its run.

## 2026-10-08: the registration recorded

- `README.md` states where the registration was filed: on OSF on 8 October 2026, with the other four, as one Open-Ended Registration in project https://osf.io/u3d69. The steps to unblind no longer begin by submitting it, and the README records the real run. The file list no longer names `study5_start.R`, which is in `_retired_2026-10-08/`. The README also says that a blind report rendered without `output_dir = "blind_run"` replaces the report of the real run, because `Study5_01_Quant.Rmd` and `Study5_03_Integration.Rmd` have no check that stops it. The unblinding entry above names the registration in the same way. No code changed.
- In blind mode `Study5_03_Integration.Rmd` shuffles the condition labels but not the ratings. The blind runs recorded above therefore related the words to the real ratings in the rating half of the first registered check, in the tone and topic models, which take the rating as a predictor, and in the lasso word weights of the rating. Their outputs were written to a scratch folder outside the Study 5 folder, and the entries above report no estimate from them.

## 2026-10-14

- `README.md`: a paragraph on the agreement index for essence change in `tables/study5_text_topics_embedding_agreement.csv`, which can differ in the fourth decimal between runs (0.1269 in the run of 8 October 2026, 0.1273 in a rerun on 13 October 2026) because of floating-point rounding: scikit-learn's k-means adds numbers up in an order that depends on the number of processor threads it uses, which the code does not fix. No code and no output changed; the deposited table keeps 0.1269.

## 2026-10-15

- `Study5_02_Text.ipynb`: the agreement check's k-means step now runs on one processor thread through the shared module (see `shared/CHANGELOG.md`); the setup text says that the seed and the single thread together make a rerun give the same numbers. The environment table records `kmeans_openmp_threads` as 1. Rerun on 15 October 2026; every output is byte-identical to before except the run records. The essence-change index stays 0.1269; the 0.1273 seen in a rerun on 13 October 2026 came from a multithreaded run and is no longer possible.
- `README.md`: the paragraph on the agreement index now describes the single thread; it replaces the paragraph of 14 October 2026.
