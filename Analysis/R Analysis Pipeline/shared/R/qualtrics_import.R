# ---------------------------------------------------------------------------
# qualtrics_import.R
#
# Reading a Qualtrics export and its survey file, screening the records, and
# scoring the rating items by position. Studies 2 to 5 source this file.
#
# Qualtrics, the survey platform, exports each study twice. The Values export
# stores each answer as a number and the Labels export stores the same answer
# as the text the participant saw. Both are CSV files (comma-separated
# values, a plain-text table) with two metadata rows under the header: the
# full question text, then a row of import identifiers.
#
# The numbers in the Values export are raw choice codes, the internal
# identifiers Qualtrics gave each answer option when the question was built.
# They are not scale positions. In the Study 5 survey "Highly transformative"
# is 14 on one item and 26 on another, and the codes on one item need not run
# in sequence: Study 3's 1FigureEff offers codes 1, 2, 3, 6 and 7. So a
# rating is scored from its label. The label is looked up in the item's
# answer options, taken in the order the options were shown on screen, and
# its place in that list (1 for the first option, k for the last) is the
# score.
#
# That order comes from the .qsf file, the survey definition Qualtrics
# exports as JSON (a plain-text format for nested lists and named fields).
# Each question in it carries Choices, the answer options keyed by choice
# code, and ChoiceOrder, the codes in on-screen order from top to bottom.
#
# The reference implementation of the same steps in Python is
# Study 5/study5_build.py. On the Study 5 exports the two give the same
# rating for every answer.
#
# Packages: readr reads the CSV files, jsonlite reads the .qsf, and dplyr
# and tibble build the tables.
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tibble)
})

# ---------------------------------------------------------------------------
# The two families of rating items, named by their export tags. An export tag
# is the column name Qualtrics gives a question in both exports.
#
#   original    a rating of an original artwork: image number, image kind,
#               dimension, as in 3NonFigureEff (the third non-figurative
#               image, effort). Studies 1 and 3.
#   derivative  a rating of a second work made from an original: image
#               number, image kind, modification level, dimension, as in
#               1FigureMinTrans (the first figurative image, slight
#               modification, transformativeness). Studies 2, 4 and 5.
#
# An image kind is Figure (the image shows a human or humanoid figure) or
# NonFigure. A regular expression, the pattern language R uses to match
# text, picks out each family's tags, and its bracketed groups capture the
# parts of the name in the order listed under `parts`.
# ---------------------------------------------------------------------------
ITEM_FAMILIES <- list(
  original = list(
    pattern = "^(\\d)(Figure|NonFigure)(Creat|Eff)$",
    parts   = c("image", "stimulus_type", "dimension"),
    dimension_names = c(Creat = "creativity", Eff = "effort")
  ),
  derivative = list(
    pattern = "^(\\d)(Figure|NonFigure)(None|Min|Max)(Trans|Ess|Creat)$",
    parts   = c("image", "stimulus_type", "modification", "dimension"),
    dimension_names = c(Trans = "transformativeness",
                        Ess   = "essence_change",
                        Creat = "creativity"),
    modification_names = c(None = "None", Min = "Slight", Max = "Dramatic")
  )
)

# Each rating is followed by a required written justification. Its column is
# the rating item's tag with one of three endings, which vary from item to
# item: 1FigureNoneCreatResp, 1NonFigureMaxCreatRe, 1NonFigureNoneCreatR.
JUSTIFICATION_SUFFIXES <- c("Resp", "Re", "R")

# The character codes that occur in the survey text, each with the character
# it stands for. An HTML entity is such a code: &amp; is how a web page writes
# an ampersand. Numeric codes such as &#8217; are decoded separately by
# decode_numeric_entities().
HTML_ENTITIES <- c(
  "&nbsp;"  = " ",
  "&amp;"   = "&",
  "&quot;"  = "\"",
  "&#39;"   = "'",
  "&rsquo;" = "'",
  "&ldquo;" = "\"",
  "&rdquo;" = "\"",
  "&lsquo;" = "'"
)

# ---------------------------------------------------------------------------
# Where a study's files are
# ---------------------------------------------------------------------------

