"""
Speech-to-Text Evaluation Script
Vergleicht die Transkriptionsqualität verschiedener AI-Systeme
gegen einen manuell erstellten Ground Truth.

Metriken:
  - WER (Word Error Rate):       Anteil falscher Wörter
  - MER (Match Error Rate):      Fehlerquote relativ zu allen Operationen
  - WIL (Word Information Lost): Verlorene Informationsmenge
  - WIP (Word Information Preserved): Erhaltene Informationsmenge
  - CER (Character Error Rate):  Fehlerquote auf Zeichenebene
"""

import jiwer


# ─── Konfiguration ──────────────────────────────────────────────────────────
GROUND_TRUTH_FILE = "GroundTruthTranslate.txt"

SYSTEM_FILES = {
    "Speechmatics": "SpeechmaticsTranslate.txt",
    "Starteve":     "StarteveTranslate.txt",
}


# ─── Normalisierung ─────────────────────────────────────────────────────────
# Texte werden vor dem Vergleich vereinheitlicht:
#   - Kleinschreibung
#   - Satzzeichen entfernt
#   - Leerzeichen am Rand entfernt
#   - In Wort- bzw. Zeichenliste umgewandelt

WORD_NORMALIZER = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfWords(),
])

CHAR_NORMALIZER = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfChars(),
])


# ─── Hilfsfunktionen ────────────────────────────────────────────────────────
def read_text_file(path: str) -> str:
    """Liest eine UTF-8-Textdatei ein und entfernt Whitespace am Rand."""
    with open(path, encoding="utf-8") as file:
        return file.read().strip()


def evaluate_system(reference: str, hypothesis: str) -> dict:
    """
    Vergleicht eine AI-Transkription (hypothesis) mit dem Ground Truth (reference).
    Berechnet WER, MER, WIL, WIP, CER sowie die Anzahl der einzelnen Fehlertypen.
    """
    word_result = jiwer.process_words(
        reference, hypothesis,
        reference_transform=WORD_NORMALIZER,
        hypothesis_transform=WORD_NORMALIZER,
    )

    char_result = jiwer.process_characters(
        reference, hypothesis,
        reference_transform=CHAR_NORMALIZER,
        hypothesis_transform=CHAR_NORMALIZER,
    )

    return {
        "wer": word_result.wer,
        "mer": word_result.mer,
        "wil": word_result.wil,
        "wip": word_result.wip,
        "cer": char_result.cer,
        "hits":          word_result.hits,
        "substitutions": word_result.substitutions,
        "deletions":     word_result.deletions,
        "insertions":    word_result.insertions,
    }


# ─── Ausgabe-Funktionen ─────────────────────────────────────────────────────
def print_metrics_table(results: dict) -> None:
    """Gibt die Hauptmetriken (WER, MER, WIL, WIP, CER) als Tabelle aus."""
    print(f"\n{'System':<15} {'WER':>8} {'MER':>8} {'WIL':>8} {'WIP':>8} {'CER':>8}")
    print("-" * 60)

    for name, metrics in results.items():
        print(
            f"{name:<15} "
            f"{metrics['wer']:>8.4f} "
            f"{metrics['mer']:>8.4f} "
            f"{metrics['wil']:>8.4f} "
            f"{metrics['wip']:>8.4f} "
            f"{metrics['cer']:>8.4f}"
        )


def print_error_details(results: dict) -> None:
    """Gibt die einzelnen Fehlertypen pro System aus."""
    print("\nDetails (H=Hits, S=Substitutionen, D=Deletionen, I=Insertionen):")
    print(f"{'System':<15} {'H':>8} {'S':>8} {'D':>8} {'I':>8}")
    print("-" * 50)

    for name, metrics in results.items():
        print(
            f"{name:<15} "
            f"{metrics['hits']:>8} "
            f"{metrics['substitutions']:>8} "
            f"{metrics['deletions']:>8} "
            f"{metrics['insertions']:>8}"
        )


def print_ranking(results: dict) -> None:
    """Sortiert die Systeme nach WER und gibt das Ranking aus."""
    print("\nRanking nach WER (niedrigster Wert = beste Genauigkeit):")

    ranked = sorted(results.items(), key=lambda item: item[1]["wer"])

    for position, (name, metrics) in enumerate(ranked, start=1):
        print(f"  {position}. {name:<15}  WER={metrics['wer']:.4f}  CER={metrics['cer']:.4f}")


# ─── Hauptprogramm ──────────────────────────────────────────────────────────
def main() -> None:
    # 1. Ground Truth einmalig laden
    reference_text = read_text_file(GROUND_TRUTH_FILE)

    # 2. Jedes System auswerten
    results = {}
    for system_name, file_path in SYSTEM_FILES.items():
        hypothesis_text = read_text_file(file_path)
        results[system_name] = evaluate_system(reference_text, hypothesis_text)

    # 3. Ergebnisse ausgeben
    print_metrics_table(results)
    print_error_details(results)
    print_ranking(results)


if __name__ == "__main__":
    main()