"""
Benchmark script: compares Sahara vs Whisper vs Google STT vs Meta MMS
across audio samples with known ground-truth transcripts.

Usage: python -m benchmark.run_benchmark
Expects a CSV at benchmark/samples.csv with columns:
  audio_path, language, ground_truth
  (language should be one of: en, am, yo, pcm, ak)
"""
import csv
import time
import sys
import os
import base64
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.main import transcribe_with_sahara, transcribe_with_whisper

GOOGLE_API_KEY = os.environ.get("GOOGLE_STT_API_KEY")
HF_API_KEY = os.environ.get("HF_API_KEY")

# Google Cloud STT language codes for our 5 languages
GOOGLE_LANG_MAP = {
    "en": "en-US",
    "am": "am-ET",
    "yo": "yo-NG",
    "pcm": "en-NG",  # Google has no dedicated Pidgin code; closest fallback
    "ak": "ak-GH",   # may not be supported — flagged as a possible qualitative finding
}

# Meta MMS uses ISO 639-3 codes, different from our app's codes
MMS_LANG_MAP = {
    "en": "eng",
    "am": "amh",
    "yo": "yor",
    "pcm": None,  # MMS has no dedicated Nigerian Pidgin adapter — expected failure, worth reporting
    "ak": "aka",
}


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])

    return d[len(ref_words)][len(hyp_words)] / max(len(ref_words), 1)


def transcribe_with_google(file_path: str, language: str) -> dict:
    if not GOOGLE_API_KEY:
        raise Exception("GOOGLE_STT_API_KEY not set")

    lang_code = GOOGLE_LANG_MAP.get(language, "en-US")

    with open(file_path, "rb") as f:
        audio_content = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}",
        json={
            "config": {
                "encoding": "WEBM_OPUS",
                "sampleRateHertz": 48000,
                "languageCode": lang_code,
            },
            "audio": {"content": audio_content}
        },
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(f"Google STT error: {response.text}")

    data = response.json()
    results = data.get("results", [])
    if not results:
        return {"text": "", "engine": "google"}

    text = " ".join(r["alternatives"][0]["transcript"] for r in results)
    return {"text": text, "engine": "google"}


def transcribe_with_mms(file_path: str, language: str) -> dict:
    if not HF_API_KEY:
        raise Exception("HF_API_KEY not set")

    mms_lang = MMS_LANG_MAP.get(language)
    if mms_lang is None:
        raise Exception(f"MMS has no adapter for language '{language}' — not supported")

    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    response = requests.post(
        "https://api-inference.huggingface.co/models/facebook/mms-1b-all",
        headers={
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "audio/flac"
        },
        params={"target_lang": mms_lang},
        data=audio_bytes,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(f"MMS/HF error: {response.text}")

    data = response.json()
    return {"text": data.get("text", ""), "engine": "mms"}


def run():
    results = []
    with open("benchmark/samples.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audio_path = row["audio_path"]
            language = row["language"]
            ground_truth = row["ground_truth"]

            print(f"Testing {audio_path} ({language})...")

            engines = [
                ("sahara", lambda: transcribe_with_sahara(audio_path, language_code=language)),
                ("whisper", lambda: transcribe_with_whisper(audio_path, language)),
                ("google", lambda: transcribe_with_google(audio_path, language)),
                ("mms", lambda: transcribe_with_mms(audio_path, language)),
            ]

            for engine_name, engine_fn in engines:
                try:
                    start = time.time()
                    result = engine_fn()
                    latency = time.time() - start
                    wer = word_error_rate(ground_truth, result["text"])
                    results.append({
                        "audio": audio_path,
                        "language": language,
                        "engine": engine_name,
                        "transcript": result["text"],
                        "wer": round(wer, 3),
                        "latency_sec": round(latency, 2)
                    })
                    print(f"  {engine_name}: WER={round(wer,3)} latency={round(latency,2)}s")
                except Exception as e:
                    print(f"  {engine_name}: FAILED — {e}")
                    results.append({
                        "audio": audio_path,
                        "language": language,
                        "engine": engine_name,
                        "transcript": f"ERROR: {e}",
                        "wer": None,
                        "latency_sec": None
                    })

    with open("benchmark/results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["audio", "language", "engine", "transcript", "wer", "latency_sec"])
        writer.writeheader()
        writer.writerows(results)

    print("\nDone. Results written to benchmark/results.csv")


if __name__ == "__main__":
    run()