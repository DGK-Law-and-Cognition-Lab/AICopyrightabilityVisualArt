# Shared R helpers for Studies 2 to 5

This folder holds the R code that the analysis notebooks of Studies 2 to 5 have in common. A notebook here means an R Markdown file (`.Rmd`), a file that mixes code with text and is knitted, that is, run from top to bottom to produce a report. Each helper takes one step that Study 1 performs inside its own notebooks and makes it a function, so that every later study performs that step the same way.

| File | What it does |
|---|---|
| `qualtrics_import.R` | Reads a study's two exports from Qualtrics, the survey platform, and its survey file, applies the exclusion steps in order, scores each rating by its position on the answer scale, and reshapes the ratings into one row per participant and item. |
| `text_checks.R` | Runs the two text checks the Study 1 registration fixes for every study: how closely the words track the rating and the arm, and whether one arm reuses its own words more than the other. |
| `fit_status.R` | Reads whether a mixed model (a regression with an estimated adjustment for each participant and each image) converged, keeps a record of each run's inputs and outputs, finds the project folder, and supplies the blind switch. |

None of these files reads or writes anything when it is sourced (loaded into R with `source()`). They only define functions, and no analysis runs until a study's notebook calls them. The Study 5 data build is a separate script, `Study 5/study5_build.py`, which writes `study5_long.csv`; the helpers here reproduce that table exactly, so a Study 5 notebook can either read the file or rebuild it with step 1 below.

## How a study notebook uses them

A study notebook sits in its own folder, `Study N/`, beside this `shared/` folder. Knitting sets the working directory to the notebook's folder, so the helpers are found one level up. An environment variable (a named setting the operating system passes to every program it starts), `STUDY_SHARED_R`, can name the folder instead, for a copy of the project kept somewhere else.

```r
SHARED_R <- Sys.getenv("STUDY_SHARED_R", file.path("..", "shared", "R"))
source(file.path(SHARED_R, "fit_status.R"))
source(file.path(SHARED_R, "qualtrics_import.R"))
source(file.path(SHARED_R, "text_checks.R"))

# The project root is the folder that holds Data and Analysis. It is found by
# walking up from the notebook's folder, or read from STUDY5_PROJECT_ROOT.
PROJECT_ROOT <- find_project_root(env_var = "STUDY5_PROJECT_ROOT")
STUDY_DIR    <- file.path(PROJECT_ROOT, "Analysis", "R Analysis Pipeline", "Study 5")
```

No notebook should write the project's absolute path into its code or its output. `find_project_root()` and `relative_path()` exist so that it never has to: the first finds the folder, and the second turns any path into one relative to a folder for printing.

## The order of the steps

### 1. Build the ratings

```r
paths  <- study_export_paths(PROJECT_ROOT, 5)
ex     <- read_qualtrics_pair(paths$values, paths$labels)
flow   <- exclusion_flow(ex$values, ex$labels, steps)   # steps: the study's registered rules
scales <- read_item_scales(paths$qsf, ITEM_FAMILIES$derivative$pattern)
built  <- reshape_ratings_long(flow$values, flow$labels, scales, "derivative",
                               carry_values = c("Type", "ArtistHr_Derivative"))
long   <- dplyr::rename(built$long, deriv_effort = ArtistHr_Derivative)
```

Qualtrics exports each study twice. The Values export stores each answer as a raw choice code, the internal number Qualtrics gave the answer option, and the Labels export stores the text the participant saw. The raw codes are not scale positions and differ from item to item, so a rating is scored from its label: `score_by_position()` looks the label up in the item's answer options, taken from the survey file (the `.qsf`) in the order they were shown, and its place in that list, 1 to k, is the score. An answer whose label is not among the item's options becomes NA and is listed in `built$unscored`, which the notebook should print.

`steps` is a named list of functions, one per registered exclusion rule, each returning TRUE for the records to keep. The exclusion rules differ from study to study, so they are written in each study's notebook and not here. `flow$flow` is the participant flow table.

Two item families exist. The original family (`3NonFigureEff`: image, image kind, dimension) is used in Studies 1 and 3, and the derivative family (`1FigureMinTrans`: image, image kind, modification level, dimension) in Studies 2, 4 and 5.

### 2. Decide whether the run is blind

```r
UNBLIND <- as.logical(Sys.getenv("UNBLIND_STUDY5", "FALSE"))
if (!UNBLIND) long <- blind_shuffle(long, "id", c("Type", "deriv_effort"), seed = 20260421L)
```

Studies 3 and 5 read their own switch, `UNBLIND_STUDY3` or `UNBLIND_STUDY5`, at the top of each R Markdown file and send a blind run's outputs to `blind_run/` and `tables/blind_run/`; each study's README gives the commands. Only `blind_shuffle()` is shared. `blind_mode()` and `blind_paths()` in `fit_status.R` are an older form of the same switch that no study uses.

A blind run is the whole analysis run on condition labels shuffled across participants. Every model, table and figure is produced and can be checked, but no number describes the real conditions, because the link between each person and their condition has been cut. `blind_shuffle()` moves the listed between-participant labels together, so each participant receives another participant's whole set of labels and every cell keeps its size. `blind_paths()` sends a blind run's outputs to `Study N/blind_run/`, including the copies that would otherwise go to the paper folder.

A run is blind unless the study's environment variable is set to `TRUE`. Forgetting to set it therefore produces a blind run, never an unblinded one. The shuffle belongs immediately after the ratings are built and before any summary by condition. The built data files themselves carry the real labels, so nothing may summarise them by condition outside a notebook that has passed through this step.

### 3. Record the run

