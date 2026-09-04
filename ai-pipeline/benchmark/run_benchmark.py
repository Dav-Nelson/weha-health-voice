"""
Benchmark script: compares Sahara vs Whisper vs [third model TBD]
across your audio samples with known ground-truth transcripts.

Usage: python -m benchmark.run_benchmark
Expects a CSV at benchmark/samples.csv with columns:
  audio_path, language, ground_truth
"""
import csv
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.main import transcribe_with_sahara, transcribe_with_whisper


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Simple WER using edit distance on words."""
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


def run():
    results = []
    with open("benchmark/samples.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audio_path = row["audio_path"]
            language = row["language"]
            ground_truth = row["ground_truth"]

            print(f"Testing {audio_path} ({language})...")

            for engine_name, engine_fn in [
                ("sahara", lambda: transcribe_with_sahara(audio_path, language_code=language)),
                ("whisper", lambda: transcribe_with_whisper(audio_path, language)),
            ]:
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
                except Exception as e:
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

    print("Done. Results written to benchmark/results.csv")


if __name__ == "__main__":
    run()