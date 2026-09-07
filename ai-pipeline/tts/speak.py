import base64
import re
from io import BytesIO
from gtts import gTTS

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


def text_to_speech(text: str, language: str = "en") -> str:
    """
    Converts localized response text into an in-memory MP3 stream,
    encoding it as a Base64 data URI string.

    Language codes match our app's ISO codes: en, pcm, yo, ak, am.
    gTTS has no dedicated Nigerian Pidgin voice, so pcm falls back to
    English (readable, since Pidgin is English-based). Yoruba and Akan
    (as "tw" — gTTS's code for Twi/Akan) both have native gTTS voices
    and should NOT fall back to English — that was the previous bug
    causing letter-by-letter mispronunciation on tonal/diacritic text.
    """
    text = strip_emojis(text)

    gtts_lang_map = {
        "en": "en",
        "pcm": "en",
        "yo": "yo",
        "ak": "tw",
        "am": "am",
    }

    gtts_tld_map = {
        "en": "com.ng",
        "pcm": "com.ng",
        "yo": "com.ng",
        "ak": "com.gh",
        "am": "com",
    }

    target_gtts_code = gtts_lang_map.get(language.lower(), "en")
    target_tld = gtts_tld_map.get(language.lower(), "com.ng")

    try:
        mp3_fp = BytesIO()
        tts = gTTS(text=text, lang=target_gtts_code, tld=target_tld)
        tts.write_to_fp(mp3_fp)

        mp3_fp.seek(0)
        audio_base64 = base64.b64encode(mp3_fp.read()).decode("utf-8")

        return f"data:audio/mp3;base64,{audio_base64}"
    except Exception as e:
        print(f"TTS Engine Error: {str(e)}")
        try:
            mp3_fp = BytesIO()
            fallback_tts = gTTS(text="An audio processing error occurred.", lang="en", tld="com.ng")
            fallback_tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_base64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
            return f"data:audio/mp3;base64,{audio_base64}"
        except Exception:
            return ""