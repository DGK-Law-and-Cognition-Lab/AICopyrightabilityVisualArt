# ---------------------------------------------------------------------------
# text_checks.R
#
# The two text checks the Study 1 registration fixes for every study, as
# functions. The method is the one in section 8 of
# Study 1/Study1_03_Integration.Rmd, unchanged. What a study changes is
# passed as an argument: the rating dimensions the check is registered for,
# the columns that name the stimulus, and the column and levels of the arm.
#
#   text_recoverability()  how closely the words alone track the rating, and
#                          how well they pick out the arm, scored on
#                          participants the model was not fitted to.
#   text_self_overlap()    whether participants in the second arm reuse their
#                          own words across their explanations more than
#                          participants in the first arm, beyond the overlap
#                          with other people writing about the same stimulus.
#
# A stimulus is what one explanation is about. In Studies 1 and 3 it is the
# image (stimulus_id). In Study 5 it is the second work, the source image at
# one modification level, so the stimulus key there is two columns or one
# column that combines them. Whichever it is, the ratings frame and the text
# tables must carry the same key columns.
#
# The arm is the between-participant label the checks compare, such as Type
# with levels Human and AI. The second level is the positive class of every
# AUC and the arm the overlap check predicts to reuse more. Each participant
# carries one arm.
#
# Both checks read tables that the text notebook writes blind to the arm and
# to the rating: the count of each content word in each response, the list of
# those words, and each response's set of distinct content words. A content
# word is a lower-case run of letters and apostrophes left after the
# notebook's fixed list of function words (the, was, of and the like) is
# removed. The functions here join the arm and the rating to those tables and
# run the statistics. check_text_table() stops a run if a text table carries
# the arm, the rating, the text or the condition.
#
# Packages: dplyr and tibble build the tables, Matrix stores the word counts,
# glmnet fits the ridge regressions, and parallel runs the permutations on
# several cores.
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(dplyr)
  library(tibble)
})

# The columns no table from the measurement step may carry.
TEXT_FORBIDDEN_COLS <- c("Type", "rating", "response_text", "condition")

# The registered settings, as Study 1 sets them. The penalty grid of the
# ridge regressions runs from 10,000 down to 0.001 in 100 steps evenly spaced
# on the log scale. It is fixed rather than derived from each training set,
# so that every fold, every permutation and every study searches the same
# candidates.
TEXT_SEED               <- 20260421L
TEXT_N_OUTER_FOLDS      <- 10L
TEXT_N_PERM             <- 200L
TEXT_N_BOOT             <- 2000L
TEXT_WORD_MIN_RESPONSES <- 5L
TEXT_NOTEBOOK_MIN_RESPONSES <- 2L
TEXT_LAMBDA_GRID        <- exp(seq(log(1e4), log(1e-3), length.out = 100))

# Only these fit statuses permit an interval, a null, a p-value or a reading,
# as in fit_status.R.
TEXT_ELIGIBLE_STATUS <- c("ok", "singular")

# How many cores the permutations use: one on Windows, where forked workers
# are not available, and otherwise one fewer than the machine has, up to
# eight.
text_default_workers <- function() {
  if (.Platform$OS.type == "windows") 1L else
    max(1L, min(8L, parallel::detectCores() - 1L))
}

# ---------------------------------------------------------------------------
# Reading the text tables
# ---------------------------------------------------------------------------

# The columns each text table must carry, given the stimulus key.
#   wordcounts  one row per response and word with a count above zero
#   vocabulary  the words the notebook kept, with the number of responses
#               each appears in
#   tokens      one row per response: its distinct content words in lower
#               case, sorted and joined by single spaces (empty when the
#               response has none)
text_table_columns <- function(kind, stim_cols = "stimulus_id") {
  switch(kind,
         wordcounts = c("id", stim_cols, "dimension", "word", "count"),
         vocabulary = c("word", "n_responses"),
         tokens     = c("id", stim_cols, "dimension", "content_words"),
         stop("Unknown text table: ", kind))
}

# Stop unless a text table carries exactly the expected columns and none of
# the forbidden ones. The forbidden columns are checked first, so that a
# broken blind is reported as one rather than as an extra column.
check_text_table <- function(m, expected, label,
                             forbidden = TEXT_FORBIDDEN_COLS) {
  present <- intersect(forbidden, names(m))
  if (length(present) > 0) {
    stop("BLIND BROKEN: ", label, " contains ", paste(present, collapse = ", "),
         ". The text tables may carry neither the condition, nor the rating, ",
         "nor the text. Fix the text notebook that wrote it.")
  }
  missing_cols <- setdiff(expected, names(m))
  extra_cols   <- setdiff(names(m), expected)
  if (length(missing_cols) > 0) {
    stop(label, " is missing required columns: ",
         paste(missing_cols, collapse = ", "))
  }
  if (length(extra_cols) > 0) {
    stop(label, " has columns it should not have: ",
         paste(extra_cols, collapse = ", "))
  }
  invisible(TRUE)
}

# Read the three text tables with their column types stated, and check each
# against its contract. Every key column is read as character. Messages name
# the file and not its folder.
read_text_wordcounts <- function(path, stim_cols = "stimulus_id") {
  cols <- text_table_columns("wordcounts", stim_cols)
  types <- c(rep(list(readr::col_character()), length(cols) - 1),
             list(readr::col_integer()))
  names(types) <- cols
  m <- readr::read_csv(path, col_types = do.call(readr::cols, types),
                       progress = FALSE)
  check_text_table(m, cols, basename(path))
  m
}

read_text_vocabulary <- function(path) {
  m <- readr::read_csv(path, col_types = readr::cols(
    word = readr::col_character(), n_responses = readr::col_integer()),
    progress = FALSE)
  check_text_table(m, text_table_columns("vocabulary"), basename(path))
  m
}

read_text_tokens <- function(path, stim_cols = "stimulus_id") {
  m <- readr::read_csv(path, col_types = readr::cols(.default = readr::col_character()),
                       na = character(), progress = FALSE)
  check_text_table(m, text_table_columns("tokens", stim_cols), basename(path))
  m
}

# ---------------------------------------------------------------------------
# Preparing the ratings
# ---------------------------------------------------------------------------

