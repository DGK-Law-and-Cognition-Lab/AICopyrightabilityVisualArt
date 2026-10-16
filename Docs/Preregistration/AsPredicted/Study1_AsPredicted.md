# Study 1: AsPredicted registration

## 1) Data collection. Have any data been collected for this study already?

Yes: collection ran from 25 February to 3 March 2025. This is a postregistration, written after collection and analysis. Study 1 was not registered before collection, and our CogSci 2025 paper predates it.

- April 2025: we ran Welch t-tests (which allow unequal variances) on participant means, and analyses of variance comparing means by condition and image kind, on the 111 participants kept under question 6. The first author showed Study 1 at a lab meeting on 18 April.
- 26 September 2025: the three authors' public DataBlitz talk showed those t-tests, with Cohen's d (a difference in standard deviations) of -0.66 for creativity and -1.18 for effort.
- November 2025: we ran topic models (word groupings found without labels) and sentiment scores on the justifications.
- By April 2026: a language model had coded the justifications, with the condition label (and for sentiment the rating) in its prompts. A manuscript draft reported means, d, robustness checks and these text results. None of this text work is used here.
- Before 7 September 2026: exploratory work predicted the ratings from the text by another method.
- September and October 2026: we ran the code described here, a code review of 8 September summarised its results for the first author, and we revised and reran it. Section 8 of the long registration (`Docs/Preregistration/Study1_Preregistration.md`) lists decisions made with those estimates known.

## 2) Hypothesis. What's the main question being asked or hypothesis being tested?

With the image held constant, does an AI-prompting label lower judged creativity and effort, and which does it lower more?

- H1. AI attribution lowers both ratings.
- H2. The drop is larger for effort, a ground of protection copyright rejects (*Feist v. Rural Telephone*, 1991), than for creativity.
- H3. The drop is the same for figurative and non-figurative images.
- H4. Under AI attribution, ratings vary more between participants and less within a participant across images, as if one discount covered every image.

## 3) Dependent variable. Describe the key dependent variable(s), specifying how they will be measured.

Two five-point items per image ask "How much creativity (effort) was involved in the production of this work?" The creativity item defines creativity as "the presence of at least a minimal original, intellectual contribution to the creation of the work." Answers run from "No creativity (effort) involved" to "A great deal of creativity (effort) involved", scored 1 to 5 by position (one exception, question 8). A required justification follows each rating.

## 4) Conditions. How many and which conditions will participants be assigned to?

Two, between participants, balanced by a Qualtrics randomizer with quotas of 60 each. The artist Alex "uses his graphic design skills and digital sketching tools" (Human) or "develops and inputs prompts into an artificial intelligence (AI) system" (AI). Everyone rates the same ten AI-made images in random order, five showing a human or humanoid figure, so the Human vignette is a cover story.

## 5) Analyses. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

Each rating gets a linear mixed model, a regression giving each participant and image its own baseline: `rating ~ attribution * image_kind + (1 | participant) + (1 | image)`, with Satterthwaite degrees of freedom (an approximation for such models).

- H1: Human minus AI on each rating, averaged over image kind. Both must hold.
- H2: the attribution by dimension term of a joint model of both ratings, with each participant's effort-creativity gap free to vary. An ordinal version (answers as ordered categories) must agree in sign and significance.
- H3: the attribution by image kind term. It is supported if not significant and its 90 percent confidence interval lies inside ±0.20 points (an equivalence test; the bound was set with the estimates known). This must also hold with effects free to vary by image and participant, unless that fit is singular (cannot estimate all its variances). A failure is uninformative if the test's power, its chance of passing at a true difference of zero, is under 80 percent.
- H4: AI over Human ratios of between-participant and of residual (within-participant) variance, with 95 percent intervals from 1,000 resamples of participants within condition. H4 holds on a rating if the first interval lies above 1 and the second below 1.

Holm's correction holds the chance of any false positive at .05 across four tests: both H1 contrasts, H2, and a likelihood-ratio test of whether between-participant variance differs by condition. Fits that do not reach a stable solution yield no *p*-value or verdict.

## 6) Outliers and Exclusions. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

In order, with export counts: survey test runs (2), unfinished records (3), and anything but "Yes, I did", blank included, to "Did you complete this experiment seriously throughout (without responding randomly)?" (3). That leaves 111 of 119. The attention check let everyone continue, so it removes no one. Ratings are bounded, so none is an outlier.

## 7) Sample Size. How many observations will be collected or what will determine sample size?

Collection is complete: 111 participants (56 Human, 55 AI), each giving all 20 ratings and justifications, 2,220 of each.

## 8) Other. Anything else you would like to pre-register?

The long registration governs where this summary is silent. Every robustness check reports the H1 contrast. Cohen's *d* uses participant means and 10,000 bootstrap resamples, seed 20260421.

On the first figure image's effort item, 4 reads "A lot of effort involved" and 5 "Significant effort involved"; it is scored by position and dropped in a sensitivity refit. Image order was not recorded, no question checked that participants registered the label, and the AI vignette is one sentence longer.

No language model or person labels, codes or judges any response. The one use of a pretrained model is a check that turns each text into numbers with a locally stored sentence-embedding model (all-mpnet-base-v2) and compares the resulting grouping with the topic model's by the adjusted Rand index (agreement between two groupings beyond chance). Eight fixed word lists measure the text blind to condition and rating. We wrote them by reading responses with both hidden, and settled four parts after reading results by condition.

- Five tests of what "effort" and "creativity" meant form one exploratory family, Benjamini-Hochberg corrected (which limits the expected share of false positives).
- Two checks run in every study: ridge regression (shrinking word weights toward zero) predicting rating and condition for participants left out of fitting, and a test, Holm-corrected across the two ratings, of the prediction that AI-condition participants reuse their own words more.
- Exploratory: the tone and concreteness of the words, from published norms that give average ratings for single words (Warriner et al., 2013; Brysbaert et al., 2014). So are the topic models and the check on them. We also report which words predictions lean on.

Justifications followed ratings, so none is read as a cause.

## 9) Name. Give a title for this AsPredicted pre-registration.

Study 1: Does an AI label lower judged creativity and effort? (Postregistration)
