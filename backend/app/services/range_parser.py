"""Turn the strings printed on a lab report into numbers and a status (spec §8.4).

These are pure functions with no LLM involved. This is how MedBridge avoids trusting
an AI-invented range: the LLM only copies the raw text, and this module decides
whether a value is low, normal or high.
"""

import logging
import re

from app.schemas import Status

logger = logging.getLogger("medbridge.range_parser")

# A number: digits with optional thousands separators (Western 1,000,000 or Indian
# 1,50,000 grouping) and an optional decimal part. A lone comma decimal ("10,8")
# is handled separately in parse_number.
_NUMBER = r"\d+(?:,\d+)*(?:\.\d+)?"
_NUMBER_RE = re.compile(_NUMBER)

# Range separators: hyphen, en dash, em dash, or the word "to".
_RANGE_RE = re.compile(rf"({_NUMBER})\s*(?:-|–|—|to)\s*({_NUMBER})", re.IGNORECASE)

# One-sided ranges. "Up to 200", "<200", "less than 200", "≤ 200", "below 200".
_UPPER_RE = re.compile(
    rf"(?:<=?|≤|less\s+than|up\s*to|upto|below|under|max(?:imum)?)\s*:?\s*({_NUMBER})",
    re.IGNORECASE,
)
# ">40", ">= 40", "more than 40", "greater than 40", "above 40", "≥ 40".
_LOWER_RE = re.compile(
    rf"(?:>=?|≥|more\s+than|greater\s+than|above|over|min(?:imum)?)\s*:?\s*({_NUMBER})",
    re.IGNORECASE,
)

# Flags that clearly state a direction. A bare "*" or "A" (abnormal) does not say
# which direction, so it is not mapped here.
_HIGH_FLAGS = {"H", "HI", "HIGH", "↑", "HH", "ABOVE"}
_LOW_FLAGS = {"L", "LO", "LOW", "↓", "LL", "BELOW"}
_BORDERLINE_WORDS = ("BORDERLINE",)


def parse_number(s: str | None) -> float | None:
    """Pull the main number out of a printed value.

    "10.8" → 10.8, "10,8" → 10.8 (comma decimal), "1,50,000" → 150000 (Indian grouping),
    "7,200" → 7200, "150 x10^3" → 150.0, "Negative" → None.
    """
    if s is None:
        return None
    text = str(s).strip()
    if not text:
        return None

    # A comma decimal such as "10,8" or "4,25": exactly one comma, then 1–2 digits
    # (3 digits after a comma means a thousands separator, as in "7,200").
    comma_decimal = re.fullmatch(r"\s*[<>]?\s*(\d+),(\d{1,2})\s*\D*", text)
    if comma_decimal:
        return float(f"{comma_decimal.group(1)}.{comma_decimal.group(2)}")

    match = _NUMBER_RE.search(text)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def parse_range(s: str | None) -> tuple[float | None, float | None]:
    """Convert a reference-range string into (low, high). Missing side → None.

    "12.0 - 15.5" → (12.0, 15.5); "12–15.5 g/dL" → (12.0, 15.5)
    "< 200" / "Less than 200" / "Up to 200" → (None, 200)
    "> 40" / "More than 40" / ">= 40" → (40, None)
    "Desirable: <200 Borderline: 200-239 High: >=240" → (None, 200)  (first band wins)
    "Negative" / "" / None → (None, None)
    """
    if not s:
        return (None, None)
    text = str(s).strip()

    # Find the earliest-starting pattern, so labelled bands such as
    # "Desirable: <200 Borderline: 200-239" use the first (desirable) band.
    candidates = []
    for kind, regex in (("range", _RANGE_RE), ("upper", _UPPER_RE), ("lower", _LOWER_RE)):
        m = regex.search(text)
        if m:
            candidates.append((m.start(), kind, m))
    if not candidates:
        return (None, None)

    _, kind, m = min(candidates, key=lambda c: c[0])
    if kind == "range":
        low, high = parse_number(m.group(1)), parse_number(m.group(2))
        if low is not None and high is not None and low > high:
            low, high = high, low  # tolerate reversed ranges like "15 - 12"
        return (low, high)
    if kind == "upper":
        return (None, parse_number(m.group(1)))
    return (parse_number(m.group(1)), None)


def flag_to_status(lab_flag: str | None) -> Status | None:
    """Map the flag printed by the lab ("H", "Low", "↑", "*", "HH CRITICAL") to a status.

    Returns None when the flag does not say a direction (e.g. "*" on its own).
    """
    if not lab_flag:
        return None
    flag = lab_flag.strip().upper()
    if not flag:
        return None
    if any(word in flag for word in _BORDERLINE_WORDS):
        return "borderline"
    # Look at each word, so "HH CRITICAL" → high and "L*" → low.
    for token in re.split(r"[\s,/*()]+", flag):
        if token in _HIGH_FLAGS:
            return "high"
        if token in _LOW_FLAGS:
            return "low"
    if "HIGH" in flag or "↑" in flag:
        return "high"
    if "LOW" in flag or "↓" in flag:
        return "low"
    return None


def compute_status(
    value: float | None,
    low: float | None,
    high: float | None,
    lab_flag: str | None,
) -> tuple[Status, str]:
    """Decide the status of one result. Returns (status, status_source).

    1. If we have a number and at least one bound, compare numerically ("computed").
    2. If the lab printed a flag that disagrees with our comparison, trust the lab
       (labs may use age/sex-specific cut-offs we cannot see) and log a warning.
    3. If there is no usable number/range, fall back to the lab's flag ("lab_flag").
    4. Otherwise the status is unknown ("none").
    """
    flag_status = flag_to_status(lab_flag)

    if value is not None and (low is not None or high is not None):
        if low is not None and value < low:
            computed: Status = "low"
        elif high is not None and value > high:
            computed = "high"
        else:
            computed = "normal"

        if flag_status is not None and flag_status != computed:
            # Do not log the value itself (privacy) — only that a disagreement happened.
            logger.warning("Lab flag disagrees with computed status; using lab flag.")
            return (flag_status, "lab_flag")
        return (computed, "computed")

    if flag_status is not None:
        return (flag_status, "lab_flag")
    return ("unknown", "none")
