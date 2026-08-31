"""
LLM-based structured field extraction + clarifying-question generation
for the multi-turn voice intake flow. Uses the same Groq client as the
rest of the pipeline (no new dependency, no new cost).
"""
import json

REQUIRED_FIELDS = ["symptom_category", "symptoms", "duration", "severity"]


def extract_fields(transcript: str, existing_fields: dict, language: str, client) -> dict:
    """
    Merges new info from the latest transcript into the fields gathered so far.
    Returns an updated fields dict.
    """
    prompt = f"""You are a medical intake assistant extracting structured data from a patient's spoken description.
The patient may be speaking in a mix of {language} and English.

Fields to fill (use null if not mentioned):
- symptom_category: one of ["maternal", "general"]
- symptoms: list of symptom strings mentioned
- duration: how long symptoms have lasted
- severity: one of ["mild", "moderate", "severe"]
- is_pregnant: true/false/null
- danger_signs: list of any danger signs mentioned, from this set:
  ["heavy_bleeding", "severe_headache", "reduced_fetal_movement", "severe_abdominal_pain",
   "high_fever", "convulsions", "difficulty_breathing", "chest_pain", "severe_pain", "confusion"]

Existing known fields (merge with, don't discard, unless the new transcript updates them):
{json.dumps(existing_fields)}

New transcript: "{transcript}"

Respond ONLY with valid JSON matching the fields above, no extra text.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    extracted = json.loads(response.choices[0].message.content)

    merged = {**existing_fields}
    for key, value in extracted.items():
        if value not in (None, "", []):
            merged[key] = value

    return merged


def generate_clarifying_question(missing_field: str, fields_so_far: dict, language: str, client) -> str:
    """
    Generates a natural, short follow-up question in the patient's language
    to fill in the next missing required field.
    """
    prompt = f"""You are a warm, clear voice health assistant speaking to a patient in {language} (mixed with English is fine, matching how they've been speaking).

You already know: {json.dumps(fields_so_far)}

You still need to find out: "{missing_field}"

Ask ONE short, natural, non-clinical-sounding question to get this information.
Respond with ONLY the question text, nothing else.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()