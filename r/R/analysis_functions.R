# Survival analysis helpers for 30-day readmission.
#
# Each function takes a data frame or DBI connection, so it can be tested
# without the full database.

read_survival_frame <- function(con, sql_path) {
  query <- paste(readLines(sql_path, warn = FALSE), collapse = "\n")
  prepare_survival_frame(DBI::dbGetQuery(con, query))
}

# Survival models need positive times. Two cases give time 0:
#   - a same-day readmission (event = 1). This is a real readmission, so it is
#     kept and moved to half a day, a common convention for day-level data.
#   - a discharge on the last eligible day (event = 0). It has no follow-up at
#     all, so it carries no information and is dropped.
prepare_survival_frame <- function(frame) {
  same_day_event <- frame$time_days <= 0 & frame$event == 1
  frame$time_days[same_day_event] <- 0.5
  frame <- frame[frame$time_days > 0, , drop = FALSE]
  frame$condition <- factor(frame$condition)
  frame$age_band <- factor(frame$age_band, levels = c("0-39", "40-59", "60-74", "75+"))
  frame$sex <- factor(frame$sex)
  frame$admission_type <- factor(frame$admission_type, levels = c("elective", "emergency"))
  frame
}

fit_kaplan_meier <- function(frame) {
  survival::survfit(survival::Surv(time_days, event) ~ condition, data = frame)
}

fit_cox <- function(frame) {
  survival::coxph(
    survival::Surv(time_days, event) ~ condition + age_band + sex + admission_type,
    data = frame
  )
}

km_to_frame <- function(fit) {
  s <- summary(fit)
  data.frame(
    time = s$time,
    surv = s$surv,
    condition = sub("^condition=", "", as.character(s$strata))
  )
}

plot_kaplan_meier <- function(km_df) {
  ggplot2::ggplot(km_df, ggplot2::aes(x = time, y = surv, colour = condition)) +
    ggplot2::geom_step() +
    ggplot2::labs(
      title = "Probability of no readmission within 30 days",
      subtitle = "Synthetic data, Kaplan-Meier estimate by condition",
      x = "Days since discharge",
      y = "Probability not readmitted",
      colour = "Condition"
    ) +
    ggplot2::theme_minimal()
}
