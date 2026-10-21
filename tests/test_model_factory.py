"""Unit tests for model factory (Stage 10).

Validates:
- Built estimators are unfitted (calling check_is_fitted raises NotFittedError).
- Unknown model names raise ValueError.
- Missing dependencies yield an UnavailableModel placeholder rather than crashing.
"""

from __future__ import annotations

import pytest
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from solar_flare.modelling.model_factory import build_model, UnavailableModel


def test_built_models_are_unfitted():
    """Verify that build_model returns estimators in strictly unfitted states."""
    lr = build_model("logistic_regression")
    with pytest.raises(NotFittedError):
        check_is_fitted(lr)

    rf = build_model("random_forest")
    with pytest.raises(NotFittedError):
        check_is_fitted(rf)


def test_unknown_model_raises_value_error():
    """Verify that an unsupported model name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown model name"):
        build_model("unsupported_deep_net")


def test_unavailable_model_behavior():
    """Verify that an UnavailableModel instance handles attempts to fit gracefully with error."""
    unavail = UnavailableModel(name="test_model", reason="Library absent")
    assert unavail.is_available is False
    with pytest.raises(RuntimeError, match="Cannot fit 'test_model'"):
        unavail.fit()
