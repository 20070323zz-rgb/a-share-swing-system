from __future__ import annotations

import re
from datetime import date


DASHED_DATE = re.compile(r"^20\d{2}-[01]\d-[0-3]\d$")
COMPACT_DATE = re.compile(r"^20\d{6}$")
DASHED_MONTH = re.compile(r"^20\d{2}-[01]\d$")
COMPACT_MONTH = re.compile(r"^20\d{4}$")


def valid_date_token(value: str, allow_compact: bool = True) -> bool:
    if DASHED_DATE.fullmatch(value):
        year, month, day = (int(part) for part in value.split("-"))
    elif allow_compact and COMPACT_DATE.fullmatch(value):
        year, month, day = int(value[:4]), int(value[4:6]), int(value[6:8])
    else:
        return False
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def valid_month_token(value: str, allow_compact: bool = False) -> bool:
    if DASHED_MONTH.fullmatch(value):
        year, month = (int(part) for part in value.split("-"))
    elif allow_compact and COMPACT_MONTH.fullmatch(value):
        year, month = int(value[:4]), int(value[4:6])
    else:
        return False
    return 2000 <= year <= 2099 and 1 <= month <= 12
