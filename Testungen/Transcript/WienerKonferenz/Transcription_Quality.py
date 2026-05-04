"""
WER-Evaluation für Speech-to-Text-Systeme.

Vergleicht die Transkriptionen mehrerer AI-Systeme gegen einen
manuell erstellten Ground-Truth-Transkript und berechnet folgende Metriken:
  - WER (Word Error Rate)
  - MER (Match Error Rate)
  - WIL (Word Information Lost)
  - WIP (Word Information Preserved)
  - CER (Character Error Rate)
"""

import jiwer


# Konfiguration
GROUND_TRUTH_FILE = "GroundTruthTranscript.txt"

# Mapping: System-Name -> Dateiname des generierten Transkripts
SYSTEM_TRANSCRIPTS = {
    "Speechmatics": "SpeechmaticsTranscript.txt",
    "Starteve":     "StarteveTranscript.txt",
    "Whisper":      "WhisperTranscript.txt",
    "GoogleCloud":  "GoogleCloudTranscript.txt",
}


# Normalisierung

# Vor dem Vergleich werden beide Texte normalisiert, damit z.B.
# Groß/Kleinschreibung oder Satzzeichen das Ergebnis nicht verfälschen.

WORD_NORMALIZATION = jiwer.Compose([
    jiwer.ToLowerCase(),              # alles in Kleinbuchstaben
    jiwer.RemovePunctuation(),        # Satzzeichen entfernen
    jiwer.Strip(),                    # führende/abschließende Leerzeichen
    jiwer.ReduceToListOfListOfWords() # Text -> Liste von Wörtern
])

CHAR_NORMALIZATION = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfChars()
])


# Hilfsfunktionen

# Liest eine UTF-8-Textdatei ein und entfernt Whitespace am Rand.
def read_text_file(path: str) -> str:
    with open(path, encoding="utf-8") as file:
        return file.read().strip()


"""
    Berechnet alle Metriken für ein einzelnes System.

    :param reference:  Ground-Truth-Transkript (manuell erstellt)
    :param hypothesis: Vom AI-System erzeugtes Transkript
    :return: Dictionary mit allen Metriken und Fehler-Statistiken
"""
def evaluate_system(reference: str, hypothesis: str) -> dict:
    # Word-Level-Metriken (WER, MER, WIL, WIP)
    word_result = jiwer.process_words(
        reference, hypothesis,
        reference_transform=WORD_NORMALIZATION,
        hypothesis_transform=WORD_NORMALIZATION,
    )

    # Character-Level-Metrik (CER)
    char_result = jiwer.process_characters(
        reference, hypothesis,
        reference_transform=CHAR_NORMALIZATION,
        hypothesis_transform=CHAR_NORMALIZATION,
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

# Ausgabefunktionen

# Gibt eine Übersichtstabelle mit allen Metriken aus.
def print_metrics_table(results: dict) -> None:
    print(f"\n{'System':<15} {'WER':>8} {'MER':>8} "
          f"{'WIL':>8} {'WIP':>8} {'CER':>8}")
    print("-" * 60)

    for name, r in results.items():
        print(f"{name:<15} {r['wer']:>8.4f} {r['mer']:>8.4f} "
              f"{r['wil']:>8.4f} {r['wip']:>8.4f} {r['cer']:>8.4f}")

# Gibt eine Detail-Tabelle mit Hits, Substitutionen, Deletionen, Insertionen aus.
def print_error_details(results: dict) -> None:
    print("\nDetails (H=Hits, S=Substitutionen, "
          "D=Deletionen, I=Insertionen):")
    print(f"{'System':<15} {'H':>8} {'S':>8} {'D':>8} {'I':>8}")
    print("-" * 50)

    for name, r in results.items():
        print(f"{name:<15} {r['hits']:>8} {r['substitutions']:>8} "
              f"{r['deletions']:>8} {r['insertions']:>8}")


# Sortiert die Systeme nach WER (aufsteigend) und gibt das Ranking aus.
def print_ranking(results: dict) -> None:
    print("\nRanking nach WER (niedrigster Wert = beste Genauigkeit):")

    ranked_systems = sorted(results.items(), key=lambda item: item[1]["wer"])

    for position, (name, r) in enumerate(ranked_systems, start=1):
        print(f"  {position}. {name:<15}  "
              f"WER={r['wer']:.4f}  CER={r['cer']:.4f}")


# Hauptprogramm

def main() -> None:
    # 1. Ground Truth einlesen
    reference_text = read_text_file(GROUND_TRUTH_FILE)

    # 2. Jedes System auswerten
    all_results = {}
    for system_name, transcript_path in SYSTEM_TRANSCRIPTS.items():
        hypothesis_text = read_text_file(transcript_path)
        all_results[system_name] = evaluate_system(reference_text, hypothesis_text)

    # 3. Ergebnisse ausgeben
    print_metrics_table(all_results)
    print_error_details(all_results)
    print_ranking(all_results)


if __name__ == "__main__":
    main()