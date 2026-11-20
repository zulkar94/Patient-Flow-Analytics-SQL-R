# Run the 30-day readmission survival analysis.
#
# Usage (from the repository root, after building the database):
#   Rscript r/analysis.R data/patient_flow.db

suppressPackageStartupMessages({
  library(DBI)
  library(RSQLite)
  library(survival)
  library(ggplot2)
})

args <- commandArgs(trailingOnly = TRUE)
db_path <- if (length(args) >= 1) args[1] else "data/patient_flow.db"
out_dir <- "outputs"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

source("r/R/analysis_functions.R")

con <- dbConnect(SQLite(), db_path)
on.exit(dbDisconnect(con), add = TRUE)

frame <- read_survival_frame(con, "sql/analysis/05_readmission_survival_input.sql")

km_fit <- fit_kaplan_meier(frame)
ggsave(
  file.path(out_dir, "readmission_kaplan_meier.png"),
  plot_kaplan_meier(km_to_frame(km_fit)),
  width = 8, height = 5, dpi = 150
)

cox_fit <- fit_cox(frame)
writeLines(
  capture.output(summary(cox_fit)),
  file.path(out_dir, "readmission_cox_summary.txt")
)

cat(sprintf(
  "Discharges analysed: %d, readmitted within 30 days: %d\n",
  nrow(frame), sum(frame$event)
))
