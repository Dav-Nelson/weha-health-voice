import base64
import re
import unicodedata
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


def strip_diacritics(text: str) -> str:
    """
    Removes tone marks/diacritics (e.g. Yoruba ọ́, ẹ̀) before TTS only —
    the displayed chat text is untouched. Google's TTS engine sometimes
    can't parse words carrying these marks and falls back to spelling
    letters instead of speaking words. This trades tonal accuracy for
    actually being intelligible speech.
    """
    if not text:
        return text
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def text_to_speech(text: str, language: str = "en") -> str:
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

    # Diacritics only stripped for languages known to carry heavy tone
    # marks that have caused letter-spelling behavior in testing.
    if language.lower() in ("yo", "ak"):
        text = strip_diacritics(text)

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