from app.models import Device
from app.services.fault_detection_engine import compute_device_health, evaluate_device


def _device(**overrides) -> Device:
    defaults = dict(
        id="CPE-TEST", router_status="online", wan_status="up", lan_status="normal",
        internet_reachable=True, latency_ms=25.0, packet_loss_percent=0.5,
    )
    defaults.update(overrides)
    return Device(**defaults)


def test_healthy_device_is_not_faulty():
    result = evaluate_device(_device())
    assert result.is_faulty is False
    assert compute_device_health(_device()) == "healthy"


def test_rule1_device_unreachable():
    result = evaluate_device(_device(router_status="offline"))
    assert result.is_faulty is True
    assert result.symptom == "Device unreachable"
    assert result.rule == "rule_1_device_unreachable"
    assert compute_device_health(_device(router_status="offline")) == "offline"


def test_rule2_wan_down():
    result = evaluate_device(_device(router_status="online", wan_status="down"))
    assert result.is_faulty is True
    assert result.symptom == "WAN/access connectivity issue"
    assert result.rule == "rule_2_wan_down"


def test_rule3_severe_packet_loss():
    result = evaluate_device(_device(internet_reachable=False, packet_loss_percent=95))
    assert result.is_faulty is True
    assert result.symptom == "Severe connectivity degradation"


def test_rule4_latency_and_loss_congestion():
    result = evaluate_device(_device(latency_ms=250, packet_loss_percent=15))
    assert result.is_faulty is True
    assert result.symptom == "Network degradation/congestion"
    assert compute_device_health(_device(latency_ms=250, packet_loss_percent=15)) == "degraded"


def test_high_latency_alone_is_not_enough():
    """Rule 4 requires BOTH latency and packet loss above threshold — high
    latency with clean packet loss should not be flagged as faulty."""
    result = evaluate_device(_device(latency_ms=250, packet_loss_percent=1))
    assert result.is_faulty is False
