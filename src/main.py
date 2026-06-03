from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from cognition.fallback_engine import EvolutionaryFallbackEngine, FallbackHypothesis, FallbackOptions
from cognition.genesis_engine import GenesisEngine, GenesisEngineError
from cognition.genesis_sandbox import GenesisSandbox
from cognition.iafa_transceiver import IafaTransceiver
from cognition.ingestion_router import IngestionRouter, IngestionRouterError
from cognition.llm_planner import LLMPlanner, LLMPlannerError
from cognition.skill_loader import DynamicSkillLoader, SkillLoaderError
from cognition.spark_engine import SparkEngine
from core.action_dispatcher import ActionDispatcher, ActionDispatcherError, DispatchResult
from core.cognitive_loop import CognitiveLoopError, CognitiveLoopResult, CognitiveOrchestrator
from core.iafa_auditor import IafaAuditor
from core.iafa_engine import IAFAEngine
from core.task_envelope import TaskEnvelope
from core.system_stress_guard import SystemStressGuard
from core.response_manager import ResponseManager
from core.semantic_tension_ledger import SemanticTensionLedger, SemanticTensionEvent
from core.failure_classifier import FailureClassifier
from core.ingestion_failure_ledger import IngestionFailureLedger, IngestionFailureEvent
from core.dependency_review_ledger import DependencyReviewLedger
from cognition.iafa_transceiver import (
    IafaTransceiver, LlmError, LlmTimeoutError, LlmConnectionError, 
    LlmCircuitOpenError, LlmHostStressedError
)
from cognition.genesis_analysis import GenesisAnalysis, GenesisAnalysisResult
from cognition.skill_candidate_review import SkillCandidateReview
from cognition.skill_promotion_gate import SkillPromotionGate
from cognition.skill_experimental_promoter import SkillExperimentalPromoter
from core.experimental_risk_profile import ExperimentalRiskProfile
from core.local_intent_router import LocalIntentRouter, LocalIntentDecision
from core.local_micro_classifier import LocalMicroClassifier
from core.symbiotic_delegation_policy import SymbioticDelegationPolicy
from core.classifier_shadow_bridge import ClassifierShadowBridge
from core.process_envelope_contract import ProcessEnvelopeContract
from core.reflex_shadow_evaluator import ReflexShadowEvaluator
from core.reflex_promotion_gate import ReflexPromotionGate
from core.minimal_neural_layer import MinimalNeuralLayer
from cognition.dream_mode import DreamMode
from cognition.evolution_option_queue import EvolutionOptionQueue
from cognition.morning_brief import MorningBrief


DEBUG_MODE = os.getenv("GREYS_DEBUG_OUTPUT") == "1"
logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO)
from core.fast_path_reflex_gate import FastPathReflexGate

logger = logging.getLogger("GreysV3-Main")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_LOG = PROJECT_ROOT / "assets" / "memory" / "iafa_audit.log"
DEFAULT_SKILLS_DIR = PROJECT_ROOT / "src" / "skills"
DEFAULT_IAFA_WEIGHTS = {"O": 0.1, "M": 0.2, "P": 0.3, "V": 0.2, "K": 0.2, "R": -0.4, "I": -0.3, "N": -0.2, "A": 0.8}
DEFAULT_INTERNAL_CONTEXT = {"O": 0.9, "M": 0.9, "P": 0.9, "V": 0.9, "K": 0.9, "A": 0.8}
DEFAULT_TRANSCEIVER_TIMEOUT_SECONDS = 180


