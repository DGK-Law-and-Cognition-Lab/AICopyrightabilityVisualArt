# ---------------------------------------------------------------------------
# SampleDescription.R
#
# Describes who was analyzed in each of the five studies, and how many
# different people the five analyzed samples hold.
#
# For each study it reports the number of participants analyzed, their age
# (mean, standard deviation, youngest and oldest) and their answers to the
# gender question. Across the five studies it reports the number of
# different people and how many of them were analyzed in more than one
# study. It is descriptive: it tests no hypothesis, and no registration
# names it.
#
# The analyzed sample of each study is the one that study's own pipeline
# analyzed: the participants in the long data file its real run wrote. This
# script applies no exclusion of its own. Age and gender are read from the
# study's Labels export from Qualtrics, the survey platform, which stores
# each answer as text: the wording of the option chosen, or what the
# participant typed. People are linked across studies by the subject-pool
# participant code in the export's `id` column. In the public copy of the
# project that code is replaced by another code, with the same replacement in
# every study, so the counts come out the same.
#
# Every table it writes holds counts and summaries only. No table holds a
# value that belongs to one participant.
#
# Run it from this folder with
#   Rscript SampleDescription.R
# It needs R 4.5.2 with readr, dplyr and tibble, and the shared helpers in
# shared/R/. Paths are found from this file's own folder; the environment
# variables listed under PATHS can name other folders.
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
})

# The versions this script was written and run with. A run records the
# versions it used beside these and says so if any differs.
PINNED <- c(R = "4.5.2", readr = "2.2.0", dplyr = "1.2.1", tibble = "3.3.1")

# ===========================================================================
# PATHS
# ===========================================================================
#
# This file's folder is found from the command that ran it (Rscript passes
# it as --file=), or is the working folder when the file is sourced. These
# environment variables, named settings that the shell passes to R when it
# starts, override the defaults:
#   SAMPLE_DESCRIPTION_DIR    this folder, where the tables go
#   PIPELINE_DIR              the analysis pipeline folder, two levels up
#   STUDY_SHARED_R            the folder of the shared R helpers
#   STUDY1_DIR to STUDY5_DIR  the five study folders
#   CROSS_STUDY_PROJECT_ROOT  the project root, the folder that holds Data
#                             and Analysis
# Printed paths are relative to the project root, so no printed line names a
# folder particular to one machine.

# Rscript writes each space in that path as "~+~", which is undone here.
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
HERE <- if (length(script_arg) == 1) {
  dirname(normalizePath(gsub("~+~", " ", sub("^--file=", "", script_arg), fixed = TRUE)))
} else {
  getwd()
}
STEP_DIR     <- normalizePath(Sys.getenv("SAMPLE_DESCRIPTION_DIR", HERE), mustWork = TRUE)
PIPELINE_DIR <- normalizePath(Sys.getenv("PIPELINE_DIR", file.path(STEP_DIR, "..", "..")),
                              mustWork = TRUE)
SHARED_R     <- Sys.getenv("STUDY_SHARED_R", file.path(PIPELINE_DIR, "shared", "R"))
source(file.path(SHARED_R, "fit_status.R"))         # paths and the run record
source(file.path(SHARED_R, "qualtrics_import.R"))   # reading a Qualtrics export

PROJECT_ROOT <- find_project_root(start = STEP_DIR, env_var = "CROSS_STUDY_PROJECT_ROOT")
STUDY_NUMBERS <- 1:5
STUDIES <- paste("Study", STUDY_NUMBERS)
STUDY_DIRS <- setNames(lapply(STUDY_NUMBERS, function(n) {
  normalizePath(Sys.getenv(paste0("STUDY", n, "_DIR"),
                           file.path(PIPELINE_DIR, paste("Study", n))),
                mustWork = TRUE)
}), STUDIES)
OUT_TABLES <- file.path(STEP_DIR, "tables")
dir.create(OUT_TABLES, recursive = TRUE, showWarnings = FALSE)

for (s in STUDIES) cat(s, "folder:", relative_path(STUDY_DIRS[[s]], PROJECT_ROOT), "\n")
cat("Tables to:", relative_path(OUT_TABLES, PROJECT_ROOT), "\n")

