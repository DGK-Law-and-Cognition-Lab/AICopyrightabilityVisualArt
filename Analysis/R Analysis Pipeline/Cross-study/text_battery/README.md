# Text battery: what participants wrote, in all five studies

**This analysis is exploratory.** It was specified on 31 October 2026, after every registered result was known, so that the same analyses of the written explanations run in all five studies. No registration names it, and it changes no registered verdict. Every table says so in its first column, `analysis_status`.

## What it asks

After each rating, participants explained it in a few words. Each study's text step flagged every explanation with eight fixed word lists, the same in all five studies (`Study N/tables/studyN_text_rules.txt`), without seeing the label or the rating. Until now each study used the flags for its own registered checks, and only Study 1 linked them to ratings, under the Human label alone. This folder runs three analyses the same way in every study.

1. **What the explanations named.** The share of explanations that carry each of six flags: visible detail, time, skill, the idea, prompting or a machine, and a machine making the work. It is given under each label, AI against Human, and in Studies 2, 4 and 5 at each modification level (None, Slight, Dramatic) and over all three.
2. **The words that set the label groups apart.** Every content word (a word left once a fixed list of function words such as *the* and *of* is removed) is scored by how much more often AI-label explanations use it than Human-label explanations, with no word list chosen in advance. The score is Monroe, Colaresi and Quinn's log-odds ratio with an informative Dirichlet prior, the method of section 8 of `Study 1/Study1_02_Text.ipynb`. It compares the odds of the word on the two sides after adding to each count a small amount in proportion to the word's overall frequency, so a rare word needs more evidence to move, and divides by its standard error to give a z score. With thousands of words scored at once, z ranks words; it is not a significance test.
3. **Words linked to ratings within a label.** For each flag, how much higher or lower the rating was when the explanation carried the flag, among participants who saw the same label, and whether that link differs between the labels. For example: did an explanation that mentioned prompting or a machine come with a lower rating even among people who were all told the same thing about how the work was made?

Beside the six word-list flags, every analysis also runs on three flags of the agency rule (`agency/`), which reads each explanation's grammar for who it says made or changed the work: a person, a machine, or no one named. The rule was tested once against three model annotators on 400 explanations it had never read. The machine flag met the pass marks set in advance and is a validated measure; the person flag and the no-doer flag did not, and are reported as exploratory. Every table says which kind each flag is in its column `flag_source`.

A word-list flag records a topic, not an endorsement: "not much detail" is detail talk. Every explanation was written after its rating, so nothing here says what produced a rating; the analyses describe what people wrote beside the numbers they gave.

Study 5's sample is its analyzed sample of 197: the 223 of its registration less the 26 who had completed an earlier study (`../repeat_participants/`).

## The files

| File | What it does |
|---|---|
| `TextBattery_01_Measure.py` | Reads four columns of each study's long data file (the participant, the work, the question and the text) and nothing else, counts every content word of every explanation with the shared tokenizer, `tokenize()` in `../../shared/python/study_text.py`, and applies the frozen agency rule to every explanation. It never reads the label, the conditions or the rating: the shared `check_blind()` refuses any other column. |
| `TextBattery_02_Analysis.R` | Checks its inputs, joins each study's flags to the label, the conditions and the rating, and runs the three analyses. Before it fits the rating models, it checks that its code reproduces Study 1's deposited tables, and it stops if any check fails. |
| `README.md` | This file. |
| `CHANGELOG.md` | The edit history of the two files, which carry none themselves. |
| `agency/` | The agency rule, its codebook, its validation plan, samples, annotations, freeze record and scores, with its own README. |
| `nlp/` | The word counts and the agency flags that step 1 writes. The public copy of the project leaves this folder out, because it labels Study 1's participants by their participant numbers; step 1 writes it again in a few seconds. |
| `tables/` | Every table the two steps write. |

## How to run it

Each study's pipeline must have been run first, on its real labels. From this folder:

```sh
python3 TextBattery_01_Measure.py
Rscript TextBattery_02_Analysis.R
```

Step 1 took about a minute and a half, most of it parsing 42,769 explanations for the agency rule, and step 2 about fifteen seconds on a twelve-core Mac; step 2 fits its models on up to eight cores at once. Step 1 needs spaCy 3.7.4 with its model `en_core_web_sm` 3.7.1 (`agency/README.md`).

Step 2 reads, from each study folder: the long data file `studyN_long_with_text.csv`; the flags, `nlp/studyN_text_measures.csv`; and the two run manifests in `tables/`, the records each study's real runs wrote of their outputs with the SHA-256 checksum (a 64-character fingerprint of a file's exact bytes) of each. It also reads the agency flags and the agency rule's validation scores, and the Study 1 tables it reproduces. It uses `../../shared/R/fit_status.R` for the fit status of every model and for the run record.

## What it checks

The run stops unless:

- each long data file and each flags file has the checksum its study's real run manifest lists, so the run reads the files the registered analyses read;
- step 1 read the same long data files, and the word counts are the ones step 1 wrote;
- each study has its registered number of participants, each participant has one label, and the flags join to the ratings one row to one row;
- the code reproduces Study 1's deposited tables: the distinctive words of high against low ratings under the Human label (`Study 1/tables/text_keyness_effort.csv` and `text_keyness_creativity.csv`), the seven Human-label models of rating on a flag (`Study 1/tables/study1_text_*_lmm.csv`), and the shares of effort explanations that name detail, time, skill and prompting. On the run of 31 October 2026 the largest difference was 1.2e-14.

## How the code reads the specification

