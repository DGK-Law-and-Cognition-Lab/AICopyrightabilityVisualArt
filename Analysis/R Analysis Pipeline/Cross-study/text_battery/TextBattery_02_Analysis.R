# Text battery, step 2: what participants wrote, in all five studies
#
# Exploratory. Specified on 31 October 2026, after every registered result was
# known. No registration names it, and it changes no registered verdict.
#
# The same three analyses of the written explanations, in every study:
#   1. What the explanations named. The share of explanations that carry each
#      of six word-list flags (visible detail, time, skill, the idea, prompting
#      or a machine, a machine making the work), under each label, and in
#      Studies 2, 4 and 5 at each modification level, with 95 percent
#      intervals from 2,000 resamples of participants within each label.
#   2. The words that set the label groups apart. Monroe, Colaresi and Quinn's
#      log-odds ratio with an informative Dirichlet prior, AI-label
#      explanations against Human-label explanations, for each study and
#      question, over every content word that step 1 counted.
#   3. Words linked to ratings within a label. For each flag, how much higher
#      or lower the rating was when the explanation carried the flag, among
#      participants who saw the same label, from a linear mixed model with the
#      study's registered design, and whether that link differs between the
#      labels. Three further versions: the link within one person's own
#      explanations, the link holding word count constant, and, for the four
#      flags with a polarity reading, claimed and denied mentions apart.
#
# The flags are those each study's text step computed blind to the label and
# the rating, by the eight rules every study applies unchanged
# (Study N/nlp/studyN_text_measures.csv). A flag records a topic, not an
# endorsement: "not much detail" is detail talk.
#
# Study 5's sample is its analyzed sample of 197: the 223 of the registration
# less the 26 who had completed an earlier study (Study 5/Study5_01_Quant.Rmd,
# exclusion step 6).
#
# Before it fits the rating models, the script checks that its code
# reproduces Study 1's deposited tables: the distinctive words of high against
# low ratings, the Human-label models of rating on a flag, and the shares of
# explanations that carry a flag. It stops if any check fails.
#
# Study numbers follow the pipeline's folders. The paper swaps two of them:
# the pipeline's Study 2 is the paper's Study 3, and its Study 3 is the
# paper's Study 2. Every table gives both.
#
# No table holds a participant code or any value that belongs to one
# participant.
#
# Run from this folder, after TextBattery_01_Measure.py:
#   Rscript TextBattery_02_Analysis.R

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(tibble)
  library(lme4)
  library(lmerTest)
  library(parallel)
})

HERE <- normalizePath(getwd(), mustWork = TRUE)
stopifnot(file.exists(file.path(HERE, "TextBattery_02_Analysis.R")))
PIPELINE <- normalizePath(file.path(HERE, "..", ".."), mustWork = TRUE)
source(file.path(PIPELINE, "shared", "R", "fit_status.R"))
source(file.path(PIPELINE, "shared", "R", "qualtrics_import.R"))
PROJECT_ROOT <- find_project_root(start = PIPELINE)
TAB_DIR <- file.path(HERE, "tables")
dir.create(TAB_DIR, showWarnings = FALSE)

ANALYSIS_STATUS <- paste("exploratory; specified on 31 October 2026, after every registered",
                         "result was known; changes no registered verdict")
SEED <- 20260421L               # the seed Study 1's registration names for resampling
B <- 2000L                      # resamples of participants
MIN_FLAGGED_RESPONSES <- 20L    # a link is estimated under a label only when the flag
MIN_FLAGGED_PEOPLE <- 10L       #   appears in this many explanations from this many people
KEYNESS_ALPHA0 <- 500           # Study 1's prior weight (section 8 of its text notebook)
KEYNESS_MIN_TOTAL <- 5L         # Study 1's floor: words used fewer times are not scored
N_WORKERS <- max(1L, min(8L, parallel::detectCores() - 1L))
if (.Platform$OS.type == "windows") N_WORKERS <- 1L

STUDIES <- tibble(study_pipeline = 1:5,
                  study_paper = c(1L, 3L, 2L, 4L, 5L),
                  part = c("originals", "second works", "originals", "second works",
                           "second works"))
N_PEOPLE <- c(111L, 235L, 85L, 117L, 197L)
WORD_FLAGS <- c(says_detail = "visible detail", says_time = "time", says_skill = "skill",
                says_concept = "the idea", says_prompt = "prompting or a machine",
                says_machine_made = "a machine making the work")
# The agency rule's flags (agency/agency_rule.py), applied by step 1 once the
# rule was frozen; each is reported with the result of its validation test.
AGENCY_FLAGS <- c(person_maker = "a person made or changed it",
                  machine_maker = "a machine made or changed it",
                  agentless_making = "made or changed, with no doer named")
FLAGS <- c(WORD_FLAGS, AGENCY_FLAGS)
POLARITY <- c(says_detail = "detail_polarity", says_time = "time_polarity",
              says_skill = "skill_polarity", says_concept = "concept_polarity")
# Each study's registered fixed effects, with its label column named label.
DESIGN <- c(`1` = "label * stimulus_type",
            `2` = "label * modification * image_kind",
            `3` = "label * time",
            `4` = "label * source_time * modification",
            `5` = "label * editing_time * modification + image_kind")
