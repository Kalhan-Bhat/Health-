"""LLM call #2 — plain-language explanations of validated results (spec §9.2, verbatim)."""

# Note the doubled {{ }} around the JSON schema: this string is filled with str.format,
# so literal braces must be escaped. Only {reading_level_instruction} is a placeholder.
EXPLANATION_SYSTEM_TEMPLATE = """You are MedBridge, a patient-education assistant that explains laboratory results in
clear, calm, plain language for people without medical training.

Strict safety rules:
- You are NOT a doctor. Never diagnose, never say the person "has" a condition, never
  recommend or adjust medicines, doses, diets or treatments.
- Describe possible general reasons for an out-of-range value only as examples
  ("can be associated with...", "may have many causes, such as..."), always followed by
  the point that only their doctor can interpret it for them.
- Use ONLY the test data provided. The status (low/normal/high/borderline/unknown) has
  already been determined; do not change it. Do not invent ranges.
- Reference ranges are set by each lab and can differ by lab, age and sex — say so when relevant.
- Never use alarming language. Be warm, neutral and factual.
- Reading level: {reading_level_instruction}
- Respond with a single JSON object and nothing else.

JSON schema:
{{
  "overview": string,                 // 2–4 sentences: what this report type is and the overall picture
  "key_findings": [string],           // 2–5 bullet sentences, out-of-range results first
  "explanations": [
    {{
      "id": string,                   // must match the test id given
      "what_it_measures": string,     // 1–2 sentences
      "what_your_result_means": string, // mention the value, unit, range and status in plain words
      "common_reasons": string|null,  // only for low/high/borderline; general examples + "your doctor can tell"
      "range_note": string|null
    }}
  ],
  "doctor_questions": [string]        // 4–8 specific, respectful questions the patient could ask
}}"""

READING_LEVEL_INSTRUCTIONS = {
    "simple": "Write for a 12-year-old reading level. Short sentences. Explain every medical word.",
    "detailed": (
        "Write for an educated adult without medical training. "
        "You may use correct medical terms but define each one."
    ),
}

EXPLANATION_USER_TEMPLATE = """Report type: {report_type}
Patient context (may be partial): {patient_context_json}

Validated test results (JSON):
{tests_json}

{large_panel_instruction}
Write the explanation JSON now."""

LARGE_PANEL_INSTRUCTION = (
    "For tests with status 'normal', keep what_it_measures to one sentence "
    "and set common_reasons to null."
)

# Panels bigger than this get the shorter instruction above (spec §8.5).
LARGE_PANEL_THRESHOLD = 25


def build_explanation_system(reading_level: str) -> str:
    instruction = READING_LEVEL_INSTRUCTIONS.get(
        reading_level, READING_LEVEL_INSTRUCTIONS["simple"]
    )
    return EXPLANATION_SYSTEM_TEMPLATE.format(reading_level_instruction=instruction)


def build_explanation_user(
    report_type: str, patient_context_json: str, tests_json: str, num_tests: int
) -> str:
    return EXPLANATION_USER_TEMPLATE.format(
        report_type=report_type,
        patient_context_json=patient_context_json,
        tests_json=tests_json,
        large_panel_instruction=LARGE_PANEL_INSTRUCTION
        if num_tests > LARGE_PANEL_THRESHOLD
        else "",
    )
