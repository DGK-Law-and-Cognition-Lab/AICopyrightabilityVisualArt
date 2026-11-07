# Does the AI label change how closely explanations describe the picture?
#
# Exploratory. Specified on 6 November 2026, after every registered result was known; changes
# no registered verdict. Step 1 (ImageGrounding_01_Measure.py) scored each explanation, blind to
# the label and the rating, with CLIP: grounding is the explanation's similarity to its own
# picture minus its average similarity to the other nine artworks at the same edit level. This
# step joins the label, the conditions and the rating, and asks:
#
#   1. Validity: how often is an explanation's own picture the one CLIP places closest to it, out
#      of ten (chance 1 in 10)? Reported by study and edit level, with an interval from 2,000
#      resamples of participants.
#   2. On originals (paper Studies 1 and 2): is grounding lower under the AI label, which would mean
#      that AI-label explanations describe the picture less?
#   3. On secondary works (paper Studies 3 to 5), at Slight and Dramatic: is grounding lower under
#      the AI label? At None the picture is the original shown again and explanations mostly say
#      that nothing changed (validity below), so None is left out.
#
# Each question is fitted per study and question with a linear mixed model, grounding (in standard
# deviations of that study and question) ~ the study's registered terms (label with stimulus type
# in paper Study 1, with stated time in Study 2, with edit level and image kind in Study 3, with
# edit level and stated source time in Study 4, with edit level and stated editing time, plus image
# kind, in Study 5) + the log of the number of words CLIP read (at most 77 tokens) + (1 | participant)
# + (1 | artwork). Two further versions: with the rating added, to check that a difference is not
# only a restatement of the rating; and without mentions, the main model fitted only to the
# explanations that do not mention prompting or a machine (the shared word list says_prompt, from
# each study's text measures), so that explanations that talk about the machine instead of the
# picture cannot carry the difference. Holm's correction runs over each study's label tests in the
# main version. The step's other score, edit pull (similarity to the edited
# picture minus similarity to the original), is described but not modelled: its validity check
# fails (below).
#
# Run from this folder:  Rscript ImageGrounding_02_Analysis.R

suppressPackageStartupMessages({
  library(readr); library(dplyr); library(tidyr); library(tibble)
  library(lme4); library(lmerTest); library(emmeans); library(digest)
})

HERE <- normalizePath(getwd(), mustWork = TRUE)
stopifnot(file.exists(file.path(HERE, "ImageGrounding_02_Analysis.R")))
PIPELINE <- normalizePath(file.path(HERE, "..", ".."), mustWork = TRUE)
TAB <- file.path(HERE, "tables")
STATUS <- paste("exploratory; specified on 6 November 2026, after every registered result was known;",
                "changes no registered verdict")
PAPER <- c(`1` = 1L, `2` = 3L, `3` = 2L, `4` = 4L, `5` = 5L)
set.seed(20260421)  # the seed Study 1's registration names for resampling
# Satterthwaite degrees of freedom for every contrast, as in the registered models.
emm_options(lmer.df = "satterthwaite", lmerTest.limit = 1e6)

scores_path <- file.path(HERE, "nlp", "image_grounding_scores.csv")
man <- read_csv(file.path(TAB, "image_grounding_measure_run_manifest.csv"), show_col_types = FALSE)
if (!identical(man$sha256[man$file == "nlp/image_grounding_scores.csv"], digest(file = scores_path, algo = "sha256"))) {
  stop("nlp/image_grounding_scores.csv is not the file step 1 wrote")
}
scores <- read_csv(scores_path, show_col_types = FALSE, col_types = cols(id = col_character(), .default = col_guess()))

