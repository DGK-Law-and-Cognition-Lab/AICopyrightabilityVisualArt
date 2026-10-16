# Beyond the Original Sin: Lay Evaluations of Creative Contribution in AI-Assisted Artworks

David G. Kamper, Alice Lin and Keith J. Holyoak, University of California, Los Angeles

This repository holds the data, the analysis code and its outputs, the stimuli and the registrations of the paper's five studies.

## What the studies ask

The five studies ask how people judge the creative contribution behind an artwork when they are told that an AI system had a hand in making it. In every study, participants read about an artist, Alex, who made the works either with design software and digital sketching tools (the Human label) or by prompting an AI system (the AI label). They rated each work and wrote a justification after every rating. Study 1 asks whether the AI label lowers the creativity and the effort people see in the same ten images. Study 3 asks why it does: if the label tells people that little work went in, then saying that Alex spent under 1 hour, 10 hours or 100 hours on an image should close the gap at 100 hours. Studies 2, 4 and 5 show second works that Alex made by hand from a first artwork, either unchanged or changed slightly or dramatically, and ask whether a penalty attached to an AI-made first artwork carries over to the work built on it. There, participants rated how transformative each second work was, how much its essence had changed and how much creativity went into it. Study 4 also varies the time Alex is said to have spent on the first artwork, and Study 5 the time he is said to have spent making the second.

## What is where

```
Analysis/R Analysis Pipeline/    the analysis code and its outputs
    Study 1/ to Study 5/         one folder per study, each with a README and a CHANGELOG
    Cross-study/                 the exploratory analyses across studies
    shared/                      the R and Python code that Studies 2 to 5 share
    Exported Studies/            the five surveys as exported from Qualtrics
Data/Study 1/ to Data/Study 5/   the de-identified Qualtrics exports
Stimuli/                         the printout of the Study 5 survey and its draft survey file
Docs/Preregistration/            copies of the registrations
```

The folders keep the layout of the project the analyses were run in, so every path in the code works as it stands.

## How to rerun the analyses

Each folder of code has a README that gives its commands, its inputs and its outputs. Start with `Analysis/R Analysis Pipeline/README.md`, which describes the software, the switch that makes a run blind and the state of each study, and then follow each study's README. An R Markdown file (`.Rmd`) mixes R code with text and is knitted, that is, run from top to bottom into a report. A Jupyter notebook (`.ipynb`) is a file of Python cells run in order. Every file finds its paths from its own folder.

Run the studies in this order, because later files read what earlier ones write:

1. Study 1: `Study1_01_Quant.Rmd`, `Study1_02_Text.ipynb`, `Study1_03_Integration.Rmd`, `Study1_04_Robustness.Rmd`, `Study1_Supplements.Rmd` and `Study1_Figures.Rmd`.
2. Studies 2, 3 and 4, each in the order its README gives: the ratings file (`StudyN_01_Quant.Rmd`), the text notebook (`StudyN_02_Text.ipynb`) and the integration file (`StudyN_03_Integration.Rmd`).
3. Study 5, after Study 3, because Study 5's equivalence bound on editing time is read from a file that Study 3's real run writes. `study5_build.py` builds Study 5's data, and its outputs are already in the folder; the same three files then run.
4. The analyses in `Cross-study/`, last, because they read what the five studies' real runs wrote: `CrossStudy_Penalty_Curve.Rmd`, and the folders `explanation_shift/`, `structural_topics/` and `image_check/`, each as its README says.

A run of Studies 2 to 5 is blind unless told otherwise. A blind run shuffles the condition labels, so every model and table can be checked for errors while no number describes the real conditions. The registrations are filed, so to repeat the real analyses, set the environment variable of each study (`UNBLIND_STUDY2` to `UNBLIND_STUDY5`, a named setting that R reads when a run starts) to `TRUE`, as each study's README shows.

Four things differ from the project folder the analyses were run in.

- Study 1's saved outputs that list participants carry the same codes as the data in place of the participant numbers: its long data file, the data files of its text notebook, its per-participant tables, and the responses that the notebook and `tables/text_audit_matches.txt` print. The run manifests, the records in each `tables/` folder that list every output with its SHA-256 checksum (a fingerprint of a file's exact bytes), still give the checksums of those files as the run wrote them. `Cross-study/CrossStudy_Penalty_Curve.Rmd` and the test in `shared/python/` compare Study 1's files with those manifests, so they accept the files again once Study 1 has been run, which writes new manifests.
- The survey files (`.qsf`) are as exported from Qualtrics, except that the link at the end of each survey, which sent participants to the subject pool's page for course credit, carries `REMOVED` in place of its credit token, the code that lets the link grant credit. No analysis reads that link. The run records that list each survey file with its checksum (`tables/studyN_quant_run_inputs.csv` in Studies 2 to 5, `Cross-study/tables/crossstudy_run_inputs.csv`, and the image check's `stimuli/extraction_run_manifest.csv`, `stimuli/extraction_checks.csv` and notebook output) give the checksums of the files as exported, so they do not match the survey files here.
- Study 1's model files, `Study 1/models/*.rds`, are not in this repository: the project's saved models hold the participant numbers, and the saved Bayesian fits also record the full path of the folder they were saved in. `Study1_01_Quant.Rmd` and `Study1_03_Integration.Rmd` write theirs again, and `Study1_04_Robustness.Rmd` refits its four Bayesian models when they are absent, which takes considerably longer and needs a C++ compiler (`Analysis/R Analysis Pipeline/README.md` says how to get one). `.gitignore` keeps the model files a run writes out of the repository.
- Knitted reports, the outputs of blind runs, R session files, working notes, retired files and backups are left out, and so is side work on a text measure that is not part of the pipeline (`Study 1/nlp/agency_rule_candidates/`, which the Study 1 README mentions). Several files also write copies for the manuscript into `Docs/Writing/Final Paper/`, which is not in this repository; the runs make that folder, and `.gitignore` keeps it out.

