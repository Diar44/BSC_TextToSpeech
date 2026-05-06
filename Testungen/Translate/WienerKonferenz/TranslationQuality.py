"""
BLEU Score Evaluator for Translation Validation
------------------------------------------------
Vergleicht Übersetzungen gegen eine Ground Truth mit BLEU Score.
Usage: python evaluate_bleu.py
"""

import os
import re

try:
    from nltk.translate.bleu_score import sentence_bleu, corpus_bleu, SmoothingFunction
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except ImportError:
    print("Installing nltk...")
    os.system("pip install nltk")
    from nltk.translate.bleu_score import sentence_bleu, corpus_bleu, SmoothingFunction
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)


# Konfiguration
GROUND_TRUTH_FILE = "GroundTruthTranslate.txt"

# Mapping: System-Name -> Dateiname der generierten Übersetzung
SYSTEM_TRANSLATIONS = {
    "Speechmatics": "SpeechmaticsTranslate.txt",
    "Starteve":     "StarteveTranslate.txt",
    "Whisper":      "WhisperTranslate.txt",
    "GoogleCloud":  "GoogleCloudTranslate.txt",
}


# Hilfsfunktionen

def read_text_file(path: str) -> str:
    """Liest eine UTF-8-Textdatei ein und entfernt Whitespace am Rand."""
    with open(path, encoding="utf-8") as file:
        return file.read().strip()


def normalize(text: str) -> str:
    """Lowercase, Satzzeichen entfernen, Whitespace normalisieren."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    return normalize(text).split()


def bleu_scores(reference_tokens: list[str], hypothesis_tokens: list[str]) -> dict:
    """
    Berechnet BLEU-1 bis BLEU-4 sowie Corpus BLEU-4.

    :param reference_tokens:  Ground-Truth-Tokens
    :param hypothesis_tokens: Vom AI-System erzeugte Tokens
    :return: Dictionary mit allen BLEU-Metriken
    """
    smoother = SmoothingFunction().method1
    ref = [reference_tokens]

    scores = {}
    for n in range(1, 5):
        weights = tuple(1.0 / n if i < n else 0.0 for i in range(4))
        scores[f"BLEU-{n}"] = sentence_bleu(
            ref, hypothesis_tokens,
            weights=weights,
            smoothing_function=smoother
        )

    scores["BLEU-4 (corpus)"] = corpus_bleu(
        [[reference_tokens]], [hypothesis_tokens],
        smoothing_function=smoother
    )
    return scores


# Ausgabefunktionen

def print_metrics_table(results: dict) -> None:
    """Gibt eine Übersichtstabelle mit allen BLEU-Metriken aus."""
    print(f"\n{'System':<15} {'BLEU-1':>8} {'BLEU-2':>8} "
          f"{'BLEU-3':>8} {'BLEU-4':>8} {'CORPUS-4':>10}")
    print("-" * 65)

    for name, r in results.items():
        print(f"{name:<15} {r['BLEU-1']:>8.4f} {r['BLEU-2']:>8.4f} "
              f"{r['BLEU-3']:>8.4f} {r['BLEU-4']:>8.4f} "
              f"{r['BLEU-4 (corpus)']:>10.4f}")


def print_ranking(results: dict) -> None:
    """Sortiert die Systeme nach BLEU-4 (corpus) und gibt das Ranking aus."""
    print("\nRanking nach BLEU-4 (höchster Wert = beste Übersetzungsqualität):")

    ranked_systems = sorted(
        results.items(),
        key=lambda item: item[1]["BLEU-4 (corpus)"],
        reverse=True
    )

    for position, (name, r) in enumerate(ranked_systems, start=1):
        print(f"  {position}. {name:<15}  "
              f"BLEU-4={r['BLEU-4 (corpus)']:.4f}  ")


# Hauptprogramm

def main() -> None:
    # 1. Ground Truth einlesen
    reference_text = read_text_file(GROUND_TRUTH_FILE)
    reference_tokens = tokenize(reference_text)

    print(f"\nGround Truth : {GROUND_TRUTH_FILE}")
    print(f"Words (GT)   : {len(reference_tokens)}")

    # 2. Jedes System auswerten
    all_results = {}
    for system_name, translation_path in SYSTEM_TRANSLATIONS.items():
        hypothesis_text = read_text_file(translation_path)
        hypothesis_tokens = tokenize(hypothesis_text)
        all_results[system_name] = bleu_scores(reference_tokens, hypothesis_tokens)

    # 3. Ergebnisse ausgeben
    print_metrics_table(all_results)
    print_ranking(all_results)


if __name__ == "__main__":
    main()
