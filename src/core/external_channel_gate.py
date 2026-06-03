from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("ExternalChannelGate")

@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reason: str
    mode: str # interactive, dream, morning_brief, test, health_check
    degradation: str = "none" # none, local_only, skip
    requires_user_approval: bool = False
    schema_version: str = "gate-decision.v1"

class ExternalChannelGate:
    """
    Unificador de políticas de acceso al canal externo (LLM).
    Centraliza Circuit Breaker, Stress Guard y configuraciones de modo.
    """

    def __init__(self, stress_guard: Optional[Any] = None, circuit_breaker: Optional[Any] = None):
        self.stress_guard = stress_guard
        self.circuit_breaker = circuit_breaker

    def can_call_llm(self, context: Dict[str, Any]) -> GateDecision:
        """
        Evalúa si se permite una llamada al LLM basada en el contexto y estado del sistema.
        """
        mode = context.get("mode", "interactive")
        source = context.get("source", "unknown")

        # 1. Global Force Local Only
        if os.getenv("GREYS_FORCE_LOCAL_ONLY") == "1":
            return GateDecision(False, "GREYS_FORCE_LOCAL_ONLY is enabled", mode, "local_only")

        # 2. Dream Mode Policy
        if mode == "dream" or os.getenv("GREYS_DREAM_MODE_ACTIVE") == "1":
            if os.getenv("GREYS_DREAM_LLM_ENABLED") == "0":
                return GateDecision(False, "GREYS_DREAM_LLM_ENABLED is disabled", mode, "local_only")
        
        # 3. Semantic Dream Policy
        if source == "semantic_dream_miner" and os.getenv("GREYS_SEMANTIC_DREAM_LLM_ENABLED") == "0":
            return GateDecision(False, "GREYS_SEMANTIC_DREAM_LLM_ENABLED is disabled", mode, "skip")

        # 4. Stress Guard Check
        if self.stress_guard and self.stress_guard.is_host_under_stress():
            return GateDecision(False, "System host is under stress", mode, "local_only")

        # 5. Circuit Breaker Check
        if self.circuit_breaker and not self.circuit_breaker.check_status():
            return GateDecision(False, "LLM Circuit Breaker is OPEN", mode, "local_only")

        # 6. Test environment check (Ollama real shouldn't be called in tests unless explicit)
        if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("GREYS_ALLOW_REAL_LLM_IN_TESTS") == "1":
            return GateDecision(False, "Real LLM call blocked in test environment", mode, "skip")

        return GateDecision(True, "All gates passed", mode, "none")

    def should_degrade_local_only(self, decision: GateDecision) -> bool:
        return decision.degradation == "local_only"

    def explain_decision(self, decision: GateDecision) -> str:
        return f"Decision: {'ALLOWED' if decision.allowed else 'DENIED'} | Reason: {decision.reason} | Mode: {decision.mode} | Degradation: {decision.degradation}"
