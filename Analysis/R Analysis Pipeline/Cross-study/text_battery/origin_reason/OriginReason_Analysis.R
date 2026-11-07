# Origin as reason: how often explanations give how the work was made as a reason, by label.
#
# Exploratory. Specified on 6 November 2026, after every registered result was known; changes no
# registered verdict. Reads the frozen rule's codes (nlp/origin_reason_flags.csv, written by
# `python3 OriginReason.py apply`) and checks them against the record that step wrote.
#
#   0. The validation scores in each Part, from the saved codes (nothing is rescored). The rule is
#      used only in a Part where it met the pass marks fixed beforehand (agreement at least 85%,
#      recall of yes and of no at least 75%); in the other Part nothing is reported.
#   1. The share of explanations that give origin as a reason, under each label, with the
#      AI-minus-Human difference and the AI-to-Human ratio, all with 95% intervals from 2,000
#      resamples of participants within each label.
#   2. Within one label, the rating that comes with such an explanation against one without it,
#      from the text battery's main rating-link model (TextBattery_02_Analysis.R): rating ~ the
#      study's registered terms (sum-to-zero contrasts) + the flag under each label + (1 | participant)
#      + (1 | artwork), REML, bobyqa, Satterthwaite tests. A link is reported only where the flag
#      appears in at least 20 explanations from at least 10 participants under that label; Holm's
#      correction runs over the reported links of each study.
#
# Run from this folder:  Rscript OriginReason_Analysis.R

suppressPackageStartupMessages({ library(readr); library(dplyr); library(tibble); library(lme4); library(lmerTest) })
HERE <- normalizePath(getwd(), mustWork = TRUE)
stopifnot(file.exists(file.path(HERE, "OriginReason_Analysis.R")))
PIPELINE <- normalizePath(file.path(HERE, "..", "..", ".."), mustWork = TRUE)
TAB <- file.path(HERE, "tables")
STATUS <- paste("exploratory; specified on 6 November 2026, after every registered result was known;",
                "changes no registered verdict")
PAPER <- c(`1` = 1L, `2` = 3L, `3` = 2L, `4` = 4L, `5` = 5L)
PART <- c(`1` = "originals", `2` = "secondary works", `3` = "originals", `4` = "secondary works",
          `5` = "secondary works")
MARKS <- c(agreement = 0.85, recall_yes = 0.75, recall_no = 0.75)
MIN_FLAGGED_RESPONSES <- 20L
MIN_FLAGGED_PEOPLE <- 10L
set.seed(20260421)
sha256 <- function(path) digest::digest(file = path, algo = "sha256")

# 0. Validation, overall and by Part ------------------------------------------------------------
val <- read_csv(file.path(TAB, "origin_reason_validation_scores.csv"), show_col_types = FALSE)
codes <- read_csv(file.path(TAB, "origin_reason_validation_codes.csv"), show_col_types = FALSE) %>%
  inner_join(read_csv(file.path(HERE, "samples", "validation_key.csv"), show_col_types = FALSE) %>%
               select(uid, part, says_prompt), by = "uid", relationship = "one-to-one")
stopifnot(nrow(codes) == val$items)
by_part <- codes %>% group_by(part) %>%
  summarise(items = n(), reference_yes = sum(reference), agreement = mean(reference == rule),
            recall_yes = sum(rule & reference) / sum(reference), recall_no = sum(!rule & !reference) / sum(!reference),
            precision_yes = sum(rule & reference) / sum(rule),
            mentions = sum(says_prompt), mentions_reason_reference = mean(reference[says_prompt]),
            mentions_reason_rule = mean(rule[says_prompt]), .groups = "drop") %>%
  mutate(meets_marks = agreement >= MARKS[["agreement"]] & recall_yes >= MARKS[["recall_yes"]] &
           recall_no >= MARKS[["recall_no"]],
         used = meets_marks & isTRUE(as.logical(val$passes)), analysis_status = STATUS, .before = 1)
write_csv(by_part, file.path(TAB, "origin_reason_validation_by_part.csv"))
USED_PARTS <- by_part$part[by_part$used]
cat("Parts where the rule is used:", if (length(USED_PARTS)) paste(USED_PARTS, collapse = ", ") else "none", "\n")

# The codes, checked against the record the apply step wrote -------------------------------------
flags_path <- file.path(HERE, "nlp", "origin_reason_flags.csv")
record <- read_csv(file.path(TAB, "origin_reason_apply_record.csv"), show_col_types = FALSE)
if (sha256(flags_path) != record$value[record$item == "flags sha256"])
  stop("nlp/origin_reason_flags.csv is not the file the apply step wrote")
