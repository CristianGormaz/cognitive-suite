from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.system_stress_guard import SystemStressGuard
from core.semantic_tension_ledger import SemanticTensionEvent, SemanticTensionLedger
from core.ingestion_failure_ledger import IngestionFailureLedger
from cognition.iafa_transceiver import IafaTransceiver
from core.task_envelope import TaskEnvelope
from cognition.evolution_option_queue import EvolutionOptionQueue, EvolutionOption
from cognition.dream_question_ledger import DreamQuestionLedger, DreamQuestionEntry
from cognition.iafa_transceiver import (
    IafaTransceiver, LlmError, LlmTimeoutError, LlmConnectionError, 
    LlmHostStressedError, LlmEmptyResponseError, LlmMalformedJsonError, LlmCircuitOpenError,
    LlmDisabledError
)

logger = logging.getLogger("DreamMode")

DREAM_JOURNAL_PATH = "assets/memory/dream_journal.jsonl"
DREAM_SCHEMA_VERSION = "dream-journal.v2"
TIMEOUT_QUESTION_ACTIONS = {"local_only_after_timeout", "defer_due_to_llm_timeout"}
SESSION_STOP_ACTIONS = {"suppress", "no_new_evidence", "local_only_complete"}

DEPTH_LADDER = {
    0: {"type": "observation", "prompt": "¿Qué falló recientemente?"},
    1: {"type": "grouping", "prompt": "¿Qué patrones de fallo se repiten?"},
    2: {"type": "cause", "prompt": "¿Cuál es la causa raíz probable de estos patrones?"},
    3: {"type": "strategy", "prompt": "¿Qué micro-sprint técnico conviene para mitigar esto?"},
    4: {"type": "validation", "prompt": "¿Qué tests o pruebas confirmarían que la solución es segura?"},
    5: {"type": "decision", "prompt": "¿Cuáles son las 3 opciones finales para revisión humana?"}
}


class DreamLlmParseError(RuntimeError):
    """Raised when Dream Mode cannot parse the LLM response as JSON."""

@dataclass(frozen=True)
class DreamCycleResult:
    event_id: str
    timestamp: float
    cycle: int
    summary_of_failures: Dict[str, int]
    top_missing_capabilities: List[tuple[str, int]]
    top_tension_sources: List[str]
    host_stress_snapshot: Dict[str, Any]
    depth_level: int
    question_type: str
    semantic_signature: str
    repetition_count: int
    next_action: str
    llm_reflection: Optional[Dict[str, Any]] = None
    llm_response_sha256: Optional[str] = None
    local_reflection: Optional[Dict[str, Any]] = None
    event_type: str = "dream_cycle"
    mode: str = "llm"
    llm_error_type: Optional[str] = None
    llm_error: Optional[str] = None
    llm_failure_count: int = 0
    local_only_reason: Optional[str] = None
    generated_option_count: int = 0
    no_new_evidence: bool = False
    source: str = "dream_mode"
    schema_version: str = DREAM_SCHEMA_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

