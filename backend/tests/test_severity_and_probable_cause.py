from app.models import Severity
from app.services.incident_engine import (_build_reasons, _confidence_for,
                                           severity_for_count)


def test_severity_thresholds_are_configurable_and_correct():
    assert severity_for_count(1) == Severity.low
    assert severity_for_count(2) == Severity.low
    assert severity_for_count(3) == Severity.medium
    assert severity_for_count(9) == Severity.medium
    assert severity_for_count(10) == Severity.high
    assert severity_for_count(19) == Severity.high
    assert severity_for_count(20) == Severity.critical
    assert severity_for_count(38) == Severity.critical


def test_confidence_scales_with_corroborating_customers():
    assert _confidence_for(1) == "Low"
    assert _confidence_for(5) == "Medium"
    assert _confidence_for(15) == "High"


def test_probable_cause_reasons_never_overclaim():
    reasons = _build_reasons(38, "OLT-003", "WAN/access connectivity issue")
    joined = " ".join(reasons)
    assert "38 customer(s) affected" in reasons
    assert "customers share OLT-003" in reasons
    # The reasoning must describe symptoms, never assert a confirmed
    # physical fault (e.g. "the fibre is cut").
    assert "cut" not in joined.lower()
    assert "confirmed" not in joined.lower()
