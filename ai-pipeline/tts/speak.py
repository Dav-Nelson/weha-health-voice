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


# In-memory cache: avoids re-hitting Google/HF for text we've already
# synthesized this instance's lifetime (resets on Render cold start,
# but cuts most repeat traffic during an active demo/testing session).
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


def _try_mms_tts(text: str, language: str, max_retries: int = 2) -> str:
    """Attempts native TTS via Meta's MMS models on HF Inference API.
    Retries on 429 (rate limit) with backoff; returns None on any
    other failure so the caller can fall back to gTTS."""
    model = MMS_TTS_MODELS.get(language.lower())
    if not model or not HF_API_KEY:
        return None

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
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
    """English voice only — confirmed via production logs that gTTS
    does not actually accept 'yo' or 'tw' language codes despite
    earlier documentation suggesting otherwise. Used as a fallback for
    Pidgin and for any language when MMS-TTS is unavailable. Retries
    on rate-limit errors from Google's unofficial TTS endpoint, which
    frequently throttles shared/datacenter IPs like Render's."""
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
    cache_key = (language.lower(), text)

    cached = _cache_get(cache_key)
    if cached:
        print(f"[tts] cache hit for language={language}")
        return cached

    result = None
    if language.lower() in MMS_TTS_MODELS:
        result = _try_mms_tts(text, language)
        if not result:
            print(f"[tts] Falling back to English voice for '{language}' — MMS-TTS unavailable this request.")

    if not result:
        result = _gtts_fallback(text)

    if result:
        _cache_set(cache_key, result)

    return result