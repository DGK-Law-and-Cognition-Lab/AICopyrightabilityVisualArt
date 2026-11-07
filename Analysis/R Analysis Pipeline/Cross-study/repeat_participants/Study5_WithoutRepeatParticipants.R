# Study 5: the registered sample beside the analyzed sample
#
# Study 5's analysis removes the 26 participants who had completed one of
# Studies 1 to 4 before taking Study 5 (exclusion step 6 of
# Study 5/Study5_01_Quant.Rmd, added on 1 November 2026, after every
# registered result was known, at a co-author's request; it is not in the
# registration). Studies 1 to 4 shared one subject-pool listing, so a student
# could take only one of them; Study 5 had its own listing, with no
# restriction against the earlier one. Those 26 had already done the same kind
# of task and read the same debriefing.
#
# This script sets the registered analysis on the registered sample of 223
# beside the same analysis on the 197 analyzed, so a reader can see what the
# removal changed. It
#   1. finds the 26 by the rule of step 6: a Study 5 participant of the
#      registered sample whose subject-pool code has a completed record
#      (Finished True) in the Labels export of Study 1, 2, 3 or 4; it stops
#      unless they are exactly the participants step 6 removed, and it counts
#      how many had been analyzed in their earlier study;
#   2. refits Study 5's registered models (Study5_01_Quant.Rmd, sections 6 to
#      10) on the registered sample and stops unless the refit reproduces the
#      tables of the registered run of 13 October 2026, kept unchanged in
#      registered_run/;
#   3. refits them on the analyzed sample and stops unless the refit reproduces
#      Study 5's tables, and the penalty at each editing time and level in
#      Cross-study/tables/crossstudy_time_check.csv;
#   4. writes every result of both samples side by side.
#
# Study numbers follow the pipeline's folders. The paper swaps two of them:
# the pipeline's Study 2 is the paper's Study 3 and its Study 3 is the paper's
# Study 2. Study 1, Study 4 and Study 5 are the same in both.
#
# No table holds a participant code or any value that belongs to one
# participant. In the public copy of the project the codes are replaced by
# other codes, the same replacement in every study, so the script finds the
# same people there.
#
# Run from this folder, after Study 5's pipeline and the cross-study analysis:
#   Rscript Study5_WithoutRepeatParticipants.R

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
  library(lme4)
  library(lmerTest)
  library(emmeans)
  library(ordinal)
})

HERE <- normalizePath(getwd(), mustWork = TRUE)
PIPELINE <- normalizePath(file.path(HERE, "..", ".."), mustWork = TRUE)
source(file.path(PIPELINE, "shared", "R", "fit_status.R"))
source(file.path(PIPELINE, "shared", "R", "qualtrics_import.R"))
PROJECT_ROOT <- find_project_root(start = PIPELINE)
TAB_DIR <- file.path(HERE, "tables")
dir.create(TAB_DIR, showWarnings = FALSE)
REG_DIR <- file.path(HERE, "registered_run")

ANALYSIS_STATUS <- paste("sensitivity analysis: the registered analysis on the registered sample",
                         "of 223, beside the analysis reported, which removes the 26 participants",
                         "who had completed an earlier study (a deviation adopted on 1 November",
                         "2026, at a co-author's request, after every registered result was known)")
SAMPLE_REGISTERED <- "registered sample (223)"
SAMPLE_ANALYZED <- "analyzed sample (197)"

# ---------------------------------------------------------------------------
# 1. The participants who had completed an earlier study
# ---------------------------------------------------------------------------
LINK_COLUMN <- c("1" = "id", "2" = "ResponseId", "3" = "ResponseId",
                 "4" = "ResponseId", "5" = "ResponseId")