# The paths of one study's two exports and its survey file, under the project
# root (the folder that holds Data and Analysis). The exports are
# Data/Study N/StudyN_Values.csv and StudyN_Labels.csv. The survey file is
# looked for in the study's own analysis folder first and in Exported Studies
# second, the two places the project keeps it.
study_export_paths <- function(root, study) {
  data_dir <- file.path(root, "Data", paste("Study", study))
  pipeline <- file.path(root, "Analysis", "R Analysis Pipeline")
  qsf_name <- paste0("Final_-_AI_Copyright_-_Study_", study, ".qsf")
  qsf_candidates <- c(file.path(pipeline, paste("Study", study), qsf_name),
                      file.path(pipeline, "Exported Studies", qsf_name))
  qsf <- qsf_candidates[file.exists(qsf_candidates)][1]
  if (is.na(qsf)) stop("Cannot find ", qsf_name, " in the study folder or ",
                       "in Exported Studies.")
  list(values = file.path(data_dir, paste0("Study", study, "_Values.csv")),
       labels = file.path(data_dir, paste0("Study", study, "_Labels.csv")),
       qsf    = qsf)
}

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

# Replace every numeric entity (&#NNN; in decimal, &#xHH; in hexadecimal)
# with the character it names. A code that names no character is left as it
# is.
decode_numeric_entities <- function(x) {
  m <- gregexpr("&#(x[0-9A-Fa-f]+|[0-9]+);", x, perl = TRUE)
  regmatches(x, m) <- lapply(regmatches(x, m), function(codes) {
    if (length(codes) == 0) return(codes)
    body <- sub(";$", "", sub("^&#", "", codes))
    num  <- ifelse(grepl("^x", body),
                   strtoi(sub("^x", "", body), 16L),
                   strtoi(body, 10L))
    out <- vapply(num, function(n) {
      if (is.na(n) || n < 1L || n > 1114111L) NA_character_ else intToUtf8(n)
    }, character(1))
    ifelse(is.na(out), codes, out)
  })
  x
}

# Clean a piece of survey text: remove HTML tags (the markup in angle
# brackets, such as <br> or <span>) by turning each into a space, decode the
# entities, collapse every run of white space into one space, and trim both
# ends. Missing text becomes "". The steps and their order follow clean() in
# study5_build.py.
qualtrics_clean_text <- function(x) {
  x <- as.character(x)
  x[is.na(x)] <- ""
  x <- gsub("<[^>]+>", " ", x, perl = TRUE)
  for (code in names(HTML_ENTITIES)) {
    x <- gsub(code, HTML_ENTITIES[[code]], x, fixed = TRUE)
  }
  x <- decode_numeric_entities(x)
  x <- gsub("[\\s\\p{Z}]+", " ", x, perl = TRUE)
  trimws(x, whitespace = "[\\h\\v]")
}

# Trim white space from both ends of an answer, including the non-breaking
# and other Unicode spaces, and turn a missing answer into "".
trim_answer <- function(x) {
  x <- as.character(x)
  x[is.na(x)] <- ""
  trimws(x, whitespace = "[\\h\\v]")
}

# ---------------------------------------------------------------------------
# Reading the exports
# ---------------------------------------------------------------------------

# Read one Qualtrics export as text. Every column is read as character, an
# empty cell stays "" rather than becoming NA (so a justification that reads
# "NA" stays text), and nothing is trimmed. The header gives the column
# names, and the two metadata rows under it are dropped after the file is
# parsed rather than skipped as lines, because a question text can run over
# several lines inside its quotation marks. The second metadata row is the
# row of import identifiers, and the read stops if it is not. Messages name
# the file and not its folder.
read_qualtrics_export <- function(path) {
  if (!file.exists(path)) stop("Cannot find the export ", basename(path))
  raw <- readr::read_csv(
    path,
    col_types      = readr::cols(.default = readr::col_character()),
    na             = character(),
    trim_ws        = FALSE,
    name_repair    = "minimal",
    progress       = FALSE,
    show_col_types = FALSE
  )
  dup <- unique(names(raw)[duplicated(names(raw))])
  if (length(dup) > 0) {
    stop(basename(path), " has duplicated column names: ",
         paste(dup, collapse = ", "))
  }
  if (nrow(raw) < 2 || !grepl("ImportId", raw[[1]][2], fixed = TRUE)) {
    stop(basename(path), ": the second row under the header is not the row ",
         "of import identifiers, so this is not a standard Qualtrics export.")
  }
  raw[-(1:2), , drop = FALSE]
}