flags <- read_csv(flags_path, show_col_types = FALSE, col_types = cols(id = col_character()))

LABEL <- c(`1` = "Type", `2` = "source", `3` = "Type", `4` = "label", `5` = "source")
WORK <- c(`1` = "stimulus_id", `2` = "work_id", `3` = "stimulus_id", `4` = "work_id", `5` = "work_id")
IMAGE <- c(`1` = "stimulus_id", `2` = "image", `3` = "stimulus_id", `4` = "source", `5` = "image")
DESIGN <- c(`1` = "label * stimulus_type", `2` = "label * modification * image_kind", `3` = "label * time",
            `4` = "label * source_time * modification", `5` = "label * editing_time * modification + image_kind")
FACTOR_LEVELS <- list(label = c("Human", "AI"), stimulus_type = c("NonFigure", "Figure"),
                      image_kind = c("NonFigure", "Figure"), modification = c("None", "Slight", "Dramatic"),
                      time = c("under 1 hour", "10 hours", "100 hours"),
                      source_time = c("less than 1 hour", "10 hours", "100 hours"),
                      editing_time = c("less than 1 hour", "10 hours", "100 hours"))
STUDIES <- as.integer(names(PART)[PART %in% USED_PARTS])
rows <- list()
for (s in STUDIES) {
  path <- file.path(PIPELINE, paste("Study", s), sprintf("study%d_long_with_text.csv", s))
  long <- read_csv(path, show_col_types = FALSE, guess_max = 1e5, col_types = cols(.default = col_character()))
  long$row <- seq_len(nrow(long)) - 1L
  long$label <- long[[LABEL[as.character(s)]]]
  long$work <- long[[WORK[as.character(s)]]]
  long$image <- long[[IMAGE[as.character(s)]]]
  f <- flags %>% filter(study == s) %>% select(row, f_id = id, f_work = work, f_dimension = dimension,
                                                origin_reason, direction)
  d <- long %>% inner_join(f, by = "row", relationship = "one-to-one")
  stopifnot(nrow(d) == nrow(f), all(d$id == d$f_id), all(d$work == d$f_work), all(d$dimension == d$f_dimension))
  rows[[as.character(s)]] <- d %>% mutate(study_pipeline = s)
}

# 1. Shares, the difference and the ratio ---------------------------------------------------------
boot_label <- function(x, id, label, B = 2000) {
  per <- tapply(x, id, sum); n <- tapply(x, id, length)
  lab <- tapply(label, id, function(v) v[1])
  ids_h <- names(per)[lab == "Human"]; ids_a <- names(per)[lab == "AI"]
  t(replicate(B, {
    h <- sample(ids_h, replace = TRUE); a <- sample(ids_a, replace = TRUE)
    sh <- sum(per[h]) / sum(n[h]); sa <- sum(per[a]) / sum(n[a])
    c(human = sh, ai = sa, diff = sa - sh, ratio = if (sh > 0) sa / sh else NA_real_)
  }))
}
q <- function(v) unname(quantile(v, c(.025, .975), na.rm = TRUE))
shares <- bind_rows(lapply(rows, function(d) {
  d %>% group_by(study_pipeline, dimension) %>% group_modify(~ {
    b <- boot_label(.x$origin_reason, .x$id, .x$label)
    sh <- mean(.x$origin_reason[.x$label == "Human"]); sa <- mean(.x$origin_reason[.x$label == "AI"])
    tibble(label = c("Human", "AI", "AI minus Human", "AI over Human"),
           share = c(sh, sa, sa - sh, sa / sh),
           ci95_low = c(q(b[, "human"])[1], q(b[, "ai"])[1], q(b[, "diff"])[1], q(b[, "ratio"])[1]),
           ci95_high = c(q(b[, "human"])[2], q(b[, "ai"])[2], q(b[, "diff"])[2], q(b[, "ratio"])[2]),
           share_lowers = c(mean(.x$direction[.x$label == "Human"] == "lowers"),
                            mean(.x$direction[.x$label == "AI"] == "lowers"), NA, NA),
           explanations = c(sum(.x$label == "Human"), sum(.x$label == "AI"), nrow(.x), nrow(.x)),
           participants = c(n_distinct(.x$id[.x$label == "Human"]), n_distinct(.x$id[.x$label == "AI"]),
                            n_distinct(.x$id), n_distinct(.x$id)))
  }) %>% ungroup()
})) %>% mutate(study_paper = PAPER[as.character(study_pipeline)], part = PART[as.character(study_pipeline)],
               analysis_status = STATUS, .before = 1)