# The exclusion-flow table each study's real run wrote, whose last row gives
# the size of its analyzed sample. Study 5's is the analyzed flow its first R
# Markdown file writes: the five registered steps and a sixth, added on
# 1 November 2026, that removes the participants who had completed an earlier
# study (study5_exclusion_flow_analyzed.csv); study5_exclusion_flow.csv comes
# from the data build.
FLOW_TABLE <- c("Study 1" = "study1_exclusion_flow.csv",
                "Study 2" = "study2_exclusion_flow.csv",
                "Study 3" = "study3_exclusion_flow.csv",
                "Study 4" = "study4_exclusion_flow.csv",
                "Study 5" = "study5_exclusion_flow_analyzed.csv")

# The column of the Labels export that the long data file's `id` matches. In
# Study 1 the long file's `id` is the subject-pool participant code itself;
# in Studies 2 to 5 it is ResponseId, the random code Qualtrics gives each
# response.
LINK_COLUMN <- c("Study 1" = "id", "Study 2" = "ResponseId", "Study 3" = "ResponseId",
                 "Study 4" = "ResponseId", "Study 5" = "ResponseId")

# The column of the Labels export that holds the subject-pool participant
# code. A code found in two studies' analyzed samples is counted as one
# person analyzed twice.
PERSON_COLUMN <- "id"

# The answers the gender question offered ("What is your gender?"), the same
# in all five surveys, and how they are grouped. A blank cell is listed as
# "(no answer)". Women and men are the answers Female and Male; every other
# answer, a blank included, is grouped as other.
GENDER_ANSWERS <- c("Female", "Male", "Other", "Prefer not to say", "(no answer)")
GENDER_GROUP   <- c("Female" = "women", "Male" = "men", "Other" = "other",
                    "Prefer not to say" = "other", "(no answer)" = "other")

ANALYSIS_STATUS <- paste("descriptive; describes the analyzed samples and tests no",
                         "hypothesis; specified on 19 October 2026")

# The inputs, each with its SHA-256 checksum in the run record.
in_study <- function(s, ...) file.path(STUDY_DIRS[[s]], ...)
labels_export <- function(n) {
  file.path(PROJECT_ROOT, "Data", paste("Study", n), paste0("Study", n, "_Labels.csv"))
}
IN <- character(0)
for (n in STUDY_NUMBERS) {
  s <- paste("Study", n)
  IN[paste0("study", n, "_long")]     <- in_study(s, paste0("study", n, "_long_with_text.csv"))
  IN[paste0("study", n, "_manifest")] <- in_study(s, "tables",
                                                  paste0("study", n, "_quant_run_manifest.csv"))
  IN[paste0("study", n, "_flow")]     <- in_study(s, "tables", FLOW_TABLE[[s]])
  IN[paste0("study", n, "_labels")]   <- labels_export(n)
}
IN["study1_demo_age"]    <- in_study("Study 1", "tables", "study1_demo_age.csv")
IN["study1_demo_gender"] <- in_study("Study 1", "tables", "study1_demo_gender.csv")

# ===========================================================================
# RUN RECORD
# ===========================================================================
#
# The run record (shared/R/fit_status.R) stores the checksum of every input,
# deletes the previous run's manifest now and every output's previous copy
# before anything is computed, and writes the manifest last. A manifest on
# disk therefore means the run reached its end, and a run that stops at a
# failed check leaves no result table behind.

table_path <- function(name) file.path(OUT_TABLES, name)
OUT <- c(
  inputs   = table_path("sample_description_run_inputs.csv"),
  checks   = table_path("sample_description_checks.csv"),
  by_study = table_path("sample_description_by_study.csv"),
  gender   = table_path("sample_description_gender.csv"),
  overlap  = table_path("sample_description_overlap.csv"),
  session  = table_path("sample_description_sessionInfo.txt"),
  versions = table_path("sample_description_package_versions.csv"))

run <- start_run_record(IN, table_path("sample_description_run_manifest.csv"), STEP_DIR)
run_clear_outputs(run, OUT)
cat("Run identifier:", run$run_id, "\n")

# Every table carries the analysis status in its last column, so a table
# read on its own still says what it is.
write_table <- function(df, path) {
  readr::write_csv(mutate(df, analysis_status = ANALYSIS_STATUS), path, na = "NA")
}
write_table(run$inputs, OUT[["inputs"]])

# ===========================================================================
# READ EACH STUDY'S ANALYZED SAMPLE
# ===========================================================================

