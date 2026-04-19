from __future__ import annotations

import re


PATTERNS = {
    "email": re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),
    "phone": re.compile(r"(?<!\d)(?:\+7|8)?[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}(?!\d)"),
    "birth_date": re.compile(r"\b(?:0[1-9]|[12]\d|3[01])[./-](?:0[1-9]|1[0-2])[./-](?:19\d{2}|20\d{2})\b"),
    "passport_rf": re.compile(r"\b\d{2}\s?\d{2}\s?\d{6}\b"),
    "snils": re.compile(r"\b\d{3}-\d{3}-\d{3}\s\d{2}\b|\b\d{11}\b"),
    "inn": re.compile(r"\b\d{10}\b|\b\d{12}\b"),
    "card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "bik": re.compile(r"\b\d{9}\b"),
    "account": re.compile(r"\b\d{20}\b"),
    "cvv": re.compile(r"(?i)\b(?:cvv|cvc|cvv2|cvc2)\D{0,5}(\d{3,4})\b"),
    "mrz": re.compile(r"\bP<[A-Z<]{10,}\b|\b[A-Z0-9<]{30,44}\b"),
}

SPECIAL_KEYWORDS = {
    "health": [
        "здоровье", "диагноз", "пациент", "болезнь", "медицин", "анализы", "инвалид",
        "health", "diagnosis", "patient", "disease", "medical", "disability"
    ],
    "religion": [
        "религ", "вероисповед", "православ", "мусульман", "христиан", "будд",
        "religion", "faith", "christian", "muslim", "buddhist"
    ],
    "politics": [
        "политическ", "партия", "оппозиция", "депутат", "голосование",
        "politic", "party member", "election", "opposition", "voting"
    ],
    "race_nationality": [
        "национальн", "раса", "этническ",
        "nationality", "race", "ethnic", "ethnicity"
    ],
}

BIOMETRIC_KEYWORDS = [
    "биометр", "отпечат", "радужк", "голосовой образец", "face recognition",
    "biometric", "fingerprint", "iris", "voice sample", "facial geometry"
]

COMMON_PD_KEYWORDS = {
    "fio_context": [
        "фио", "фамилия", "имя", "отчество",
        "full name", "surname", "first name", "last name", "patronymic"
    ],
    "birth_place": [
        "место рождения", "birth place", "born in"
    ],
    "address": [
        "адрес", "адрес проживания", "регистрация", "место жительства",
        "address", "residence", "registration address"
    ],
}

FIO_RU_PATTERN = re.compile(r"\b[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2}\b")
FIO_EN_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b")