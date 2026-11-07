# Hours check: the effect of stated hours on originals, with a slope for each person

**This analysis is exploratory.** It was specified on 5 November 2026, after every registered result was known, when a co-author asked whether the small rise in creativity ratings with stated hours in the paper's Study 2 is reliable. It changes no registered verdict.

The paper's Study 2 is the pipeline's `Study 3/`. There, each participant saw three originals at each stated time (under 1 hour, 10 hours, 100 hours). The registered model gives each participant and each image their own average rating. It assumes, though, that the hours move every participant's ratings by the same amount. Because the hours varied within participants, people who respond to the hours differently could make that model too sure of the hours effect.

`HoursCheck_Study2.R` fits the registered model and a refit that adds a random slope of stated time for each participant and of the label for each image. That refit is the random-slope model Study 3's registration names for its equivalence check. For creativity and effort, under each model, the script writes three contrasts with their 95 percent intervals:

- 100 hours minus under 1 hour, averaged over the two labels with equal weights, as registered;
- the same within each label;
- 10 hours minus under 1 hour.

## Checks

The run stops unless:

- `Study 3/study3_long_with_text.csv` has the SHA-256 checksum that Study 3's run recorded in `Study 3/tables/study3_quant_run_manifest.csv`;
- its refit of the registered model reproduces Study 3's registered contrast (`Study 3/tables/study3_time_contrast.csv`) to 1e-8.

The column `singular` records whether a fit set one of its variances at zero, which means the data could not estimate every variance the model allows for. On the run of 5 November 2026 the random-slope refit was singular for both ratings. Its fixed effects, which give the contrasts, are still estimated.

## How to run it

From this folder:

```sh
Rscript HoursCheck_Study2.R
```

It needs R 4.5 with readr, dplyr, tibble, lme4, lmerTest, emmeans and digest, and takes a few seconds.

## What it writes

- `tables/hours_check_study2.csv`: one row per rating, model, label and contrast, with the estimate, standard error, Kenward-Roger degrees of freedom, 95 percent interval, t, p, the singular flag and any fitting messages.
- `tables/hours_check_sessionInfo.txt`: the R session.

No table holds a participant code.
