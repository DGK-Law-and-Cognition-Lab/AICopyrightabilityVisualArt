# Structural topics in the justifications

**This analysis is exploratory.** It was specified on 9 October 2026, after every registered result of the five studies was known. No registration, the plan of analysis filed for a study before its results were seen, names it, and it changes no registered verdict. The R Markdown file says so at its top, every table in `tables/` says so in its last column, `analysis_status`, and each figure says so at its foot. Every justification was written after its rating, so nothing here is evidence of why anyone rated as they did: the analysis describes what people wrote once their number was chosen.

## What it asks

In Studies 2, 4 and 5 each participant was told that the artist Alex made a first artwork either with design software and sketching tools (Human) or by prompting an AI system (AI). Each rated second works that Alex made by hand from it at three levels of modification, None (the first work unchanged), Slight (colour and contrast adjustments) and Dramatic (substantial changes by hand), and wrote a short justification after every rating.

The analysis asks whether the label changes what people write about, and whether that change differs as the second work moves away from the first. A structural topic model answers it. A topic is a group of words that tend to appear in the same responses; formally, a probability distribution over the words. The structural topic model, fitted with the R package stm, finds the topics and lets the share of each topic in a response, its prevalence, depend on covariates, quantities recorded for each response: here the source label, the modification level, the rating and the study. The label's effect on each topic is then estimated from repeated draws of every response's topic shares, so its uncertainty includes the uncertainty of those shares. It does not include the uncertainty of the topics' word lists, which are held at their estimates; the stability check below examines that separately.

Each study's own files answered a similar question in two steps: a topic model fitted without the label, then a test of the label topic by topic. That approach stays as each study registered it. This analysis sits beside it as description and replaces nothing.

No person and no language model labels, codes or judges any response, and no topic is named by anyone. Each topic is identified by its number, its highest-probability words and its most distinctive words, all computed by the model.

## The files

| File | What it does |
|---|---|
| `StructuralTopics.Rmd` | Reads each study's long data file, word counts and item wording, checks each against the record of the run that wrote it, applies the vocabulary rule, chooses the number of topics, fits the models, checks their stability, estimates the label's effect on each topic, draws the figures, and records fit status and a run manifest. |
| `README.md` | This file. |
| `CHANGELOG.md` | The edit history of the R Markdown file, which carries none itself. |
| `tables/` | Every table the R Markdown file writes. |
| `figures/` | One figure per question, as PDF and PNG. |

An R Markdown file (`.Rmd`) mixes R code with text and is knitted, that is, run from top to bottom into an HTML report, here `StructuralTopics.html` beside it.

## How to run it

From this folder:

```sh
Rscript -e 'rmarkdown::render("StructuralTopics.Rmd")'
```

or open the file in RStudio and press Knit. The knit prints a line with the clock time to the console at each step, so a long run can be followed. The model fits run on up to nine processor cores at once (one on Windows); every fit gives the same result from the same seed, so the results do not depend on the number of cores. On a twelve-core Mac with little else running the knit took about 42 minutes: 7 to 10 minutes of searchK for each question and about 15 for the eighteen fits at the chosen K. Other work on the machine lengthens it.

Each study's pipeline must have been run first, on its real labels. The file reads, from each of the folders `Study 2`, `Study 4` and `Study 5`:

- `studyN_long_with_text.csv`, the long data file, one row per participant, second work and question, with the label, the level, the rating and the justification;
- `nlp/studyN_text_wordcounts.csv`, the word counts that the study's text notebook wrote with the shared module `shared/python/study_text.py`: the justification lower-cased, split into words, the function words (words such as *the* and *of* that carry grammar rather than content) removed, and the words used in at least two responses of the study kept;
- `tables/studyN_item_scales.csv`, the stem and answer labels of every rated item;
- `tables/studyN_quant_run_manifest.csv` and `tables/studyN_text_run_manifest.csv`, the records the real quantitative run and the text run wrote, and for Study 5 `tables/study5_quant_run_inputs.csv`.

