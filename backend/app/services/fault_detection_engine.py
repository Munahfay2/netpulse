"""
fault_detection_engine.py

Deterministic, explainable rules — no black-box ML in the MVP (see spec
section 29 and the AI roadmap in section 49). Each rule maps observed
telemetry to a *detected symptom*, never to a confirmed physical fault.
"""
from dataclasses import dataclass
from typing import Optional

from .. import models


@dataclass
class DetectionResult:
    is_faulty: bool
    symptom: Optional[str] = None  # e.g. "WAN/access connectivity issue"
    rule: Optional[str] = None


def evaluate_device(device: models.Device) -> DetectionResult:
    """Apply Rules 1-4 to a single device's latest telemetry."""

    # Rule 1: device unreachable entirely.
    if device.router_status == "offline":
        return DetectionResult(True, "Device unreachable", "rule_1_device_unreachable")

    # Rule 2: router reachable but WAN is down.
    if device.router_status == "online" and device.wan_status == "down":
        return DetectionResult(True, "WAN/access connectivity issue", "rule_2_wan_down")

    # Rule 3: severe packet loss + no internet reachability.
    if (not device.internet_reachable) and device.packet_loss_percent > 80:
        return DetectionResult(True, "Severe connectivity degradation", "rule_3_severe_loss")

    # Rule 4: latency + moderate packet loss => congestion/degradation.
    if device.latency_ms > 200 and device.packet_loss_percent > 10:
        return DetectionResult(True, "Network degradation/congestion", "rule_4_congestion")

    return DetectionResult(False)


def compute_device_health(device: models.Device) -> str:
    result = evaluate_device(device)
    if not result.is_faulty:
        return "healthy"
    if result.rule in ("rule_1_device_unreachable", "rule_2_wan_down", "rule_3_severe_loss"):
        return "offline"
    return "degraded"
