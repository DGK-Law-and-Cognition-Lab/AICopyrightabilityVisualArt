# Explanation shift within a person

**This analysis is exploratory.** It was specified on 9 October 2026, after the registered results of all five studies were known, and no registration names it. Nothing in it tests a registered hypothesis. The two analysis files say so at their top. Every table in `tables/`, and the pairs file in `nlp/`, says so in its first column, `analysis`, and the figure says so in its caption.

## What it asks

In Studies 2, 4 and 5 each participant explained the same source artwork at three levels of modification, None, Slight and Dramatic, once for each of the three rating questions (transformativeness, essence change and creativity). The analysis asks whether the label on the source changes how far those explanations move as the work changes.

If an AI source taints the second work, participants told that the source was made by prompting an AI system should keep writing about where the source came from however much Alex changed it, so their explanations should move less from None to Dramatic than those of participants told that Alex made the source with design and sketching tools. If participants judge what Alex added, the explanations of the two arms should move about as far.

Two quantities answer it.

1. **The shift.** For one participant, source image and question, the distance between the explanation at None and the explanation at Dramatic, minus a stranger baseline: the mean distance from the participant's None explanation to other participants' Dramatic explanations of the same image and question in the same study. Two people writing about one picture share words because the picture supplies them, and the baseline removes that. Distance is measured in two ways. The embedding distance is 1 minus the cosine similarity of the two explanations' lists of 768 numbers from the sentence-embedding model all-mpnet-base-v2, a network trained beforehand on other text that turns a sentence into numbers so that sentences with similar meanings get similar lists; the cosine similarity is 1 when two lists point the same way and 0 when they are unrelated. The word distance is 1 minus the Jaccard overlap of the two explanations' content words, the number of words both use divided by the number either uses, where a content word is a word left once the fixed list of function words such as *the* and *of* is removed. Under taint, AI minus Human in the shift is negative. Creativity is the primary question; transformativeness and essence change are secondary.
2. **Talk of origin by level.** From each study's deposited text measures, the share of explanations that mention prompting or a machine, and the share that state a machine made the work, at each level and in each arm. Under taint, origin talk in the AI arm stays up at Dramatic. If raters turn to what Alex added, it falls as the work changes.

No person and no language model labels, codes or judges any response. The embedding model turns each response into numbers and does nothing else, and the step that runs it never sees the label or the rating.

## The files

| File | What it does |
|---|---|
| `ExplanationShift_01_Measure.ipynb` | A Jupyter notebook (a file of Python cells run in order). It reads six columns of each study's long data file (the participant, the source image, the modification level, the rating question, the item name and the text; the item name is read only to check the other columns) and computes, for every complete set of three explanations and every pair of levels, the embedding distance, the word distance and the stranger baseline of each. It never reads the label, the time condition or the rating. |
| `ExplanationShift_02_Analysis.Rmd` | An R Markdown file (R code and text that is knitted, that is, run from top to bottom into an HTML report). It joins the source label from each study's long data file, fits the model of the shift, runs its permutation null, computes the origin-talk shares with intervals from resampling participants, draws the figure, and records fit status and a run manifest. |
| `README.md` | This file. |
| `CHANGELOG.md` | The edit history of the two analysis files, which carry none themselves. |

The files use the shared helpers of the pipeline: `../../shared/python/study_text.py` (the tokenizer, the function-word list, the embedding loader and the seed) and `../../shared/R/fit_status.R` and `../../shared/R/text_checks.R` (fit status, the run record and the parallel runner of the permutations).

## Run order

1. `ExplanationShift_01_Measure.ipynb`
2. `ExplanationShift_02_Analysis.Rmd`

The R file reads what the notebook writes, and it stops if the pairs file is not the one the notebook's manifest records, or if any study file is not the one its own study's manifest records.

## Where it runs

Both files run on a local machine. The notebook also runs in Google Colab, Google's service that runs a notebook on its own machines from a web browser. The R file runs locally.

### Locally

