"""
ai-pipeline/benchmark/fill_missing_downstream.py

One-time patch script: finds rows in results.csv where reference_urgency
or actual_urgency contain a Groq rate-limit error (not a real triage
result) and re-runs ONLY the downstream classification step using the
transcript/ground_truth that's already present. Does not re-call any
STT engine.

Run from ai-pipeline/ folder: python -m benchmark.fill_missing_downstream
"""
import csv
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark.run_benchmark import get_downstream_result

ground_truth_map = {}
with open("benchmark/samples.csv") as f:
    for row in csv.DictReader(f):
        ground_truth_map[row["audio_path"]] = row["ground_truth"]

rows = []
with open("benchmark/results.csv") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

def is_corrupted(value):
    return value.startswith("ERROR") if value else False

patched = 0
for row in rows:
    needs_fix = is_corrupted(row["reference_urgency"]) or is_corrupted(row["actual_urgency"])
    if not needs_fix:
        continue
    if row["transcript"].startswith("ERROR"):
        continue  # transcript itself failed, nothing to classify

    audio_path = row["audio"]
    language = row["language"]
    ground_truth = ground_truth_map.get(audio_path, "")

    print(f"Fixing downstream classification for {audio_path} ({row['engine']})...")
    try:
        reference = get_downstream_result(ground_truth, language)
        time.sleep(1.5)  # stay well under Groq's rate limit
        actual = get_downstream_result(row["transcript"], language)
        time.sleep(1.5)

        downstream_match = (
            actual["urgency"] == reference["urgency"]
            and actual["signs"] == reference["signs"]
        )

        row["reference_urgency"] = reference["urgency"]
        row["actual_urgency"] = actual["urgency"]
        row["downstream_match"] = downstream_match
        patched += 1
        print(f"  FIXED: reference={reference['urgency']} actual={actual['urgency']} match={downstream_match}")
    except Exception as e:
        print(f"  STILL FAILING: {e}")

with open("benchmark/results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nDone. Patched {patched} rows in results.csv")