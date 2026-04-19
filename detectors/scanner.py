from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from detectors.patterns import (
    PATTERNS,
    SPECIAL_KEYWORDS,
    BIOMETRIC_KEYWORDS,
    COMMON_PD_KEYWORDS,
    FIO_RU_PATTERN,
    FIO_EN_PATTERN,
)
from detectors.validators import (
    luhn_check,
    snils_check,
    inn_fl_check,
    inn_ul_check,
    bik_check,
    account_check,
    mask_value,
)


@dataclass(slots=True)
class DetectionItem:
    category: str
    subtype: str
    count: int
    samples_masked: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DetectionResult:
    categories: dict[str, int] = field(default_factory=dict)
    items: list[DetectionItem] = field(default_factory=list)

    def add(self, category: str, subtype: str, values: list[str]) -> None:
        if not values:
            return

        self.categories[category] = self.categories.get(category, 0) + len(values)
        masked = [mask_value(v) for v in values[:5]]
        self.items.append(
            DetectionItem(
                category=category,
                subtype=subtype,
                count=len(values),
                samples_masked=masked,
            )
        )


def _find_keywords(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    found = [kw for kw in keywords if kw.lower() in lowered]
    return found


def _has_context(text: str, keywords: list[str]) -> bool:
    return bool(_find_keywords(text, keywords))


def _has_field_context(text: str, metadata: dict[str, Any] | None, keywords: list[str]) -> bool:
    if _has_context(text, keywords):
        return True
    if not metadata:
        return False

    for key in ("columns", "json_keys", "fields", "headers"):
        values = metadata.get(key)
        if not values:
            continue
        for value in values:
            if any(kw.lower() in str(value).lower() for kw in keywords):
                return True
    return False


def _is_structured_source(kind: Any) -> bool:
    try:
        kind_value = kind.value
    except AttributeError:
        kind_value = str(kind)
    return kind_value in {"csv", "json", "parquet"}


def detect_pdn(text: str, kind: Any | None = None, metadata: dict[str, Any] | None = None) -> DetectionResult:
    result = DetectionResult()
    if not text.strip():
        return result

    emails = PATTERNS["email"].findall(text)
    phones = [m.group(0) for m in PATTERNS["phone"].finditer(text)]
    birth_dates = PATTERNS["birth_date"].findall(text)
    passports = [m.group(0) for m in PATTERNS["passport_rf"].finditer(text)]

    snils_raw = [m.group(0) for m in PATTERNS["snils"].finditer(text)]
    snils_valid = [x for x in snils_raw if snils_check(x)]

    inn_raw = [m.group(0) for m in PATTERNS["inn"].finditer(text)]
    inn_valid = [x for x in inn_raw if inn_fl_check(x) or inn_ul_check(x)]

    cards_raw = [m.group(0) for m in PATTERNS["card"].finditer(text)]
    cards_valid = [x for x in cards_raw if luhn_check(x)]

    biks_raw = [m.group(0) for m in PATTERNS["bik"].finditer(text)]
    biks_valid = [x for x in biks_raw if bik_check(x)]

    accounts_raw = [m.group(0) for m in PATTERNS["account"].finditer(text)]
    accounts_valid = [x for x in accounts_raw if account_check(x)]

    cvv = PATTERNS["cvv"].findall(text)
    mrz = [m.group(0) for m in PATTERNS["mrz"].finditer(text)]

    passport_context = _has_field_context(text, metadata, ["паспорт", "passport"])
    snils_context = _has_field_context(text, metadata, ["снилс", "snils"])
    inn_context = _has_field_context(text, metadata, ["инн", "inn"])
    card_context = _has_field_context(text, metadata, ["карта", "card", "номер карты", "card number", "visa", "mastercard", "maestro"])
    account_context = _has_field_context(text, metadata, ["счет", "account", "bank account", "р/с", "расчетный счет"])
    bik_context = _has_field_context(text, metadata, ["бик", "bik", "bank id", "bank identification"])

    fio_ru = FIO_RU_PATTERN.findall(text)
    fio_en = FIO_EN_PATTERN.findall(text)

    address_context = _find_keywords(text, COMMON_PD_KEYWORDS["address"])
    birth_place_context = _find_keywords(text, COMMON_PD_KEYWORDS["birth_place"])
    fio_context = _find_keywords(text, COMMON_PD_KEYWORDS["fio_context"])

    biometrics = _find_keywords(text, BIOMETRIC_KEYWORDS)

    health = _find_keywords(text, SPECIAL_KEYWORDS["health"])
    religion = _find_keywords(text, SPECIAL_KEYWORDS["religion"])
    politics = _find_keywords(text, SPECIAL_KEYWORDS["politics"])
    race_nationality = _find_keywords(text, SPECIAL_KEYWORDS["race_nationality"])

    result.add("common", "email", emails)
    result.add("common", "phone", phones)
    result.add("common", "birth_date", birth_dates)

    fio_candidates = fio_ru[:100] + fio_en[:100]
    if fio_context or len(fio_candidates) >= 4:
        result.add("common", "fio", fio_candidates)

    if address_context:
        result.add("common", "address_context", address_context)

    if birth_place_context:
        result.add("common", "birth_place_context", birth_place_context)

    structured = _is_structured_source(kind)

    if passports and (passport_context or (not structured and len(passports) >= 2) or len(passports) >= 4):
        result.add("government_id", "passport_rf", passports)
    if snils_valid and (snils_context or (not structured and len(snils_valid) >= 2) or len(snils_valid) >= 4):
        result.add("government_id", "snils", snils_valid)
    if inn_valid and (inn_context or (not structured and len(inn_valid) >= 2) or len(inn_valid) >= 4):
        result.add("government_id", "inn", inn_valid)
    result.add("government_id", "mrz", mrz)

    if cards_valid and (card_context or (not structured and len(cards_valid) >= 2) or len(cards_valid) >= 4):
        result.add("payment", "bank_card", cards_valid)
    if biks_valid and (bik_context or (not structured and len(biks_valid) >= 2) or len(biks_valid) >= 4):
        result.add("payment", "bik", biks_valid)
    if accounts_valid and (account_context or (not structured and len(accounts_valid) >= 2) or len(accounts_valid) >= 4):
        result.add("payment", "account", accounts_valid)
    result.add("payment", "cvv", cvv)
    result.add("biometric", "biometric_keywords", biometrics)

    result.add("special", "health", health)
    result.add("special", "religion", religion)
    result.add("special", "politics", politics)
    result.add("special", "race_nationality", race_nationality)

    return result

def has_personal_data(detection: DetectionResult) -> bool:
    strong_subtypes = {
        "email",
        "phone",
        "passport_rf",
        "snils",
        "inn",
        "mrz",
        "bank_card",
        "cvv",
    }
    identity_subtypes = {
        "passport_rf",
        "snils",
        "inn",
        "mrz",
        "bank_card",
        "cvv",
    }

    strong_hits = 0
    identity_hits = 0
    soft_hits = 0
    email_phone_hits = 0

    for item in detection.items:
        if item.subtype in strong_subtypes and item.count > 0:
            strong_hits += item.count
        if item.subtype in identity_subtypes and item.count > 0:
            identity_hits += item.count
        if item.subtype in {"email", "phone"} and item.count > 0:
            email_phone_hits += item.count
        if item.subtype not in strong_subtypes and item.count > 0:
            soft_hits += item.count

    if strong_hits >= 2:
        return True

    if identity_hits >= 1 and soft_hits >= 1:
        return True

    if email_phone_hits >= 2:
        return True

    if detection.categories.get("special", 0) > 0:
        return True

    if detection.categories.get("biometric", 0) > 0:
        return True

    if soft_hits >= 4:
        return True

    return False