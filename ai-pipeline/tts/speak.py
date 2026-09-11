import base64
import os
import re
import time
import random
from collections import OrderedDict
from io import BytesIO
import requests
from gtts import gTTS

HF_API_KEY = os.environ.get("HF_API_KEY")
SAHARA_API_KEY = os.environ.get("SAHARA_API_KEY")

# --- Sahara TTS (primary for Pidgin/Yoruba/Amharic) ---
SAHARA_TTS_ENQUEUE_URL = "https://infer.voice.intron.io/tts/v1/enqueue"
SAHARA_TTS_STATUS_URL = "https://infer.voice.intron.io/tts/v1/status/{text_id}"

# Confirmed from Intron's docs: voice_accent matches the language name,
# lowercase. Akan is NOT in Sahara's supported-language list at all.
SAHARA_TTS_CONFIG = {
    "pcm": {"voice_language": "pcm", "voice_accent": "pidgin"},
    "yo": {"voice_language": "yo", "voice_accent": "yoruba"},
    "am": {"voice_language": "am", "voice_accent": "amharic"},
}

# --- MMS-TTS (fallback, and Akan's only native option) ---
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


# In-memory cache: avoids re-hitting any TTS provider for text we've
# already synthesized this instance's lifetime (resets on Render cold
# start, but cuts most repeat traffic during an active session).
_AUDIO_CACHE = OrderedDict()
_AUDIO_CACHE_MAX_ENTRIES = 100


def _cache_get(key):
    if key in _AUDIO_CACHE:
        _AUDIO_CACHE.move_to_end(key)
        return _AUDIO_CACHE[key]
    return None


def _cache_set(key, value):
    _AUDIO_CACHE[key] = value
    _AUDIO_CACHE.move_to_end(key)
    if len(_AUDIO_CACHE) > _AUDIO_CACHE_MAX_ENTRIES:
        _AUDIO_CACHE.popitem(last=False)


def _try_sahara_tts(text: str, language: str, voice_gender: str = "female") -> str:
    """Sahara's official TTS: enqueue -> poll status -> download audio_path.
    Bounded to roughly 15s of polling so a stuck job still leaves room
    for MMS-TTS/gTTS fallback within the 45s node gateway timeout."""
    config = SAHARA_TTS_CONFIG.get(language.lower())
    if not config or not SAHARA_API_KEY:
        return None

    try:
        enqueue_response = requests.post(
            SAHARA_TTS_ENQUEUE_URL,
            headers={"Authorization": f"Bearer {SAHARA_API_KEY}", "Content-Type": "application/json"},
            json={
                "text": text,
                "voice_language": config["voice_language"],
                "voice_accent": config["voice_accent"],
                "voice_gender": voice_gender,
                "output_audio_format": "wav",
            },
            timeout=15
        )

        if enqueue_response.status_code == 429:
            retry_after = int(enqueue_response.headers.get("Retry-After", 2))
            print(f"[tts] Sahara TTS enqueue rate limited, Retry-After={retry_after}s")
            return None
        if enqueue_response.status_code != 200:
            print(f"[tts] Sahara TTS enqueue failed {enqueue_response.status_code}: {enqueue_response.text[:200]}")
            return None

        text_id = enqueue_response.json().get("data", {}).get("text_id")
        if not text_id:
            print("[tts] Sahara TTS enqueue returned no text_id")
            return None

        status_url = SAHARA_TTS_STATUS_URL.format(text_id=text_id)
        max_attempts = 10
        poll_interval = 1.5

        for attempt in range(max_attempts):
            time.sleep(poll_interval)
            status_response = requests.get(
                status_url,
                headers={"Authorization": f"Bearer {SAHARA_API_KEY}"},
                timeout=10
            )

            if status_response.status_code == 429:
                retry_after = int(status_response.headers.get("Retry-After", 2))
                time.sleep(min(retry_after, 3))
                continue
            if status_response.status_code != 200:
                print(f"[tts] Sahara TTS status check failed {status_response.status_code}")
                return None

            status_data = status_response.json().get("data", {})
            processing_status = status_data.get("processing_status")

            if processing_status == "TTS_TEXT_AUDIO_GENERATED":
                audio_url = status_data.get("audio_path")
                if not audio_url:
                    print("[tts] Sahara TTS generated but no audio_path returned")
                    return None
                audio_response = requests.get(audio_url, timeout=20)
                if audio_response.status_code != 200:
                    print(f"[tts] Sahara TTS audio download failed {audio_response.status_code}")
                    return None
                audio_base64 = base64.b64encode(audio_response.content).decode("utf-8")
                print(f"[tts] Sahara TTS success for language={language}")
                return f"data:audio/wav;base64,{audio_base64}"

            if processing_status == "TTS_TEXT_AUDIO_PROCESSING_FAILED":
                print(f"[tts] Sahara TTS processing failed for language={language}")
                return None
            # else: queued / pending / processing -> keep polling

        print(f"[tts] Sahara TTS timed out waiting for audio (language={language})")
        return None

    except Exception as e:
        print(f"[tts] Sahara TTS request failed: {e}")
        return None


