"""
Benchmark script: compares Sahara vs Whisper vs AssemblyAI vs Hugging Face MMS
across audio samples with known ground-truth transcripts, AND measures
downstream triage accuracy per engine — does the transcript quality
actually change whether the agent correctly identifies urgency and
danger signs? This is separate from raw WER/CER.

Usage: python -m benchmark.run_benchmark
Expects a CSV at benchmark/samples.csv with columns:
  audio_path, language, ground_truth, expected_urgency, expected_danger_signs
  (language should be one of: en, am, yo, pcm, ak)
  (expected_danger_signs is semicolon-separated, empty if none)
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


def evaluate_downstream_task(transcript: str, language_code: str, expected_urgency: str, expected_signs: set) -> dict:
    """Runs a transcript through the real triage pipeline and checks
    whether it reaches the correct urgency and danger signs — this
    measures whether transcription errors actually break the agentic
    task, not just whether words are misspelled."""
    lang_name = get_full_language_name(language_code)
    try:
        fields = extract_fields(
            transcript=transcript,
            existing_fields={},
            language=lang_name,
            client=groq_client
        )
        assessment = assess_urgency(fields, language=lang_name)
        actual_signs = {s["sign"] for s in assessment["matched_signs"]}

        return {
            "downstream_urgency_correct": assessment["urgency"] == expected_urgency,
            "downstream_signs_correct": actual_signs == expected_signs,
            "actual_urgency": assessment["urgency"],
            "actual_signs": ";".join(sorted(actual_signs)) or "none"
        }
    except Exception as e:
        return {
            "downstream_urgency_correct": False,
            "downstream_signs_correct": False,
            "actual_urgency": f"ERROR: {e}",
            "actual_signs": "error"
        }


def run():
    results = []
    with open("benchmark/samples.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audio_path = row["audio_path"]
            language = row["language"]
            ground_truth = row["ground_truth"]
            expected_urgency = row.get("expected_urgency", "").strip()
            expected_signs = set(
                s.strip() for s in row.get("expected_danger_signs", "").split(";") if s.strip()
            )

            print(f"Testing {audio_path} ({language})...")

            engines = [
                ("sahara", lambda: transcribe_with_sahara(audio_path, language_code=language)),
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

                    downstream = {}
                    if expected_urgency:
                        downstream = evaluate_downstream_task(
                            result["text"], language, expected_urgency, expected_signs
                        )

                    results.append({
                        "audio": audio_path,
                        "language": language,
                        "engine": engine_name,
                        "transcript": result["text"],
                        "wer": round(wer, 3),
                        "latency_sec": round(latency, 2),
                        "downstream_urgency_correct": downstream.get("downstream_urgency_correct", ""),
                        "downstream_signs_correct": downstream.get("downstream_signs_correct", ""),
                    })
                    print(f"  {engine_name}: WER={round(wer,3)} latency={round(latency,2)}s "
                          f"downstream_urgency_ok={downstream.get('downstream_urgency_correct','n/a')}")
                except Exception as e:
                    print(f"  {engine_name}: FAILED — {e}")
                    results.append({
                        "audio": audio_path,
                        "language": language,
                        "engine": engine_name,
                        "transcript": f"ERROR: {e}",
                        "wer": None,
                        "latency_sec": None,
                        "downstream_urgency_correct": "",
                        "downstream_signs_correct": "",
                    })

    fieldnames = ["audio", "language", "engine", "transcript", "wer", "latency_sec",
                  "downstream_urgency_correct", "downstream_signs_correct"]
    with open("benchmark/results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\nDone. Results written to benchmark/results.csv")


if __name__ == "__main__":
    run()