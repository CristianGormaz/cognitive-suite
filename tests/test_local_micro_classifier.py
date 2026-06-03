import pytest
from core.local_micro_classifier import LocalMicroClassifier, LocalClassifierPrediction

def test_classifier_greeting():
    clf = LocalMicroClassifier()
    # Frase no idéntica pero con tokens clave
    res = clf.predict_intent("buenas tardes")
    assert res.predicted_intent == "greeting"
    assert res.confidence > 0.0

def test_classifier_help():
    clf = LocalMicroClassifier()
    res = clf.predict_intent("dime los comandos disponibles")
    assert res.predicted_intent == "help"

def test_classifier_status():
    clf = LocalMicroClassifier()
    res = clf.predict_intent("como esta el sistema")
    assert res.predicted_intent == "status"

def test_classifier_identity():
    clf = LocalMicroClassifier()
    res = clf.predict_intent("dime quien eres")
    assert res.predicted_intent == "identity"

def test_classifier_unknown_ambiguous():
    clf = LocalMicroClassifier()
    # Frase que genera colisión o margen bajo (si existiera)
    # Por ahora probamos ruido total
    res = clf.predict_intent("manzana azul volando")
    assert res.predicted_intent == "unknown_safe"
    assert res.confidence == 0.0

def test_should_execute_is_always_false_v0():
    clf = LocalMicroClassifier()
    res = clf.predict_intent("hola")
    assert res.should_execute is False