long_of <- function(n) {
  path <- file.path(PIPELINE, paste("Study", n), sprintf("study%d_long_with_text.csv", n))
  stopifnot(identical(man$sha256[man$file == file.path("..", "..", paste("Study", n), basename(path))],
                      digest(file = path, algo = "sha256")))
  d <- read_csv(path, show_col_types = FALSE, guess_max = 1e5, col_types = cols(id = col_character()))
  if (n == 1) {
    d <- d %>% mutate(artwork = sub("^(Figure|NonFigure)_(\\d)$", "\\2\\1", stimulus_id), level = "original",
                      label = Type)
  } else if (n == 3) {
    d <- d %>% mutate(artwork = stimulus_id, level = "original", label = Type)
  } else {
    d <- d %>% mutate(artwork = sub("_(None|Slight|Dramatic)$", "", work_id),
                      level = sub("^.*_", "", work_id),
                      label = if (n == 4) label else source)
  }
  if (!"k_points" %in% names(d)) d$k_points <- 5
  d$stimulus_key <- if (n %in% c(1, 3)) d$stimulus_id else d$work_id
  tm <- read_csv(file.path(PIPELINE, paste("Study", n), "nlp", sprintf("study%d_text_measures.csv", n)),
                 show_col_types = FALSE, col_types = cols(.default = col_character())) %>%
    transmute(id, stimulus_key = stimulus_id, dimension, mentions_prompt = says_prompt == "True")
  d <- d %>% left_join(tm, by = c("id", "stimulus_key", "dimension"), relationship = "one-to-one")
  d %>% filter(!is.na(rating), k_points == 5) %>%
    transmute(study_pipeline = n, id, artwork, level, dimension, label, rating, mentions_prompt,
              stimulus_type = if (n == 1) stimulus_type else NA_character_,
              image_kind = if (n %in% c(2, 5)) image_kind else NA_character_,
              time = if (n == 3) time else NA_character_,
              source_time = if (n == 4) source_time else NA_character_,
              editing_time = if (n == 5) editing_time else NA_character_)
}
d <- bind_rows(lapply(1:5, long_of)) %>%
  inner_join(scores %>% select(study_pipeline, id, artwork, level, dimension, grounding, edit_pull, hit,
                               n_tokens_kept),
             by = c("study_pipeline", "id", "artwork", "level", "dimension"), relationship = "one-to-one") %>%
  mutate(study_paper = PAPER[as.character(study_pipeline)], label = factor(label, levels = c("Human", "AI")))
counts <- d %>% count(study_paper, label, name = "explanations")
stopifnot(nrow(d) > 40000, !anyNA(d$mentions_prompt))

# 1. Validity ----------------------------------------------------------------------------------
boot_share <- function(x, id, B = 2000) {
  ids <- unique(id); per <- tapply(x, id, sum); n <- tapply(x, id, length)
  stats <- replicate(B, { s <- sample(ids, replace = TRUE); sum(per[s]) / sum(n[s]) })
  unname(quantile(stats, c(.025, .975)))
}
validity <- d %>% group_by(study_paper, level) %>%
  group_modify(~ { ci <- boot_share(.x$hit, .x$id); tibble(hit_rate = mean(.x$hit), ci_lo = ci[1], ci_hi = ci[2],
                    explanations = nrow(.x), edit_pull_mean = mean(.x$edit_pull, na.rm = TRUE)) }) %>%
  ungroup() %>% mutate(analysis_status = STATUS, chance = 0.1, .before = 1)
write_csv(validity, file.path(TAB, "image_grounding_validity.csv"))

# 1b. The same hit rate under each label: how often CLIP found an explanation's own picture among
# the ten, for Human-label and AI-label explanations separately, with an interval from 2,000
# resamples of participants. Descriptive; the label tests below use grounding. Secondary works
# pool the Slight and Dramatic edits.
hits_by_label <- d %>% filter(level != "None") %>%
  mutate(level = ifelse(level == "original", "original", "Slight and Dramatic")) %>%
  group_by(study_paper, dimension, level, label) %>%
  group_modify(~ { ci <- boot_share(.x$hit, .x$id); tibble(hit_rate = mean(.x$hit), ci_lo = ci[1], ci_hi = ci[2],
                    explanations = nrow(.x), participants = n_distinct(.x$id)) }) %>%
  ungroup() %>% mutate(label = as.character(label), analysis_status = STATUS, chance = 0.1, .before = 1)