The notebook runs on the Jupyter kernel named `python312`, the entry that tells Jupyter which Python to start. From this folder:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=python312 ExplanationShift_01_Measure.ipynb
```

or open it in Jupyter and run every cell on that kernel. The embedding model is read from the local Hugging Face cache, the folder where these Python libraries keep downloaded models, and nothing is downloaded. `Study 1/README.md` gives the one command that fetches the model if it is missing. On a twelve-core Mac the notebook took about three minutes, two and a half of them to embed 29,296 distinct texts.

Then knit the R file. In RStudio, open `R Analysis Pipeline.Rproj`, open `ExplanationShift_02_Analysis.Rmd` and press Knit, or from the R console with this folder as the working folder:

```r
rmarkdown::render("ExplanationShift_02_Analysis.Rmd")
```

The report is written beside the `.Rmd` file. The knit took about fifteen seconds, because the 1,200 permutation refits run on up to eight processor cores.

### In Google Colab

1. In Google Drive, open this folder, right-click `ExplanationShift_01_Measure.ipynb`, and choose Open with, then Google Colaboratory.
2. Choose Runtime, then Run all. The first code cell asks for permission to mount Google Drive, that is, to attach it to the Colab machine so that its files are visible there.
3. The embedding cell installs the sentence-transformers library if Colab lacks it and downloads the model once into Colab's cache. If the Colab machine has a graphics card, the model runs on it, which changes the distances only in about the sixth decimal place; the environment table records the device.

The notebook writes its outputs into this folder on Google Drive, which syncs to the local copy. Knit the R file locally once the sync has finished.

## What each file writes

Paths are relative to this folder.

`ExplanationShift_01_Measure.ipynb`:

- `nlp/explanation_shift_pairs.csv`: one row per participant, source image, question and pair of levels (38,121 rows), with the columns `analysis` (the status of the analysis), `study`, `id`, `image`, `dimension`, `pair` (`None-Slight`, `Slight-Dramatic` or `None-Dramatic`), `emb_distance`, `emb_stranger`, `word_distance`, `word_stranger`, `words_a` and `words_b` (the number of distinct content words at the first and the second level). It carries no label and no rating. A word distance is empty where an explanation has no content word.
- `tables/explanation_shift_measure_environment.csv`: the software, the model, the device and the seed.
- `tables/explanation_shift_measure_run_manifest.csv`, written last: every input and output with its size and its SHA-256 checksum, a 64-character fingerprint of the file's exact bytes.

`ExplanationShift_02_Analysis.Rmd`:

- `tables/explanation_shift_input_check.csv`: each input beside the checksum its producing run recorded.
- `tables/explanation_shift_description.csv`: mean distances, baselines and shifts by study, arm, question and pair of levels.
- `tables/explanation_shift_models.csv`: AI minus Human in the None to Dramatic shift, for each question and kind of distance, pooled over the three studies with equal weight and within each study, with its 95 percent interval, its model p-value, its permutation p-value and the reading.
- `tables/explanation_shift_arm_means.csv`: the estimated mean shift of each arm, pooled and within each study.
- `tables/explanation_shift_origin_talk.csv`: the origin-talk shares by study, arm, level and question, the change from None to Dramatic in each arm, AI minus Human at each level and in the change, each with its interval.
- `figures/explanation_shift.pdf` and `figures/explanation_shift.png`: one greyscale figure. The top row shows the mean shift of each arm on creativity by study and pooled; the bottom rows show the origin-talk shares by level.
- `tables/explanation_shift_fit_log.csv`, `tables/explanation_shift_analysis_run_inputs.csv`, `tables/explanation_shift_analysis_sessionInfo.txt`, `tables/explanation_shift_analysis_package_versions.csv` and, written last, `tables/explanation_shift_analysis_run_manifest.csv`.
- `ExplanationShift_02_Analysis.html`, the knitted report.

Each run deletes its earlier manifest when it starts and writes the new one last, so a manifest on disk means the run reached its end.

The tables name the unchanged level `None`. pandas reads the text `None` as a missing value unless told otherwise, so a Python reader should pass `keep_default_na=False` to `pandas.read_csv`. R's `readr` reads it as text.

## How the code reads the specification

Where the specification leaves a choice open, the code takes these readings.

- **The six-point items.** Each study leaves its two six-point transformativeness items, `1NonFigure` at None and at Slight, out of its main models. Study 2's long data file does not hold them, and those of Studies 4 and 5 hold 140 and 274 rows of them. They are dropped in all three studies, so transformativeness of `1NonFigure` has no complete set of three.
- **Levels.** The column `modification` names the levels None, Slight and Dramatic. The item names, such as `1FigureMaxCreat`, call them `None`, `Min` and `Max`. On every row the notebook checks that the item name agrees with the row's image, level and question, with `Min` read as Slight and `Max` as Dramatic, so each pair joins one participant's explanations of one image and one question.
- **Complete sets.** Only a participant, image and question with an explanation at all three levels is measured: 6,794 sets in Study 2, 2,036 in Study 4 and 3,877 in Study 5, 12,707 in all. Seven Study 2 participants lack the trial at Slight for `1Figure`.
- **The stranger baseline.** For the pair of levels A and B, the mean distance from the participant's explanation at A to every other participant's explanation at B of the same image and question in the same study, whether or not that other participant has a complete set. It is the baseline of the registered word-overlap check in `shared/R/text_checks.R`, built here for each pair of levels.
- **Explanations with no content word.** An explanation such as *same* has no content word. As in the registered overlap check, it has no word distance and is no one's stranger on words. It keeps its embedding distance.
- **Content words.** The shared `tokenize()` with `FUNCTION_WORDS` removed. The task words, such as *creativity* and *artwork*, stay in, as in the overlap check.
- **The model.** `shift ~ source * study + words_c + (1 | study:id) + (1 | image)`, fitted with lmerTest by restricted maximum likelihood and the bobyqa optimizer, where `words_c` is the mean number of distinct content words of the two explanations, centred on its mean in the model's data. AI minus Human comes from the estimated marginal means, within each study and averaged over the three studies with equal weight, with Satterthwaite's degrees of freedom.
- **The permutation null.** The labels are shuffled among participants within each study 200 times from seed 20260421, the same shuffles serve all six models, and each refit gives the pooled and the three within-study differences. The p-value counts the observed data as one shuffle. The reading of each row rests on its 95 percent interval: negative and clear of zero is "as taint predicts", positive and clear of zero is "against", and an interval that includes zero shows no difference. No interval or p-value in the 24 rows of the model table or in the origin-talk table is adjusted for the number of comparisons, so about one row in twenty can fall clear of zero by chance alone.
- **Origin talk.** `says_prompt` true, and the machine-made reading `asserted`, from each study's `nlp/studyN_text_measures.csv`, joined one row to one row on the participant, the second work and the question. The shares are over the same complete sets as the shift, so each level holds the same people writing about the same images. Intervals come from 2,000 resamples of participants within each study and arm from seed 20260421, and pooled values are the mean of the three studies, computed within each resample.

## The environment

- Python 3.12 on the `python312` kernel, with pandas 2.2.2, NumPy 1.26.4, SciPy 1.13.0, scikit-learn 1.5.2, sentence-transformers 3.3.1 and PyTorch 2.5.1, recorded in `tables/explanation_shift_measure_environment.csv`.
- R 4.5.2 with readr 2.2.0, dplyr 1.2.1, tidyr 1.3.2, tibble 3.3.1, lme4 2.0-1, lmerTest 3.2-1, emmeans 2.0.3, ggplot2 4.0.3, patchwork 1.3.2, rmarkdown and knitr, recorded in `tables/explanation_shift_analysis_package_versions.csv`.

Paths are found from each file's own folder. The environment variable `EXPLANATION_SHIFT_DIR`, a named setting the shell passes to a program, names this folder instead, and `STUDY_SHARED_PYTHON` and `STUDY_SHARED_R` name the shared helpers. Printed paths are relative to the pipeline folder, so no output names a folder particular to one machine.

## What it does not do

Every explanation was written after its rating, so nothing here says what produced a rating. The analysis describes how far people's words moved once their numbers were chosen. Neither quantity was named before the registered results were known, and neither can confirm or overturn a registered result.
