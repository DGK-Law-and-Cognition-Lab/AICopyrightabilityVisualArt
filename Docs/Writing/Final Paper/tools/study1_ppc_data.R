# study1_ppc_data.R: the data behind Supplementary Figure 5, the posterior predictive check of
# Study 1's two Bayesian models.
#
# The pipeline's Study1_04_Robustness.Rmd draws this check with brms::pp_check(fit, ndraws = 100):
# the density of the observed ratings against the densities of 100 data sets simulated from the
# fitted model. This script repeats that comparison from the saved fits, without refitting, and
# writes the curves to a table that tools/make_figures.py draws in the paper's style.
#
# Run from the Final Paper folder:
#   DEVELOPER_DIR=/Library/Developer/CommandLineTools Rscript tools/study1_ppc_data.R
# PIPELINE_DIR overrides the pipeline folder, as in the paper's other tools.
#
# Inputs (read only): Study 1/models/study1_brms_primary_creativity.rds and
# study1_brms_primary_effort.rds in the pipeline (Gaussian mixed models fitted with brms).
# Output: figures/figS_study1_ppc_curves.csv, one row per curve and grid point, with no
# participant identifiers, and figures/figS_study1_ppc_sources.csv, the checksum of each input.

suppressPackageStartupMessages({
  library(brms)
  library(digest)
})

args_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
here <- dirname(normalizePath(args_file))
paper <- normalizePath(file.path(here, ".."))
pipeline <- Sys.getenv("PIPELINE_DIR",
                       file.path(paper, "..", "..", "..", "Analysis", "R Analysis Pipeline"))
pipeline <- normalizePath(pipeline, mustWork = TRUE)

SEED <- 20260421   # the pipeline's Study 1 seed; fixes which 100 posterior draws are used
NDRAWS <- 100      # as in the pipeline's pp_check call
NGRID <- 512       # points at which each density is evaluated

curves <- list()
sources <- list()
for (dim in c("creativity", "effort")) {
  rel <- file.path("Study 1", "models", sprintf("study1_brms_primary_%s.rds", dim))
  path <- file.path(pipeline, rel)
  if (!file.exists(path)) stop("missing fit: ", rel)
  fit <- readRDS(path)
  y <- fit$data$rating
  if (is.null(y)) stop(rel, ": the fit's data hold no column 'rating'")
  set.seed(SEED)
  yrep <- posterior_predict(fit, ndraws = NDRAWS)
  if (!all(dim(yrep) == c(NDRAWS, length(y)))) stop(rel, ": unexpected posterior_predict shape")
  # One common grid over every value, as ggplot2's stat_density (used by pp_check) does when it
  # does not trim; Gaussian kernel with the default bandwidth rule (nrd0), as there.
  lo <- min(y, yrep)
  hi <- max(y, yrep)
  dens_at <- function(v) density(v, bw = "nrd0", kernel = "gaussian", from = lo, to = hi,
                                 n = NGRID)
  d <- dens_at(y)
  curves[[length(curves) + 1]] <- data.frame(rating = dim, curve = "observed", x = d$x, density = d$y)
  for (i in seq_len(NDRAWS)) {
    d <- dens_at(yrep[i, ])
    curves[[length(curves) + 1]] <- data.frame(rating = dim, curve = sprintf("draw_%03d", i),
                                               x = d$x, density = d$y)
  }
  sources[[length(sources) + 1]] <- data.frame(
    rating = dim, file = rel, sha256 = digest(path, algo = "sha256", file = TRUE),
    n_observed = length(y), ndraws = NDRAWS, seed = SEED,
    family = family(fit)$family)
}

out <- do.call(rbind, curves)
out$x <- formatC(out$x, digits = 6, format = "f")
out$density <- formatC(out$density, digits = 6, format = "f")
write.csv(out, file.path(paper, "figures", "figS_study1_ppc_curves.csv"), row.names = FALSE,
          quote = FALSE)
write.csv(do.call(rbind, sources), file.path(paper, "figures", "figS_study1_ppc_sources.csv"),
          row.names = FALSE)
cat("Wrote figures/figS_study1_ppc_curves.csv and figures/figS_study1_ppc_sources.csv\n")