# Read the Values and Labels exports of one study and check that they hold the
# same records in the same order, which every later step assumes: record i of
# one export is record i of the other.
read_qualtrics_pair <- function(values_path, labels_path, id_col = "ResponseId") {
  values <- read_qualtrics_export(values_path)
  labels <- read_qualtrics_export(labels_path)
  if (nrow(values) != nrow(labels)) {
    stop("The Values and Labels exports differ in length (", nrow(values),
         " and ", nrow(labels), " records).")
  }
  if (!identical(values[[id_col]], labels[[id_col]])) {
    stop("The Values and Labels exports do not list the same ", id_col,
         " values in the same order.")
  }
  list(values = values, labels = labels)
}

# ---------------------------------------------------------------------------
# Screening the records
# ---------------------------------------------------------------------------

# Apply a study's exclusion steps in order and count the records left after
# each. `steps` is a named list of functions. Each takes the two exports as
# they stand after the steps before it (values, labels) and returns TRUE for
# every record to keep. The names label the rows of the flow table, and the
# first row counts the records in the export.
#
# Returns a list:
#   values, labels  the records that pass every step, still in matching order
#   flow            one row per step: step, n (records left after it) and
#                   removed (records the step removed)
exclusion_flow <- function(values, labels, steps,
                           first_row = "records in export") {
  if (nrow(values) != nrow(labels)) {
    stop("values and labels must hold the same records in the same order.")
  }
  if (length(steps) == 0 || is.null(names(steps)) || any(names(steps) == "")) {
    stop("Every exclusion step needs a name.")
  }
  flow <- tibble(step = first_row, n = nrow(values), removed = NA_integer_)
  for (nm in names(steps)) {
    keep <- steps[[nm]](values, labels)
    if (!is.logical(keep) || length(keep) != nrow(values) || anyNA(keep)) {
      stop("The step '", nm, "' must return TRUE or FALSE for every record.")
    }
    values <- values[keep, , drop = FALSE]
    labels <- labels[keep, , drop = FALSE]
    flow <- bind_rows(flow, tibble(step = nm, n = nrow(values),
                                   removed = sum(!keep)))
  }
  list(values = values, labels = labels, flow = flow)
}

# ---------------------------------------------------------------------------
# Reading the survey file
# ---------------------------------------------------------------------------

# Read a .qsf file as nested lists, exactly as the JSON lays it out.
read_qsf <- function(path) {
  if (!file.exists(path)) stop("Cannot find the survey file ", basename(path))
  jsonlite::read_json(path, simplifyVector = FALSE)
}

# The question identifiers (QID numbers) in the survey's Trash block. These
# questions were deleted before the survey ran but stay in the .qsf, and a
# deleted question can carry the export tag of a live one. In the Study 2, 4
# and 5 survey files the deleted QID28 and the live QID29 are both tagged
# 1FigureMaxCreat. In the Study 1 and 3 files every derivative-family
# question sits in the Trash block.
qsf_trash_questions <- function(qsf) {
  out <- character(0)
  for (e in qsf$SurveyElements) {
    if (!identical(e$Element, "BL")) next
    for (b in e$Payload) {
      if (!identical(b$Type, "Trash")) next
      for (be in b$BlockElements) {
        if (identical(be$Type, "Question")) out <- c(out, be$QuestionID)
      }
    }
  }
  unique(out)
}

# One row per live rating item whose export tag matches `pattern`:
#   item         the export tag
#   question_id  the QID number in the survey file
#   k            the number of answer options
#   labels       the option labels in ChoiceOrder, cleaned, as a list column
#                (a column whose every cell holds a vector)
#   anchors      the same labels joined by " | ", for reading
#   stem         the question text, cleaned
# Deleted questions are left out, and the read stops if two live questions
# share a tag. `qsf` is the path of a .qsf file or the result of read_qsf().
# `pattern` is usually ITEM_FAMILIES$original$pattern or
# ITEM_FAMILIES$derivative$pattern.
read_item_scales <- function(qsf, pattern) {
  if (is.character(qsf)) qsf <- read_qsf(qsf)
  trash <- qsf_trash_questions(qsf)
  rows  <- list()
  for (e in qsf$SurveyElements) {
    if (!identical(e$Element, "SQ")) next
    p   <- e$Payload
    tag <- if (is.null(p$DataExportTag)) "" else as.character(p$DataExportTag)
    ch  <- p$Choices
    if (!grepl(pattern, tag, perl = TRUE)) next
    if (!is.list(ch) || is.null(names(ch))) next
    if (isTRUE(p$QuestionID %in% trash)) next
    if (tag %in% names(rows)) {
      stop(tag, ": more than one live question carries this export tag.")
    }
    order <- as.character(unlist(p$ChoiceOrder))
    if (length(order) == 0) order <- names(ch)
    order <- order[order %in% names(ch)]
    opts  <- qualtrics_clean_text(vapply(order, function(code) {
      d <- ch[[code]]$Display
      if (is.null(d)) "" else as.character(d)
    }, character(1), USE.NAMES = FALSE))
    rows[[tag]] <- tibble(
      item        = tag,
      question_id = as.character(p$QuestionID),
      k           = length(opts),
      labels      = list(opts),
      anchors     = paste(opts, collapse = " | "),
      stem        = qualtrics_clean_text(p$QuestionText)
    )
  }
  if (length(rows) == 0) {
    return(tibble(item = character(), question_id = character(),
                  k = integer(), labels = list(), anchors = character(),
                  stem = character()))
  }
  out <- bind_rows(rows)
  out[order(out$item, method = "radix"), , drop = FALSE]
}

