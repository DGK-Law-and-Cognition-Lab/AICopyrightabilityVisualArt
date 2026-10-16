# ---------------------------------------------------------------------------
# fit_status.R
#
# Three sets of helpers that every analysis notebook in Studies 2 to 5 uses.
#
#   Fit status     what an lme4 fit's numbers may be used for. A fit that
#                  stopped with an error or did not converge carries no
#                  p-value, interval or verdict. The rule and the code are
#                  those of Study 1/Study1_01_Quant.Rmd, section 7.
#   Run record     which inputs a run read, which outputs it was responsible
#                  for, and whether it wrote each one. The code follows the
#                  run record of Study1_01_Quant.Rmd (sections 1.2 and 13.1).
#   Blind switch   a run on shuffled condition labels, written to its own
#                  folders, so that every step of an analysis can be built
#                  and checked before any result by condition is seen.
#
# Paths. No path in these helpers is written into a file or a message as an
# absolute path. find_project_root() finds the project root (the folder that
# holds Data and Analysis) by walking up from the working directory, which is
# the notebook's own folder when the notebook is knitted, and an environment
# variable can name the root instead. relative_path() turns a path into one
# relative to a folder for printing.
#
# Packages: tibble and dplyr build the tables, readr writes them, and lme4
# supplies the fits whose status is read.
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(dplyr)
  library(tibble)
})

# ===========================================================================
# PATHS
# ===========================================================================