# The ratings frame both checks take: one row per response, with id, the
# stimulus key columns, dimension, the rating and the arm. A response with no
# rating keeps its row with rating NA; the overlap check uses its words and
# the recoverability check leaves it out. This function returns the columns
# the checks use internally: id as character, .stim (the stimulus key as one
# string: the column itself when the key is one column, the columns joined by
# "|" when it is several), dimension as character, rating, and arm as a
# factor with arm_levels. It stops if a participant carries more than one arm
# or an arm outside arm_levels.
prepare_text_ratings <- function(ratings, stim_cols, arm_col, arm_levels) {
  need <- c("id", stim_cols, "dimension", "rating", arm_col)
  miss <- setdiff(need, names(ratings))
  if (length(miss) > 0) stop("The ratings frame has no column ",
                             paste(miss, collapse = ", "), ".")
  out <- tibble(
    id        = as.character(ratings$id),
    .stim     = stimulus_key(ratings, stim_cols),
    dimension = as.character(ratings$dimension),
    rating    = as.numeric(ratings$rating),
    arm       = factor(as.character(ratings[[arm_col]]), levels = arm_levels)
  )
  if (anyNA(out$arm)) {
    stop("Some rows carry an arm outside ", paste(arm_levels, collapse = ", "), ".")
  }
  if (nrow(distinct(out, id, arm)) != n_distinct(out$id)) {
    stop("Some participant carries more than one arm.")
  }
  if (anyDuplicated(out[, c("id", ".stim", "dimension")]) > 0) {
    stop("The ratings frame has more than one row for some response.")
  }
  out
}

# The stimulus key as one string per row.
stimulus_key <- function(df, stim_cols) {
  if (length(stim_cols) == 1) return(as.character(df[[stim_cols]]))
  do.call(paste, c(lapply(stim_cols, function(col) as.character(df[[col]])),
                   sep = "|"))
}

# A text table with one row per response must name exactly the responses the
# ratings frame names, no more and no fewer.
check_text_response_keys <- function(m, prepared, label) {
  keys_m <- paste(m$id, m$.stim, m$dimension)
  keys_r <- paste(prepared$id, prepared$.stim, prepared$dimension)
  if (anyDuplicated(keys_m) > 0) {
    stop(label, " has more than one row for some response.")
  }
  if (!setequal(keys_m, keys_r)) {
    stop(label, " and the ratings frame name different sets of responses (",
         length(setdiff(keys_m, keys_r)), " only in the table, ",
         length(setdiff(keys_r, keys_m)), " only in the ratings frame).")
  }
  invisible(TRUE)
}

# The three consistency checks between the word-count table, the vocabulary
# and the ratings. (a) Every word counted is in the vocabulary, with the same
# number of responses behind it that the counts themselves show, and that
# number is at least the notebook's floor. (b) Every response the counts name
# exists in the ratings frame, so the join of the rating and the arm cannot
# manufacture rows. (c) The size of the corpus the models will see, returned
# so that a reader can judge the counts against it. A response that used no
# counted word has no row in the counts and enters the models as a row of
# zeros.
check_text_wordcounts <- function(ratings, wordcounts, vocabulary,
                                  stim_cols = "stimulus_id",
                                  arm_col = "Type",
                                  arm_levels = c("Human", "AI"),
                                  notebook_min_responses = TEXT_NOTEBOOK_MIN_RESPONSES) {
  prepared <- prepare_text_ratings(ratings, stim_cols, arm_col, arm_levels)
  wc <- wordcounts
  wc$.stim <- stimulus_key(wc, stim_cols)
  if (anyDuplicated(wc[, c("id", ".stim", "dimension", "word")]) > 0) {
    stop("The word-count table has more than one row for some response and word.")
  }
  freq <- wc %>% count(word, name = "n_in_counts") %>%
    left_join(vocabulary, by = "word")
  if (anyNA(freq$n_responses)) {
    stop("The word-count table uses words the vocabulary table does not list.")
  }
  if (any(freq$n_responses != freq$n_in_counts)) {
    stop("The vocabulary table's n_responses disagrees with the word-count table.")
  }
  if (any(freq$n_responses < notebook_min_responses)) {
    stop("The word-count table keeps words that appear in fewer than ",
         notebook_min_responses, " responses.")
  }
  if (!all(wc$dimension %in% unique(prepared$dimension))) {
    stop("The word-count table names a dimension the ratings frame does not.")
  }
  unmatched <- wc %>% distinct(id, .stim, dimension) %>%
    anti_join(prepared, by = c("id", ".stim", "dimension"))
  if (nrow(unmatched) > 0) {
    stop("The word-count table names ", nrow(unmatched),
         " response(s) the ratings frame does not have.")
  }
  n_with_word <- nrow(distinct(wc, id, .stim, dimension))
  tibble(response_word_rows = nrow(wc), words = n_distinct(wc$word),
         responses = nrow(prepared), responses_with_counted_word = n_with_word,
         responses_without_counted_word = nrow(prepared) - n_with_word)
}

# ---------------------------------------------------------------------------
# Resampling participants
# ---------------------------------------------------------------------------

# A participant bootstrap. The bootstrap builds many pretend re-runs of the
# study out of the data already collected, recomputes a statistic in each,
# and reads the middle 95 percent of the resulting spread as the interval (a
# percentile interval: the 2.5th and 97.5th percentiles of the B recomputed
# values). Each re-run draws as many participants as the data hold, with
# replacement, and takes all of each drawn person's rows, so a person drawn
# twice contributes their whole block twice. Resampling people rather than
# responses is what keeps the interval honest, because one person's
# responses are not independent of one another.
#
# A replicate can be undefined. It is recorded as NA rather than stopping the
# run, and n_valid reports how many replicates were defined. Participants are
# taken in byte order of their identifiers, so the draws do not depend on the
# machine's language setting.
text_boot_by_participant <- function(df, stat_fun, B = TEXT_N_BOOT,
                                     seed = TEXT_SEED) {
  ids_chr   <- as.character(df$id)
  idx_by_id <- split(seq_len(nrow(df)),
                     factor(ids_chr, levels = sort(unique(ids_chr), method = "radix")))
  ids       <- names(idx_by_id)
  n_ids     <- length(ids)

  observed <- stat_fun(df)
  k        <- length(observed)

  set.seed(seed)
  reps <- matrix(NA_real_, nrow = B, ncol = k)
  for (b in seq_len(B)) {
    drawn <- sample(ids, n_ids, replace = TRUE)
    rows  <- unlist(idx_by_id[drawn], use.names = FALSE)
    val   <- stat_fun(df[rows, , drop = FALSE])
    if (length(val) == k) reps[b, ] <- val
  }

  tibble(
    quantity  = if (!is.null(names(observed))) names(observed)
                else paste0("q", seq_len(k)),
    estimate  = as.numeric(observed),
    ci_lo     = apply(reps, 2, quantile, probs = 0.025, na.rm = TRUE, names = FALSE),
    ci_hi     = apply(reps, 2, quantile, probs = 0.975, na.rm = TRUE, names = FALSE),
    B         = B,
    n_valid   = apply(reps, 2, function(x) sum(!is.na(x))),
    resampled = "participants, with replacement"
  )
}