# ---------------------------------------------------------------------------
# Scoring by position
# ---------------------------------------------------------------------------

# Score every item in `scales` from the Labels export. Each answer label is
# cleaned as the survey labels were and looked up in its item's labels; the
# score is its position, 1 to k. A blank answer is NA. An answer whose label
# is not among the item's current options is also NA, and it is counted in
# the returned log, because it is a recorded answer that cannot be placed on
# the scale. In Study 3, two 1FigureEff answers carry choice code 5, which
# the final survey does not offer, and the Labels export shows them as "5".
#
# Returns a list:
#   scores  one integer column per item, rows in the order of labels_df
#   log     one row per item and unplaceable label: item, label, n, reason
score_by_position <- function(labels_df, scales) {
  missing_items <- setdiff(scales$item, names(labels_df))
  if (length(missing_items) > 0) {
    stop("The Labels export has no column for: ",
         paste(missing_items, collapse = ", "))
  }
  scores <- vector("list", nrow(scales))
  names(scores) <- scales$item
  log <- vector("list", nrow(scales))
  for (i in seq_len(nrow(scales))) {
    item <- scales$item[i]
    lab  <- qualtrics_clean_text(labels_df[[item]])
    pos  <- match(lab, scales$labels[[i]])
    pos[lab == ""] <- NA_integer_
    scores[[item]] <- as.integer(pos)
    bad <- lab != "" & is.na(pos)
    if (any(bad)) {
      tab <- table(lab[bad])
      log[[i]] <- tibble(item = item, label = names(tab), n = as.integer(tab),
                         reason = "label is not among the item's choices")
    }
  }
  log <- bind_rows(log)
  if (nrow(log) == 0) {
    log <- tibble(item = character(), label = character(), n = integer(),
                  reason = character())
  }
  list(scores = as_tibble(scores), log = log)
}

# ---------------------------------------------------------------------------
# Item names and justification columns
# ---------------------------------------------------------------------------

# The rating items of one family present in an export's header, in byte
# order of their tags (the order study5_build.py uses).
rating_items <- function(header, family) {
  fam <- ITEM_FAMILIES[[family]]
  if (is.null(fam)) stop("Unknown item family: ", family)
  items <- header[grepl(fam$pattern, header, perl = TRUE)]
  sort(items, method = "radix")
}

# The justification column of each rating item, looked up once in the
# export's header. The lookup stops if an item has no such column or more
# than one. Returns a character vector named by item.
justification_columns <- function(items, header) {
  out <- vapply(items, function(item) {
    found <- paste0(item, JUSTIFICATION_SUFFIXES)
    found <- found[found %in% header]
    if (length(found) != 1) {
      stop(item, ": expected one justification column, found ",
           if (length(found) == 0) "none" else paste(found, collapse = ", "))
    }
    found
  }, character(1))
  names(out) <- items
  out
}

