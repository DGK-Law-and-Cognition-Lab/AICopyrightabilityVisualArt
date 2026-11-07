# Image grounding: how closely explanations describe their picture

**This analysis is exploratory.** It was specified on 6 November 2026, after every registered result was known, at the lead author's request for a measure of the written explanations that uses no word list. It changes no registered verdict.

## What it asks

CLIP is a network that OpenAI trained to match pictures with their captions. It turns a picture and a piece of text into lists of numbers, called embeddings, such that a caption lies close to the picture it describes. Here each written explanation is treated as a caption of the picture it explains.

- **Grounding.** An explanation's CLIP similarity to its own picture, minus its average similarity to the other nine artworks at the same edit level. It is above zero when the text describes its own picture more than pictures in general.
- **Edit pull** (secondary works only). The similarity to the edited picture shown, minus the similarity to that artwork's original.
- **Hit.** Whether the explanation's own picture is the one, of the ten artworks at that level, that CLIP places closest to it. Chance is 1 in 10.

The analysis then asks three questions:

1. **Validity.** Does CLIP find each explanation's own picture more often than chance?
2. **Originals** (paper Studies 1 and 2). Is grounding lower under the AI label, meaning that AI-label explanations describe the picture less?
3. **Secondary works** (paper Studies 3 to 5, Slight and Dramatic). Is grounding lower under the AI label?

## The files

| File | What it does |
|---|---|
| `ImageGrounding_01_Measure.py` | Blind step. It reads the participant, the picture, the question and the text of each explanation from each study's long data file, and never the label, the conditions or the rating. It scores every explanation with CLIP and writes `nlp/image_grounding_scores.csv`. |
| `ImageGrounding_02_Analysis.R` | Joins the label, the conditions and the rating, and writes the tables. |
| `nlp/` | The per-explanation scores. They are left out of the public copy because Study 1 labels participants by their participant numbers. Step 1 writes them again in about 8 minutes. |
| `tables/` | Every table the two steps write. |

## How to run it

From this folder:

```sh
python3 ImageGrounding_01_Measure.py
Rscript ImageGrounding_02_Analysis.R
```

Step 1 needs:

- Python 3.12 with torch, transformers, numpy, pandas and Pillow, at the versions recorded in `tables/image_grounding_measure_environment.csv`;
- CLIP, `openai/clip-vit-base-patch32` at the revision `../image_check/` pins (`3d74acf...`), in the local Hugging Face cache. `../image_check/README.md` gives the command that fetches it.

Pictures are fed to CLIP as in the image check's primary variant: the whole image resized to 224 by 224 pixels, without cropping. Text longer than CLIP's 77 tokens is cut at 77.

Step 2 needs R 4.5 with readr, dplyr, tidyr, tibble, lme4, lmerTest, emmeans and digest.

## What it checks

Step 1 stops unless:

- every long data file has the checksum its study's registered run recorded;
- every picture has the checksum of `../image_check/stimuli/stimuli_manifest.csv`.

Step 2 stops unless the scores file is the one step 1 recorded.

## The models

For each study and question: grounding (in standard deviations of that study and question) ~ the study's registered terms + log length + (1 | participant) + (1 | artwork).

- The registered terms are the label with stimulus type (paper Study 1), with stated time (Study 2), with edit level and image kind (Study 3), with edit level and stated source time (Study 4), and with edit level and stated editing time, plus image kind (Study 5). Stimulus type and image kind use sum-to-zero contrasts, so the label effect is averaged over them.
- Length is the log of the number of tokens CLIP read. CLIP reads at most 77, so 0.3% to 1.7% of explanations are cut at that length.
- The model is fitted again with the rating added, to check that a difference is not only a restatement of the rating.
- It is fitted again without mentions: only on the explanations that do not mention prompting or a machine (the shared word list `says_prompt`, read from each study's `nlp/studyN_text_measures.csv`). This checks whether a difference comes only from explanations that talk about the machine instead of the picture.
- Degrees of freedom are Satterthwaite's.
- Holm's correction runs over each study's label tests in the main version.

## What it found (run of 6 November 2026; registered terms and the without-mentions version added the same day)

- **Validity.** For originals, CLIP placed the explanation's own picture first in 42% (Study 1) and 38% (Study 2) of explanations, against 10% by chance. For secondary works it did so in 19% to 24% at Slight and Dramatic. At None it was at chance, since those explanations mostly say that nothing changed.
- **Edit pull fails.** Its mean is about zero at both Slight and Dramatic, so CLIP cannot tell from the text whether an explanation describes the edited picture or its original. It is reported and not used.
- **Originals.**
  - In Study 1, effort explanations under the AI label described the picture less: by 0.30 standard deviations, with a 95% interval of 0.14 to 0.47 (Holm p < .001).
  - The difference held with the rating added (0.22).
  - Without the explanations that mention prompting or a machine, it shrank to 0.18 (95% interval −0.38 to 0.01, uncorrected p = .058): part of the difference comes from explanations that write about the machine instead of the picture.
  - Creativity in Study 1, and both questions in Study 2 (85 participants), leaned the same way but not significantly.
- **Secondary works.** In none of Studies 3 to 5 did grounding differ by label after correction.

## What it writes

In `tables/`:

- `image_grounding_validity.csv`: hit rate and mean edit pull by study and level, with participant-resampled 95% intervals.
- `image_grounding_label_effects.csv`: the AI minus Human difference in grounding, by study, question and level, in the main version, with the rating added, and without mentions.
- `image_grounding_samples.csv`: explanations by study and label.
- The run records `image_grounding_measure_environment.csv`, `image_grounding_measure_run_manifest.csv` and `image_grounding_analysis_sessionInfo.txt`.

No table holds a participant code.
