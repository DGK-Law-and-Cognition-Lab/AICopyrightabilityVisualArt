# The `suppA_` and `s1_` tables

These files belong to three sections of the Supplementary Information:
`supplement/sections/registrations.tex`, `study1.tex` and `text_measures.tex`. This note says
where each came from. Paths that start `Study 1/` are inside `Analysis/R Analysis Pipeline/`.

## Tables written for these sections

Every number in them is a macro from `generated/numbers.tex`; the rest is design fact taken
from the registrations or the survey files.

| File | What it is | Source of its content |
|---|---|---|
| `suppA_registrations.tex` | The six registration documents, the study each covers, its data-collection dates and analyzed sample, and what it registers | `Docs/Preregistration/AsPredicted/Study1_AsPredicted.md` to `Study5_AsPredicted.md` and `Docs/Preregistration/Study1_Preregistration.md`; sample sizes are the macros `\SOneN` to `\SFiveN` |
| `suppA_wordlists.tex` | The eight word lists, what each flags, examples of what it matches, and the further reading of a match | `Study 1/tables/text_rules.txt` (SHA-256 `6aa77dbc26c9086c5349a863c1cab808d7bd3758265fc365de2fb36c46a30239`, as `Study 1/tables/text_rules.sha256` records); the lists themselves are in `shared/python/study_text.py` |
| `suppA_h2_versions.tex` | Study 1's H2 in its two registered versions | Macros `\SOneHTwo...` from `Study 1/tables/study1_joint_model_contrast_of_contrasts.csv`, `study1_confirmatory_family.csv` and `study1_h2_ordinal.csv`. It replaces the pipeline's `sup_table_h2_ordinal.tex`, whose 18 columns print at under 3 points when fitted to the page |
| `suppA_denotation_tests.tex` | Study 1's five word-meaning tests | Macros `\SOneText...` from `Study 1/tables/study1_text_denotation_tests.csv`. It replaces the pipeline's `sup_table_denotation_tests.tex`, which prints at under 3 points when fitted to the page |

## Readable copies of the Study 1 pipeline tables (`s1_*`)

`supplement/sections/study1.tex` inputs these sixteen tables, not the pipeline's own. Each is
written by `tools/make_tables.py` from the CSV table (or tables) that its original was written
from, and keeps its original's label, so every cross-reference is unchanged. The pipeline's
versions printed CSV column names as headings, carried captions of up to 400 words, and were
shrunk to fit the page at 6 to 7 points. The copies have plain headings, a caption of a few
sentences that says what the table shows and the status of each result, a note below the table
that defines every abbreviation, and type of at least 9 points. Numbers are rounded as
`tools/make_numbers.py` rounds the macros (two decimals for ratings, effect sizes and test
statistics; three for very small differences in AUC or word overlap; degrees of freedom whole,
or to one decimal when not close to whole, without a thousands separator; counts whole;
percentages to one decimal; $p$-values in APA style). Before writing anything the script checks
each CSV against the SHA-256 that the last run of `Study 1/Study1_Supplements.Rmd` recorded
for it (`Study 1/tables/study1_supplements_run_manifest.csv`, run of 7 October 2026) and against
the SHA-256 in `generated/numbers_check.csv`. Wherever a macro prints the same cell, the two
printed values must be identical (80 cells, 79 of them in the same format; the other is the
three-decimal macro `\SOneHOneCreatDiffPrecise`). `s1_sources.csv` in this folder lists every
source with its checksum.

