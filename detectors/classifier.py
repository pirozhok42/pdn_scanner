from __future__ import annotations

from detectors.scanner import DetectionResult


def classify_security_level(detection: DetectionResult) -> str:
    common = detection.categories.get("common", 0)
    government_id = detection.categories.get("government_id", 0)
    payment = detection.categories.get("payment", 0)
    biometric = detection.categories.get("biometric", 0)
    special = detection.categories.get("special", 0)

    if special > 0 or biometric > 0:
        return "УЗ-1"

    if payment > 0 or government_id >= 10:
        return "УЗ-2"

    if government_id > 0 or common >= 20:
        return "УЗ-3"

    if common > 0:
        return "УЗ-4"

    return "НЕТ_ПДН"