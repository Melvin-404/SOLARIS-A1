"""Interval overlap and tolerance matching algorithms for SOLARIS-A1 (Stage 6).

CRITICAL REQUIREMENT:
tolerance_seconds is a strictly required argument with NO default value in code.
Calling matching functions without an explicit tolerance raises an error.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union


def interval_overlap_seconds(
    start1: float,
    end1: float,
    start2: float,
    end2: float,
    tolerance_seconds: float,  # REQUIRED: NO DEFAULT VALUE
) -> float:
    """Compute the overlap duration in seconds between two intervals with explicit tolerance.
    
    Parameters
    ----------
    start1 : float
        Start timestamp of first interval (e.g. observation window).
    end1 : float
        End timestamp of first interval.
    start2 : float
        Start timestamp of second interval (e.g. flare event).
    end2 : float
        End timestamp of second interval.
    tolerance_seconds : float
        Matching tolerance window in seconds (Decision D-02). MUST BE EXPLICIT.
        
    Returns
    -------
    float
        Overlap duration in seconds (>= 0.0).
        
    Raises
    -------
    ValueError
        If timestamps are inverted or tolerance_seconds is negative.
    """
    if tolerance_seconds is None or not isinstance(tolerance_seconds, (int, float)):
        raise ValueError("tolerance_seconds is a required numerical argument with no default.")

    if tolerance_seconds < 0.0:
        raise ValueError(f"tolerance_seconds cannot be negative, got {tolerance_seconds}")

    if end1 < start1:
        raise ValueError(f"First interval inverted: end1 ({end1}) < start1 ({start1})")
    if end2 < start2:
        raise ValueError(f"Second interval inverted: end2 ({end2}) < start2 ({start2})")

    # Expand interval 1 by tolerance
    adj_s1 = float(start1 - tolerance_seconds)
    adj_e1 = float(end1 + tolerance_seconds)

    overlap_s = min(adj_e1, float(end2)) - max(adj_s1, float(start2))
    return max(0.0, float(overlap_s))


def is_event_in_window(
    window_start: float,
    window_end: float,
    event_start: float,
    event_end: float,
    tolerance_seconds: float,  # REQUIRED: NO DEFAULT VALUE
    min_overlap_fraction: float = 0.5,
) -> bool:
    """Evaluate whether an event overlaps an observation window meeting overlap criteria.
    
    Parameters
    ----------
    window_start : float
        Start of sliding window.
    window_end : float
        End of sliding window.
    event_start : float
        Start of event.
    event_end : float
        End of event.
    tolerance_seconds : float
        Required tolerance parameter.
    min_overlap_fraction : float
        Fraction of window duration required to overlap for positive assignment.
        
    Returns
    -------
    bool
        True if overlap criteria are satisfied.
    """
    if tolerance_seconds is None or not isinstance(tolerance_seconds, (int, float)):
        raise ValueError("tolerance_seconds is a required numerical argument with no default.")

    overlap_s = interval_overlap_seconds(
        window_start, window_end, event_start, event_end, tolerance_seconds=tolerance_seconds
    )

    win_duration = window_end - window_start
    if win_duration <= 0.0:
        return False

    return bool(overlap_s >= (win_duration * min_overlap_fraction))