class RouteTextProtocol(Protocol):
    async def route_text(
        self,
        text: str,
        origin: str = "user",
        source_name: Optional[str] = None,
        declared_intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> TaskEnvelope: ...


class PlanProtocol(Protocol):
    async def plan(self, envelope: TaskEnvelope, max_payload_chars: int = 6000) -> Any: ...


class DispatchProtocol(Protocol):
    async def dispatch(self, plan: Any, recent_intents: Optional[list[str]] = None) -> DispatchResult: ...


class FallbackProtocol(Protocol):
    async def handle_fallback_cycle(self, dispatch_result: DispatchResult, envelope: TaskEnvelope) -> CognitiveLoopResult: ...


class GenesisProtocol(Protocol):
    async def synthesize_and_install_skill(
        self,
        intent_name: str,
        task_envelope: TaskEnvelope,
        fallback_context: dict,
    ) -> bool: ...


class SkillLoaderProtocol(Protocol):
    async def execute_skill(self, intent_name: str, context: dict) -> dict: ...


@dataclass(frozen=True)
class MainProcessResult:
    task_id: str
    stage: str
    status: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MainOrchestrator:
    """
    Trunk-level coordinator for Greys-v3.

    It wires ingestion, planning, dispatch, fallback UI, safe skill synthesis,
    and hot-reloaded execution behind one typed entrypoint.
    """

    def __init__(
        self,
        ingestion_router: RouteTextProtocol,
        planner: PlanProtocol,
        dispatcher: DispatchProtocol,
        cognitive_orchestrator: FallbackProtocol,
        genesis_engine: GenesisProtocol,
        skill_loader: SkillLoaderProtocol,
        auditor: IafaAuditor,
        stress_guard: Optional[SystemStressGuard] = None,
        tension_ledger: Optional[SemanticTensionLedger] = None,
        failure_ledger: Optional[IngestionFailureLedger] = None,
        genesis_analysis: Optional[GenesisAnalysis] = None,
        skill_reviewer: Optional[SkillCandidateReview] = None,
        skill_promoter: Optional[SkillPromotionGate] = None,
        experimental_promoter: Optional[SkillExperimentalPromoter] = None,
        dream_mode: Optional[DreamMode] = None,
        option_queue: Optional[EvolutionOptionQueue] = None,
        dependency_ledger: Optional[DependencyReviewLedger] = None,
        local_intent_router: Optional[LocalIntentRouter] = None,
        shadow_evaluator: Optional[ReflexShadowEvaluator] = None,
        minimal_neural_layer: Optional[MinimalNeuralLayer] = None,
        reflex_promotion_gate: Optional[ReflexPromotionGate] = None,
        local_classifier: Optional[LocalMicroClassifier] = None,
        classifier_bridge: Optional[ClassifierShadowBridge] = None,
        delegation_policy: Optional[SymbioticDelegationPolicy] = None,
        memory_dir: str = "assets/memory",
    ) -> None:
        self.memory_dir = Path(memory_dir)
        self.ingestion_router = ingestion_router
        self.planner = planner
        self.dispatcher = dispatcher
        self.cognitive_orchestrator = cognitive_orchestrator
        self.genesis_engine = genesis_engine
        self.skill_loader = skill_loader
        self.auditor = auditor
        self.iafa_engine = getattr(dispatcher, "iafa_engine", None)
        self.stress_guard = stress_guard or SystemStressGuard()
        self.tension_ledger = tension_ledger or SemanticTensionLedger(ledger_path=str(self.memory_dir / "semantic_tension_ledger.jsonl"))
        self.failure_ledger = failure_ledger or IngestionFailureLedger(ledger_path=str(self.memory_dir / "ingestion_failure_ledger.jsonl"))
        self.dependency_ledger = dependency_ledger or DependencyReviewLedger(ledger_path=str(self.memory_dir / "dependency_review_ledger.jsonl"))
        self.genesis_analysis = genesis_analysis or GenesisAnalysis(self.genesis_engine)
        self.skill_reviewer = skill_reviewer or SkillCandidateReview()
        self.skill_promoter = skill_promoter or SkillPromotionGate(
            self.skill_reviewer, 
            dependency_ledger=self.dependency_ledger
        )
        self.experimental_promoter = experimental_promoter or SkillExperimentalPromoter(self.skill_promoter)
        
        self.option_queue = option_queue or EvolutionOptionQueue()
        self.minimal_neural_layer = minimal_neural_layer or MinimalNeuralLayer(memory_dir=str(self.memory_dir))
        self.reflex_promotion_gate = reflex_promotion_gate or ReflexPromotionGate(memory_dir=str(self.memory_dir))
        self.local_classifier = local_classifier or LocalMicroClassifier()
        self.classifier_bridge = classifier_bridge or ClassifierShadowBridge(memory_dir=str(self.memory_dir))
        self.delegation_policy = delegation_policy or SymbioticDelegationPolicy(memory_dir=str(self.memory_dir))
        self.local_intent_router = local_intent_router or LocalIntentRouter(
            stress_guard=self.stress_guard,
            minimal_neural_layer=self.minimal_neural_layer,
            promotion_gate=self.reflex_promotion_gate
        )
        self.shadow_evaluator = shadow_evaluator or ReflexShadowEvaluator(memory_dir=str(self.memory_dir))
        self.contract = ProcessEnvelopeContract()
        
        # Paths para ledgers directos
        self.classifier_shadow_ledger_path = self.memory_dir / "local_classifier_shadow_ledger.jsonl"
        
        # DreamMode utiliza el transceptor del planner para reflexionar sobre los ledgers
        transceiver = getattr(planner, "transceiver", None)
        self.dream_mode = dream_mode or DreamMode(
            transceiver=transceiver,
            tension_ledger=self.tension_ledger,
            failure_ledger=self.failure_ledger,
            stress_guard=self.stress_guard,
            option_queue=self.option_queue
        )
        
        self.morning_brief = MorningBrief(
            failure_ledger=self.failure_ledger,
            tension_ledger=self.tension_ledger,
            dependency_ledger=self.dependency_ledger
        )
        self.response_manager = ResponseManager()
        self.awaiting_human_feedback = False
        self.last_activity_timestamp = time.time()

    async def handle_evolutionary_doubt(self, payload: Dict[str, Any]) -> None:
        """Handles proactive doubt signals from SparkEngine."""
        proposal = payload.get("proposal", {})
        intent = proposal.get("suggested_intent")
        logger.info("DUDAS_EVOLUTIVAS_RECIBIDAS -> %s", intent)
        
        if self.auditor:
            await self.auditor.append_payload({
                "timestamp": time.time(),
                "record_type": "spark_evolutionary_doubt_received",
                "details": payload
            })

        if os.getenv("GREYS_EVOLUTION_UI_ENABLED") != "1":
            logger.info("Evolution UI disabled. Skipping dialog.")
            return

        # Convert SparkProposal to FallbackOptions
        fallback_options = FallbackOptions(
            task_id=proposal.get("task_id", "unknown_spark_task"),
            source_status="spark_reflection",
            ui_state="evolutionary_doubt",
            hypotheses=(
                FallbackHypothesis(
                    id="opt_1",
                    action_type="sandbox_code",
                    label=f"Explorar: {intent}",
                    description="Permitir que Greys investigue esta duda en el sandbox."
                ),
                FallbackHypothesis(
                    id="opt_2",
                    action_type="ask_human",
                    label="Discutir con humano",
                    description="Hablar sobre por qué surgió esta duda evolutiva."
                ),
                FallbackHypothesis(
                    id="opt_3",
                    action_type="abort",
                    label="Ignorar por ahora",
                    description="Mantener el estado actual y no profundizar."
                )
            ),
            thought_trace=proposal.get("reasoning", "")
        )

        try:
            logger.info("Showing EvolutionDialog for proactive doubt...")
            fallback_result = await self.cognitive_orchestrator.handle_evolutionary_doubt(fallback_options)
            logger.info("EvolutionDialog selection: %s", fallback_result.selected_action)

            # Si el usuario elige algo proactivo, podríamos querer ejecutarlo
            # Pero por ahora cumplimos la REGLA CRÍTICA: El usuario debe aprobar explícitamente.
            # handle_evolutionary_doubt en CognitiveOrchestrator devuelve un CognitiveLoopResult.
            # Podríamos pasar este resultado por el mismo flujo de _handle_fallback_selection.
            
            if fallback_result.selected_action != "abort":
                # Simular un plan y dispatch_result mínimos para reutilizar _handle_fallback_selection
                from types import SimpleNamespace
                fake_decision = SimpleNamespace(intent_category=intent, iafa_friction_estimates=SimpleNamespace(to_dict=lambda: {}))
                fake_plan = SimpleNamespace(
                    decision=fake_decision,
                    to_dict=lambda: {"spark_proposal": proposal, "decision": {"intent_category": intent}}
                )
                
                fake_dispatch = DispatchResult(
                    status="spark_reflection",
                    ui_state="evolutionary_doubt",
                    iafa_score=0.5,
                    threshold=0.7,
                    action="spark_reflection",
                    task_id=fallback_options.task_id,
                    details={"source": "spark_engine", "spark_proposal": proposal}
                )
                fake_envelope = TaskEnvelope.from_text(
                    text=f"Spark reflection on {intent}",
                    origin="spark_engine",
                    declared_intent="evolutionary_reflection"
                )
                
                # Registramos la duda en el ledger para que sea rastreable ANTES de handle_fallback_selection
                self._register_tension_event(fake_envelope.task_id, "evolutionary_doubt", {
                    "plan": {"decision": proposal},
                    "dispatch_result": {"iafa_score": 0.5, "status": "spark_reflection"}
                })
                
                logger.info("Routing Spark selection: %s", fallback_result.selected_action)
                final_result = await self._handle_fallback_selection(
                    fake_envelope, fake_plan, fake_dispatch, fallback_result
                )
                logger.info("Spark selection execution result: %s", final_result.status)
            else:
                logger.info("User dismissed evolutionary doubt.")

        except Exception as exc:
            logger.error("Failed to handle evolutionary doubt UI: %s", exc, exc_info=True)

    @classmethod
    async def create_default(cls, memory_dir: str = "assets/memory") -> "MainOrchestrator":
        m_dir = Path(memory_dir)
        timeout = int(os.getenv("GREYS_OLLAMA_TIMEOUT", str(DEFAULT_TRANSCEIVER_TIMEOUT_SECONDS)))
        host = os.getenv("GREYS_OLLAMA_URL", "http://127.0.0.1:11434")
        stress_guard = SystemStressGuard()
        tension_ledger = SemanticTensionLedger(ledger_path=str(m_dir / "semantic_tension_ledger.jsonl"))
        failure_ledger = IngestionFailureLedger(ledger_path=str(m_dir / "ingestion_failure_ledger.jsonl"))
        transceiver = IafaTransceiver(host=host, timeout_seconds=timeout, stress_guard=stress_guard)
        auditor = IafaAuditor(str(DEFAULT_AUDIT_LOG), os.getenv("GREYS_AUDIT_SECRET", "secreto_seguro"))
        sandbox = GenesisSandbox(auditor)
        ingestion_router = IngestionRouter(auditor=auditor)
        planner = LLMPlanner(transceiver, auditor)
        iafa_engine = IAFAEngine(weights=DEFAULT_IAFA_WEIGHTS, bias=0.1)
        dispatcher = ActionDispatcher(
            iafa_engine,
            auditor=auditor,
            threshold=0.7,
            internal_context=DEFAULT_INTERNAL_CONTEXT,
        )
        fallback_engine = EvolutionaryFallbackEngine(transceiver, auditor)
        cognitive_orchestrator = CognitiveOrchestrator(
            fallback_engine=fallback_engine,
            auditor=auditor,
            dispatcher=dispatcher,
            genesis_sandbox=sandbox,
        )
        genesis_engine = GenesisEngine(
            transceiver=transceiver,
            sandbox=sandbox,
            auditor=auditor,
            skills_directory=str(DEFAULT_SKILLS_DIR),
        )
        genesis_analysis = GenesisAnalysis(genesis_engine)
        skill_reviewer = SkillCandidateReview()
        # Nota: DependencyReviewLedger también debería usar m_dir
        dep_ledger = DependencyReviewLedger(ledger_path=str(m_dir / "dependency_review_ledger.jsonl"))
        skill_promoter = SkillPromotionGate(skill_reviewer, dependency_ledger=dep_ledger)
        experimental_promoter = SkillExperimentalPromoter(skill_promoter)
        skill_loader = DynamicSkillLoader(skills_directory=str(DEFAULT_SKILLS_DIR))
        
        # Configurar allowlist experimental si está habilitada
        if os.getenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED") == "1":
            allowlist_str = os.getenv("GREYS_EXPERIMENTAL_SKILL_ALLOWLIST", "")
            if allowlist_str:
                allowlist = {s.strip() for s in allowlist_str.split(",") if s.strip()}
                skill_loader.set_allowlist(allowlist)
                logger.info("Experimental skills ENABLED with allowlist: %s", allowlist)
            else:
                logger.warning("Experimental skills enabled but allowlist is empty.")
        
        option_queue = EvolutionOptionQueue()
        minimal_neural_layer = MinimalNeuralLayer(memory_dir=str(m_dir))
        reflex_promotion_gate = ReflexPromotionGate(memory_dir=str(m_dir))
        local_classifier = LocalMicroClassifier()
        classifier_bridge = ClassifierShadowBridge(memory_dir=str(m_dir))
        delegation_policy = SymbioticDelegationPolicy(memory_dir=str(m_dir))
        fast_path_gate = FastPathReflexGate(memory_dir=str(m_dir))
        local_intent_router = LocalIntentRouter(
            stress_guard=stress_guard,
            minimal_neural_layer=minimal_neural_layer,
            promotion_gate=reflex_promotion_gate,
            fast_path_gate=fast_path_gate
        )
        shadow_evaluator = ReflexShadowEvaluator(memory_dir=str(m_dir))
        
        dream_mode = DreamMode(
            transceiver=transceiver,
            tension_ledger=tension_ledger,
            failure_ledger=failure_ledger,
            stress_guard=stress_guard,
            option_queue=option_queue
        )

        return cls(
            ingestion_router=ingestion_router,
            planner=planner,
            dispatcher=dispatcher,
            cognitive_orchestrator=cognitive_orchestrator,
            genesis_engine=genesis_engine,
            skill_loader=skill_loader,
            auditor=auditor,
            stress_guard=stress_guard,
            tension_ledger=tension_ledger,
            failure_ledger=failure_ledger,
            genesis_analysis=genesis_analysis,
            skill_reviewer=skill_reviewer,
            skill_promoter=skill_promoter,
            experimental_promoter=experimental_promoter,
            dream_mode=dream_mode,
            option_queue=option_queue,
            local_intent_router=local_intent_router,
            minimal_neural_layer=minimal_neural_layer,
            shadow_evaluator=shadow_evaluator,
            reflex_promotion_gate=reflex_promotion_gate,
            local_classifier=local_classifier,
            classifier_bridge=classifier_bridge,
            delegation_policy=delegation_policy,
            memory_dir=memory_dir
        )

    async def process_input(self, raw_text: str) -> MainProcessResult:
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ValueError("raw_text must be a non-empty string")

        self.last_activity_timestamp = time.time()
        declared_intent = "human_feedback" if self.awaiting_human_feedback else None
        if self.awaiting_human_feedback:
            logger.info("ESPERANDO_FEEDBACK_HUMANO -> procesando la siguiente entrada")
            self.awaiting_human_feedback = False

        try:
            envelope = await self.ingestion_router.route_text(
                raw_text,
                declared_intent=declared_intent,
            )
            return await self.process_envelope(envelope)
        except (
            IngestionRouterError,
            LLMPlannerError,
            ActionDispatcherError,
            CognitiveLoopError,
            GenesisEngineError,
            SkillLoaderError,
        ) as exc:
            return self._error_result("process_input", raw_text, exc)
        except Exception as exc:
            return self._error_result("process_input", raw_text, exc)

    async def process_envelope(self, envelope: TaskEnvelope) -> MainProcessResult:
        """
        Orquesta el ciclo completo (Plan -> Dispatch -> Execute) para un sobre ya ingerido.
        """
        self.last_activity_timestamp = time.time()
        start_time_ms = time.time() * 1000.0
        classifier_pred = None
        
        # 1. Validación de Contrato Estructural (NUEVO)
        v_res = self.contract.validate_envelope(envelope)
        if not v_res.valid:
            # Forzamos ValueError con info de contrato para que el clasificador lo atrape
            return self._error_result("process_envelope", str(envelope), ValueError(self.contract.summarize_contract_failure(v_res)), envelope=envelope)

        # 0. Fast-Path Bypass (Mielinizado)
        try:
            fast_decision = self.local_intent_router.check_fast_path(envelope, start_time_ms)
            if fast_decision and fast_decision.matched:
                from cognition.llm_planner import CognitivePlan, CognitiveDecision, IafaFrictionEstimates, CognitiveExecutionPayload
                plan = CognitivePlan(
                    task_id=envelope.task_id,
                    thought_trace=f"Fast-Path Match: {fast_decision.reason}",
                    raw_response_sha256="fast_path_determinism",
                    decision=CognitiveDecision(
                        intent_category=fast_decision.intent_category,
                        proposed_action=fast_decision.proposed_action,
                        iafa_friction_estimates=IafaFrictionEstimates(R=0.01, I=0.01, N=0.01),
                        execution_payload=CognitiveExecutionPayload(
                            target_path=fast_decision.execution_payload.get("target_path", "n/a"),
                            extracted_tags=tuple(fast_decision.execution_payload.get("tags", ())),
                            message_key=fast_decision.execution_payload.get("message_key")
                        )
                    )
                )
                dispatch_result = await self.dispatcher.dispatch(plan)
                self._register_tension_event(envelope.task_id, "dispatch", {
                    "plan": plan.to_dict(),
                    "dispatch_result": dispatch_result.to_dict()
                })
                
                details = dispatch_result.details.copy() if dispatch_result.details else {}
                if dispatch_result.action == "respond" and dispatch_result.status == "executed":
                    payload = plan.decision.execution_payload
                    payload_dict = payload.to_dict() if hasattr(payload, "to_dict") else payload
                    response_text = self.response_manager.generate_response(
                        plan.decision.intent_category,
                        envelope.payload.value or "",
                        payload_dict
                    )
                    details["response_text"] = response_text

                # No evaluamos sombras ni delegación si es fast-path
                return MainProcessResult(
                    task_id=envelope.task_id,
                    stage="completed_fast_path",
                    status="completed",
                    details=details
                )
        except Exception as exc:
            logger.error("Fast-Path check failed: %s", exc)
        
        # Symbiotic Delegation Policy (Dry Run)
        try:
            task_type = "chat" if envelope.source_type == "text" else "ingestion"
            val = envelope.payload.value or ""
            complexity = 0.8 if len(val) > 100 or "?" in val else 0.2
            # Heurística temporal de estrés (asume check_stress o similar si no existe is_under_stress)
            host_stress_val = 1.0 if (hasattr(self.stress_guard, "is_under_stress") and self.stress_guard.is_under_stress()) or (hasattr(self.stress_guard, "check_stress") and self.stress_guard.check_stress().get("is_stressed")) else 0.0
            llm_latency_risk = 0.5
            
            signature_val = getattr(envelope.payload, "hash", None) or str(hash(val))[:16]
            self.delegation_policy.assess_task(
                task_signature=signature_val,
                task_type=task_type,
                complexity_score=complexity,
                host_stress=host_stress_val,
                llm_latency_risk=llm_latency_risk,
                active_reflex_exists=False,
                ambiguity_margin=1.0,
                evidence_score=0.5
            )
        except Exception as e:
            logger.error(f"Delegation policy assessment failed: {e}")
            
        try:
            # 1. Rutéo determinístico local
            local_decision = self.local_intent_router.route_envelope(envelope)
            
            # --- SHADOW MODE: Micro-Clasificador Local ---
            if os.getenv("GREYS_LOCAL_CLASSIFIER_SHADOW_ENABLED") == "1" and envelope.source_type == "text":
                try:
                    classifier_pred = self.local_classifier.predict_intent(envelope.payload.value)
                except Exception as exc:
                    logger.error("Local classifier prediction failed: %s", exc)
            # ---------------------------------------------------

            if local_decision.matched and local_decision.bypass_llm:
                logger.info("Local decision matched: %s (reason: %s)", local_decision.intent_category, local_decision.reason)
                
                # Transformar decisión local en un 'plan' compatible para el despachador
                from cognition.llm_planner import CognitivePlan, CognitiveDecision, IafaFrictionEstimates, CognitiveExecutionPayload
                
                # Heurística: Las decisiones locales tienen fricción mínima
                plan = CognitivePlan(
                    task_id=envelope.task_id,
                    thought_trace=f"Local heuristic match: {local_decision.reason}",
                    raw_response_sha256="local_determinism",
                    decision=CognitiveDecision(
                        intent_category=local_decision.intent_category,
                        proposed_action=local_decision.proposed_action,
                        iafa_friction_estimates=IafaFrictionEstimates(R=0.01, I=0.01, N=0.01),
                        execution_payload=CognitiveExecutionPayload(
                            target_path=local_decision.execution_payload.get("target_path", "n/a"),
                            extracted_tags=tuple(local_decision.execution_payload.get("tags", ())),
                            message_key=local_decision.execution_payload.get("message_key")
                        )
                    )
                )
            else:
                # 2. Flujo LLM tradicional (respetando ExternalChannelGate internamente)
                plan = await self.planner.plan(envelope)

            # 2b. Validar contrato del Plan (NUEVO)
            plan_v = self.contract.validate_plan_result(plan)
            if not plan_v.valid:
                raise ValueError(f"Planner contract failure: {self.contract.summarize_contract_failure(plan_v)}")

            dispatch_result = await self.dispatcher.dispatch(plan)
            
            # 2c. Validar contrato del Despacho (NUEVO)
            dispatch_v = self.contract.validate_dispatch_result(dispatch_result)
            if not dispatch_v.valid:
                raise ValueError(f"Dispatcher contract failure: {self.contract.summarize_contract_failure(dispatch_v)}")
        
            # --- SHADOW MODE: Evaluación de Reflejos (NUEVO) ---
            if os.getenv("GREYS_REFLEX_SHADOW_ENABLED") == "1":
                try:
                    # Firma básica del input
                    input_sig = envelope.payload.value[:100] if envelope.source_type == "text" else envelope.payload.mime_type
                    
                    # Consultar capa neural (sombra)
                    context = {"trigger_signature": input_sig, "mode": "shadow"}
                    suggestion = self.minimal_neural_layer.match_pattern(context)
                    
                    # Evaluar contra la ruta real
                    self.shadow_evaluator.evaluate(
                        input_signature=input_sig,
                        real_route=dispatch_result.action,
                        minimal_layer_suggestion=suggestion
                    )
                except Exception as exc:
                    logger.error("Shadow mode evaluation failed: %s", exc)

            if classifier_pred:
                real_intent = local_decision.intent_category if local_decision.matched else plan.decision.intent_category
                self._record_classifier_shadow(classifier_pred, real_intent, dispatch_result.action)

            # Registramos el evento base de despacho
            self._register_tension_event(envelope.task_id, "dispatch", {
                "plan": plan.to_dict(),
                "dispatch_result": dispatch_result.to_dict()
            })

            if self._needs_fallback(dispatch_result):
                fallback_result = await self.cognitive_orchestrator.handle_fallback_cycle(dispatch_result, envelope)
                return await self._handle_fallback_selection(envelope, plan, dispatch_result, fallback_result)

            details = {
                "task": envelope.to_audit_record_details(),
                "plan": plan.to_dict(),
                "dispatch_result": dispatch_result.to_dict(),
            }

            if dispatch_result.action == "respond" and dispatch_result.status == "executed":
                # Aseguramos que el payload sea accesible
                payload = plan.decision.execution_payload
                payload_dict = payload.to_dict() if hasattr(payload, "to_dict") else payload
                response_text = self.response_manager.generate_response(
                    plan.decision.intent_category,
                    envelope.payload.value or "",
                    payload_dict
                )
                details["response_text"] = response_text
            elif dispatch_result.status == "executed" and dispatch_result.action not in ["store_in_semantic_memory"]:
                # Intentar cargar y ejecutar como habilidad dinámica
                try:
                    # EVALUACIÓN DE RIESGO IAFA EXPERIMENTAL
                    # Heurística: Consultamos el estado de revisión humana si está disponible
                    review_status = self.skill_reviewer.get_candidate_status(f"skill_{dispatch_result.action}.py")
                    
                    is_allowlisted = False
                    if hasattr(self.skill_loader, "allowlist") and self.skill_loader.allowlist:
                        is_allowlisted = dispatch_result.action in self.skill_loader.allowlist

                    risk_profile = ExperimentalRiskProfile.for_skill(
                        skill_name=dispatch_result.action,
                        is_allowlisted=is_allowlisted,
                        human_review_status=review_status,
                        sandbox_safe=True 
                    )
                    
                    details["experimental_risk_profile"] = risk_profile.to_dict()
                    
                    self._register_tension_event(envelope.task_id, "experimental_iafa_evaluated", {
                        "action": dispatch_result.action,
                        "risk_profile": risk_profile.to_dict()
                    })

                    skill_context = self._build_skill_context(envelope, plan, dispatch_result, {}, {})
                    skill_context["experimental_risk_profile"] = risk_profile.to_dict()
                    
                    # Ejecución real
                    skill_result = await self.skill_loader.execute_skill(
                        dispatch_result.action, 
                        skill_context,
                        subfolder="experimental"
                    )
                    
                    details["skill_result"] = skill_result
                    if "response_text" in skill_result:
                        details["response_text"] = skill_result["response_text"]
                    
                    self._register_tension_event(envelope.task_id, "experimental_skill_invoked", {
                        "action": dispatch_result.action,
                        "status": "success"
                    })
                except Exception as exc:
                    logger.error("Failed to execute dynamic skill %s: %s", dispatch_result.action, exc)
                    self._register_tension_event(envelope.task_id, "experimental_skill_failed", {
                        "action": dispatch_result.action,
                        "error": str(exc)
                    }, exc)
                    details["response_text"] = f"La habilidad {dispatch_result.action} falló: {exc}"

            return MainProcessResult(
                task_id=envelope.task_id,
                stage="dispatch_complete",
                status=dispatch_result.status,
                details=details,
            )
        except Exception as exc:
            return self._error_result("process_envelope", envelope.payload.value, exc, envelope=envelope, classifier_pred=classifier_pred)

    async def run_interactive(self) -> None:
        logger.info("Greys escuchando por stdin. Escribe /quit para salir.")
        while True:
            try:
                line = await asyncio.to_thread(sys.stdin.readline)
            except (KeyboardInterrupt, EOFError):
                break

            if line == "":
                break

            raw_text = line.strip()
            if not raw_text:
                continue
            if raw_text.lower() in {"/quit", "quit", "exit"}:
                break

            # --- COMANDOS DE REVISIÓN DE CANDIDATOS ---
            if raw_text.startswith("/candidates"):
                candidates = self.skill_reviewer.list_candidates()
                if not candidates:
                    print("[Sistema]: No hay candidatos en cuarentena.")
                else:
                    print("\n--- Candidatos en Cuarentena ---")
                    for c in candidates:
                        print(f"- ID: {c.candidate_id} | Cap: {c.capability_signature} | Status: {c.current_status} | Dangerous: {c.dangerous_calls_detected}")
                    print("--------------------------------\n")
                continue

            if raw_text.startswith("/summarize "):
                cid = raw_text.split(" ", 1)[1].strip()
                try:
                    summary = self.skill_reviewer.summarize_candidate(cid)
                    print(f"\n--- Resumen: {cid} ---")
                    print(f"Status: {summary['status']}")
                    print(f"Hash: {summary['sha256']}")
                    print(f"Preview:\n{summary['preview']}")
                    print("------------------------\n")
                except Exception as exc:
                    print(f"[Error]: {exc}")
                continue

            if raw_text.startswith("/review "):
                # Usage: /review <id> <status> <reason>
                parts = raw_text.split(" ", 3)
                if len(parts) < 3:
                    print("[Sistema]: Uso: /review <candidate_id> <status> [reason]")
                    continue
                cid, status = parts[1], parts[2]
                reason = parts[3] if len(parts) > 3 else None
                try:
                    self.skill_reviewer.mark_candidate_status(cid, status, reason)
                    print(f"[Sistema]: Candidato {cid} marcado como {status}")
                    
                    # Registrar tensión semántica
                    outcome_map = {
                        "rejected_by_human": "rejected",
                        "approved_for_future_promotion": "approved_for_future_review",
                        "unsafe_rejected": "rejected",
                        "needs_dependency": "needs_dependency"
                    }
                    user_outcome = outcome_map.get(status, "reviewed")
                    
                    # Registramos el outcome para el task_id asociado al candidato si existiera, 
                    # o simplemente un evento nuevo de revisión.
                    self._register_tension_event(f"review_{cid[:8]}", "human_candidate_review", {
                        "analysis": {"recommendation": reason or status, "sandbox_status": status != "unsafe_rejected"},
                        "user_outcome": user_outcome
                    })
                except Exception as exc:
                    print(f"[Error]: {exc}")
                continue

            if raw_text.startswith("/approve-evolution "):
                oid = raw_text.split(" ", 1)[1].strip()
                try:
                    self.option_queue.mark_status(oid, "approved")
                    print(f"[Sistema]: Opción de evolución {oid} APROBADA para futuro micro-sprint.")
                except Exception as exc:
                    print(f"[Error]: {exc}")
                continue

            if raw_text.startswith("/promotion-dry-run "):
                # Usage: /promotion-dry-run <id> <stage>
                parts = raw_text.split(" ", 2)
                if len(parts) < 3:
                    print("[Sistema]: Uso: /promotion-dry-run <candidate_id> <stage>")
                    continue
                cid, stage = parts[1], parts[2]
                try:
                    result = self.skill_promoter.dry_run_promote(cid, stage)
                    print(f"\n--- Resultado Dry-Run: {cid} ---")
                    print(f"Status: {result['status']}")
                    print(f"Can Promote: {result['can_promote']}")
                    print(f"Blockers: {result['blockers']}")
                    print("--------------------------------\n")
                except Exception as exc:
                    print(f"[Error]: {exc}")
                continue

            if raw_text.startswith("/promotion"):
                # Usage: /promotion [candidate_id]
                parts = raw_text.split(" ", 1)
                if len(parts) == 1:
                    candidates = self.skill_promoter.reviewer.list_candidates()
                    if not candidates:
                        print("[Sistema]: No hay candidatos para evaluar promoción.")
                    else:
                        print("\n--- Evaluación de Promoción (Dry-Run) ---")
                        for c in candidates:
                            assessment = self.skill_promoter.assess_candidate(c.candidate_id)
                            status_icon = "✅" if assessment.can_promote else "❌"
                            print(f"{status_icon} ID: {c.candidate_id} | Can Promote: {assessment.can_promote} | Risk: {assessment.risk_level}")
                        print("------------------------------------------\n")
                else:
                    cid = parts[1].strip()
                    try:
                        assessment = self.skill_promoter.assess_candidate(cid)
                        print(f"\n--- Assessment: {cid} ---")
                        print(f"Can Promote: {assessment.can_promote}")
                        print(f"Risk Level: {assessment.risk_level}")
                        print(f"Blockers: {assessment.blockers}")
                        print(f"Recommendation: {assessment.recommendation}")
                        print("--------------------------\n")
                    except Exception as exc:
                        print(f"[Error]: {exc}")
                continue

            if raw_text.startswith("/promote-experimental "):
                cid = raw_text.split(" ", 1)[1].strip()
                try:
                    result = await self.experimental_promoter.promote_to_experimental(cid)
                    if result["status"] == "success":
                        print(f"[Sistema]: {result['message']}")
                        print(f"Destino: {result['target_path']} | Rollback: {'Sí' if result['rollback_available'] else 'No'}")
                    else:
                        print(f"[Sistema]: Promoción bloqueada para {cid}:")
                        for b in result.get("blockers", []):
                            print(f"  - {b}")
                except Exception as exc:
                    print(f"[Error]: {exc}")
                continue

            # --- COMANDOS DE PROMOCIÓN DE REFLEJOS (NUEVO) ---
            if raw_text.startswith("/reflex-candidates"):
                patterns = self.minimal_neural_layer.patterns
                ctx_frame = self.shadow_evaluator.context_engine.build_context_frame(target="reflex_promotion_audit")
                if not patterns:
                    print("[Sistema]: No hay patrones destilados para evaluar.")
                else:
                    print("\n--- Candidatos a Reflejo Local ---")
                    for p in patterns:
                        pid = p.get("pattern_id")
                        assessment = self.reflex_promotion_gate.assess_pattern_for_promotion(pid, ctx_frame)
                        status_icon = "✅" if assessment.promotion_allowed else "❌"
                        active = " [ACTIVO]" if pid in self.reflex_promotion_gate.get_active_reflexes() else ""
                        print(f"{status_icon} ID: {pid} | {p.get('pattern_name')}{active} | Agreement: {assessment.agreement_rate*100}% | Risk: {assessment.risk_score}")
                    print("----------------------------------\n")
                continue

            if raw_text.startswith("/reflex-review "):
                parts = raw_text.split(" ", 1)
                if len(parts) < 2:
                    print("[Sistema]: Uso: /reflex-review <pattern_id>")
                    continue
                pid = parts[1].strip()
                try:
                    ctx_frame = self.shadow_evaluator.context_engine.build_context_frame(target="reflex_promotion_audit")
                    assessment = self.reflex_promotion_gate.assess_pattern_for_promotion(pid, ctx_frame)
                    print(f"\n--- Revisión de Reflejo: {pid} ---")
                    print(f"Nombre: {assessment.pattern_name}")
                    print(f"Agreement Rate: {assessment.agreement_rate*100}%")
                    print(f"Context Score: {assessment.context_score*100}%")
                    print(f"Risk Score: {assessment.risk_score}")
                    print(f"Can Promote: {'SÍ' if assessment.promotion_allowed else 'NO'}")
                    if not assessment.promotion_allowed:
                        print(f"Bloqueadores: {assessment.reason_summary}")
                    print("----------------------------------\n")
                except Exception as exc:
                    print(f"[Error]: {exc}")
                continue

            if raw_text.startswith("/reflex-approve "):
                parts = raw_text.split(" ", 2)
                if len(parts) < 2:
                    print("[Sistema]: Uso: /reflex-approve <pattern_id> [reason]")
                    continue
                pid = parts[1].strip()
                reason = parts[2] if len(parts) > 2 else "Aprobado manualmente por operador."
                if self.reflex_promotion_gate.approve_promotion(pid, reason):
                    print(f"[Sistema]: Reflejo {pid} APROBADO y ACTIVADO para ruteo local.")
                else:
                    print(f"[Error]: No se pudo registrar la aprobación para {pid}")
                continue

            if raw_text.startswith("/reflex-disable "):
                parts = raw_text.split(" ", 2)
                if len(parts) < 2:
                    print("[Sistema]: Uso: /reflex-disable <pattern_id> [reason]")
                    continue
                pid = parts[1].strip()
                reason = parts[2] if len(parts) > 2 else "Desactivado manualmente por operador."
                if self.reflex_promotion_gate.disable_reflex(pid, reason):
                    print(f"[Sistema]: Reflejo {pid} DESACTIVADO.")
                else:
                    print(f"[Error]: No se pudo registrar la desactivación para {pid}")
                continue

            if any(cmd in raw_text for cmd in ["GREYS_", "python src/main.py", "export ", "ollama run", "cd /"]):
                print("Eso parece un comando de terminal. Escríbelo fuera de Greys o usa /quit para salir.")
                continue

            result = await self.process_input(raw_text)
            if "response_text" in result.details:
                print(f"\n[Greys]: {result.details['response_text']}\n")
            
            if os.getenv("GREYS_DEBUG_OUTPUT") == "1":
                logger.info("Main result: %s", result.to_dict())
            else:
                # En modo usuario limpio, solo logueamos a nivel DEBUG
                logger.debug("Main result: %s", result.to_dict())
                if result.status == "error":
                    print(f"[Sistema]: Ocurrió un error al procesar tu entrada: {result.details.get('error', 'Error desconocido')}")

    async def _handle_fallback_selection(
        self,
        envelope: TaskEnvelope,
        plan: Any,
        dispatch_result: DispatchResult,
        fallback_result: CognitiveLoopResult,
    ) -> MainProcessResult:
        outcome = fallback_result.selected_action
        self.tension_ledger.mark_user_outcome(envelope.task_id, "rejected" if outcome == "abort" else outcome)

        if fallback_result.selected_action == "abort":
            return MainProcessResult(
                task_id=envelope.task_id,
                stage="aborted",
                status=fallback_result.status,
                details=self._fallback_details(envelope, plan, dispatch_result, fallback_result),
            )

        if fallback_result.selected_action == "ask_human":
            self.awaiting_human_feedback = True
            return MainProcessResult(
                task_id=envelope.task_id,
                stage="awaiting_human_feedback",
                status=fallback_result.status,
                details=self._fallback_details(envelope, plan, dispatch_result, fallback_result),
            )

        if fallback_result.selected_action == "sandbox_code":
            intent_name = self._resolve_skill_intent(plan, envelope)
            capability_sig = f"{intent_name}"
            
            # Realizamos SOLO análisis, no instalación
            analysis_result = await self.genesis_analysis.analyze_missing_capability(
                capability_sig, envelope, self._build_genesis_context(envelope, plan, dispatch_result, fallback_result)
            )
            
            # Registramos el evento de análisis en el ledger
            self._register_tension_event(envelope.task_id, "genesis_sandbox_analysis", {
                "plan": plan.to_dict() if hasattr(plan, "to_dict") else {},
                "dispatch_result": dispatch_result.to_dict(),
                "analysis": analysis_result.to_dict()
            })
            
            status = "analysis_complete" if analysis_result.sandbox_status else "analysis_rejected"
            return MainProcessResult(
                task_id=envelope.task_id,
                stage="genesis_analysis",
                status=status,
                details={
                    "analysis": analysis_result.to_dict(),
                    "message": analysis_result.recommendation,
                    "quarantine_note": "Candidato guardado en assets/quarantine/ (NO instalado)"
                },
            )

        return MainProcessResult(
            task_id=envelope.task_id,
            stage="aborted",
            status="unknown_selection_aborted",
            details=self._fallback_details(envelope, plan, dispatch_result, fallback_result),
        )

    @staticmethod
    def _needs_fallback(dispatch_result: DispatchResult) -> bool:
        return dispatch_result.ui_state == "evolutionary_doubt" or dispatch_result.status.endswith("_fallback")

    @staticmethod
    def _resolve_skill_intent(plan: Any, envelope: TaskEnvelope) -> str:
        candidate = getattr(getattr(plan, "decision", None), "intent_category", None) or envelope.declared_intent or "generated_skill"
        return MainOrchestrator._sanitize_intent_name(candidate)

    @staticmethod
    def _sanitize_intent_name(intent_name: str) -> str:
        normalized_chars = []
        for character in intent_name.strip().lower():
            normalized_chars.append(character if (character.isalnum() or character == "_") else "_")
        normalized = "".join(normalized_chars).strip("_")
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        if not normalized:
            return "generated_skill"
        if normalized[0].isdigit():
            normalized = f"intent_{normalized}"
        return normalized

    @staticmethod
    def _build_genesis_context(
        envelope: TaskEnvelope,
        plan: Any,
        dispatch_result: DispatchResult,
        fallback_result: CognitiveLoopResult,
    ) -> Dict[str, Any]:
        return {
            "task": envelope.to_audit_record_details(),
            "plan": plan.to_dict() if hasattr(plan, "to_dict") else {},
            "dispatch_result": dispatch_result.to_dict(),
            "fallback_result": fallback_result.to_dict(),
        }

    @staticmethod
    def _build_skill_context(
        envelope: TaskEnvelope,
        plan: Any,
        dispatch_result: DispatchResult,
        fallback_result: Any,
        genesis_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        context = {
            "task": envelope.to_llm_safe_dict(),
            "task_details": envelope.to_audit_record_details(),
            "plan": plan.to_dict() if hasattr(plan, "to_dict") else plan,
            "dispatch_result": dispatch_result.to_dict() if hasattr(dispatch_result, "to_dict") else dispatch_result,
            "fallback_result": fallback_result.to_dict() if hasattr(fallback_result, "to_dict") else fallback_result,
            "genesis_context": genesis_context,
        }

        # Inject target_path from ingestion metadata if present
        meta = envelope.metadata
        ingestion = meta.get("ingestion", {})
        if "source_path" in ingestion:
            context["target_path"] = ingestion["source_path"]

        return context

    @staticmethod
    def _fallback_details(
        envelope: TaskEnvelope,
        plan: Any,
        dispatch_result: DispatchResult,
        fallback_result: CognitiveLoopResult,
    ) -> Dict[str, Any]:
        return {
            "task": envelope.to_audit_record_details(),
            "plan": plan.to_dict() if hasattr(plan, "to_dict") else {},
            "dispatch_result": dispatch_result.to_dict(),
            "fallback_result": fallback_result.to_dict(),
        }

    def _register_ingestion_failure(self, task_id: str, failure_type: str, details: Dict[str, Any], exc: Optional[Exception] = None):
        """Registra un fallo de ingestión en el ledger de fallos."""
        snapshot = self.stress_guard.get_stress_snapshot()
        
        # Obtenemos info del sobre (si está en details)
        task = details.get("task", {})
        plan = details.get("plan", {})
        decision = plan.get("decision", {}) if isinstance(plan, dict) else {}
        
        intent = decision.get("intent_category") or task.get("declared_intent") or "unknown"
        action = decision.get("proposed_action") or "unknown"
        mime_type = task.get("payload_mime_type", "application/octet-stream")
        
        failure_event = IngestionFailureEvent(
            event_id=f"fail_{os.urandom(4).hex()}",
            timestamp=time.time(),
            source="main_orchestrator",
            task_id=task_id,
            source_type=task.get("source_type", "text"),
            payload_mime_type=mime_type,
            payload_size_bytes=task.get("payload_size_bytes", 0),
            payload_sha256=task.get("payload_sha256", ""),
            declared_intent=task.get("declared_intent"),
            detected_intent=intent,
            proposed_action=action,
            failure_type=failure_type,
            failure_stage=details.get("stage", "process_input"),
            error_type=exc.__class__.__name__ if exc else "UnknownError",
            error_summary=str(exc) if exc else "No error summary",
            supported_actions=details.get("dispatch_result", {}).get("supported_actions", ["store_in_semantic_memory", "respond"]),
            missing_capability_signature=f"{intent}:{action}",
            suggested_skill_category=IngestionFailureLedger.suggest_category(intent, action, mime_type),
            host_under_stress=snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"],
            iafa_score=details.get("dispatch_result", {}).get("iafa_score", 0.0) if isinstance(details.get("dispatch_result"), dict) else 0.0
        )
        self.failure_ledger.append_failure(failure_event)

    def _register_tension_event(self, task_id: str, event_type: str, details: Dict[str, Any], exc: Optional[Exception] = None):
        """Registra un evento de tensión en el ledger."""
        snapshot = self.stress_guard.get_stress_snapshot()
        
        # Extraemos info del plan si existe
        plan = details.get("plan", {})
        if hasattr(plan, "decision"):
            decision = plan.decision
        else:
            decision = plan.get("decision", {}) if isinstance(plan, dict) else {}
        
        intent = getattr(decision, "intent_category", None) or decision.get("intent_category", "unknown")
        action = getattr(decision, "proposed_action", None) or decision.get("proposed_action", details.get("action", "unknown"))
        
        friction_obj = getattr(decision, "iafa_friction_estimates", None)
        if hasattr(friction_obj, "to_dict"):
            friction = friction_obj.to_dict()
        else:
            friction = decision.get("iafa_friction_estimates", {}) if isinstance(decision, dict) else {}
        
        # Si hay info de análisis, la metemos en notes de forma legible
        notes = str(exc) if exc else ""
        analysis = details.get("analysis")
        if analysis:
            notes = f"Analysis: {analysis.get('recommendation')} | Safe: {analysis.get('sandbox_status')}"

        event = SemanticTensionEvent(
            event_id=f"main_{os.urandom(4).hex()}",
            timestamp=time.time(),
            source="main_orchestrator",
            event_type=event_type,
            task_id=task_id,
            intent_category=intent,
            proposed_action=action,
            proposal_signature=f"{intent}:{action}",
            iafa_score=details.get("dispatch_result", {}).get("iafa_score", 0.0) if isinstance(details.get("dispatch_result"), dict) else 0.0,
            friction_R=friction.get("R", 0.0),
            friction_I=friction.get("I", 0.0),
            friction_N=friction.get("N", 0.0),
            host_under_stress=snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"],
            host_load_1m=snapshot["load_1m"],
            available_memory_mb=snapshot["mem_available_mb"],
            tension_tau=self.tension_ledger.compute_tensions(
                event_type, 
                snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"],
                friction
            ),
            capacity_A=self.tension_ledger.compute_capacity(
                snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"],
                details.get("dispatch_result", {}).get("iafa_score", 0.5) if isinstance(details.get("dispatch_result"), dict) else 0.5
            ),
            damage_delta=0.4 if event_type in ["timeout", "error"] else 0.0,
            notes=notes
        )
        self.tension_ledger.append_event(event)

    def _record_classifier_shadow(self, prediction: LocalClassifierPrediction, real_intent: str, real_action: str):
        """Registra la predicción del clasificador en modo sombra y genera candidatos."""
        try:
            # Mapping de granularidad para v0 (comparar familias de intención)
            intent_map = {"greeting": "chat", "help": "chat", "status": "chat", "identity": "chat"}
            effective_pred = intent_map.get(prediction.predicted_intent, prediction.predicted_intent)
            
            ledger_entry = {
                "event_id": f"cls_{os.urandom(4).hex()}",
                "timestamp": time.time(),
                "input_signature": prediction.input_signature,
                "predicted_intent": prediction.predicted_intent,
                "confidence": prediction.confidence,
                "real_intent": real_intent,
                "real_route": real_action,
                "agreement_with_router": effective_pred == real_intent,
                "classifier_version": prediction.classifier_version,
                "schema_version": "local-classifier-shadow.v2"
            }
            
            self.classifier_shadow_ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.classifier_shadow_ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(ledger_entry) + "\n")

            # --- CLASSIFIER BRIDGE: Generar candidato shadow si aplica ---
            self.classifier_bridge.build_candidate_from_prediction(prediction)
            
        except Exception as exc:
            logger.error("Failed to record classifier shadow result: %s", exc)

    def _error_result(self, stage: str, raw_text: str, exc: Exception, envelope: Optional[TaskEnvelope] = None, classifier_pred: Optional[LocalClassifierPrediction] = None) -> MainProcessResult:
        error_msg = str(exc)
        friendly_response = None
        
        classification = FailureClassifier.classify_exception(exc, {"stage": stage})
        event_type = classification.failure_type
        
        if isinstance(exc, LlmTimeoutError):
            logger.error("LLM Timeout at %s: %s", stage, exc)
            friendly_response = "El cerebro profundo (LLM) no respondió a tiempo. Estoy operando en modo local."
        elif isinstance(exc, LlmCircuitOpenError):
            logger.warning("LLM Circuit Open at %s", stage)
            friendly_response = "El acceso al LLM está temporalmente pausado por fallos técnicos. Usando respuesta básica."
        elif isinstance(exc, LlmHostStressedError):
            logger.warning("LLM Host Stressed at %s", stage)
            friendly_response = "El sistema está bajo mucha carga. He pausado las funciones pesadas para protegerme."
        elif isinstance(exc, LlmConnectionError):
            logger.error("LLM Connection error at %s: %s", stage, exc)
            friendly_response = "No puedo conectar con el motor LLM. Por favor, verifica Ollama."
        elif isinstance(exc, LlmError):
            logger.error("LLM General error at %s: %s", stage, exc)
            friendly_response = "Hubo un inconveniente con el motor LLM. Intentando respuesta local."
        else:
            logger.exception("Main orchestrator failure at %s: %s", stage, event_type)
            
        task_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()[:12]
        task_id = f"task_error_{task_hash}"
        
        # Intentar respuesta local si es un error LLM
        if friendly_response and self.response_manager:
            # Si era un chat, podemos intentar generar una respuesta real basada en keywords
            if stage == "process_input":
                fallback_ans = self.response_manager.generate_response("chat", raw_text)
                if fallback_ans and "Entendí tu mensaje, pero aún estoy" not in fallback_ans:
                    friendly_response = f"{friendly_response}\n\n[Respuesta Local]: {fallback_ans}"

        result = MainProcessResult(
            task_id=task_id,
            stage="error",
            status="error",
            details={
                "stage": stage,
                "error_type": exc.__class__.__name__,
                "error": error_msg,
                "response_text": friendly_response or f"Lo siento, ocurrió un error interno ({stage})."
            },
        )
        
        # Shadow mode recording on error (if possible)
        if classifier_pred:
            # En caso de error, la intención real era lo que el router dijo o lo que intentábamos
            real_intent = getattr(envelope, "declared_intent", "unknown") if envelope else "unknown"
            self._record_classifier_shadow(classifier_pred, real_intent, "error")

        # Registramos tanto la tensión como el fallo de ingestión
        self._register_tension_event(task_id, event_type, result.details, exc)
        self._register_ingestion_failure(task_id, IngestionFailureLedger.classify_failure(exc, {"stage": stage}), result.details, exc)
        return result


def _parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Greys-v3 main orchestrator")
    parser.add_argument("--text", dest="text", default=None, help="Process a single input and exit")
    parser.add_argument("--file", dest="file", default=None, help="Process a file and exit")
    parser.add_argument("--experimental-skill", dest="experimental_skill", type=str, help="Manually invoke an experimental skill")
    parser.add_argument("--spark", dest="spark", action="store_true", help="Enable proactive SparkEngine pulse")
    parser.add_argument("--dream", dest="dream", action="store_true", help="Enable cognitive Dream Mode session")
    parser.add_argument("--compact-ledgers", dest="compact_ledgers", action="store_true", help="Compact and archive old ledger events")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run mode for compaction or promotion")
    parser.add_argument("--morning-brief", dest="morning_brief", action="store_true", help="Show morning summary of technical evolution options")
    parsed, remaining = parser.parse_known_args(argv)
    return parsed, remaining


def _build_dream_mode_for_cli() -> DreamMode:
    """Build only the components Dream Mode needs, without Genesis or skill loading."""
    timeout = int(os.getenv("GREYS_OLLAMA_TIMEOUT", str(DEFAULT_TRANSCEIVER_TIMEOUT_SECONDS)))
    host = os.getenv("GREYS_OLLAMA_URL", "http://127.0.0.1:11434")
    stress_guard = SystemStressGuard()
    tension_ledger = SemanticTensionLedger()
    failure_ledger = IngestionFailureLedger()
    option_queue = EvolutionOptionQueue()
    transceiver = IafaTransceiver(host=host, timeout_seconds=timeout, stress_guard=stress_guard)
    return DreamMode(
        transceiver=transceiver,
        tension_ledger=tension_ledger,
        failure_ledger=failure_ledger,
        stress_guard=stress_guard,
        option_queue=option_queue,
    )


def run_app(argv: Optional[list[str]] = None) -> int:
    cli_argv = list(sys.argv if argv is None else argv)
    parsed, qt_args = _parse_args(cli_argv[1:])

    app = QApplication([cli_argv[0], *qt_args])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    async def bootstrap() -> None:
        if parsed.morning_brief or parsed.dream or parsed.compact_ledgers or parsed.experimental_skill:
            try:
                if parsed.morning_brief:
                    print(MorningBrief().generate_brief())
                elif parsed.experimental_skill:
                    # Carga el orquestador completo para tener acceso a los cargadores
                    orchestrator = await MainOrchestrator.create_default()
                    skill_name = parsed.experimental_skill
                    file_path = parsed.file
                    
                    if not file_path:
                        print(f"\n[Experimental] Error: Se requiere --file para ejecutar '{skill_name}'\n")
                    else:
                        print(f"\n[Experimental] Invocando habilidad '{skill_name}' sobre '{file_path}'...")
                        # Contexto mínimo controlado
                        envelope = TaskEnvelope.from_text(f"Experimental call to {skill_name}", origin="user")
                        context = {
                            "target_path": file_path,
                            "source": "manual_experimental_cli"
                        }
                        
                        try:
                            # La skill_loader ya maneja la allowlist si fue configurada en create_default
                            result = await orchestrator.skill_loader.execute_skill(skill_name, context, subfolder="experimental")
                            print(f"\nResultado ({result.get('status')}):")
                            print(f"  {result.get('response_text')}\n")
                            if "metadata" in result:
                                print(f"  Metadata: {result.get('metadata')}\n")
                        except Exception as e:
                            print(f"\n[Experimental] Error en ejecución: {e}\n")
                elif parsed.compact_ledgers:
                    from core.ledger_compactor import LedgerCompactor
                    compactor = LedgerCompactor()
                    is_confirmed = os.getenv("GREYS_LEDGER_COMPACTION_CONFIRM") == "1"
                    dry_run = parsed.dry_run or not is_confirmed
                    if dry_run:
                        print("\n[LedgerCompactor] MODO DRY-RUN: Previsualizando compactación...")
                        if not is_confirmed:
                            print("Para aplicar cambios físicos, usa GREYS_LEDGER_COMPACTION_CONFIRM=1")
                    else:
                        print("\n[LedgerCompactor] EJECUTANDO COMPACTACIÓN REAL...")
                    results = compactor.run_compaction(keep_recent=200, dry_run=dry_run)
                    print("\nResultados de compactación:")
                    for ledger, res in results.items():
                        status = res.get("status")
                        if status == "skipped":
                            print(f"  - {ledger}: Omitido ({res.get('count')} eventos, bajo el umbral).")
                        elif status in ["compacted", "dry_run_ready"]:
                            prefix = "[SIMULADO] " if dry_run else ""
                            print(f"  - {ledger}: {prefix}Compactado {res.get('archived')} eventos -> {res.get('retained')} retenidos.")
                        elif status == "error":
                            print(f"  - {ledger}: ERROR: {res.get('reason')}")
                    print("\nProceso finalizado.\n")
                else:
                    max_cycles = int(os.getenv("GREYS_DREAM_MAX_CYCLES", "5"))
                    sleep_sec = int(os.getenv("GREYS_DREAM_SLEEP_SECONDS", "60"))
                    await _build_dream_mode_for_cli().run_session(max_cycles=max_cycles, sleep_seconds=sleep_sec)
            except (KeyboardInterrupt, asyncio.CancelledError):
                logger.info("Interrupción recibida, cerrando Greys...")
            except Exception:
                logger.exception("Greys dream/bootstrap failed")
            finally:
                QCoreApplication.quit()
            return

        orchestrator = await MainOrchestrator.create_default()
        
        # Integración de SparkEngine (Proactividad)
        spark_enabled = parsed.spark or os.getenv("GREYS_SPARK_ENABLED") == "1"
        spark = None

        if spark_enabled:
            logger.info("SparkEngine enabled via CLI/Env")
            # Probe de inactividad: SIEMPRE TRUE (DEBUG/TEST)
            async def idle_probe():
                return True


            spark = SparkEngine(
                auditor=orchestrator.auditor,
                planner=orchestrator.planner,
                iafa_engine=orchestrator.iafa_engine,
                orchestrator=orchestrator,
                idle_probe=idle_probe,
                pulse_interval_seconds=int(os.getenv("GREYS_SPARK_INTERVAL", "300")),
                cooldown_seconds=int(os.getenv("GREYS_SPARK_COOLDOWN", "3600")),
                enabled=True,
                dry_run=False,
                stress_guard=orchestrator.stress_guard,
                tension_ledger=orchestrator.tension_ledger,
                failure_ledger=orchestrator.failure_ledger
            )
            spark.start()
            logger.info("SparkEngine started")
        else:
            logger.info("SparkEngine disabled")

        try:
            if parsed.text is not None:
                result = await orchestrator.process_input(parsed.text)
                logger.info("Main result: %s", result.to_dict())
            elif parsed.file is not None:
                logger.info("Ingesting file: %s", parsed.file)
                try:
                    envelope = await orchestrator.ingestion_router.route_path(parsed.file)
                    
                    if envelope.payload.mime_type == "application/pdf":
                        # Tarea 4: Flujo seguro para PDF vía proceso cognitivo
                        result = await orchestrator.process_envelope(envelope)
                        logger.info("PDF process result: %s", result.to_dict())
                        if "response_text" in result.details:
                            print(f"\n[Greys]: {result.details['response_text']}\n")
                    elif envelope.payload.mime_type == "text/plain":
                        result = await orchestrator.process_input(envelope.payload.value)
                        logger.info("File process result: %s", result.to_dict())
                    else:
                        logger.warning("MIME type '%s' no tiene flujo de procesamiento automático.", envelope.payload.mime_type)
                except Exception as exc:
                    logger.error("Failed to process file: %s", exc)
                    # Registramos el fallo de forma segura
                    await orchestrator.failure_ledger.append_failure(
                        orchestrator.failure_ledger.classify_failure(exc),
                        error=exc,
                        context={"filename": os.path.basename(parsed.file), "stage": "ingestion_router"}
                    )
            else:
                await orchestrator.run_interactive()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Interrupción recibida, cerrando Greys...")
        except Exception:
            logger.exception("Greys bootstrap failed")
        finally:
            if spark:
                await spark.stop()
                logger.info("SparkEngine stopped")
            QCoreApplication.quit()

    QTimer.singleShot(0, lambda: loop.create_task(bootstrap()))
    app.aboutToQuit.connect(loop.stop)

    try:
        with loop:
            loop.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    return 0


def main() -> int:
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
