"""
FastAPI server for Weha Health AI Pipeline — Sahara CodeSwitch Africa Challenge build.
Node.js backend calls these endpoints.

Run: uvicorn main:app --reload --port 8000
     (from inside ai-pipeline/ folder)
"""
import os
import shutil
import time
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import requests

from triage.rules import assess_urgency
from triage.extract import extract_fields, generate_clarifying_question, REQUIRED_FIELDS
from triage.escalate import send_whatsapp_alert
from triage.facility import find_nearest_facility

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "am": "Amharic",
    "yo": "Yoruba",
    "pcm": "Nigerian Pidgin",
    "ak": "Akan",
}

SAHARA_API_URL = "https://infer.voice.intron.io/file/v1/upload/sync"
SAHARA_API_KEY = os.environ.get("SAHARA_API_KEY")
USE_SAHARA = bool(SAHARA_API_KEY)

ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

# Hugging Face MMS uses ISO 639-3 codes, different from our app's codes.
# MMS has no dedicated Nigerian Pidgin adapter — expected, reportable gap.
MMS_LANG_MAP = {"en": "eng", "am": "amh", "yo": "yor", "pcm": None, "ak": "aka"}

app = FastAPI(
    title="Weha Health — AI Pipeline",
    description="Multilingual voice health triage agent, built for the Sahara CodeSwitch Africa Challenge",
    version="0.6.0"
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
    session_id: str = "unknown"
    lat: Optional[float] = None
    lng: Optional[float] = None


def get_full_language_name(lang_code: str) -> str:
    return SUPPORTED_LANGUAGES.get(lang_code.lower(), "English")


def map_to_whisper_lang(lang_code: str) -> str:
    whisper_lang_map = {"en": "en", "am": "am", "yo": "yo", "pcm": "en", "ak": "en"}
    return whisper_lang_map.get(lang_code.lower(), "en")


def transcribe_with_sahara(file_path: str, language_code: str = "en") -> dict:
    """Send audio to Sahara's File Upload Sync API. Files must be <=120s."""
    with open(file_path, "rb") as audio_file:
        response = requests.post(
            SAHARA_API_URL,
            headers={"Authorization": f"Bearer {SAHARA_API_KEY}"},
            files={"audio_file_blob": audio_file},
            data={
                "audio_file_name": os.path.basename(file_path),
                "use_language_asr_input": language_code,
            },
            timeout=125
        )

    if response.status_code == 503:
        raise HTTPException(
            status_code=504,
            detail="Sahara transcription timed out synchronously. File may need async polling (not implemented)."
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Sahara API error: {response.text}")

    result = response.json()
    data = result.get("data", {})
    return {
        "text": data.get("audio_transcript", ""),
        "detected_language": language_code,
        "status": "success",
        "engine": "sahara",
        "duration_seconds": data.get("processed_audio_duration_in_seconds")
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


def transcribe_with_assemblyai(file_path: str, language: str = "en") -> dict:
    """
    AssemblyAI has no native support for Yoruba, Akan, Nigerian Pidgin, or
    Amharic. We use automatic language detection rather than forcing an
    unsupported code — expect English-biased or degraded output for our
    four African languages. That gap is itself a valid benchmark finding.
    """
    if not ASSEMBLYAI_API_KEY:
        raise HTTPException(status_code=503, detail="ASSEMBLYAI_API_KEY not configured.")

    headers = {"authorization": ASSEMBLYAI_API_KEY}

    with open(file_path, "rb") as f:
        upload_response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=f,
            timeout=60
        )
    if upload_response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"AssemblyAI upload error: {upload_response.text}")

    audio_url = upload_response.json()["upload_url"]

    transcript_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        json={"audio_url": audio_url, "language_detection": True},
        headers=headers,
        timeout=30
    )
    if transcript_response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"AssemblyAI transcript error: {transcript_response.text}")

    transcript_id = transcript_response.json()["id"]
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    for _ in range(30):
        polling_response = requests.get(polling_endpoint, headers=headers, timeout=30)
        result = polling_response.json()
        if result["status"] == "completed":
            return {
                "text": result.get("text") or "",
                "detected_language": result.get("language_code", "unknown"),
                "status": "success",
                "engine": "assemblyai"
            }
        if result["status"] == "error":
            raise HTTPException(status_code=502, detail=f"AssemblyAI transcription failed: {result.get('error')}")
        time.sleep(2)

    raise HTTPException(status_code=504, detail="AssemblyAI transcription timed out.")


def transcribe_with_huggingface(file_path: str, language: str = "en") -> dict:
    """Facebook MMS-1b-all via Hugging Face Inference API."""
    if not HF_API_KEY:
        raise HTTPException(status_code=503, detail="HF_API_KEY not configured.")

    mms_lang = MMS_LANG_MAP.get(language)
    if mms_lang is None:
        raise HTTPException(
            status_code=422,
            detail=f"Hugging Face MMS has no language adapter for '{language}' — documented model gap, not a bug."
        )

    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    response = requests.post(
        "https://api-inference.huggingface.co/models/facebook/mms-1b-all",
        headers={"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "audio/flac"},
        params={"target_lang": mms_lang},
        data=audio_bytes,
        timeout=60
    )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Hugging Face MMS error: {response.text}")

    data = response.json()
    return {
        "text": data.get("text", ""),
        "detected_language": language,
        "status": "success",
        "engine": "huggingface_mms"
    }


@app.get("/")
def home():
    return {
        "message": "Weha Health AI Pipeline running",
        "version": "0.6.0",
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
            return transcribe_with_sahara(temp_path, language_code=language)
        elif chosen == "whisper":
            return transcribe_with_whisper(temp_path, language)
        elif chosen == "assemblyai":
            return transcribe_with_assemblyai(temp_path, language)
        elif chosen == "huggingface":
            return transcribe_with_huggingface(temp_path, language)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model '{chosen}'")

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

        alert_sent = False
        facility = None

        if assessment["urgency"] == "urgent":
            alert_sent = send_whatsapp_alert(
                session_id=data.session_id,
                language=lang_name,
                fields=updated_fields,
                urgency=assessment["urgency"],
                matched_signs=assessment["matched_signs"],
                guidance=assessment["guidance"]
            )
            if data.lat is not None and data.lng is not None:
                facility = find_nearest_facility(data.lat, data.lng)

        return {
            "status": "complete",
            "fields": updated_fields,
            "urgency": assessment["urgency"],
            "matched_signs": assessment["matched_signs"],
            "guidance": assessment["guidance"],
            "alert_sent": alert_sent,
            "nearest_facility": facility
        }

    except Exception as e:
        print(f"Error in /intake/process: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing intake.")