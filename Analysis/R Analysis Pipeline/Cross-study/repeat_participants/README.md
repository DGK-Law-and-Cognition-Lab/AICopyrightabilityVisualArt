# Study 5: the registered sample beside the analyzed sample

**This is a sensitivity analysis.** It sets Study 5's registered analysis on its registered sample of 223 beside the same analysis on the 197 the paper reports, so a reader can see what removing 26 participants changed. Every table says so in its last column, `analysis_status`.

## The deviation it documents

Studies 1 to 4 shared one listing in the UCLA Psychology subject pool, so a student could take part in only one of them. Study 5, run in October and November 2025, had its own listing, with no restriction against the earlier one. Of the 223 participants the registration's five exclusion steps leave, 26 had completed one of Studies 1 to 4 seven to eleven months before: 7 in Study 1, 3 in Study 2, 8 in Study 3 and 8 in Study 4 (the paper's study numbers; see below). Twenty-four of them had been analyzed in that study; two had completed it but been excluded from its analysis. None of the 26 had completed two of the earlier studies.

These 26 had already done the same kind of task, seen some of the same originals and read the debriefing, the same in all five studies, which told them that anything produced with AI is insufficiently creative, even when it is used as a base for new work. Study 5 asks how people judge new work built on an AI-made image, so their first session could have changed their answers. On 1 November 2026, after every registered result was known, at a co-author's request, the authors removed them: a sixth exclusion step in `Study 5/Study5_01_Quant.Rmd`, not in the registration. Every Study 5 result in the paper uses the 197 who remain.

## How they are found

A Study 5 participant of the registered sample is removed when their subject-pool participant code, the code the survey returned to the pool to grant credit and the same for a student in every study, appears on a completed record (Finished True) in the Labels export of Study 1, 2, 3 or 4. The script finds them by that rule and stops unless they are exactly the 26 that Study 5's sixth step removed. It also counts how many had been analyzed in their earlier study, by linking each earlier study's analyzed participants to their codes as `../sample_description/` does.

Two checks on 31 October 2026 (made outside this script and not saved, because they read values that belong to single participants) support the match for the 24 analyzed earlier: in 23 of the 24 pairs, the gender answer was the same in both sessions, and in all 24 the age given in Study 5 was the same as or one year more than the age given 7 to 11 months earlier. Among random pairs of different people drawn from the same two studies, the rates were 67% and 52%.

## What it does

1. Finds the 26 and writes their number by earlier study, and how many had been analyzed there.
2. Refits Study 5's registered analysis (`Study 5/Study5_01_Quant.Rmd`, sections 6 to 10) on the registered sample of 223, from `Study 5/study5_long_registered_sample.csv`: the three linear mixed models, `rating ~ source * editing_time * modification + image_kind + (1 | id) + (1 | image)` with sum-to-zero contrasts, REML and the bobyqa optimizer; the six confirmatory F tests with Holm's correction; the equivalence tests of editing time (bound ±0.219, Study 3's registered contrast) and of the label at each level (bound ±0.224); and the ordinal check of each Holm verdict. It stops unless these reproduce the tables of the registered run of 13 October 2026, kept unchanged in `registered_run/`.
3. Refits the same analysis on the 197, from `Study 5/study5_long_with_text.csv`, and stops unless it reproduces Study 5's tables and the label penalty at each editing time and level in `../tables/crossstudy_time_check.csv`.
4. Writes every result of both samples side by side.

## What changed

Of 24 verdicts compared, four differ. On the 223, the source-by-editing-time test on creativity survived Holm's correction (Holm p = .048), and so did its ordinal check; on the 197 neither does (Holm p = .111). The transformativeness penalty at Dramatic, significant on the 223, is inconclusive on the 197; the creativity penalty at Dramatic, inconclusive on the 223, is shown to be small on the 197. Every other verdict is the same in both samples.

## What it writes

In `tables/`:

- `repeat_participants_overlap.csv`: the number of Study 5 participants who had completed each earlier study, how many of them had been analyzed there, and the totals.
- `study5_fit_status_both.csv`: each fit's sample size, convergence and singularity.
- `study5_confirmatory_both.csv`: the six confirmatory tests, F, raw and Holm p-values.
- `study5_equivalence_editing_time_both.csv` and `study5_equivalence_source_both.csv`: the registered equivalence tests and their verdicts.
- `study5_penalty_by_editing_time_both.csv`: the label penalty at each editing time and level (exploratory in the paper).
- `study5_clmm_holm_check_both.csv`: the ordinal check of each Holm verdict.
- `study5_verdicts_both.csv`: every verdict in the registered sample beside the verdict in the analyzed sample, and whether it changed.

`registered_run/` holds, unchanged, the tables the registered run of 13 October 2026 wrote and its run manifest, which lists each with its SHA-256 checksum, so the check of step 2 can be made in any copy of the project.

No table holds a participant code or any value that belongs to one participant.

## Study numbers

This folder, like the pipeline, names studies by their folders, which follow the order in which the studies were built. The paper numbers them in the order it presents them, which swaps two: the pipeline's Study 2 is the paper's Study 3, and its Study 3 is the paper's Study 2. Studies 1, 4 and 5 are the same in both. The prose above uses the paper's numbers; `repeat_participants_overlap.csv` gives both.

## How to run it

After the real runs of all five studies and the cross-study analysis, from this folder:

```sh
Rscript Study5_WithoutRepeatParticipants.R
```

It needs R 4.5.2 with readr, dplyr, tibble, lme4, lmerTest, emmeans and ordinal, at the versions the Study 5 run records, and the shared helpers in `shared/R/`. It takes about three minutes. In the public copy of the project the participant codes are replaced by other codes, with the same replacement in every study, so the script finds the same 26 people there.