# ===========================================================================
# CHECK 1. HOW CLOSELY THE WORDS TRACK THE RATING AND THE ARM
# ===========================================================================
#
# The question is: given only the words a person wrote, how well can the
# number they gave be guessed, and how well can the arm they were in be
# guessed? Each is answered by fitting a model on some responses and scoring
# it on responses it has never seen, because a model scored on the responses
# it was fitted to can look good by memorising them.
#
# The model is ridge regression: an ordinary regression of the outcome on
# every kept word's count at once, with a penalty added that pulls every
# coefficient toward zero. With several hundred words and about a thousand
# responses an unpenalised regression would fit noise, and the penalty is
# what makes the fit usable. How hard to pull is set by a tuning constant,
# lambda, and lambda is chosen by inner cross-validation: within the training
# responses the model is fitted on nine tenths and scored on the tenth left
# out, for each of ten such splits and for each value of lambda on the fixed
# grid, and the lambda with the best average score is kept. For the arm the
# same machinery is run as a logistic regression (a regression for a yes-or-no
# outcome), so the model predicts a probability of being in the second arm.
#
# The outer split is ten folds GROUPED BY PARTICIPANT: all of a participant's
# responses fall in one fold, so no participant is ever on both the training
# and the test side. People repeat themselves, and a model that had seen most
# of a person's explanations could guess the rest from their habits alone,
# which would recover the person and not the rating. The inner splits are
# grouped the same way. The predictions collected from the ten test folds are
# out-of-fold predictions: every response is predicted by a model that never
# saw it or its author, and every statistic below is computed on those.
#
# THE VOCABULARY IS BUILT INSIDE EACH TRAINING FOLD. The registered floor
# keeps a word only if it appears in at least five responses. Counted over
# the whole corpus, that floor would let the held-out participants decide
# which words become columns. So the floor is applied, for each outer fold,
# to the training responses of the dimension being modelled, and the held-out
# responses are scored on those columns only. The inner cross-validation uses
# the outer fold's vocabulary. Five responses can come from fewer than five
# people, so the floor guards against rare words and does not guarantee that
# no word is one person's habit; the grouped folds keep a habit from scoring.
#
# For the rating the statistic is the Pearson correlation r between the
# out-of-fold prediction and the observed rating, from zero (no relation) to
# one (perfect). A model that has shrunk every coefficient to nothing
# predicts the same number for every response, and that case is scored as
# zero: no recovery. For the arm the statistic is the AUC, the area under the
# receiver operating characteristic curve, read here as the probability that
# a randomly chosen second-arm response gets a higher predicted probability
# of being second-arm than a randomly chosen first-arm response. One half is
# coin-flipping; one is perfect separation. It is computed from the rank
# formula (the Mann-Whitney identity: rank every response by its score, sum
# the second-arm ranks, subtract the smallest sum they could have had, divide
# by the number of cross-arm pairs).
#
# TWO KINDS OF UNCERTAINTY are reported beside each statistic. The 95 percent
# interval comes from resampling participants over the out-of-fold
# predictions; it holds the fitted models fixed, so it leaves out the
# variation that refitting the models on a fresh sample would add. The
# permutation null says what the statistic looks like when the link it is
# about has been cut: the outcome is shuffled, the whole pipeline is run
# again on the shuffled outcome, and the 95th percentile of the shuffled
# statistics is the bar a real one has to clear.
#
# WHAT EACH SHUFFLE CUTS. For the rating the shuffle is RESTRICTED: each
# participant's ratings in the dimension are shuffled among that same
# participant's own explanations, so every person keeps their own ratings
# and their own average, and only which stimulus got which rating is
# scrambled. An observed r above that null says the words carry which
# stimuli a person rated higher. For the arm the shuffle is across
# PARTICIPANTS: each participant keeps one label and the labels are dealt out
# afresh among them, so the shuffled arm keeps the structure the real one
# has, one arm per person.
#
# Beside the arm-from-words AUC sit two models of the arm that use the
# RATING: an ordinary logistic regression of the arm on the rating alone, and
# a ridge logistic regression on the rating and the word counts together,
# with the rating left unpenalised so that it enters as it does in the
# rating-only model and only the words are shrunk. Both are scored on the
# same folds and the same held-out participants, and the difference between
# their AUCs, with an interval from resampling participants over the paired
# held-out predictions, is the incremental AUC: how much the words add to the
# rating in telling the arms apart.
#
# RUNTIME AND REPRODUCIBILITY. Each dimension needs one pass of the pipeline
# for each observed model and n_perm shuffled passes for the rating and for
# the arm, so the shuffled passes run on several cores at once. Every random
# draw, the fold assignments and the shuffled outcomes alike, is made from
# the seed before the parallel section starts, so the numbers do not depend
# on how many cores were used. The table records the number of permutations
# used.
# ---------------------------------------------------------------------------

# Deal participants into K folds, balanced across the arms so that every fold
# holds responses from each. Returns fold numbers named by participant.
text_participant_folds <- function(id_arm, K, arm_levels) {
  fold <- integer(nrow(id_arm))
  for (a in arm_levels) {
    rows <- which(id_arm$arm == a)
    fold[rows] <- sample(rep_len(seq_len(K), length(rows)))
  }
  setNames(fold, id_arm$id)
}

# One dimension's responses in a fixed order (by participant, then
# stimulus), its word counts, and its participants with their arms.
text_dimension_frame <- function(prepared, wordcounts, dim_name) {
  resp <- prepared %>%
    filter(dimension == dim_name, !is.na(rating)) %>%
    arrange(id, .stim)
  counts <- wordcounts %>%
    filter(dimension == dim_name) %>%
    semi_join(resp, by = c("id", ".stim"))
  id_arm <- resp %>% distinct(id, arm) %>% arrange(id)
  list(resp = resp, counts = counts, id_arm = id_arm)
}