labels_of <- function(n) {
  read_qualtrics_export(file.path(PROJECT_ROOT, "Data", paste("Study", n),
                                  paste0("Study", n, "_Labels.csv")))
}
completed_codes <- function(n) {
  l <- labels_of(n)
  unique(trim_answer(l$id)[trim_answer(l$Finished) == "True" & trim_answer(l$id) != ""])
}
analyzed_codes <- function(n) {
  file <- if (n == 5) "study5_long_registered_sample.csv" else paste0("study", n, "_long_with_text.csv")
  ids <- unique(read_csv(file.path(PIPELINE, paste("Study", n), file),
                         col_types = cols(.default = col_character()), progress = FALSE)$id)
  l <- labels_of(n)
  link <- l[[LINK_COLUMN[[as.character(n)]]]]
  stopifnot(all(vapply(ids, function(i) sum(link == i) == 1, logical(1))))
  tibble(id = ids, code = trim_answer(l$id[match(ids, link)]))
}
s5 <- analyzed_codes(5)
stopifnot(nrow(s5) == 223, !anyNA(s5$code), all(s5$code != ""), !anyDuplicated(s5$code))
earlier <- bind_rows(lapply(1:4, function(n) {
  tibble(earlier_study_pipeline = n, code = completed_codes(n),
         analyzed_there = completed_codes(n) %in% analyzed_codes(n)$code)
}))
hit <- s5 %>% inner_join(earlier, by = "code", relationship = "one-to-many")
repeat_ids <- unique(hit$id)
stopifnot(!anyDuplicated(hit$id))   # none of the 26 completed two earlier studies
flow <- read_csv(file.path(PIPELINE, "Study 5", "tables", "study5_exclusion_flow_analyzed.csv"),
                 show_col_types = FALSE)
stopifnot(length(repeat_ids) == 26, flow$removed[nrow(flow)] == length(repeat_ids))
overlap <- hit %>% count(earlier_study_pipeline, name = "completed_earlier") %>%
  left_join(hit %>% filter(analyzed_there) %>% count(earlier_study_pipeline, name = "analyzed_there"),
            by = "earlier_study_pipeline") %>%
  mutate(analyzed_there = coalesce(analyzed_there, 0L),
         earlier_study_paper = c(`1` = 1, `2` = 3, `3` = 2, `4` = 4)[as.character(earlier_study_pipeline)],
         .after = earlier_study_pipeline) %>%
  bind_rows(tibble(earlier_study_pipeline = NA, earlier_study_paper = NA,
                   completed_earlier = length(repeat_ids), analyzed_there = sum(hit$analyzed_there))) %>%
  mutate(what = c(rep("Study 5 participants who had completed this earlier study", n() - 1),
                  "Study 5 participants who had completed any earlier study"),
         analysis_status = ANALYSIS_STATUS)
cat("Registered sample:", nrow(s5), "| completed an earlier study:", length(repeat_ids),
    "(of whom analyzed there:", sum(hit$analyzed_there), ") | analyzed:", nrow(s5) - length(repeat_ids), "\n")
write_csv(overlap, file.path(TAB_DIR, "repeat_participants_overlap.csv"))
rm(s5, earlier, hit)

# ---------------------------------------------------------------------------
# 2. Study 5's registered analysis (Study5_01_Quant.Rmd, sections 6 to 10)
# ---------------------------------------------------------------------------
set.seed(20260421L)
RATINGS <- c("transformativeness", "essence_change", "creativity")
SUM_CONTRASTS <- list(source = "contr.sum", editing_time = "contr.sum",
                      modification = "contr.sum", image_kind = "contr.sum")
FIXED <- "source * editing_time * modification + image_kind"
FAMILY_TERMS <- c("editing_time" = "editing time, averaged over the other factors",
                  "source:editing_time" = "source by editing time")
LMER_DF <- list(lmer.df = "satterthwaite", lmerTest.limit = 20000)
SOURCE_BOUND <- 0.224
s3b <- read_csv(file.path(PIPELINE, "Study 3", "tables", "study3_time_contrast_for_study5.csv"),
                show_col_types = FALSE)
stopifnot(nrow(s3b) == 1, isFALSE(as.logical(s3b$blind_run)), isTRUE(as.logical(s3b$usable)))
TIME_BOUND <- abs(s3b$estimate)

read_long <- function(file) {
  read_csv(file.path(PIPELINE, "Study 5", file),
           col_types = cols(.default = col_character()), progress = FALSE) %>%
    mutate(rating = as.numeric(rating), k_points = as.numeric(k_points),
           source = factor(source, levels = c("Human", "AI")),
           editing_time = factor(editing_time, levels = c("less than 1 hour", "10 hours", "100 hours")),
           modification = factor(modification, levels = c("None", "Slight", "Dramatic")),
           image_kind = factor(image_kind, levels = c("NonFigure", "Figure")),
           id = factor(id), image = factor(image))
}
long_registered <- read_long("study5_long_registered_sample.csv")
long_analyzed <- read_long("study5_long_with_text.csv")
stopifnot(n_distinct(long_registered$id) == 223, n_distinct(long_analyzed$id) == 197,
          all(long_registered$label_mode == "real"), all(long_analyzed$label_mode == "real"),
          setequal(setdiff(levels(long_registered$id), levels(long_analyzed$id)), repeat_ids))