FACTOR_LEVELS <- list(
  label = c("Human", "AI"),
  stimulus_type = c("NonFigure", "Figure"),
  image_kind = c("NonFigure", "Figure"),
  modification = c("None", "Slight", "Dramatic"),
  time = c("under 1 hour", "10 hours", "100 hours"),
  source_time = c("less than 1 hour", "10 hours", "100 hours"),
  editing_time = c("less than 1 hour", "10 hours", "100 hours"))
SAMPLE_ALL <- "all analyzed participants"

# ---------------------------------------------------------------------------
# 1. Inputs, and the checks that they are the files the real runs wrote
# ---------------------------------------------------------------------------
in_study <- function(n, ...) file.path(PIPELINE, paste("Study", n), ...)
IN <- c(
  wordcounts = file.path(HERE, "nlp", "text_battery_wordcounts.csv"),
  agency = file.path(HERE, "nlp", "text_battery_agency.csv"),
  agency_scores = file.path(HERE, "agency", "tables", "agency_validation_scores.csv"),
  measure_manifest = file.path(TAB_DIR, "text_battery_measure_run_manifest.csv"),
  study1_keyness_effort = in_study(1, "tables", "text_keyness_effort.csv"),
  study1_keyness_creativity = in_study(1, "tables", "text_keyness_creativity.csv"),
  study1_effort_detail_lmm = in_study(1, "tables", "study1_text_effort_detail_lmm.csv"),
  study1_effort_other_lmm = in_study(1, "tables", "study1_text_effort_other_lmm.csv"),
  study1_creativity_concept_lmm = in_study(1, "tables", "study1_text_creativity_concept_lmm.csv"),
  study1_creativity_execution_lmm = in_study(1, "tables", "study1_text_creativity_execution_lmm.csv"),
  study1_effort_prevalence = in_study(1, "tables", "study1_text_effort_prevalence.csv"),
  study1_prompt_by_arm = in_study(1, "tables", "study1_text_prompt_by_arm.csv"))
for (n in 1:5) {
  IN[[sprintf("study%d_long", n)]] <- in_study(n, sprintf("study%d_long_with_text.csv", n))
  IN[[sprintf("study%d_measures", n)]] <- in_study(n, "nlp", sprintf("study%d_text_measures.csv", n))
  IN[[sprintf("study%d_quant_manifest", n)]] <- in_study(n, "tables", sprintf("study%d_quant_run_manifest.csv", n))
  IN[[sprintf("study%d_text_manifest", n)]] <- in_study(n, "tables", sprintf("study%d_text_run_manifest.csv", n))
}

run <- start_run_record(IN, file.path(TAB_DIR, "text_battery_analysis_run_manifest.csv"), HERE)
write_run_inputs(run, file.path(TAB_DIR, "text_battery_analysis_run_inputs.csv"))
# Every output of the previous run is deleted now, so a run that stops part
# way leaves none of them behind.
OUTPUTS <- c("text_battery_input_checks.csv", "text_battery_samples.csv",
             "text_battery_prevalence.csv", "text_battery_keyness.csv",
             "text_battery_reproduction_checks.csv", "text_battery_rating_links.csv",
             "text_battery_analysis_package_versions.csv",
             "text_battery_analysis_sessionInfo.txt")
run_clear_outputs(run, file.path(TAB_DIR, OUTPUTS))
OUT <- function(name) {
  stopifnot(name %in% OUTPUTS)
  file.path(TAB_DIR, name)
}
sha <- function(path) unname(tools::sha256sum(path))
read_chr <- function(path) {
  read_csv(path, col_types = cols(.default = col_character()), na = character(),
           progress = FALSE)
}
check <- function(study, quantity, expected, observed) {
  tibble(study_pipeline = study, quantity = quantity, expected = as.character(expected),
         observed = as.character(observed),
         pass = identical(as.character(expected), as.character(observed)))
}
# The long data file is the one its study's real run wrote when its checksum
# equals the one that run's manifest lists (as Cross-study/CrossStudy_Penalty_Curve.Rmd
# checks); the measures file, when its checksum equals the one the study's text
# run manifest lists.
quant_listed <- function(n) {
  m <- read_chr(IN[[sprintf("study%d_quant_manifest", n)]])
  row <- m[m$file == sprintf("study%d_long_with_text.csv", n), ]
  nrow(row) == 1 && isTRUE(as.logical(row$written_this_run)) &&
    identical(row$sha256, sha(IN[[sprintf("study%d_long", n)]]))
}
text_listed <- function(n) {
  m <- read_chr(IN[[sprintf("study%d_text_manifest", n)]])
  row <- m[m$file == sprintf("nlp/study%d_text_measures.csv", n), ]
  nrow(row) == 1 && identical(row$sha256, sha(IN[[sprintf("study%d_measures", n)]]))
}
measure_manifest <- read_chr(IN[["measure_manifest"]])
step1_listed <- function(file, path) {
  row <- measure_manifest[measure_manifest$file == file, ]
  nrow(row) == 1 && identical(row$sha256, sha(path))
}
input_checks <- bind_rows(
  lapply(1:5, function(n) bind_rows(
    check(n, "long data file equals the one the study's real run manifest lists", TRUE,
          quant_listed(n)),
    check(n, "text measures equal the ones the study's text run manifest lists", TRUE,
          text_listed(n)),
    check(n, "step 1 read this long data file", TRUE,
          step1_listed(sprintf("Study %d/study%d_long_with_text.csv", n, n),
                       IN[[sprintf("study%d_long", n)]])))),
  check(NA, "the word counts are the ones step 1 wrote", TRUE,
        step1_listed("Cross-study/text_battery/nlp/text_battery_wordcounts.csv", IN[["wordcounts"]])),
  check(NA, "the agency flags are the ones step 1 wrote", TRUE,
        step1_listed("Cross-study/text_battery/nlp/text_battery_agency.csv", IN[["agency"]]))) %>%
  mutate(analysis_status = ANALYSIS_STATUS)
