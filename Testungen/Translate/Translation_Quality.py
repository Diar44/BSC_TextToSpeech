import jiwer

# ── Dateipfade ──────────────────────────────────────────────────────────────
GROUND_TRUTH = "GroundTruthTranslate.txt"

SYSTEMS = {
    "Speechmatics": "SpeechmaticsTranslate.txt",
    "Starteve":     "StarteveTranslate.txt",
}

# ── Normalisierungs-Transforms ───────────────────────────────────────────────
word_transforms = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfWords(),
])

char_transforms = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfChars(),
])

# ── Ground Truth laden ───────────────────────────────────────────────────────
with open(GROUND_TRUTH, encoding="utf-8") as f:
    reference = f.read().strip()

# ── Auswertung ───────────────────────────────────────────────────────────────
print(f"\n{'System':<15} {'WER':>8} {'MER':>8} {'WIL':>8} {'WIP':>8} {'CER':>8}")
print("-" * 60)

results = {}
for name, path in SYSTEMS.items():
    with open(path, encoding="utf-8") as f:
        hypothesis = f.read().strip()

    # Word-level Metriken
    word_out = jiwer.process_words(
        reference, hypothesis,
        reference_transform=word_transforms,
        hypothesis_transform=word_transforms,
    )

    # Character-level Metrik (CER)
    char_out = jiwer.process_characters(
        reference, hypothesis,
        reference_transform=char_transforms,
        hypothesis_transform=char_transforms,
    )

    results[name] = {
        "wer": word_out.wer,
        "mer": word_out.mer,
        "wil": word_out.wil,
        "wip": word_out.wip,
        "cer": char_out.cer,
        "hits":          word_out.hits,
        "substitutions": word_out.substitutions,
        "deletions":     word_out.deletions,
        "insertions":    word_out.insertions,
    }

    print(f"{name:<15} {word_out.wer:>8.4f} {word_out.mer:>8.4f} "
          f"{word_out.wil:>8.4f} {word_out.wip:>8.4f} {char_out.cer:>8.4f}")

# ── Detail-Tabelle ───────────────────────────────────────────────────────────
print(f"\nDetails  (H=Hits, S=Substitutionen, D=Deletionen, I=Insertionen):")
print(f"{'System':<15} {'H':>8} {'S':>8} {'D':>8} {'I':>8}")
print("-" * 50)
for name, r in results.items():
    print(f"{name:<15} {r['hits']:>8} {r['substitutions']:>8} "
          f"{r['deletions']:>8} {r['insertions']:>8}")

# ── Ranking nach WER ─────────────────────────────────────────────────────────
print("\nRanking nach WER (niedrigster Wert = beste Genauigkeit):")
ranked = sorted(results.items(), key=lambda x: x[1]["wer"])
for i, (name, r) in enumerate(ranked, 1):
    print(f"  {i}. {name:<15}  WER={r['wer']:.4f}  CER={r['cer']:.4f}")