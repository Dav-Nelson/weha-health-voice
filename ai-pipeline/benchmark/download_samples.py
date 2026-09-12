"""
One-time script: downloads sample code-switched clips from Intron's
AfriSwitch dataset and builds samples.csv for our benchmark.
Run once from the ai-pipeline/benchmark/ folder.
"""
import os
import csv
import io
import soundfile as sf
from datasets import load_dataset, Audio
from huggingface_hub import login

login(token=os.environ["HF_API_KEY"])

os.makedirs("audio", exist_ok=True)

# Confirmed config names from the AfriSwitch dataset card (all lowercase).
# Akan has no AfriSwitch config at all (14 languages, Akan not among them) —
# so it's intentionally excluded here, not guessed-and-skipped.
CANDIDATES = {
    "yo": ["yoruba"],
    "am": ["amharic"],
    "pcm": ["pidgin"],
}

SAMPLES_PER_LANGUAGE = 30
rows = []

for app_code, candidate_configs in CANDIDATES.items():
    loaded = None
    for config_name in candidate_configs:
        try:
            loaded = load_dataset("intronhealth/AfriSwitch", config_name, split="test")
            # Stop the datasets library from auto-decoding audio with torchcodec
            # (torchcodec needs a system FFmpeg lib that isn't installed in this
            # Replit environment). We decode manually with soundfile instead.
            loaded = loaded.cast_column("audio", Audio(decode=False))
            break
        except Exception as e:
            print(f"Failed to load config '{config_name}' for {app_code}: {e}")
    if loaded is None:
        print(f"COULD NOT LOAD any version for {app_code}. Skipping.")
        continue

    n = min(SAMPLES_PER_LANGUAGE, len(loaded))
    for i in range(n):
        example = loaded[i]
        audio_bytes = example["audio"]["bytes"]
        audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
        filename = f"{app_code}_{i:02d}.wav"
        filepath = os.path.join("audio", filename)
        sf.write(filepath, audio_array, sample_rate)
        transcript = example.get("transcription") or example.get("text") or example.get("sentence") or ""
        rows.append({"audio_path": f"benchmark/{filepath}", "language": app_code, "ground_truth": transcript})

with open("samples.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["audio_path", "language", "ground_truth"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. {len(rows)} samples in samples.csv")