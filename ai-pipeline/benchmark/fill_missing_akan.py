"""
ai-pipeline/benchmark/fill_missing_akan.py

One-time patch script: re-runs Akan rows across sahara/whisper/assemblyai
in results.csv that failed due to a filename mismatch (files were saved
as ak_1.mp3..ak_9.mp3 instead of ak_01.mp3..ak_09.mp3, now renamed).
Leaves all other rows untouched.

Run from ai-pipeline/ folder: python -m benchmark.fill_missing_akan
"""
import csv
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from api.main import (
    transcribe_with_sahara,
    transcribe_with_whisper,
    transcribe_with_assemblyai,
)
from benchmark.run_benchmark import (
    word_error_rate,
    get_downstream_result,
    transcribe_with_sahara_retrying,
)

ENGINE_FUNCS = {
    "sahara": lambda path, lang: transcribe_with_sahara_retrying(path, lang),
    "whisper": lambda path, lang: transcribe_with_whisper(path, lang),
    "assemblyai": lambda path, lang: transcribe_with_assemblyai(path, lang),
}

ground_truth_map = {}
with open("benchmark/samples.csv") as f:
    for row in csv.DictReader(f):
        ground_truth_map[row["audio_path"]] = row["ground_truth"]

rows = []
with open("benchmark/results.csv") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

patched = 0
for row in rows:
    if row["language"] != "ak":
        continue
    if row["engine"] not in ENGINE_FUNCS:
        continue
    if not row["transcript"].startswith("ERROR"):
        continue  # already succeeded, leave it

    audio_path = row["audio"]
    ground_truth = ground_truth_map.get(audio_path, "")

    print(f"Retrying {audio_path} ({row['engine']})...")
    try:
        start = time.time()
        result = ENGINE_FUNCS[row["engine"]](audio_path, "ak")
        latency = time.time() - start
        wer = word_error_rate(ground_truth, result["text"])

        reference = get_downstream_result(ground_truth, "ak")
        actual = get_downstream_result(result["text"], "ak")
        downstream_match = (
            actual["urgency"] == reference["urgency"]
            and actual["signs"] == reference["signs"]
        )

        row["transcript"] = result["text"]
        row["wer"] = round(wer, 3)
        row["latency_sec"] = round(latency, 2)
        row["reference_urgency"] = reference["urgency"]
        row["actual_urgency"] = actual["urgency"]
        row["downstream_match"] = downstream_match
        patched += 1
        print(f"  SUCCESS: WER={round(wer,3)}")
    except Exception as e:
        print(f"  STILL FAILING: {e}")
        row["transcript"] = f"ERROR: {e}"

with open("benchmark/results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nDone. Patched {patched} Akan rows in results.csv")