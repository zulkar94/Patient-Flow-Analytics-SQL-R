# Tests for the survival helpers. Run from the repository root:
#   Rscript -e 'testthat::test_dir("r/tests/testthat")'

source(testthat::test_path("../../R/analysis_functions.R"))

make_frame <- function(n = 300, seed = 1) {
  set.seed(seed)
  data.frame(
    time_days = pmin(30, pmax(1, round(rexp(n, rate = 1 / 15)))),
    event = rbinom(n, 1, 0.3),
    condition = sample(c("pneumonia", "heart_failure", "appendicitis"), n, replace = TRUE),
    age_band = sample(c("0-39", "40-59", "60-74", "75+"), n, replace = TRUE),
    sex = sample(c("F", "M"), n, replace = TRUE),
    admission_type = sample(c("elective", "emergency"), n, replace = TRUE),
    stringsAsFactors = FALSE
  )
}

test_that("Cox model returns one coefficient per non-reference level", {
  frame <- make_frame()
  frame$condition <- factor(frame$condition)
  frame$age_band <- factor(frame$age_band)
  frame$sex <- factor(frame$sex)
  frame$admission_type <- factor(frame$admission_type)
  fit <- fit_cox(frame)
  expect_equal(length(coef(fit)), 2 + 3 + 1 + 1)
  expect_true(all(is.finite(coef(fit))))
})

test_that("Kaplan-Meier output has one strata per condition", {
  frame <- make_frame()
  km <- km_to_frame(fit_kaplan_meier(frame))
  expect_setequal(unique(km$condition), c("appendicitis", "heart_failure", "pneumonia"))
  expect_true(all(km$surv >= 0 & km$surv <= 1))
})

test_that("plot_kaplan_meier builds a ggplot object", {
  frame <- make_frame()
  p <- plot_kaplan_meier(km_to_frame(fit_kaplan_meier(frame)))
  expect_s3_class(p, "ggplot")
})
