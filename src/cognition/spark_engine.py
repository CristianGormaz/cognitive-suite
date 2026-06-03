from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from core.task_envelope import TaskEnvelope
from core.system_stress_guard import SystemStressGuard
from core.semantic_tension_ledger import SemanticTensionLedger, SemanticTensionEvent
from core.ingestion_failure_ledger import IngestionFailureLedger

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SparkSignal:
    timestamp: float
    source: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SparkProposal:
    task_id: str
    reasoning: str
    suggested_intent: str
    friction_estimates: Dict[str, float]
    created_at: float = field(default_factory=time.time)


class SparkEngineError(RuntimeError):
    """Base error for SparkEngine failures."""


class SparkEngine:
    """
    SparkEngine: Motor de reflexión proactiva controlada para Greys-v3.
    
    Observa el estado inactivo del sistema, recolecta señales de auditoría,
    formula propuestas usando el planner, las valida con IAFA y emite
    "dudas evolutivas" al orquestador. NO ejecuta acciones directamente.
    """

    def __init__(
        self,
        auditor: Any = None,
        planner: Any = None,
        iafa_engine: Any = None,
        orchestrator: Any = None,
        idle_probe: Any = None,
        memory_probe: Any = None,
        pulse_interval_seconds: int = 300,
        cooldown_seconds: int = 3600,
        max_signals_per_pulse: int = 5,
        enabled: bool = True,
        dry_run: bool = False,
        stress_guard: Optional[SystemStressGuard] = None,
        tension_ledger: Optional[SemanticTensionLedger] = None,
        failure_ledger: Optional[IngestionFailureLedger] = None,
    ):
        self.auditor = auditor
        self.planner = planner
        self.iafa_engine = iafa_engine
        self.orchestrator = orchestrator
        self.idle_probe = idle_probe
        self.memory_probe = memory_probe

        self.pulse_interval = max(1, pulse_interval_seconds)
        self.cooldown = max(0, cooldown_seconds)
        self.max_signals = max(1, max_signals_per_pulse)
        self.enabled = enabled
        self.dry_run = dry_run
        self.stress_guard = stress_guard or SystemStressGuard()
        self.tension_ledger = tension_ledger or SemanticTensionLedger()
        self.failure_ledger = failure_ledger or IngestionFailureLedger()

        self._task: Optional[asyncio.Task[None]] = None
        self._last_proposal_time: float = 0.0
        self._running: bool = False

    def start(self) -> None:
        """Inicia el ciclo en segundo plano de manera segura."""
        if not self.enabled:
            logger.info("SparkEngine is disabled. Not starting.")
            return

        if self._running:
            return

        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._run_loop())
            logger.info(f"SparkEngine started (interval={self.pulse_interval}s, dry_run={self.dry_run})")
        except RuntimeError:
            logger.error("SparkEngine cannot start: No event loop running.")

    async def stop(self) -> None:
        """Detiene el ciclo y limpia la tarea."""
        self._running = False
        if self._task:
            if not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            self._task = None
        logger.info("SparkEngine stopped.")

    async def _run_loop(self) -> None:
        """Bucle principal del pulso, atrapando CancelledError correctamente."""
        while self._running:
            try:
                await self.pulse()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Unexpected error in SparkEngine loop: {exc}", exc_info=True)
            
            await asyncio.sleep(self.pulse_interval)

    async def pulse(self) -> None:
        """Un ciclo simple de recolección y propuesta."""
        logger.debug("SparkEngine pulse tick")
        
        is_idle = await self._is_idle()
        logger.debug(f"SparkEngine system idle: {is_idle}")
        if not is_idle:
            return

        is_stressed = self.stress_guard.is_host_under_stress()
        logger.debug(f"SparkEngine host under stress: {is_stressed}")
        if is_stressed:
            logger.info("SparkEngine pulse skipped: Host is under stress.")
            return

        time_since_last = time.time() - self._last_proposal_time
        if time_since_last < self.cooldown:
            logger.debug(f"SparkEngine pulse skipped: Cooldown active ({int(time_since_last)}s < {self.cooldown}s)")
            return

        signals = await self._collect_signals()
        logger.debug(f"SparkEngine signals collected: {len(signals)}")

        # --- PROPUESTA BASADA EN FALLOS DE INGESTIÓN ---
        top_failures = self.failure_ledger.get_top_missing_capabilities(limit=1)
        if top_failures:
            sig, count = top_failures[0]
            # Si hemos fallado 3+ veces y no está suprimido por tensión
            if count >= 3 and not self.tension_ledger.should_suppress_proposal(f"skill_needed:{sig}"):
                logger.info(f"Proposing missing capability: {sig} (failed {count} times)")
                await self._emit_missing_capability_doubt(sig, count)
                self._last_proposal_time = time.time()
                return

        if not signals:
            return

        logger.info(f"Collected {len(signals)} signals. Querying planner for reflection...")
        proposal = await self._ask_planner(signals)
        logger.debug(f"SparkEngine planner called: {'yes' if proposal else 'no'}")
        if not proposal:
            return

        # --- VERIFICACIÓN DE TENSIÓN SEMÁNTICA ---
        proposal_sig = f"{proposal.suggested_intent}:reflection"
        if self.tension_ledger.should_suppress_proposal(proposal_sig):
            logger.warning(f"SparkEngine proposal '{proposal_sig}' suppressed due to cognitive fatigue.")
            return

        logger.info(f"Planner proposed reflection: {proposal.suggested_intent}. Validating with IAFA...")
        is_safe = await self._validate_with_iafa(proposal)
        if not is_safe:
            logger.warning(f"SparkEngine proposal '{proposal.suggested_intent}' rejected by IAFA.")
            self._register_tension_event(proposal, "iafa_rejected", is_safe)
            return

        await self._emit_evolutionary_doubt(proposal, signals)
        self._register_tension_event(proposal, "evolutionary_doubt", is_safe)
        logger.debug("SparkEngine evolutionary doubt emitted: yes")
        self._last_proposal_time = time.time()

    def _register_tension_event(self, proposal: SparkProposal, event_type: str, iafa_allowed: bool):
        """Helper para registrar eventos en el ledger."""
        snapshot = self.stress_guard.get_stress_snapshot()
        
        event = SemanticTensionEvent(
            event_id=f"spark_{os.urandom(4).hex()}",
            timestamp=time.time(),
            source="spark_engine",
            event_type=event_type,
            task_id=proposal.task_id,
            intent_category=proposal.suggested_intent,
            proposed_action="reflection",
            proposal_signature=f"{proposal.suggested_intent}:reflection",
            iafa_score=0.5 if not iafa_allowed else 0.9,
            friction_R=proposal.friction_estimates.get("R", 0.0),
            friction_I=proposal.friction_estimates.get("I", 0.0),
            friction_N=proposal.friction_estimates.get("N", 0.0),
            host_under_stress=snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"],
            host_load_1m=snapshot["load_1m"],
            available_memory_mb=snapshot["mem_available_mb"],
            tension_tau=self.tension_ledger.compute_tensions(
                event_type, 
                snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"],
                proposal.friction_estimates
            ),
            capacity_A=self.tension_ledger.compute_capacity(
                snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"],
                0.5 if not iafa_allowed else 0.9
            ),
            damage_delta=0.1 if event_type == "evolutionary_doubt" else 0.3
        )
        self.tension_ledger.append_event(event)

    async def _emit_missing_capability_doubt(self, signature: str, count: int) -> None:
        """Emite una duda proactiva sobre una habilidad faltante."""
        if not self.orchestrator: return
        
        proposal = SparkProposal(
            task_id=f"spark_missing_{os.urandom(4).hex()}",
            reasoning=f"He detectado que fallé {count} veces con la capacidad '{signature}'. Sugiero analizar una habilidad futura.",
            suggested_intent="missing_capability_evolution",
            friction_estimates={"R": 0.3, "I": 0.2, "N": 0.1}
        )
        
        payload = {
            "event_type": "evolutionary_doubt",
            "source": "spark_engine",
            "proposal": asdict(proposal),
            "requires_user_approval": True,
            "suggested_next_engine": "GenesisEngine",
            "missing_capability": signature,
            "failure_count": count
        }
        
        for method_name in ["handle_evolutionary_doubt", "handle_spark_proposal", "emit_event"]:
            if hasattr(self.orchestrator, method_name):
                self._register_tension_event(proposal, "missing_capability_doubt", True)
                await self._maybe_await(getattr(self.orchestrator, method_name), payload)
                break

    async def _is_idle(self) -> bool:
        """
        Consulta de forma defensiva si el sistema está inactivo.
        Falla "seguro" (retorna False) si no hay probe o falla la llamada.
        """
        if self.idle_probe is None:
            return False
        
        try:
            return bool(await self._maybe_await(self.idle_probe))
        except Exception as exc:
            logger.debug(f"idle_probe failed: {exc}")
            return False

    async def _collect_signals(self) -> List[SparkSignal]:
        """Recolecta señales de componentes pasados defendiéndose contra fallos de forma y tipo."""
        targets = [t for t in (self.auditor, self.memory_probe) if t is not None]
        
        # Intentamos obtener entradas verificadas del auditor si es posible
        collected_data: List[Any] = []
        if self.auditor and hasattr(self.auditor, "iter_verified_entries"):
            try:
                # Solo leemos una muestra reciente para no bloquear
                entries = list(self.auditor.iter_verified_entries())
                # Buscamos registros de tipo 'llm_cognitive_plan_rejected' o errores
                relevant = [e for e in entries if e.get("payload", {}).get("record_type") == "llm_cognitive_plan_rejected"]
                collected_data.extend(relevant[-self.max_signals:])
            except Exception as exc:
                logger.debug(f"Failed to iterate verified entries: {exc}")

        # Fallback a métodos genéricos si no hay datos relevantes aún
        if not collected_data:
            methods_to_try = ["get_recent_failures", "recent_failures", "get_unknown_intentions"]
            for target in targets:
                for method_name in methods_to_try:
                    if hasattr(target, method_name):
                        try:
                            raw_signals = await self._maybe_await(getattr(target, method_name))
                            if isinstance(raw_signals, list):
                                collected_data.extend(raw_signals[-self.max_signals:])
                                break
                        except Exception:
                            continue

        signals: List[SparkSignal] = []
        for item in collected_data:
            payload = item.get("payload", item) if isinstance(item, dict) else {}
            content = str(payload.get("error", payload.get("content", str(item))))
            source = str(payload.get("record_type", "unknown_source"))
            signals.append(SparkSignal(time.time(), source, content, metadata=payload))
            
        return signals

    async def _ask_planner(self, signals: List[SparkSignal]) -> Optional[SparkProposal]:
        if not self.planner:
            return None

        # Creamos un TaskEnvelope real para cumplir con el protocolo del Planner
        summary = " | ".join(s.content for s in signals)
        try:
            envelope = TaskEnvelope.from_text(
                text=f"SparkEngine internal reflection on signals: {summary}",
                origin="spark_engine",
                declared_intent="evolutionary_reflection"
            )
        except Exception as exc:
            logger.error(f"Failed to create TaskEnvelope for reflection: {exc}")
            return None

        try:
            # LLMPlanner.plan(envelope)
            plan = await self.planner.plan(envelope)
            
            # Extraemos la decisión del plan
            decision = getattr(plan, "decision", None)
            if decision:
                return SparkProposal(
                    task_id=envelope.task_id,
                    reasoning=getattr(plan, "thought_trace", "Reflection generated"),
                    suggested_intent=getattr(decision, "intent_category", "unknown_intent"),
                    friction_estimates=decision.iafa_friction_estimates.to_dict()
                )
        except Exception as exc:
            logger.error(f"Planner error during reflection: {exc}")
        
        return None

    async def _validate_with_iafa(self, proposal: SparkProposal) -> bool:
        if not self.iafa_engine:
            return self.dry_run

        try:
            # Variables de estado mental para el pulso proactivo
            current_variables = {
                "O": 0.9, "M": 0.7, "P": 0.9, "V": 0.9, "K": 0.8, "A": 0.2,
                "R": proposal.friction_estimates.get("R", 0.5),
                "I": proposal.friction_estimates.get("I", 0.5),
                "N": proposal.friction_estimates.get("N", 0.5)
            }

            decision = await self._maybe_await(
                self.iafa_engine.evaluate_action, 
                action_name=proposal.suggested_intent,
                current_variables=current_variables,
                recent_intents=["spark_reflection"],
                current_hz=0.05  # Frecuencia baja en idle
            )
            
            return getattr(decision, "allowed", False)
        except Exception as exc:
            logger.error(f"IAFA validation error: {exc}")
            return False

    async def _emit_evolutionary_doubt(self, proposal: SparkProposal, signals: List[SparkSignal]) -> None:
        if not self.orchestrator:
            logger.info(f"Spark Reflection: {proposal.suggested_intent}")
            return

        payload = {
            "event_type": "evolutionary_doubt",
            "source": "spark_engine",
            "proposal": asdict(proposal),
            "signals": [asdict(s) for s in signals],
            "requires_user_approval": True,
            "suggested_next_engine": "GenesisEngine"
        }

        # Intentamos llamar al método de manejo de dudas en el orquestador
        for method_name in ["handle_evolutionary_doubt", "handle_spark_proposal", "emit_event"]:
            if hasattr(self.orchestrator, method_name):
                try:
                    await self._maybe_await(getattr(self.orchestrator, method_name), payload)
                    logger.info(f"SparkEngine emitted doubt: {proposal.suggested_intent}")
                    return
                except Exception:
                    continue
        
        logger.warning(f"SparkEngine could not find an entry point in orchestrator to emit doubt.")

    async def _maybe_await(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        if not callable(func):
            return func
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result) or hasattr(result, "__await__"):
            return await result
        return result