fit_lmm <- function(d) {
  f <- stats::as.formula(paste0("rating ~ ", FIXED, " + (1 | id) + (1 | image)"))
  res <- fit_with_status(lmerTest::lmer(f, data = d, REML = TRUE, contrasts = SUM_CONTRASTS,
                                        control = lme4::lmerControl(optimizer = "bobyqa")))
  res$data <- d
  res
}
emm_of <- function(res, spec) {
  do.call(emmeans::emmeans, c(list(object = res$fit, specs = spec, data = res$data), LMER_DF))
}
tost <- function(est, se, df, bound, alpha = 0.05) {
  p_lower <- pt((est + bound) / se, df, lower.tail = FALSE)
  p_upper <- pt((est - bound) / se, df, lower.tail = TRUE)
  crit <- qt(1 - alpha, df)
  tibble(bound = bound, ci90_lo = est - crit * se, ci90_hi = est + crit * se,
         tost_p = pmax(p_lower, p_upper), equivalent = pmax(p_lower, p_upper) < alpha)
}
verdict <- function(significant, equivalent) {
  case_when(is.na(significant) | is.na(equivalent) ~ NA_character_,
            significant & !equivalent ~ "significant, not inside the bound",
            significant & equivalent  ~ "significant and inside the bound",
            !significant & equivalent ~ "absent or small: inside the bound",
            TRUE ~ "inconclusive: neither significant nor equivalent")
}
fit_clmm <- function(d) {
  d$rating_ord <- factor(d$rating, levels = 1:5, ordered = TRUE)
  f <- stats::as.formula(paste0("rating_ord ~ ", FIXED, " + (1 | id) + (1 | image)"))
  warns <- character(0)
  fit <- withCallingHandlers(
    tryCatch(ordinal::clmm(f, data = d, link = "logit", Hess = TRUE, contrasts = SUM_CONTRASTS),
             error = function(e) e),
    warning = function(w) { warns <<- c(warns, conditionMessage(w)); invokeRestart("muffleWarning") })
  failed <- inherits(fit, "error")
  list(fit = fit, data = d, failed = failed,
       converged = !failed && isTRUE(fit$optRes$convergence == 0) &&
         !any(grepl("converge|Hessian", warns, ignore.case = TRUE)))
}
wald_term <- function(res, term) {
  mm <- model.matrix(stats::as.formula(paste("~", FIXED)), data = res$data, contrasts.arg = SUM_CONTRASTS)
  labs <- attr(terms(stats::as.formula(paste("~", FIXED))), "term.labels")
  cols <- colnames(mm)[attr(mm, "assign") == match(term, labs)]
  b <- res$fit$beta[cols]; V <- as.matrix(vcov(res$fit))[cols, cols, drop = FALSE]
  chisq <- as.numeric(t(b) %*% solve(V, b))
  tibble(chisq = chisq, df = length(cols), p = pchisq(chisq, length(cols), lower.tail = FALSE))
}