```r
run <- start_run_record(c(values_export = paths$values, labels_export = paths$labels),
                        file.path(OUT$tables, "study5_run_manifest.csv"), STUDY_DIR,
                        other_dirs = c("Docs/Writing/Final Paper" = PATH_PAPER))
run_clear_outputs(run, file.path(OUT$tables, "some_table.csv"))   # at the top of each chunk that writes
# ... the chunk writes its files ...
write_run_manifest(run)                                           # in the last chunk
```

The run record ties every output to one run. It stores a checksum of each input (a fingerprint of the file's exact bytes), deletes each output's previous copy before the chunk that writes it runs, and ends with a manifest saying which outputs this run wrote. A manifest on disk means the run reached its last chunk.

### 4. Fit the models

```r
res <- fit_with_status(lmerTest::lmer(rating ~ Type * deriv_effort * modification +
                                        stimulus_type + (1 | id) + (1 | stimulus_id),
                                      data = d))
res$status          # fit_error, converged, singular, lme4_messages
if (!res$status$fit_error) {
  coefs <- broom.mixed::tidy(res$fit, effects = "fixed", conf.int = TRUE)
  coefs$p.value <- na_unless_usable(coefs$p.value, res$status)
  coefs$note    <- fit_note(res$status)
}
```

A fit that stopped with an error or did not converge carries no p-value, interval or verdict: `na_unless_usable()` sets them to NA, and `fit_note()` gives the reason for the note column. A singular fit, one with a variance estimated at zero or a correlation at plus or minus one, keeps its numbers when it converged, and its `singular` column says so. This is the rule of Study 1's quantitative notebook.

### 5. Run the text checks

```r
wordcounts <- read_text_wordcounts(file.path(STUDY_DIR, "nlp", "study5_text_wordcounts.csv"))
vocabulary <- read_text_vocabulary(file.path(STUDY_DIR, "nlp", "study5_text_vocabulary.csv"))
tokens     <- read_text_tokens(file.path(STUDY_DIR, "nlp", "study5_text_tokens.csv"))
check_text_wordcounts(ratings, wordcounts, vocabulary)

recover <- text_recoverability(ratings, wordcounts, dims = "creativity")
recoverability_readings(recover)
overlap <- text_self_overlap(ratings, tokens, dims = "creativity")
overlap$by_arm
```

The text tables are written by the text measurement step (`shared/python/study_text.py`, run from each study's text notebook), which never sees the condition or the rating. The checks join the arm and the rating to those tables, and the read functions stop if a table carries the condition, the rating or the text. `ratings` holds one row per response with `id`, the stimulus columns, `dimension`, `rating` and the arm column.

Three arguments carry what changes from study to study.

- `dims`: the rating dimensions the check is registered for. Study 3 registers both ratings (`c("creativity", "effort")`), so the overlap check corrects the two together by the Holm procedure, which compares the smallest p-value with .05 divided by the number of tests, the next with .05 divided by one fewer, and stops at the first that fails. Studies 2, 4 and 5 register creativity alone.
- `stim_cols`: the columns that together name what one explanation is about, in both the ratings and the text tables. In Studies 1 and 3 that is the image, `stimulus_id`. In Study 5 it is the second work, the source image at one modification level. When the text tables fold the modification level into `stimulus_id`, build the same combined identifier in `ratings` and keep `stim_cols = "stimulus_id"`; when they carry the two as separate columns, pass both names.
- `arm_col` and `arm_levels`: the between-participant label the checks compare, `Type` with levels `Human` and `AI` by default. The second level is the positive class of every AUC (the probability that a randomly chosen response from that arm scores above one from the other) and the arm predicted to reuse its words more.

The recoverability check fits ridge regressions (regressions that shrink every word's weight toward zero) on ten folds grouped by participant, with 200 permutations (reruns of the whole check on shuffled outcomes) per outcome and dimension. On eight cores, Study 1's two dimensions of 1,110 responses each take about eight minutes. Study 5's creativity dimension holds 4,014 responses and takes longer.

Every setting is that of Study 1: seed 20260421, ten folds, a vocabulary floor of five responses applied inside each training fold, 200 permutations, 2,000 bootstrap replicates (resamples of participants with replacement) and the same penalty grid (the candidate strengths of the shrinkage). The defaults are those values, and a study should change none of them.

## How the helpers were checked

- On the Study 5 exports, the exclusion steps of `study5_build.py` written as `exclusion_flow()` steps give the same flow table, `read_item_scales()` gives the same 90 items with the same scale lengths, anchors and question texts as `tables/study5_item_scales.csv`, and `reshape_ratings_long()` reproduces every one of the 12,042 rows of `study5_long.csv` exactly: the rating, the number of scale points, the label, the raw choice code, the justification and the condition columns, in the same row order.
- On the Study 3 exports, the registered exclusions leave 85 participants with 1,530 justifications and 1,525 scored ratings. The two `1FigureEff` answers with choice code 5, which the final survey does not offer, are scored NA and listed in the unscored log.
- On Study 1's deposited files (`study1_long_with_text.csv` and the word, vocabulary and token tables in `nlp/`), `text_recoverability()` and `text_self_overlap()` reproduce `tables/study1_text_recoverability.csv` and `tables/study1_text_selfsimilarity_by_arm.csv`, every column and row, with no numeric difference above 1e-10.
- `fit_status.R` was tested on fits that converge, fits that are singular, fits whose optimizer stopped short and fits that fail, and its blind switch on a small made-up data set: the labels move as a unit, every cell keeps its size, the same seed gives the same shuffle, and the random-number state is unchanged afterwards.

These checks ran under R 4.5.2 with readr 2.2.0, dplyr 1.2.1, tibble 3.3.1, jsonlite 2.0.0, Matrix 1.7-5, glmnet 5.0, lme4 2.0-1 and lmerTest 3.2-1. The ridge fits come from glmnet, so another glmnet version can move the recoverability numbers slightly.