write_csv(hits_by_label, file.path(TAB, "image_grounding_hits_by_label.csv"))

# 2-3. Label effects ---------------------------------------------------------------------------
fit_one <- function(dd, study, dim, with_rating) {
  dd <- dd %>% mutate(g = as.numeric(scale(grounding)), lw = as.numeric(scale(log(n_tokens_kept))),
                      rz = as.numeric(scale(rating)))
  terms <- c(`1` = "label * stimulus_type", `2` = "label * time", `3` = "label * level * image_kind",
             `4` = "label * level * source_time", `5` = "label * level * editing_time + image_kind")[[as.character(study)]]
  f <- as.formula(paste("g ~", terms, "+ lw", if (with_rating) "+ rz" else "", "+ (1 | id) + (1 | artwork)"))
  m <- lmer(f, data = dd, REML = TRUE, control = lmerControl(optimizer = "bobyqa"),
            contrasts = Filter(Negate(is.null), list(stimulus_type = if (study == 1) "contr.sum",
                                                     image_kind = if (study %in% c(3, 5)) "contr.sum")))
  em <- if (study %in% c(1, 2)) emmeans(m, ~ label) else emmeans(m, ~ label | level)
  ct <- summary(contrast(em, list(`AI minus Human` = c(-1, 1))), infer = TRUE) %>% as_tibble()
  if (!"level" %in% names(ct)) ct$level <- "original"
  avg <- NULL
  if (study %in% c(3, 4, 5)) {
    avg <- summary(contrast(emmeans(m, ~ label), list(`AI minus Human` = c(-1, 1))), infer = TRUE) %>%
      as_tibble() %>% mutate(level = "Slight and Dramatic, averaged")
  }
  bind_rows(ct, avg) %>% transmute(level = as.character(level), estimate_sd = estimate, std_error = SE, df,
                                   ci95_low = lower.CL, ci95_high = upper.CL, p = p.value,
                                   singular = isSingular(m))
}
effects <- list()
for (sp in c(1, 3, 2, 4, 5)) {
  for (dim in sort(unique(d$dimension[d$study_pipeline == sp]))) {
    dd <- d %>% filter(study_pipeline == sp, dimension == dim, level != "None")
    for (version in c("main", "rating added", "without mentions")) {
      dv <- if (version == "without mentions") dd %>% filter(!mentions_prompt) else dd
      r <- fit_one(dv, PAPER[as.character(sp)], dim, version == "rating added")
      effects[[length(effects) + 1]] <- r %>% mutate(study_pipeline = sp, study_paper = PAPER[as.character(sp)],
                                                     measure = dim, version = version,
                                                     explanations = nrow(dv), .before = 1)
    }
  }
}
effects <- bind_rows(effects) %>% group_by(study_paper, version) %>%
  mutate(p_holm = ifelse(version == "main" & level %in% c("original", "Slight and Dramatic, averaged"),
                         p.adjust(ifelse(level %in% c("original", "Slight and Dramatic, averaged"), p, NA), "holm"),
                         NA_real_)) %>%
  ungroup() %>% mutate(analysis_status = STATUS, outcome = "grounding, in SD of the study and question",
                       contrast = "AI minus Human", .before = 1)
write_csv(effects, file.path(TAB, "image_grounding_label_effects.csv"))
write_csv(counts %>% mutate(analysis_status = STATUS, .before = 1), file.path(TAB, "image_grounding_samples.csv"))
writeLines(capture.output(sessionInfo()), file.path(TAB, "image_grounding_analysis_sessionInfo.txt"))
cat("wrote validity, label effects and samples to tables/\n")
