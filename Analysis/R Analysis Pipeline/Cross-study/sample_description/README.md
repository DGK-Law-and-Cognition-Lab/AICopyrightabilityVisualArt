# Sample description: age, gender and people in more than one study

**This step is descriptive.** It was specified on 19 October 2026, after the registered results of all five studies were known. No registration names it, and it tests no hypothesis. Every table it writes says so in its last column, `analysis_status`.

## What it reports

For each study, it describes the participants whose answers the study analyzed:

- how many there were;
- their age: the mean, the standard deviation (how far ages typically lie from the mean), the youngest and the oldest;
- their answers to the question "What is your gender?", which offered Male, Female, Other and Prefer not to say.

Across the five studies, it counts participations and people. A participation is one person's session in one study, so the five analyzed samples added together give the number of participations. The step reports how many different people those participations come from, how many people were analyzed in two or more studies, and how many in each pair of studies. Some people took part in two studies, so there are fewer people than participations. No registered analysis removes a second participation, and this step changes no analysis.

## Where the numbers come from

**The analyzed sample.** Each study's analyzed sample is the set of participants in the long data file that the study's own real run wrote (its run on the true condition labels, not a blind run on shuffled ones), `Study N/studyN_long_with_text.csv`, which has one row per participant, item and rating question, with the study's own exclusions already applied. The step takes its participants from that file and applies no exclusion of its own, so it describes the people each study analyzed, no more and no fewer.

**Age and gender.** Both are read from the study's Labels export from Qualtrics, the survey platform: `Data/Study N/StudyN_Labels.csv`, which stores each answer as text, either the wording of the option chosen or what the participant typed. Each analyzed participant is found in the export by the code the long data file uses. In Study 1 that is the subject-pool participant code (described below); in Studies 2 to 5 it is `ResponseId`, the random code Qualtrics gives each response. Age was typed as free text. It is read with `readr::parse_number()`, which takes the first number in the answer, so "20 years" reads as 20 and an answer with no number would read as missing; this is how Study 1's own pipeline reads age. The standard deviation is R's `sd()`, which divides by the number of ages minus one.

**Gender groups.** The survey offered the answers Female and Male; the tables and the paper's macros (the named commands through which the manuscript prints each number) call these women and men. Every other answer, that is Other, Prefer not to say or a blank, is counted in one group, other. `sample_description_gender.csv` keeps each answer separately, so the group can be split again.

**People across studies.** The export's `id` column holds the subject-pool participant code, the code that the survey sent back at its end to the subject pool's page for granting course credit. A code that appears in two studies' analyzed samples is counted as one person analyzed twice. In the public copy of the project, each code is replaced by another code, with the same replacement in every study, so the step finds the same people there and writes the same result tables. The codes are held in memory while the step runs. No table holds one, and no table holds any value that belongs to one participant.

## What it checks

The run stops, and writes no result table, unless every check passes. `tables/sample_description_checks.csv` lists each check with its expected and observed value.

For each study:

