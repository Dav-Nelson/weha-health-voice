"""
Rule-based urgency assessment for Weha Health voice triage.
Covers general symptom danger signs, with a maternal-health-specific
branch (WHO-aligned danger signs) as the flagship scenario.

Guidance and danger-sign explanations are localized to our 5 target
languages, matching the pattern used in rag/query.py's FALLBACK_MESSAGES.
Translations below are a first pass — team native speakers should
review before final submission, same as HelpModal and App.js copy.
"""

MATERNAL_DANGER_SIGNS = {
    "heavy_bleeding": {
        "English": "Heavy vaginal bleeding can be life-threatening and needs urgent care.",
        "Nigerian Pidgin": "Heavy bleeding for your private part fit dangerous well well, e need urgent care.",
        "Yoruba": "Ẹ̀jẹ̀ tí ó pọ̀jù láti abẹ́ lè léwu gan an, ó nílò ìtọ́jú kánjúkánjú.",
        "Akan": "Mogya a ɛba mmoroso wɔ awo mu betumi ayɛ hu na ɛhia ntɛm ayaresa.",
        "Amharic": "ከፍተኛ የማህፀን ደም መፍሰስ ለሕይወት አስጊ ሊሆን ይችላል፣ አፋጣኝ እርዳታ ያስፈልጋል።",
    },
    "severe_headache": {
        "English": "Severe headache with vision changes can signal pre-eclampsia.",
        "Nigerian Pidgin": "Serious headache wey come with eye wey dey blur fit be sign of pre-eclampsia.",
        "Yoruba": "Orí fífọ́ tó le pẹ̀lú ìyípadà ojú lè jẹ́ àmì pre-eclampsia.",
        "Akan": "Ti wo ti yɛ den kɛse na w'ani so sesa a, ebetumi akyerɛ pre-eclampsia.",
        "Amharic": "ከዓይን ለውጥ ጋር ከባድ ራስ ምታት ቅድመ ኤክላምፕሲያን ሊያመለክት ይችላል።",
    },
    "reduced_fetal_movement": {
        "English": "Reduced or absent baby movement needs urgent checking.",
        "Nigerian Pidgin": "If baby no dey move well or e stop to move, e need urgent check up.",
        "Yoruba": "Bí ọmọ inú kò bá ṣí kiri dáadáa tàbí kò ṣí rárá, ó nílò àyẹ̀wò kánjúkánjú.",
        "Akan": "Sɛ abofra a ɔwɔ awotwaa mu no ntumi nkeka ne ho yiye anaasɛ ɔnkeka ne ho koraa a, ehia ntɛm nhwehwɛmu.",
        "Amharic": "የልጅ እንቅስቃሴ መቀነስ ወይም መጥፋት አፋጣኝ ምርመራ ያስፈልገዋል።",
    },
    "severe_abdominal_pain": {
        "English": "Severe abdominal pain in pregnancy needs urgent evaluation.",
        "Nigerian Pidgin": "Serious pain for belle when you dey pregnant need urgent check.",
        "Yoruba": "Ìrora ikun tó le nígbà oyún nílò àyẹ̀wò kánjúkánjú.",
        "Akan": "Yafunu mu ya a ano yɛ den wɔ awoyɛ mu no hia ntɛm nhwehwɛmu.",
        "Amharic": "በእርግዝና ወቅት ከባድ የሆድ ህመም አፋጣኝ ምርመራ ያስፈልገዋል።",
    },
    "high_fever": {
        "English": "High fever during pregnancy can indicate a serious infection.",
        "Nigerian Pidgin": "Serious fever when you dey pregnant fit mean say infection dey.",
        "Yoruba": "Ibà gbóná nígbà oyún lè fi hàn pé àkóràn le kan wà.",
        "Akan": "Huraeɛ a emu yɛ den wɔ awoyɛ mu no betumi akyerɛ ɔyaredɔm a ano yɛ den.",
        "Amharic": "በእርግዝና ወቅት ከፍተኛ ትኩሳት ከባድ ኢንፌክሽንን ሊያመለክት ይችላል።",
    },
    "convulsions": {
        "English": "Convulsions or fits are a medical emergency in pregnancy.",
        "Nigerian Pidgin": "If body dey shake or you get fit, na emergency for pregnancy.",
        "Yoruba": "Gìrì tàbí wíwárìrì jẹ́ pàjáwìrì ìṣègùn nígbà oyún.",
        "Akan": "Ntwaho anaa nkitahodie yɛ ɔyaresafo a ɛho hia ntɛm wɔ awoyɛ mu.",
        "Amharic": "መንቀጥቀጥ ወይም ቁርጠት በእርግዝና ወቅት የድንገተኛ ህክምና ጉዳይ ነው።",
    },
}

