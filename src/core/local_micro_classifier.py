from __future__ import annotations

import os
import time
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("LocalMicroClassifier")

@dataclass(frozen=True)
class LocalClassifierPrediction:
    input_signature: str
    predicted_intent: str # greeting, help, status, identity, unknown_safe
    confidence: float
    matched_features: List[str]
    classifier_version: str = "local-micro-v0"
    should_execute: bool = False # Siempre False en v0 (Shadow Mode)
    requires_human_review: bool = True
    reason_summary: str = ""
    schema_version: str = "local-classifier-prediction.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class LocalMicroClassifier:
    """
    Clasificador liviano basado en tokens para generalizar intenciones básicas localmente.
    v1.2: Matriz de confusión avanzada, penalización por ambigüedad y balanced accuracy.
    """

    def __init__(self):
        # Dataset sintético integrado (v1.2 rebalanceado)
        self.training_data = {
            "greeting": [
                "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", 
                "hey greys", "hola greys", "que tal", "saludos", "buen dia", "aloha",
                "hi greys", "saludo inicial", "hola sistema", "que onda", "buenas vibras",
                "hola hola", "saludos cordiales"
            ],
            "help": [
                "ayuda", "comandos", "lista de comandos", "dime los comandos disponibles",
                "como uso greys", "que opciones tengo", "necesito instrucciones",
                "muestrame que puedo pedirte", "ayudame", "help", "auxilio",
                "instrucciones de uso", "guia de comandos", "que funciones tienes",
                "ayuda por favor", "necesito soporte", "como funcionas", "que haces"
            ],
            "status": [
                "estado", "status", "estas operativo", "como esta el sistema", 
                "como vas", "estas funcionando", "revisar estado", "vitals", 
                "salud del sistema", "modo actual", "estas encendido", "reporte de salud",
                "ver vitals", "estado operativo", "estas activo", "como va todo", "diagnostico"
            ],
            "identity": [
                "quien eres", "que eres", "dime quien eres", "eres greys", 
                "cual es tu proposito", "presentate", "identidad", "quien es greys",
                "presentate sistema", "hablame de ti", "eres un bot", "que eres exactamente",
                "cual es tu origen", "definicion de greys", "quien te creo", "que naturaleza tienes"
            ],
        }
        self.token_weights: Dict[str, Dict[str, float]] = self._train_simple()

    def _train_simple(self) -> Dict[str, Dict[str, float]]:
        """Construye un mapa de tokens y sus pesos por intención."""
        weights = {}
        for intent, examples in self.training_data.items():
            intent_tokens = {}
            for ex in examples:
                tokens = self.tokenize_safe(ex)
                for t in tokens:
                    intent_tokens[t] = intent_tokens.get(t, 0.0) + 1.0
            
            total = sum(intent_tokens.values())
            weights[intent] = {t: v / total for t, v in intent_tokens.items()} if total > 0 else {}
        return weights

    def tokenize_safe(self, text: str) -> List[str]:
        """Tokenización con normalización profunda y limpieza."""
        # 1. Normalizar tildes (á->a, etc.)
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
            "ü": "u", "ñ": "n"
        }
        clean = text.lower()
        for original, replacement in replacements.items():
            clean = clean.replace(original, replacement)
            
        # 2. Eliminar puntuación y caracteres especiales
        clean = re.sub(r"[^a-z0-9\s]", " ", clean)
        
        # 3. Eliminar espacios repetidos y tokens de 1 letra
        return [t for t in clean.split() if len(t) > 1]

    def predict_intent(self, text: str) -> LocalClassifierPrediction:
        """Predice la intención con hardening por margen y ambigüedad."""
        tokens = self.tokenize_safe(text)
        if not tokens:
            return self._unknown_prediction("empty_input")

        # Penalización por entrada extremadamente corta
        ambiguity_penalty = 1.0
        if len(tokens) == 1: ambiguity_penalty = 0.8

        scores = {intent: 0.0 for intent in self.training_data}
        matched_tokens = {intent: [] for intent in self.training_data}

        for t in tokens:
            for intent, token_map in self.token_weights.items():
                if t in token_map:
                    # El peso se ve afectado por la ambigüedad global del token
                    weight = token_map[t] * ambiguity_penalty
                    scores[intent] += weight
                    matched_tokens[intent].append(t)

        total_score = sum(scores.values())
        if total_score == 0:
            return self._unknown_prediction("no_tokens_matched")

        # Ordenar intenciones por score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_intent, best_val = sorted_scores[0]
        second_intent, second_val = sorted_scores[1] if len(sorted_scores) > 1 else ("none", 0.0)

        confidence = round(best_val / total_score, 2)
        second_confidence = round(second_val / total_score, 2)
        margin = round(confidence - second_confidence, 2)

        # Umbrales de Madurez v1.2
        margin_threshold = 0.12
        confidence_min = 0.40
        
        is_ambiguous = (second_val > 0) and (margin < margin_threshold)
        
        final_intent = best_intent
        if confidence < confidence_min or is_ambiguous:
            final_intent = "unknown_safe"

        # Overconfidence check (Shadow Warning)
        overconfidence = (confidence > 0.8) and (margin < 0.2)

        return LocalClassifierPrediction(
            input_signature=" ".join(tokens[:3]),
            predicted_intent=final_intent,
            confidence=confidence,
            matched_features=matched_tokens.get(best_intent, []),
            reason_summary=f"Score {round(best_val, 2)}, Margin {margin} {'[OVERCONFIDENCE]' if overconfidence else ''}"
        )

    def evaluate_confusion_matrix(self, test_set: Dict[str, List[str]]) -> Dict[str, Any]:
        """Matriz de confusión avanzada con balanced accuracy y precision/recall."""
        all_results = []
        intents = list(self.training_data.keys()) + ["unknown_safe"]
        
        metrics_by_intent = {i: {"tp": 0, "fp": 0, "fn": 0, "total": 0} for i in intents}
        
        for expected_intent, examples in test_set.items():
            for ex in examples:
                pred = self.predict_intent(ex)
                actual = pred.predicted_intent
                all_results.append((expected_intent, actual))
                
                metrics_by_intent[expected_intent]["total"] += 1
                if actual == expected_intent:
                    metrics_by_intent[expected_intent]["tp"] += 1
                else:
                    metrics_by_intent[actual]["fp"] += 1
                    metrics_by_intent[expected_intent]["fn"] += 1
        
        total = len(all_results)
        correct = sum(1 for e, p in all_results if e == p)
        accuracy = round(correct / total, 2) if total > 0 else 0.0
        
        # Balanced Accuracy
        recalls = []
        for i in self.training_data.keys():
            m = metrics_by_intent[i]
            rec = m["tp"] / m["total"] if m["total"] > 0 else 0.0
            recalls.append(rec)
        balanced_acc = round(sum(recalls) / len(recalls), 2) if recalls else 0.0

        confusion = {}
        for e, p in all_results:
            if e != p and p != "unknown_safe":
                pair = f"{e}->{p}"
                confusion[pair] = confusion.get(pair, 0) + 1

        return {
            "total_examples": total,
            "accuracy": accuracy,
            "balanced_accuracy": balanced_acc,
            "unknown_safe_rate": round(sum(1 for e, p in all_results if p == "unknown_safe") / total, 2) if total > 0 else 0.0,
            "confusion_pairs": confusion,
            "overconfidence_warning": accuracy > 0.9 and balanced_acc < 0.7,
            "version": "local-micro-v1.2"
        }

    def _unknown_prediction(self, reason: str) -> LocalClassifierPrediction:
        return LocalClassifierPrediction(
            input_signature="unknown",
            predicted_intent="unknown_safe",
            confidence=0.0,
            matched_features=[],
            reason_summary=reason
        )

    def _unknown_prediction(self, reason: str) -> LocalClassifierPrediction:
        return LocalClassifierPrediction(
            input_signature="unknown",
            predicted_intent="unknown_safe",
            confidence=0.0,
            matched_features=[],
            reason_summary=reason
        )

    def explain_prediction(self, pred: LocalClassifierPrediction) -> str:
        if pred.predicted_intent == "unknown_safe":
            return "No se detectaron patrones conocidos con suficiente confianza."
        return f"Intención '{pred.predicted_intent}' detectada vía tokens: {pred.matched_features} (Confianza: {pred.confidence})"
