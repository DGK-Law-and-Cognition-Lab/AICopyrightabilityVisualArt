# The agency measure: who an explanation says made or changed the work

**Exploratory.** Specified on 31 October 2026, after every registered result was known. No registration names it. The procedure follows the memo `Docs/Preregistration/Study1_Text_Measures_Candidates.md`, section (vi), and the plan in `agency_validation_plan.md`, written before any explanation in either sample was coded.

## What it measures

The word lists of each study record what an explanation mentions. The agency measure records who the explanation says did the making or changing. A rule (`agency_rule.py`) reads each explanation's grammar with spaCy's English pipeline and, for every verb of making or changing the work, finds its doer. It records three yes-or-no flags, defined in `agency_codebook.md`:

- `person_maker`: a person (Alex, the artist, a human) made or changed the work;
- `machine_maker`: an AI or other machine made or changed it, including "AI-generated" and "made with AI";
- `agentless_making`: the work or a change to it was made with no doer stated ("it was edited slightly").

A doer the explanation denies ("Alex didn't draw this") sets no flag, and neither does a thing as subject ("the colors changed"), which describes a result rather than an act. No person and no language model codes the explanations that the analyses use: the rule codes all of them, the same way. Language models were used only to test the rule, as below.

## How it was tested

1. Two samples were drawn on 31 October 2026 from the five studies, when Study 5's analyzed sample was still its registered 223, 25 and 40 explanations per study and label, without the 360 Study 1 explanations used in the rule's first development in September 2026: a development sample of 250 and a validation sample of 400 (`samples/`). The label was used only to stratify; no annotator saw it.
2. Three model annotators coded every item of both samples from the codebook alone, each item on its own and blind to the study, the label, the rating and the rule: OpenAI's `gpt-5.5-2026-04-23` and Google's `gemini-3.1-pro-preview` through their APIs (`AgencyValidation.py annotate`, every request and response kept in `annotations/cache_*.jsonl`), and Claude (`claude-opus-5-5`) in separate sessions given only the codebook and the items. The reference code of each flag on each item is the majority of the three.
3. The codebook was revised once, before any reference code existed, when the first development codes showed two open boundaries (`agency_validation_plan.md`, "Revision of the codebook"). Every code made under the first version is kept in `annotations/codebook_v1/` and unused.
4. The rule was adjusted on the development sample only, then frozen: `agency_freeze.md` records its SHA-256 checksum, the codebook's, and the spaCy model's version, written before the rule read any validation item. `AgencyValidation.py score validation` and `../TextBattery_01_Measure.py` both stop unless the rule is the frozen one.
5. The frozen rule was run once on the validation sample and scored against the pass marks fixed in the plan: for each flag, agreement with the reference of at least 85 percent, and recall of at least 75 percent of the items of each class.

## The result

On the 400 validation explanations (`tables/agency_validation_scores.csv`, with 95 percent Wilson intervals):

| Flag | Annotators' Fleiss kappa | Reference yes | Agreement | Recall of yes | Recall of no | Verdict |
|---|---|---|---|---|---|---|
| `machine_maker` | 0.88 | 14 | 0.993 | 0.86 (12 of 14) | 0.997 | validated |
| `person_maker` | 0.89 | 12 | 0.978 | 0.50 (6 of 12) | 0.992 | not validated |
| `agentless_making` | 0.96 | 50 | 0.922 | 0.68 (34 of 50) | 0.957 | not validated |

The rule's scores on the development sample were near perfect (`agency_freeze.md`); the drop on the validation sample is the reason the plan held a separate sample back. The memo's pattern form, scored on the same items, found 2 of the 12 person items, 11 of the 14 machine items and 5 of the 50 agentless items.

Only `machine_maker` is reported as a validated measure. The other two flags are reported, with these numbers, as exploratory and unvalidated, and the battery's tables say so in their column `flag_source`. Every yes count is small, so each recall is uncertain: the interval for `machine_maker` runs from 0.60 to 0.96.

## The files

| File | What it is |
|---|---|
| `agency_codebook.md` | The coding instructions, version 2, which every reference code follows. |
| `agency_validation_plan.md` | The plan, with the pass marks, written before any coding, and the record of the codebook's revision. |
| `agency_rule.py` | The rule. Frozen; see `agency_freeze.md`. |
| `agency_pattern.py` | The pattern form printed in the memo, scored beside the rule as the memo asks. |
| `AgencyValidation.py` | Draws the samples (`draw`), has the two API annotators code them (`annotate`), freezes the rule (`freeze`) and scores it (`score`). |
| `agency_freeze.md` | The checksums that fix the rule, and its development scores. |
| `samples/` | Each sample's items (an item number and the text) and its key (study, row of the long data file, label and question; never shown to an annotator), and the rows left out because they were used in September. |
| `annotations/` | Each annotator's codes for each sample, the API caches, and the first version's codes in `codebook_v1/`. |
| `tables/` | The scores and the item-level codes (reference and rule) of each sample. |

## How to run it

The samples, the annotations and the freeze are records of what was done once; rerunning them is not needed to reproduce the analyses. `python3 AgencyValidation.py score validation` rescores the frozen rule against the saved codes in a few seconds. `annotate` replays the cached responses and sends nothing unless a text or the codebook has changed; a new request needs the environment variables `OPENAI_API_KEY_AICOPYRIGHT` and `GEMINI_API_KEY_AICOPYRIGHT`, and, since the hosted models change, may not return the same codes. The Claude codes were written by separate sessions, not by this script.

The rule needs spaCy 3.7.4 and its model `en_core_web_sm` 3.7.1, which `agency_freeze.md` records and `../TextBattery_01_Measure.py` writes into its environment table. Install the model with `python3 -m spacy download en_core_web_sm-3.7.1 --direct`.
