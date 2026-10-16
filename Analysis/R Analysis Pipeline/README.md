# Analysis pipeline

This folder holds the analysis code of the five studies. Each study has its own folder, and each study's README gives its run order and says what every file writes. Start there.

## What lives where

| Folder or file | What it holds |
|---|---|
| `R Analysis Pipeline.Rproj` | The R project file. Opening it in RStudio starts R with this folder as the working folder, the folder from which R reads and writes. |
| `Study 1/` to `Study 5/` | One folder per study: its analysis files, its `README.md`, its `CHANGELOG.md` (the edit history, which the source files do not carry) and its outputs. |
| `shared/R/` | The R functions Studies 2 to 5 share: reading the exports from Qualtrics, the survey platform; removing records by the registered exclusion steps in order; scoring each rating by its position on the answer scale; reading whether each model fit converged; keeping a record of each run's inputs and outputs; and the two registered text checks. |
| `shared/python/` | The Python code that measures the written justifications for the text notebooks of Studies 2 to 5, and a test showing that it reproduces Study 1's text outputs exactly. |
| `Cross-study/` | The exploratory analyses across studies, each specified after the registered results were known: `CrossStudy_Penalty_Curve.Rmd`, which pools Studies 2, 4 and 5 to trace the source penalty across modification levels, and three folders, `explanation_shift/`, `structural_topics/` and `image_check/`. Each has its own README. They read what the studies' real runs wrote, so they run after all five studies. |
| `Exported Studies/` | The five survey files (`.qsf`) exported from Qualtrics. |

Each folder under `shared/` has its own README. The data are not in this folder. Each study's two Qualtrics exports are in `Data/Study N/` at the top of the project, two folders up from this one: `StudyN_Values.csv`, which stores each answer as a code, and `StudyN_Labels.csv`, which stores the text the participant saw.

An R Markdown file (`.Rmd`) mixes R code with text and is knitted, that is, run from top to bottom into an HTML report. A Jupyter notebook (`.ipynb`) is a file of Python cells run in order.

## The registrations

A registration is the analysis plan, filed with a date before the analysis is run. The five registrations were registered together on the Open Science Framework (OSF), a website that keeps such plans with their dates, on 8 October 2026, as one Open-Ended Registration in project https://osf.io/u3d69. Each keeps the nine questions of the form used by AsPredicted, another registration website. The files are in `Docs/Preregistration/` at the top of the project. Each is a Markdown file (`.md`, plain text with light formatting marks), and a formatted Word copy (`.docx`) with the same wording sits beside it:

- `Docs/Preregistration/AsPredicted/Study1_AsPredicted.md` to `Study5_AsPredicted.md`, with `Study1_AsPredicted.docx` to `Study5_AsPredicted.docx` beside them;
- `Docs/Preregistration/Study1_Preregistration.md`, the full Study 1 plan, with `Study1_Preregistration.docx`.

The Markdown file is the one the code is built to.

## The five studies

| Study | State | Run order |
|---|---|---|
| 1 | Complete. Every file has been run, and its outputs are in the folder. | `Study1_01_Quant.Rmd`, `Study1_02_Text.ipynb`, `Study1_03_Integration.Rmd`, `Study1_04_Robustness.Rmd`, `Study1_Supplements.Rmd`, `Study1_Figures.Rmd` |
| 2 | Built to its registration, run blind, and run on the real labels on 8 October 2026. | `Study2_01_Quant.Rmd`, `Study2_02_Text.ipynb`, `Study2_03_Integration.Rmd` |
| 3 | Built to its registration, run blind, and run on the real labels on 8 October 2026. | `Study3_01_Quant.Rmd`, `Study3_02_Text.ipynb`, `Study3_03_Integration.Rmd` |
| 4 | Built to its registration, run blind, and run on the real labels on 8 October 2026. | `Study4_01_Quant.Rmd`, `Study4_02_Text.ipynb`, `Study4_03_Integration.Rmd` |
| 5 | Built to its registration, run blind, and run on the real labels on 8 October 2026, after Study 3. | `study5_build.py` (already run), `Study5_01_Quant.Rmd`, `Study5_02_Text.ipynb`, `Study5_03_Integration.Rmd` |

In Studies 1 to 4 the text notebook reads the long data file that the first R Markdown file writes; in Study 5 it reads `study5_long.csv`, which `study5_build.py` writes. In every study the integration file reads the outputs of both. Study 5 runs after Study 3, because its editing-time bound is read from a file that the real Study 3 run writes. Each study's README gives the commands.

