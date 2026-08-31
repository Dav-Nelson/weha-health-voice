"""
Rule-based urgency assessment for Weha Health voice triage.
Covers general symptom danger signs, with a maternal-health-specific
branch (WHO-aligned danger signs) as the flagship scenario.
"""

MATERNAL_DANGER_SIGNS = {
    "heavy_bleeding": "Heavy vaginal bleeding can be life-threatening and needs urgent care.",
    "severe_headache": "Severe headache with vision changes can signal pre-eclampsia.",
    "reduced_fetal_movement": "Reduced or absent baby movement needs urgent checking.",
    "severe_abdominal_pain": "Severe abdominal pain in pregnancy needs urgent evaluation.",
    "high_fever": "High fever during pregnancy can indicate a serious infection.",
    "convulsions": "Convulsions or fits are a medical emergency in pregnancy.",
}

GENERAL_DANGER_SIGNS = {
    "difficulty_breathing": "Difficulty breathing needs urgent medical attention.",
    "chest_pain": "Chest pain should be evaluated urgently.",
    "high_fever": "Persistent high fever needs medical evaluation.",
    "severe_pain": "Severe, unrelieved pain needs medical evaluation.",
    "confusion": "Confusion or altered consciousness is a medical emergency.",
}


def assess_urgency(fields: dict) -> dict:
    """
    fields expected keys (all optional, filled by the LLM extractor):
      symptom_category, symptoms (list[str]), duration, severity,
      is_pregnant (bool), danger_signs (list[str] matched by the extractor)
    """
    matched = []
    danger_signs_present = fields.get("danger_signs", []) or []

    sign_pool = MATERNAL_DANGER_SIGNS if fields.get("is_pregnant") else GENERAL_DANGER_SIGNS

    for sign in danger_signs_present:
        normalized = sign.lower().replace(" ", "_")
        if normalized in sign_pool:
            matched.append({"sign": normalized, "explanation": sign_pool[normalized]})

    severity = (fields.get("severity") or "").lower()

    if matched or severity == "severe":
        urgency = "urgent"
        guidance = "Please seek medical care as soon as possible. This is not a substitute for a doctor's evaluation."
    elif severity == "moderate":
        urgency = "moderate"
        guidance = "Please see a health worker soon if symptoms continue or worsen."
    else:
        urgency = "routine"
        guidance = "Monitor your symptoms. See a health worker if things get worse."

    return {
        "urgency": urgency,
        "matched_signs": matched,
        "guidance": guidance
    }