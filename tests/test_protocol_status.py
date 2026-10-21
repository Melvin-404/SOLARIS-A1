"""Unit tests for training protocol status and Gate G7 freezing (Stage 10).

Validates:
- Protocol in DRAFT status raises ProtocolNotFrozenError.
- Protocol marked FROZEN or PILOT but missing approval name/date raises error.
- Fully approved FROZEN or PILOT protocol passes guard.
"""

from __future__ import annotations

import pytest

from solar_flare.modelling.guards import assert_protocol_frozen, ProtocolNotFrozenError


def test_draft_protocol_refuses():
    """Verify that a DRAFT protocol raises ProtocolNotFrozenError."""
    protocol = {
        "protocol_id": "PROTO_001",
        "status": "DRAFT",
        "approved_by": None,
        "approved_date": None,
    }
    with pytest.raises(ProtocolNotFrozenError, match="status is 'DRAFT'"):
        assert_protocol_frozen(protocol)


def test_frozen_protocol_missing_approver_refuses():
    """Verify that a FROZEN protocol missing approver or date raises error."""
    protocol = {
        "protocol_id": "PROTO_001",
        "status": "FROZEN",
        "approved_by": None,
        "approved_date": "2026-10-21",
    }
    with pytest.raises(ProtocolNotFrozenError, match="missing approved_by or approved_date"):
        assert_protocol_frozen(protocol)


def test_frozen_protocol_valid_passes():
    """Verify that a properly signed FROZEN protocol passes cleanly."""
    protocol = {
        "protocol_id": "PROTO_001",
        "status": "FROZEN",
        "approved_by": "Researcher Name",
        "approved_date": "2026-10-21",
    }
    assert assert_protocol_frozen(protocol) is True


def test_pilot_protocol_valid_passes():
    """Verify that a properly signed PILOT protocol passes cleanly."""
    protocol = {
        "protocol_id": "PROTO_PILOT_001",
        "status": "PILOT",
        "approved_by": "Researcher Name",
        "approved_date": "2026-10-21",
    }
    assert assert_protocol_frozen(protocol) is True