- **The explanations analyzed.** Those with at least one letter, on a five-point item, with a rating: the explanations the registered analyses rate, less the few with no text. The two six-point transformativeness items of Studies 4 and 5 are left out, as each study's main analysis leaves them out. `tables/text_battery_samples.csv` gives the counts.
- **The flags.** `says_detail`, `says_time`, `says_skill`, `says_concept` (the idea), `says_prompt` (prompting, typing, generating, or a named machine or image generator) and `says_machine_made` (a machine, a program or an image generator making the work, whether stated, denied or supposed), from each study's flags file, unchanged. The rules are in `Study 1/tables/text_rules.txt`, identical in all five studies except for the title and the count of responses. The agency flags `person_maker`, `machine_maker` and `agentless_making` come from step 1, which applies the frozen rule (`agency/agency_freeze.md`); their `flag_source` gives each one's validation result from `agency/tables/agency_validation_scores.csv`.
- **The intervals of the shares.** From 2,000 resamples of participants within each label from seed 20260421, the seed Study 1's registration names for resampling. Each resample draws, within each label, as many participants as the label has, with replacement, and pools all their explanations; the difference AI minus Human is taken within each resample. The interval is the 2.5th to the 97.5th percentile.
- **The distinctive words.** Prior weight 500 and a floor of five uses, as in Study 1. Every word is scored, and each row gives, beside z, the word's count on each side and how many explanations and how many participants used it under each label, so that a word one person repeated can be told from a word many people used.
- **The rating links.** For one study, question and flag, the model is `rating ~ <the study's registered fixed effects> + on_human + on_ai + (1 | id) + (1 | image)`, where `on_human` is 1 for a Human-label explanation that carries the flag and `on_ai` is 1 for an AI-label explanation that carries it. The registered fixed effects, with the label and the conditions under sum-to-zero contrasts, absorb the label, the conditions and their interactions, so each coefficient compares explanations with and without the flag under the same label and condition. AI minus Human is the difference of the two coefficients. The models are fitted with lmerTest by restricted maximum likelihood with the bobyqa optimizer, and each estimate has Satterthwaite's degrees of freedom, as in the registered models. The registered fixed effects are: Study 1, `label * stimulus_type`; Study 2, `label * modification * image_kind`; Study 3, `label * time`; Study 4, `label * source_time * modification`; Study 5, `label * editing_time * modification + image_kind`.
- **The three further versions.** *Within person*: the flag is split into the participant's share of explanations (to that question) that carry it, and the explanation's departure from that share. The departure's coefficient is the link within one person's own explanations, which no difference between people can produce; the share's is the link between people. *Word count*: the main model plus the z-scored logarithm of the explanation's word count, since a longer explanation has more chances to name anything. *Polarity*: for detail, time, skill and the idea, the mentions the rules read as claimed and those they read as denied ("not much detail"), each against explanations without the flag.
- **Links too rare to estimate.** A link is reported under a label only where the flag appears in at least 20 explanations from at least 10 participants under that label; the within-person link also needs at least 10 participants who carry the flag in some but not all of their explanations. The table keeps these rows with a note and no estimate.
- **Multiple comparisons.** `p_holm` applies Holm's correction to the main-model links of each study and sample together (each flag, question and label). No other interval or p-value is adjusted.

## What it writes

In `tables/`:

- `text_battery_input_checks.csv` and `text_battery_reproduction_checks.csv`: the checks above.
- `text_battery_samples.csv`: participants and explanations by study and label.
- `text_battery_prevalence.csv`: the share of explanations that carry each flag, by study, sample, question, level and label, and AI minus Human, with intervals and counts.
- `text_battery_keyness.csv`: every scored word, by study, sample and question, with its z score, the side it leans to and its rank on that side, its log-odds ratio, and its counts of uses, explanations and participants under each label.
- `text_battery_rating_links.csv`: every rating link, by study, sample, question, flag, version and label, with its estimate, standard error, degrees of freedom, p-value, Holm p-value for the main model, 95 percent interval, the counts behind it, and the fit's convergence and singularity.
- `text_battery_measure_environment.csv` and `text_battery_measure_run_manifest.csv` from step 1; `text_battery_analysis_run_inputs.csv`, `text_battery_analysis_package_versions.csv`, `text_battery_analysis_sessionInfo.txt` and, written last, `text_battery_analysis_run_manifest.csv` from step 2. Each step deletes its earlier manifest when it starts and writes the new one last, so a manifest on disk means the run reached its end.

No table holds a participant code or any value that belongs to one participant. The tables name the unchanged level `None`; a Python reader should pass `keep_default_na=False` to `pandas.read_csv`, which otherwise reads it as missing.

## Study numbers

This folder, like the pipeline, names studies by their folders, which follow the order in which the studies were run. The paper numbers them in the order it presents them, which swaps two: the pipeline's Study 2 is the paper's Study 3, and its Study 3 is the paper's Study 2. Studies 1, 4 and 5 are the same in both. Every table gives both, as `study_pipeline` and `study_paper`, and `part` says whether the study rated originals (paper Studies 1 and 2) or second works (paper Studies 3, 4 and 5).

## The environment

- Python 3.12.3 with pandas 2.2.2 and NumPy 1.26.4, and the packages `study_text.py` imports, recorded in `tables/text_battery_measure_environment.csv`.
- R 4.5.2 with readr 2.2.0, dplyr 1.2.1, tidyr 1.3.2, tibble 3.3.1, lme4 2.0-1, lmerTest 3.2-1 and Matrix 1.7-5, recorded in `tables/text_battery_analysis_package_versions.csv`.

Paths are found from each file's own folder; `STUDY_SHARED_PYTHON` names another folder for the shared Python module. Printed paths are relative to the pipeline folder, so no output names a folder particular to one machine.