# The words that appear in at least `word_min` of the responses marked TRUE
# in `rows`, which index `resp`. This is the registered floor, applied to
# whichever responses a model is allowed to learn from.
text_floor_vocabulary <- function(resp, counts, rows, word_min) {
  keys <- paste(resp$id, resp$.stim)[rows]
  counts %>%
    filter(paste(id, .stim) %in% keys) %>%
    count(word, name = "n_responses") %>%
    filter(n_responses >= word_min) %>%
    arrange(word)
}

# The response-by-word matrix for one dimension. Rows follow `resp`; columns
# are `words`; cells are counts, mostly zero, so the matrix is stored sparsely
# (only the non-zero cells are kept in memory), which is the form glmnet
# takes directly.
text_response_word_matrix <- function(resp, counts, words) {
  key_resp <- paste(resp$id, resp$.stim)
  cnt <- counts %>% filter(word %in% words)
  Matrix::sparseMatrix(
    i = match(paste(cnt$id, cnt$.stim), key_resp),
    j = match(cnt$word, words),
    x = as.numeric(cnt$count),
    dims = c(nrow(resp), length(words)),
    dimnames = list(NULL, words)
  )
}

# Out-of-fold ridge predictions on the response scale (the rating itself for
# the gaussian model, a probability for the binomial one). `X_list[[k]]` is
# the matrix on fold k's training vocabulary; `outer_fold` gives each
# response's fold; `inner_folds[[k]]` gives the inner fold of each training
# response when fold k is held out. `unpenalised`, when given, is a column
# added to every fold's matrix with a penalty factor of zero, so that glmnet
# fits its coefficient without shrinking it.
text_ridge_oof <- function(X_list, y, family, outer_fold, inner_folds,
                           n_folds, lambda_grid, unpenalised = NULL) {
  pred <- rep(NA_real_, length(y))
  for (k in seq_len(n_folds)) {
    tr <- outer_fold != k
    X  <- X_list[[k]]
    pf <- rep(1, ncol(X))
    if (!is.null(unpenalised)) {
      X  <- cbind(Matrix::Matrix(unpenalised, ncol = 1, sparse = TRUE,
                                 dimnames = list(NULL, "rating")), X)
      pf <- c(0, pf)
    }
    cv <- glmnet::cv.glmnet(
      X[tr, , drop = FALSE], y[tr],
      family = family, alpha = 0, lambda = lambda_grid,
      foldid = inner_folds[[k]], penalty.factor = pf
    )
    pred[!tr] <- as.numeric(predict(cv, X[!tr, , drop = FALSE],
                                    s = "lambda.min", type = "response"))
  }
  pred
}

# The comparison model: the arm from the rating alone, same outer folds.
text_rating_oof <- function(rating, y, outer_fold, n_folds) {
  d    <- data.frame(y = y, rating = rating)
  pred <- rep(NA_real_, length(y))
  for (k in seq_len(n_folds)) {
    tr  <- outer_fold != k
    fit <- glm(y ~ rating, data = d[tr, , drop = FALSE], family = binomial)
    pred[!tr] <- unname(predict(fit, newdata = d[!tr, , drop = FALSE],
                                type = "response"))
  }
  pred
}

# Pearson r with a constant prediction scored as zero, and the AUC by the
# rank formula, with ties given their average rank as the Mann-Whitney
# identity requires.
text_oof_r <- function(pred, obs) {
  if (sd(pred) < 1e-12 || sd(obs) < 1e-12) return(0)
  cor(pred, obs)
}