## The registrations

The five studies were registered together on the Open Science Framework (OSF), a website that keeps analysis plans with the date they were filed, on 8 October 2026, as one Open-Ended Registration in project https://osf.io/u3d69. Each registration keeps the nine questions of the form used by AsPredicted, another registration website. Every study's data had been collected before it was registered, and the first question of each registration says what had already been done with them.

Copies are in `Docs/Preregistration/`: `AsPredicted/Study1_AsPredicted.md` to `AsPredicted/Study5_AsPredicted.md`, and `Study1_Preregistration.md`, the full Study 1 plan. Each Markdown file (`.md`, plain text with light formatting marks) has a formatted Word copy (`.docx`) with the same wording beside it. The Markdown files are the ones the code is built to.

## The data

`Data/Study 1/` to `Data/Study 5/` hold each study's two exports from Qualtrics, the survey platform: `StudyN_Values.csv`, which stores each answer as a code, and `StudyN_Labels.csv`, which stores the text the participant saw. They are the raw exports, de-identified in two ways and changed in no other.

- The IP address and the latitude and longitude that Qualtrics records with each response are removed. Their cells are empty, but the columns stay, so no column moves.
- The participant number that each person typed in is replaced by a code. The numbers, sorted from smallest to largest, were given the codes 100001, 100002 and so on, one code per person across all five studies. The codes keep the order of the numbers, so every step that sorts participants sorts them as before, and a person who took part in two studies has the same code in both. The key that links the codes to the numbers is not in this repository.

`ResponseId`, the random code that Qualtrics gives each response, is unchanged. So is every other cell, the written justifications included, along with the three header rows of each export and its quoting and line endings.

## The stimuli

The 30 images that participants saw are in `Analysis/R Analysis Pipeline/Cross-study/image_check/stimuli/`, as the surveys showed them: ten first artworks, five with a human or humanoid figure and five without, and a Slight and a Dramatic second work made from each. Studies 1 and 3 showed the ten first artworks, and Studies 2, 4 and 5 showed all thirty. The images were taken out of a printout of the Study 5 survey without being re-encoded, and `Cross-study/image_check/README.md` says how. The printout, `Stimuli/Qualtrics Survey Software.pdf` (71 MB), and the draft of the Study 5 survey, `Stimuli/Draft_-_AI_Copyright_-_Study_5.qsf`, which the extraction also reads, are in `Stimuli/`. Each study's survey file as exported from Qualtrics (`.qsf`, a file that records every question, its wording and its answer options) is in `Analysis/R Analysis Pipeline/Exported Studies/`.

## What has to be fetched separately

Two published word-norm files, the average ratings that other laboratories collected for single English words, are not ours to redistribute. The text notebook of every study reads them from `Analysis/R Analysis Pipeline/Study 1/nlp/norms/`, whose README gives the sources, the file names and the checksums:

- the concreteness ratings of Brysbaert, Warriner and Kuperman (2014), *Behavior Research Methods, 46*, 904–911, saved as `Concreteness_ratings_Brysbaert_et_al_BRM.txt`;
- the valence, arousal and dominance ratings of Warriner, Kuperman and Brysbaert (2013), *Behavior Research Methods, 45*, 1191–1207, saved as `Warriner_et_al_2013_VAD.csv`.

Both are published with the supplementary material of each article on the publisher's Springer page, and on the authors' site, crr.ugent.be. `Study 1/.gitignore` keeps the two files out of the repository once they are in place.

Three trained models are fetched once from Hugging Face, a website that hosts them, into the local Hugging Face cache, the folder where the Python libraries keep downloaded models. The code reads only that cache and never downloads anything.

- all-mpnet-base-v2, a sentence-embedding model that turns each justification into a list of numbers, for the check on the topic model in each study's text notebook and for the analysis in `Cross-study/explanation_shift/`. `Analysis/R Analysis Pipeline/Study 1/README.md` gives the one command that fetches it.
- DINOv2 and CLIP, two image networks that the image check uses to measure how far apart the stimuli are. `Analysis/R Analysis Pipeline/Cross-study/image_check/README.md` gives the command that fetches them at fixed versions.