# Every column is read as text, so that a participant code is kept exactly
# as written.
read_text_csv <- function(path) {
  readr::read_csv(path, col_types = readr::cols(.default = readr::col_character()),
                  progress = FALSE, show_col_types = FALSE)
}

# TRUE when `path` is the file listed under `label` in a study's real run
# manifest: the row says the run wrote it, and its checksum is the file's. A
# blind run writes its manifest to tables/blind_run/ instead, so a match here
# can only come from a real run. Study 1 had no blind mode.
listed_in_manifest <- function(manifest_path, label, path) {
  m <- readr::read_csv(manifest_path, show_col_types = FALSE, progress = FALSE)
  row <- m[m$file == label, ]
  nrow(row) == 1 && isTRUE(as.logical(row$written_this_run)) &&
    identical(row$sha256, unname(tools::sha256sum(path)))
}

check <- function(study, quantity, expected, observed) {
  tibble(study = study, quantity = quantity,
         expected = as.character(expected), observed = as.character(observed),
         pass = identical(as.character(expected), as.character(observed)))
}

# A whole number written alone, with or without spaces around it.
BARE_NUMBER <- "^\\s*[0-9]+\\s*$"

# One study: its analyzed participants, their export records, and every check
# on them. Nothing here is written; only the counts and summaries computed
# from `records` are.
read_study <- function(n) {
  s <- paste("Study", n)
  long <- read_text_csv(IN[[paste0("study", n, "_long")]])
  flow <- read_text_csv(IN[[paste0("study", n, "_flow")]])
  labels <- read_qualtrics_export(IN[[paste0("study", n, "_labels")]])
  ids <- unique(long$id)

  # Each analyzed participant must match exactly one export record.
  link <- labels[[LINK_COLUMN[[s]]]]
  matches <- vapply(ids, function(i) sum(link == i), integer(1))
  records <- labels[match(ids, link), , drop = FALSE]
  person <- records[[PERSON_COLUMN]]
  gender <- ifelse(records$Gender == "", "(no answer)", records$Gender)

  checks <- bind_rows(
    check(s, "long data file equals the one listed in the study's real run manifest", TRUE,
          listed_in_manifest(IN[[paste0("study", n, "_manifest")]],
                             paste0("study", n, "_long_with_text.csv"),
                             IN[[paste0("study", n, "_long")]])),
    check(s, "exclusion-flow table equals the one listed in the same manifest", TRUE,
          listed_in_manifest(IN[[paste0("study", n, "_manifest")]],
                             file.path("tables", FLOW_TABLE[[s]]),
                             IN[[paste0("study", n, "_flow")]])),
    check(s, "participants in the long data file equal the last count of the exclusion flow",
          flow$n[nrow(flow)], length(ids)),
    check(s, paste("analyzed participants matching exactly one record of the Labels export",
                   "(by", LINK_COLUMN[[s]], "in the export)"),
          length(ids), sum(matches == 1)),
    check(s, "analyzed participants with a subject-pool participant code in the export",
          length(ids), sum(!is.na(person) & person != "")),
    check(s, "subject-pool participant codes that repeat within the analyzed sample",
          0, sum(duplicated(person))),
    check(s, "gender answers that are not among the answers the survey offered",
          0, sum(!gender %in% GENDER_ANSWERS)))
  list(study = s, n = length(ids), long = long, records = records, person = person,
       gender = gender, checks = checks)
}

samples <- setNames(lapply(STUDY_NUMBERS, read_study), STUDIES)

# ===========================================================================
# AGE AND GENDER IN EACH STUDY
# ===========================================================================
#
# Age was a free-text answer. readr::parse_number() reads the first number in
# the answer, so "20 years" reads as 20, and an answer with no number reads as
# missing. This is how Study 1's own pipeline reads age
# (Study 1/Study1_01_Quant.Rmd, section 3), and the standard deviation is R's
# sd(), which divides by the number of ages minus one.

age_of <- function(x) suppressWarnings(readr::parse_number(x))

by_study <- bind_rows(lapply(samples, function(d) {
  age <- age_of(d$records$Age)
  g <- table(factor(d$gender, levels = GENDER_ANSWERS))
  tibble(study = d$study,
         n = d$n,
         age_n = sum(!is.na(age)),
         age_mean = mean(age, na.rm = TRUE),
         age_sd = sd(age, na.rm = TRUE),
         age_min = min(age, na.rm = TRUE),
         age_max = max(age, na.rm = TRUE),
         age_answers_not_a_bare_number = sum(!grepl(BARE_NUMBER, d$records$Age)),
         n_women = sum(g[GENDER_GROUP[names(g)] == "women"]),
         n_men = sum(g[GENDER_GROUP[names(g)] == "men"]),
         n_gender_other = sum(g[GENDER_GROUP[names(g)] == "other"]))
}))