write_csv(input_checks, OUT("text_battery_input_checks.csv"))
if (!all(input_checks$pass)) {
  print(as.data.frame(input_checks[!input_checks$pass, c("study_pipeline", "quantity")]))
  stop("An input is not the file its run wrote; see text_battery_input_checks.csv.")
}

# ---------------------------------------------------------------------------
# 2. The explanations, with their label, design, rating and flags
# ---------------------------------------------------------------------------
agency <- read_chr(IN[["agency"]])
read_study <- function(n) {
  long <- read_chr(IN[[sprintf("study%d_long", n)]])
  d <- switch(as.character(n),
    "1" = long %>% transmute(id, stimulus_id, label = Type, image = stimulus_id, stimulus_type,
                             dimension, rating, k_points = "5", label_mode = "real", response_text),
    "2" = long %>% transmute(id, stimulus_id = work_id, label = source, image, image_kind,
                             modification, dimension, rating, k_points, label_mode, response_text),
    "3" = long %>% transmute(id, stimulus_id, label = Type, image = stimulus_id, time,
                             dimension, rating, k_points, label_mode = "real", response_text),
    "4" = long %>% transmute(id, stimulus_id = work_id, label, image = source, source_time,
                             modification, image_kind, dimension, rating, k_points, label_mode,
                             response_text),
    "5" = long %>% transmute(id, stimulus_id = work_id, label = source, image, image_kind,
                             editing_time, modification, dimension, rating, k_points, label_mode,
                             response_text))
  measures <- read_chr(IN[[sprintf("study%d_measures", n)]]) %>%
    select(id, stimulus_id, dimension, n_words, all_of(names(WORD_FLAGS)), all_of(unname(POLARITY))) %>%
    inner_join(agency %>% filter(study == as.character(n)) %>% select(-study),
               by = c("id", "stimulus_id", "dimension"), relationship = "one-to-one",
               na_matches = "never")
  # One explanation is one row on each side, joined one to one.
  j <- inner_join(d, measures, by = c("id", "stimulus_id", "dimension"),
                  relationship = "one-to-one", na_matches = "never")
  stopifnot(nrow(j) == nrow(d), nrow(j) == nrow(measures))
  j <- j %>% mutate(across(all_of(names(FLAGS)), as.logical),
                    rating = as.numeric(rating), k_points = as.integer(k_points),
                    n_words = as.integer(n_words),
                    usable = grepl("[A-Za-z]", response_text),
                    analyzed = usable & k_points == 5L & !is.na(rating))
  for (f in intersect(names(FACTOR_LEVELS), names(j))) {
    stopifnot(all(j[[f]] %in% FACTOR_LEVELS[[f]]))
    j[[f]] <- factor(j[[f]], levels = FACTOR_LEVELS[[f]])
  }
  stopifnot(!anyNA(j[names(FLAGS)]), all(j$label_mode == "real"),
            n_distinct(j$id) == N_PEOPLE[n],
            all(j %>% group_by(id) %>% summarise(k = n_distinct(label)) %>% pull(k) == 1),
            all(j$n_words[j$usable] > 0))
  j %>% select(-response_text, -label_mode) %>% mutate(study_pipeline = n, .before = 1)
}
studies <- lapply(1:5, read_study)

# Each flag's source, and for an agency flag the result of its one validation
# test (agency/agency_validation_plan.md): validated when the rule agreed with
# the annotators' majority on at least 85 percent of the 400 validation items
# and found at least 75 percent of the items of each class.
agency_scores <- read_csv(IN[["agency_scores"]], show_col_types = FALSE) %>%
  filter(what == "rule", scope == "all items")
stopifnot(setequal(agency_scores$flag, names(AGENCY_FLAGS)))
FLAG_STATUS <- c(stats::setNames(rep("word list (each study's registered rules)", length(WORD_FLAGS)),
                                 names(WORD_FLAGS)),
                 stats::setNames(vapply(names(AGENCY_FLAGS), function(f) {
                   s <- agency_scores[agency_scores$flag == f, ]
                   pass <- s$agreement >= 0.85 && s$recall_yes >= 0.75 && s$recall_no >= 0.75
                   sprintf("agency rule, %s (agreement %.2f, recall %.2f yes and %.2f no, on %d items)",
                           if (pass) "validated" else "not validated: missed a pass mark",
                           s$agreement, s$recall_yes, s$recall_no, s$n)
                 }, character(1)), names(AGENCY_FLAGS)))

samples <- lapply(1:5, function(n) list(n = n, sample = SAMPLE_ALL, data = studies[[n]]))
tag <- function(df, s) {
  info <- STUDIES[STUDIES$study_pipeline == s$n, ]
  df %>% mutate(analysis_status = ANALYSIS_STATUS, study_pipeline = s$n,
                study_paper = info$study_paper, part = info$part, sample = s$sample,
                .before = 1)
}

