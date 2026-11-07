# Changelog: text battery

The two analysis files carry no edit history themselves; it is kept here.


## 2026-11-06

`agency/AgencyValidation.py`: `annotate` now asks for an API key only when a text is not in the cache, so replaying the cached annotations runs without keys and sends nothing, as the README says. Before, it stopped unless both key variables were set, even with nothing to send. No output changes.

## 1 November 2026, Study 5's analyzed sample

- Study 5's analyzed sample is now its 197 (the 223 of its registration less the 26 who had completed an earlier study, a deviation adopted this day; `../repeat_participants/`). Step 2 no longer runs Study 5 a second time without repeat participants, and no longer reads the Labels exports or the sample description; step 1 expects 10,638 Study 5 explanations. The agency validation samples were drawn on 31 October 2026 from the explanations of the registered sample; `agency/AgencyValidation.py` now reads that sample's long data file for Study 5, so `draw` would draw the same samples again.

## 1 November 2026

- Added the agency measure (`agency/`): a rule that reads each explanation's grammar for who it says made or changed the work, with three flags (a person, a machine, no doer named). Its codebook was written before any coding and revised once on the development sample; three model annotators (OpenAI, Google, Claude) coded a development sample of 250 and a validation sample of 400; the rule was adjusted on the development sample, frozen (`agency/agency_freeze.md`), and tested once on the validation sample against pass marks fixed in advance. The machine flag passed (agreement 0.993, recall 0.86 of yes and 0.997 of no); the person flag (recall 0.50) and the no-doer flag (recall 0.68) did not and are reported as exploratory.
- `TextBattery_01_Measure.py` applies the frozen rule to every explanation and stops if the rule differs from the frozen one; `TextBattery_02_Analysis.R` runs every analysis on the three agency flags beside the six word-list flags, and every table gives each flag's source and validation result in `flag_source`.

## 31 October 2026

- Added `TextBattery_01_Measure.py` and `TextBattery_02_Analysis.R`, specified this day after every registered result was known, so that the same three analyses of the written explanations run in all five studies: the share of explanations carrying each of six word-list flags by label (and by modification level in Studies 2, 4 and 5), the words that set the label groups apart (Monroe, Colaresi and Quinn's log-odds ratio with an informative Dirichlet prior), and the link between each flag and the rating within a label, with within-person, word-count and polarity versions. Study 5 is run with and without its 24 repeat participants.
- Step 2 checks, before it fits the rating models, that its code reproduces Study 1's deposited distinctive-word tables, its seven Human-label models of rating on a flag and its shares of effort explanations naming detail, time, skill and prompting; all agreed to within 1.2e-14.
- The public copy leaves out `nlp/`, which labels Study 1's participants by their participant numbers and which step 1 writes again in seconds (`Analysis/_publish/make_github_copy.py`, `EXCLUDED_PATHS`).
