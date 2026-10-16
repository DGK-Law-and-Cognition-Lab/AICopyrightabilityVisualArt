# AsPredicted registration for Study 2

## 1) Data collection. Have any data been collected for this study already?

Yes. Data were collected on Qualtrics from 23 November to 5 December 2024, before Study 1. This registers analyses of existing data, written before any analysis below is run in the current pipeline.

- By February 2025 we had fitted an analysis of variance (a test of differences between condition means) to the 235 participants kept under question 6. Our CogSci 2025 submission (as Study 1; proceedings version unverified) and a DataBlitz talk on 26 September 2025 reported it, with plots of every cell. Modification had very large effects. Source mattered only for creativity (p = .026; Human 2.20, AI 2.08), though not at any single level (all p > .244). No interaction was significant.
- In April 2025 we ran keyword, topic and sentiment analyses of the justifications. Mean sentiment, a score for how positive the wording is, was 0.066 under the Human label and 0.049 under AI.
- Since then, only counts and a few pooled answer frequencies have been read from the exports.

Study 2 was not registered with any registry before collection; its only planning document, an Open Science Framework preregistration template filled in Google Docs and never submitted, was begun on 5 November 2024 and last edited on 29 January 2025, after collection. The CogSci submission nonetheless calls the experiment pre-registered.

## 2) Hypothesis. What's the main question being asked or hypothesis being tested?

In Study 1 an AI-prompting label lowered the rated creativity of original artworks. Does that penalty reach a second work that the artist, Alex, makes by hand from the first? If AI origin taints what is built on it, the penalty holds at every level of modification. If raters judge the second work partly by the first, it is largest at None and shrinks with modification. If they judge only what Alex added, it is absent.

- H1. Ratings rise from None to Slight to Dramatic on all three measures.
- H2. Averaged over modification, the penalty is small or absent on each measure.
- H3. We ask, with no predicted direction, whether the penalty shrinks with modification. This separates the first two accounts.

## 3) Dependent variable. Describe the key dependent variable(s), specifying how they will be measured.

Each participant rated 30 second works on three five-point scales: how transformative the second work is compared to the first (defined on 28 of 30 items), how much the first work's essence changed, and how much creativity went into the second work. Ratings are scored 1 to 5 by answer position, since the numeric export stores raw choice codes. A required written justification followed each rating.

## 4) Conditions. How many and which conditions will participants be assigned to?

Source process varies between participants (each sees one condition), assigned at random with quotas (counters that cap each arm) of 125. To make the first artwork, Alex either "only uses graphic design software and digital sketching tools" (Human) or "develops and inputs prompts into an artificial intelligence (AI) system" (AI). In both, he makes every second work himself with design tools.

Modification varies within participants (each sees every level). Ten source artworks, five showing a human or humanoid figure, each appeared as None (shown again unchanged), Slight (colour and contrast adjustments) and Dramatic (substantial changes by hand), in an unrecorded random order.

## 5) Analyses. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

Each measure gets a linear mixed model, a regression giving each participant and source artwork its own baseline: `rating ~ source * modification * image_kind + (1 | participant) + (1 | image)`. P-values use Satterthwaite's approximation for mixed models, and contrasts use estimated marginal means, the model's cell means averaged equally over the other factors. Four confirmatory tests per measure:

1. Slight minus None, and 2. Dramatic minus Slight. H1 holds when both are positive and significant.
3. Human minus AI (H2), by an equivalence test: two one-sided tests of whether it lies inside ±0.224 points, whose p-value is the larger of the two.
4. Human minus AI at None, minus the same at Dramatic (H3), two-sided. A positive value means the penalty shrinks.

Holm's correction holds the chance of any false positive across the twelve at .05.

The bound is half the Study 1 creativity penalty of 0.448 points, so a pass means less than half that penalty reaches a hand-made second work. For lack of other benchmarks it serves all three measures. We set it knowing the Study 1 estimate and question 1's results. A fail means only that the penalty is not shown to be small.

A cumulative-link mixed model, which treats the answers as ordered categories, checks tests 1, 2 and 4.

## 6) Outliers and Exclusions. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

In order, with counts from the export:

1. Survey test runs (none).
2. Unfinished sessions (31; 244 left).
3. Any answer but "Yes, I did" to the seriousness item, a blank included (9; 235 left).
4. A wrong answer to the arithmetic check (8 + 7); a blank passes (none).
5. No recorded condition (none).

The task check ("What is your task in this experiment?") never ended a session, so it is not a criterion; all 235 answered it correctly. Ratings are bounded, so none is an outlier. Two transformativeness items, `1NonFigureNoneTrans` and `1NonFigureMinTrans`, ran on six points with a reworded stem and no definition; their 470 ratings and justifications are dropped.

## 7) Sample Size. How many observations will be collected or what will determine sample size?

Collection is complete: 275 records, 235 kept (122 Human, 113 AI). 228 gave 90 ratings; 7 lack the trial `1FigureMin` and gave 87. That is 21,129 ratings and as many justifications, 20,659 of each after the drop in question 6. The planning document set a sample of 210 and a stop at 250.

## 8) Other. Anything else you would like to pre-register?

Known problems:

- No creativity or essence item carries a definition. Every other study defines creativity, so creativity comparisons across studies are exploratory.
- There is no manipulation check.
- At None the second work is the first unchanged, which makes the questions odd to answer, and test 4 leans on that level.

Departures from the planning document. It planned analyses of variance with Bonferroni-corrected pairwise tests, had no seriousness rule, and dropped anyone missing a condition. Its H2, a creativity penalty at every level, is the taint account. Its H3, a larger modification effect on transformativeness for human sources, predicts a negative test 4. Its H5, more essence change for an AI source at Dramatic, becomes an exploratory source contrast at each level.

Text. No language model or person labels, codes or judges any response. The one use of a pretrained model is a check that turns each response into numbers with a locally stored sentence-embedding model (all-mpnet-base-v2) and compares the resulting grouping with the topics below by the adjusted Rand index (agreement between two groupings beyond chance). The measurement step never sees condition or rating. Study 1's eight word lists, which flag topics such as visible detail, run unchanged. Two checks fixed for every study in the Study 1 registration run on the creativity justifications. One asks how well the words predict rating and condition in participants left out of fitting, by ridge regression (which shrinks each word's weight toward zero). The other asks whether AI-condition participants reuse their own words more, as the share of words two of their explanations have in common. All else is exploratory, including the same steps on the other measures, word pleasantness and concreteness from published norms (Warriner et al., 2013; Brysbaert et al., 2014), topics found without labels, and the words the first check leans on most. Resampling uses the Study 1 seed, 20260421.

## 9) Name. Give a title for this AsPredicted pre-registration.

Study 2: Does an AI-made source lower ratings of a second work made by hand? Analyses of existing data