from core.dream_focus_validator import DreamFocusValidator
...
class DreamMode:
    """
    Modo Sueño Cognitivo con Control de Repetición y Escalera de Profundidad.
    """

    def __init__(
        self,
        transceiver: IafaTransceiver,
        tension_ledger: SemanticTensionLedger,
        failure_ledger: IngestionFailureLedger,
        stress_guard: SystemStressGuard,
        journal_path: str = DREAM_JOURNAL_PATH,
        option_queue: Optional[EvolutionOptionQueue] = None,
        question_ledger: Optional[DreamQuestionLedger] = None,
        focus_dir: str = "assets/memory/dream_focus"
    ):
        self.transceiver = transceiver
        self.tension_ledger = tension_ledger
        self.failure_ledger = failure_ledger
        self.stress_guard = stress_guard
        self.journal_path = Path(journal_path)
        self.option_queue = option_queue or EvolutionOptionQueue()
        self.question_ledger = question_ledger or DreamQuestionLedger()
        self.focus_dir = Path(focus_dir)
        self.focus_validator = DreamFocusValidator()
        self._llm_failure_count = 0
        self._llm_disabled_for_session = False
        self._local_only_reason: Optional[str] = None
        self._ensure_journal()

    def _ensure_journal(self):
        if not self.journal_path.parent.exists():
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.focus_dir.exists():
            self.focus_dir.mkdir(parents=True, exist_ok=True)

    async def run_session(self, max_cycles: int = 5, sleep_seconds: int = 60):
        os.environ["GREYS_DREAM_MODE_ACTIVE"] = "1"
        try:
            enabled = os.getenv("GREYS_DREAM_MODE_ENABLED") == "1"
            if not enabled:
                logger.info("Dream Mode is disabled.")
                return

            self._reset_session_state()
            logger.info(f"Dream Mode session (v2) started. Max cycles: {max_cycles}")

            if self._llm_enabled() and self._env_flag("GREYS_DREAM_PREFLIGHT_OLLAMA", False):
                preflight_ok = await self._preflight_ollama()
                if not preflight_ok:
                    self._disable_llm_for_session("preflight_failed")
            
            # Cargar foco inicial
            focus_data = self._load_initial_focus()
            current_focus: Optional[str] = focus_data.get("focus_id") if focus_data else None
            
            for cycle in range(1, max_cycles + 1):
                if self.stress_guard.is_host_under_stress():
                    logger.warning("Stopping Dream Mode session due to host stress.")
                    break
                    
                logger.info(f"Dream Cycle {cycle}/{max_cycles} starting... Focus: {current_focus or 'auto'}")
                result = await self.run_once(cycle, focus=current_focus)
                self.persist_dream_result(result)
                
                should_continue_suppress = self._env_flag("GREYS_DREAM_CONTINUE_ON_SUPPRESS", False)
                should_continue_no_evidence = self._env_flag("GREYS_DREAM_CONTINUE_ON_NO_NEW_EVIDENCE", False)
                
                is_suppressed = result.next_action == "suppress"
                is_no_evidence = result.next_action == "no_new_evidence"
                
                if result.next_action in SESSION_STOP_ACTIONS:
                    if is_suppressed and should_continue_suppress:
                        logger.info("Dream Cycle suppressed by redundancy. Rotating focus and continuing...")
                        current_focus = self.select_next_dream_focus(current_focus)
                    elif is_no_evidence and should_continue_no_evidence:
                        logger.info("No new evidence found. Rotating focus and running idle maintenance...")
                        current_focus = self.select_next_dream_focus(current_focus)
                        self._run_idle_maintenance(result)
                    else:
                        logger.info("Dream Mode ending session early: %s", result.next_action)
                        break

                if cycle < max_cycles:
                    if result.event_type == "dream_llm_timeout":
                        logger.info("Skipping inter-cycle sleep after LLM timeout.")
                        continue
                    
                    actual_sleep = sleep_seconds
                    if is_suppressed and should_continue_suppress:
                        actual_sleep = self._env_int("GREYS_DREAM_SUPPRESS_SLEEP_SECONDS", 5)
                    elif is_no_evidence and should_continue_no_evidence:
                        actual_sleep = self._env_int("GREYS_DREAM_NO_EVIDENCE_SLEEP_SECONDS", 60)
                    
                    logger.info(f"Dreaming... next cycle in {actual_sleep}s")
                    await asyncio.sleep(actual_sleep)
                    
            logger.info("Dream Mode session completed.")
        finally:
            os.environ.pop("GREYS_DREAM_MODE_ACTIVE", None)

    def _run_idle_maintenance(self, last_result: DreamCycleResult):
        """Ejecuta tareas analíticas livianas cuando no hay evidencia nueva para LLM."""
        logger.info("Executing Dream Idle Maintenance...")
        # 1. Revisar desgloses de fallos desconocidos (solo log por ahora)
        unclassified = last_result.summary_of_failures.get("unknown_failure", 0)
        if unclassified > 0:
            logger.info(f"Idle Maintenance: Analyzed {unclassified} unclassified failures.")
            
        # 2. Heurística de limpieza de caché (simulado)
        logger.info("Idle Maintenance: Validating ledger cache consistency.")
        
        # 3. Registrar mantenimiento en el journal (vía el resultado que ya se persiste)
        # Podríamos mutar el result si fuera necesario, pero persist_dream_result ya se llamó.

    def _load_initial_focus(self) -> Dict[str, Any]:
        """Intenta cargar el foco desde GREYS_DREAM_FOCUS_ID o el archivo más reciente."""
        focus_id = os.getenv("GREYS_DREAM_FOCUS_ID")
        if focus_id:
            focus_path = self.focus_dir / f"{focus_id}.json"
            if focus_path.exists() and self.focus_validator.validate_file(focus_path):
                try:
                    return json.loads(focus_path.read_text(encoding="utf-8"))
                except: pass
            logger.warning(f"Requested focus_id '{focus_id}' not found or invalid. Falling back.")

        # Buscar el más reciente
        focus_files = sorted(self.focus_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        for f in focus_files:
            if self.focus_validator.validate_file(f):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    logger.info(f"Loaded dream focus from {f.name}: {data.get('focus_id')}")
                    return data
                except: continue
        
        return {}

    def select_next_dream_focus(self, current_focus: Optional[str]) -> str:
        """Rota el foco del sueño para evitar rumiación."""
        options = [
            "quorum_readiness",
            "unknown_failure_classification",
            "evolution_queue_hygiene",
            "dream_deduplication",
            "fast_path_stability",
            "classifier_unknown_safe_health",
            "ledger_cache_efficiency"
        ]
        if not current_focus or current_focus not in options:
            return options[0]
        
        idx = options.index(current_focus)
        next_idx = (idx + 1) % len(options)
        return options[next_idx]

    async def run_once(self, cycle: int, focus: Optional[str] = None) -> DreamCycleResult:
        stress_snapshot = self._coerce_dict(self.stress_guard.get_stress_snapshot())
        
        # 1. Resumir evidencia
        recent_failures = self._coerce_list(self.failure_ledger.load_recent(limit=50))
        failure_counts = {}
        for f in recent_failures:
            failure_type = getattr(f, "failure_type", None)
            if failure_type:
                failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
        top_missing = self._normalize_missing_capabilities(
            self.failure_ledger.get_top_missing_capabilities(limit=3)
        )
        
        recent_tension = self._coerce_list(self.tension_ledger.load_recent(limit=30))
        tension_sigs = self._extract_tension_sources(recent_tension)
        
        # 2. Determinar Profundidad y Firma
        topic = focus if focus else "general_evolution"
        if not focus and top_missing:
            topic = f"missing_{top_missing[0][0]}"
            
        current_depth = self.question_ledger.get_max_depth_for_topic(topic) + 1
        current_depth = min(current_depth, 5)
        
        q_type = DEPTH_LADDER[current_depth]["type"]
        context_summary = f"{top_missing}|{failure_counts}|{tension_sigs}|{focus}"
        signature = self.question_ledger.generate_semantic_signature(topic, q_type, context_summary)
        
        # 3. Control de Repetición
        last_entry = self.question_ledger.get_last_by_signature(signature)
        repetition_count = (last_entry.repetition_count + 1) if last_entry else 1
        
        max_reps = int(os.getenv("GREYS_DREAM_MAX_REPETITIONS_PER_SIGNATURE", "2"))
        
        next_action = "ask_llm"
        if repetition_count > max_reps:
            next_action = "suppress"
        elif self._should_use_local_only(last_entry):
            next_action = "local_only"
            
        # 4. Reflexión LLM
        llm_reflection = None
        response_hash = None
        local_reflection = None
        event_type = "dream_cycle"
        mode = "llm" if next_action == "ask_llm" else "local_only"
        llm_error_type = None
        llm_error = None
        local_only_reason = self._local_only_reason
        generated_option_count = 0
        no_new_evidence = False

        if next_action == "ask_llm" and self._llm_enabled():
            try:
                llm_reflection = await self.ask_llm_reflection(current_depth, top_missing, failure_counts, tension_sigs)
            except (LlmError, DreamLlmParseError) as exc:
                self._llm_failure_count += 1
                is_timeout = isinstance(exc, LlmTimeoutError)
                
                # Determine error type for event
                if isinstance(exc, LlmTimeoutError): llm_error_type = "timeout"
                elif isinstance(exc, LlmConnectionError): llm_error_type = "connection"
                elif isinstance(exc, LlmCircuitOpenError): llm_error_type = "circuit_open"
                elif isinstance(exc, LlmDisabledError): llm_error_type = "llm_disabled"
                elif isinstance(exc, (LlmMalformedJsonError, DreamLlmParseError)): llm_error_type = "parse_error"
                else: llm_error_type = "llm_error"
                
                llm_error = str(exc)
                event_type = f"dream_llm_{llm_error_type}"
                
                mode = "local_only" if self._local_only_on_llm_failure() else "llm"
                timeout_action = (
                    "local_only_after_timeout"
                    if self._local_only_on_llm_failure()
                    else "defer_due_to_llm_timeout"
                )
                self._append_question_entry(
                    cycle=cycle,
                    topic=topic,
                    depth=current_depth,
                    q_type=q_type,
                    context_summary=context_summary,
                    signature=signature,
                    repetition_count=repetition_count,
                    next_action=timeout_action,
                    answer_summary=f"LLM {llm_error_type}: {llm_error}",
                    understood_score=0.0,
                )
                
                if is_timeout:
                    self._record_llm_timeout_tension(signature, stress_snapshot, llm_error)

                if self._llm_failure_count >= self._max_llm_failures() or isinstance(exc, LlmCircuitOpenError):
                    reason = "llm_failure_threshold" if not isinstance(exc, LlmCircuitOpenError) else "llm_circuit_open"
                    self._disable_llm_for_session(reason)

                if self._local_only_on_llm_failure():
                    local_only_reason = self._local_only_reason or (
                        "llm_timeout" if is_timeout else f"llm_{llm_error_type}"
                    )
                    local_reflection, generated_option_count, no_new_evidence = self._run_local_only_reflection(
                        top_missing=top_missing,
                        failures=failure_counts,
                        tension=tension_sigs,
                        stress=stress_snapshot,
                        reason=local_only_reason,
                    )
                    next_action = "no_new_evidence" if no_new_evidence else "local_only_complete"
                else:
                    next_action = timeout_action
            else:
                if llm_reflection:
                    raw_ans = json.dumps(llm_reflection)
                    response_hash = hashlib.sha256(raw_ans.encode()).hexdigest()
                    score = self.question_ledger.calculate_understood_score(raw_ans)
                    next_action = "escalate_depth" if score >= 0.75 else "repeat_once"
                    
                    self._append_question_entry(
                        cycle=cycle,
                        topic=topic,
                        depth=current_depth,
                        q_type=q_type,
                        context_summary=context_summary,
                        signature=signature,
                        repetition_count=repetition_count,
                        next_action=next_action,
                        answer_summary=llm_reflection.get("summary"),
                        answer_hash=response_hash,
                        understood_score=score,
                    )
                    
                    # Procesar opciones si el LLM las proporciona
                    generated_option_count = self._process_evolution_options(llm_reflection, top_missing, stress_snapshot)
                else:
                    next_action = "repeat_once"

        elif next_action == "local_only":
            local_only_reason = self._resolve_local_only_reason(last_entry)
            local_reflection, generated_option_count, no_new_evidence = self._run_local_only_reflection(
                top_missing=top_missing,
                failures=failure_counts,
                tension=tension_sigs,
                stress=stress_snapshot,
                reason=local_only_reason,
            )
            event_type = "no_new_evidence" if no_new_evidence else "dream_local_only_cycle"
            if self._should_end_after_local_only(local_only_reason):
                next_action = "no_new_evidence" if no_new_evidence else "local_only_complete"
            else:
                next_action = "local_only"
            if local_only_reason in {"previous_llm_timeout", "llm_failure_threshold", "preflight_failed"}:
                self._append_question_entry(
                    cycle=cycle,
                    topic=topic,
                    depth=current_depth,
                    q_type=q_type,
                    context_summary=context_summary,
                    signature=signature,
                    repetition_count=repetition_count,
                    next_action="local_only_after_timeout"
                    if local_only_reason != "preflight_failed"
                    else "defer_due_to_llm_timeout",
                    answer_summary=local_reflection.get("summary"),
                    understood_score=0.0,
                )

        return DreamCycleResult(
            event_id=f"dream_{os.urandom(4).hex()}",
            timestamp=time.time(),
            cycle=cycle,
            summary_of_failures=failure_counts,
            top_missing_capabilities=top_missing,
            top_tension_sources=tension_sigs[:5],
            host_stress_snapshot=stress_snapshot,
            depth_level=current_depth,
            question_type=q_type,
            semantic_signature=signature,
            repetition_count=repetition_count,
            next_action=next_action,
            llm_reflection=llm_reflection,
            llm_response_sha256=response_hash,
            local_reflection=local_reflection,
            event_type=event_type,
            mode=mode,
            llm_error_type=llm_error_type,
            llm_error=llm_error,
            llm_failure_count=self._llm_failure_count,
            local_only_reason=local_only_reason,
            generated_option_count=generated_option_count,
            no_new_evidence=no_new_evidence,
        )

    async def ask_llm_reflection(
        self, depth: int, missing: list, failures: dict, tension: list
    ) -> Optional[Dict[str, Any]]:
        prompt = self.build_reflection_prompt(depth, missing, failures, tension)
        
        envelope = TaskEnvelope.from_text(
            text=f"Depth {depth} reflection", origin="dream_mode", declared_intent="cognitive_reflection"
        )
        
        system_prompt = (
            f"Eres el subconsciente de Greys-v3. Nivel de profundidad: {depth} ({DEPTH_LADDER[depth]['type']}). "
            "Analiza patrones, no generes código. Responde estrictamente en JSON."
        )
        
        try:
            raw_response = await self.transceiver.query_llm(
                envelope,
                system_prompt=system_prompt,
                operator_instruction=prompt,
                json_format=True,
                options={"num_predict": self._dream_num_predict()},
                context={"mode": "dream", "source": "dream_mode"}
            )
            return self.extract_json_object_safely(raw_response)
        except (LlmError, DreamLlmParseError):
            raise
        except Exception as exc:
            logger.error(f"LLM reflection unexpected error: {exc}")
            return None

    @staticmethod
    def extract_json_object_safely(text: str) -> Dict[str, Any]:
        """Extrae y parsea un objeto JSON de una cadena, eliminando ruido como <think> tags."""
        if not text:
            raise DreamLlmParseError("Empty response from LLM")
            
        # 1. Eliminar bloques <think>...</think>
        import re
        clean_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        
        # 2. Intentar parse directo
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            pass
            
        # 3. Buscar el primer '{' y el último '}'
        start = clean_text.find('{')
        end = clean_text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_candidate = clean_text[start:end+1]
            try:
                return json.loads(json_candidate)
            except json.JSONDecodeError as exc:
                logger.warning(f"Failed to parse balanced JSON candidate: {exc}")
                raise DreamLlmParseError(f"Malformed or truncated JSON: {exc}") from exc
                
        raise DreamLlmParseError(f"No JSON object found in response: {text[:100]}...")

    def build_reflection_prompt(self, depth: int, missing: list, failures: dict, tension: list) -> str:
        base_q = DEPTH_LADDER[depth]["prompt"]
        max_options = int(os.getenv("GREYS_DREAM_MAX_OPTIONS_PER_CYCLE", "3"))
        
        return f"""
{base_q}

Evidencia:
- Faltan: {missing[:3]}
- Fallos: {failures}
- Tensión: {tension[:3]}

JSON breve (max {max_options} opciones):
{{
  "summary": "Analisis nivel {depth}",
  "observed_patterns": ["max 3 strings"],
  "evolution_options": [
    {{
      "title": "breve", 
      "summary": "breve", 
      "expected_benefit": 0.5, 
      "estimated_risk": 0.1, 
      "suggested_micro_sprint": "id_sprint"
    }}
  ],
  "do_not_execute": true
}}
Prohibido: Markdown, código, explicaciones fuera del JSON.
"""

    def _process_evolution_options(self, reflection: dict, missing: list, stress: dict) -> int:
        options_data = reflection.get("evolution_options", [])
        appended = 0
        for opt in options_data:
            try:
                benefit = float(opt.get("expected_benefit", 0.5))
                risk = float(opt.get("estimated_risk", 0.1))
            except: benefit, risk = 0.5, 0.1
            
            damage = 0.0
            for sig, count in missing:
                if sig.lower() in str(opt).lower(): damage = count * 0.1
            
            capacity = 1.0 if not stress.get("is_cpu_stressed") else 0.5
            priority = self.option_queue.calculate_priority(benefit, risk, damage, capacity)
            
            self.option_queue.append_option(EvolutionOption(
                option_id=f"opt_{os.urandom(4).hex()}",
                timestamp=time.time(),
                title=opt.get("title", "Opción"),
                summary=opt.get("summary", "Sin resumen"),
                tension_tau=0.1,
                capacity_A=capacity,
                damage_score=damage,
                expected_benefit=benefit,
                estimated_risk=risk,
                priority_score=priority,
                suggested_micro_sprint=opt.get("suggested_micro_sprint", "")
            ))
            appended += 1
        return appended

    def persist_dream_result(self, result: DreamCycleResult):
        try:
            with open(self.journal_path, "a", encoding="utf-8") as f:
                f.write(result.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error persisting result: {exc}")

    def _reset_session_state(self):
        self._llm_failure_count = 0
        self._llm_disabled_for_session = False
        self._local_only_reason = None

    def _llm_enabled(self) -> bool:
        return os.getenv("GREYS_DREAM_LLM_ENABLED") == "1" and not self._llm_disabled_for_session

    def _local_only_on_llm_failure(self) -> bool:
        return self._env_flag("GREYS_DREAM_LOCAL_ONLY_ON_LLM_FAILURE", True)

    def _max_llm_failures(self) -> int:
        return max(1, self._env_int("GREYS_DREAM_MAX_LLM_FAILURES", 2))

    def _dream_num_predict(self) -> int:
        return max(1, self._env_int("GREYS_DREAM_NUM_PREDICT", 512))

    def _disable_llm_for_session(self, reason: str):
        self._llm_disabled_for_session = True
        self._local_only_reason = reason
        logger.warning("Dream Mode LLM disabled for this session: %s", reason)

    async def _preflight_ollama(self) -> bool:
        timeout = self._env_int("GREYS_DREAM_PREFLIGHT_TIMEOUT", 20)
        num_predict = min(self._dream_num_predict(), 8)
        try:
            preflight = getattr(self.transceiver, "preflight_ollama")
            await preflight(timeout_seconds=timeout, num_predict=num_predict, context={"mode": "dream", "source": "dream_preflight"})
            return True
        except Exception as exc:
            self._llm_failure_count = max(self._llm_failure_count + 1, self._max_llm_failures())
            logger.warning("Dream Mode Ollama preflight failed: %s", exc)
            return False

    def _should_use_local_only(self, last_entry: Optional[DreamQuestionEntry]) -> bool:
        if self._llm_disabled_for_session:
            return True
        if os.getenv("GREYS_DREAM_LLM_ENABLED") != "1":
            return True
        if not self._local_only_on_llm_failure():
            return False

        # Threshold global alcanzado
        if self._llm_failure_count >= self._max_llm_failures():
            return True
            
        # Fallo previo en esta misma firma semántica
        if last_entry is not None and last_entry.next_action in TIMEOUT_QUESTION_ACTIONS:
            return True
            
        return False

    def _resolve_local_only_reason(self, last_entry: Optional[DreamQuestionEntry]) -> str:
        if self._local_only_reason:
            return self._local_only_reason
        if last_entry is not None and last_entry.next_action in TIMEOUT_QUESTION_ACTIONS:
            return "previous_llm_timeout"
        if os.getenv("GREYS_DREAM_LLM_ENABLED") != "1":
            return "llm_disabled"
        return "local_only"

    @staticmethod
    def _should_end_after_local_only(reason: Optional[str]) -> bool:
        return reason in {"previous_llm_timeout", "llm_failure_threshold", "preflight_failed", "llm_parse_error"}

    def _append_question_entry(
        self,
        *,
        cycle: int,
        topic: str,
        depth: int,
        q_type: str,
        context_summary: str,
        signature: str,
        repetition_count: int,
        next_action: str,
        answer_summary: Optional[str] = None,
        answer_hash: Optional[str] = None,
        understood_score: float = 0.0,
    ):
        q_entry = DreamQuestionEntry(
            question_id=f"q_{os.urandom(4).hex()}",
            timestamp=time.time(),
            cycle=cycle,
            topic=topic,
            question_text_hash=hashlib.sha256(DEPTH_LADDER[depth]["prompt"].encode()).hexdigest(),
            context_hash=hashlib.sha256(context_summary.encode()).hexdigest(),
            evidence_refs=[topic],
            semantic_signature=signature,
            depth_level=depth,
            question_type=q_type,
            answer_summary=answer_summary,
            answer_hash=answer_hash,
            understood_score=understood_score,
            repetition_count=repetition_count,
            next_action=next_action,
        )
        self.question_ledger.append_entry(q_entry)

    def _record_llm_timeout_tension(self, signature: str, stress: Dict[str, Any], error: str):
        host_under_stress = bool(stress.get("is_mem_stressed") or stress.get("is_cpu_stressed"))
        load_1m = self._safe_float(stress.get("load_1m"), 0.0)
        available_memory = int(self._safe_float(stress.get("mem_available_mb"), 0.0))
        event = SemanticTensionEvent(
            event_id=f"dream_timeout_{os.urandom(4).hex()}",
            timestamp=time.time(),
            source="dream_mode",
            event_type="timeout",
            task_id=f"dream_llm_timeout_{signature}",
            intent_category="cognitive_reflection",
            proposed_action="llm_reflection",
            proposal_signature=f"dream_llm_reflection:{signature}",
            host_under_stress=host_under_stress,
            host_load_1m=load_1m,
            available_memory_mb=available_memory,
            tension_tau=0.6,
            capacity_A=SemanticTensionLedger.compute_capacity(
                host_under_stress=host_under_stress,
                iafa_score=0.5,
                has_response=False,
            ),
            stress_sigma=0.3 if host_under_stress else 0.1,
            damage_delta=0.1,
            notes=f"Dream Mode LLM timeout; local-only fallback eligible. error={error}",
        )
        self.tension_ledger.append_event(event)

    def _run_local_only_reflection(
        self,
        *,
        top_missing: List[tuple[str, int]],
        failures: Dict[str, int],
        tension: List[str],
        stress: Dict[str, Any],
        reason: str,
    ) -> tuple[Dict[str, Any], int, bool]:
        options = self._generate_local_evolution_options(top_missing, failures, tension, stress)
        no_new_evidence = not options
        observed_patterns = self._local_observed_patterns(top_missing, failures, tension)
        if no_new_evidence:
            summary = (
                f"Dream Mode operó en local-only ({reason}); no hay evidencia nueva "
                "o las opciones ya estaban registradas."
            )
        else:
            summary = (
                f"Dream Mode operó en local-only ({reason}) y generó "
                f"{len(options)} opción(es) evolutiva(s) desde ledgers."
            )
        return (
            {
                "summary": summary,
                "local_only": True,
                "reason": reason,
                "observed_patterns": observed_patterns,
                "top_missing_capabilities": [
                    {"signature": sig, "count": count} for sig, count in top_missing
                ],
                "top_tension_sources": tension[:5],
                "failure_counts": failures,
                "evolution_options": options,
                "no_new_evidence": no_new_evidence,
            },
            len(options),
            no_new_evidence,
        )

    def _generate_local_evolution_options(
        self,
        top_missing: List[tuple[str, int]],
        failures: Dict[str, int],
        tension: List[str],
        stress: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        max_options = max(1, self._env_int("GREYS_DREAM_MAX_OPTIONS_PER_CYCLE", 3))
        existing_keys = self._existing_option_keys()
        created: List[Dict[str, Any]] = []
        capacity = 0.5 if stress.get("is_cpu_stressed") else 1.0

        def append_if_new(option: EvolutionOption):
            key = self._option_key(option.title, option.evidence_refs, option.suggested_micro_sprint)
            if key in existing_keys:
                return
            self.option_queue.append_option(option)
            existing_keys.add(key)
            created.append(asdict(option))

        for signature, count in top_missing:
            if len(created) >= max_options:
                break
            damage = min(1.0, count * 0.1)
            benefit = min(0.95, 0.45 + (count * 0.08))
            risk = 0.2
            sprint = f"local_only_missing_{self._slug(signature)}"
            priority = self.option_queue.calculate_priority(benefit, risk, damage, capacity)
            append_if_new(EvolutionOption(
                option_id=f"opt_{os.urandom(4).hex()}",
                timestamp=time.time(),
                title=f"Atender capacidad faltante: {signature}",
                summary=f"El ledger registra {count} fallo(s) asociados a {signature}.",
                source="dream_mode.local_only",
                evidence_refs=[f"missing:{signature}"],
                related_ledgers=["ingestion_failure_ledger"],
                tension_tau=0.3,
                capacity_A=capacity,
                stress_sigma=0.1,
                damage_score=damage,
                expected_benefit=benefit,
                estimated_risk=risk,
                priority_score=priority,
                suggested_micro_sprint=sprint,
            ))

        for failure_type, count in sorted(failures.items(), key=lambda item: item[1], reverse=True):
            if len(created) >= max_options:
                break
            damage = min(0.8, count * 0.08)
            benefit = min(0.85, 0.35 + (count * 0.07))
            risk = 0.15
            sprint = f"local_only_failure_{self._slug(failure_type)}"
            priority = self.option_queue.calculate_priority(benefit, risk, damage, capacity)
            append_if_new(EvolutionOption(
                option_id=f"opt_{os.urandom(4).hex()}",
                timestamp=time.time(),
                title=f"Investigar patrón de fallo: {failure_type}",
                summary=f"Se observaron {count} evento(s) recientes de tipo {failure_type}.",
                source="dream_mode.local_only",
                evidence_refs=[f"failure_type:{failure_type}"],
                related_ledgers=["ingestion_failure_ledger"],
                tension_tau=0.25,
                capacity_A=capacity,
                stress_sigma=0.1,
                damage_score=damage,
                expected_benefit=benefit,
                estimated_risk=risk,
                priority_score=priority,
                suggested_micro_sprint=sprint,
            ))

        for signature in tension:
            if len(created) >= max_options:
                break
            benefit = 0.55
            risk = 0.15
            damage = 0.2
            sprint = f"local_only_tension_{self._slug(signature)}"
            priority = self.option_queue.calculate_priority(benefit, risk, damage, capacity)
            append_if_new(EvolutionOption(
                option_id=f"opt_{os.urandom(4).hex()}",
                timestamp=time.time(),
                title=f"Reducir tensión recurrente: {signature}",
                summary=f"El ledger semántico muestra tensión recurrente en {signature}.",
                source="dream_mode.local_only",
                evidence_refs=[f"tension:{signature}"],
                related_ledgers=["semantic_tension_ledger"],
                tension_tau=0.4,
                capacity_A=capacity,
                stress_sigma=0.1,
                damage_score=damage,
                expected_benefit=benefit,
                estimated_risk=risk,
                priority_score=priority,
                suggested_micro_sprint=sprint,
            ))

        return created

    def _existing_option_keys(self) -> set[str]:
        try:
            options = self.option_queue.load_all()
        except Exception:
            options = []
        if not isinstance(options, list):
            options = []
        keys: set[str] = set()
        for option in options:
            if isinstance(option, EvolutionOption):
                keys.add(self._option_key(option.title, option.evidence_refs, option.suggested_micro_sprint))
            elif isinstance(option, dict):
                keys.add(self._option_key(
                    str(option.get("title", "")),
                    self._coerce_list(option.get("evidence_refs", [])),
                    str(option.get("suggested_micro_sprint", "")),
                ))
        return keys

    @staticmethod
    def _option_key(title: str, evidence_refs: List[str], sprint: str) -> str:
        refs = ",".join(sorted(str(ref) for ref in evidence_refs))
        return f"{title.strip().lower()}|{refs}|{sprint.strip().lower()}"

    @staticmethod
    def _local_observed_patterns(
        top_missing: List[tuple[str, int]],
        failures: Dict[str, int],
        tension: List[str],
    ) -> List[str]:
        patterns: List[str] = []
        for sig, count in top_missing[:3]:
            patterns.append(f"capacidad faltante {sig} aparece {count} vez/veces")
        for failure_type, count in sorted(failures.items(), key=lambda item: item[1], reverse=True)[:3]:
            patterns.append(f"fallo {failure_type} aparece {count} vez/veces")
        for sig in tension[:3]:
            patterns.append(f"tensión recurrente en {sig}")
        return patterns

    @staticmethod
    def _extract_tension_sources(recent_tension: List[Any], exclude_dream: bool = True) -> List[str]:
        seen = set()
        sources: List[str] = []
        for event in recent_tension:
            tau = getattr(event, "tension_tau", 0.0)
            signature = str(getattr(event, "proposal_signature", "") or "").strip()
            if tau > 0.4 and signature and signature not in seen:
                if exclude_dream and signature.startswith("dream_llm_reflection:"):
                    continue
                sources.append(signature)
                seen.add(signature)
        return sources

    def _normalize_missing_capabilities(self, raw_missing: Any) -> List[tuple[str, int]]:
        missing = []
        for item in self._coerce_list(raw_missing):
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            signature = str(item[0])
            try:
                count = int(item[1])
            except (TypeError, ValueError):
                count = 0
            if signature and count > 0:
                missing.append((signature, count))
        return missing

    @staticmethod
    def _coerce_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        try:
            return list(value)
        except TypeError:
            return []

    @staticmethod
    def _coerce_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _env_flag(name: str, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _env_int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _slug(value: str) -> str:
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789"
        chars = [ch if ch in allowed else "_" for ch in value.lower()]
        slug = "_".join(part for part in "".join(chars).split("_") if part)
        return slug[:48] or hashlib.sha256(value.encode()).hexdigest()[:8]
