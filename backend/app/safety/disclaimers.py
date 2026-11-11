"""Fixed safety text (spec §12). Returned with every AI response and shown in the UI."""

DISCLAIMER = (
    "MedBridge provides educational information only and is not a substitute for "
    "professional medical advice, diagnosis, or treatment. Always discuss your results "
    "with a qualified healthcare provider. If you think you may have a medical emergency, "
    "contact your local emergency number immediately."
)

EMERGENCY_MESSAGE = (
    "It sounds like you may need urgent help. MedBridge can't help with emergencies. "
    "Please contact your local emergency number (for example, 112 in India) or go to the "
    "nearest emergency department right away."
)

RED_FLAG_MESSAGE = (
    "Your report marks this value as critical. Please contact your doctor or the lab promptly."
)