sample_table <- bind_rows(lapply(samples, function(s) {
  d <- s$data
  tag(d %>% group_by(label) %>%
        summarise(participants = n_distinct(id), explanations = n(),
                  analyzed = sum(analyzed), no_usable_text = sum(!usable),
                  six_point_items = sum(k_points == 6L), .groups = "drop"), s)
}))
write_csv(sample_table, OUT("text_battery_samples.csv"))
print(as.data.frame(sample_table %>% select(study_pipeline, sample, label, participants, analyzed)))

# ---------------------------------------------------------------------------
# 3. What the explanations named
# ---------------------------------------------------------------------------
# The share of a label group's explanations that carry a flag, with a 95
# percent interval from resampling participants: each resample draws, within
# each label, as many participants as the label has, with replacement, and
# pools all of the explanations of the participants drawn. The difference
# AI minus Human is taken within each resample. In Studies 2, 4 and 5 the
# shares are given at each modification level and over all three.
prevalence <- function(s) {
  info <- STUDIES[STUDIES$study_pipeline == s$n, ]
  base <- s$data %>% filter(analyzed) %>%
    mutate(level = if (info$part == "second works") as.character(modification) else "all levels")
  if (info$part == "second works") base <- bind_rows(base, base %>% mutate(level = "all levels"))
  per_person <- base %>%
    select(label, id, dimension, level, all_of(names(FLAGS))) %>%
    pivot_longer(all_of(names(FLAGS)), names_to = "flag", values_to = "on") %>%
    group_by(label, id, dimension, level, flag) %>%
    summarise(n = n(), k = sum(on), .groups = "drop") %>%
    mutate(id = as.character(id), cell = paste(dimension, level, flag, sep = "|"))
  cells <- sort(unique(per_person$cell))
  by_label <- function(lab) {
    p <- per_person[per_person$label == lab, ]
    ids <- sort(unique(p$id), method = "radix")
    N <- K <- matrix(0, length(ids), length(cells), dimnames = list(ids, cells))
    at <- cbind(match(p$id, ids), match(p$cell, cells))
    N[at] <- p$n
    K[at] <- p$k
    W <- t(vapply(seq_len(B), function(b)
      tabulate(sample.int(length(ids), length(ids), replace = TRUE), length(ids)),
      integer(length(ids))))
    list(est = colSums(K) / colSums(N), star = (W %*% K) / (W %*% N),
         n = colSums(N), k = colSums(K), people = length(ids), people_k = colSums(K > 0))
  }
  set.seed(SEED)
  h <- by_label("Human")
  a <- by_label("AI")
  ci <- function(m) apply(m, 2, quantile, probs = c(0.025, 0.975), na.rm = TRUE, names = FALSE)
  block <- function(label, est, star, n, k, people, people_k) {
    q <- ci(star)
    tibble(cell = cells, label = label, estimate = unname(est), ci_lo = q[1, ], ci_hi = q[2, ],
           n_explanations = unname(n), n_flagged = unname(k), n_participants = people,
           n_participants_flagged = unname(people_k))
  }
  out <- bind_rows(
    block("Human", h$est, h$star, h$n, h$k, h$people, h$people_k),
    block("AI", a$est, a$star, a$n, a$k, a$people, a$people_k),
    block("AI minus Human", a$est - h$est, a$star - h$star, a$n + h$n, a$k + h$k,
          a$people + h$people, a$people_k + h$people_k)) %>%
    separate(cell, c("measure", "level", "flag"), sep = "\\|") %>%
    mutate(flag_words = unname(FLAGS[flag]), flag_source = unname(FLAG_STATUS[flag]),
           quantity = ifelse(label == "AI minus Human",
             "difference in the share of explanations, AI minus Human",
             "share of explanations that carry the flag"),
           B = B, seed = SEED, resampled = "participants within each label, with replacement")
  tag(out, s)
}
prev <- bind_rows(lapply(samples, prevalence)) %>%
  mutate(level = factor(level, levels = c("all levels", "None", "Slight", "Dramatic")),
         flag = factor(flag, levels = names(FLAGS))) %>%
  arrange(study_paper, sample, measure, flag, level, label) %>%
  mutate(level = as.character(level), flag = as.character(flag))
write_csv(prev, OUT("text_battery_prevalence.csv"))