def _try_mms_tts(text: str, language: str, max_retries: int = 2) -> str:
    """Meta's MMS models via Hugging Face's router API. Retries on 429
    with backoff; returns None on any other failure so the caller can
    fall back further.

    Note: HF retired the old api-inference.huggingface.co host — it now
    returns hard errors telling callers to migrate. This uses the
    replacement router endpoint instead."""
    model = MMS_TTS_MODELS.get(language.lower())
    if not model or not HF_API_KEY:
        return None

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                f"https://router.huggingface.co/hf-inference/models/{model}",
                headers={"Authorization": f"Bearer {HF_API_KEY}"},
                json={"inputs": text},
                timeout=30
            )
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "audio/flac")
                audio_base64 = base64.b64encode(response.content).decode("utf-8")
                print(f"[tts] MMS-TTS success for language={language}")
                return f"data:{content_type};base64,{audio_base64}"

            if response.status_code == 429 and attempt < max_retries:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"[tts] MMS-TTS ({model}) rate limited, retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue

            print(f"[tts] MMS-TTS ({model}) returned {response.status_code}: {response.text[:200]}")
            return None
        except Exception as e:
            if attempt < max_retries:
                wait = 1 + attempt
                print(f"[tts] MMS-TTS request failed (attempt {attempt + 1}): {e} — retrying in {wait}s")
                time.sleep(wait)
                continue
            print(f"[tts] MMS-TTS request failed: {e}")
            return None
    return None


def _gtts_fallback(text: str, max_retries: int = 2) -> str:
    """English voice only — gTTS does not accept 'yo'/'tw' language
    codes. Last-resort fallback for all languages. Retries on
    rate-limit errors from Google's unofficial TTS endpoint."""
    for attempt in range(max_retries + 1):
        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=text, lang="en", tld="com.ng")
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_base64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
            return f"data:audio/mp3;base64,{audio_base64}"
        except Exception as e:
            err_text = str(e)
            is_rate_limit = "429" in err_text or "Too Many Requests" in err_text
            if is_rate_limit and attempt < max_retries:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"[tts] gTTS rate limited, retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
            print(f"[tts] gTTS fallback error: {err_text}")
            return ""
    return ""


def text_to_speech(text: str, language: str = "en") -> str:
    text = strip_emojis(text)
    lang = language.lower()
    cache_key = (lang, text)

    cached = _cache_get(cache_key)
    if cached:
        print(f"[tts] cache hit for language={language}")
        return cached

    result = None

    if lang in SAHARA_TTS_CONFIG:
        result = _try_sahara_tts(text, lang)
        if not result:
            print(f"[tts] Sahara TTS unavailable for '{lang}' this request, trying next option.")

    if not result and lang in MMS_TTS_MODELS:
        result = _try_mms_tts(text, lang)
        if not result:
            print(f"[tts] Falling back to English voice for '{lang}' — MMS-TTS unavailable this request.")

    if not result:
        result = _gtts_fallback(text)

    if result:
        _cache_set(cache_key, result)

    return result