"""
rag/query.py - Weha Health RAG Query Engine
Uses Gemini embeddings for retrieval + Groq openai/gpt-oss-120b for generation
"""
import os
import re
import psycopg2
from google import genai
from google.genai import types
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

GROQ_CHAT_MODEL = "openai/gpt-oss-120b"

# Matches Sahara v2.5's code-switch pairs used in this competition build
SUPPORTED_LANGUAGES = {
    "English", "Nigerian Pidgin", "Yoruba", "Akan", "Amharic"
}

LANGUAGE_ENFORCEMENT = {
    "English": "Respond entirely in English.",
    "Nigerian Pidgin": "You must respond ENTIRELY in Nigerian Pidgin English — every sentence, no English-only sentences mixed in, no switching back to standard English. Use natural Pidgin phrasing throughout (e.g. 'Your body dey hot' not 'Your body is hot').",
    "Yoruba": "You must respond ENTIRELY in Yoruba — every sentence, no English-only sentences mixed in, no switching back to standard English. If a medical term has no natural Yoruba equivalent, keep that single term in English but write the surrounding explanation in Yoruba.",
    "Akan": "You must respond ENTIRELY in Akan (Twi) — every sentence, no English-only sentences mixed in. If a medical term has no natural Akan equivalent, keep that single term in English but write the surrounding explanation in Akan.",
    "Amharic": "መልስህን ሙሉ በሙሉ በአማርኛ ስጥ — እያንዳንዱ ዓረፍተ ነገር በአማርኛ መሆን አለበት፣ ከእንግሊዝኛ ጋር አትቀላቅል።"
}

FALLBACK_MESSAGES = {
    "English": "I don't have enough reliable information to answer that confidently. Please consult a qualified healthcare provider or visit your nearest health facility.",
    "Nigerian Pidgin": "I no get enough correct information to answer dat question well well. Abeg go see correct doctor or visit di health center near you.",
    "Yoruba": "Mi ò ní àlàyé tó pé láti dá̀hùn ìbéèrè yìí dáadáa. Jọ̀wọ́ lọ bá dókítà tó gbẹ́kẹ̀lé sọ̀rọ̀ tàbí lọ sí ilé ìwòsàn tó súnmọ́ ọ.",
    "Akan": "Menni nsɛm a edi mu pii a mede bɛyi saa asɛmmisa yi ano yiye. Yɛsrɛ wo, kɔ hwɛ oduruyɛfo anaa kɔ ayaresabea a ɛbɛn wo.",
    "Amharic": "ለዚህ ጥያቄ በትክክል ለመመለስ በቂ መረጃ የለኝም። እባክዎ ብቁ የጤና ባለሙያ ያማክሩ ወይም በአቅራቢያዎ ወዳለው የጤና ተቋም ይሂዱ።"
}


def strip_markdown(text: str) -> str:
    if not text:
        return text
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\*\-]\s+', '', text, flags=re.MULTILINE)
    return text.strip()


def is_degenerate(text: str) -> bool:
    if not text or len(text) < 10:
        return False

    for frag_len in (3, 4, 5, 6):
        if len(text) < frag_len * 8:
            continue
        for start in range(0, min(len(text) - frag_len * 6, 50)):
            fragment = text[start:start + frag_len]
            if not fragment.strip():
                continue
            if fragment * 6 in text:
                return True

    words = text.split()
    if len(words) < 8:
        return False

    unique_words = set(words)
    if len(unique_words) / len(words) < 0.25:
        return True

    for phrase_len in (3, 4, 5):
        if len(words) < phrase_len * 4:
            continue
        phrases = [' '.join(words[i:i + phrase_len]) for i in range(len(words) - phrase_len)]
        if phrases:
            most_common_count = max(phrases.count(p) for p in set(phrases))
            if most_common_count >= 5:
                return True

    sentences = [s.strip() for s in re.split(r'[.?።]', text) if s.strip()]
    if len(sentences) > 2:
        if len(set(sentences)) / len(sentences) < 0.65:
            return True

    longest_word = max((len(w) for w in words), default=0)
    if longest_word > 80:
        return True

    return False


def detect_language_and_translate(text: str) -> dict:
    """Detect language and translate to English using Groq."""
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are a medical language detector and translator.

TASK:
1. Detect the language of the input.
2. Translate it to English.

IMPORTANT MEDICAL TERMS:

AMHARIC: ወባ=malaria, ኮሌራ=cholera, ነቀርሳ=tuberculosis, ትኩሳት=fever, ተቅማጥ=diarrhea, የራስ ህመም=headache
YORUBA: ibà=fever/malaria, ìgbẹ́gbuuru=diarrhea, ọ̀gbẹ́ni orí=headache
PIDGIN: body dey hot=fever, running stomach=diarrhea, head dey pain me=headache
AKAN: atiridii=malaria, tirim=headache

Language codes: am=Amharic, yo=Yoruba, pcm=Nigerian Pidgin, ak=Akan, en=English