# Split item tags into their parts, with the dimension and modification codes
# spelled out in words. stimulus_id is the image number followed by the image
# kind (1Figure, 4NonFigure), one identifier per original image.
parse_item_names <- function(items, family) {
  fam <- ITEM_FAMILIES[[family]]
  if (is.null(fam)) stop("Unknown item family: ", family)
  if (!all(grepl(fam$pattern, items, perl = TRUE))) {
    stop("Some items do not belong to the ", family, " family: ",
         paste(items[!grepl(fam$pattern, items, perl = TRUE)], collapse = ", "))
  }
  parts <- regmatches(items, regexec(fam$pattern, items, perl = TRUE))
  m <- do.call(rbind, lapply(parts, function(p) p[-1]))
  colnames(m) <- fam$parts
  out <- bind_cols(tibble(item = items), as_tibble(m))
  out$dimension <- unname(fam$dimension_names[out$dimension])
  if ("modification" %in% fam$parts) {
    out$modification <- unname(fam$modification_names[out$modification])
  }
  out$stimulus_id <- paste0(out$image, out$stimulus_type)
  out
}

# ---------------------------------------------------------------------------
# One row per participant and item
# ---------------------------------------------------------------------------

# Turn the two exports into a long table, one row per participant and rating
# item, for the items of one family. `values` and `labels` are the two
# exports, already screened to the participants to keep and in the same
# order; `scales` comes from read_item_scales(). Each row carries:
#   id             the participant identifier (the column named by id_col)
#   item, image, stimulus_type, [modification], dimension, stimulus_id
#   rating         the scale position, 1 to k, or NA
#   k_points       the number of options on the item's scale
#   rating_label   the answer text from the Labels export
#   raw_choice_id  the choice code from the Values export, kept for checking
#   justification  the written justification, trimmed
# plus any columns named in carry_values (taken from the Values export) or
# carry_labels (taken from the Labels export), such as the condition or the
# demographics.
#
# A row is kept when the participant gave a rating or a justification for
# the item. An item the participant was never shown has neither and gives no
# row. A rating left blank beside a written justification keeps its row, with
# rating NA.
#
# Returns a list:
#   long      the table
#   unscored  the log of recorded answers that have no score: the rows of
#             score_by_position()'s log, and one row per item where a choice
#             code was recorded but the Labels export holds no label for it
reshape_ratings_long <- function(values, labels, scales, family,
                                 id_col = "ResponseId",
                                 carry_values = character(0),
                                 carry_labels = character(0)) {
  if (nrow(values) != nrow(labels) ||
      !identical(values[[id_col]], labels[[id_col]])) {
    stop("values and labels must hold the same records in the same order.")
  }
  if (anyDuplicated(values[[id_col]]) > 0) {
    stop("Some ", id_col, " appears more than once.")
  }
  items <- rating_items(names(values), family)
  no_key <- setdiff(items, scales$item)
  if (length(no_key) > 0) {
    stop("No scale in the survey file for: ", paste(no_key, collapse = ", "))
  }
  scales   <- scales[match(items, scales$item), , drop = FALSE]
  just_col <- justification_columns(items, names(labels))
  scored   <- score_by_position(labels, scales)
  parsed   <- parse_item_names(items, family)

  n <- nrow(values)
  # Each column is computed before the table is built, because inside
  # tibble() a column name such as `item` would hide the variable of the same
  # name.
  no_label <- list()
  long <- bind_rows(lapply(seq_along(items), function(j) {
    tag   <- items[j]
    score <- scored$scores[[tag]]
    label <- trim_answer(labels[[tag]])
    raw   <- trim_answer(values[[tag]])
    text  <- trim_answer(labels[[just_col[[tag]]]])
    if (any(raw != "" & label == "")) {
      no_label[[tag]] <<- tibble(
        item = tag, label = "", n = sum(raw != "" & label == ""),
        reason = "choice code recorded with no label in the Labels export")
    }
    tibble(
      .row          = seq_len(n),
      .item_order   = j,
      id            = values[[id_col]],
      item          = tag,
      rating        = score,
      k_points      = scales$k[j],
      rating_label  = label,
      raw_choice_id = raw,
      justification = text
    )
  }))
  long <- long[long$raw_choice_id != "" | long$justification != "", ,
               drop = FALSE]
  long <- long[order(long$.row, long$.item_order), , drop = FALSE]

  for (col in carry_values) long[[col]] <- values[[col]][long$.row]
  for (col in carry_labels) long[[col]] <- labels[[col]][long$.row]

  long <- left_join(long, parsed, by = "item")
  first <- c("id", "item", setdiff(names(parsed), "item"))
  long <- long[, c(first, setdiff(names(long), c(first, ".row", ".item_order")))]
  list(long = long, unscored = bind_rows(scored$log, bind_rows(no_label)))
}
