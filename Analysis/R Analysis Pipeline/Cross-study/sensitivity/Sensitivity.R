# What each registered test could detect
#
# Descriptive. Specified on 1 November 2026, after every registered result was
# known. It tests no hypothesis and changes no verdict.
#
# None of the five studies set its sample size by a power analysis: each was
# registered after its data were collected, and its size was set by the
# subject pool's quotas. So instead of asking whether a study was "powered",
# this script asks, for each registered test, how large an effect it could
# detect. It reads the standard error and degrees of freedom of each estimate
# from the tables the studies' own runs wrote, and computes:
#
#   mde80         the smallest true effect a two-sided test at alpha .05 would
#                 find significant in 80 percent of studies of this size and
#                 precision: (t[.975, df] + t[.80, df]) x SE;
#   eq_power      for an equivalence test, the chance that the 90 percent
#                 interval of an effect that is truly zero would fall inside
#                 the bound: 2 x Phi(bound / SE - t[.95, df]) - 1, and 0 when
#                 the interval is wider than the bound, which happens when
#                 t[.95, df] x SE exceeds the bound.
#
# Both depend only on the precision of the estimate, never on the estimate
# itself, so neither is the "observed power" of a test, which only restates its
# p-value. Study 1's robustness file computed the same quantities by simulating
# from its fitted model; the script stops unless its closed forms agree with
# those simulations.
#
# Study 5's label-by-editing-time interaction is a test of whether the label's
# penalty differs between the groups told different editing times. The script
# refits Study 5's registered creativity model to get the penalty at each
# editing time, averaged over the edit levels, and the standard error of the
# difference between two editing times.
#
# Study numbers follow the pipeline's folders; every row also gives the paper's.
#
# Run from this folder:  Rscript Sensitivity.R

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
  library(lme4)
  library(lmerTest)
  library(emmeans)
})

HERE <- normalizePath(getwd(), mustWork = TRUE)
stopifnot(file.exists(file.path(HERE, "Sensitivity.R")))
PIPELINE <- normalizePath(file.path(HERE, "..", ".."), mustWork = TRUE)
source(file.path(PIPELINE, "shared", "R", "fit_status.R"))
TAB_DIR <- file.path(HERE, "tables")
dir.create(TAB_DIR, showWarnings = FALSE)
ANALYSIS_STATUS <- paste("descriptive; specified on 1 November 2026, after every registered result",
                         "was known; tests no hypothesis and changes no verdict")
PAPER <- c(`1` = 1L, `2` = 3L, `3` = 2L, `4` = 4L, `5` = 5L)

tab <- function(n, f) file.path(PIPELINE, paste("Study", n), "tables", f)
IN <- c(
  s1_confirmatory = tab(1, "study1_confirmatory_family.csv"),
  s1_h2 = tab(1, "study1_joint_model_contrast_of_contrasts.csv"),
  s1_h3 = tab(1, "study1_h3_equivalence.csv"),
  s1_h3_power = tab(1, "study1_h3_equivalence_power.csv"),
  s1_power = tab(1, "study1_sensitivity_power.csv"),
  s2_confirmatory = tab(2, "study2_confirmatory_family.csv"),
  s2_by_level = tab(2, "study2_source_by_modification.csv"),
  s3_gap = tab(3, "study3_gap_by_time.csv"),
  s3_time = tab(3, "study3_time_contrast.csv"),
  s4_confirmatory = tab(4, "study4_confirmatory_family.csv"),
  s4_by_level = tab(4, "study4_secondary_label_by_modification.csv"),
  s4_time = tab(4, "study4_secondary_time_equivalence.csv"),
  s5_eq_source = tab(5, "study5_equivalence_source.csv"),
  s5_eq_time = tab(5, "study5_equivalence_editing_time.csv"),
  s5_long = file.path(PIPELINE, "Study 5", "study5_long_with_text.csv"),
  pooled = file.path(PIPELINE, "Cross-study", "tables", "crossstudy_penalty_equivalence.csv"))
run <- start_run_record(IN, file.path(TAB_DIR, "sensitivity_run_manifest.csv"), HERE)
OUTPUTS <- file.path(TAB_DIR, c("sensitivity_registered_tests.csv", "sensitivity_checks.csv",
                                "sensitivity_run_inputs.csv"))
run_clear_outputs(run, OUTPUTS)
write_run_inputs(run, file.path(TAB_DIR, "sensitivity_run_inputs.csv"))
rd <- function(k) read_csv(IN[[k]], show_col_types = FALSE, na = c("", "NA"))

mde80 <- function(se, df, alpha = 0.05, power = 0.80) {
  (qt(1 - alpha / 2, df) + qt(power, df)) * se
}
eq_power <- function(se, df, bound) {
  ifelse(is.na(bound), NA_real_, pmax(0, 2 * pnorm(bound / se - qt(0.95, df)) - 1))
}
row <- function(study, part, test, role, measure, level, estimate, se, df, bound = NA_real_) {
  tibble(study_pipeline = study, study_paper = unname(PAPER[as.character(study)]), part = part,
         test = test, role = role, measure = measure, level = level, estimate = estimate, se = se,
         df = df, mde80 = mde80(se, df), bound = bound, eq_power = eq_power(se, df, bound))
}
ORIG <- "originals"
SECOND <- "second works"

