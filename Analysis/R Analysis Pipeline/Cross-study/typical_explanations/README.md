# Typical explanations

**This step is descriptive.** It was specified on 6 November 2026, after every registered result was known, at the lead author's request to quote participants' written explanations in the paper without the authors choosing which ones. It tests nothing and changes no registered verdict.

## What it does

For each group, it picks the explanation whose meaning is closest to the group's average, by a rule fixed before any explanation was read:

- **Groups.** For each Part, question and label:
  - originals (paper Studies 1 and 2 pooled), effort and creativity;
  - secondary works (paper Studies 3 to 5 pooled), creativity, at the Slight and Dramatic edits only. At None the picture is the original shown again, and explanations mostly say that nothing changed.
- **Typical.** Each explanation is placed by its sentence embedding (`all-mpnet-base-v2`, the pipeline's model, read from the cache of `../label_from_meaning/`), so that explanations that mean the same thing lie close together. The group's center is the average of its participants' average embeddings, so each participant counts once. An explanation is the more typical the closer it lies to that center (cosine similarity).
- **Length.** Only explanations at least as long as the group's median, in words, are eligible, so a quote is not a one-word reply.
- **One per person.** The two most typical eligible explanations of a group come from two different participants.

The explanations are those every other analysis uses. They are quoted exactly as written.

## How to run it

From this folder, after `../label_from_meaning/LabelFromMeaning.py` has cached the embeddings:

```sh
python3 TypicalExplanations.py
```

It takes about a minute.

## What it writes

- `tables/typical_explanations.csv`: for each group, the two chosen explanations, word for word, with the paper's study number, the edit level, the rating, the length, the similarity to the group's center and the group's size. No participant code.
- `tables/typical_explanations_run_manifest.csv`: the checksums of the table, the script, the label-from-meaning script it reads through, and the five long data files.

The paper quotes the first explanation of four groups in the main text, and all twelve in a Supplementary table.
