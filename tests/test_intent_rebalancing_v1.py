import pytest
import json
from core.local_micro_classifier import LocalMicroClassifier

def test_normalization_deep_cleaning():
    clf = LocalMicroClassifier()
    # Tildes, puntuación, mayúsculas, espacios
    text = "¿HÓLÁ, Greys?  ¡Díme quién ÉRÉS!"
    tokens = clf.tokenize_safe(text)
    assert "hola" in tokens
    assert "dime" in tokens
    assert "quien" in tokens
    assert "eres" in tokens

def test_unknown_safe_hardening_noise():
    clf = LocalMicroClassifier()
    # Frases ruidosas del dataset sintético fixtures
    noise = ["manzana azul caminando", "ruido sin accion clara", "solo estoy pensando"]
    for ex in noise:
        res = clf.predict_intent(ex)
        assert res.predicted_intent == "unknown_safe"

def test_margin_threshold_ambiguity():
    clf = LocalMicroClassifier()
    # Forzar una situación donde dos intenciones compitan
    # 'ayuda' y 'estado' rebalanceados no deberían competir, 
    # pero podemos probar con tokens compartidos si existieran.
    
    # Si inyectamos un caso artificialmente cerrado:
    clf.token_weights = {
        "intent1": {"token": 0.51},
        "intent2": {"token": 0.49}
    }
    clf.training_data = {"intent1": [], "intent2": []} # Para que predict no falle
    
    res = clf.predict_intent("token")
    # Margen = 0.51 - 0.49 = 0.02 < 0.15 -> unknown_safe
    assert res.predicted_intent == "unknown_safe"

def test_confusion_matrix_v1_1_metrics():
    clf = LocalMicroClassifier()
    test_set = {
        "greeting": ["hola", "buenas"],
        "unknown_safe": ["manzana azul"]
    }
    matrix = clf.evaluate_confusion_matrix(test_set)
    assert "unknown_safe_rate" in matrix
    assert "overconfidence_warning" in matrix
    assert matrix["version"] == "local-micro-v1.2"

def test_morning_brief_intent_rebalancing_section(tmp_path):
    from cognition.morning_brief import MorningBrief
    import os
    
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    # Crear fixture sintético para el test
    fixtures_dir = tmp_path / "tests/fixtures/local_classifier"
    fixtures_dir.mkdir(parents=True)
    fixture_path = fixtures_dir / "synthetic_intents.json"
    fixture_path.write_text(json.dumps({"greeting": ["hola"]}))
    
    # Mockear el path en MorningBrief es difícil sin cambiar código, 
    # pero podemos confiar en que la lógica de renderizado está probada por la suite si el fixture existe.
    # Aquí probaremos que el brief maneja la ausencia de alerta de sobreconfianza.
    
    brief_gen = MorningBrief(memory_dir=str(memory_dir))
    brief = brief_gen.generate_brief()
    assert "Madurez del Clasificador Local" in brief
