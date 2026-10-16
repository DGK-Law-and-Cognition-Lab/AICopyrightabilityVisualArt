# Study 4: AsPredicted registration

## 1) Data collection. Have any data been collected for this study already?

Yes, all of them, from 27 January to 2 February 2025. This is a registration of analyses on existing data, written before any analysis below is run in the current pipeline.

In February 2025 we fitted mixed ANOVAs (analyses of variance with between- and within-participant factors) to 117 participants, 116 of them in the sample of question 6. Our CogSci 2025 submission ("Study 2", N given as 119) and a public talk on 26 September 2025 reported a large modification effect, no significant label effect, a source-time effect on creativity only (p = .009), and a label effect on essence change that varied with modification (p = .025). We found no analysis of the justifications. For this registration we read counts, screening answers, image slots and answer codes, and summarised no rating by condition. We wrote the hypotheses knowing these results.

## 2) Hypothesis. What's the main question being asked or hypothesis being tested?

In Study 1 an AI label lowered creativity ratings of original works. Do the label and the time Alex spent on the source carry over to a second work he makes from it? Raters who judge only what the second work adds, the only part its copyright covers (17 U.S.C. § 103(b)), should show neither. Carry-over predicts both, largest at None, where the second work is the source unchanged.

- H1. Ratings rise from None to Slight to Dramatic on every measure.
- H2. On every measure, the label's average effect lies inside the bound in question 5.
- H3. With no predicted direction: does source time move ratings, alone or with modification?

## 3) Dependent variable. Describe the key dependent variable(s), specifying how they will be measured.

After each of 18 source and second-work pairs, participants gave three five-point ratings, each defined on screen: how transformative the second work is compared with the first, how much the essence of the first changed in it, and how much creativity went into producing it (Study 1's definition). Ratings are scored 1 to 5 by answer position, since the numeric export stores raw choice codes. Each has a required written justification.

## 4) Conditions. How many and which conditions will participants be assigned to?

Source label varies between participants (each sees one), assigned at random under a quota (a Qualtrics cap on assignment) of 62 per arm. Alex uses graphic design and sketching tools (Human) or prompts an AI system that generates the artworks (AI).

The rest varies within participants (each sees every level). Each person sees 6 of the 10 sources, three with a human or humanoid figure. A vignette says Alex spent less than 1 hour, 10 hours or 100 hours on each, two sources per level, in random order. Three second works, each made from the source, follow it in random order: None (unchanged), Slight (colour and contrast adjustments) and Dramatic (substantial hand changes). In both arms Alex makes them with his own tools; no time is stated.

## 5) Analyses. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

Each measure gets a linear mixed model, a regression with an estimated adjustment for each participant and each source: rating ~ label × source time × modification + (1 | participant) + (1 | source). Tests use Satterthwaite degrees of freedom, an approximation for mixed models. Contrasts use estimated marginal means, the model's predicted cell means averaged over the other factors.

Holm's correction, which keeps the chance of any false positive at .05, covers fifteen tests, five per measure. H1 needs Slight minus None and Dramatic minus Slight both positive and significant. H2 is an equivalence test of Human minus AI: two one-sided tests that pass when the 90 percent confidence interval lies inside ±0.224 rating points. The larger one-sided p-value enters the correction. H3 tests source time and its interaction with modification.

The bound, for all three measures, is half Study 1's 0.448-point creativity penalty: a pass means less than half that penalty reaches the second work. We set it knowing the results in question 1. Cumulative-link mixed models, which treat the answers as ordered categories, refit each model as a check.

## 6) Outliers and Exclusions. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

In order, with counts from the export, we remove preview records, which are test runs (7); unfinished records (8); any answer but "Yes, I did" to the seriousness item, a blank included (6); and wrong answers to the arithmetic check (none; a blank passes). All 119 left have a condition and answered the task check correctly.

A valid completion rates exactly six sources, each named once in the six image slots, two per source time. Two records fail, leaving 117: `R_3SPOPWqijqK09xf` rated all ten sources, and `R_6mZWuqtRNco0jiF` names one source in two slots, a 3/2/1 split of times.

The six-point transformativeness items, `1NonFigureNoneTrans` and `1NonFigureMinTrans`, are left out (140 ratings). Other answers lie on five-point scales, so none is an outlier.

## 7) Sample Size. How many observations will be collected or what will determine sample size?

Collection is complete, capped by the quotas. Of 140 records, 117 participants are analysed (62 AI, 55 Human), giving 6,178 analysed ratings and 6,318 justifications.

## 8) Other. Anything else you would like to pre-register?

Secondary analyses: the label effect at each modification level, whether time changes it, and equivalence of 100 hours and less than 1 hour, with the same bound.

Known problems: wording slips in three essence items' answer options, one reworded creativity stem, unrecorded modification order, and no check that participants took in the label. The Study 1 registration says an AI system made every source, so the Human vignette is a cover story.

An unsubmitted Open Science Framework form, last edited during collection (29 January 2025), planned mixed ANOVAs and a perceived-effort measure the survey lacks. It predicted that time would raise ratings, most under the AI label. The CogSci submission calls the study pre-registered, but Study 4 was not registered with any registry before collection, and this form, a Google Docs file that also covers Study 2, is its only planning document.

No language model or person labels, codes or judges any response. The one use of a pretrained model is a check that turns each response into numbers with a locally stored sentence-embedding model (all-mpnet-base-v2) and compares the resulting grouping with the topics below by the adjusted Rand index (agreement between two groupings beyond chance). The eight Study 1 word lists run unchanged on every justification, blind to condition and rating. A secondary refit drops Human-arm participants whom one list flags for writing that a machine made the work. Two checks run on creativity justifications. One asks how well the words predict rating and label, by ridge regression (a regression that shrinks word weights toward zero), tested on participants left out of fitting. The other asks whether AI-arm participants reuse their own words across 18 explanations more than Human-arm participants, relative to overlap with others writing about the same pair. As in Study 1, we predict they do. Exploratory: affect (how pleasant, arousing and dominant words are rated) and concreteness from published norms (Warriner et al., 2013; Brysbaert et al., 2014), topics found by a model given no labels, and the words carrying the predictions. Seeds: 20260421 in R, 20260903 for text.

## 9) Name. Give a title for this AsPredicted pre-registration.

Study 4: Do an AI label and source time carry over to a second work? Analyses of existing data