| Copy | Replaces | Source CSV in `Analysis/R Analysis Pipeline` (SHA-256) |
|---|---|---|
| `s1_exclusions.tex` | `sup_table_exclusions.tex` | `Study 1/tables/study1_exclusion_flow.csv` (`5a76f3fe7f18f46d3c304d1e538b31f3ae1a17975029d55dcb384cf18eab7d10`) |
| `s1_attrition.tex` | `sup_table_attrition.tex` | `Study 1/tables/study1_attrition_by_condition.csv` (`ad43935243eb6c87150c77cd64dab1f7ff34e901a0dbf4cb34a79eb6d1623f6e`) |
| `s1_demographics.tex` | `sup_table_demographics.tex` | `Study 1/tables/study1_demo_age.csv` (`95fda01292f4a4cc41845ddc3de73c77a497c3e65747bb758ba236d7a11118a4`); `Study 1/tables/study1_demo_gender.csv` (`846ba92df512e0f199472d00abc578f58ff9ab5470084edd7a93238b3d3465e5`); `Study 1/tables/study1_demo_race.csv` (`dac3c3e28a8942ff391aab00e9c04a2dcaf1cfe3b6e64907d9c2f22e61329b5d`); `Study 1/tables/study1_demo_experience.csv` (`590883417fee4e75547b3369e3026420a22a6e2e4b465996c49b0aeab2d0bf03`); `Study 1/tables/study1_demo_balance.csv` (`1c1a883be1c80d7a1de4364e5a61b2e8946a271a2b2973cc4cc33bb92cd5cbfb`) |
| `s1_balance.tex` | `sup_table_balance.tex` | `Study 1/tables/study1_balance.csv` (`794c8844a3e4f130cbd245beb28aa7ed1c920da9ba1496080475832220f05ca9`) |
| `s1_holm_family.tex` | `sup_table_holm_family.tex` | `Study 1/tables/study1_confirmatory_family.csv` (`d502d85829e95b88558fc42e57ea4256f2c2506ef932396cfb090241b2d06fbc`); `Study 1/tables/study1_joint_model_anova.csv` (`c7e91d3bef09735c81a4b0b0533c03e9c6db850983f615b65775cfbea7543c83`); `Study 1/tables/study1_h4_variance_test.csv` (`499b8678ab6a36e9b9d5b1d9bfa2c9b547b16020d745fde8a443cecb28b62e07`) |
| `s1_full_lmm.tex` | `sup_table_full_lmm.tex` | `Study 1/tables/study1_lmm_fixed_effects.csv` (`e050698a9459c7df8aede2cdd6c34fd54ce2c5d2203b53be11a3ec5e25eeb942`) |
| `s1_robustness.tex` | `sup_table_1_robustness.tex` | `Study 1/tables/study1_confirmatory_family.csv` (`d502d85829e95b88558fc42e57ea4256f2c2506ef932396cfb090241b2d06fbc`); `Study 1/tables/study1_specification_curve.csv` (`bf372ede20c3a9887df35cbeacdeda5983fe44a4d0c7f9e7dc06a8325ecf4c09`); `Study 1/tables/study1_brms_primary_fixed.csv` (`60514547f37adf2c52b47d6e914a82ef2db0380e86e9f7caf49028948101ef5b`); `Study 1/tables/study1_brms_cumulative_fixed.csv` (`865874e9bead54ac27d9f389a0b49f6c01badcfd61c5c84b962a465b267cc34c`); `Study 1/tables/study1_lmm_fixed_effects.csv` (`e050698a9459c7df8aede2cdd6c34fd54ce2c5d2203b53be11a3ec5e25eeb942`); `Study 1/tables/study1_equivalence_sensitivity.csv` (`be48d50f8987f8042a6e995e697c338c383eb78fa584ea70b1ae1727dbd1f634`) |
| `s1_influence.tex` | `sup_table_influence.tex` | `Study 1/tables/study1_influence_lopo.csv` (`199b870aa85ac5a1074944aaac070a5fcd4287ea7505a961b225e6ad83ab6e75`); `Study 1/tables/study1_influence_loso.csv` (`c17b0224327a1532aff03995fa274b44509a1d136bb408aef06f4f3d23341e13`) |
| `s1_item_sensitivity.tex` | `sup_table_item_sensitivity.tex` | `Study 1/tables/study1_item_sensitivity.csv` (`434b75e3bb2ffaac902aa9c073a2424283507dcb489a9e201fb97be7639f44e5`) |
| `s1_bootstrap_d.tex` | `sup_table_bootstrap_d.tex` | `Study 1/tables/study1_bootstrap_d.csv` (`a223905d69ebbaaa35cb1f512a1a1cdefca4c5678b8057acd613e38876f048ca`) |
| `s1_text_rates.tex` | `sup_table_2_text_rates.tex` | `Study 1/tables/study1_text_effort_prevalence.csv` (`e312979f6f455d06c2e566ffaa664e76acc741d5ffef4debcf986730f52832ac`); `Study 1/tables/study1_text_creativity_prevalence.csv` (`b4017bff3c84c961dd6dfc4ffccf4beb8b439a0b6e3e770c38756ab56ef81726`) |
| `s1_prompt_talk.tex` | `sup_table_3_prompt_talk.tex` | `Study 1/tables/study1_text_prompt_by_arm.csv` (`90cb709fae69a3f0623a99565fc0f97ed61b6d082321c6429757617775a2d858`) |
| `s1_denotation_slope_sensitivity.tex` | `sup_table_denotation_slope_sensitivity.tex` | `Study 1/tables/study1_text_denotation_slope_sensitivity.csv` (`7b92f279a83a0c66990ce6bf3c8a500da9ce97b00e1cab45c8c7fb412802875a`) |
| `s1_text_recoverability.tex` | `sup_table_text_recoverability.tex` | `Study 1/tables/study1_text_recoverability.csv` (`23af11956d87fa145255dddef8f9a3ded2c67aedc1e6c04a61a6879708e0babe`) |
| `s1_text_selfsimilarity.tex` | `sup_table_text_selfsimilarity_by_arm.tex` | `Study 1/tables/study1_text_selfsimilarity_by_arm.csv` (`1503b1471e4774488e277de4b26e8415543040f5c3d3897169696890288e0672`) |
| `s1_text_topics_stability.tex` | `sup_table_text_topics_stability.tex` | `Study 1/tables/text_topics_stability.csv` (`fa312640420b5534bc1eceb367d6f094fbd1949ca6765c465870583d9c140475`) |