# The project root. When `env_var` names an environment variable that is
# set, its value is the root. Otherwise the root is the first folder at or
# above `start` that holds both a Data and an Analysis folder. The search
# stops with a message, which names no folder, if neither finds one.
find_project_root <- function(start = getwd(), env_var = NULL) {
  is_root <- function(p) dir.exists(file.path(p, "Data")) &&
                         dir.exists(file.path(p, "Analysis"))
  if (!is.null(env_var) && nzchar(Sys.getenv(env_var))) {
    root <- normalizePath(Sys.getenv(env_var), mustWork = FALSE)
    if (!is_root(root)) {
      stop("The folder ", env_var, " names has no Data and Analysis folders.")
    }
    return(root)
  }
  p <- normalizePath(start, mustWork = TRUE)
  repeat {
    if (is_root(p)) return(p)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  stop("No folder at or above the working directory holds both Data and ",
       "Analysis. Knit the notebook from its own folder",
       if (!is.null(env_var)) paste0(", or set ", env_var, " to the project root"),
       ".")
}

# A path in its full form, with links resolved. A file that does not exist
# yet (or no longer exists) is resolved through its folder, so that it
# compares equal to the folder's other files.
full_path <- function(p) {
  vapply(p, function(x) {
    if (file.exists(x)) return(normalizePath(x))
    d <- dirname(x)
    if (dir.exists(d)) file.path(normalizePath(d), basename(x))
    else normalizePath(x, mustWork = FALSE)
  }, character(1), USE.NAMES = FALSE)
}

# `path` relative to `base`, for printing and for the run manifest. A path
# outside `base` comes back as its file name alone.
relative_path <- function(path, base) {
  path <- full_path(path)
  base <- full_path(base)
  inside <- startsWith(path, paste0(base, "/"))
  ifelse(inside, substring(path, nchar(base) + 2), basename(path))
}

# ===========================================================================
# FIT STATUS
# ===========================================================================
#
# Fit status, read the same way for every lme4 fit whose numbers a notebook
# reports. One row with four columns:
#   fit_error      TRUE when the call stopped with an error and returned no
#                  fit.
#   converged      TRUE when the optimizer, the routine that searches for the
#                  best-fitting parameter values, reported success (return
#                  code 0) and lme4's convergence checks raised no message
#                  and no optimizer warning was recorded. The checks are the
#                  ones lmerControl() names check.conv: lme4 runs them after
#                  the fit, on the gradient (the slope of the likelihood at
#                  the solution, zero at a true optimum) and on the Hessian
#                  (the matrix of second derivatives the standard errors come
#                  from). lme4's notice of a singular fit is recorded with
#                  those messages but is not a convergence failure, so it is
#                  left out of this test.
#   singular       isSingular() at tol = 1e-4: at least one random-effect
#                  variance or correlation sits at the boundary of its range
#                  (a variance at zero or a correlation at plus or minus one).
#   lme4_messages  every message lme4 recorded and every warning captured
#                  while fitting, joined with " | ", or "" for none.
# A reported p-value or verdict that rests on a fit with fit_error TRUE or
# converged FALSE is set to NA, and the table says why in a note column. A
# singular fit that converged keeps its numbers, and its singular column
# says where it stands.
# ---------------------------------------------------------------------------
lmer_fit_status <- function(fit, warnings = character(0)) {
  if (inherits(fit, "error")) {
    return(tibble(fit_error = TRUE, converged = FALSE, singular = NA,
                  lme4_messages = conditionMessage(fit)))
  }
  if (is.null(fit)) {
    return(tibble(fit_error = TRUE, converged = FALSE, singular = NA,
                  lme4_messages = "no fit was returned"))
  }
  msgs <- c(as.character(unlist(fit@optinfo$conv$lme4$messages)),
            as.character(unlist(fit@optinfo$warnings)),
            as.character(warnings))
  failure_msgs <- msgs[!grepl("singular", msgs, ignore.case = TRUE)]
  tibble(fit_error     = FALSE,
         converged     = isTRUE(all(fit@optinfo$conv$opt == 0)) &&
                         length(failure_msgs) == 0,
         singular      = lme4::isSingular(fit, tol = 1e-4),
         lme4_messages = paste(unique(msgs), collapse = " | "))
}

# TRUE when a fit's numbers may be reported; the note says why when not.
fit_usable <- function(status) {
  !isTRUE(status$fit_error) && isTRUE(status$converged)
}

fit_note <- function(status, what = "p-value") {
  if (isTRUE(status$fit_error)) {
    paste0("fit stopped with an error, so the ", what, " is set to NA")
  } else if (!isTRUE(status$converged)) {
    paste0("fit did not converge, so the ", what, " is set to NA")
  } else ""
}

# `x` when the fit is usable, and otherwise `x` with every value set to NA,
# keeping its type and length. Every p-value, interval and verdict column
# passes through this before it is written.
na_unless_usable <- function(x, status) {
  if (fit_usable(status)) return(x)
  x[] <- NA
  x
}

# Fit a model and keep its status. `expr` is the fitting call, such as
# lmerTest::lmer(rating ~ Type + (1 | id), data = d). Warnings are caught by
# a calling handler, a hook that sees each warning as it is raised and lets
# the fit continue, so the fit is kept and the warning is kept; an error is
# kept in place of the fit. Returns list(fit, warnings, status), with status
# from lmer_fit_status().
fit_with_status <- function(expr) {
  warns <- character(0)
  fit <- withCallingHandlers(
    tryCatch(expr, error = function(e) e),
    warning = function(w) {
      warns <<- c(warns, conditionMessage(w))
      invokeRestart("muffleWarning")
    }
  )
  list(fit = fit, warnings = warns, status = lmer_fit_status(fit, warns))
}

# ===========================================================================
# RUN RECORD
# ===========================================================================
#
# Every file a notebook writes is tied to one run of it.
#
#   run_start     the clock time at which the run began. The manifest
#                 compares each output's modification time against it, so a
#                 file the run did not write reads as not written this run.
#   sha256        the SHA-256 checksum of each input file, a 64-character
#                 fingerprint of the file's exact bytes that changes if any
#                 byte of the file changes.
#   run_id        the start time followed by the first eight characters of a
#                 checksum taken over the input checksums, so two runs on the
#                 same inputs share the suffix and a run on different inputs
#                 does not.
#
# start_run_record() deletes the previous run's manifest before anything else
# is written, so a run that stops part way leaves no manifest, and a file
# downstream that requires one cannot take a half-finished set of outputs for
# a finished one.
#
# run_clear_outputs() is called at the top of every chunk that writes a
# file. It deletes that chunk's outputs from the previous run before the
# chunk computes anything, so a chunk that fails leaves its files missing
# rather than leaving the previous run's copies in place, and it adds each
# path to the list the manifest is built from.
#
# The record is an environment, an R object that functions can change in
# place, so the list of outputs grows as the notebook runs without a global
# variable.
# ---------------------------------------------------------------------------

# Start a run. `inputs` is a named character vector of the input files.
# `manifest_path` is where write_run_manifest() will write the manifest.
# `base_dir` is the folder the manifest's paths are written relative to,
# usually the study folder. `other_dirs` is an optional named vector of
# further folders the run writes to, each name being the label its paths
# carry in the manifest (such as c("Docs/Writing/Final Paper" = paper_dir)).
start_run_record <- function(inputs, manifest_path, base_dir,
                             other_dirs = character(0)) {
  if (is.null(names(inputs)) || any(names(inputs) == "")) {
    stop("Every input needs a name.")
  }
  if (!all(file.exists(inputs))) {
    stop("Cannot find the input(s): ",
         paste(basename(inputs[!file.exists(inputs)]), collapse = ", "))
  }
  run <- new.env(parent = emptyenv())
  run$run_start <- Sys.time()
  sha <- unname(tools::sha256sum(inputs))
  # tools::sha256sum() reads files, so the checksum over the input checksums
  # is taken on a temporary file holding them one per line.
  hash_file <- tempfile(fileext = ".txt")
  writeLines(sha, hash_file)
  run$run_id <- paste0(format(run$run_start, "%Y%m%dT%H%M%S"), "-",
                       substr(unname(tools::sha256sum(hash_file)), 1, 8))
  unlink(hash_file)
  run$inputs <- tibble(run_id = run$run_id,
                       input  = names(inputs),
                       file   = basename(inputs),
                       bytes  = unname(file.size(inputs)),
                       sha256 = sha)
  run$manifest_path <- manifest_path
  run$base_dir      <- base_dir
  run$other_dirs    <- other_dirs
  run$outputs       <- character(0)
  unlink(manifest_path)
  run
}

# Register paths as this run's outputs and delete their previous copies.
run_clear_outputs <- function(run, ...) {
  paths <- c(...)
  run$outputs <- union(run$outputs, paths)
  unlink(paths)
  invisible(paths)
}

# Write the input record, one row per input file with its size and checksum,
# as one of the run's outputs.
write_run_inputs <- function(run, path) {
  run_clear_outputs(run, path)
  readr::write_csv(run$inputs, path)
  invisible(run$inputs)
}

# The label a path carries in the manifest: relative to base_dir, or to one
# of other_dirs under that folder's label, or its file name alone.
run_path_label <- function(run, p) {
  p <- full_path(p)
  dirs <- c(stats::setNames(run$base_dir, ""), run$other_dirs)
  for (i in seq_along(dirs)) {
    d <- full_path(dirs[[i]])
    if (startsWith(p, paste0(d, "/"))) {
      rel <- substring(p, nchar(d) + 2)
      return(if (names(dirs)[i] == "") rel else file.path(names(dirs)[i], rel))
    }
  }
  basename(p)
}

# Write the manifest: one row per registered output, in the order the chunks
# registered them.
#   run_id            this run's identifier.
#   file              the path, labelled by run_path_label().
#   written_this_run  TRUE when the file exists and its modification time is
#                     no earlier than the second in which the run started.
#                     Every listed file was deleted at the top of the chunk
#                     that writes it, so FALSE means that chunk wrote nothing.
#   sha256            the file's SHA-256 checksum, NA when it does not exist.
# The manifest does not list itself. Returns the manifest.
write_run_manifest <- function(run) {
  paths     <- setdiff(run$outputs, run$manifest_path)
  start_sec <- trunc(run$run_start, units = "secs")
  exists_now <- file.exists(paths)
  manifest <- tibble(
    run_id           = run$run_id,
    file             = vapply(paths, function(p) run_path_label(run, p),
                              character(1), USE.NAMES = FALSE),
    written_this_run = exists_now & file.mtime(paths) >= start_sec,
    sha256           = ifelse(exists_now,
                              unname(tools::sha256sum(paths)),
                              NA_character_)
  ) %>%
    mutate(written_this_run = coalesce(written_this_run, FALSE))
  cat("Outputs listed:", nrow(manifest),
      "| written this run:", sum(manifest$written_this_run),
      "| not written:", sum(!manifest$written_this_run), "\n")
  if (any(!manifest$written_this_run)) {
    cat("Not written this run:\n")
    print(manifest$file[!manifest$written_this_run])
  }
  readr::write_csv(manifest, run$manifest_path)
  invisible(manifest)
}

# ===========================================================================
# BLIND SWITCH
# ===========================================================================
#
# A blind run is the whole analysis run on condition labels that have been
# shuffled across participants. Every model, table and figure is produced
# and can be checked for errors, but no number in it says anything about the
# real conditions, because the link between each person and their condition
# has been cut. Its outputs go to a blind_run/ folder inside the study
# folder, so that they cannot overwrite or be mistaken for the real ones.
#
# The switch is the environment variable STUDY_BLIND. A run is blind unless
# STUDY_BLIND is set to FALSE (or false, 0 or no), so that forgetting to set
# it produces a blind run and never an unblinded one.
# ---------------------------------------------------------------------------

# TRUE unless STUDY_BLIND turns blinding off.
blind_mode <- function() {
  v <- tolower(trimws(Sys.getenv("STUDY_BLIND", unset = "TRUE")))
  !(v %in% c("false", "0", "no"))
}

# Shuffle the between-participant labels of `df` across participants. The
# columns in `label_cols` move together as one unit, so each participant
# receives another participant's whole set of labels (in Study 5, the
# source condition and the editing time together), every combination keeps
# the number of participants it had, and every row of a participant carries
# the same new labels. The shuffle stops if some participant carries more
# than one set of labels, since a label that varies within a person is not
# between-participant.
#
# Participants are taken in byte order of their identifiers and dealt their
# new labels from a permutation drawn with `seed`, so the shuffle is the same
# on every machine. The random-number state is put back afterwards, so
# turning the blind on or off changes no other random draw in the run.
blind_shuffle <- function(df, id_col, label_cols, seed) {
  miss <- setdiff(c(id_col, label_cols), names(df))
  if (length(miss) > 0) stop("df has no column ", paste(miss, collapse = ", "), ".")
  units <- distinct(df[, c(id_col, label_cols), drop = FALSE])
  if (anyDuplicated(units[[id_col]]) > 0) {
    stop("Some participant carries more than one set of the labels ",
         paste(label_cols, collapse = ", "), ", so they are not between-participant.")
  }
  ids   <- as.character(units[[id_col]])
  units <- units[order(ids, method = "radix"), , drop = FALSE]

  had_seed <- exists(".Random.seed", envir = globalenv(), inherits = FALSE)
  if (had_seed) old_seed <- get(".Random.seed", envir = globalenv())
  on.exit({
    if (had_seed) assign(".Random.seed", old_seed, envir = globalenv())
    else rm(".Random.seed", envir = globalenv())
  }, add = TRUE)
  set.seed(seed)
  perm <- sample.int(nrow(units))

  dealt <- units[perm, label_cols, drop = FALSE]
  dealt[[id_col]] <- units[[id_col]]
  out <- df
  m <- match(as.character(out[[id_col]]), as.character(dealt[[id_col]]))
  for (col in label_cols) out[[col]] <- dealt[[col]][m]
  attr(out, "blind_shuffle") <- list(seed = seed, label_cols = label_cols,
                                     n_participants = nrow(units))
  out
}

# The output folders of a run. When `blind` is TRUE every folder sits inside
# <study_dir>/blind_run/, and so does the copy for the paper when
# `paper_dir` is given; when FALSE the folders sit in the study folder and
# the paper copy goes to `paper_dir` itself. With create = TRUE the folders
# are made, and a blind run's folder gets a short note saying what it is.
# Returns a named list: root, blind (the switch as given), one entry per
# subfolder, and paper (NULL when no paper_dir is given).
blind_paths <- function(study_dir, blind = blind_mode(),
                        subdirs = c("tables", "figures", "models"),
                        paper_dir = NULL, create = TRUE) {
  root <- if (blind) file.path(study_dir, "blind_run") else study_dir
  out  <- list(root = root, blind = blind)
  for (s in subdirs) out[[s]] <- file.path(root, s)
  out$paper <- if (is.null(paper_dir)) NULL
               else if (blind) file.path(root, "paper") else paper_dir
  if (create) {
    for (p in c(out$root, unlist(out[subdirs]), out$paper)) {
      dir.create(p, recursive = TRUE, showWarnings = FALSE)
    }
    if (blind) {
      writeLines(c(
        "Outputs of a blind run.",
        "The condition labels were shuffled across participants before any",
        "model was fitted, so no number in this folder describes the real",
        "conditions. A run with STUDY_BLIND set to FALSE writes the real",
        "outputs to the study folder."),
        file.path(root, "BLIND_RUN.txt"))
    }
  }
  out
}