# ---------------------------------------------------------------------------
# 4. The words that set the label groups apart
# ---------------------------------------------------------------------------
# Monroe, Colaresi and Quinn (2008), "Fightin' words", Political Analysis
# 16(4), 372-403, section 3.4: the log-odds ratio with an informative
# Dirichlet prior, written out here as section 8 of Study1_02_Text.ipynb
# writes it. For a word w, y_a and y_b are its counts on the two sides; the
# prior adds to each count alpha0 times the word's share of the two sides'
# words together, so a rare word needs more evidence to move; z is the
# log-odds ratio divided by its standard error. z ranks words; with thousands
# scored at once it is not a significance test.
monroe <- function(y_a, y_b, alpha0 = KEYNESS_ALPHA0, min_total = KEYNESS_MIN_TOTAL) {
  vocab <- sort(union(names(y_a), names(y_b)), method = "radix")
  ya <- as.numeric(y_a[vocab]); ya[is.na(ya)] <- 0
  yb <- as.numeric(y_b[vocab]); yb[is.na(yb)] <- 0
  total <- ya + yb
  a <- alpha0 * total / sum(total)
  a0 <- sum(a)
  delta <- log((ya + a) / (sum(ya) + a0 - ya - a)) - log((yb + a) / (sum(yb) + a0 - yb - a))
  z <- delta / sqrt(1 / (ya + a) + 1 / (yb + a))
  tibble(word = vocab, z = z, log_odds_ratio = delta, n_a = as.integer(ya),
         n_b = as.integer(yb)) %>%
    filter(n_a + n_b >= min_total)
}
counts_of <- function(wc) {
  x <- wc %>% group_by(word) %>% summarise(n = sum(count), .groups = "drop")
  setNames(x$n, x$word)
}
wordcounts <- read_csv(IN[["wordcounts"]], na = character(), progress = FALSE,
                       col_types = cols(study = col_integer(), count = col_integer(),
                                        .default = col_character()))

keyness <- function(s) {
  rows <- s$data %>% filter(analyzed) %>%
    transmute(id = as.character(id), stimulus_id, dimension, label)
  wc <- wordcounts %>% filter(study == s$n) %>%
    inner_join(rows, by = c("id", "stimulus_id", "dimension"))
  bind_rows(lapply(sort(unique(rows$dimension)), function(dim) {
    w <- wc[wc$dimension == dim, ]
    people <- rows %>% filter(dimension == dim) %>% group_by(label) %>%
      summarise(n = n_distinct(id), .groups = "drop")
    spread <- w %>% group_by(word, label) %>%
      summarise(responses = n(), participants = n_distinct(id), .groups = "drop") %>%
      pivot_wider(names_from = label, values_from = c(responses, participants), values_fill = 0)
    for (col in c("responses_AI", "responses_Human", "participants_AI", "participants_Human")) {
      if (!col %in% names(spread)) spread[[col]] <- 0L
    }
    monroe(counts_of(w[w$label == "AI", ]), counts_of(w[w$label == "Human", ])) %>%
      rename(n_ai = n_a, n_human = n_b) %>%
      left_join(spread, by = "word") %>%
      mutate(measure = dim, side = ifelse(z > 0, "AI", "Human"),
             share_participants_ai = participants_AI / people$n[people$label == "AI"],
             share_participants_human = participants_Human / people$n[people$label == "Human"]) %>%
      group_by(side) %>% arrange(desc(abs(z)), word, .by_group = TRUE) %>%
      mutate(rank_within_side = row_number()) %>% ungroup()
  })) %>%
    transmute(measure, side, rank_within_side, word, z, log_odds_ratio, n_ai, n_human,
              responses_ai = responses_AI, responses_human = responses_Human,
              participants_ai = participants_AI, participants_human = participants_Human,
              share_participants_ai, share_participants_human,
              alpha0 = KEYNESS_ALPHA0, min_total = KEYNESS_MIN_TOTAL) %>%
    tag(s)
}
key_table <- bind_rows(lapply(samples, keyness)) %>%
  arrange(study_paper, sample, measure, side, rank_within_side)
write_csv(key_table, OUT("text_battery_keyness.csv"))

# ---------------------------------------------------------------------------
# 5. Does the code reproduce Study 1's deposited tables?
# ---------------------------------------------------------------------------
s1 <- studies[[1]]
# 5.1 The distinctive words of high (4 or 5) against low (1 or 2) ratings
#     under the Human label (Study1_02_Text.ipynb, section 8).
repro_keyness <- bind_rows(lapply(c("effort", "creativity"), function(dim) {
  rows <- s1 %>% filter(label == "Human", dimension == dim) %>%
    transmute(id = as.character(id), stimulus_id, dimension, rating)
  w <- wordcounts %>% filter(study == 1L) %>% inner_join(rows, by = c("id", "stimulus_id", "dimension"))
  mine <- monroe(counts_of(w[w$rating %in% 4:5, ]), counts_of(w[w$rating %in% 1:2, ]))
  dep <- read_csv(IN[[paste0("study1_keyness_", dim)]], na = character(), show_col_types = FALSE)
  both <- inner_join(mine, dep, by = "word")
  tibble(check = paste("distinctive words,", dim, "(high against low ratings, Human label)"),
         rows_deposited = nrow(dep), rows_reproduced = nrow(mine), rows_matched = nrow(both),
         max_abs_difference = max(abs(both$z.x - both$z.y), abs(both$n_a - both$n_high),
                                  abs(both$n_b - both$n_low)),
         pass = nrow(both) == nrow(dep) && nrow(both) == nrow(mine) &&
           max_abs_difference < 1e-9)
}))
# 5.2 The Human-label models of rating on a flag (Study1_03_Integration.Rmd,
#     sections 3.2 and 4.2): rating ~ flag (+ word count) + (1 | id) +
#     (1 | stimulus_id), word count z-scored within the model's data.
repro_specs <- tribble(
  ~table, ~model, ~dimension, ~flag, ~with_words,
  "study1_effort_detail_lmm", "rating ~ detail talk", "effort", "says_detail", FALSE,
  "study1_effort_detail_lmm", "rating ~ detail talk + word count", "effort", "says_detail", TRUE,
  "study1_effort_other_lmm", "rating ~ says_time", "effort", "says_time", FALSE,
  "study1_effort_other_lmm", "rating ~ says_skill", "effort", "says_skill", FALSE,
  "study1_creativity_concept_lmm", "rating ~ concept talk", "creativity", "says_concept", FALSE,
  "study1_creativity_concept_lmm", "rating ~ concept talk + word count", "creativity", "says_concept", TRUE,
  "study1_creativity_execution_lmm", "rating ~ execution talk (visible detail)", "creativity", "says_detail", FALSE)
