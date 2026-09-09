Weha Health — Code-Switching Speech Benchmark Report

## Methodology
- N audio samples per language (Pidgin, Yoruba, Akan, Amharic, English)
- Ground-truth transcripts: human-verified, bilingual annotator [or team-verified]
- Metric: Word Error Rate (WER) + latency (seconds)
- Models: Sahara v2.5, Whisper-large-v3 (via Groq), AssemblyAI, Hugging Face MMS-1b-all

## Results by language

| Language | Sahara WER | Whisper WER | AssemblyAI WER | MMS WER | Fastest engine |
|----------|-----------|--------------|------------------|---------|-----------------|
| Pidgin   |           |              |                  | N/A (no adapter) | |
| Yoruba   |           |              |                  |         | |
| Akan     |           |              |                  |         | |
| Amharic  |           |              |                  |         | |
| English  |           |              |                  |         | |

## Qualitative findings
- AssemblyAI: no native language support for our 4 African languages; relies on auto-detection, expect English-biased output.
- Hugging Face MMS: no Nigerian Pidgin adapter — documented model gap.
- [Add: where Sahara specifically outperforms on code-switched mid-sentence transitions, with example transcript excerpts]

## Conclusion
[Which engine you're shipping with in production and why — likely Sahara given it's purpose-built for this exact code-switching problem]