Two of the copies add a value that their original did not print, from a table that the same
pipeline run read: `s1_holm_family.tex` gives H2's denominator degrees of freedom from
`study1_joint_model_anova.csv` (the script checks that this row's $F$ and $p$ equal those in the
confirmatory family), and states H4's registered verdict from `study1_h4_variance_test.csv`.
`s1_full_lmm.tex` reads `study1_lmm_fixed_effects.csv`; its original was drawn from the saved
model files (`Study 1/models/study1_lmm_*.rds`), which hold the same fits. Columns that only
described the run (random seeds, numbers of word columns, the number of resamples on every row)
are left out or stated once in the note. The two influence columns print to two decimals, where
the original printed three. The original caption of the topic-stability table said the topic
model was refitted from ten random starting points; the analysis code refits it on ten random
80 percent subsets of the participants, and the copy says so.

## Earlier copies of tables the pipeline writes (kept; no longer input)

`Study 1/Study1_Supplements.Rmd` writes 29 tables and 3 figures straight into
`supplement/tables/` and `supplement/figures/` (run of 7 October 2026). Four of them were used
through a copy with one or more changes to layout or wording. No number is changed: the script
that made each copy compared every number in the copy with the original. The checksum below is
the original's SHA-256, which equals the value that `Study 1/tables/study1_supplements_run_manifest.csv`
records for it. If the pipeline rewrites an original, copy it again and repeat the change.

| Copy | Original (SHA-256) | Change |
|---|---|---|
| `suppA_full_lmm.tex` | `sup_table_full_lmm.tex` (`3ada050706b6c859d3c9336e60b2dc84d150d9f87639d90f6de75d91bbec0a3a`) | The caption's `Supplementary Table 1`, the pipeline's own numbering, becomes `Supplementary Table~\ref{tab:supp_table_1}`, the robustness table in this document |
| `suppA_robustness.tex` | `sup_table_1_robustness.tex` (`4fa44484448911f156df17522ea265cac02acbddab428b9bca6aa5e28b3db001`) | Column widths `p{4.2cm}` and `p{10.8cm}` in place of `l` and `p{10cm}`, which ran 170 points past the margin; caption set `small` and body at 8 points, so that the table fits one page; the caption's `summarise` becomes `summarize` (American spelling) |
| `suppA_demographics.tex` | `sup_table_demographics.tex` (`ffccfb4cc29d79aa2f358590ddb34386015c08e5c3da0203fbbd22f52af109ac`) | Columns 2 and 3 set as `p{7cm}` and `p{5.2cm}` in place of `l`, which ran 137 points past the margin |
| `suppA_denotation_slope_sensitivity.tex` | `sup_table_denotation_slope_sensitivity.tex` (`8980f50779e425c7d532d5c59a9640fffd04a431600c7bee25c0aab3c1cb588c`) | `The preregistration lists this refit` becomes `The registration lists this refit`: Study 1 was registered after its analyses had been run |

## Pipeline figure input unchanged

`sup_fig_2_brms_ppc.pdf` (Supplementary Figure 3), set at the full text width so that its smallest
text prints at about 8 points, with a caption that explains its axes and its legend. It matches
the checksum that the run manifest records. Redrawing it would need the fitted Bayesian models,
which `tools/make_figures.py` cannot read.

## Pipeline tables and figures not used

All are current; they are left out for the reason given. The analysis CSV named in
`supplement/sections/study1.tex` gives every row.

| File | Reason |
|---|---|
| `sup_table_exclusions`, `sup_table_attrition`, `sup_table_balance`, `sup_table_holm_family`, `sup_table_influence`, `sup_table_item_sensitivity`, `sup_table_bootstrap_d`, `sup_table_2_text_rates`, `sup_table_3_prompt_talk`, `sup_table_text_recoverability`, `sup_table_text_selfsimilarity_by_arm`, `sup_table_text_topics_stability` | Replaced by the `s1_` copies above |
| `suppA_demographics`, `suppA_full_lmm`, `suppA_robustness`, `suppA_denotation_slope_sensitivity` | Earlier copies, replaced by the `s1_` copies above |
| `sup_table_h3_equivalence`, `sup_table_h3_equivalence_power`, `sup_table_h4_variance`, `sup_table_h4_resolution`, `sup_table_fully_maximal`, `sup_table_joint_model` | 12 to 15 columns each; fitted to the page they print at about 3.3 to 4.6 points. Supplementary Note 1 and the Study 1 section give their results through macros |
| `sup_table_text_affect_by_arm`, `sup_table_text_novelty_within_between`, `sup_table_text_topics_by_arm`, `sup_table_text_prediction_weights` | 19 to 22 columns; fitted to the page they print at about 1.7 to 2.9 points. The Study 1 section summarizes each. The caption of `sup_table_text_prediction_weights` also calls the lasso weights ridge weights |
| `sup_table_text_topics_embedding_agreement` | Its caption says that no measure in the paper rests on the embedding model; Supplementary Note 7's measure of how far explanations moved now does |
| `sup_table_h2_ordinal`, `sup_table_denotation_tests` | Replaced by `suppA_h2_versions` and `suppA_denotation_tests` |
| `sup_fig_1a_specification_creativity.pdf`, `sup_fig_1b_specification_effort.pdf` | The axis title and the right-hand panel are cut off at the page edge in the PDF itself; the specification curve is summarized in `s1_robustness` and in Supplementary Note 2 |