repro_lmm <- bind_rows(lapply(seq_len(nrow(repro_specs)), function(i) {
  sp <- repro_specs[i, ]
  d <- s1 %>% filter(label == "Human", dimension == sp$dimension) %>%
    mutate(n_words_z = as.numeric(scale(n_words)))
  f <- paste("rating ~", sp$flag, if (sp$with_words) "+ n_words_z", "+ (1 | id) + (1 | stimulus_id)")
  fit <- lmerTest::lmer(stats::as.formula(f), data = d, REML = TRUE,
                        control = lme4::lmerControl(optimizer = "bobyqa"))
  co <- summary(fit)$coefficients[paste0(sp$flag, "TRUE"), ]
  dep <- read_csv(IN[[sp$table]], show_col_types = FALSE) %>%
    filter(model == sp$model, term == paste0(sp$flag, "TRUE"))
  diff <- max(abs(co[["Estimate"]] - dep$estimate), abs(co[["Std. Error"]] - dep$std.error))
  tibble(check = paste0("Human-label model, ", sp$dimension, ": ", sp$model),
         rows_deposited = nrow(dep), rows_reproduced = 1L, rows_matched = nrow(dep),
         max_abs_difference = diff, pass = nrow(dep) == 1 && diff < 1e-6)
}))
# 5.3 The shares of explanations that carry a flag, Study 1, effort.
p1 <- prev %>% filter(study_pipeline == 1, measure == "effort", label != "AI minus Human")
dep_prev <- read_csv(IN[["study1_effort_prevalence"]], show_col_types = FALSE) %>%
  filter(quantity %in% c("detail", "time", "skill")) %>%
  mutate(flag = paste0("says_", quantity)) %>%
  inner_join(p1 %>% select(label, flag, mine = estimate), by = c(arm = "label", "flag"))
dep_prompt <- read_csv(IN[["study1_prompt_by_arm"]], show_col_types = FALSE) %>%
  inner_join(p1 %>% filter(flag == "says_prompt") %>% select(label, mine = estimate),
             by = c(arm = "label"))
n_dep <- c(nrow(read_csv(IN[["study1_effort_prevalence"]], show_col_types = FALSE) %>%
                 filter(quantity %in% c("detail", "time", "skill"))),
           nrow(read_csv(IN[["study1_prompt_by_arm"]], show_col_types = FALSE)))
repro_prev <- tibble(
  check = c("shares of effort explanations naming detail, time and skill (Human label)",
            "shares of effort explanations naming prompting or a machine, by label"),
  rows_deposited = n_dep, rows_reproduced = c(nrow(dep_prev), nrow(dep_prompt)),
  rows_matched = c(nrow(dep_prev), nrow(dep_prompt)),
  max_abs_difference = c(max(abs(dep_prev$estimate - dep_prev$mine)),
                         max(abs(dep_prompt$estimate - dep_prompt$mine)))) %>%
  mutate(pass = rows_matched == rows_deposited & max_abs_difference < 1e-12)
repro <- bind_rows(repro_keyness, repro_lmm, repro_prev) %>%
  mutate(analysis_status = ANALYSIS_STATUS, .before = 1)
write_csv(repro, OUT("text_battery_reproduction_checks.csv"))
print(as.data.frame(repro %>% select(check, max_abs_difference, pass)))
if (!all(repro$pass)) stop("The code does not reproduce a Study 1 table; see text_battery_reproduction_checks.csv.")

# ---------------------------------------------------------------------------
# 6. Words linked to ratings within a label
# ---------------------------------------------------------------------------
# For one study, sample, question and flag, the main model is
#   rating ~ <registered design> + on_human + on_ai + (1 | id) + (1 | image)
# where on_human is 1 for a Human-label explanation that carries the flag and
# on_ai is 1 for an AI-label explanation that carries it. The registered design
# (each study's fixed effects, with sum-to-zero contrasts) absorbs the label,
# the conditions and their interactions, so each coefficient compares
# explanations with and without the flag inside the same label and condition:
# its link to the rating among people who saw that label. AI minus Human is the
# difference of the two coefficients. REML, the bobyqa optimizer and
# Satterthwaite's degrees of freedom, as in the registered models.
#
# The versions:
#   within person   the flag split into each participant's share of
#                   explanations (of this question) that carry it and the
#                   explanation's departure from that share; the departure's
#                   coefficient is the link within one person's own
#                   explanations, the share's is the link between people;
#   word count      the main model plus the z-scored log of the explanation's
#                   word count, since a longer explanation has more chances to
#                   name anything;
#   polarity        for detail, time, skill and the idea, claimed mentions and
#                   denied mentions ("not much detail") apart, each against
#                   explanations without the flag.
# A link is reported only where the flag appears in at least
# MIN_FLAGGED_RESPONSES explanations from at least MIN_FLAGGED_PEOPLE
# participants under that label (for the within-person link, at least
# MIN_FLAGGED_PEOPLE participants who carry it in some but not all of their
# explanations). Holm's correction runs over every main-model link of a study
# and sample.
CONTRAST_COLS <- c("label", "stimulus_type", "time", "modification", "image_kind",
                   "source_time", "editing_time")
