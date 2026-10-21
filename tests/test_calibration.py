"""Unit tests for probability calibration assessment (Stage 11).

Tests:
1. Exact Brier score calculation on known inputs.
2. Expected Calibration Error (ECE) on perfectly calibrated synthetic probabilities.
3. Reliability binning statistics.
"""

import numpy as np
import pytest
from solar_flare.evaluation.calibration import compute_calibration_assessment


def test_brier_score_exact_on_known_input():
    """Verify Brier score on hand-calculated synthetic data."""
    # y_true = [1, 0, 1, 0]
    # y_prob = [0.8, 0.2, 0.6, 0.4]
    # Squared errors:
    # (0.8 - 1)^2 = 0.04
    # (0.2 - 0)^2 = 0.04
    # (0.6 - 1)^2 = 0.16
    # (0.4 - 0)^2 = 0.16
    # Mean: (0.04 + 0.04 + 0.16 + 0.16) / 4 = 0.40 / 4 = 0.10
    y_true = [1, 0, 1, 0]
    y_prob = [0.8, 0.2, 0.6, 0.4]

    rep = compute_calibration_assessment(y_true, y_prob, n_bins=5)
    assert pytest.approx(rep.brier_score, 1e-6) == 0.10


def test_perfectly_calibrated_data_gives_ece_near_zero():
    """Verify that synthetic data sampled from true Bernoulli probabilities achieves near-zero ECE."""
    np.random.seed(42)
    # 20,000 samples with predicted probabilities uniformly distributed in [0, 1]
    # Ground truth drawn with P(y=1) = p
    probs = np.random.uniform(0.0, 1.0, size=20000)
    y_true = (np.random.uniform(0.0, 1.0, size=20000) < probs).astype(int)

    rep = compute_calibration_assessment(y_true, probs, n_bins=10)

    # In perfectly calibrated data, empirical ECE approaches 0 as sample size increases
    assert rep.expected_calibration_error < 0.02
    assert rep.n_bins == 10
    assert len(rep.bins) == 10
    assert sum(b.n_samples for b in rep.bins) == 20000