write_csv(shares, file.path(TAB, "origin_reason_shares.csv"))

# 2. Within-label links to the rating, as in the text battery -------------------------------------
links <- bind_rows(lapply(rows, function(d) {
  s <- d$study_pipeline[1]
  bind_rows(lapply(sort(unique(d$dimension)), function(dim) {
    dd <- d %>% filter(dimension == dim, !is.na(rating), rating != "")
    if ("k_points" %in% names(dd)) dd <- dd %>% filter(k_points == "5")
    dd <- dd %>% mutate(rating = as.numeric(rating), id = factor(id), image = factor(image),
                        on_human = as.numeric(origin_reason & label == "Human"),
                        on_ai = as.numeric(origin_reason & label == "AI"))
    used <- names(FACTOR_LEVELS)[vapply(names(FACTOR_LEVELS), function(v)
      grepl(paste0("\\b", v, "\\b"), DESIGN[as.character(s)]), logical(1))]
    for (v in used) dd[[v]] <- factor(dd[[v]], levels = FACTOR_LEVELS[[v]])
    stopifnot(!anyNA(dd[used]))
    counts <- dd %>% group_by(label) %>%
      summarise(flagged = sum(origin_reason), people = n_distinct(id[origin_reason]), .groups = "drop")
    ok <- setNames(counts$flagged >= MIN_FLAGGED_RESPONSES & counts$people >= MIN_FLAGGED_PEOPLE, counts$label)
    terms <- c("on_human", "on_ai")[c(sum(dd$on_human) > 0, sum(dd$on_ai) > 0)]
    if (!length(terms)) return(NULL)
    m <- lmer(as.formula(paste("rating ~", DESIGN[as.character(s)], "+", paste(terms, collapse = " + "),
                               "+ (1 | id) + (1 | image)")),
              data = dd, REML = TRUE, contrasts = setNames(rep(list("contr.sum"), length(used)), used),
              control = lmerControl(optimizer = "bobyqa"))
    nm <- names(fixef(m))
    specs <- list(Human = c(on_human = 1), AI = c(on_ai = 1), `AI minus Human` = c(on_ai = 1, on_human = -1))
    keep <- c(Human = isTRUE(ok["Human"]), AI = isTRUE(ok["AI"]))
    keep["AI minus Human"] <- keep[["Human"]] && keep[["AI"]]
    bind_rows(lapply(names(specs), function(k) {
      sp <- specs[[k]]
      if (!keep[[k]] || !all(names(sp) %in% nm)) return(NULL)
      L <- setNames(numeric(length(nm)), nm); L[names(sp)] <- sp
      ct <- as.data.frame(contest(m, matrix(L, nrow = 1), joint = FALSE, confint = TRUE, level = 0.95))
      tibble(study_pipeline = s, measure = dim, label = k, estimate = ct[["Estimate"]], std_error = ct[["Std. Error"]],
             df = ct[["df"]], p = ct[["Pr(>|t|)"]], ci95_low = ct[["lower"]], ci95_high = ct[["upper"]],
             singular = isSingular(m),
             flagged = if (k == "AI minus Human") sum(counts$flagged) else counts$flagged[counts$label == k])
    }))
  }))
})) %>% group_by(study_pipeline) %>% mutate(p_holm = p.adjust(p, "holm")) %>% ungroup() %>%
  mutate(study_paper = PAPER[as.character(study_pipeline)], analysis_status = STATUS,
         quantity = "rating with an origin-as-reason explanation minus without, within one label", .before = 1)
write_csv(links, file.path(TAB, "origin_reason_rating_links.csv"))

# Run record ---------------------------------------------------------------------------------------
inputs <- c(file.path("tables", "origin_reason_validation_scores.csv"), file.path("tables", "origin_reason_validation_codes.csv"),
            file.path("samples", "validation_key.csv"), file.path("nlp", "origin_reason_flags.csv"),
            "OriginReason_Analysis.R")
write_csv(tibble(run = format(Sys.time(), "%Y%m%dT%H%M%S", tz = "UTC"), file = inputs,
                 sha256 = vapply(file.path(HERE, inputs), sha256, character(1))),
          file.path(TAB, "origin_reason_analysis_run_inputs.csv"))
writeLines(capture.output(sessionInfo()), file.path(TAB, "origin_reason_analysis_sessionInfo.txt"))
cat("wrote origin_reason_validation_by_part.csv, origin_reason_shares.csv and origin_reason_rating_links.csv\n")