model_formula <- function(n, terms) {
  stats::as.formula(paste("rating ~", DESIGN[[as.character(n)]], "+",
                          paste(terms, collapse = " + "), "+ (1 | id) + (1 | image)"))
}
fit_model <- function(n, d, terms) {
  used <- CONTRAST_COLS[vapply(CONTRAST_COLS, function(f)
    grepl(paste0("\\b", f, "\\b"), DESIGN[[as.character(n)]]), logical(1))]
  ctr <- stats::setNames(rep(list("contr.sum"), length(used)), used)
  fit_with_status(lmerTest::lmer(model_formula(n, terms), data = d, REML = TRUE,
                                 contrasts = ctr,
                                 control = lme4::lmerControl(optimizer = "bobyqa")))
}
# Linear combinations of the coefficients, each with its Satterthwaite test.
combine <- function(res, specs) {
  empty <- tibble(contrast = names(specs), estimate = NA_real_, std_error = NA_real_,
                  df = NA_real_, t = NA_real_, p = NA_real_, ci_lo = NA_real_, ci_hi = NA_real_)
  if (!fit_usable(res$status)) return(empty)
  nm <- names(lme4::fixef(res$fit))
  ok <- vapply(specs, function(s) all(names(s) %in% nm), logical(1))
  if (!any(ok)) return(empty)
  L <- t(vapply(specs[ok], function(s) {
    v <- stats::setNames(numeric(length(nm)), nm)
    v[names(s)] <- s
    v
  }, numeric(length(nm))))
  ct <- as.data.frame(lmerTest::contest(res$fit, L, joint = FALSE, confint = TRUE, level = 0.95))
  got <- tibble(contrast = names(specs)[ok], estimate = ct[["Estimate"]],
                std_error = ct[["Std. Error"]], df = ct[["df"]], t = ct[["t value"]],
                p = ct[["Pr(>|t|)"]], ci_lo = ct[["lower"]], ci_hi = ct[["upper"]])
  bind_rows(got, empty[!ok, ]) %>% slice(match(names(specs), contrast))
}
pair_specs <- function(h, a) {
  list(Human = stats::setNames(1, h), AI = stats::setNames(1, a),
       `AI minus Human` = stats::setNames(c(1, -1), c(a, h)))
}
# Counts behind each link, by label: explanations and participants with the
# indicator on.
enough <- function(d, indicator) {
  d %>% group_by(label) %>%
    summarise(n_explanations = n(), n_flagged = sum(.data[[indicator]] > 0),
              n_participants = n_distinct(id),
              n_participants_flagged = n_distinct(id[.data[[indicator]] > 0]),
              .groups = "drop") %>%
    mutate(estimable = n_flagged >= MIN_FLAGGED_RESPONSES &
             n_participants_flagged >= MIN_FLAGGED_PEOPLE,
           label = as.character(label))
}
link_rows <- function(res, specs, counts, variant, term) {
  est <- combine(res, specs)
  ok_h <- counts$estimable[counts$label == "Human"]
  ok_a <- counts$estimable[counts$label == "AI"]
  keep <- c(Human = ok_h, AI = ok_a, `AI minus Human` = ok_h && ok_a)
  rare <- "too rare under this label to estimate"
  est %>%
    mutate(label = contrast, variant = variant, term = term,
           note = case_when(!keep[contrast] ~ rare,
                            !fit_usable(res$status) ~ fit_note(res$status),
                            TRUE ~ ""),
           across(c(estimate, std_error, df, t, p, ci_lo, ci_hi),
                  ~ ifelse(keep[contrast], .x, NA_real_))) %>%
    left_join(bind_rows(counts, counts %>% summarise(
      label = "AI minus Human", n_explanations = sum(n_explanations),
      n_flagged = sum(n_flagged), n_participants = sum(n_participants),
      n_participants_flagged = sum(n_participants_flagged), estimable = all(estimable))) %>%
        select(-estimable), by = "label") %>%
    select(-contrast) %>%
    mutate(converged = res$status$converged, singular = res$status$singular,
           lme4_messages = res$status$lme4_messages)
}
links_one <- function(job) {
  s <- samples[[job$sample_index]]
  n <- s$n
  d <- s$data %>% filter(analyzed, dimension == job$measure) %>%
    mutate(id = factor(id), image = factor(image),
           on = as.numeric(.data[[job$flag]]),
           is_h = as.numeric(label == "Human"), is_a = as.numeric(label == "AI"),
           on_h = on * is_h, on_a = on * is_a,
           words_z = as.numeric(scale(log(n_words)))) %>%
    group_by(id) %>% mutate(share = mean(on)) %>% ungroup() %>%
    mutate(dev = on - share, dev_h = dev * is_h, dev_a = dev * is_a,
           share_h = share * is_h, share_a = share * is_a,
           varies = as.numeric(share > 0 & share < 1))
  counts <- enough(d, "on")
  out <- list()
  # The main model, and the word-count version.
  terms <- c("on_h", "on_a")[c(sum(d$on_h) > 0, sum(d$on_a) > 0)]
  if (length(terms) > 0) {
    res <- fit_model(n, d, terms)
    out$main <- link_rows(res, pair_specs("on_h", "on_a"), counts, "main", "carries the flag")
    res_w <- fit_model(n, d, c(terms, "words_z"))
    out$words <- link_rows(res_w, pair_specs("on_h", "on_a"), counts, "word count",
                           "carries the flag")
    # The within-person version. The within-person link needs people whose
    # explanations vary on the flag.
    vary <- d %>% group_by(label) %>%
      summarise(n_varying = n_distinct(id[varies == 1]), .groups = "drop") %>%
      mutate(label = as.character(label))
    counts_w <- counts %>% left_join(vary, by = "label") %>%
      mutate(estimable = estimable & n_varying >= MIN_FLAGGED_PEOPLE) %>% select(-n_varying)
    terms_p <- c(c("dev_h", "share_h")[rep(sum(d$on_h) > 0, 2)],
                 c("dev_a", "share_a")[rep(sum(d$on_a) > 0, 2)])
    res_p <- fit_model(n, d, terms_p)
    out$within <- link_rows(res_p, pair_specs("dev_h", "dev_a"), counts_w, "within person",
                            "carries the flag, within one person's explanations")
    out$between <- link_rows(res_p, pair_specs("share_h", "share_a"), counts, "within person",
                             "share of the person's explanations that carry the flag, between people")
  }
  # The polarity version.
  if (job$flag %in% names(POLARITY)) {
    pol <- d[[POLARITY[[job$flag]]]]
    stopifnot(all((pol != "neither") == (d$on == 1)))
    d <- d %>% mutate(claimed = as.numeric(pol == "asserted"), denied = as.numeric(pol == "negated"),
                      claimed_h = claimed * is_h, claimed_a = claimed * is_a,
                      denied_h = denied * is_h, denied_a = denied * is_a)
    present <- c(claimed_h = sum(d$claimed_h), claimed_a = sum(d$claimed_a),
                 denied_h = sum(d$denied_h), denied_a = sum(d$denied_a)) > 0
    if (any(present)) {
      res_q <- fit_model(n, d, names(present)[present])
      out$claimed <- link_rows(res_q, pair_specs("claimed_h", "claimed_a"), enough(d, "claimed"),
                               "polarity", "claims it, against no mention")
      out$denied <- link_rows(res_q, pair_specs("denied_h", "denied_a"), enough(d, "denied"),
                              "polarity", "denies it, against no mention")
    }
  }
  bind_rows(out) %>% mutate(measure = job$measure, flag = job$flag,
                            flag_words = unname(FLAGS[job$flag]),
                            flag_source = unname(FLAG_STATUS[job$flag]),
                            model = paste("rating ~", DESIGN[[as.character(n)]],
                                          "+ <the version's flag terms> + (1 | id) + (1 | image)")) %>%
    tag(s)
}
jobs <- list()
for (i in seq_along(samples)) {
  for (m in sort(unique(samples[[i]]$data$dimension))) {
    for (f in names(FLAGS)) jobs[[length(jobs) + 1]] <- list(sample_index = i, measure = m, flag = f)
  }
}
cat("Fitting the rating links:", length(jobs), "jobs on", N_WORKERS, "cores\n")
t0 <- Sys.time()
link_list <- parallel::mclapply(jobs, links_one, mc.cores = N_WORKERS, mc.preschedule = FALSE)
failed <- vapply(link_list, function(x) inherits(x, "try-error") || is.null(x), logical(1))
if (any(failed)) stop("A rating-link job failed: ", paste(unlist(link_list[failed])[1], collapse = " "))
cat("Done in", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "minutes\n")
links <- bind_rows(link_list) %>%
  group_by(study_pipeline, sample) %>%
  mutate(p_holm = {
    use <- variant == "main" & label != "AI minus Human" & !is.na(p)
    out <- rep(NA_real_, n())
    out[use] <- p.adjust(p[use], method = "holm")
    out
  }) %>%
  ungroup() %>%
  mutate(flag = factor(flag, levels = names(FLAGS))) %>%
  arrange(study_paper, sample, measure, flag, variant, term, label) %>%
  mutate(flag = as.character(flag)) %>%
  select(analysis_status, study_pipeline, study_paper, part, sample, measure, flag, flag_words,
         flag_source, variant, term, label, estimate, std_error, df, t, p, p_holm, ci_lo, ci_hi,
         n_explanations, n_flagged, n_participants, n_participants_flagged, converged,
         singular, lme4_messages, note, model)
write_csv(links, OUT("text_battery_rating_links.csv"))

# ---------------------------------------------------------------------------
# 7. The run record
# ---------------------------------------------------------------------------
pkgs <- c("readr", "dplyr", "tidyr", "tibble", "lme4", "lmerTest", "Matrix")
write_csv(tibble(package = c("R", pkgs),
                 version = c(paste(R.version$major, R.version$minor, sep = "."),
                             vapply(pkgs, function(p) as.character(utils::packageVersion(p)),
                                    character(1)))),
          OUT("text_battery_analysis_package_versions.csv"))
writeLines(utils::capture.output(utils::sessionInfo()),
           OUT("text_battery_analysis_sessionInfo.txt"))
write_run_manifest(run)
