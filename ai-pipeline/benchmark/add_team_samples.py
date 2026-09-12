"""
ai-pipeline/benchmark/add_team_samples.py

One-time script: appends team-recorded rows (Yoruba, Pidgin, Akan,
Amharic) to the existing samples.csv built by download_samples.py.
Run once from the ai-pipeline/benchmark/ folder, AFTER download_samples.py.
"""
import csv

TEAM_ROWS = []

# --- Yoruba (Ibukun, monolingual — labeled as supplementary/bonus, not primary) ---
YORUBA_TEXTS = [
    "Kí ni mo lè ṣe tí mo bá ní iba?",
    "Ṣé mo lè ra oogun malaria fúnra mi?",
    "Báwo ni mo ṣe lè mọ̀ pé malaria ni mo ní?",
    "Kí ló lè fa kí orí mi máa fò?",
    "Nígbà wo ni orí fífọ́ yẹ kí n lọ sí ilé ìwòsàn?",
    "Kí ló yẹ kí obìnrin tó lóyún máa ṣe láti jẹ́ kí oyun rẹ̀ lọ dáadáa?",
    "Nígbà wo ni obìnrin tó lóyún yẹ kí ó bẹ̀rẹ̀ antenatal?",
    "Kí ni àwọn àmì ewu tí obìnrin tó lóyún yẹ kí ó kíyè sí?",
    "Kí ni mo lè ṣe tí mo bá ń ṣe ẹ̀jẹ̀ nígbà tí mo lóyún?",
    "Kí ni mo yẹ kí n ṣe tí ọmọ mi bá ní iba?",
    "Igba melo ni ọmọ tuntun yẹ kí ó máa mu ọmú?",
    "Ṣé ọmú nikan ló yẹ kí ọmọ máa mu ní oṣù mẹ́fà àkọ́kọ́?",
    "Ṣé mo lè fún ọmọ mi ní omi nígbà tí mo bá ń fún un ní ọmú?",
    "Kí ni mo lè ṣe tí mo bá ń gbuuru?",
    "Kí ló lè fa ikọ́?",
    "Kí lo yẹ kí n ṣe tí ẹnikan bá gé ara rẹ̀ tí ẹ̀jẹ̀ sì ń jáde?",
    "Ó kò máa ń rẹ̀ mí lónìí ọjọ́ mẹ́ta yìí, kí ló lè fà?",
    "Ó dà bíi pé mo lóyún. Ṣé mo tún lè lọ sí oko báyìí?",
    "Ó yi a ko de de ma ko mí tí mo bá dìde dúró. Kí ló lè máa fà á báyìí?",
    "Mo gbàgbé láti l'oògùn mi lánàá. Kí ni mo lè ṣe?",
]
for i, text in enumerate(YORUBA_TEXTS, start=1):
    TEAM_ROWS.append({
        "audio_path": f"benchmark/audio/yo_{i:02d}.mp3",
        "language": "yo",
        "ground_truth": text,
    })

# --- Pidgin (David) ---
PIDGIN_TEXTS = [
    "I don dey get headache and my vision dey blurry for three days.",
    "My stomach don dey pain me since this morning and the pain dey very sharp.",
    "I don dey cough and my body weak since yesterday.",
    "I dey get fever and my body dey shake since last night.",
    "I get injury for leg and blood dey comot well well. I'm scared.",
    "My chest dey pain me and my breathing no normal.",
    "I dey shit water water shit since two days now and I feel dizzy.",
    "My head dey turn me and I no fit stand up properly.",
    "I don dey vomit since yesterday and I no get appetite.",
    "I dey feel weak and tired for some days now.",
    "My back dey pain me very well since I wake up this morning.",
    "I get sore throat and e dey pain me when I swallow food.",
    "I dey hear ringing sound for my ear and I no fit hear well.",
    "I just dey piss plenty plenty times and e dey pepper me.",
    "My eyes dey very red and it's been itching me since yesterday.",
    "I suddenly felt very dizzy and I almost fall for ground.",
    "I get wound for leg wey swell up and e dey comot water.",
    "I dey get serious tooth pain and my face don dey swell up.",
    "I dey struggle to breathe especially when I wan waka or climb staircase.",
    "I take one medicine. Now, I con dey get kro-kro for body and my mouth dey swell up.",
]
for i, text in enumerate(PIDGIN_TEXTS, start=1):
    TEAM_ROWS.append({
        "audio_path": f"benchmark/audio/pcm_{i:02d}.mp3",
        "language": "pcm",
        "ground_truth": text,
    })

