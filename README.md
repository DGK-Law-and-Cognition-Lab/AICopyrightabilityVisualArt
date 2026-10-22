# Beyond the Original Sin: Lay Evaluations of Creative Contribution in AI-Assisted Artworks

David G. Kamper, Alice Lin and Keith J. Holyoak

Department of Psychology, University of California, Los Angeles; University of Chicago Law School (D.G.K.)

This repository holds everything behind the paper: the manuscript and its Supplementary Information, the de-identified data of the five studies, the surveys and the 30 images participants saw, the registrations, the analysis code with every output it wrote, and the scripts that write every number, table and figure in the paper.

| What | Where |
|---|---|
| The paper | [`Docs/Writing/Final Paper/main.pdf`](Docs/Writing/Final%20Paper/main.pdf) |
| Supplementary Information | [`Docs/Writing/Final Paper/supplement.pdf`](Docs/Writing/Final%20Paper/supplement.pdf) |
| Source data for the figures | [`Docs/Writing/Final Paper/figures/plotted_values.csv`](Docs/Writing/Final%20Paper/figures/plotted_values.csv) |
| The data | [`Data/`](Data) |
| The analysis code and its outputs | [`Analysis/R Analysis Pipeline/`](Analysis/R%20Analysis%20Pipeline) |
| The images participants saw | [`Analysis/R Analysis Pipeline/Cross-study/image_check/stimuli/`](Analysis/R%20Analysis%20Pipeline/Cross-study/image_check/stimuli) |
| The registrations | [`Docs/Preregistration/`](Docs/Preregistration), filed on the Open Science Framework |

## The question

United States copyright protects only what a human author contributed. When a person reworks an image made with an AI system, the rules ask whoever applies them to credit the person's part while knowing that the base was machine-made. Can lay evaluators do that? On one view, which the paper calls the original-sin hypothesis, an AI origin acts like a stain that passes to whatever is built from it. On another, an AI label is information about who did what, and it matters only for the act it describes.

## What the five studies found

Every image was made with OpenAI's DALL·E, used through ChatGPT. A label told each participant that the artist, Alex, had made the originals either with design and sketching tools (the Human label) or by prompting an AI system (the AI label), so any difference between the two groups is an effect of the label.

- On the same images, the AI label lowered ratings of the originals' creativity by 0.45 points and of their effort by 0.92 points on 1-to-5 scales (Study 1).
- Saying that Alex had spent up to 100 hours on an image raised ratings under both labels, but the gap between the labels persisted (Study 3).
- When Alex then edited each image by hand, ratings of the new work rose steeply with how much he changed it. The label carried much less into those ratings than into ratings of the originals: small and uneven across studies, but not nothing, and detectable at slight edits in Study 5. That comparison is read across studies; no study tested it.

Each result carries the status its registration gives it, and the paper says what had been seen of each study's data before it was registered: all five studies were registered after their data were collected.

## What is where

```
Docs/Writing/Final Paper/        the manuscript
    main.pdf, supplement.pdf     the paper and its Supplementary Information
    main.tex, sections/          the paper's LaTeX source
    supplement/                  the Supplementary Information's source, tables and figures
    tools/                       the scripts that write every number, table and figure
    generated/                   every number in the text, with the table, row and column behind it
    figures/, tables/            the figures, the source data behind them, and Table 1
Analysis/R Analysis Pipeline/    the analysis code and its outputs
    Study 1/ to Study 5/         one folder per study, each with a README and a CHANGELOG
    Cross-study/                 the analyses across studies, the image check and the sample description
    shared/                      the R and Python code that Studies 2 to 5 share
    Exported Studies/            the five surveys as exported from Qualtrics
Data/Study 1/ to Data/Study 5/   the de-identified Qualtrics exports
Stimuli/                         the printout of the Study 5 survey and its draft survey file
Docs/Preregistration/            copies of the registrations
```

The folders keep the layout of the project the analyses were run in, so every path in the code works as it stands.

## Rebuilding the paper

From `Docs/Writing/Final Paper/`, with Python 3.12 (matplotlib and Pillow) and a LaTeX installation:

```
python3 tools/make_numbers.py
python3 tools/make_tables.py
python3 tools/make_figures.py
latexmk -pdf main.tex
latexmk -pdf supplement/supplement.tex
```