- The long data file is the one listed in the study's real run manifest, the record, in the study's `tables/` folder, of every file a real run wrote, each with its SHA-256 checksum (a 64-character fingerprint of the file's exact bytes).
- So is the study's exclusion-flow table, the table of how many records each registered exclusion step removed.
- The long data file holds as many participants as the last row of that table.
- Every analyzed participant matches exactly one record of the Labels export and has a participant code, and no code repeats within the study.
- Every gender answer is one the survey offered, or a blank.

For Study 1, whose pipeline already reports age and gender in `Study 1/tables/study1_demo_age.csv` and `study1_demo_gender.csv`:

- Both tables are the ones listed in Study 1's real run manifest.
- The age and gender carried in Study 1's long data file agree with the export for every analyzed participant.
- The number of ages, their mean, their standard deviation, the youngest and the oldest equal Study 1's own table exactly, as stored. The macros `\SOneAgeMean`, `\SOneAgeSD`, `\SOneAgeMin` and `\SOneAgeMax` are read from that table, so they print the numbers this step computes.
- The counts of women, men and other answers equal Study 1's own gender table.
- That table holds no answer but Female, Male and Other. Its Other row, which `\SOneNGenderOther` prints, is therefore the whole other group.

Across the five studies, the participations equal the last counts of the five exclusion flows added together.

## How to run it

Run it after the real runs of all five studies, because it reads what they wrote. It does not depend on the other cross-study analyses. From this folder:

```sh
Rscript SampleDescription.R
```

or, in RStudio, with this folder as the working folder, `source("SampleDescription.R")`. The run takes about a second.

## What it reads

From each study folder `Study N/`:

- `studyN_long_with_text.csv`, the long data file;
- `tables/studyN_quant_run_manifest.csv`, the run manifest of the study's first R Markdown file;
- the exclusion-flow table: `tables/studyN_exclusion_flow.csv` in Studies 1 to 4, and `tables/study5_exclusion_flow_registered.csv` in Study 5, the one Study 5's first R Markdown file writes;
- in Study 1 only, `tables/study1_demo_age.csv` and `tables/study1_demo_gender.csv`.

From `Data/Study N/`, the Labels export `StudyN_Labels.csv`. It uses `shared/R/fit_status.R` for paths and the run record and `shared/R/qualtrics_import.R` to read the exports.

## What it writes

In `tables/`:

- `sample_description_by_study.csv`: one row per study, with these columns:
  - `n`, the participants analyzed;
  - `age_n`, the participants whose age answer holds a number;
  - `age_mean`, `age_sd`, `age_min` and `age_max`;
  - `age_answers_not_a_bare_number`, the age answers that hold more than a whole number, such as "20 years";
  - `n_women`, `n_men` and `n_gender_other`, the three gender groups.
- `sample_description_gender.csv`: one row per study and gender answer (Female, Male, Other, Prefer not to say, and "(no answer)" for a blank), with the group it is counted in and the count, zeros included.
- `sample_description_overlap.csv`: the participations, the different people, the people analyzed in two or more studies and in three or more, and the people analyzed in each pair of studies.
- `sample_description_checks.csv`: every check above.
- `sample_description_run_inputs.csv`, `sample_description_sessionInfo.txt`, `sample_description_package_versions.csv` and, written last, `sample_description_run_manifest.csv`. The run deletes its earlier manifest and outputs when it starts, so a manifest on disk means the run reached its end. The run inputs and the manifest carry the run's identifier and the checksums of its inputs, so they differ between the project and the public copy, whose exports and Study 1 long data file carry the replacement codes.

## Where the paper uses it

`Docs/Writing/Final Paper/tools/make_numbers.py` reads two of these tables into the paper's macros.

- From `sample_description_by_study.csv`: the age of Studies 2 to 5 (`\STwoAgeMean`, `\STwoAgeSD`, `\STwoAgeMin`, `\STwoAgeMax`, and the same four for `SThree`, `SFour` and `SFive`); women and men in all five studies (`\SOneNWomen` to `\SFiveNWomen`, `\SOneNMen` to `\SFiveNMen`); and the other group in Studies 2 to 5 (`\STwoNGenderOther` to `\SFiveNGenderOther`).
- From `sample_description_overlap.csv`: `\NPeople`, the different people across the five analyzed samples, and `\NPeopleRepeat`, the people analyzed in two or more studies.

Study 1's age macros and `\SOneNGenderOther` are still read from Study 1's own tables, which this step reproduces.

## The environment

R 4.5.2 with readr 2.2.0, dplyr 1.2.1 and tibble 3.3.1. The script names these versions, and each run records the versions it used beside them in `tables/sample_description_package_versions.csv`.

Paths are found from the script's own folder. These environment variables, named settings that the shell passes to R when it starts, name other folders:

| Variable | What it names |
|---|---|
| `SAMPLE_DESCRIPTION_DIR` | this folder |
| `PIPELINE_DIR` | the analysis pipeline folder, two levels up |
| `STUDY_SHARED_R` | the shared R helpers |
| `STUDY1_DIR` to `STUDY5_DIR` | the five study folders |
| `CROSS_STUDY_PROJECT_ROOT` | the project root, the folder that holds `Data` and `Analysis` |

Printed paths are relative to the project root, so no output names a folder particular to one machine.

## What it does not show

- Age and gender are what participants typed or chose. Nothing checks them against another record.
- The count of people rests on the participant code. It would count one person as two if that person had held two codes, and two people as one if they had shared a code. No analyzed record lacks a code, and no code repeats within a study.
- The other group joins three different answers, Other, Prefer not to say and a blank. The gender table keeps them apart.
- The step counts people who took part twice. It does not ask whether they answered differently the second time, although all five studies drew on the same ten original images, so a second participation came after seeing some of them once.
