# What each registered test could detect

**Descriptive.** Specified on 1 November 2026, after every registered result was known. It tests no hypothesis and changes no verdict; every row of its table says so in `analysis_status`.

## Why

None of the five studies set its sample size by a power analysis. Each was registered after its data were collected, and its size was set by the subject pool's quotas: 60 per condition in Study 1, 50 in Study 2, 125 in Study 3, 62 in Study 4 and 40 per group in Study 5 (the paper's numbering). So the question "was the study powered?" has no planned target to answer it against. The question this folder answers instead is the one a reader needs: for each registered test, how large an effect could it detect, and, for each test that can show an effect to be small, how likely was it to show that an effect that is truly absent is small?

## What it computes

For each registered estimate, from the standard error (SE) and degrees of freedom (df) in the table its study's run wrote:

- `mde80`, the smallest true effect that a two-sided test at alpha .05 would find significant in 80 percent of studies of this size and precision, (t[.975, df] + t[.80, df]) x SE, in rating points;
- `eq_power`, for an equivalence test, the chance that the 90 percent interval of an effect that is truly zero would fall inside the bound, 2 x Phi(bound / SE - t[.95, df]) - 1; it is 0 when the interval is wider than the bound, so that the test could never pass.

Both depend only on the precision of the estimate, never on the estimate itself. Neither is the "observed power" of a test, which only restates its p-value. A test with an `mde80` above an effect that matters, or an `eq_power` well below 1, could miss that effect or fail to show a small one, and its non-significant or inconclusive verdict says little.

Study 5's label-by-editing-time interaction asks whether the label's penalty differs between the groups told different editing times. The script refits Study 5's registered creativity model on its 197 analyzed participants to get the penalty at each editing time, averaged over the edit levels, and the standard error of the difference between each pair of editing times; `mde80` of that difference is the smallest difference between two times' penalties the design could detect.

## The check

Study 1's robustness file computed power by simulating data from its fitted model. The script stops unless its closed forms agree with those simulations: the chance of showing Study 1's H3 interaction small equals the analytic value Study 1 wrote beside its simulation (0.357 and 0.344) and lies within 0.03 of the simulated value, and the smallest detectable label penalty lies within 0.05 points of where the simulated power curve crosses 80 percent (0.363 against 0.365 on creativity, 0.428 against 0.456 on effort; each simulated power rests on 200 simulated data sets).

## What it found

- Originals. Study 1 could detect a label penalty of 0.36 points on creativity and 0.43 on effort; the penalties it found, 0.45 and 0.92, were larger. Its H3 test, whether the penalty is the same with or without a human figure, had a 36 and 34 percent chance of showing a truly equal penalty to be equal, so an inconclusive verdict was the likely outcome. In Study 2, the penalty at 100 hours was too imprecise ever to be shown small: its 90 percent interval was wider than the bound of 0.224 points, so the registered decision at 100 hours rests on the penalty being above zero.
- Second works. Study 3 could detect a penalty of 0.14 to 0.16 points and had a 98 to 100 percent chance of showing an absent penalty small. Study 5 could detect 0.19 to 0.20 points at each edit level, with an 86 to 90 percent chance. Study 4 was the least precise: 0.23 to 0.29 points at each level, with a 40 to 70 percent chance. Pooled over the three studies, a penalty of 0.12 points was detectable at each level.
- Hours on second works. Study 4 could detect an effect of the hours stated for the original of 0.11 points; Study 5, an effect of the editing hours of 0.20 to 0.22 points, with a 76 to 84 percent chance of showing an absent effect small.
- Study 5's interaction. The penalty at one editing time rests on 30 to 36 people per label, and two editing times' creativity penalties had to differ by about 0.43 points to be detected 80 percent of the time.

## Files

| File | What it is |
|---|---|
| `Sensitivity.R` | The script. |
| `tables/sensitivity_registered_tests.csv` | One row per registered estimate: the study (pipeline and paper numbers), the part, the test, its role, the measure, the level, the estimate, its SE and df, `mde80`, the bound and `eq_power`. |
| `tables/sensitivity_checks.csv` | The checks against Study 1's simulations. |
| `tables/sensitivity_run_inputs.csv`, `tables/sensitivity_run_manifest.csv` | The run record: every input and output with its SHA-256 checksum. |

## How to run it

After every study's pipeline and the cross-study analysis, from this folder:

```sh
Rscript Sensitivity.R
```

It needs R 4.5.2 with readr, dplyr, tibble, lme4, lmerTest and emmeans, and the shared helpers in `../../shared/R/`. It takes about half a minute.
