import pytest
from core.local_micro_classifier import LocalMicroClassifier

def test_normalization_accents():
    clf = LocalMicroClassifier()
    # áéíóú -> aeiou
    tokens = clf.tokenize_safe("Hólá Gréis")
    assert "hola" in tokens
    assert "greis" in tokens

def test_normalization_punctuation():
    clf = LocalMicroClassifier()
    tokens = clf.tokenize_safe("¿Hola, Greys? ¡Ayuda!")
    assert tokens == ["hola", "greys", "ayuda"]

def test_confidence_threshold_unknown():
    clf = LocalMicroClassifier()
    # Frase que no tiene nada que ver
    res = clf.predict_intent("manzana azul volando")
    # Score será 0 o muy bajo -> unknown_safe
    assert res.predicted_intent == "unknown_safe"
    assert res.confidence < 0.45

def test_confusion_matrix_generation():
    clf = LocalMicroClassifier()
    test_set = {
        "greeting": ["hola", "buenas"],
        "help": ["ayuda", "help"]
    }
    matrix = clf.evaluate_confusion_matrix(test_set)
    assert matrix["total_examples"] == 4
    assert "accuracy" in matrix
    assert "confusion_pairs" in matrix

def test_classifier_v1_precision_threshold():
    clf = LocalMicroClassifier()
    # Test contra sus propios datos de entrenamiento
    matrix = clf.evaluate_confusion_matrix(clf.training_data)
    # v1.2 es más cauto, aceptamos >= 0.70 de exactitud en exact matches por el margen
    assert matrix["accuracy"] >= 0.70
