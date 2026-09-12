"""
ai-pipeline/benchmark/fill_missing_hf.py

One-time patch script: re-runs ONLY the huggingface_mms rows that
failed in results.csv (due to the old api-inference.huggingface.co
endpoint being retired), now that transcribe_with_huggingface points
to the new router.huggingface.co endpoint. Leaves all other rows
(sahara, whisper, assemblyai) untouched.

Run from ai-pipeline/ folder: python -m benchmark.fill_missing_hf
"""
import csv
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from api.main import transcribe_with_huggingface, get_full_language_name
from triage.extract import extract_fields
from triage.rules import assess_urgency
from benchmark.run_benchmark import word_error_rate, get_downstream_result

groq_client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Load samples.csv to get ground_truth per audio_path (results.csv
# doesn't store ground_truth directly).
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
    if row["engine"] != "huggingface_mms":
        continue
    if not row["transcript"].startswith("ERROR"):
        continue  # already succeeded, leave it

    audio_path = row["audio"]
    language = row["language"]
    ground_truth = ground_truth_map.get(audio_path, "")

    print(f"Retrying {audio_path} ({language})...")
    try:
        start = time.time()
        result = transcribe_with_huggingface(audio_path, language)
        latency = time.time() - start
        wer = word_error_rate(ground_truth, result["text"])

        reference = get_downstream_result(ground_truth, language)
        actual = get_downstream_result(result["text"], language)
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

print(f"\nDone. Patched {patched} huggingface_mms rows in results.csv")