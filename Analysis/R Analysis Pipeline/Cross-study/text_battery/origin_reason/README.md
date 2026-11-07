# Origin as reason

**This analysis is exploratory.** It was specified on 6 November 2026, after every registered result was known, and approved by the lead author the same day (`origin_reason_plan.md`). It changes no registered verdict.

## What it asks

A word list records whether an explanation *mentions* prompting or a machine. That is a topic, not a stance: "although it was made by AI, the idea is clever" mentions AI and gives the idea as the reason for the rating. This measure asks a question no word list can answer: did the explanation give **how the work was made** as a **reason** for the rating? "How it was made" covers making by AI, by prompting or by a machine, and also making by hand. The full definition, with examples, is `origin_reason_codebook.md`, which is also the instruction the annotators read.

## How it was built and tested

The rule (`origin_reason_rule.py`) splits each explanation into sentences with spaCy and reads each sentence with fixed patterns (regular expressions); it does not use a full grammatical parse. It finds the explanation's mentions of how a work was made: the shared word list `says_prompt`, plus phrases of making by hand. (The plan, `origin_reason_plan.md`, expected a parse of each sentence's grammar; the rule as built uses sentence splits and patterns instead.) It drops a mention that sits in a concessive clause or only names the original. It counts the rest as a reason when the sentence ties them to a judgment of creativity, effort or change, or when they are the substance of a short explanation.

It was tested like the agency rule (`../agency/`):

1. `python3 OriginReason.py draw` drew two disjoint samples of analyzed explanations from all five studies: a development sample of 250 and a validation sample of 400. Both were stratified by Part, label and whether `says_prompt` fires, so that the rare yes cases are well represented. The item files hold only an item number and the text.
2. Three model annotators coded each sample from the codebook alone, each item on its own and blind to the study, the label, the rating and the rule:
   - OpenAI's `gpt-5.5-2026-04-23` and Google's `gemini-3.1-pro-preview`, through `OriginReason.py annotate`, with every request cached in `annotations/`;
   - Claude, `claude-opus-5-5`, in separate sessions given only the codebook and the items.

   The majority of the three is the reference.
3. The rule was adjusted on the development sample only, then frozen (`origin_reason_freeze.md` records its checksum).
4. `python3 OriginReason.py score validation` scored it once on the validation sample. The pass marks were fixed beforehand: agreement with the reference on at least 85% of items, and recall of at least 75% of the reference's yes items and of its no items.

The rule also codes a direction: lowers, raises or unclear. Direction is not part of the pass marks; its agreement with the reference is reported beside the scores.

## What the test found (6 November 2026)

The rule passed: on the 400 validation items it agreed with the reference on 86.3%, and its recall was 92.5% for yes and 80.8% for no. The three annotators agreed with one another at a kappa of 0.91.

Scored by Part from the same codes (`tables/origin_reason_validation_by_part.csv`; nothing is rescored), the rule met the marks for originals (agreement 90.5%, recall 90.3% for yes and 90.8% for no) but not for secondary works (agreement 82.0%, recall 74.0% for no). For secondary works it calls too many mentions reasons: only 68.0% of the items it called yes were yes for the reference. The plan says a measure that fails is reported as failed and not used.

The rule is therefore used for originals only: `OriginReason_Analysis.R` reports shares and links only in a Part where the rule met the marks.

For originals, a mention of prompting or a machine was nearly always given as the reason: the reference judged 93.3% of the sampled mentions to be reasons, and the rule 90.8%.

Two notes on the scores. They are computed on the stratified sample, in which mentions are over-represented (240 of 400 items, against about 5% of all explanations); weighted back to all explanations, the overall scores are higher (agreement about 98%). And 13 short validation texts (median 3 words) repeat a development text word for word, though no explanation is in both samples; leaving them out changes the agreement from 86.3% to 86.6%.

## How to run it

From this folder, with Python 3.12, spaCy 3.7.4 and `en_core_web_sm` 3.7.1:

```sh
python3 OriginReason.py score validation   # rescore from the saved annotations; sends nothing
python3 OriginReason.py apply              # code every explanation with the frozen rule (about 5 minutes)
Rscript OriginReason_Analysis.R            # shares by label and Part, and links to the rating
```

`annotate` replays the cached responses without any key. A new request, which happens only if a text or the codebook changes, needs `OPENAI_API_KEY_AICOPYRIGHT` and `GEMINI_API_KEY_AICOPYRIGHT`. `draw` and `freeze` refuse to run again, so the samples and the freeze stay as recorded.

## The checks

`score validation` and `apply` stop unless the rule and the codebook have the checksums `origin_reason_freeze.md` records, the shared word-list module `shared/python/study_text.py` (which supplies `says_prompt`) has the checksum it had at the freeze, and spaCy and `en_core_web_sm` are 3.7.4 and 3.7.1. The validation sample is scored once: a later `score validation` must reproduce the saved scores exactly, or it stops. `apply` writes `tables/origin_reason_apply_record.csv` with the checksum of the codes it wrote, and `OriginReason_Analysis.R` stops unless the codes match it and unless every row joins the right participant, question and work.

## The analysis

For each study of a Part where the rule is used:

- the share of explanations that give origin as a reason, under each label, with the AI-minus-Human difference and the AI-to-Human ratio, all with 95% intervals from 2,000 resamples of participants within each label;
- within one label, the rating that comes with such an explanation against one without it, from the text battery's main rating-link model: rating ~ the study's registered terms (sum-to-zero contrasts) + the flag under each label + (1 | participant) + (1 | artwork), REML, bobyqa, Satterthwaite tests. A link is reported only where the flag appears in at least 20 explanations from at least 10 participants under that label, and Holm's correction runs over the reported links of each study.

## What it writes

- `samples/`: the items (number and text) and, kept apart, their keys (study, row, label, question, Part, stratum).
- `annotations/`: each annotator's codes and the API caches.
- `tables/`:
  - `origin_reason_<sample>_scores.csv`: the rule against the reference;
  - `origin_reason_<sample>_codes.csv`: each item's reference and rule codes;
  - `origin_reason_apply_record.csv`: what `apply` wrote, with checksums and versions;
  - from the R step, `origin_reason_validation_by_part.csv` (the validation scores in each Part, and whether the rule is used there), `origin_reason_shares.csv`, `origin_reason_rating_links.csv` and the run record `origin_reason_analysis_run_inputs.csv`.
- `nlp/origin_reason_flags.csv`: the rule's code for every explanation. It is left out of the public copy because Study 1 labels participants by their participant numbers.