text_auc_rank <- function(score, is_positive) {
  n1 <- sum(is_positive)
  n0 <- sum(!is_positive)
  if (n1 == 0 || n0 == 0) return(NA_real_)
  r <- rank(score)
  (sum(r[is_positive]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

# Run one function over a list of pre-drawn shuffled outcomes, in parallel
# where the platform allows it. Nothing inside draws a random number, so the
# result is the same whatever the number of workers. A failure in a worker is
# raised here rather than returned as a silent gap in the null.
text_run_permutations <- function(items, f, n_workers) {
  out <- if (n_workers > 1L) {
    parallel::mclapply(items, f, mc.cores = n_workers, mc.set.seed = FALSE)
  } else {
    lapply(items, f)
  }
  failed <- vapply(out, inherits, logical(1), what = "try-error")
  if (any(failed)) {
    stop("A permuted pass failed: ",
         conditionMessage(attr(out[[which(failed)[1]]], "condition")))
  }
  unlist(out)
}

# Evaluate an expression and keep every warning it raised. glmnet reports a
# path that stopped short of convergence as a warning, and so does glm for a
# separation problem; any warning from an observed fit gives that dimension's
# rows the status nonconvergence, and the warnings themselves go in the note.
text_with_warnings <- function(expr) {
  warns <- character()
  value <- withCallingHandlers(
    expr,
    warning = function(w) {
      warns <<- c(warns, conditionMessage(w))
      invokeRestart("muffleWarning")
    }
  )
  list(value = value, warnings = unique(warns))
}

# The whole check for one rating dimension: the matrices, the folds, the
# observed statistics, their intervals, and the three permutation nulls.
text_recoverability_dimension <- function(prepared, wordcounts, dim_name, arm_levels,
                                          n_folds, n_perm, seed, word_min,
                                          lambda_grid, n_boot, n_workers,
                                          eligible_status) {
  fr     <- text_dimension_frame(prepared, wordcounts, dim_name)
  resp   <- fr$resp
  counts <- fr$counts
  id_arm <- fr$id_arm
  positive <- arm_levels[2]

  # Every random draw happens here, in a fixed order from the seed: the outer
  # folds, the inner folds for each outer fold, then the shuffled outcomes.
  set.seed(seed)
  outer_by_id <- text_participant_folds(id_arm, n_folds, arm_levels)
  outer_fold  <- unname(outer_by_id[resp$id])
  inner_folds <- lapply(seq_len(n_folds), function(k) {
    tr          <- outer_fold != k
    inner_by_id <- text_participant_folds(id_arm %>% filter(id %in% resp$id[tr]),
                                          n_folds, arm_levels)
    unname(inner_by_id[resp$id[tr]])
  })
  y_rating <- resp$rating
  y_arm    <- as.integer(resp$arm == positive)
  # The restricted rating shuffle: within each participant, that person's
  # ratings are reassigned among their own explanations.
  perm_rating <- replicate(n_perm, {
    ave(y_rating, resp$id, FUN = function(v) v[sample.int(length(v))])
  }, simplify = FALSE)
  perm_arm <- replicate(n_perm, {
    dealt <- setNames(sample(as.character(id_arm$arm)), id_arm$id)
    as.integer(dealt[resp$id] == positive)
  }, simplify = FALSE)

  # One matrix per outer fold, on that fold's training vocabulary. These
  # depend on no outcome, so the shuffled passes reuse them.
  vocab_by_fold <- lapply(seq_len(n_folds), function(k) {
    text_floor_vocabulary(resp, counts, outer_fold != k, word_min)$word
  })
  X_list <- lapply(vocab_by_fold, function(w) {
    text_response_word_matrix(resp, counts, w)
  })
  n_feat <- vapply(X_list, ncol, integer(1))

  ridge <- function(y, family, unpenalised = NULL) {
    text_ridge_oof(X_list, y, family, outer_fold, inner_folds, n_folds,
                   lambda_grid, unpenalised)
  }

  # The observed out-of-fold predictions, with any warning they raised.
  observed <- text_with_warnings(list(
    pred_rating           = ridge(y_rating, "gaussian"),
    pred_arm              = ridge(y_arm, "binomial"),
    pred_arm_from_rating  = text_rating_oof(y_rating, y_arm, outer_fold, n_folds),
    pred_arm_rating_words = ridge(y_arm, "binomial", unpenalised = y_rating)
  ))
  status <- if (length(observed$warnings) == 0) "ok" else "nonconvergence"
  note   <- if (length(observed$warnings) == 0) {
    "status ok; no warning from any observed fit"
  } else {
    paste0("status nonconvergence; ", paste(observed$warnings, collapse = "; "))
  }
  pr <- observed$value

  # The permutation nulls, same pipeline on the shuffled outcomes.
  null_r <- text_run_permutations(perm_rating, function(yp) {
    text_oof_r(ridge(yp, "gaussian"), yp)
  }, n_workers)
  null_auc_words <- text_run_permutations(perm_arm, function(yp) {
    text_auc_rank(ridge(yp, "binomial"), yp == 1L)
  }, n_workers)
  null_auc_rating <- vapply(perm_arm, function(yp) {
    suppressWarnings(text_auc_rank(text_rating_oof(y_rating, yp, outer_fold, n_folds),
                                   yp == 1L))
  }, numeric(1))

  # Participant-resampled intervals over the out-of-fold predictions. The
  # incremental AUC is computed inside each replicate from the paired
  # predictions of the same drawn participants.
  oof <- tibble(
    id                    = resp$id,
    obs_rating            = y_rating,
    obs_arm               = y_arm == 1L,
    pred_rating           = pr$pred_rating,
    pred_arm              = pr$pred_arm,
    pred_arm_from_rating  = pr$pred_arm_from_rating,
    pred_arm_rating_words = pr$pred_arm_rating_words
  )
  boot <- text_boot_by_participant(oof, function(d) {
    auc_r  <- text_auc_rank(d$pred_arm_from_rating, d$obs_arm)
    auc_rw <- text_auc_rank(d$pred_arm_rating_words, d$obs_arm)
    c(rating_from_words          = text_oof_r(d$pred_rating, d$obs_rating),
      arm_from_words             = text_auc_rank(d$pred_arm, d$obs_arm),
      arm_from_rating            = auc_r,
      arm_from_rating_plus_words = auc_rw,
      incremental_auc            = auc_rw - auc_r)
  }, B = n_boot, seed = seed)

  eligible <- status %in% eligible_status
  fold_vocab_text <- paste0("words in at least ", word_min,
                            " training explanations of this dimension, ",
                            "rebuilt in each outer fold")
  auc_text <- paste0("out-of-fold AUC, ", positive, " arm as the positive class")
  tibble(
    dimension  = dim_name,
    target     = c("rating", "arm", "arm", "arm", "arm"),
    predictors = c("words", "words", "rating", "rating plus words",
                   "incremental AUC (rating plus words minus rating)"),
    statistic  = c("out-of-fold Pearson r, predicted vs observed rating",
                   auc_text, auc_text, auc_text,
                   paste0("difference in out-of-fold AUC, rating plus words ",
                          "minus rating, same held-out participants")),
    estimate   = boot$estimate,
    ci_low     = if (eligible) boot$ci_lo else NA_real_,
    ci_high    = if (eligible) boot$ci_hi else NA_real_,
    null_95th  = if (eligible) c(quantile(null_r,          0.95, names = FALSE),
                                 quantile(null_auc_words,  0.95, names = FALSE),
                                 quantile(null_auc_rating, 0.95, names = FALSE),
                                 NA_real_, NA_real_)
                 else NA_real_,
    n_perm     = c(n_perm, n_perm, n_perm, NA_integer_, NA_integer_),
    n_folds    = n_folds,
    n_features = c(median(n_feat), median(n_feat), 1, median(n_feat) + 1,
                   NA_real_),
    n_features_min = c(min(n_feat), min(n_feat), 1, min(n_feat) + 1, NA_real_),
    n_features_max = c(max(n_feat), max(n_feat), 1, max(n_feat) + 1, NA_real_),
    seed       = seed,
    n_boot     = boot$B,
    n_valid    = boot$n_valid,
    n_responses    = nrow(resp),
    n_participants = nrow(id_arm),
    n_responses_without_kept_word = sum(Matrix::rowSums(X_list[[1]]) == 0),
    vocabulary = c(fold_vocab_text, fold_vocab_text, "none",
                   fold_vocab_text, fold_vocab_text),
    model = c(paste0("ridge regression (glmnet, alpha = 0), lambda by inner ",
                     "ten-fold cross-validation grouped by participant"),
              paste0("ridge logistic regression (glmnet, alpha = 0), lambda ",
                     "by inner ten-fold cross-validation grouped by participant"),
              "logistic regression, arm ~ rating, same outer folds",
              paste0("ridge logistic regression on the rating and the word ",
                     "counts, rating unpenalised (penalty factor 0), lambda by ",
                     "inner ten-fold cross-validation grouped by participant"),
              paste0("paired difference of the two rows above, scored on the ",
                     "same held-out participants")),
    permutation = c(paste0("rating shuffled among each participant's own ",
                           "explanations in this dimension; keeps each ",
                           "person's level, so an r above it means the words ",
                           "carry which images a person rated higher"),
                    "arm shuffled across participants",
                    "arm shuffled across participants",
                    "none", "none"),
    status = status,
    note   = note
  )
}

# Check 1 for every dimension in `dims`. Returns one table with five rows per
# dimension: the rating from the words, the arm from the words, the arm from
# the rating, the arm from the rating and the words, and the incremental AUC.
# The model descriptions name ten folds because the registered number is
# ten; n_folds records the number used.
#
#   ratings     one row per response: id, the stim_cols, dimension, rating
#               and the arm column
#   wordcounts  the word-count table (read_text_wordcounts())
#   dims        the rating dimensions the check is registered for
text_recoverability <- function(ratings, wordcounts, dims,
                                stim_cols = "stimulus_id",
                                arm_col = "Type",
                                arm_levels = c("Human", "AI"),
                                n_folds = TEXT_N_OUTER_FOLDS,
                                n_perm = TEXT_N_PERM,
                                seed = TEXT_SEED,
                                word_min_responses = TEXT_WORD_MIN_RESPONSES,
                                lambda_grid = TEXT_LAMBDA_GRID,
                                n_boot = TEXT_N_BOOT,
                                n_workers = text_default_workers(),
                                eligible_status = TEXT_ELIGIBLE_STATUS) {
  stopifnot(length(arm_levels) == 2)
  prepared <- prepare_text_ratings(ratings, stim_cols, arm_col, arm_levels)
  wc <- wordcounts
  wc$.stim <- stimulus_key(wc, stim_cols)
  wc$dimension <- as.character(wc$dimension)
  wc$id <- as.character(wc$id)
  bind_rows(lapply(dims, function(dim_name) {
    text_recoverability_dimension(prepared, wc, dim_name, arm_levels, n_folds,
                                  n_perm, seed, word_min_responses,
                                  lambda_grid, n_boot, n_workers,
                                  eligible_status)
  }))
}

# The registered reading of check 1, one row per dimension and quantity. For
# the stand-alone scores, recovery is read as present when the estimate lies
# above the null's 95th percentile AND the interval is clear of the chance
# value, 0 for r and 0.5 for the AUC; when either clause fails the check has
# not shown recovery, which is a different thing from showing there is none.
# The incremental AUC has no null; its interval is read against zero, and an
# interval that includes zero is inconclusive. A dimension whose observed
# fits did not have status ok gets no reading. The arm from the rating alone
# and from the rating and the words are references and get no reading of
# their own. All of these are descriptive: they enter no correction family
# and support no prediction.
recoverability_readings <- function(tab) {
  tab %>%
    mutate(reading = case_when(
      status != "ok" ~ NA_character_,
      target == "rating" & estimate > null_95th & ci_low > 0 ~ "recovery present",
      target == "rating" & estimate <= null_95th ~
        "not shown: at or below the permutation null",
      target == "rating" ~ "not shown: interval reaches chance",
      predictors == "words" & estimate <= null_95th ~
        "not shown: at or below the permutation null",
      predictors == "words" & ci_low <= 0.5 ~ "not shown: interval reaches chance",
      predictors == "words" ~ "recovery present",
      grepl("^incremental", predictors) & ci_low > 0 ~ "words add to the rating",
      grepl("^incremental", predictors) & ci_high < 0 ~
        "words lower the held-out AUC",
      grepl("^incremental", predictors) ~ "inconclusive",
      TRUE ~ NA_character_
    )) %>%
    select(dimension, target, predictors, estimate, ci_low, ci_high,
           null_95th, reading)
}

# ===========================================================================
# CHECK 2. WITHIN-PERSON WORD OVERLAP BY ARM
# ===========================================================================
#
# From the token table this check computes, for each participant and rating
# dimension:
#
#   self_overlap     the mean Jaccard overlap across every pair of the
#                    participant's explanations. The Jaccard overlap of two
#                    word sets is the number of words in both divided by the
#                    number of words in either, so it runs from zero (no word
#                    shared) to one (the same words).
#   stranger_overlap the same overlap between each of the participant's
#                    explanations and the explanations OTHER participants
#                    wrote about the same stimulus in the same dimension,
#                    averaged first over those other participants and then
#                    over the participant's stimuli. Two people who saw the
#                    same picture share words because the picture supplies
#                    them, and this is how much of that sharing to expect.
#   self_minus_stranger  the difference: how much more a person's
#                    explanations resemble each other than they resemble
#                    strangers' explanations of the same stimuli. This is the
#                    reuse that belongs to the person rather than to the
#                    stimulus, and it is the quantity the arms are compared on.
#   mean_words       the average number of distinct content words per
#                    explanation, carried because the overlap statistic
#                    depends on how much a person writes.
#   n_texts          how many explanations had any content word. An
#                    explanation with none drops out of both overlaps.
#
# The stranger baseline depends on WHO the other participants are. A
# bootstrap replicate draws a new set of participants, and the baseline for
# each of them has to be rebuilt from the others drawn into that replicate.
# So the Jaccard overlap between every pair of participants' explanations of
# each stimulus is computed once, as a matrix per stimulus and dimension,
# and each replicate reweights it by how many times each participant was
# drawn. On the full sample, with every weight equal to one, these are the
# overlaps the registered definition gives.
#
# THE COMPARISON. Within each dimension, self_minus_stranger is regressed on
# the arm with mean_words as a covariate, a variable entered so that the
# arms are compared between participants who wrote the same amount:
#
#   self_minus_stranger ~ arm + mean_words
#
# an ordinary least-squares regression with one row per participant. The arm
# coefficient is the second-minus-first difference in own-word reuse at
# equal length, and it is the registered quantity.
#
# THE INTERVAL. n_boot replicates, each drawing participants with
# replacement WITHIN each arm, so the arm sizes stay what the design
# delivered. In every replicate the stranger baseline is rebuilt from the
# participants drawn into it, a participant drawn twice counting twice among
# everyone else's strangers and never as their own stranger, and the model
# is refitted to the drawn rows. The interval is the middle 95 percent of the
# replicate coefficients.
#
# THE TEST AND ITS CORRECTION. The check predicts that the second arm reuses
# more, so the coefficient is predicted positive. The registered dimensions
# form one family corrected together by the Holm procedure: the p-values are
# ordered, the smallest is compared against alpha divided by the number of
# tests, the next against alpha divided by one fewer, and so on, stopping at
# the first that fails. Each p-value comes from the replicates themselves:
# twice the share of replicate coefficients on the far side of zero, with one
# added to the count and to the number of replicates so that no p-value is
# reported as exactly zero, and capped at one. The reading has three values:
#
#   supported           p_holm below alpha and the estimate positive, the
#                       predicted direction;
#   opposite direction  p_holm below alpha and the estimate negative;
#   inconclusive        p_holm at or above alpha. Inconclusive is not
#                       evidence that the arms reuse their words equally.
#
# The raw self_overlap, stranger_overlap, self_minus_stranger and mean_words
# by arm are reported beside the difference as description, with intervals
# from the same replicates.
# ---------------------------------------------------------------------------

text_split_words <- function(s) {
  if (nzchar(s)) strsplit(s, " ", fixed = TRUE)[[1]] else character(0)
}

text_jaccard <- function(a, b) {
  u <- length(union(a, b))
  if (u == 0) NA_real_ else length(intersect(a, b)) / u
}

# For one dimension: the stranger matrices (overlap of participant i's
# explanation of a stimulus with participant j's, zero on the diagonal and in
# the column of an empty or missing explanation), the matching indicator of
# which entries count, and each participant's self overlap, mean_words and
# n_texts.
text_overlap_inputs <- function(tokens, dim_name, participant_ids, stim_ids) {
  tk <- tokens %>% filter(dimension == dim_name)
  sets <- lapply(stim_ids, function(s) {
    t_s <- tk %>% filter(.stim == s)
    w   <- lapply(t_s$content_words, text_split_words)
    names(w) <- t_s$id
    w[participant_ids]
  })
  names(sets) <- stim_ids
  n <- length(participant_ids)

  J <- V <- vector("list", length(stim_ids))
  names(J) <- names(V) <- stim_ids
  for (s in stim_ids) {
    w   <- sets[[s]]
    ok  <- vapply(w, length, integer(1)) > 0
    m   <- matrix(0, n, n)
    for (i in which(ok)) for (j in which(ok)) {
      if (i < j) m[i, j] <- m[j, i] <- text_jaccard(w[[i]], w[[j]])
    }
    v <- matrix(rep(as.numeric(ok), each = n), n, n)
    diag(v) <- 0
    J[[s]] <- m
    V[[s]] <- v
  }

  per_person <- lapply(seq_len(n), function(i) {
    own <- Filter(length, lapply(stim_ids, function(s) sets[[s]][[i]]))
    pairs <- if (length(own) >= 2) {
      combn(length(own), 2, function(p) text_jaccard(own[[p[1]]], own[[p[2]]]))
    } else numeric(0)
    tibble(id = participant_ids[i], n_texts = length(own),
           self_overlap = if (length(pairs)) mean(pairs) else NA_real_,
           mean_words = if (length(own)) mean(lengths(own)) else NA_real_)
  })
  has_text <- sapply(stim_ids, function(s) lengths(sets[[s]]) > 0)
  list(J = J, V = V, person = bind_rows(per_person), has_text = has_text)
}

# The stranger overlap of every participant, given how many times each
# participant was drawn (w, one weight per participant).
text_stranger_overlap_given <- function(inp, w) {
  per_stim <- sapply(names(inp$J), function(s) {
    num <- as.numeric(inp$J[[s]] %*% w)
    den <- as.numeric(inp$V[[s]] %*% w)
    ifelse(inp$has_text[, s] & den > 0, num / den, NA_real_)
  })
  rowMeans(per_stim, na.rm = TRUE) * ifelse(rowSums(!is.na(per_stim)) > 0, 1, NA)
}

text_selfsim_arm_coef <- function(d, coef_name) {
  d <- d[!is.na(d$self_minus_stranger), , drop = FALSE]
  fit <- tryCatch(lm(self_minus_stranger ~ arm + mean_words, data = d),
                  error = function(e) NULL)
  if (is.null(fit) || !coef_name %in% names(coef(fit))) return(NA_real_)
  unname(coef(fit)[[coef_name]])
}

text_selfsim_levels <- function(d, arm_levels) {
  out <- c()
  for (a in arm_levels) {
    dd <- d[d$arm == a & !is.na(d$self_minus_stranger), , drop = FALSE]
    out[paste0("self_overlap_", a)]        <- mean(dd$self_overlap)
    out[paste0("stranger_overlap_", a)]    <- mean(dd$stranger_overlap)
    out[paste0("self_minus_stranger_", a)] <- mean(dd$self_minus_stranger)
    out[paste0("mean_words_", a)]          <- mean(dd$mean_words)
  }
  out
}

# One dimension: the observed coefficient and levels, then the replicates.
text_selfsim_dimension <- function(inp, base, dim_name, participant_ids,
                                   arm_col, arm_levels, seed, n_boot) {
  stopifnot(identical(base$id, participant_ids))
  coef_name <- paste0("arm", arm_levels[2])

  obs_fit <- tryCatch(lm(self_minus_stranger ~ arm + mean_words,
                         data = base %>% filter(!is.na(self_minus_stranger))),
                      error = function(e) e)
  status <- if (inherits(obs_fit, "error")) "error" else "ok"
  note   <- if (status == "ok") "status ok; ordinary least squares" else
    paste0("status error; ", conditionMessage(obs_fit))

  obs_coef   <- text_selfsim_arm_coef(base, coef_name)
  obs_levels <- text_selfsim_levels(base, arm_levels)

  idx_by_arm <- split(seq_along(participant_ids), base$arm)
  set.seed(seed)
  reps <- matrix(NA_real_, nrow = n_boot, ncol = 1 + length(obs_levels))
  for (b in seq_len(n_boot)) {
    drawn <- unlist(lapply(arm_levels, function(a) {
      ix <- idx_by_arm[[a]]
      ix[sample.int(length(ix), length(ix), replace = TRUE)]
    }), use.names = FALSE)
    w <- tabulate(drawn, nbins = length(participant_ids))
    rep_frame <- base %>%
      mutate(stranger_overlap = text_stranger_overlap_given(inp, w),
             self_minus_stranger = self_overlap - stranger_overlap)
    rep_frame <- rep_frame[drawn, , drop = FALSE]
    reps[b, ] <- c(text_selfsim_arm_coef(rep_frame, coef_name),
                   text_selfsim_levels(rep_frame, arm_levels))
  }

  coef_draws <- reps[, 1]
  coef_draws <- coef_draws[!is.na(coef_draws)]
  p_boot <- if (length(coef_draws) == 0) NA_real_ else
    min(1, 2 * (min(sum(coef_draws <= 0), sum(coef_draws >= 0)) + 1) /
          (length(coef_draws) + 1))

  ci <- function(x) unname(quantile(x, c(0.025, 0.975), na.rm = TRUE))
  ci_coef <- ci(reps[, 1])
  has_pair <- !is.na(base$self_minus_stranger)
  out <- bind_rows(
    tibble(
      quantity = paste0("arm_difference_", arm_levels[2], "_minus_", arm_levels[1]),
      role     = "registered comparison",
      estimate = obs_coef,
      ci_lo    = if (status == "ok") ci_coef[1] else NA_real_,
      ci_hi    = if (status == "ok") ci_coef[2] else NA_real_,
      p_raw    = if (status == "ok") p_boot else NA_real_,
      n_valid  = length(coef_draws),
      model    = paste0("self_minus_stranger ~ ", arm_col,
                        " + mean_words, ordinary least squares"),
      predicted_direction = paste0(arm_levels[2], " > ", arm_levels[1])
    ),
    tibble(
      quantity = names(obs_levels),
      role     = "description, raw level by arm",
      estimate = unname(obs_levels),
      ci_lo    = apply(reps[, -1, drop = FALSE], 2, function(x) ci(x)[1]),
      ci_hi    = apply(reps[, -1, drop = FALSE], 2, function(x) ci(x)[2]),
      p_raw    = NA_real_,
      n_valid  = apply(reps[, -1, drop = FALSE], 2, function(x) sum(!is.na(x))),
      model    = "mean",
      predicted_direction = NA_character_
    )
  ) %>%
    mutate(
      dimension      = dim_name,
      B              = n_boot,
      seed           = seed,
      resampled      = paste0("participants within arm, with replacement; ",
                              "stranger baseline rebuilt from the drawn ",
                              "participants in each replicate"),
      n_participants = sum(has_pair)
    )
  for (a in arm_levels) {
    out[[paste0("n_", tolower(a))]] <- sum(has_pair & base$arm == a)
  }
  out$status <- status
  out$note   <- note
  out
}

# Check 2 for every dimension in `dims`, with Holm across them. Returns a
# list:
#   by_arm      one block of rows per dimension: the registered comparison
#               (with p_raw, p_holm and reading) and the raw levels by arm
#   per_person  one row per participant and dimension: id, n_texts,
#               self_overlap, mean_words, dimension, stranger_overlap,
#               self_minus_stranger and the arm
#
#   ratings  one row per response: id, the stim_cols, dimension, rating and
#            the arm column. Every response with a token row must appear.
#   tokens   the token table (read_text_tokens())
#   dims     the rating dimensions the check is registered for
#
# A participant with fewer than two explanations in a dimension has no pairs
# to overlap and no self_overlap; such rows are left out of the comparison,
# though their explanations still serve as strangers to others.
text_self_overlap <- function(ratings, tokens, dims,
                              stim_cols = "stimulus_id",
                              arm_col = "Type",
                              arm_levels = c("Human", "AI"),
                              seed = TEXT_SEED,
                              n_boot = TEXT_N_BOOT,
                              alpha = 0.05,
                              eligible_status = TEXT_ELIGIBLE_STATUS) {
  stopifnot(length(arm_levels) == 2)
  prepared <- prepare_text_ratings(ratings, stim_cols, arm_col, arm_levels)
  tk <- tokens
  tk$.stim <- stimulus_key(tk, stim_cols)
  tk$id <- as.character(tk$id)
  tk$dimension <- as.character(tk$dimension)
  check_text_response_keys(tk, prepared, "The token table")

  # Participants and stimuli in byte order of their identifiers, so that the
  # draws do not depend on the machine's language setting.
  participant_ids <- sort(unique(prepared$id), method = "radix")
  stim_ids        <- sort(unique(prepared$.stim), method = "radix")
  id_arm <- prepared %>% distinct(id, arm)
  id_arm <- id_arm[match(participant_ids, id_arm$id), , drop = FALSE]
  stopifnot(identical(id_arm$id, participant_ids))

  inputs <- lapply(dims, function(d) {
    text_overlap_inputs(tk, d, participant_ids, stim_ids)
  })
  names(inputs) <- dims

  per_person <- bind_rows(lapply(dims, function(dim_name) {
    inp <- inputs[[dim_name]]
    inp$person %>%
      mutate(dimension = dim_name,
             stranger_overlap = text_stranger_overlap_given(
               inp, rep(1, length(participant_ids))),
             self_minus_stranger = self_overlap - stranger_overlap) %>%
      left_join(id_arm, by = "id")
  }))
  stopifnot(nrow(distinct(per_person, id, dimension)) == nrow(per_person))

  by_arm <- bind_rows(lapply(dims, function(dim_name) {
    base <- per_person %>% filter(dimension == dim_name)
    text_selfsim_dimension(inputs[[dim_name]], base, dim_name, participant_ids,
                           arm_col, arm_levels, seed, n_boot)
  }))
  is_test <- by_arm$role == "registered comparison"
  by_arm$p_holm <- NA_real_
  by_arm$p_holm[is_test] <- p.adjust(by_arm$p_raw[is_test], method = "holm",
                                     n = sum(is_test))
  by_arm <- by_arm %>%
    mutate(reading = case_when(
      role != "registered comparison" ~ NA_character_,
      !status %in% eligible_status | is.na(p_holm) ~ NA_character_,
      p_holm < alpha & estimate > 0 ~ "supported",
      p_holm < alpha & estimate < 0 ~ "opposite direction",
      TRUE ~ "inconclusive"
    )) %>%
    relocate(dimension, role, quantity, estimate, ci_lo, ci_hi, p_raw,
             p_holm, reading)

  names(per_person)[names(per_person) == "arm"] <- arm_col
  list(by_arm = by_arm, per_person = per_person)
}
