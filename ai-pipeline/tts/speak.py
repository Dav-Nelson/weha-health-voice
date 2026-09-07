import base64
import re
from io import BytesIO
from gtts import gTTS

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols, pictographs, extended-A
    "\U00002600-\U000027BF"  # misc symbols, dingbats
    "\U0001F1E6-\U0001F1FF"  # flags
    "\U00002190-\U000021FF"  # arrows
    "\U00002B00-\U00002BFF"  # misc symbols and arrows
    "\U0000FE0F"             # variation selector
    "]+",
    flags=re.UNICODE
)


def strip_emojis(text: str) -> str:
    """Removes emoji so gTTS never voices them — spoken emoji names
    (e.g. 'medical symbol') break conversational flow."""
    if not text:
        return text
    return _EMOJI_PATTERN.sub("", text).strip()


def text_to_speech(text: str, language: str = "en") -> str:
    """
    Converts localized response text into an in-memory MP3 stream,
    encoding it as a Base64 data URI string to bypass disk write limitations.
    Dynamically routes regional accents (TLDs) for localized language trust.
    """
    text = strip_emojis(text)

    gtts_lang_map = {
        "en": "en",
        "sw": "sw",
        "am": "am",
        "om": "om",
        "pcm": "en",
        "tw": "en"
    }

    gtts_tld_map = {
        "en": "com.ng",
        "pcm": "com.ng",
        "tw": "com.ng",
        "om": "co.za",
        "sw": "com",
        "am": "com"
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