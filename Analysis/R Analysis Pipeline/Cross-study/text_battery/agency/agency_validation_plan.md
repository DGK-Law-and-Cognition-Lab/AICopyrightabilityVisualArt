# Validation plan for the agency rule

Written on 31 October 2026, after the two samples were drawn and before any explanation in either sample was coded by an annotator or read by the rule. Exploratory: no registration names the agency measure, and the memo `Docs/Preregistration/Study1_Text_Measures_Candidates.md`, section (vi), sets the procedure this plan follows. A rule that fails is reported as exploratory and unvalidated, not dropped.

## What is tested

The agency rule (`agency_rule.py`) reads one explanation at a time and records three yes-or-no flags, defined in `agency_codebook.md`:

- `person_maker`: the explanation presents a person as having made or changed the work;
- `machine_maker`: it presents an AI or other machine as having made or changed the work;
- `agentless_making`: it describes the work, or a change to it, being made or changed without saying who or what did it.

The pattern form printed in the memo is scored on the same items, as the memo asks.

## The samples

Drawn by `AgencyValidation.py draw` from seed 20261031, from every analyzed explanation of the five studies (at least one letter, on a five-point item), less the 360 Study 1 explanations sampled for the rule's first development on 2 September 2026 (`samples/earlier_sample_rows.csv`). Stratified by study and label, with the label used only to stratify:

- development sample: 25 explanations per study and label, 250 in all (`samples/development_items.csv`, SHA-256 8378cb08a8ba6f3f9dfde225691a04c81b4224f99cec567c68d603e48394fdc5). The rule may be adjusted on these.
- validation sample: 40 per study and label, 400 in all (`samples/validation_items.csv`, SHA-256 32b014ddf3973ba4e3d9f39b22845540c34262586bca66effbe0965460ed07d7). The rule is run on these once, after it is frozen. No one reads these explanations before the test.

Each study and label counts equally in the samples, whatever its size in the data.

## The annotators and the reference code

Three model annotators code every item of both samples, each on its own and blind to the study, the label, the rating and the rule, with `agency_codebook.md` as their only instructions:

- OpenAI `gpt-5.5-2026-04-23` and Google `gemini-3.1-pro-preview`, called by `AgencyValidation.py annotate`, one explanation per request, every request and response kept in `annotations/cache_*.jsonl`;
- Claude (`claude-opus-5-5`), run as separate annotator sessions given only the codebook and the items file.

The reference code of each flag on each item is the majority of the three. Agreement among the annotators is reported as Fleiss' kappa and mean pairwise agreement for each flag.

## Pass marks

Fixed now, from the memo, for each flag separately, on the 400 validation items:

- agreement of the rule with the reference code of at least 85 percent; and
- recall of at least 75 percent for each class: of the items the reference codes yes, the rule codes at least 75 percent yes, and of the items the reference codes no, the rule codes at least 75 percent no.

A flag that meets both marks is reported as validated on this sample; a flag that misses either is reported as exploratory and unvalidated, with its numbers. Precision, and every number by part (originals, Studies 1 and 3 of the pipeline; second works, Studies 2, 4 and 5), are reported as description, not as pass marks.

## Revision of the codebook, 31 October 2026

The first version of the codebook (`annotations/codebook_v1/agency_codebook_v1.md`, SHA-256 of its text beginning cee653c4e95f) left two boundaries open, and the development codes of the first annotator showed both: whether "the colors changed", a verb whose subject is the thing that changed, is an act with no doer stated, as "the colors were changed" is; and whether a thing can be the doer ("this created a new style"). The development phase is where the memo asks for the boundary between "agentless" and "not about the making" to be redrawn, so the codebook was revised before any reference code existed. Version 2 (`agency_codebook.md`, SHA-256 of its text beginning b0c14a3bedc8) closes the list of verbs, counts a change described by a passive, a participle, an infinitive or a gerund, and not one described by a verb whose subject is a thing, and says that a thing is never a doer. Every code made under version 1, by any annotator, is kept in `annotations/codebook_v1/` and not used: the three annotators coded both samples again under version 2. No validation code made under version 1 was read; the only figures seen were one annotator's counts of yes codes in that sample.

## The order of work

1. The three annotators code the development sample. The rule is adjusted on the development sample only, against the majority code.
2. The rule is frozen: its SHA-256 checksum, and that of the spaCy model it loads, are written to `agency_freeze.md` before the rule reads any validation item.
3. The three annotators code the validation sample. Their codes may be collected before the freeze, since they never see the rule, but no validation code or text is read before it.
4. The frozen rule is run once on the validation sample and scored against these marks. Nothing in the rule changes afterwards.
