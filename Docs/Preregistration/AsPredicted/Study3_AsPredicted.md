# Study 3: AsPredicted registration

## 1) Data collection. Have any data been collected for this study already?

Yes, all of them, from 4 to 9 March 2025. Study 3 was not registered before collection. This is a registration of analyses on existing data, written before any of them is run in the current pipeline. We checked the code by running it with the condition labels shuffled at random across participants, which shows that it runs but yields no result.

In April 2025 we ran a mixed ANOVA (an analysis of variance for factors that vary across and within people) on the 94 finished participant records, nine of which question 6 excludes, and saw its means for each condition and time. A public CogForum DataBlitz talk on 26 September 2025 reported source and time effects on both ratings, and a source-by-time interaction, a gap that changes with time, on effort (p = .043) but not creativity (p = .817). It called the AI-Human difference significant at under 1 and 10 hours for creativity, and at under 1 and 100 hours for effort. No analysis of the justifications was run. We wrote the hypotheses and the plan knowing these results.

## 2) Hypothesis. What's the main question being asked or hypothesis being tested?

Telling participants that the artist prompted an AI system (the AI label) could lower ratings because it signals little work, or because people discount the process itself. Only the first predicts that stated hours shrink the gap until it is negligible at 100 hours.

We predict that the label lowers both ratings and that more stated time raises both. The main question is whether time closes the gap. Two tests decide it: the source-by-time interaction, and an equivalence test of whether the 100-hour gap is small enough to call negligible. A gap significant at one time and not at another does not.

## 3) Dependent variable. Describe the key dependent variable(s), specifying how they will be measured.

Each image gets two five-point ratings, each followed by a required written justification. Creativity: "How much creativity was involved in the production of this work?", defined as "the presence of at least a minimal original, intellectual contribution to the creation of the work". Effort: the same question about effort, with no definition.

They are scored 1 to 5 by position, because the numeric export stores raw choice codes (1, 2, 3, 6 and 7 on `1FigureEff`, the first figure image's effort item).

## 4) Conditions. How many and which conditions will participants be assigned to?

Six: two source conditions, one per person, crossed with three stated times, all seen by each person. The artist Alex either "uses only his graphic design skills and digital sketching tools such as iPad apps and Adobe Photoshop" (Human) or prompts an AI system that generates the artworks (AI).

Before each image, participants read that Alex spent less than 1 hour, 10 hours or 100 hours on it, in the AI condition "developing and inputting prompts into the AI image generator, revising each prompt as he goes". Each participant rates 9 of the 10 images, drawn at random, and a survey script assigns three to each time at random and records them.

## 5) Analyses. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

Each rating gets a linear mixed model, a regression with its own baseline for each participant and each image: rating ~ source × time + (1 | participant) + (1 | image), with time as a three-level factor. Source, time and their interaction get F tests with Satterthwaite degrees of freedom, an approximation for mixed models, and the effect of each factor is averaged over the other. Holm's method corrects the six tests (three per rating) together, holding the chance of any false positive at .05. Estimated marginal means (the model's predicted mean for each condition and time) give the Human minus AI gap at each time and the 100 hours minus under 1 hour contrast.

On each rating, the 100-hour gap passes an equivalence test (two one-sided tests) if its 90 percent confidence interval, the range of gaps compatible with the data, lies inside ±0.224 rating points. That is half the 0.448-point creativity penalty the deposited Study 1 analysis estimated on these images. Removing less than half of it could not fairly be called closing the gap. The test must also pass with random slopes (source varying by image, time by participant), unless that fit cannot estimate all its variance terms, which we then state. We count it as unable to when it stops with an error, does not converge, or is singular, meaning a variance or correlation sits at the edge of its possible range.

On each rating, time closes the gap if the interaction survives correction, the gap is smaller at 100 hours than at under 1 hour, and the equivalence test passes. Smaller compares the Human minus AI gaps with their signs. The gap persists if that test fails and the 95 percent interval at 100 hours lies above zero. Any other pattern is inconclusive.

Cumulative-link mixed models, which treat the answers as ordered categories, check each Holm verdict, testing each term by a Wald chi-square test with Holm's method over the same six tests. Resampling and shuffling use the Study 1 seed, 20260421.

## 6) Outliers and Exclusions. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

In order, with counts from the exports, we remove survey test runs (4), unfinished records (2), any answer but "Yes, I did" to the seriousness item, blanks included (7), and wrong answers to "What does 8+7 equal?" (2). The 85 left of 100 all have a recorded condition and a correct answer to the task question.

Three participants have 17 ratings rather than 18, and the models use every rating present. Two `1FigureEff` ratings carry an answer code absent from the final survey. The option those participants saw was not recorded, so both ratings are treated as missing. Ratings are bounded at 1 and 5, so none is an outlier.

## 7) Sample Size. How many observations will be collected or what will determine sample size?

Quotas, survey counters that cap assignment, allowed 50 participants per source condition. The analysed sample is 85 participants (43 Human, 42 AI), with 1,525 ratings and 1,530 justifications.

## 8) Other. Anything else you would like to pre-register?

In the AI condition the hours go into revising prompts, so a time effect there may be an effect of control over the image, which was not manipulated. All ten images were made with AI, so the Human vignette is a cover story, and no question asked whether participants believed it.

No language model or person labels, codes or judges any response. The one use of a pretrained model is a check that turns each response into numbers with a locally stored sentence-embedding model (all-mpnet-base-v2) and compares the resulting grouping with the topics below by the adjusted Rand index (agreement between two groupings beyond chance). The measurement step never sees condition or rating. The eight Study 1 word lists, which flag topics such as time, skill and machines, run unchanged. So do the two checks the Study 1 registration fixes for every study, on both ratings. One asks how well the words predict the rating and the condition in participants left out of fitting, by ridge regression (which shrinks each word's weight toward zero). The other predicts that participants under the AI label reuse their own words across images more than Human participants do, relative to others writing about the same image, with Holm correction across the two ratings.

Everything else is exploratory: comparisons built on the word lists, word pleasantness and concreteness from published ratings (Warriner, Kuperman & Brysbaert, 2013; Brysbaert, Warriner & Kuperman, 2014), topics found by a model given no labels, and the words that carry the rating prediction. Each justification follows its rating, so none is read as its cause.

## 9) Name. Give a title for this AsPredicted pre-registration.

Stated time and the AI-source gap in judgments of original artworks (Study 3, analyses of existing data).