analyze <- function(long, sample) {
  fits <- setNames(lapply(RATINGS, function(r) {
    fit_lmm(long %>% filter(dimension == r, k_points == 5, !is.na(rating)))
  }), RATINGS)
  status <- bind_rows(lapply(RATINGS, function(r) tibble(sample = sample, rating = r,
    n_participants = n_distinct(fits[[r]]$data$id), n_obs = nrow(fits[[r]]$data), fits[[r]]$status))) %>%
    select(sample, rating, n_participants, n_obs, converged, singular)
  confirmatory <- bind_rows(lapply(RATINGS, function(r) {
    a <- as.data.frame(anova(fits[[r]]$fit, type = "III", ddf = "Satterthwaite"))
    tibble(rating = r, term = rownames(a), num_df = a$NumDF, den_df = a$DenDF, F = a[["F value"]],
           p_raw = a[["Pr(>F)"]])
  })) %>% filter(term %in% names(FAMILY_TERMS)) %>%
    mutate(test = unname(FAMILY_TERMS[term]), .after = term) %>%
    mutate(p_holm = p.adjust(p_raw, method = "holm", n = 6), holm_significant = p_holm < .05,
           sample = sample, .before = 1)
  eq_time <- bind_rows(lapply(RATINGS, function(r) {
    ct <- as.data.frame(summary(emmeans::contrast(emm_of(fits[[r]], ~ editing_time),
                        list("100 hours minus less than 1 hour" = c(-1, 0, 1))), infer = c(FALSE, TRUE)))
    h <- confirmatory %>% filter(rating == r, term == "editing_time")
    tibble(sample = sample, rating = r, estimate = ct$estimate, se = ct$SE, df = ct$df,
           p_contrast = ct$p.value) %>%
      bind_cols(tost(ct$estimate, ct$SE, ct$df, TIME_BOUND)) %>%
      mutate(holm_significant = h$holm_significant, verdict = verdict(holm_significant, equivalent))
  }))
  eq_source <- bind_rows(lapply(RATINGS, function(r) {
    ct <- as.data.frame(summary(emmeans::contrast(emm_of(fits[[r]], ~ source | modification),
                        list("Human minus AI" = c(1, -1))), infer = c(FALSE, TRUE)))
    tibble(sample = sample, rating = r, modification = as.character(ct$modification),
           estimate = ct$estimate, se = ct$SE, df = ct$df, p_contrast = ct$p.value) %>%
      bind_cols(tost(ct$estimate, ct$SE, ct$df, SOURCE_BOUND)) %>%
      mutate(significant = p_contrast < .05, verdict = verdict(significant, equivalent))
  }))
  by_time <- bind_rows(lapply(RATINGS, function(r) {
    ct <- emmeans::contrast(emm_of(fits[[r]], ~ source | editing_time * modification),
                            list("Human minus AI" = c(1, -1)), adjust = "none")
    as_tibble(summary(ct, infer = c(TRUE, TRUE), level = 0.95)) %>%
      mutate(across(where(is.factor), as.character)) %>%
      transmute(sample = sample, rating = r, editing_time, modification, estimate, se = SE, df,
                p_two_sided = p.value, ci95_lo = lower.CL, ci95_hi = upper.CL)
  }))
  clmm <- bind_rows(lapply(RATINGS, function(r) {
    res <- fit_clmm(fits[[r]]$data)
    bind_rows(lapply(names(FAMILY_TERMS), function(term) {
      w <- if (res$failed) tibble(chisq = NA_real_, df = NA_integer_, p = NA_real_) else wald_term(res, term)
      tibble(sample = sample, rating = r, term = term, clmm_chisq = w$chisq, clmm_df = w$df,
             clmm_p_raw = if (!res$failed && res$converged) w$p else NA_real_, clmm_converged = res$converged)
    }))
  })) %>% mutate(clmm_p_holm = p.adjust(clmm_p_raw, method = "holm", n = 6),
                 clmm_holm_significant = clmm_p_holm < .05)
  list(status = status, confirmatory = confirmatory, eq_time = eq_time, eq_source = eq_source,
       by_time = by_time, clmm = clmm)
}

# ---------------------------------------------------------------------------
# 3. Check: each refit reproduces the tables of its own run
# ---------------------------------------------------------------------------
same <- function(a, b) isTRUE(all.equal(as.numeric(a), as.numeric(b), tolerance = 1e-6))
reproduces <- function(res, dir) {
  t <- function(f) read_csv(file.path(dir, f), show_col_types = FALSE)
  r_conf <- t("study5_confirmatory_family.csv")
  r_eqt  <- t("study5_equivalence_editing_time.csv")
  r_eqs  <- t("study5_equivalence_source.csv")
  r_clmm <- t("study5_clmm_holm_check.csv")
  same(res$confirmatory$F, r_conf$F) && same(res$confirmatory$p_holm, r_conf$p_holm) &&
    same(res$eq_time$estimate, r_eqt$estimate) && same(res$eq_time$tost_p, r_eqt$tost_p) &&
    same(res$eq_source$estimate, r_eqs$estimate) && same(res$eq_source$tost_p, r_eqs$tost_p) &&
    same(res$clmm$clmm_p_holm, r_clmm$clmm_p_holm)
}
reg_run <- analyze(long_registered, SAMPLE_REGISTERED)
stopifnot(reproduces(reg_run, REG_DIR))
cat("Check passed: the refit on the registered sample reproduces the registered run's tables.\n")
ana_run <- analyze(long_analyzed, SAMPLE_ANALYZED)
stopifnot(reproduces(ana_run, file.path(PIPELINE, "Study 5", "tables")))
xs <- read_csv(file.path(PIPELINE, "Cross-study", "tables", "crossstudy_time_check.csv"),
               show_col_types = FALSE) %>% filter(study == "Study 5")