`make_numbers.py` reads every number the paper prints from the analysis tables and records, in `generated/numbers_check.csv`, the table, row and column behind each. `make_figures.py` records every value it plots, with its source, in `figures/plotted_values.csv`, the source data for the figures. The curves of Supplementary Figure 5 come from Study 1's saved Bayesian fits through `tools/study1_ppc_data.R`; those fits are not in this repository (see below), so the committed curves are used unless the fits have been made again. The folder's `README.md` describes each step.

## Rerunning the analyses

Each folder of code has a README that gives its commands, its inputs and its outputs. Start with `Analysis/R Analysis Pipeline/README.md`, which describes the software, the switch that makes a run blind and the state of each study, and then follow each study's README. An R Markdown file (`.Rmd`) mixes R code with text and is knitted, that is, run from top to bottom into a report. A Jupyter notebook (`.ipynb`) is a file of Python cells run in order. Every file finds its paths from its own folder.

Run the studies in this order, because later files read what earlier ones write:

1. Study 1: `Study1_01_Quant.Rmd`, `Study1_02_Text.ipynb`, `Study1_03_Integration.Rmd`, `Study1_04_Robustness.Rmd`, `Study1_Supplements.Rmd` and `Study1_Figures.Rmd`.
2. Studies 2, 3 and 4, each in the order its README gives: the ratings file (`StudyN_01_Quant.Rmd`), the text notebook (`StudyN_02_Text.ipynb`) and the integration file (`StudyN_03_Integration.Rmd`).
3. Study 5, after Study 3, because Study 5's equivalence bound on editing time is read from a file that Study 3's real run writes. `study5_build.py` builds Study 5's data, and its outputs are already in the folder; the same three files then run.
4. The analyses in `Cross-study/`, last, because they read what the five studies' real runs wrote: `CrossStudy_Penalty_Curve.Rmd`, and the folders `explanation_shift/`, `structural_topics/`, `image_check/` and `sample_description/`, each as its README says.

A run of Studies 2 to 5 is blind unless told otherwise. A blind run shuffles the condition labels, so every model and table can be checked for errors while no number describes the real conditions. The registrations are filed, so to repeat the real analyses, set the environment variable of each study (`UNBLIND_STUDY2` to `UNBLIND_STUDY5`, a named setting that R reads when a run starts) to `TRUE`, as each study's README shows.

## The data

`Data/Study 1/` to `Data/Study 5/` hold each study's two exports from Qualtrics, the survey platform: `StudyN_Values.csv`, which stores each answer as a code, and `StudyN_Labels.csv`, which stores the text the participant saw. They are the raw exports, de-identified in two ways and changed in no other.

- The IP address and the latitude and longitude that Qualtrics records with each response are removed. Their cells are empty, but the columns stay, so no column moves.
- The participant number that each person typed in is replaced by a code. The numbers, sorted from smallest to largest, were given the codes 100001, 100002 and so on, one code per person across all five studies. The codes keep the order of the numbers, so every step that sorts participants sorts them as before, and a person who took part in two studies has the same code in both. The key that links the codes to the numbers is not in this repository.

`ResponseId`, the random code that Qualtrics gives each response, is unchanged. So is every other cell, the written justifications included, along with the three header rows of each export and its quoting and line endings.

## The images and the surveys

The 30 images that participants saw are in `Analysis/R Analysis Pipeline/Cross-study/image_check/stimuli/`, as the surveys showed them: ten originals, five with a human or humanoid figure and five without, and a Slight and a Dramatic second work made by hand from each. Studies 1 and 3 showed the originals, and Studies 2, 4 and 5 showed all thirty. The images were taken out of a printout of the Study 5 survey without being re-encoded, and `Cross-study/image_check/README.md` says how. The printout, `Stimuli/Qualtrics Survey Software.pdf` (71 MB), and the draft of the Study 5 survey, `Stimuli/Draft_-_AI_Copyright_-_Study_5.qsf`, which the extraction also reads, are in `Stimuli/`. Each study's survey file as exported from Qualtrics (`.qsf`, a file that records every question, its wording and its answer options) is in `Analysis/R Analysis Pipeline/Exported Studies/`.

## The registrations

The five studies were registered together on the Open Science Framework (OSF), a website that keeps study plans with the date they were filed, on 8 October 2026: https://osf.io/u3d69/overview?view_only=be795b275c3548428d74457df31a4159. Each registration answers the nine questions of the form used by AsPredicted, another registration website, and Study 1 also has a long registration. Every study's data had been collected before it was registered, and the first question of each registration says what had already been done with them. Copies are in `Docs/Preregistration/`: `AsPredicted/Study1_AsPredicted.md` to `AsPredicted/Study5_AsPredicted.md`, and `Study1_Preregistration.md`, each with a formatted Word copy (`.docx`) beside it.