It also reads the function words, the task vocabulary and the word pattern from `shared/python/study_text.py`, so it keeps no copy of its own, and it uses `shared/R/fit_status.R` for the run record.

## What it checks before it models anything

The run stops unless every check passes:

- each long data file has the SHA-256 checksum (a 64-character fingerprint of a file's exact bytes) that its study's real quantitative run manifest lists, and `label_mode` says `real` on every row; a blind run, one on shuffled labels, writes its records elsewhere, so a match can only come from a real run;
- each item-scale table matches the record of the real quantitative run (for Study 5, the run's input record, since its build script writes the table);
- each word-count file matches the study's text run manifest;
- the counts are those registered: Study 2, 235 participants and 20,659 analysed ratings; Study 4, 117 and 6,178, with 140 six-point ratings left out; Study 5, 223 and 11,768, with 274 six-point ratings left out;
- every response in the word counts is a response in the long data file, and no function word appears in them;
- the word pattern and function words read from the shared module, applied in R to every justification, reproduce each study's deposited word counts exactly, which shows that the item wording is split into words by the same rule.

## The analysis

Creativity is the primary question, because it is the one asked of original artworks and second works alike. Transformativeness and essence change are secondary. Each question gets its own corpus, a collection of responses, pooled over the three studies. The two six-point transformativeness items are dropped, as each study's primary analysis drops them.

1. **The vocabulary rule**, fixed in code. A word every participant read appears wherever people restate the question, so the rule removes from each study's responses the shared task vocabulary (the Study 1 instrument's words, such as *alex*, *artwork* and *creativity*), with the plural of each task word as the shared module removes them, and every word in the stems or answer labels of that study's rated items. It then keeps, within each question's pooled corpus, the words used in at least 5 responses. A response left with no word is dropped and counted.
2. **The model.** For each question, `prevalence ~ source * modification + rating_c + study`, where `rating_c` is the rating minus the mean rating of the question's modelled responses. The model has no content covariate, so each topic has one list of word probabilities for every response. The rating is in the model so that a label effect on a topic is not merely the label's effect on the rating carried into the words.
3. **The number of topics**, K, chosen by a rule fixed in code. `stm::searchK` fits K = 4 to 12, each from a spectral initialisation (a starting point computed from how often pairs of words appear together, with no random draw), after drawing a random tenth of the documents from seed 20260421 and setting aside half the word occurrences of each (rounded down, and at least one); a drawn document with only one distinct word gives up none, so 880 creativity, 843 transformativeness and 891 essence change documents lose words. The held-out likelihood is the log probability a fitted model gives to each word it did not see, averaged over the set-aside words of each document and then over the documents. The chosen K has the highest held-out likelihood; an exact tie goes to the smaller K. Semantic coherence (how often a topic's top words appear together in the same responses) and exclusivity (how specific a topic's top words are to it) are reported for every K.
4. **The fit and the topics.** The chosen K is fitted to every modelled response from the spectral start with seed 20260421. For each topic the file lists its seven highest-probability words, its seven FREX words (FREX weighs a word's frequency in the topic against its exclusivity to it, here with equal weight), its mean share, and the three responses with the largest share of it, identified by study, participant identifier and second work, with no text.
5. **Stability.** The chosen K is fitted five more times from the latent Dirichlet allocation (LDA) start, which draws initial topics from a short run of a simpler topic model and so depends on the seed, here 20260421 to 20260425. For each topic of the spectral fit, the best-match correlation is the largest correlation, across the vocabulary, between its word probabilities and those of any topic of a refit; the table gives its mean over the five refits, its smallest value, and in how many refits the best match was shared with another topic.
6. **The label's effect.** `stm::estimateEffect` with uncertainty "Global" fits a linear regression of each topic's share on the covariates 25 times, each on a fresh draw of every response's topic shares from the fitted model, which carries the uncertainty of those shares into the effects (the method of composition). The topics' word probabilities are held at their estimates, so their uncertainty is not carried. "Global" is stm's approximation that centres each response's draw on its estimated shares and gives every response the same spread, estimated once from the whole model. From each of the 25 coefficient sets, 500 draws are taken from a normal distribution centred on the coefficients, with the spread and correlations that the regression estimated for them, as stm's own summary does. For each topic the file gives (a) the AI minus Human difference in expected topic share at None, Slight and Dramatic, (b) that difference averaged over the three levels, and (c) the difference at Dramatic minus the difference at None, which says whether the label difference changes across the levels. Each has a 95 percent interval and a two-sided p-value from the mean and standard deviation of the draws and the t distribution, the distribution that an estimate divided by its standard error follows when the true difference is zero, with the residual degrees of freedom of the regression (documents minus coefficients). The Benjamini-Hochberg adjustment, which controls the expected share of false findings among results called significant, is applied across the topics of each question, separately to (b) and (c), and is labelled description. The values in (a) carry no adjustment.

## What it writes

In `tables/`, each table with a last column, `analysis_status`, that says it is exploratory (the session information file says so in its first line):

- `structural_topics_input_checks.csv`: every check above, with the expected and observed value;
- `structural_topics_vocabulary_removed.csv`: every word the rule removes, by question and study, with the reason (task vocabulary, plural of a task word, item wording, or used in fewer than 5 responses), the number of analysed responses that used it, and whether the word is removed from all three studies' responses or only some;
- `structural_topics_corpus_counts.csv`: by question, by study and pooled, the analysed responses, those dropped for keeping no word, those modelled by label and level, the participants, the word tokens at each step, the vocabulary size and the mean and median words per modelled response;
- `structural_topics_dropped_by_label_and_level.csv`: by question, by study and pooled, the analysed responses in each cell of label and level, the number dropped for keeping no word, and the share dropped;
- `structural_topics_searchk.csv`: for every question and K, the documents drawn for holding out and the number that gave up words, the held-out likelihood, semantic coherence, exclusivity, residual dispersion (stm's check of whether the words vary across responses more than the model allows, near 1 when they do not), lower bound (the quantity each fit maximises), iterations and whether the fit reached the iteration limit;
- `structural_topics_chosen_k.csv`: the chosen K of each question, its held-out likelihood, the runner-up and the rule;
- `structural_topics_topic_words.csv`: every topic's label (its number and four highest-probability words), its seven highest-probability and seven FREX words, and its mean share;
- `structural_topics_topic_examples.csv`: the three example identifiers of every topic with their topic shares;
- `structural_topics_stability.csv`: the best-match correlations of the five LDA refits with the spectral fit, per topic;
- `structural_topics_label_effects_by_level.csv`: AI minus Human in expected topic share at each level, with its standard error, 95 percent interval, t statistic, degrees of freedom and uncorrected p-value, whether the model converged, and a note when it did not;
- `structural_topics_label_effects_averaged_and_change.csv`: the difference averaged over levels and the difference at Dramatic minus at None, with the same columns and the Benjamini-Hochberg adjusted p-value;
- `structural_topics_fit_status.csv`: every model fitted, with whether it stopped with an error, whether it converged, its iterations, the last relative change of its bound beside the threshold, and any warning;
- `structural_topics_run_inputs.csv`, `structural_topics_sessionInfo.txt`, `structural_topics_package_versions.csv` and, written last, `structural_topics_run_manifest.csv`. The manifest lists every output with its checksum; the file deletes the old manifest when it starts, so a manifest on disk means the run reached its end.

In `figures/`, as PDF and PNG, in greyscale, each with a line at its foot saying it is exploratory: `structural_topics_creativity`, `structural_topics_transformativeness` and `structural_topics_essence_change`. Each shows every topic's AI minus Human difference in expected share at None, Slight and Dramatic with its 95 percent interval, each topic labelled by its number and its four highest-probability words.

## How the code reads the specification

Where the specification leaves a choice open, the code takes these readings.

- **Whose item words.** Each study's rule removes the words of that study's own items, as the specification says. Study 2's creativity and essence items carried no definition, and Studies 4 and 5 used Study 1's, so words such as *original*, *unique*, *feeling* and *sense* are removed from the responses of Studies 4 and 5 and kept in those of Study 2. The vocabulary table marks every such word.
- **Which items.** Every item in the item-scale table, the six-point items included, since participants read those too. The six-point items add *somewhat* to every study's list and *consider* to Study 2's.
- **Plurals.** The task vocabulary is removed with the plural of each task word (the word with a final *s*), as the shared module removes it. Item words are removed as written, so *changes* stays while *change* and *changed* go.
- **The rarity rule** counts responses within each question's pooled corpus, after the task and item words are removed, among the analysed five-point responses.
- **The centred rating** is centred on the mean rating of the question's modelled responses.
- **Ties in K** go to the smaller K only when the held-out likelihoods are exactly equal.
- **searchK's settings** are its defaults: in a random tenth of the documents, half the word occurrences of each (rounded down, and at least one) are held out, except in a drawn document with one distinct word, which keeps it, and semantic coherence and exclusivity are computed on each topic's ten most probable words, exclusivity with FREX weight 0.7.
- **Stability seeds** are 20260421 to 20260425, the registered R seed and the four numbers after it. The best match is not one to one: two spectral topics can share a best match in a refit, and the table counts how often they do.
- **Effects** are computed from the model's predicted share in each cell of label and level at the average rating, so the factor coding does not change them. With no label by study or label by rating term in the model, each difference is the same in every study and at every rating.
- **Convergence.** A stm fit converged when its search stopped before the limit of 500 iterations, because its bound, the quantity the search maximises, rose by less than 0.00001 of itself from one iteration to the next, or fell. searchK returns no convergence flag, so its fits are marked by whether they reached that limit. The pipeline's rule for a model that did not converge, written in `shared/R/fit_status.R` for the mixed models, is applied to the topic models too: the model's estimates are kept as description, and its standard errors, intervals, t statistics and p-values are set to missing with a note. In the runs of 9 and 10 October 2026 this applies to essence change, whose model reached 500 iterations.

## Limits

- Every justification was written after its rating.
- The responses are short, a few kept words each, so each response's topic shares rest on little evidence.
- The model reads only the responses that kept a word. At None the AI arm, the participants told that the first work was made by prompting an AI system, lost a larger share of its responses than the Human arm (31.1 against 25.9 percent for creativity, 30.7 against 27.5 for transformativeness, 33.3 against 28.1 for essence change), so a label effect at None compares responses selected differently in the two arms, and part of it may come from which responses kept a word rather than from what the kept ones say.
- The intervals carry the uncertainty of each response's topic shares but not that of the topics' word probabilities, which are held at their estimates. The stability check speaks to the second, and a label effect on a topic that the LDA refits do not recover may not survive another start.
- Each participant wrote many responses, and the model treats them as independent. stm has no term for the participant, so the intervals do not widen for responses that share a writer and are likely too narrow.
- The effects rest on 25 simulated sets of topic shares, stm's default, so every standard error carries simulation noise, and another seed would move each interval somewhat. The CHANGELOG entry of 10 October gives its size for one topic.
- The label's effect is assumed the same in all three studies, and Study 4's source time and Study 5's editing time are left out.
- The deposited word counts hold only words used in at least two responses of their study, so a word used once in a study does not count toward the pooled rarity rule.

## Environment

R 4.5.2 with stm 1.3.8, readr, dplyr, tidyr, tibble, MASS, ggplot2, rmarkdown and knitr; `tables/structural_topics_package_versions.csv` records the versions of a run. Paths are found from this file's own folder. These environment variables, named settings the shell passes to R when it starts, name other folders:

| Variable | What it names |
|---|---|
| `STRUCTURAL_TOPICS_DIR` | this folder |
| `PIPELINE_DIR` | the analysis pipeline folder, two levels up |
| `STUDY_SHARED_R`, `STUDY_SHARED_PYTHON` | the shared R and Python helpers |
| `STUDY2_DIR`, `STUDY4_DIR`, `STUDY5_DIR` | the three study folders |

Printed paths are relative to the pipeline folder, so no output names a folder particular to one machine.