# ---------------------------------------------------------------------------
# The tests
# ---------------------------------------------------------------------------
s1c <- rd("s1_confirmatory") %>% filter(hypothesis == "H1")
s1h2 <- rd("s1_h2")
s1h3 <- rd("s1_h3") %>% filter(bound_role == "registered", startsWith(random_structure, "intercepts only"))
s2c <- rd("s2_confirmatory")
s2l <- rd("s2_by_level")
s3g <- rd("s3_gap")
s3t <- rd("s3_time")
s4c <- rd("s4_confirmatory")
s4l <- rd("s4_by_level")
s4t <- rd("s4_time")
s5s <- rd("s5_eq_source")
s5t <- rd("s5_eq_time")
pool <- rd("pooled") %>% filter(study == "Study 2, Study 4, Study 5")

tests <- bind_rows(
  row(1, ORIG, "label penalty (Human minus AI)", "registered (H1)", s1c$test %>% sub(".*, (creativity|effort), .*", "\\1", .),
      "all images", s1c$estimate, s1c$se, s1c$df),
  row(1, ORIG, "effort penalty minus creativity penalty", "registered (H2)", "effort minus creativity",
      "all images", s1h2$estimate, s1h2$SE, s1h2$df),
  row(1, ORIG, "penalty with a figure minus penalty without", "registered (H3, equivalence)", s1h3$dimension,
      "all images", s1h3$estimate, s1h3$se, s1h3$df, s1h3$bound_hi),
  row(3, ORIG, "label penalty at each stated time", "registered (decision at 100 hours) and exploratory",
      s3g$dimension, s3g$time, s3g$estimate, s3g$SE, s3g$df,
      ifelse(s3g$time == "100 hours", 0.224, NA_real_)),
  row(3, ORIG, "stated hours, 100 minus under 1", "registered", s3t$dimension, "both labels",
      s3t$estimate, s3t$SE, s3t$df),
  row(2, SECOND, "label penalty, averaged over edit levels", "registered (H2, equivalence)",
      s2c$measure[s2c$test == 3], "all levels", s2c$estimate[s2c$test == 3], s2c$se[s2c$test == 3],
      s2c$df[s2c$test == 3], 0.224),
  row(2, SECOND, "penalty at None minus penalty at Dramatic", "registered (H3)",
      s2c$measure[s2c$test == 4], "None minus Dramatic", s2c$estimate[s2c$test == 4],
      s2c$se[s2c$test == 4], s2c$df[s2c$test == 4]),
  row(2, SECOND, "label penalty at each edit level", "exploratory",
      s2l$measure, ifelse(is.na(s2l$modification), "None", s2l$modification), s2l$estimate, s2l$se,
      s2l$df, 0.224),
  row(4, SECOND, "label penalty, averaged over edit levels", "registered (H2, equivalence)",
      s4c$measure[s4c$hypothesis == "H2"], "all levels",
      as.numeric(s4c$estimate[s4c$hypothesis == "H2"]), as.numeric(s4c$std_error[s4c$hypothesis == "H2"]),
      s4c$den_df[s4c$hypothesis == "H2"], 0.224),
  row(4, SECOND, "label penalty at each edit level", "registered (secondary, equivalence)",
      s4l$measure, ifelse(is.na(s4l$modification), "None", s4l$modification), s4l$estimate,
      s4l$std_error, s4l$df, s4l$bound),
  row(4, SECOND, "hours stated for the original, 100 minus under 1", "registered (secondary, equivalence)",
      s4t$measure, "both labels", s4t$estimate, s4t$std_error, s4t$df, s4t$bound),
  row(5, SECOND, "label penalty at each edit level", "registered (secondary, equivalence)",
      s5s$rating, s5s$modification, s5s$estimate, s5s$se, s5s$df, s5s$bound),
  row(5, SECOND, "editing hours, 100 minus under 1", "registered (secondary, equivalence)",
      s5t$rating, "both labels", s5t$estimate, s5t$se, s5t$df, s5t$bound),
  row(NA, SECOND, "label penalty at each edit level, pooled over Studies 3 to 5", "exploratory",
      pool$measure, pool$modification, pool$estimate, pool$se, pool$df, pool$bound)
)
tests$study_paper[is.na(tests$study_pipeline)] <- NA_integer_

# Study 5's interaction: the creativity penalty at each editing time, averaged
# over the edit levels, from the registered model, and the difference between
# each pair of editing times.
long5 <- read_csv(IN[["s5_long"]], col_types = cols(.default = col_character()), progress = FALSE) %>%
  filter(dimension == "creativity", k_points == "5") %>%
  mutate(rating = as.numeric(rating),
         source = factor(source, levels = c("Human", "AI")),
         editing_time = factor(editing_time, levels = c("less than 1 hour", "10 hours", "100 hours")),
         modification = factor(modification, levels = c("None", "Slight", "Dramatic")),
         image_kind = factor(image_kind, levels = c("NonFigure", "Figure")),
         id = factor(id), image = factor(image))