Respond EXACTLY in this format:
LANGUAGE_CODE: code
LANGUAGE_NAME: name
ENGLISH: translation"""
                },
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            max_tokens=150
        )
        content = response.choices[0].message.content.strip()
        result = {"language_code": "en", "language_name": "English", "english": text}
        for line in content.split("\n"):
            if line.startswith("LANGUAGE_CODE:"):
                result["language_code"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("LANGUAGE_NAME:"):
                result["language_name"] = line.split(":", 1)[1].strip()
            elif line.startswith("ENGLISH:"):
                result["english"] = line.split(":", 1)[1].strip()
        return result
    except Exception as e:
        print(f"Language detection failed: {e}")
        return {"language_code": "en", "language_name": "English", "english": text}


def get_query_embedding(text: str) -> list:
    result = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768
        )
    )
    vector = result.embeddings[0].values
    norm = sum(v * v for v in vector) ** 0.5
    normalized = [v / norm for v in vector] if norm > 0 else vector
    return normalized


def ask_rag(question: str, language: str = "English", history: list = []) -> dict:
    detection = detect_language_and_translate(question)
    language_code = detection["language_code"]
    language_name = detection["language_name"]
    search_query = detection["english"]

    response_language = language if language in SUPPORTED_LANGUAGES else language_name

    print(f"[Original]  {question}")
    print(f"[Detected]  {language_name} ({language_code})")
    print(f"[Search]    {search_query}")
    print(f"[Respond]   {response_language}")

    query_embedding = get_query_embedding(search_query)

    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("""
        SELECT text, source_name, 1 - (embedding <=> %s::vector) AS score
        FROM knowledge_base
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """, (str(query_embedding), str(query_embedding)))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows or rows[0][2] < 0.30:
        return {
            "answer": FALLBACK_MESSAGES.get(response_language, FALLBACK_MESSAGES["English"]),
            "score": 0.0,
            "sources": []
        }

    context = "\n\n".join([f"[Source: {row[1]}]\n{row[0]}" for row in rows])
    sources = list(set([row[1] for row in rows]))
    best_score = float(rows[0][2])

    history_text = ""
    if history:
        history_lines = []
        for msg in history[-6:]:
            role = "Assistant" if msg.get("sender") == "bot" else "User"
            history_lines.append(f"{role}: {msg.get('text', '')}")
        history_text = "\n".join(history_lines)

    language_rule = LANGUAGE_ENFORCEMENT.get(response_language, LANGUAGE_ENFORCEMENT["English"])

    system_instruction = (
        f"You are Weha Health, a warm and knowledgeable community health companion "
        f"serving users across Nigeria, Ghana, and Ethiopia.\n\n"

        f"=== LANGUAGE REQUIREMENT — HIGHEST PRIORITY ===\n"
        f"The user's selected language is: {response_language}.\n"
        f"{language_rule}\n"
        f"The knowledge base context is in English. Translate and explain everything in {response_language}.\n"
        f"Do NOT respond in English unless the selected language is English.\n"
        f"Never switch languages mid-response.\n"
        f"Never repeat the same sentence twice.\n"
        f"=================================================\n\n"

        f"=== FORMATTING ===\n"
        f"Write in plain conversational text only. No markdown — no asterisks, no # headers, "
        f"no bullet point markers. If listing items, use natural sentences or simple numbered "
        f"lines like '1. ', '2. ' without symbols.\n"
        f"=================================================\n\n"

        f"=== TERMINOLOGY ANCHORS ===\n"
        f"ወባ = malaria | ነቀርሳ = tuberculosis | ኮሌራ = cholera | ትኩሳት = fever | ተቅማጥ = diarrhea\n"
        f"ibà = fever/malaria | ìgbẹ́gbuuru = diarrhea\n"
        f"atiridii = malaria (Akan)\n"
        f"=================================================\n\n"

        f"=== BEHAVIOR ===\n"
        f"- Acknowledge what the person said before answering so they feel heard.\n"
        f"- Ask clarifying questions when a concern is vague.\n"
        f"- Keep responses conversational and human, not clinical bullet lists.\n"
        f"- Write in plain, complete sentences. Do NOT use dashes or hyphens "
        f"(-, –, —) to add an aside or join two clauses within a sentence — "
        f"use a comma, a period, or a separate sentence instead.\n"
        f"- Do NOT use emojis anywhere in your response.\n"
        f"- When a condition appears differently on darker skin (e.g. eczema as dark brown or "
        f"grey patches rather than red), mention this — many users have been misdiagnosed.\n"
        f"- If symptoms suggest an emergency (fever with stiff neck, convulsions, heavy bleeding, "
        f"difficulty breathing, altered consciousness), say so clearly and urge immediate care.\n"
        f"- Never diagnose. Never prescribe medications by name without noting a provider must confirm.\n"
        f"- Ground every factual claim in the context below. If context doesn't cover something, "
        f"say so honestly rather than guessing.\n"
        f"- End with a helpful next step or gentle follow-up question.\n\n"

        + (f"=== CONVERSATION HISTORY ===\n{history_text}\n\n" if history_text else "")
        + f"=== CONTEXT FROM KNOWLEDGE BASE ===\n{context}\n\n"

        f"=== FINAL REMINDER ===\n"
        f"{language_rule}\n"
        f"No markdown. No asterisks. Plain conversational text only.\n"
        f"Give a complete response — do not cut off mid-sentence."
    )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": (
                    f"{question}\n\n"
                    f"(English meaning: {search_query}. Respond entirely in {response_language}.)"
                )}
            ],
            temperature=0.3,
            max_tokens=1024
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq generation error] {e}")
        return {
            "answer": FALLBACK_MESSAGES.get(response_language, FALLBACK_MESSAGES["English"]),
            "score": best_score,
            "sources": sources
        }

    if is_degenerate(answer):
        print(f"Degenerate output detected for language={response_language}")
        return {
            "answer": FALLBACK_MESSAGES.get(response_language, FALLBACK_MESSAGES["English"]),
            "score": round(best_score, 4),
            "sources": sources
        }

    answer = strip_markdown(answer)

    if is_degenerate(answer):
        answer = FALLBACK_MESSAGES.get(response_language, FALLBACK_MESSAGES["English"])

    print(f"[Score]   {round(best_score, 4)}")
    print(f"[Sources] {sources}")

    return {
        "answer": answer,
        "score": round(best_score, 4),
        "sources": sources
    }