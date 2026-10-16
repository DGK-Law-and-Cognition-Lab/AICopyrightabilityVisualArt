# Study 5: AsPredicted registration

## 1) Data collection. Have any data been collected for this study already?

Yes. All data were collected from 21 October to 2 November 2025, after our CogSci 2025 paper and our DataBlitz talk of 26 September 2025, so neither reports Study 5. Nothing was registered before collection. This registers analyses of existing data, written before any of them is run in the current pipeline. We checked the code by running it with the condition labels shuffled at random across participants, which shows that it runs but yields no result.

A November 2025 manuscript draft reported a sample size (257, which our exclusions do not reproduce), age and gender, and no rating result. In 2026, coding sessions in which an AI assistant worked for the first author displayed the exclusion counts and cell sizes (7 September), one participant's three ratings and justifications for one trial (22 September), and a pooled count of answers in the six-point items' extra category (6 October). No rating has been summarised by condition, and no outcome model has been fitted.

## 2) Hypothesis. What's the main question being asked or hypothesis being tested?

Alex makes each second work himself from a first artwork, and participants are told he spent less than 1 hour, 10 hours or 100 hours on it. We call this editing time. The pictures are the same at every level. If people credit labour, the "sweat of the brow" that *Feist v. Rural Telephone* (1991) refused to protect, more hours should raise ratings. If they judge what the picture shows, editing time should not matter. We predict neither.

We also ask whether editing time changes the source penalty, the lower rating a second work gets when its first artwork is attributed to AI. If editing counts as Alex's own contribution, the penalty should shrink as hours rise.

## 3) Dependent variable. Describe the key dependent variable(s), specifying how they will be measured.

Each participant rates 18 second works, 54 ratings in all: how transformative the second work is compared to the first, how much the essence of the first changed in it, and how much creativity went into producing it. Each item shows its definition and five labelled points (six on two items; question 8), scored by position because the numeric export stores raw choice codes. A required written justification follows each rating.

## 4) Conditions. How many and which conditions will participants be assigned to?

Six cells, between participants: source process crossed with editing time, assigned once by a randomizer that balances the cells. Alex makes the first artwork with graphic design and sketching tools (Human) or by entering prompts into an AI system (AI), and the second works with his own tools.

Within participants, each person sees 6 of the 10 sources, 3 of each image kind (with or without a human or humanoid figure). Each is paired in random order with three second works: None (unchanged), Slight (colour and contrast adjustments) and Dramatic (substantial hand changes). A source time, the hours spent on the first artwork, is also stated at the same three levels, two sources each.

## 5) Analyses. Specify exactly which analyses you will conduct to examine the main question/hypothesis.

Each rating gets a linear mixed model, a regression with an estimated adjustment for each participant and each source image: rating ~ source × editing time × modification + image kind + (1 | participant) + (1 | image). F tests use Satterthwaite degrees of freedom, an approximation for mixed models. Six tests are confirmatory: the editing-time effect, averaged over the other factors, and the source-by-editing-time interaction, on each rating. Holm's method corrects them together, holding the chance of any false positive at .05.

An effect is called absent or small only if an equivalence test, by two one-sided tests, puts its 90 percent confidence interval inside a bound:

- Editing time (100 hours minus less than 1 hour): the size of the same contrast for source time on creativity in the registered Study 3 model. It is fixed before any Study 5 model is fitted, since in Study 3 too the hours went into the rated work. A pass means smaller than Study 3's effect, not zero.
- Source (Human minus AI at each modification level, from estimated marginal means, the model's predicted cell means): ±0.224 points, half the 0.448-point creativity penalty Study 1 estimated on these images. A pass means less than half that penalty reaches the second work.

A test neither significant nor equivalent is inconclusive. For editing time, significant means the Holm-corrected F test across its three levels, with the 100 hours minus less than 1 hour contrast reported beside it. The nine source tests, three ratings at three modification levels, are each judged at .05 without correction. Cumulative-link mixed models, which treat answers as ordered categories, check each Holm verdict, testing each term by a Wald chi-square test with Holm's method over the same six tests.

## 6) Outliers and Exclusions. Describe exactly how outliers will be defined and handled, and your precise rule(s) for excluding observations.

In order, with counts from the exports, we remove:

1. Survey test runs (none).
2. Unfinished records (17).
3. Seriousness answers other than "Yes, I did", blanks included (16).
4. Wrong answers to "What does 8+7 equal?" (1). A blank would pass; none occurs.
5. Records with no condition (2, neither with ratings).

That leaves 223 of 259, each with 54 ratings and justifications. The task attention check removes no one; all 223 answered it correctly. Ratings are bounded, so none is an outlier, and no one is removed for what they wrote.

## 7) Sample Size. How many observations will be collected or what will determine sample size?

Six quotas, survey counters that cap assignment, limited each cell to 40. The AI cells hold 35, 38 and 38 participants and the Human cells 37, 37 and 38, at less than 1, 10 and 100 hours. The 223 give 12,042 ratings and as many justifications.

## 8) Other. Anything else you would like to pre-register?

Source time was shown but not recorded. The script that records each trial's time reads a field named ArtistHr, which the Study 5 survey had renamed ArtistHr_Source, so the six trial-time fields, Image1_Time to Image6_Time, are blank in the numeric, label and archived exports. Another script gave each participant two sources per level, so source time is balanced within participants and cannot confound the between-participant factors. It enters no model. The ArtistHr_Source value stored in each record is only the last level drawn, not a condition. No trial-level question about source time can be answered.

Two transformativeness items (1NonFigureNoneTrans, 1NonFigureMinTrans) add "Somewhat transformative" as a sixth point. Their 274 ratings enter only a second analysis that rescales every item from 0 to 1. It repeats the six Holm tests and runs no equivalence test, because both bounds are in rating points. Three essence answer labels have wording slips. All ten sources were made with AI, so the Human vignette is a cover story, and no question checks whether participants believed it.

Text. No language model or person labels, codes or judges any response in these analyses. The one use of a pretrained model is a check that turns each response into numbers with a locally stored sentence-embedding model (all-mpnet-base-v2) and compares the resulting grouping with the topics below by the adjusted Rand index (agreement between two groupings beyond chance). The measurement step never sees condition or rating. Study 1's eight fixed word lists, flagging topics such as visible detail, time, skill and machines, run unchanged on every justification. Two checks from every study are registered for creativity. First, ridge regression, which shrinks each word's weight toward zero, predicts rating and source condition from the words of participants left out of fitting. Second, we predict that AI-condition participants reuse their own words across their 18 justifications more than Human-condition participants, relative to others writing about the same second work. Exploratory: a count of Human-condition participants who write that a machine made the work; emotional tone and concreteness from published word ratings (Warriner et al., 2013; Brysbaert et al., 2014); topics found by a model given no labels; and the words carrying the rating prediction. Random steps use seeds 20260421 in R and 20260903 in the text code.

## 9) Name. Give a title for this AsPredicted pre-registration.

Study 5: Does stated editing time change judgments of a second work, or its AI-source penalty? Analyses of existing data