# --- Akan (Peggy) ---
AKAN_TEXTS = [
    "Me ti pae me na me ni susu ebri me bɛyɛ three days.",
    "Me yem aye me ya fiti anopa na ano ye den.",
    "Me bɔ wa na my yemren ehyɛaseɛ ənnera.",
    "Me nyem na me nte akolaa no nkekaye fiti ənnera anadwo.",
    "Me wɔ high fever na me ho ɛpopor fiti ənnera anadwo.",
    "Mogya ɛtu me na me suro.",
    "Me koko ɛye me ya sɛ me home den a.",
    "Me nya diarrhea for the past two days na me ni so ebri me.",
    "Me nyem na me nan ne me nsa nyinaa honhon.",
    "Me ni su bri me na me ntumi ngyina yie.",
]
for i, text in enumerate(AKAN_TEXTS, start=1):
    TEAM_ROWS.append({
        "audio_path": f"benchmark/audio/ak_{i:02d}.mp3",
        "language": "ak",
        "ground_truth": text,
    })

# --- Amharic (Ibsa) — rows 4 and 5 corrected per confirmed audio content ---
AMHARIC_TEXTS = [
    "ለሶስት ቀናት headache ወይም ራሴን ምታት ነበረብኝ:: የማየት ችሎታዬም ድብዛዛ ወይም blurry ነው::",
    "ከጥዋት ጀምሮ ሆዴን በጣም እያመመኝ ነው:: በጣም ይወጋኛል:: It's very sharp stomach pain.",
    "እያሳልኩኝ ነው:: እና በጣም የድካም ስሜትም ይሰማኛል:: ትናንትና ነው ደግሞ የጀመረኝ:: I'm so feel very weak.",
    "ከትናንት ጀምሮ እያስታወክኩ ነው:: እናም ምንም አይነት ምግብ ሆዴ ውስጥ መቆየት አልቻለም::",
    "Since ከሁለት ቀናት በፊት ጀምሮ ከፍተኛ fever ትኩሳት አለብኝ:: እና last night ከትናንትና ማታ ጀምሮ ደግሞ እየተንቀጠቀጥኩ ነው::",
    "I'm on my period. የወር አበባዬ ላይ ነኝ:: እና ከፍተኛ የደም መፍሰስ ወይም bleeding አጋጥሞኛል:: ፈርቻለሁ በጣም::",
    "በጥልቀት ስተነፍስ ደረቴን ያመኛል:: It's like stabbing pain. በጣም ይወጋኛል::",
    "ለሁለት ቀናት ጥቅምጥ ወይም diarrhea እያጋጠመኝ ነው:: እና የማዞር ስሜት አለብኝ:: It's like feel dizzy.",
    "Pregnant ነኝ:: ወይም ማለቴ ነፍሰ ጡር ነኝ:: እናማ በእግሮቼ እና በእጆቼ ላይ swelling ወይም እብጠት አለብኝ::",
    "Confused ሆኛለሁ:: በጣም ተጋብቻለሁ:: እና በትክክል መቆም አልቻልኩም::",
]
for i, text in enumerate(AMHARIC_TEXTS, start=1):
    TEAM_ROWS.append({
        "audio_path": f"benchmark/audio/am_{i:02d}.mp3",
        "language": "am",
        "ground_truth": text,
    })

with open("samples.csv", "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["audio_path", "language", "ground_truth"])
    writer.writerows(TEAM_ROWS)

print(f"Appended {len(TEAM_ROWS)} team rows to samples.csv.")