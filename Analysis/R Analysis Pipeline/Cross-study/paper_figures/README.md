# Paper figures: one figure per claim

This folder draws the paper's seven main-text figures and two Supplementary figures. Figures 2, 3, 5 and 6 put the condition on the horizontal axis and the rating (1 to 5) on the vertical axis, and show the whole distribution: each violin is the spread of participants' mean ratings, the small dots are those participants, and the large marker with its black bar is the group mean with its 95 percent confidence interval. The figures are in grayscale: the Human label, named on the figures "Human-generated original", is a black circle on a solid line over a gray violin, and the AI label, "AI-generated original", a white circle on a dashed line over a white violin. Figures 4 and 7 and the two Supplementary figures are bar charts with 95 percent intervals and the value printed beside each bar.

These figures are descriptive. The paper's text reports the registered models' estimates. `output/figure_values.csv` sets each plotted group mean beside the model's estimate for the same cell wherever a pipeline table gives one; they agree to within about 0.05 points.

## The figures

Study numbers on the figures are the paper's. The paper numbers the studies in the order it presents them, which swaps two of the pipeline's folders: the pipeline's `Study 2/` is the paper's Study 3, and its `Study 3/` is the paper's Study 2.

| File | Claim | Data (pipeline folder) |
|---|---|---|
| `fig1_stimuli` | What participants saw: three of the ten AI-made originals, each beside its Slight and Dramatic hand edits. | `image_check/stimuli/`, each image checked against `stimuli_manifest.csv` |
| `fig2_study1` | Study 1: the same images were rated lower on creativity and effort under the AI label. | `Study 1/` |
| `fig3_study2` | Study 2: stated hours raised ratings of the originals under both labels, but did not remove the AI label's penalty. | `Study 3/` |
| `fig4_explanations_originals` | Studies 1 and 2: under the AI label, explanations of originals often mentioned prompting or a machine. Bars are the shares of explanations with the flag, with the text battery's 95 percent interval from resampling participants. | `text_battery/tables/text_battery_prevalence.csv` |
| `fig5_secondary` | Studies 3 to 5: ratings of the secondary works rose with the edit level, and the original's label made little difference. One row per rating (A creativity, B transformativeness, C essence change), one column per study. | `Study 2/`, `Study 4/`, `Study 5/` |
| `fig6_hours_secondary` | Hours stated for making the original (Study 4) or the secondary work (Study 5) left creativity ratings of the secondary works flat. Each participant's ratings are averaged over the three edit levels. | `Study 4/`, `Study 5/` |
| `fig7_explanations_secondary` | As Figure 4, for the secondary works of Studies 3 to 5, on the same 0 to 60 percent scale: such mentions were rare. | `text_battery/tables/text_battery_prevalence.csv` |
| `figS_image_grounding` | Supplementary: how much less closely explanations described their own picture under the AI label (AI minus Human, in standard deviations, from CLIP), with all explanations and without those that mention prompting or a machine. | `image_grounding/tables/image_grounding_label_effects.csv` |
| `figS_label_from_meaning` | Supplementary: how well each participant's label is predicted (AUC, from 0.5 at chance) from rating and length, from meaning alone, and from meaning alone without the explanations that mention prompting or a machine. | `label_from_meaning/tables/label_from_meaning.csv` |

Each figure is written as a PDF and a PNG in `output/`.

## Which ratings are used

The ratings the registered analyses used: every row with a rating, except, in Studies 4 and 5 (the pipeline's `Study 4/` and `Study 5/`), the two transformativeness items with six answer options, which the registrations leave out. The script stops if a study's number of participants differs from its analyzed N (111, 85, 235, 117 and 197 in the paper's Studies 1 to 5; Study 5's 197 are the 223 of its registration less the 26 who had completed an earlier study).

## How to run it

From this folder:

```sh
python -m pip install -r requirements.txt
python make_paper_figures.py
```

It needs Python 3.12 and the packages in `requirements.txt`, and the Times New Roman font. Paths are found from the script's location, so it runs from anywhere in a copy of the repository. The jitter of the dots uses a fixed seed and the files carry no creation date, so two runs on the same data write identical files. To write the figures elsewhere, set the environment variable `PAPER_FIGURES_OUT`.

The script writes no participant identifier. `output/figure_values.csv` holds group summaries only: figure, panel, study, rating, label, condition, number of participants, mean, standard deviation, interval and the model's estimate.