chk <- ana_run$by_time %>% inner_join(xs, by = c("rating" = "measure", "editing_time" = "time", "modification"))
stopifnot(nrow(chk) == 27, same(chk$estimate.x, chk$estimate.y))
cat("Check passed: the refit on the analyzed sample reproduces Study 5's tables and the time check.\n")

# ---------------------------------------------------------------------------
# 4. Both samples, side by side
# ---------------------------------------------------------------------------
side <- function(a, b) bind_rows(a, b) %>% mutate(analysis_status = ANALYSIS_STATUS)
write_csv(side(reg_run$status, ana_run$status), file.path(TAB_DIR, "study5_fit_status_both.csv"))
write_csv(side(reg_run$confirmatory, ana_run$confirmatory), file.path(TAB_DIR, "study5_confirmatory_both.csv"))
write_csv(side(reg_run$eq_time, ana_run$eq_time), file.path(TAB_DIR, "study5_equivalence_editing_time_both.csv"))
write_csv(side(reg_run$eq_source, ana_run$eq_source), file.path(TAB_DIR, "study5_equivalence_source_both.csv"))
write_csv(side(reg_run$by_time, ana_run$by_time), file.path(TAB_DIR, "study5_penalty_by_editing_time_both.csv"))
write_csv(side(reg_run$clmm, ana_run$clmm), file.path(TAB_DIR, "study5_clmm_holm_check_both.csv"))

# The verdicts, the registered sample against the analyzed one.
verdicts <- bind_rows(
  reg_run$confirmatory %>% select(rating, test) %>%
    mutate(family = "confirmatory (Holm)",
           registered_sample = as.character(reg_run$confirmatory$holm_significant),
           analyzed_sample = as.character(ana_run$confirmatory$holm_significant)),
  reg_run$eq_time %>% select(rating) %>%
    mutate(test = "editing time, 100 hours minus under 1 hour", family = "secondary equivalence",
           registered_sample = reg_run$eq_time$verdict, analyzed_sample = ana_run$eq_time$verdict),
  reg_run$eq_source %>% select(rating, modification) %>%
    mutate(test = paste("label penalty at", modification), family = "secondary equivalence",
           registered_sample = reg_run$eq_source$verdict, analyzed_sample = ana_run$eq_source$verdict) %>%
    select(-modification),
  reg_run$clmm %>% select(rating, test = term) %>%
    mutate(family = "ordinal check (Holm)",
           registered_sample = as.character(reg_run$clmm$clmm_holm_significant),
           analyzed_sample = as.character(ana_run$clmm$clmm_holm_significant))
) %>% mutate(changed = registered_sample != analyzed_sample, analysis_status = ANALYSIS_STATUS)
write_csv(verdicts, file.path(TAB_DIR, "study5_verdicts_both.csv"))

cat("\nVerdicts that differ between the two samples:", sum(verdicts$changed), "of", nrow(verdicts), "\n")
print(as.data.frame(verdicts %>% filter(changed) %>% select(family, rating, test, registered_sample, analyzed_sample)))
cat("\nConfirmatory family:\n")
print(as.data.frame(bind_rows(reg_run$confirmatory, ana_run$confirmatory) %>%
  select(sample, rating, test, F, p_raw, p_holm, holm_significant) %>%
  mutate(across(where(is.numeric), ~ signif(.x, 3)))))
cat("\nLabel penalty at each level:\n")
print(as.data.frame(bind_rows(reg_run$eq_source, ana_run$eq_source) %>%
  select(sample, rating, modification, estimate, ci90_lo, ci90_hi, p_contrast, verdict) %>%
  mutate(across(where(is.numeric), ~ signif(.x, 3)))))
cat("\nEditing time, 100 hours minus under 1 hour:\n")
print(as.data.frame(bind_rows(reg_run$eq_time, ana_run$eq_time) %>%
  select(sample, rating, estimate, ci90_lo, ci90_hi, verdict) %>% mutate(across(where(is.numeric), ~ signif(.x, 3)))))
cat("\nFit status:\n"); print(as.data.frame(bind_rows(reg_run$status, ana_run$status)))
