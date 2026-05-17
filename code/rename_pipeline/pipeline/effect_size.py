# Generated using Claude opus-4.6

import math
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from scipy import stats

import yaml

logger = logging.getLogger("pipeline")

config = {}
with open("pipeline/config.yml", "r") as f:
    config = yaml.safe_load(f)

_NON_NORMALITY_CORRECTION = config["NON_NORMALITY_CORRECTION"]


@dataclass
class EffectSizeResult:
    """Holds all effect size statistics for one metric."""

    metric_name: str
    wilcoxon_statistic: float
    p_value: float
    z_statistic: float
    r: float
    r_adjusted: float
    r_ci_lower: float
    r_ci_upper: float
    r_interpretation: str
    n_pairs: int
    mean_diff: float
    median_diff: float
    std_diff: float
    recommended_n: int


def _interpret_r(r: float) -> str:
    """Classify |r| using Cohen's r thresholds."""
    abs_r = abs(r)
    if abs_r >= 0.50:
        return "large"
    elif abs_r >= 0.30:
        return "medium"
    elif abs_r >= 0.10:
        return "small"
    else:
        return "negligible"


def _r_to_cohens_d(r: float) -> float:
    r = min(abs(r), 0.9999)
    return 2 * r / math.sqrt(1 - r**2)


def _adjust_r_olkin_pratt(r: float, n: int) -> float:
    """
    Bias-correct the observed r for small-sample inflation.

    Small samples systematically overestimate effect sizes. This correction
    shrinks r toward zero proportionally to how much variance is unexplained
    and how small the sample is.

    Olkin, I., & Pratt, J. W. (1958). Unbiased estimation of certain
    correlation coefficients. Annals of Mathematical Statistics, 29(1),
    201-211.

    Formula: r_adj = r * (1 - (1 - r²) / (2 * (n - 1)))
    """
    if n <= 2:
        return r
    return r * (1 - (1 - r**2) / (2 * (n - 1)))


def _r_confidence_interval(
    r: float, n: int, alpha: float = 0.05
) -> Tuple[float, float]:
    """
    95% CI for r using the Fisher Z-transformation.

    Fisher, R. A. (1915). Frequency distribution of the values of the
    correlation coefficient in samples from an indefinitely large population.
    Biometrika, 10(4), 507-521.

    Returns (lower, upper) preserving the sign of r.
    """
    if n <= 3:
        return (-1.0, 1.0)

    r_clamped = max(-0.9999, min(0.9999, r))
    z = math.atanh(r_clamped)
    se = 1.0 / math.sqrt(n - 3)
    z_crit = stats.norm.ppf(1 - alpha / 2)

    lower = math.tanh(z - z_crit * se)
    upper = math.tanh(z + z_crit * se)
    return lower, upper


def required_sample_size(
    r: float,
    alpha: float = config["ALPHA"],
    power: float = config["BETA"],
    non_normality_correction: float = _NON_NORMALITY_CORRECTION,
) -> int:
    if abs(r) < 1e-6:
        return 9999

    d_equiv = _r_to_cohens_d(r)

    z_alpha = stats.norm.ppf(1 - alpha / 2)  # 1.96 for alpha=0.05
    z_beta = stats.norm.ppf(power)  # 0.842 for power=0.80

    n_base = ((z_alpha + z_beta) / d_equiv) ** 2
    n_corrected = n_base * non_normality_correction

    return math.ceil(n_corrected)


def compute_effect_size(
    scores_original: List[float],
    scores_renamed: List[float],
    metric_name: str,
) -> Optional[EffectSizeResult]:
    if len(scores_original) != len(scores_renamed):
        logger.error(
            f"effect_size [{metric_name}]: length mismatch "
            f"({len(scores_original)} vs {len(scores_renamed)})"
        )
        return None

    arr_orig = np.array(scores_original, dtype=float)
    arr_ren = np.array(scores_renamed, dtype=float)
    diffs = arr_ren - arr_orig

    n = len(diffs)

    if n < 5:
        logger.warning(
            f"effect_size [{metric_name}]: only {n} pairs — "
            "too few for a reliable Wilcoxon test (need at least 5)."
        )
        return None

    result = stats.wilcoxon(diffs, alternative="two-sided", method="approx")
    W = float(result.statistic)
    pv = float(result.pvalue)

    mu_W = n * (n + 1) / 4.0
    sigma_W = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    z = (W - mu_W) / sigma_W if sigma_W > 0 else 0.0

    r = z / math.sqrt(n)
    r_adj = _adjust_r_olkin_pratt(r, n)
    r_ci_lower, r_ci_upper = _r_confidence_interval(r, n)
    r_conservative = min(abs(r_ci_lower), abs(r_ci_upper))

    rec_n = required_sample_size(r_conservative)

    return EffectSizeResult(
        metric_name=metric_name,
        wilcoxon_statistic=W,
        p_value=pv,
        z_statistic=z,
        r=r,
        r_adjusted=r_adj,
        r_ci_lower=r_ci_lower,
        r_ci_upper=r_ci_upper,
        r_interpretation=_interpret_r(r),
        n_pairs=n,
        mean_diff=float(np.mean(diffs)),
        median_diff=float(np.median(diffs)),
        std_diff=float(np.std(diffs, ddof=1)),
        recommended_n=rec_n,
    )


def effect_size_report(results: List[EffectSizeResult]) -> dict:
    report = {}

    for res in results:
        if res is None:
            continue

        logger.info(
            f"\n{'=' * 55}\n"
            f"  Effect size — {res.metric_name}\n"
            f"{'=' * 55}\n"
            f"  N pairs            : {res.n_pairs}\n"
            f"  Mean diff          : {res.mean_diff:+.4f}  "
            f"(renamed − original)\n"
            f"  Median diff        : {res.median_diff:+.4f}\n"
            f"  Std of diffs       : {res.std_diff:.4f}\n"
            f"  Wilcoxon W         : {res.wilcoxon_statistic:.2f}\n"
            f"  Z statistic        : {res.z_statistic:.4f}\n"
            f"  p-value            : {res.p_value:.4f}"
            f"{'  ***' if res.p_value < 0.001 else '  **' if res.p_value < 0.01 else '  *' if res.p_value < 0.05 else ''}\n"
            f"  Effect size r      : {res.r:.4f} "
            f"({res.r_interpretation})\n"
            f"  r adjusted         : {res.r_adjusted:.4f}  (Olkin & Pratt, 1958)\n"
            f"  95% CI for r       : [{res.r_ci_lower:.4f}, {res.r_ci_upper:.4f}]\n"
            f"  Recommended n      : {res.recommended_n} test pairs\n"
            f"  (conservative CI bound, power={config['BETA']}, alpha={config['ALPHA']})\n"
        )

        report[res.metric_name] = {
            "n_pairs": res.n_pairs,
            "mean_diff": round(res.mean_diff, 4),
            "median_diff": round(res.median_diff, 4),
            "std_diff": round(res.std_diff, 4),
            "wilcoxon_statistic": round(res.wilcoxon_statistic, 4),
            "z_statistic": round(res.z_statistic, 4),
            "p_value": round(res.p_value, 4),
            "effect_size_r": round(res.r, 4),
            "effect_size_r_adj": round(res.r_adjusted, 4),
            "r_ci_lower": round(res.r_ci_lower, 4),
            "r_ci_upper": round(res.r_ci_upper, 4),
            "effect_size_label": res.r_interpretation,
            "recommended_n": res.recommended_n,
        }

    return report
