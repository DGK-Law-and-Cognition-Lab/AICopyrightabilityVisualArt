# The label from meaning

**This analysis is exploratory.** It was specified on 6 November 2026, after every registered result was known, at the lead author's request for a test of the explanations that uses no word list. It changes no registered verdict.

## What it asks

Each study's registration ran a recoverability check: how well the label can be predicted from the words of the explanations, over and above the rating. That check counts words, so "made by AI" and "a machine did it" share nothing. This analysis asks the same question of what the explanations *meant*.

A sentence-embedding model turns each explanation into a list of numbers, called an embedding, such that two explanations that say the same thing in different words lie close together. No word list is used.

## How it works

The label is fixed for each participant, so the unit is the participant. For each study and question, each participant is described by:

- the average embedding of their explanations;
- their average rating;
- their average explanation length (the log of the word count).

Three logistic regressions predict the label:

1. rating and length only;
2. meaning, rating and length, where the embedding enters as its first 20 principal components, computed on the training participants of each fold only;
3. meaning only.

Each participant's prediction comes from a model fitted without them: 10 folds, stratified by label, repeated 5 times, with each participant's five predictions averaged. The result is the AUC, the chance that a randomly chosen AI-label participant scores above a randomly chosen Human-label one, so 0.5 is chance and 1 is perfect. Its 95% interval comes from 2,000 resamples of participants. The interval holds each participant's prediction fixed, so it leaves out the variation that comes from fitting and is somewhat too narrow.

The question is the **gain**: how much the AUC rises when meaning is added to rating and length. Its test keeps whatever meaning shares with the rating and length and removes only what it might add (the Freedman–Lane method):

- each embedding dimension is regressed on rating and length across participants (the label is not used);
- in each of 100 null runs, the residuals, the part of each dimension the regression leaves unexplained, are shuffled across participants and added back to the fitted values;
- the null runs use the same folds and repeats as the real fit.

The gain counts as shown when it exceeds the 95th percentile of the null gains.

A first version, run earlier on 6 November 2026, shuffled the labels instead. That also breaks the link between label and rating, so it tested whether the text predicts the label at all, not whether meaning adds to the rating, and its null was far too wide. A code review caught it the same day, and the table was replaced.

## Two checks

- **Without mentions.** The same analysis, with the primary model, on the explanations that do not mention prompting or a machine (the shared word list `says_prompt`). An explanation that restates the label ("it's AI") could otherwise carry the prediction by itself.
- **Other models.** The same analysis of all explanations with two newer sentence-embedding models that score higher on standard benchmarks. `all-mpnet-base-v2` (2021) stays the primary model, because the registered text checks used it; choosing a model after seeing the results would be a choice made after the fact.

| Model | Role | Revision | Weights | Licence |
|---|---|---|---|---|
| `sentence-transformers/all-mpnet-base-v2` | primary | `e8c3b32` | 0.42 GB | Apache-2.0 |
| `BAAI/bge-large-en-v1.5` | check | `d4aa6901` | 1.34 GB | MIT |
| `mixedbread-ai/mxbai-embed-large-v1` | check | `b33106f5` | 0.67 GB | Apache-2.0 |

## How to run it

From this folder, with Python 3.12 and the packages recorded in `tables/label_from_meaning_environment.csv`:

```sh
python3 LabelFromMeaning.py
```

The models are read from the local Hugging Face cache only. `Study 1/README.md` gives the one-time command that fetches `all-mpnet-base-v2`. The two check models are fetched once, at their pinned revisions and with only the files the model needs, by:

```sh
python3 -c "from huggingface_hub import snapshot_download as s; [s(r, revision=v, allow_patterns=['*.json', 'model.safetensors', 'vocab.txt', '1_Pooling/*'], ignore_patterns=['onnx/*', 'openvino/*']) for r, v in [('BAAI/bge-large-en-v1.5', 'd4aa6901d3a41ba39fb536a557fa166f842b0e09'), ('mixedbread-ai/mxbai-embed-large-v1', 'b33106f585b9ce46904ad7443a3b52b7a63e231c')]]"
```

A full run on a 12-core Mac takes over an hour, most of it the null runs; the first run also computes each model's embeddings of all 41,000 explanations. Each process uses one numerical thread, and the null runs are spread over all but two cores; the results do not depend on the number of cores. The script stops unless every long data file has the checksum its study's registered run recorded.

## What it found (run of 6 November 2026, 56 minutes)

- **Originals, effort.** Meaning alone told the label groups apart about as well as rating and length (AUC 0.80 against 0.77 in paper Study 1; 0.74 against 0.68 in Study 2), and added to them slightly (gains 0.02 and 0.06, above their nulls).
- **Originals, creativity.** Meaning alone gave 0.61 in both studies and added nothing.
- **Without mentions.** Without the explanations that mention prompting or a machine, meaning still told the labels apart on effort about as well as the rating (0.73 and 0.66) but no longer added to it (gains 0.00 and −0.06). On Study 1's creativity it fell to chance (0.50). The gains came from the mentions.
- **Secondary works.** Meaning alone gave 0.46 to 0.64; the gain cleared its null only for Study 5's creativity explanations (0.07), and not without the mentions.
- **Other models.** bge-large-en-v1.5 and mxbai-embed-large-v1 read slightly more (Study 1 effort, meaning alone: 0.81 and 0.83) and gave the same conclusions. The effort gains in Studies 1 and 2 and Study 5's creativity gain cleared their null with all three models. With the two newer models, Study 4's essence-change gain cleared it too; with the main model it fell just short (0.06 against 0.07).

## What it writes

- `tables/label_from_meaning.csv`: for each model, set of explanations, study and question, the three AUCs and the gain, with 95% intervals, and for the gain the null's mean, its 95th percentile and a permutation p-value.
- `tables/label_from_meaning_environment.csv` and `tables/label_from_meaning_run_manifest.csv`: the run records.
- `nlp/`: each model's embeddings of every explanation, cached so that later runs skip that step, keyed on the model, its revision, the library version and the exact texts. It is left out of the public copy because Study 1 labels participants by their participant numbers.

No table holds a participant code.