GENERAL_DANGER_SIGNS = {
    "difficulty_breathing": {
        "English": "Difficulty breathing needs urgent medical attention.",
        "Nigerian Pidgin": "If you no dey fit breathe well, e need urgent medical attention.",
        "Yoruba": "Ìṣòro mímí nílò ìtọ́jú ìṣègùn kánjúkánjú.",
        "Akan": "Ahome a ɛyɛ den hia ntɛm ayaresa.",
        "Amharic": "የመተንፈስ ችግር አፋጣኝ የህክምና እርዳታ ያስፈልገዋል።",
    },
    "chest_pain": {
        "English": "Chest pain should be evaluated urgently.",
        "Nigerian Pidgin": "Chest pain need make dem check am urgent.",
        "Yoruba": "Ìrora àyà nílò àyẹ̀wò kánjúkánjú.",
        "Akan": "Koko mu yaw hia nhwehwɛmu ntɛm.",
        "Amharic": "የደረት ህመም አፋጣኝ ምርመራ ያስፈልገዋል።",
    },
    "high_fever": {
        "English": "Persistent high fever needs medical evaluation.",
        "Nigerian Pidgin": "Fever wey no wan comot need make dem check am.",
        "Yoruba": "Ibà gbígbóná tí kò dá nílò àyẹ̀wò ìṣègùn.",
        "Akan": "Huraeɛ a ɛkɔ so hia ayaresa nhwehwɛmu.",
        "Amharic": "የማያቋርጥ ከፍተኛ ትኩሳት የህክምና ምርመራ ያስፈልገዋል።",
    },
    "severe_pain": {
        "English": "Severe, unrelieved pain needs medical evaluation.",
        "Nigerian Pidgin": "Serious pain wey no dey comot need make dem check am.",
        "Yoruba": "Ìrora líle tí kò dín kù nílò àyẹ̀wò ìṣègùn.",
        "Akan": "Ya kɛse a ɛnnyae hia ayaresa nhwehwɛmu.",
        "Amharic": "ከባድ እና የማይለቅ ህመም የህክምና ምርመራ ያስፈልገዋል።",
    },
    "confusion": {
        "English": "Confusion or altered consciousness is a medical emergency.",
        "Nigerian Pidgin": "If person confuse or e no dey fully awake, na emergency.",
        "Yoruba": "Ìdàrúdàpọ̀ tàbí ìyípadà ìmọ̀ jẹ́ pàjáwìrì ìṣègùn.",
        "Akan": "Adwenem basabasa anaa adwene a asesa yɛ ɔyaresafo a ɛho hia ntɛm.",
        "Amharic": "ግራ መጋባት ወይም የንቃተ ህሊና ለውጥ የድንገተኛ ህክምና ጉዳይ ነው።",
    },
}

GUIDANCE_TEXT = {
    "urgent": {
        "English": "Please seek medical care as soon as possible. This is not a substitute for a doctor's evaluation.",
        "Nigerian Pidgin": "Abeg go see doctor as soon as possible. This no be substitute for wetin doctor go check.",
        "Yoruba": "Jọ̀wọ́ lọ wá ìtọ́jú ìṣègùn ní kíákíá bó ti ṣeéṣe. Èyí kì í ṣe ìdípò àyẹ̀wò dókítà.",
        "Akan": "Yɛsrɛ wo kɔpɛ ayaresa ntɛm sɛ ɛbɛtumi. Wei nyɛ oduruyɛfo nhwehwɛmu ananmu.",
        "Amharic": "እባክዎ በተቻለ ፍጥነት የህክምና እርዳታ ይፈልጉ። ይህ የዶክተር ምርመራ ምትክ አይደለም።",
    },
    "moderate": {
        "English": "Please see a health worker soon if symptoms continue or worsen.",
        "Nigerian Pidgin": "Abeg go see health worker soon if the symptoms still dey continue or e worse pass.",
        "Yoruba": "Jọ̀wọ́ lọ bá òṣìṣẹ́ ìlera láìpẹ́ bí àwọn àmì àìsàn bá ń bá a lọ tàbí tí ó bá burú sí i.",
        "Akan": "Yɛsrɛ wo kɔhwɛ ɔyaresafo ntɛm sɛ nsɛnkyerɛnne no kɔ so anaasɛ ɛyɛ den kɛse.",
        "Amharic": "ምልክቶቹ ከቀጠሉ ወይም ከባሱ በቅርቡ የጤና ባለሙያ ያማክሩ።",
    },
    "routine": {
        "English": "Monitor your symptoms. See a health worker if things get worse.",
        "Nigerian Pidgin": "Dey monitor wetin dey happen to you. Go see health worker if e worse.",
        "Yoruba": "Máa ṣàkíyèsí àwọn àmì àìsàn rẹ. Lọ bá òṣìṣẹ́ ìlera bí nǹkan bá burú sí i.",
        "Akan": "Hwɛ wo nsɛnkyerɛnne no yiye. Kɔhwɛ ɔyaresafo sɛ nneɛma kɔ so bɔne.",
        "Amharic": "ምልክቶችዎን ይከታተሉ። ነገሮች ከባሱ የጤና ባለሙያ ያማክሩ።",
    },
}


def assess_urgency(fields: dict, language: str = "English") -> dict:
    """
    fields expected keys (all optional, filled by the LLM extractor):
      symptom_category, symptoms (list[str]), duration, severity,
      is_pregnant (bool), danger_signs (list[str] matched by the extractor)

    language: full language name matching rag/query.py's SUPPORTED_LANGUAGES
      ("English", "Nigerian Pidgin", "Yoruba", "Akan", "Amharic").
      Falls back to English text if the language key is missing.
    """
    matched = []
    danger_signs_present = fields.get("danger_signs", []) or []

    sign_pool = MATERNAL_DANGER_SIGNS if fields.get("is_pregnant") else GENERAL_DANGER_SIGNS

    for sign in danger_signs_present:
        normalized = sign.lower().replace(" ", "_")
        if normalized in sign_pool:
            explanation = sign_pool[normalized].get(language, sign_pool[normalized]["English"])
            matched.append({"sign": normalized, "explanation": explanation})

    severity = (fields.get("severity") or "").lower()

    if matched or severity == "severe":
        urgency = "urgent"
    elif severity == "moderate":
        urgency = "moderate"
    else:
        urgency = "routine"

    guidance = GUIDANCE_TEXT[urgency].get(language, GUIDANCE_TEXT[urgency]["English"])

    return {
        "urgency": urgency,
        "matched_signs": matched,
        "guidance": guidance
    }