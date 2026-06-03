import asyncio
import time
import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from cognition.spark_engine import SparkEngine, SparkSignal, SparkProposal
from core.task_envelope import TaskEnvelope

# --- Mocks y Dummies para el Fire Drill ---

@dataclass
class MockIAFADecision:
    allowed: bool
    reason: str

class FireDrillAuditor:
    def __init__(self, failure_signal: Dict[str, Any]):
        # Simulamos un registro real firmado (payload simplificado para el iterador)
        self.entries = [{"payload": failure_signal}]
    
    def iter_verified_entries(self):
        return iter(self.entries)

class FireDrillPlanner:
    def __init__(self, suggested_intent: str):
        self.suggested_intent = suggested_intent
        self.calls = 0
    
    async def plan(self, envelope: TaskEnvelope):
        self.calls += 1
        # Simulamos la estructura de retorno del LLMPlanner real
        class MockFriction:
            def to_dict(self): return {"R": 0.2, "I": 0.1, "N": 0.1}
            
        class MockDecision:
            def __init__(self, intent):
                self.intent_category = intent
                self.iafa_friction_estimates = MockFriction()
        
        class MockPlan:
            def __init__(self, intent):
                self.decision = MockDecision(intent)
                self.thought_trace = "Simulated reasoning for fire drill"
        
        return MockPlan(self.suggested_intent)

class FireDrillIAFA:
    def __init__(self, allowed: bool = True):
        self.allowed = allowed
    
    async def evaluate_action(self, **kwargs):
        return MockIAFADecision(allowed=self.allowed, reason="Fire drill validation")

class FireDrillOrchestrator:
    def __init__(self):
        self.events = []
    
    async def emit_event(self, payload: Dict[str, Any]):
        self.events.append(payload)

# --- Test Case ---

@pytest.mark.asyncio
async def test_spark_fire_drill_flow():
    """
    Simula el ciclo completo:
    1. Señal de fallo detectada en auditoría.
    2. SparkEngine despierta en idle.
    3. Consulta al Planner.
    4. Valida con IAFA.
    5. Emite Evolutionary Doubt al Orquestador.
    6. NO ejecuta GenesisEngine (implícito al no tenerlo inyectado).
    """
    
    # 1. Preparar señal de fallo (IAFA rechaza una acción desconocida)
    failure_signal = {
        "record_type": "llm_cognitive_plan_rejected",
        "error": "Intent 'unknown_weather_command' has no skill and high friction",
        "timestamp": time.time() - 100
    }
    
    auditor = FireDrillAuditor(failure_signal)
    planner = FireDrillPlanner(suggested_intent="weather_skill_v1")
    iafa = FireDrillIAFA(allowed=True)
    orchestrator = FireDrillOrchestrator()
    
    # 2. Configurar SparkEngine para respuesta rápida
    mock_fail = MagicMock()
    mock_fail.get_top_missing_capabilities.return_value = []
    
    mock_tension = MagicMock()
    mock_tension.should_suppress_proposal.return_value = False
    
    engine = SparkEngine(
        auditor=auditor,
        planner=planner,
        iafa_engine=iafa,
        orchestrator=orchestrator,
        idle_probe=lambda: True, # Siempre idle para el test
        pulse_interval_seconds=1,
        cooldown_seconds=0,
        enabled=True,
        dry_run=False,
        failure_ledger=mock_fail,
        tension_ledger=mock_tension
    )
    
    # 3. Ejecutar un único pulso manualmente para control total
    await engine.pulse()
    
    # 4. Verificaciones de Seguridad y Flujo
    
    # A. Se emitió exactamente una duda evolutiva
    assert len(orchestrator.events) == 1
    event = orchestrator.events[0]
    assert event["event_type"] == "evolutionary_doubt"
    assert event["source"] == "spark_engine"
    
    # B. Integridad de la propuesta
    proposal = event["proposal"]
    assert proposal["suggested_intent"] == "weather_skill_v1"
    assert "Simulated reasoning" in proposal["reasoning"]
    
    # C. Protocolos de seguridad
    assert event["requires_user_approval"] is True
    assert event["suggested_next_engine"] == "GenesisEngine"
    
    # D. Verificación de que el Planner fue consultado basado en la señal
    assert planner.calls == 1
    
    # E. Verificación de limpieza (Lifecycle)
    engine.start()
    assert engine._running is True
    await engine.stop()
    assert engine._running is False
    assert engine._task is None

@pytest.mark.asyncio
async def test_spark_fire_drill_iafa_rejection():
    """Valida que si IAFA rechaza la propuesta, no se emite nada."""
    auditor = FireDrillAuditor({"record_type": "llm_cognitive_plan_rejected", "error": "test"})
    planner = FireDrillPlanner(suggested_intent="dangerous_skill")
    iafa = FireDrillIAFA(allowed=False) # IAFA dice NO
    orchestrator = FireDrillOrchestrator()
    
    mock_fail = MagicMock()
    mock_fail.get_top_missing_capabilities.return_value = []
    
    mock_tension = MagicMock()
    mock_tension.should_suppress_proposal.return_value = False
    
    engine = SparkEngine(
        auditor=auditor, planner=planner, iafa_engine=iafa, 
        orchestrator=orchestrator, idle_probe=lambda: True,
        cooldown_seconds=0,
        failure_ledger=mock_fail,
        tension_ledger=mock_tension
    )
    
    await engine.pulse()
    
    # No debe haber eventos emitidos
    assert len(orchestrator.events) == 0
