import base64
import os
import re
from io import BytesIO
import requests
from gtts import gTTS

HF_API_KEY = os.environ.get("HF_API_KEY")

# Meta's MMS-TTS project has dedicated models for these languages.
# Confirmed available: Yoruba, Akan, Amharic. Nigerian Pidgin has no
# dedicated MMS-TTS checkpoint, so it stays on the English gTTS voice.
MMS_TTS_MODELS = {
    "yo": "facebook/mms-tts-yor",
    "ak": "facebook/mms-tts-aka",
    "am": "facebook/mms-tts-amh",
}

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE
)


def strip_emojis(text: str) -> str:
    if not text:
        return text
    return _EMOJI_PATTERN.sub("", text).strip()


def _try_mms_tts(text: str, language: str) -> str:
    """Attempts native TTS via Meta's MMS models on HF Inference API.
    Returns None on any failure so the caller can fall back to gTTS —
    the free serverless tier can have cold starts or rate limits."""
    model = MMS_TTS_MODELS.get(language.lower())
    if not model or not HF_API_KEY:
        return None
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": text},
            timeout=30
        )
        if response.status_code != 200:
            print(f"[tts] MMS-TTS ({model}) returned {response.status_code}: {response.text[:200]}")
            return None
        content_type = response.headers.get("content-type", "audio/flac")
        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        return f"data:{content_type};base64,{audio_base64}"
    except Exception as e:
        print(f"[tts] MMS-TTS request failed: {e}")
        return None


def _gtts_fallback(text: str) -> str:
    """English voice only — confirmed via production logs that gTTS
    does not actually accept 'yo' or 'tw' language codes despite
    earlier documentation suggesting otherwise. Used as a fallback for
    Pidgin and for any language when MMS-TTS is unavailable."""
    try:
        mp3_fp = BytesIO()
        tts = gTTS(text=text, lang="en", tld="com.ng")
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_base64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{audio_base64}"
    except Exception as e:
        print(f"[tts] gTTS fallback error: {str(e)}")
        return ""


def text_to_speech(text: str, language: str = "en") -> str:
    text = strip_emojis(text)

    if language.lower() in MMS_TTS_MODELS:
        mms_result = _try_mms_tts(text, language)
        if mms_result:
            return mms_result
        print(f"[tts] Falling back to English voice for '{language}' — MMS-TTS unavailable this request.")

    return _gtts_fallback(text)