## What differs from the project folder

- Study 1's saved outputs that list participants carry the same codes as the data in place of the participant numbers: its long data file, the data files of its text notebook, its per-participant tables, and the responses that the notebook and `tables/text_audit_matches.txt` print. The run manifests, the records in each `tables/` folder that list every output with its SHA-256 checksum (a fingerprint of a file's exact bytes), still give the checksums of those files as the run wrote them. `Cross-study/CrossStudy_Penalty_Curve.Rmd` and the test in `shared/python/` compare Study 1's files with those manifests, so they accept the files again once Study 1 has been run, which writes new manifests.
- The survey files (`.qsf`) are as exported from Qualtrics, except that the link at the end of each survey, which sent participants to the subject pool's page for course credit, carries `REMOVED` in place of its credit token, the code that lets the link grant credit. No analysis reads that link. The run records that list each survey file with its checksum give the checksums of the files as exported, so they do not match the survey files here.
- Study 1's model files, `Study 1/models/*.rds`, are not in this repository: the project's saved models hold the participant numbers, and the saved Bayesian fits also record the full path of the folder they were saved in. `Study1_01_Quant.Rmd` and `Study1_03_Integration.Rmd` write theirs again, and `Study1_04_Robustness.Rmd` refits its four Bayesian models when they are absent, which takes considerably longer and needs a C++ compiler (`Analysis/R Analysis Pipeline/README.md` says how to get one). `.gitignore` keeps the model files a run writes out of the repository.
- Knitted reports, the outputs of blind runs, R session files, the authors' working notes, superseded figures, LaTeX's build files, retired files and backups are left out, and so is side work on a text measure that is not part of the pipeline (`Study 1/nlp/agency_rule_candidates/`, which the Study 1 README mentions). Several analysis files write copies of their tables and figures into `Docs/Writing/Final Paper/` when they run.

## What has to be fetched separately

Two published word-norm files, the average ratings that other laboratories collected for single English words, are not ours to redistribute. The text notebook of every study reads them from `Analysis/R Analysis Pipeline/Study 1/nlp/norms/`, whose README gives the sources, the file names and the checksums:

- the concreteness ratings of Brysbaert, Warriner and Kuperman (2014), *Behavior Research Methods, 46*, 904–911, saved as `Concreteness_ratings_Brysbaert_et_al_BRM.txt`;
- the valence, arousal and dominance ratings of Warriner, Kuperman and Brysbaert (2013), *Behavior Research Methods, 45*, 1191–1207, saved as `Warriner_et_al_2013_VAD.csv`.

Both are published with the supplementary material of each article on the publisher's Springer page, and on the authors' site, crr.ugent.be. `Study 1/.gitignore` keeps the two files out of the repository once they are in place.

Three trained models are fetched once from Hugging Face, a website that hosts them, into the local Hugging Face cache, the folder where the Python libraries keep downloaded models. The code reads only that cache and never downloads anything.

- all-mpnet-base-v2, a sentence-embedding model that turns each justification into a list of numbers, for the check on the topic model in each study's text notebook and for the analysis in `Cross-study/explanation_shift/`. `Analysis/R Analysis Pipeline/Study 1/README.md` gives the one command that fetches it.
- DINOv2 and CLIP, two image networks that the image check uses to measure how far apart the images are. `Analysis/R Analysis Pipeline/Cross-study/image_check/README.md` gives the command that fetches them at fixed versions.

## Earlier report

Studies 2 and 4 were first reported in Kamper, D. G., Lin, A. and Holyoak, K. J. (2025), Is AI-assisted creativity an "Original Sin"?: Lay judgments of qualities justifying copyright protection for artworks derived from AI- vs. human-generated sources, *Proceedings of the 47th Annual Conference of the Cognitive Science Society*, 1667–1673. The paper and its Supplementary Information say where this repository's registered analyses differ from that report.

## Licence

The code (every `.R`, `.Rmd`, `.py`, `.ipynb` and `.sh` file) is released under the MIT licence (`LICENSE`). Everything else, the data, surveys, images, registrations, outputs and the manuscript included, is released under the Creative Commons Attribution 4.0 International licence (`LICENSE-CC-BY-4.0.md`). The two word-norm files that must be fetched separately are covered by neither.