gender_table <- bind_rows(lapply(samples, function(d) {
  g <- table(factor(d$gender, levels = GENDER_ANSWERS))
  tibble(study = d$study, gender_answer = names(g),
         gender_group = unname(GENDER_GROUP[names(g)]), n = as.integer(g))
}))

# ===========================================================================
# STUDY 1: THE SAME NUMBERS AS ITS OWN TABLES
# ===========================================================================
#
# Study 1's pipeline already reports age and gender, from its long data file,
# in study1_demo_age.csv and study1_demo_gender.csv; the paper's macros
# \SOneAgeMean, \SOneAgeSD, \SOneAgeMin, \SOneAgeMax, \SOneNFemale, \SOneNMale
# and \SOneNGenderOther are read from them. The numbers here must equal
# them exactly, and the run stops if they do not. The comparison is of the
# numbers as stored, so equal numbers print as equal macros.

s1 <- samples[["Study 1"]]
s1_row <- filter(by_study, study == "Study 1")
demo_age <- readr::read_csv(IN[["study1_demo_age"]], show_col_types = FALSE, progress = FALSE)
demo_gender <- readr::read_csv(IN[["study1_demo_gender"]], show_col_types = FALSE,
                               progress = FALSE)
same_number <- function(a, b) isTRUE(identical(as.double(a), as.double(b)))
number_text <- function(x) format(as.double(x), digits = 15)
age_check <- function(stat, mine, theirs, macro) {
  tibble(study = "Study 1",
         quantity = paste0(stat, " equals study1_demo_age.csv, the source of ", macro),
         expected = number_text(theirs), observed = number_text(mine),
         pass = same_number(mine, theirs))
}
s1_counts <- c(women = s1_row$n_women, men = s1_row$n_men, other = s1_row$n_gender_other)
own_counts <- c(women = sum(demo_gender$n[demo_gender$Gender == "Female"]),
                men = sum(demo_gender$n[demo_gender$Gender == "Male"]),
                other = sum(demo_gender$n[!demo_gender$Gender %in% c("Female", "Male")]))

# The long data file of Study 1 carries each participant's age and gender
# too. They must agree with the export for every analyzed participant.
s1_long_people <- distinct(s1$long, id, Age, Gender)
s1_export_people <- tibble(id = s1$records$id,
                           Age = as.character(age_of(s1$records$Age)),
                           Gender = s1$records$Gender)
s1_long_people$Age <- as.character(as.numeric(s1_long_people$Age))
s1_agree <- nrow(s1_long_people) == nrow(s1_export_people) &&
  nrow(dplyr::setdiff(s1_long_people, s1_export_people)) == 0

study1_checks <- bind_rows(
  check("Study 1", "study1_demo_age.csv equals the one listed in Study 1's real run manifest",
        TRUE, listed_in_manifest(IN[["study1_manifest"]], "tables/study1_demo_age.csv",
                                 IN[["study1_demo_age"]])),
  check("Study 1", "study1_demo_gender.csv equals the one listed in the same manifest",
        TRUE, listed_in_manifest(IN[["study1_manifest"]], "tables/study1_demo_gender.csv",
                                 IN[["study1_demo_gender"]])),
  check("Study 1", "the long data file's age and gender agree with the export for every analyzed participant",
        TRUE, s1_agree),
  check("Study 1", "ages read equal the n of study1_demo_age.csv", demo_age$n, s1_row$age_n),
  age_check("mean age", s1_row$age_mean, demo_age$mean_age, "\\SOneAgeMean"),
  age_check("standard deviation of age", s1_row$age_sd, demo_age$sd_age, "\\SOneAgeSD"),
  age_check("youngest age", s1_row$age_min, demo_age$min_age, "\\SOneAgeMin"),
  age_check("oldest age", s1_row$age_max, demo_age$max_age, "\\SOneAgeMax"),
  check("Study 1", "women equal the Female row of study1_demo_gender.csv (\\SOneNFemale)",
        own_counts[["women"]], s1_counts[["women"]]),
  check("Study 1", "men equal the Male row of study1_demo_gender.csv (\\SOneNMale)",
        own_counts[["men"]], s1_counts[["men"]]),
  check("Study 1", "other answers equal every other row of study1_demo_gender.csv",
        own_counts[["other"]], s1_counts[["other"]]),
  check("Study 1", paste("study1_demo_gender.csv has no answer but Female, Male and Other,",
                         "so its Other row (\\SOneNGenderOther) is the whole other group"),
        TRUE, all(demo_gender$Gender %in% c("Female", "Male", "Other"))))

