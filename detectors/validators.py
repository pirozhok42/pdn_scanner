from __future__ import annotations

import re


def digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def luhn_check(number: str) -> bool:
    s = digits_only(number)
    if not 13 <= len(s) <= 19:
        return False

    total = 0
    reverse_digits = s[::-1]
    for i, ch in enumerate(reverse_digits):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def snils_check(value: str) -> bool:
    s = digits_only(value)
    if len(s) != 11:
        return False

    num = s[:9]
    control = int(s[9:])

    total = sum(int(num[i]) * (9 - i) for i in range(9))
    if total < 100:
        expected = total
    elif total in (100, 101):
        expected = 0
    else:
        expected = total % 101
        if expected == 100:
            expected = 0

    return expected == control


def inn_fl_check(value: str) -> bool:
    s = digits_only(value)
    if len(s) != 12:
        return False

    coeff_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    coeff_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]

    n11 = sum(int(s[i]) * coeff_11[i] for i in range(10)) % 11 % 10
    n12 = sum(int(s[i]) * coeff_12[i] for i in range(11)) % 11 % 10

    return n11 == int(s[10]) and n12 == int(s[11])


def inn_ul_check(value: str) -> bool:
    s = digits_only(value)
    if len(s) != 10:
        return False

    coeff = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    n10 = sum(int(s[i]) * coeff[i] for i in range(9)) % 11 % 10
    return n10 == int(s[9])


def bik_check(value: str) -> bool:
    s = digits_only(value)
    return len(s) == 9


def account_check(value: str) -> bool:
    s = digits_only(value)
    return len(s) == 20


def mask_value(value: str, keep_start: int = 2, keep_end: int = 2) -> str:
    if len(value) <= keep_start + keep_end:
        return "*" * len(value)
    return value[:keep_start] + "*" * (len(value) - keep_start - keep_end) + value[-keep_end:]