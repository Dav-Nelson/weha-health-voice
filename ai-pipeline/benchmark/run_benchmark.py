"""
ai-pipeline/benchmark/run_benchmark.py

Compares Sahara vs Whisper vs AssemblyAI vs Hugging Face MMS across
code-switched audio samples with human-verified ground-truth transcripts.
Also measures downstream triage accuracy: for each sample, we compute
a "reference" triage outcome by running the verified ground-truth
transcript through our own extract_fields/assess_urgency pipeline once,
then check whether each engine's actual transcript reaches the same
outcome. No manual expected-urgency labeling required — the ground
truth transcript IS the label.

Usage: python -m benchmark.run_benchmark
Expects benchmark/samples.csv with columns: audio_path, language, ground_truth
(language should be one of: en, am, yo, pcm, ak)
"""
import csv
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from api.main import (
    transcribe_with_sahara,
    transcribe_with_whisper,
    transcribe_with_assemblyai,
    transcribe_with_huggingface,
    get_full_language_name,
)
from triage.extract import extract_fields
from triage.rules import assess_urgency

groq_client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


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


def transcribe_with_sahara_retrying(audio_path, language, max_retries=3):
    """Wraps transcribe_with_sahara with retry-on-429 handling, since
    Sahara's sync endpoint is rate-limited to 30 requests/minute and a
    benchmark run fires many calls back-to-back."""
    for attempt in range(max_retries + 1):
        try:
            return transcribe_with_sahara(audio_path, language_code=language)
        except Exception as e:
            if "429" in str(e) and attempt < max_retries:
                wait = 3 * (attempt + 1)
                print(f"  [sahara] rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
            raise


def get_downstream_result(transcript: str, language_code: str) -> dict:
    """Runs any transcript through the real triage pipeline."""
    lang_name = get_full_language_name(language_code)
    try:
        fields = extract_fields(transcript=transcript, existing_fields={}, language=lang_name, client=groq_client)
        assessment = assess_urgency(fields, language=lang_name)
        return {
            "urgency": assessment["urgency"],
            "signs": frozenset(s["sign"] for s in assessment["matched_signs"])
        }
    except Exception as e:
        return {"urgency": f"ERROR: {e}", "signs": frozenset()}


def run():
    results = []
    with open("benchmark/samples.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audio_path = row["audio_path"]
            language = row["language"]
            ground_truth = row["ground_truth"]

            print(f"Testing {audio_path} ({language})...")

            reference = get_downstream_result(ground_truth, language)

            # Small proactive delay to stay under Sahara's 30/min rate limit.
            time.sleep(2.1)

            engines = [
                ("sahara", lambda: transcribe_with_sahara_retrying(audio_path, language)),
                ("whisper", lambda: transcribe_with_whisper(audio_path, language)),
                ("assemblyai", lambda: transcribe_with_assemblyai(audio_path, language)),
                ("huggingface_mms", lambda: transcribe_with_huggingface(audio_path, language)),
            ]

            for engine_name, engine_fn in engines:
                try:
                    start = time.time()
                    result = engine_fn()
                    latency = time.time() - start
                    wer = word_error_rate(ground_truth, result["text"])

                    actual = get_downstream_result(result["text"], language)
                    downstream_match = (
                        actual["urgency"] == reference["urgency"]
                        and actual["signs"] == reference["signs"]
                    )

                    results.append({
                        "audio": audio_path,
                        "language": language,
                        "engine": engine_name,
                        "transcript": result["text"],
                        "wer": round(wer, 3),
                        "latency_sec": round(latency, 2),
                        "reference_urgency": reference["urgency"],
                        "actual_urgency": actual["urgency"],
                        "downstream_match": downstream_match,
                    })
                    print(f"  {engine_name}: WER={round(wer,3)} latency={round(latency,2)}s downstream_match={downstream_match}")
                except Exception as e:
                    print(f"  {engine_name}: FAILED — {e}")
                    results.append({
                        "audio": audio_path,
                        "language": language,
                        "engine": engine_name,
                        "transcript": f"ERROR: {e}",
                        "wer": None,
                        "latency_sec": None,
                        "reference_urgency": reference["urgency"],
                        "actual_urgency": "error",
                        "downstream_match": False,
                    })

    fieldnames = ["audio", "language", "engine", "transcript", "wer", "latency_sec",
                  "reference_urgency", "actual_urgency", "downstream_match"]
    with open("benchmark/results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\nDone. Results written to benchmark/results.csv")


if __name__ == "__main__":
    run()