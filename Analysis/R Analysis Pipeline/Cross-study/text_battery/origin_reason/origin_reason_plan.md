# Origin as reason: definition and validation plan (approved 6 November 2026)

**Status: the lead author approved this definition and plan on 6 November 2026, with the direction code and the sending of the sampled explanations (text only) to the two APIs.** The annotators' instructions are `origin_reason_codebook.md`. The steps of the plan run in order, and the rule is frozen before it reads the validation sample.

## Why

The word lists record whether an explanation mentions prompting or a machine. A mention is a topic, not a stance: "although it was made by AI, the idea is clever" mentions AI and gives the idea as the reason. The question this measure answers, which no word list can, is whether people *gave the way the work was made as a reason for their rating*. On originals, the account in the paper predicts that AI-label explanations often give the making as the reason. On secondary works it predicts that they rarely give the original's origin as the reason for rating the edit.

## The definition

An explanation **gives origin as a reason** when it gives how the work it rates was made, or how the original it was made from was made, as a reason for the rating. "How it was made" means made by AI, by prompting or by a machine or program, or not made by AI (for example "he drew it himself"). The reason can lower the rating or raise it.

It counts when:

1. a connective ties the making to the rating ("because", "since", "so", "as", "which is why", "due to", "given that", "if ... then"), as in *"Because Alex inputted the prompts, he contributed a little bit of creativity"* and *"If it is AI, then the effort is none"*;
2. the making is the whole of the explanation, so it is the only reason given, as in *"The art is clearly AI."* and *"looks like a generated ai picture"*;
3. a general claim about how such works are made is applied to this one, as in *"AI art requires little to no effort."*;
4. the making is tied to the rating by an evaluation, as in *"You could clearly tell this is AI, which made me dislike it in terms of effort"*;
5. on a secondary work, the original's AI making is the reason, as in *"The second work is copied from the one produced by AI. No creativity went into the process"*.

It does not count when:

1. the making is conceded and another reason carries the rating: *"Although it was made by AI, the idea is clever"*;
2. the making only names or describes the original while the change is the reason: *"completely different from the AI's cartoonish style"*, *"it added a level of distinctness to the original, AI-generated work"*;
3. the explanation is about the editing tools without saying the work was machine-made: *"he used Photoshop to adjust the colors"*;
4. the making is mentioned only as a guess about something other than the rated work.

Each explanation gets one code, yes or no, and, when yes, a direction: lowers, raises or unclear.

## How it would be measured

A grammar-based rule, like the agency rule (`../agency/`), written with spaCy's dependency parse:

- a mention of the making, from the word list `says_prompt` together with the agency rule's machine-maker reading;
- a causal or conditional connective that links that mention to an evaluation of creativity, effort, transformativeness or change;
- concessive frames ("although", "even though", "despite") that block the link;
- the whole-explanation case (1 and 2 under "It counts when").

It reads only the text, never the label or the rating.

## Validation, as for the agency rule

1. **Development:** 250 explanations drawn from all five studies. The draw is stratified by Part, by label, and by whether `says_prompt` fires, so that the rare yes cases are well represented.
2. **Annotators:** three model annotators code each item from this codebook alone, each item on its own, blind to the study, label, rating and rule. They are OpenAI's and Google's current models through their APIs, with every request cached, and Claude in separate sessions. The majority of the three is the reference. The rule is adjusted on the development sample only.
3. **Freeze:** the rule's code is fixed by a checksum before it reads anything else.
4. **Validation:** a fresh sample of 400, drawn the same way, is coded by the three annotators and scored once. The pass marks, fixed now, are agreement with the reference on at least 85% of items, and recall of at least 75% of the reference's yes items and of its no items.
5. **If it passes**, it runs unchanged in every study. It reports:
   - the share of explanations giving origin as a reason, by label and Part;
   - the AI-to-Human ratio;
   - the link to the rating within each label.
   
   **If it fails**, it is reported as failed and not used, as the agency rule's person flag was.

Cost: about 1,300 annotation requests to two paid APIs, a few dollars. The explanations sent carry no participant code.

## Decisions

All three were settled on 6 November 2026: the definition as written (an explanation consisting only of "it's AI" gives origin as the reason), the direction code kept, and the sampled explanations sent, text only, to the two APIs.
