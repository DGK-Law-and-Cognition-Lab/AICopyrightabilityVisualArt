# Shared helpers changelog

The edit history of the files in `shared/R/` and `shared/python/`. The source files carry none themselves.

## 2026-10-15

- `shared/python/study_text.py`: the k-means step of the embedding agreement check, which groups the responses' sentence embeddings, now runs on one processor thread (`KMEANS_OPENMP_THREADS = 1`, applied with `threadpool_limits()` from the threadpoolctl package, which scikit-learn installs). On several threads, scikit-learn's k-means adds its partial sums in the order the threads finish, which changes from run to run, and rounding depends on that order, so the k-means groups, and with them the agreement index, could differ between reruns. With one thread, every rerun gives the same numbers. A first attempt on 14 October 2026 fixed the count at ten threads; it did not make reruns repeat and was reverted before any output was kept.
- `shared/python/README.md`: the entry on `set_text_seed()` says that the seed and the single thread together make a rerun give the same numbers, and now names the studies correctly: Studies 2 and 3 call `set_text_seed(20260421)`, and Studies 4 and 5 call `set_text_seed(20260903)`.
- Effect, checked by rerunning the five text notebooks on 15 October 2026 and comparing every output's SHA-256 checksum: every output is byte-identical except the run records and Study 4's essence-change agreement index, which is now 0.1125 (the 0.1449 deposited before came from a multithreaded run). Repeat tests on 14 and 15 October 2026 called the agreement function several times per study, with one thread and with twelve allowed, and every repeat gave the same values (Studies 1, 2, 4 and 5 tested). No integration or cross-study file reads the agreement tables, so none was rerun.

## 2026-10-14

- `shared/python/README.md`: the entry on `set_text_seed()` says that the k-means grouping of the agreement check also depends on the number of processor threads scikit-learn uses, which the module does not fix, so the agreement index for essence change can differ between runs, in Study 4 by up to 0.03. No code changed.

## 2026-10-08

- `shared/python/test_reproduces_study1.py` was run again on the current `study_text.py`, with `set_text_seed()` in it. Every decisive comparison passed: the eight CSV files are byte-identical to Study 1's deposited files of run 20261007T201050Z-266603a3, `text_rules.txt` and `text_rules.sha256` are exactly equal, and the rules SHA-256 is still 6aa77dbc26c9086c5349a863c1cab808d7bd3758265fc365de2fb36c46a30239. With no call to `set_text_seed()`, the module uses Study 1's seeds, so Study 1's outputs do not change.

## 2026-10-07

### shared/python

`study_text.py` holds the Study 1 text measurement as an importable module, so that Studies 2 to 5 run the eight word lists and the measurement exports unchanged.

- The module holds the eight rules with their plain and grounding fields; the negation, quantifier, clause-boundary, self-negation, familiarity, size-of-little and supposition patterns; the function-word list and the task vocabulary; the tokenizer; the matching and reading functions, including the machine-made reading; and `apply_rules` and `format_rules`. It also holds the word-count, content-word, affect and NMF topic builders, with the stability rule for choosing the number of topics and the embedding agreement check, and the atomic writers. NMF, non-negative matrix factorisation, is the topic model: it splits the word counts into a few groups of words that tend to occur together.
- Each export has one function that takes a blind frame. Every function that takes a frame of responses refuses the condition, the rating, demographics and any column outside `id`, `stimulus_id`, `dimension`, `response_text` and the `stimulus_*` columns.
- The rules text names the study and its number of responses, so these two lines, and therefore the checksum, differ by study. Every other line is the same in every study.
- `test_reproduces_study1.py` rebuilds the Study 1 blind slice from `study1_long_with_text.csv` and compares every output with the deposited files of run 20261007T201050Z-266603a3. All eight CSV files are byte-identical, `text_rules.txt` and `text_rules.sha256` are exactly equal, and the rules SHA-256 is 6aa77dbc26c9086c5349a863c1cab808d7bd3758265fc365de2fb36c46a30239. `text_rules_grounding.txt` and `text_topics_embedding_agreement.csv` are also identical; the test reports them but does not decide on them.
- Later the same day, `study_text.py` gained `set_text_seed()` and `text_seeds()`. A study whose registration names its own seed for the text code calls `set_text_seed()` before the first fit. The ten refits of the stability rule then use that seed and the nine numbers after it, and the final topic fit and the k-means grouping of the agreement check use the seed itself. `text_seeds()` returns the seeds in force, which the Study 3 and Study 5 notebooks record in their environment tables. The defaults are Study 1's seeds.
- `README.md` describes the module, the test and the environment.

### shared/R

The R helpers for Studies 2 to 5.

- `qualtrics_import.R` reads the Values and Labels exports and the survey file, leaves out questions in the survey's Trash block, and applies the exclusion steps in order (`exclusion_flow`). It scores each rating by its position in the item's `ChoiceOrder`, the order in which the survey showed the answer options (`read_item_scales`, `score_by_position`). An answer whose label is not among the item's choices, or whose choice code has no exported label, becomes NA and is logged. It reshapes both item families, originals and derivatives, to one row per participant and item, with the justification found under the `Resp`, `Re` or `R` suffix. On the Study 5 exports it reproduces every row of `study5_long.csv` exactly.
- `text_checks.R` holds the two registered text checks of `Study1_03_Integration.Rmd` section 8 as functions (`text_recoverability`, `text_self_overlap`, `recoverability_readings`), with the dimensions, the stimulus key and the arm as arguments. On Study 1's deposited files it reproduces `study1_text_recoverability.csv` and `study1_text_selfsimilarity_by_arm.csv` to within 1e-10.
- `fit_status.R` holds the fit-status rule of `Study1_01_Quant.Rmd` for lme4 models (`lmer_fit_status`, `fit_usable`, `fit_note`, `na_unless_usable`, `fit_with_status`), the run record and manifest (`start_run_record`, `run_clear_outputs`, `write_run_inputs`, `write_run_manifest`), `find_project_root` and `relative_path`, and the blind helpers (`blind_mode`, `blind_shuffle`, `blind_paths`). It was tested on fits that converge, fits that are singular, fits whose optimizer stopped short and fits that fail. `blind_shuffle` was tested on a small made-up data set: the labels move as a unit, every cell keeps its size, the same seed gives the same shuffle, and the random-number state is unchanged afterwards.
- `README.md` gives the order in which a study notebook calls the helpers and how each was checked.