stopifnot(n_distinct(long5$id) == 197, all(long5$label_mode == "real"))
fit5 <- fit_with_status(lmerTest::lmer(
  rating ~ source * editing_time * modification + image_kind + (1 | id) + (1 | image),
  data = long5, REML = TRUE,
  contrasts = list(source = "contr.sum", editing_time = "contr.sum", modification = "contr.sum",
                   image_kind = "contr.sum"),
  control = lme4::lmerControl(optimizer = "bobyqa")))
stopifnot(fit_usable(fit5$status))
emm5 <- emmeans::emmeans(fit5$fit, ~ source | editing_time, data = long5,
                         lmer.df = "satterthwaite", lmerTest.limit = 20000)
pen5 <- emmeans::contrast(emm5, list("Human minus AI" = c(1, -1)))
pen_tab <- as_tibble(summary(pen5)) %>% mutate(editing_time = as.character(editing_time))
diff5 <- as_tibble(summary(emmeans::contrast(pen5, "pairwise", by = NULL))) %>%
  mutate(contrast = as.character(contrast))
tests <- bind_rows(
  tests,
  row(5, SECOND, "creativity penalty at each editing time, averaged over edit levels",
      "exploratory (breakdown of the registered interaction)", "creativity", pen_tab$editing_time,
      pen_tab$estimate, pen_tab$SE, pen_tab$df),
  row(5, SECOND, "difference between two editing times' creativity penalties",
      "registered interaction, label by editing time (one pair of times)", "creativity",
      diff5$contrast, diff5$estimate, diff5$SE, diff5$df)
) %>% mutate(analysis_status = ANALYSIS_STATUS)
write_csv(tests, OUTPUTS[1])

# ---------------------------------------------------------------------------
# Checks against Study 1's simulations
# ---------------------------------------------------------------------------
# (a) The closed-form chance of showing a zero interaction inside +/-0.20
#     equals the analytic value Study 1's robustness file wrote beside its
#     simulation, which agreed with the simulation within its Monte Carlo error.
h3p <- rd("s1_h3_power") %>% filter(true_interaction == 0, bound == 0.2)
mine <- tests %>% filter(study_pipeline == 1, startsWith(test, "penalty with a figure"))
h3chk <- h3p %>% select(dimension, analytic_power, equivalence_power) %>%
  inner_join(mine %>% select(dimension = measure, eq_power), by = "dimension")
# (b) The closed-form smallest detectable penalty lies within 0.05 rating
#     points of where Study 1's simulated power curve crosses 80 percent,
#     found by straight-line interpolation between the two simulated effects
#     on either side. Each simulated power rests on 200 simulated data sets,
#     so it carries a Monte Carlo error of about 3 percentage points, which
#     moves the crossing by a few hundredths of a point.
sim <- rd("s1_power") %>% filter(term == "TypeAI") %>% arrange(dimension, hypothesized_beta_rating_units)
crossing <- sim %>% group_by(dimension) %>%
  summarise(crossing = {
    b <- hypothesized_beta_rating_units; p <- power
    k <- max(which(p < 0.80))
    b[k] + (b[k + 1] - b[k]) * (0.80 - p[k]) / (p[k + 1] - p[k])
  }, .groups = "drop") %>%
  inner_join(tests %>% filter(study_pipeline == 1, startsWith(test, "label penalty")) %>%
               select(dimension = measure, mde80), by = "dimension")
checks <- bind_rows(
  tibble(check = paste("closed-form equivalence power equals Study 1's analytic value,", h3chk$dimension),
         expected = as.character(round(h3chk$analytic_power, 4)), observed = as.character(round(h3chk$eq_power, 4)),
         pass = abs(h3chk$analytic_power - h3chk$eq_power) < 0.002),
  tibble(check = paste("closed-form equivalence power within 0.03 of Study 1's simulation,", h3chk$dimension),
         expected = as.character(round(h3chk$equivalence_power, 4)), observed = as.character(round(h3chk$eq_power, 4)),
         pass = abs(h3chk$equivalence_power - h3chk$eq_power) < 0.03),
  tibble(check = paste("closed-form smallest detectable penalty within 0.05 points of Study 1's",
                       "simulated 80 percent crossing,", crossing$dimension),
         expected = as.character(round(crossing$crossing, 3)), observed = as.character(round(crossing$mde80, 3)),
         pass = abs(crossing$crossing - crossing$mde80) < 0.05)) %>%
  mutate(analysis_status = ANALYSIS_STATUS)
write_csv(checks, OUTPUTS[2])
print(as.data.frame(checks %>% select(check, expected, observed, pass)))
if (!all(checks$pass)) stop("A check against Study 1's simulations failed; see sensitivity_checks.csv.")
write_run_manifest(run)
print(as.data.frame(tests %>% select(study_paper, test, measure, level, se, mde80, bound, eq_power) %>%
                      mutate(across(where(is.numeric), ~ round(.x, 3)))))