A blind run is the whole analysis on shuffled condition labels. Every model, table and check is produced and can be checked for errors, but no number describes the real conditions. Until their registrations were filed, Studies 2 to 5 were run only blind. In Studies 2, 3 and 4 the blind integration file also shuffles the ratings, because some of its analyses relate the words to the rating alone, which a label shuffle cannot blind. Study 5's blind mode shuffles the labels only, so its blind runs of the integration file related the words to the real ratings, as one early blind run of Study 3's integration file did. `Study 3/CHANGELOG.md` and `Study 5/CHANGELOG.md` record both. A blind run writes its tables to `tables/blind_run/` and its long data file and reports to `blind_run/`, and each blind report opens with a sentence saying that nothing in it is a result. A real run writes its tables to `tables/` and its reports beside the `.Rmd` files, and each real report opens with a sentence saying that it uses the real labels. Nothing in a `blind_run/` folder is a result.

Studies 2 to 5 run equivalence tests, which ask whether a difference lies inside a stated bound, with the registered bound of plus or minus 0.224 rating points, half the 0.448-point creativity penalty Study 1 estimated. In Studies 2 and 4 the bound applies to the Human minus AI difference on each measure, averaged over the other factors. In Study 3 it applies to the Human minus AI gap at 100 hours. In Study 5 it applies to the Human minus AI difference at each modification level, the amount Alex changed the first artwork in making the second (none, slight or dramatic). Study 5's other bound, on editing time (the hours Alex is said to have spent making the second work), is taken from Study 3's real result.

## What to do with the R

Open `R Analysis Pipeline.Rproj` in RStudio, then follow each study's README. All five studies have been run, and none needs anything more unless its inputs change. To unblind a study is to set its switch, the environment variable `UNBLIND_STUDY2`, `UNBLIND_STUDY3`, `UNBLIND_STUDY4` or `UNBLIND_STUDY5`, to `TRUE`. An environment variable is a named setting that R reads when a run starts; left unset, the switch is `FALSE` and the run is blind.

From the RStudio console, starting from an empty workspace, that is, with no objects from an earlier session in R's memory (Session, then Clear Workspace):

```r
# Study 2, the real run
setwd("Study 2")
Sys.setenv(UNBLIND_STUDY2 = "TRUE")
rmarkdown::render("Study2_01_Quant.Rmd")
rmarkdown::render("Study2_03_Integration.Rmd")
```

Study 2's text notebook does not run again, because it reads no label and no rating. The real run writes its tables to `tables/` and its reports beside the `.Rmd` files, and the blind outputs stay in `blind_run/` and `tables/blind_run/`. The same steps with `UNBLIND_STUDY3`, `UNBLIND_STUDY4` or `UNBLIND_STUDY5` repeat the real run of Study 3, 4 or 5, with Study 3 before Study 5.

## Environment

- R 4.5.2, with readr, dplyr, tidyr, tibble, purrr, jsonlite, Matrix, lme4, lmerTest, emmeans, ordinal, glmnet, rmarkdown and knitr for Studies 2 to 5. Study 1 uses more packages, which its README names. Each run writes the exact R and package versions to a `sessionInfo` file in its study's folder.
- Python 3.12 for the text notebooks, run through the Jupyter kernel named `python312`. A kernel is the entry that tells Jupyter which Python to start; if this one is missing, `python3.12 -m ipykernel install --user --name python312` registers it. The notebooks use pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.5.2, SciPy 1.13.0, sentence-transformers 3.3.1 and PyTorch 2.5.1, and each run records its versions in `tables/`.
- A C++ compiler, the program that turns source code into a program the computer can run, for `Study 1/Study1_04_Robustness.Rmd`. Its four Bayesian models are written in Stan, a language for such models, and the R packages brms and rstan compile them whenever `Study 1/models/` holds no saved fit. On a Mac the compiler comes with Apple's Command Line Tools. On a Mac whose Xcode, Apple's full development suite, does not load, setting the environment variable `DEVELOPER_DIR=/Library/Developer/CommandLineTools` when R starts lets R compile the models with the Command Line Tools, for example from the `Study 1` folder: `DEVELOPER_DIR=/Library/Developer/CommandLineTools Rscript -e 'rmarkdown::render("Study1_04_Robustness.Rmd")'`.
- One sentence-embedding model, all-mpnet-base-v2, which turns each response into a list of numbers for the registered check on the topic model (the model that finds groups of words that tend to occur together) and nothing else. It is loaded only from the local Hugging Face cache, the folder where these Python libraries keep downloaded models, and is never downloaded during a run. `Study 1/README.md` gives the one command that fetches it once.

Paths are found from each file's own folder, and environment variables can name other folders; each study's README lists them.

`.gitignore` keeps knitted reports, blind runs, caches, backups, retired files and working notes out of version control, the git record of each version of the files.
