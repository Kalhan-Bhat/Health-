"""Lightweight safety checks around the LLM (spec §8.6).

The system prompts are the main safety control. These checks are a second layer:
- red flags come only from the lab's own critical markers (we never invent thresholds),
- emergency questions skip the LLM entirely,
- report text is cleaned before it goes into a prompt,
- answers are screened for prescriptive phrasing.
"""

import logging
import re
import unicodedata
from collections.abc import Sequence

from app.safety.disclaimers import RED_FLAG_MESSAGE
from app.schemas import LabTest, RedFlag

logger = logging.getLogger("medbridge.guardrails")

# ----------------------------------------------------------------- red flags

# Markers labs print next to critical values. Matched as whole words in the flag,
# so "HH" matches but "HIGH" does not, and "LL" does not match inside "CELL".
_CRITICAL_FLAG_RE = re.compile(r"(?<![A-Z])(CRITICAL|CRIT|PANIC|HH|LL)(?![A-Z])|!!", re.IGNORECASE)


def detect_red_flags(tests: Sequence[LabTest], text: str) -> list[RedFlag]:
    """Return a red flag for every test whose lab flag contains a critical marker.

    Also scans each report line that mentions the test's name, in case the
    extraction step dropped the marker from `lab_flag`.
    """
    lines = text.splitlines()
    flags: list[RedFlag] = []
    for test in tests:
        flagged = bool(test.lab_flag and _CRITICAL_FLAG_RE.search(test.lab_flag))
        if not flagged:
            name = test.name.lower()
            flagged = any(
                name in line.lower() and _CRITICAL_FLAG_RE.search(_strip_test_name(line, name))
                for line in lines
            )
        if flagged:
            flags.append(RedFlag(test_id=test.id, message=f"{test.name}: {RED_FLAG_MESSAGE}"))
    return flags


def _strip_test_name(line: str, name_lower: str) -> str:
    """Remove the test name from a line so a name like 'HH Ratio' can't look critical."""
    idx = line.lower().find(name_lower)
    return line[:idx] + line[idx + len(name_lower) :] if idx >= 0 else line


# ----------------------------------------------------------------- emergencies

# Phrases suggesting a medical emergency happening now. Kept deliberately broad:
# a false positive only shows the emergency message, which is safe.
_EMERGENCY_PATTERNS = [
    r"chest pain",
    r"pain in (my )?chest",
    r"can'?t breathe",
    r"cannot breathe",
    r"can not breathe",
    r"trouble breathing",
    r"difficulty breathing",
    r"short(ness)? of breath",
    r"not breathing",
    r"suicid",
    r"kill myself",
    r"end my life",
    r"want to die",
    r"self[- ]harm",
    r"overdos",
    r"fainted",
    r"passed out",
    r"unconscious",
    r"severe bleeding",
    r"bleeding (heavily|a lot|won'?t stop)",
    r"coughing (up )?blood",
    r"vomiting blood",
    r"stroke",
    r"face (is )?droop",
    r"slurred speech",
    r"seizure",
    r"heart attack",
    r"anaphyla",
    r"throat (is )?(closing|swelling)",
    r"poison",
]
_EMERGENCY_RE = re.compile("|".join(_EMERGENCY_PATTERNS), re.IGNORECASE)

# Educational phrasing that mentions a scary word but is clearly not an emergency.
_EDUCATIONAL_RE = re.compile(
    r"\b(risk of|risk for|linked (to|with)|associated with|what is|what are|"
    r"what does|how (does|do|is)|difference between|cholesterol and)\b",
    re.IGNORECASE,
)
_URGENT_RE = re.compile(r"\b(right now|now|currently|having|i have|i'?m|i am|help)\b", re.I)


def is_emergency_question(question: str) -> bool:
    """True if the question looks like someone describing an emergency.

    "I have chest pain right now" → True.
    "Is high LDL linked to stroke risk?" → False (educational question).
    """
    if not _EMERGENCY_RE.search(question):
        return False
    # An educational question with no sign of urgency is not an emergency.
    return not (_EDUCATIONAL_RE.search(question) and not _URGENT_RE.search(question))


# ----------------------------------------------------------------- report text


def sanitize_report_text(text: str) -> str:
    """Remove control characters and anything that could fake our prompt delimiters.

    The cleaned text is placed inside <report>...</report> in the prompt, and the prompt
    tells the model to treat it as untrusted data. Removing look-alike tags stops a PDF
    from "closing" the report block early and adding its own instructions.
    """
    cleaned = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    cleaned = re.sub(r"</?\s*report\s*>", " ", cleaned, flags=re.IGNORECASE)
    return cleaned


# ----------------------------------------------------------------- answer post-check

_PRESCRIPTIVE_RE = re.compile(
    r"you should (take|start|stop|increase|decrease|reduce)|"
    r"\b\d+\s*(mg|mcg|µg|iu)\b.{0,30}\b(daily|twice|once|a day|per day)\b|"
    r"\b(twice|once|three times) (a|per) day\b|"
    r"stop taking|start taking|"
    r"you (definitely |probably |likely )?have (anemia|anaemia|diabetes|prediabetes|"
    r"hypothyroidism|hyperthyroidism|kidney disease|liver disease|cancer|leukemia|"
    r"leukaemia|an infection|a disease)",
    re.IGNORECASE,
)

POST_CHECK_REMINDER = (
    "\n\n_Reminder: MedBridge cannot give medical or medication advice. "
    "Please talk to your doctor before making any health decisions._"
)


def post_check_answer(text: str) -> str:
    """If an answer sounds prescriptive or diagnostic, append a reminder (and log it)."""
    if _PRESCRIPTIVE_RE.search(text):
        logger.warning("Post-check: prescriptive/diagnostic phrasing detected; reminder added")
        return text + POST_CHECK_REMINDER
    return text
