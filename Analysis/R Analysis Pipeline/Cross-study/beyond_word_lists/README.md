# Beyond the word lists: one notebook and one R Markdown file

These two files run every cross-study analysis of the written explanations. They are a convenience: each step is a script in its own folder, and these files call those scripts exactly as the pipeline does, then show the results.

| File | What it runs |
|---|---|
| `BeyondWordLists.ipynb` | The Python steps: the text battery's measures and the agency rule's scores (`../text_battery/`), image grounding with CLIP (`../image_grounding/`), the label from meaning (`../label_from_meaning/`), the origin-as-reason rule (`../text_battery/origin_reason/`), and the typical explanations the paper quotes (`../typical_explanations/`). |
| `BeyondWordLists.Rmd` | The R steps for the same analyses, with a short table of results after each. |

## How to run them

1. Run each study's own pipeline first (its README gives the order).
2. Open `BeyondWordLists.ipynb` in Jupyter with the `python312` kernel and run all cells. A full test run on 6 November 2026 took 46 minutes on a 12-core Mac, with every results table identical to the one before: 12 for the text battery, 20 for image grounding, 12 for the label from meaning with its embeddings cached (its null runs use all but two cores; the first run also computes the embeddings of three models, about 45 minutes more), 2 for the origin-as-reason rule and under 1 for the typical explanations.
3. Knit `BeyondWordLists.Rmd` from this folder, in RStudio or with `Rscript -e 'rmarkdown::render("BeyondWordLists.Rmd")'`. This takes about two minutes.

Nothing is downloaded. The models are read from the local Hugging Face cache, and each folder's README gives the one-time command that fetches them. The origin-as-reason step rescores the saved annotations and sends nothing.

## What the analyses ask

All of them are exploratory: they were specified after every registered result was known, and none changes a registered verdict.

- **Word lists** (text battery). How often explanations mention prompting or a machine, visible detail, time or skill, under each label.
- **Image grounding.** How closely each explanation describes its own picture, using CLIP, a network trained to match pictures with captions. No word list is used.
- **Label from meaning.** Whether the label can be predicted from what people meant, over and above their rating and explanation length, using sentence embeddings. No word list is used.
- **Origin as reason.** Whether an explanation gives how the work was made as the reason for its rating. A fixed rule decides this; it was validated once against three model annotators on a fresh sample, and it is used for originals only, the Part where it met the pass marks.
- **Typical explanations.** For quoting: the explanation of each group whose meaning lies closest to the group's average, chosen by a fixed rule so that the authors do not choose.
