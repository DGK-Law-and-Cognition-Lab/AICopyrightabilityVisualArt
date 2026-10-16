# Explanation shift changelog

The edit history of the files in this folder. The analysis files themselves carry none.

## 2026-10-09

Added the explanation-shift analysis. It is exploratory: it was specified on 9 October 2026, after the registered results of all five studies were known, and no registration names it.

- `ExplanationShift_01_Measure.ipynb`: reads five columns of the long data files of Studies 2, 4 and 5 (participant, source image, modification level, rating question, text), drops the six-point transformativeness items, finds every complete set of three explanations, and writes the embedding distance, the word distance and the stranger baseline of each for every pair of levels. It reads no label, time condition or rating. It runs locally on the `python312` kernel with the model read offline, and in Google Colab, where it mounts Google Drive and may download the model once.
- `ExplanationShift_02_Analysis.Rmd`: joins the source label, fits the model of the None to Dramatic shift on each question and kind of distance with its permutation null, computes the origin-talk shares by level and arm with intervals from resampling participants, draws the figure, and records fit status and a run manifest with `shared/R/fit_status.R`.
- `README.md` and this file.

Run on 9 October 2026, on the real labels.

- The notebook ran in place on the `python312` kernel, offline, in about three minutes. It read 38,605 explanations after dropping 0, 140 and 274 six-point rows in Studies 2, 4 and 5, found 12,707 complete sets (6,794, 2,036 and 3,877), embedded 29,296 distinct texts on the processor, and wrote 38,121 pairs. 588 explanations have no content word, which leaves 1,066 pairs without a word distance. Five hundred own distances of each kind, recomputed one at a time, agreed with the table, and the run manifest lists four inputs and two outputs.
- The R file was knitted in place in about fifteen seconds. Every input matched the checksum its producing run recorded, and the three long data files matched the ones the notebook read. All six mixed models converged; one, essence change on the word distance, is singular, its source-image variance estimated at zero, and keeps its numbers under the rule of `fit_status.R`. Each of the six permutation nulls has 200 of 200 refits, all converged. The run manifest lists eleven outputs, all written by the run, and no output names a folder particular to one machine.

## 2026-10-09, checked and rerun

An independent check of both files, and the changes it led to.

- The check. Every set of three in the pairs file is one participant's explanations of one source image on one question, and the sets are exactly the complete sets found from the long data files. In all three studies the item names agree with the levels, with `Min` as Slight and `Max` as Dramatic. Ten pairs drawn at random were recomputed from the raw text with a separate tokenizer and a fresh run of the embedding model, and their distances and stranger baselines agreed with the file to within one part in ten million. The pooled AI minus Human differences and their intervals were refitted with a separate model coding and agreed to every printed digit. The origin-talk shares were recomputed from the measures files and agreed exactly.
- `ExplanationShift_01_Measure.ipynb` now also reads each row's item name and stops unless it agrees with the row's image, level and question. It drops the item name before any measurement. It passes the device to the embedding model on every call, so in Google Colab the model runs on the graphics card whatever the version of sentence-transformers. The pairs file and the environment table now state the analysis status in their first column, `analysis`, as the other tables do.
- `ExplanationShift_02_Analysis.Rmd` checks and drops the status column of the pairs file. It defines the embedding distance, the cosine similarity, the content word, the Jaccard overlap, taint, resampling with replacement, convergence and a singular fit where they first appear. It says that none of the 24 rows of the model table is adjusted for the number of comparisons, and the figure states the analysis status in its caption.
- Rerun on 9 October 2026. The notebook ran in place in about two and a half minutes, and every check passed. The R file was knitted in place in about fifteen seconds, every input matched its producer's record, and every number in the model, arm-mean, description and origin-talk tables is unchanged.
