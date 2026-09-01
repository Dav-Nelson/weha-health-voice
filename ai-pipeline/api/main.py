"""
FastAPI server for Weha Health AI Pipeline — Sahara CodeSwitch Africa Challenge build.
Node.js backend calls these endpoints.

Run: uvicorn main:app --reload --port 8000
     (from inside ai-pipeline/ folder)
"""
import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import requests

from triage.rules import assess_urgency
from triage.extract import extract_fields, generate_clarifying_question, REQUIRED_FIELDS

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Languages actively supported in THIS competition build
# (matches Sahara v2.5's code-switch pairs: Yoruba-English, Akan-English,
# Amharic-English, Nigerian Pidgin-English)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "am": "Amharic",
    "yo": "Yoruba",
    "pcm": "Nigerian Pidgin",
    "ak": "Akan",
}

SAHARA_API_URL = os.environ.get("SAHARA_API_URL", "https://api.intron.io/sahara/v2.5/transcribe")
SAHARA_API_KEY = os.environ.get("SAHARA_API_KEY")
USE_SAHARA = bool(SAHARA_API_KEY)

app = FastAPI(
    title="Weha Health — AI Pipeline",
    description="Multilingual voice health triage agent, built for the Sahara CodeSwitch Africa Challenge",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    language: str = "en"
    history: List[dict] = []


class SpeakRequest(BaseModel):
    text: str
    language: str = "en"


class IntakeRequest(BaseModel):
    transcript: str
    language: str = "en"
    existing_fields: dict = {}


def get_full_language_name(lang_code: str) -> str:
    return SUPPORTED_LANGUAGES.get(lang_code.lower(), "English")


def map_to_whisper_lang(lang_code: str) -> str:
    # Whisper has no dedicated code for Nigerian Pidgin or Akan/Twi,
    # so those route through English-mode transcription (same limitation
    # noted in the original HealthBridge Africa README).
    whisper_lang_map = {"en": "en", "am": "am", "yo": "yo", "pcm": "en", "ak": "en"}
    return whisper_lang_map.get(lang_code.lower(), "en")


def transcribe_with_sahara(file_path: str, language_pair: str) -> dict:
    with open(file_path, "rb") as audio_file:
        response = requests.post(
            SAHARA_API_URL,
            headers={"Authorization": f"Bearer {SAHARA_API_KEY}"},
            files={"file": audio_file},
            data={"language_pair": language_pair},
            timeout=45
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Sahara API error: {response.text}")
    result = response.json()
    return {
        "text": result.get("text", ""),
        "detected_language": result.get("detected_language", language_pair),
        "status": "success",
        "engine": "sahara"
    }


def transcribe_with_whisper(file_path: str, language: str) -> dict:
    target_whisper_code = map_to_whisper_lang(language)
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            language=target_whisper_code,
            response_format="verbose_json"
        )
    return {
        "text": transcription.text,
        "detected_language": transcription.language,
        "status": "success",
        "engine": "whisper"
    }


@app.get("/")
def home():
    return {
        "message": "Weha Health AI Pipeline running",
        "version": "0.3.0",
        "sahara_active": USE_SAHARA,
        "endpoints": ["/ask", "/transcribe", "/speak", "/intake/process"]
    }


@app.head("/")
def home_head():
    return {}


@app.post("/ask")
async def ask_question(data: QuestionRequest):
    from rag.query import ask_rag
    try:
        target_lang_name = get_full_language_name(data.language)
        result = ask_rag(data.question, language=target_lang_name, history=data.history)
        return {
            "question": data.question,
            "answer": result["answer"],
            "similarity_score": result["score"],
            "sources": result.get("sources", []),
            "language": data.language
        }
    except Exception as e:
        print(f"Error in /ask: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing your health query.")


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "en",
    model: str = "auto"
):
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chosen = model
        if chosen == "auto":
            chosen = "sahara" if USE_SAHARA else "whisper"

        if chosen == "sahara":
            if not USE_SAHARA:
                raise HTTPException(status_code=503, detail="SAHARA_API_KEY not yet configured.")
            return transcribe_with_sahara(temp_path, language_pair=f"{language}-en")

        return transcribe_with_whisper(temp_path, language)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/speak")
async def speak(data: SpeakRequest):
    from tts.speak import text_to_speech
    try:
        if not data.text:
            raise HTTPException(status_code=400, detail="Text payload parameter cannot be empty")
        audio_result = text_to_speech(data.text, data.language)
        if isinstance(audio_result, str) and audio_result.startswith("data:audio/"):
            raw_base64 = audio_result.split(",")[1] if "," in audio_result else audio_result
            return {"status": "success", "audio": raw_base64}
        raise HTTPException(status_code=500, detail="TTS engine did not return a valid audio payload.")
    except Exception as e:
        print(f"CRITICAL TTS /speak failure exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/intake/process")
async def process_intake(data: IntakeRequest):
    try:
        lang_name = get_full_language_name(data.language)

        updated_fields = extract_fields(
            transcript=data.transcript,
            existing_fields=data.existing_fields,
            language=lang_name,
            client=client
        )

        missing = [f for f in REQUIRED_FIELDS if not updated_fields.get(f)]

        if missing:
            question = generate_clarifying_question(
                missing_field=missing[0],
                fields_so_far=updated_fields,
                language=lang_name,
                client=client
            )
            return {
                "status": "need_more_info",
                "fields": updated_fields,
                "next_question": question
            }

        assessment = assess_urgency(updated_fields)

        return {
            "status": "complete",
            "fields": updated_fields,
            "urgency": assessment["urgency"],
            "matched_signs": assessment["matched_signs"],
            "guidance": assessment["guidance"]
        }

    except Exception as e:
        print(f"Error in /intake/process: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing intake.")