# ===========================================================================
# PEOPLE ACROSS THE FIVE STUDIES
# ===========================================================================
#
# People are counted by their subject-pool participant code. The codes are
# held in memory only; the table holds counts.

people <- bind_rows(lapply(samples, function(d) tibble(study = d$study, person = d$person)))
studies_per_person <- count(people, person, name = "k")
pairs <- combn(STUDIES, 2, simplify = FALSE)
pair_counts <- bind_rows(lapply(pairs, function(p) {
  tibble(quantity = "people analyzed in both studies",
         studies = paste(p[1], "and", p[2]),
         n = length(intersect(samples[[p[1]]]$person, samples[[p[2]]]$person)))
}))
overlap <- bind_rows(
  tibble(quantity = "participations analyzed (the five samples added together)",
         studies = "Studies 1 to 5", n = nrow(people)),
  tibble(quantity = "different people analyzed",
         studies = "Studies 1 to 5", n = nrow(studies_per_person)),
  tibble(quantity = "people analyzed in two or more studies",
         studies = "Studies 1 to 5", n = sum(studies_per_person$k >= 2)),
  tibble(quantity = "people analyzed in three or more studies",
         studies = "Studies 1 to 5", n = sum(studies_per_person$k >= 3)),
  pair_counts)

flow_total <- sum(vapply(STUDY_NUMBERS, function(n) {
  f <- read_text_csv(IN[[paste0("study", n, "_flow")]])
  as.integer(f$n[nrow(f)])
}, integer(1)))
cross_checks <- check("Studies 1 to 5",
                      "participations equal the five exclusion flows' last counts added together",
                      flow_total, nrow(people))

# ===========================================================================
# WRITE
# ===========================================================================

checks <- bind_rows(bind_rows(lapply(samples, `[[`, "checks")), study1_checks, cross_checks)
write_table(checks, OUT[["checks"]])
cat("Checks:", sum(checks$pass), "of", nrow(checks), "pass\n")
if (!all(checks$pass)) {
  print(as.data.frame(checks[!checks$pass, c("study", "quantity", "expected", "observed")]))
  stop("A check failed, so no result table was written. ",
       "See tables/sample_description_checks.csv.")
}

write_table(by_study, OUT[["by_study"]])
write_table(gender_table, OUT[["gender"]])
write_table(overlap, OUT[["overlap"]])

cat("\nEach study's analyzed sample:\n")
print(as.data.frame(mutate(by_study, across(c(age_mean, age_sd), ~ round(.x, 2)))),
      row.names = FALSE)
cat("\nPeople across the five studies:\n")
print(as.data.frame(overlap), row.names = FALSE)

# ===========================================================================
# SESSION INFORMATION AND THE RUN MANIFEST
# ===========================================================================

writeLines(c(paste("Analysis status:", ANALYSIS_STATUS), "",
             capture.output(sessionInfo())), OUT[["session"]])
used <- c(R = paste(R.version$major, R.version$minor, sep = "."),
          vapply(names(PINNED)[-1], function(p) as.character(packageVersion(p)),
                 character(1)))
versions <- tibble(software = names(PINNED), version_used = unname(used[names(PINNED)]),
                   version_pinned = unname(PINNED),
                   same = version_used == version_pinned)
write_table(versions, OUT[["versions"]])
if (!all(versions$same)) {
  cat("Note: this run used versions other than those the script names:",
      paste(versions$software[!versions$same], collapse = ", "), "\n")
}

# The manifest lists every output with whether this run wrote it and its
# checksum. It is written last, then written again with the analysis status
# as its last column; it does not list itself, so the second write changes
# no checksum in it.
manifest <- write_run_manifest(run)
stopifnot(all(manifest$written_this_run))
write_table(manifest, run$manifest_path)
