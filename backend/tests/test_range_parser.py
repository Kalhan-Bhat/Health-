"""Unit tests for range_parser (spec §8.4 requires at least 20 cases)."""

import pytest

from app.services.range_parser import compute_status, flag_to_status, parse_number, parse_range


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("10.8", 10.8),
        ("10,8", 10.8),  # comma decimal
        ("7,200", 7200.0),  # Western thousands separator
        ("1,50,000", 150000.0),  # Indian number grouping
        ("2,45,000 /µL", 245000.0),
        ("150 x10^3", 150.0),
        ("  6.4 ", 6.4),
        ("<0.5", 0.5),
        ("Negative", None),  # qualitative result
        ("Non-reactive", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_number(raw, expected) -> None:
    assert parse_number(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("12.0 - 15.5", (12.0, 15.5)),
        ("12–15.5", (12.0, 15.5)),  # en dash
        ("12—15.5", (12.0, 15.5)),  # em dash
        ("12-15 g/dL", (12.0, 15.0)),  # unit inside the range string
        ("4,000 - 11,000", (4000.0, 11000.0)),
        ("1,50,000 - 4,10,000", (150000.0, 410000.0)),  # Indian grouping
        ("0.4 to 4.0", (0.4, 4.0)),
        ("< 200", (None, 200.0)),
        ("Less than 200", (None, 200.0)),
        ("Up to 200", (None, 200.0)),
        ("≤ 5.1", (None, 5.1)),
        ("> 40", (40.0, None)),
        ("More than 40", (40.0, None)),
        (">= 40", (40.0, None)),
        ("Desirable < 200", (None, 200.0)),
        ("Desirable: <200 Borderline: 200-239 High: >=240", (None, 200.0)),  # first band
        ("Normal < 5.7, Prediabetes 5.7-6.4", (None, 5.7)),
        ("15 - 12", (12.0, 15.0)),  # reversed range tolerated
        ("Negative", (None, None)),
        ("", (None, None)),
        (None, (None, None)),
    ],
)
def test_parse_range(raw, expected) -> None:
    assert parse_range(raw) == expected


@pytest.mark.parametrize(
    "flag, expected",
    [
        ("H", "high"),
        ("High", "high"),
        ("↑", "high"),
        ("HH CRITICAL", "high"),
        ("L", "low"),
        ("Low", "low"),
        ("↓", "low"),
        ("LL", "low"),
        ("Borderline High", "borderline"),
        ("*", None),  # no direction
        ("", None),
        (None, None),
    ],
)
def test_flag_to_status(flag, expected) -> None:
    assert flag_to_status(flag) == expected


@pytest.mark.parametrize(
    "value, low, high, flag, expected",
    [
        (10.8, 12.0, 15.5, None, ("low", "computed")),
        (13.0, 12.0, 15.5, None, ("normal", "computed")),
        (16.0, 12.0, 15.5, None, ("high", "computed")),
        (12.0, 12.0, 15.5, None, ("normal", "computed")),  # boundary is inside
        (162, None, 100, None, ("high", "computed")),  # one-sided upper
        (38, 40, None, None, ("low", "computed")),  # one-sided lower
        (10.8, 12.0, 15.5, "L", ("low", "computed")),  # flag agrees
        (14.0, 12.0, 15.5, "H", ("high", "lab_flag")),  # disagreement → trust lab
        (None, None, None, "H", ("high", "lab_flag")),  # no numbers, lab flag only
        (None, 12.0, 15.5, "Low", ("low", "lab_flag")),
        (None, None, None, None, ("unknown", "none")),
        (5.0, None, None, None, ("unknown", "none")),  # value but no range
        (5.0, None, None, "*", ("unknown", "none")),
    ],
)
def test_compute_status(value, low, high, flag, expected) -> None:
    assert compute_status(value, low, high, flag) == expected
