# Does the effect of stated hours on the originals hold when each person may
# respond to the hours in their own way?
#
# Exploratory. Specified on 5 November 2026, after every registered result was
# known, because a co-author asked whether the small rise in creativity
# ratings with stated hours in the paper's Study 2 (the pipeline's Study 3) is
# reliable. It tests no registered hypothesis and changes no verdict.
#
# The registered model, rating ~ label x stated time + (1 | participant) +
# (1 | image), lets each participant and each image have their own average
# rating, but assumes that every participant's ratings rise with the stated
# hours by the same amount. Stated time varied within participants, so if
# people differ in how much the hours move them, that model can understate the
# uncertainty of the hours effect. The refit adds a random slope of stated time
# for each participant and of the label for each image:
#
#   rating ~ label x stated time + (1 + stated time | participant)
#                                 + (1 + label | image),
#
# the random-slope model Study 3's registration names for its equivalence
# check. For each rating and each model it writes three contrasts: 100 hours
# minus under 1 hour averaged over the two labels (equal weights, as
# registered), the same within each label, and 10 hours minus under 1 hour.
#
# It stops unless the long data file has the checksum that Study 3's real run
# recorded, and unless its refit of the registered model reproduces Study 3's
# registered contrast (study3_time_contrast.csv) to 1e-8.
#
# Run from this folder:  Rscript HoursCheck_Study2.R

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
  library(lme4)
  library(lmerTest)
  library(emmeans)
  library(digest)
})

HERE <- normalizePath(getwd(), mustWork = TRUE)
stopifnot(file.exists(file.path(HERE, "HoursCheck_Study2.R")))
PIPELINE <- normalizePath(file.path(HERE, "..", ".."), mustWork = TRUE)
TAB_DIR <- file.path(HERE, "tables")
dir.create(TAB_DIR, showWarnings = FALSE)
ANALYSIS_STATUS <- paste("exploratory; specified on 5 November 2026, after every registered result",
                         "was known; changes no registered verdict")

long_path <- file.path(PIPELINE, "Study 3", "study3_long_with_text.csv")
manifest <- read_csv(file.path(PIPELINE, "Study 3", "tables", "study3_quant_run_manifest.csv"),
                     show_col_types = FALSE)
want <- manifest$sha256[manifest$file == "study3_long_with_text.csv"]
got <- digest(file = long_path, algo = "sha256")
if (length(want) != 1 || !identical(want, got)) {
  stop("study3_long_with_text.csv does not have the checksum Study 3's run recorded")
}

d0 <- read_csv(long_path, show_col_types = FALSE) %>%
  filter(!is.na(rating)) %>%
  mutate(time = factor(time, levels = c("under 1 hour", "10 hours", "100 hours")),
         Type = factor(Type, levels = c("Human", "AI")))
stopifnot(n_distinct(d0$id) == 85)

FORMULAS <- list(
  `registered model` = rating ~ Type * time + (1 | id) + (1 | stimulus_id),
  `random-slope refit` = rating ~ Type * time + (1 + time | id) + (1 + Type | stimulus_id))
CTRL <- lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))

registered <- read_csv(file.path(PIPELINE, "Study 3", "tables", "study3_time_contrast.csv"),
                       show_col_types = FALSE)

rows <- list()
for (dim in c("creativity", "effort")) {
  d <- filter(d0, dimension == dim)
  for (model in names(FORMULAS)) {
    msgs <- character()
    fit <- withCallingHandlers(lmer(FORMULAS[[model]], data = d, REML = TRUE, control = CTRL),
                               message = function(m) { msgs <<- c(msgs, conditionMessage(m)); invokeRestart("muffleMessage") },
                               warning = function(w) { msgs <<- c(msgs, conditionMessage(w)); invokeRestart("muffleWarning") })
    singular <- isSingular(fit)
    avg <- summary(contrast(emmeans(fit, ~ time), list(`100 hours minus under 1 hour` = c(-1, 0, 1),
                                                       `10 hours minus under 1 hour` = c(-1, 1, 0))),
                   infer = TRUE) %>% as_tibble() %>% mutate(label = "both labels, equal weights")
    by_label <- summary(contrast(emmeans(fit, ~ time | Type), list(`100 hours minus under 1 hour` = c(-1, 0, 1),
                                                                   `10 hours minus under 1 hour` = c(-1, 1, 0))),
                        infer = TRUE) %>% as_tibble() %>% rename(label = Type) %>% mutate(label = as.character(label))
    out <- bind_rows(avg, by_label) %>%
      transmute(analysis_status = ANALYSIS_STATUS, study_pipeline = 3L, study_paper = 2L,
                dimension = dim, model = model, label, contrast = as.character(contrast),
                estimate, std_error = SE, df, ci95_low = lower.CL, ci95_high = upper.CL,
                t = t.ratio, p = p.value, singular = singular,
                fit_messages = paste(unique(msgs), collapse = " | "))
    if (model == "registered model") {
      mine <- out$estimate[out$label == "both labels, equal weights" & out$contrast == "100 hours minus under 1 hour"]
      theirs <- registered$estimate[registered$dimension == dim]
      if (length(theirs) != 1 || abs(mine - theirs) > 1e-8) {
        stop(sprintf("the refit of the registered model does not reproduce Study 3's %s contrast", dim))
      }
    }
    rows[[length(rows) + 1]] <- out
  }
}
result <- bind_rows(rows)
write_csv(result, file.path(TAB_DIR, "hours_check_study2.csv"))
writeLines(capture.output(sessionInfo()), file.path(TAB_DIR, "hours_check_sessionInfo.txt"))
cat("wrote tables/hours_check_study2.csv\n")
