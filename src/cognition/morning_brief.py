from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from core.system_stress_guard import SystemStressGuard
from cognition.dream_mode import DREAM_JOURNAL_PATH
from cognition.evolution_option_queue import DEFAULT_OPTION_QUEUE_PATH, EvolutionOptionQueue
from cognition.evolution_option_curator import EvolutionOptionCurator, DEFAULT_CURATED_LEDGER_PATH
from core.ingestion_failure_ledger import IngestionFailureLedger
from core.semantic_tension_ledger import SemanticTensionLedger
from core.semantic_fatigue_policy import SemanticFatiguePolicy
from core.dependency_review_ledger import DependencyReviewLedger
from core.ledger_compactor import LedgerCompactor
from core.immune_quarantine_policy import ImmuneQuarantinePolicy
from cognition.semantic_dream_miner import SemanticDreamMiner
from cognition.immune_heatmap import ImmuneHeatmapEngine
from core.canonical_state_resolver import CanonicalStateResolver
from core.local_micro_classifier import LocalMicroClassifier
from core.bio_inspired_pattern_atlas import BioInspiredPatternAtlas
from core.symbiotic_delegation_policy import SymbioticDelegationPolicy
from core.quorum_promotion_readiness import QuorumPromotionReadiness, QuorumEvidence
from core.classifier_shadow_soak import ClassifierShadowSoakEvaluator
from core.fast_path_reflex_gate import FastPathReflexGate
from core.classifier_shadow_bridge import ClassifierShadowBridge
from core.reflex_promotion_gate import ReflexPromotionGate
from core.reflex_shadow_evaluator import ReflexShadowEvaluator
from core.intrusive_signal_policy import IntrusiveSignalPolicy
from core.local_narrative_layer import LocalNarrativeLayer
from core.minimal_neural_layer import MinimalNeuralLayer
from cognition.deepseek_experience_distiller import DeepseekExperienceDistiller
from core.local_ledger_cache import LocalLedgerCache

from core.multidimensional_context import MultidimensionalContextEngine
from core.unknown_failure_reconciler import UnknownFailureReconciler

logger = logging.getLogger("MorningBrief")

TAXONOMY_TIMESTAMP = 1780495971.0

class MorningBrief:
    """
    Genera un resumen ejecutivo del aprendizaje nocturno (Dream Mode)
    y presenta las opciones evolutivas curadas.
    """

    def __init__(
        self,
        journal_path: str = DREAM_JOURNAL_PATH,
        option_queue_path: str = DEFAULT_OPTION_QUEUE_PATH,
        curated_ledger_path: str = DEFAULT_CURATED_LEDGER_PATH,
        failure_ledger: IngestionFailureLedger = None,
        tension_ledger: SemanticTensionLedger = None,
        dependency_ledger: DependencyReviewLedger = None,
        memory_dir: str = "assets/memory",
        skills_dir: str = "src/skills"
    ):
        self.journal_path = Path(journal_path)
        self.option_queue_path = Path(option_queue_path)
        self.queue = EvolutionOptionQueue(queue_path=str(self.option_queue_path))
        self.curator = EvolutionOptionCurator(queue=self.queue, curated_path=curated_ledger_path)
        self.failure_ledger = failure_ledger or IngestionFailureLedger(ledger_path=str(Path(memory_dir) / "ingestion_failure_ledger.jsonl"))
        self.tension_ledger = tension_ledger or SemanticTensionLedger(ledger_path=str(Path(memory_dir) / "semantic_tension_ledger.jsonl"))
        self.dependency_ledger = dependency_ledger or DependencyReviewLedger(ledger_path=str(Path(memory_dir) / "dependency_review_ledger.jsonl"))
        self.compactor = LedgerCompactor(memory_dir=memory_dir)
        self.immune_policy = ImmuneQuarantinePolicy()
        self.immune_ledger_path = Path(memory_dir) / "immune_quarantine_ledger.jsonl"
        self.semantic_miner = SemanticDreamMiner(
            ledger_path=str(Path(memory_dir) / "semantic_principle_ledger.jsonl")
        )
        self.heatmap_engine = ImmuneHeatmapEngine(memory_dir=memory_dir, skills_dir=skills_dir)
        self.state_resolver = CanonicalStateResolver(memory_dir=memory_dir, skills_dir=skills_dir)
        self.distiller = DeepseekExperienceDistiller(memory_dir=memory_dir)
        self.neural_layer = MinimalNeuralLayer(memory_dir=memory_dir)
        self.shadow_evaluator = ReflexShadowEvaluator(memory_dir=memory_dir)
        self.signal_policy = IntrusiveSignalPolicy()
        self.narrative = LocalNarrativeLayer()
        self.context_engine = MultidimensionalContextEngine()
        self.promotion_gate = ReflexPromotionGate(memory_dir=memory_dir)
        self.local_classifier = LocalMicroClassifier()
        self.classifier_bridge = ClassifierShadowBridge(memory_dir=memory_dir)
        self.classifier_soak = ClassifierShadowSoakEvaluator(memory_dir=memory_dir)
        self.delegation_policy = SymbioticDelegationPolicy(memory_dir=memory_dir)
        self.fast_path_gate = FastPathReflexGate(memory_dir=memory_dir)
        self.quorum_readiness = QuorumPromotionReadiness(memory_dir=memory_dir)
        self.classifier_shadow_path = Path(memory_dir) / "local_classifier_shadow_ledger.jsonl"
        self.bio_atlas = BioInspiredPatternAtlas()
        self.ledger_cache = LocalLedgerCache(memory_dir=memory_dir)
        
        reco_path = Path(memory_dir) / "unknown_failure_reconciliation_ledger.jsonl"
        self.reconciler = UnknownFailureReconciler(taxonomy_timestamp=TAXONOMY_TIMESTAMP, reconciliation_path=str(reco_path))

    def generate_brief(self) -> str:
        """Construye el resumen en texto plano para el usuario."""
        all_journal_entries = self._load_journal()
        historical_entries, last_session_entries = self._split_journal_sessions(all_journal_entries)
        
        # Ejecutar curaduría antes de mostrar
        self.curator.curate_and_save()
        curated_options = self.curator.load_curated_pending()
        recent_failures = self.failure_ledger.load_recent(limit=100)
        recent_tension = self.tension_ledger.load_recent(limit=200)
        pending_dependencies = self.dependency_ledger.get_pending_reviews()
        approved_dependencies = self.dependency_ledger.get_approved_dependencies()
        
        # Cargar historia compactada si existe
        historical_failures = self.compactor.load_compact_summaries(self.failure_ledger.ledger_path.name)
        
        # 1. Minería Semántica Automática (Si está habilitada)
        if os.getenv("GREYS_SEMANTIC_DREAM_ENABLED") == "1":
            immune_evals = self._load_immune_state()
            self.semantic_miner.run_semantic_mining_session(recent_failures, recent_tension, immune_evals)
            
        semantic_principles = self.semantic_miner.load_historical_principles(limit=5)
        
        # 2. Mapas de Calor Inmunológicos
        heatmap_reports = self.heatmap_engine.generate_all_reports()
        
        fatigue_state = self.tension_ledger.fatigue_policy.get_fatigue_state(recent_tension)
        immune_state = self._load_immune_state()
        
        brief = []
        brief.append("=" * 40)
        brief.append("  MORNING BRIEF - GREYS-V3")
        brief.append("=" * 40)
        
        # --- ÚLTIMA SESIÓN ---
        if last_session_entries:
            brief.append(f"\nÚltima sesión nocturna ({len(last_session_entries)} ciclos):")
            
            # Estadísticas de la última sesión
            suppressed = len([e for e in last_session_entries if e.get("next_action") == "suppress"])
            if suppressed:
                should_continue = os.getenv("GREYS_DREAM_CONTINUE_ON_SUPPRESS") == "1"
                status = "Continuado (Rotación de foco)" if should_continue else "Sesión finalizada"
                brief.append(f"  - Se suprimieron {suppressed} ciclos por redundancia ({status}).")

            # Focos explorados en la última sesión
            foci = [e.get("topic") for e in last_session_entries if e.get("topic")]
            if len(set(foci)) > 1:
                brief.append(f"  - Focos explorados: {', '.join(list(dict.fromkeys(foci)))}")
            elif foci:
                brief.append(f"  - Foco dominante: {foci[0]}")

            local_only = len([
                e for e in last_session_entries
                if e.get("mode") == "local_only" or (e.get("local_reflection") or {}).get("local_only")
            ])
            if local_only:
                brief.append(f"  - Degradó a modo local-only en {local_only} ciclo(s).")

            llm_timeouts = len([e for e in last_session_entries if e.get("event_type") == "dream_llm_timeout"])
            if llm_timeouts:
                brief.append(f"  - Timeout LLM registrados: {llm_timeouts}.")

            llm_parse_errors = len([e for e in last_session_entries if e.get("event_type") == "dream_llm_parse_error"])
            if llm_parse_errors:
                brief.append(f"  - Errores de parseo JSON registrados: {llm_parse_errors}.")

            no_new_evidence_list = [
                e for e in last_session_entries
                if e.get("no_new_evidence") or e.get("next_action") == "no_new_evidence"
            ]
            no_new_evidence_count = len(no_new_evidence_list)
            if no_new_evidence_count:
                should_continue = os.getenv("GREYS_DREAM_CONTINUE_ON_NO_NEW_EVIDENCE") == "1"
                status = "Continuado (Mantenimiento Idle)" if should_continue else "Sesión finalizada"
                brief.append(f"  - Ciclos sin evidencia nueva: {no_new_evidence_count} ({status}).")
            
            max_depth = max((e.get("depth_level", 0) for e in last_session_entries), default=0)
            brief.append(f"  - Nivel máximo de profundidad alcanzado: {max_depth}")

            last_res = last_session_entries[-1].get("next_action", "completed")
            brief.append(f"  - Estado final: {last_res}")

            last_reflection = last_session_entries[-1].get("llm_reflection") or last_session_entries[-1].get("local_reflection", {})
            if last_reflection:
                brief.append(f"  - Conclusión: {last_reflection.get('summary', 'Sin resumen available.')}")
        
        # --- RESUMEN HISTÓRICO ---
        if historical_entries:
            total_h = len(all_journal_entries)
            suppressed_h = len([e for e in all_journal_entries if e.get("next_action") == "suppress"])
            brief.append(f"\nEstadísticas Históricas:")
            brief.append(f"  - Ciclos acumulados: {total_h}")
            brief.append(f"  - Supresiones históricas: {suppressed_h}")
            
        if not all_journal_entries:
            brief.append("\n[Sistema]: No se encontraron reflexiones nocturnas recientes.")

        # Preparar contadores de fallo (siempre inicializados)
        failure_counts = {}
        if recent_failures:
            # Agrupar y resolver estado canónico de fallos recientes
            for f in recent_failures:
                ftype = getattr(f, "failure_type", "unknown_failure")
                failure_counts[ftype] = failure_counts.get(ftype, 0) + 1
            
            if failure_counts:
                brief.append(f"\nÚltimos {len(recent_failures)} eventos registrados:")
                
                # Desglose de process_envelope
                pe_failures = [f for f in recent_failures if getattr(f, "failure_stage", "") == "process_envelope"]
                if pe_failures:
                    brief.append("\n  [Desglose Process Envelope]:")
                    pe_counts = {}
                    for f in pe_failures:
                        ft = getattr(f, "failure_type", "unknown_failure_process_envelope")
                        pe_counts[ft] = pe_counts.get(ft, 0) + 1
                    
                    for ft, count in sorted(pe_counts.items(), key=lambda x: x[1], reverse=True):
                        brief.append(f"    * {ft}: {count}")

                brief.append("\n  [Top 5 Fallos Generales]:")
                
                # --- RECONCILIACIÓN DE DEUDA UNKNOWN ---
                reclassifications = self.reconciler.load_all_reclassifications()
                unknown_events = [f for f in recent_failures if getattr(f, "failure_type", "") == "unknown_failure"]
                
                historical_unknown = 0
                post_taxonomy_unknown = 0
                reconciled_breakdown = {}
                
                for f in unknown_events:
                    fid = getattr(f, "event_id")
                    t_val = getattr(f, "timestamp", 0.0)
                    if t_val < TAXONOMY_TIMESTAMP:
                        historical_unknown += 1
                    else:
                        post_taxonomy_unknown += 1
                    
                    if fid in reclassifications:
                        rtype = reclassifications[fid].inferred_failure_type
                        reconciled_breakdown[rtype] = reconciled_breakdown.get(rtype, 0) + 1
                    else:
                        # Reclasificar al vuelo si no está en el ledger derivado
                        reco = self.reconciler.reconcile_event(f.__dict__ if hasattr(f, "__dict__") else f)
                        if reco:
                            reconciled_breakdown[reco.inferred_failure_type] = reconciled_breakdown.get(reco.inferred_failure_type, 0) + 1
                
                if unknown_events:
                    brief.append("\n  [Reconciliación de Deuda Unknown]:")
                    brief.append(f"    - Deuda Histórica: {historical_unknown}")
                    status_marker = "[ALERTA]" if post_taxonomy_unknown > 0 else "[OK]"
                    brief.append(f"    - Unknown Post-Taxonomía: {post_taxonomy_unknown} {status_marker}")
                    if reconciled_breakdown:
                        brief.append("    - Inferencias derivadas de la deuda:")
                        for rtype, count in sorted(reconciled_breakdown.items(), key=lambda x: x[1], reverse=True):
                            brief.append(f"      * {rtype}: {count}")

                for ftype, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    canon = self.state_resolver.resolve_failure_family_state(ftype)
                    status_label = ""
                    if canon.canonical_status == "active_failure":
                        status_label = " [ACTIVO]"
                    elif canon.canonical_status == "recent_debt":
                        status_label = " [DEUDA RECIENTE]"
                    elif canon.canonical_status == "historical_debt":
                        status_label = " [HISTÓRICO]"
                    
                    details = ""
                    if ftype.startswith("unknown_failure"):
                        # Desglose de unknown_failure por etapa o tipo de error si es posible
                        unclassified = [f for f in recent_failures if getattr(f, "failure_type", "").startswith("unknown_failure") or getattr(f, "failure_type", "") == ftype]
                        stages = {}
                        for f in unclassified:
                            stage = getattr(f, "failure_stage", "unknown_stage")
                            stages[stage] = stages.get(stage, 0) + 1
                        
                        if stages:
                            top_stage, stage_count = sorted(stages.items(), key=lambda x: x[1], reverse=True)[0]
                            details = f" (Principal etapa: {top_stage})"
                            if top_stage == "process_envelope":
                                details += " [Sugerencia: Sprint Process Envelope Triage]"
                            elif top_stage == "dispatch":
                                details += " [Sugerencia: Sprint Dispatcher Debug]"
                        
                    brief.append(f"    * {ftype}: {count}{status_label}{details}")

        if historical_failures:
            total_archived = sum(s.get("archived_event_count", 0) for s in historical_failures)
            brief.append(f"\nHistoria Archivada ({total_archived} eventos previos):")
            # Agregamos tipos de fallo históricos
            hist_failure_types = {}
            for s in historical_failures:
                for ftype, count in s.get("failure_type_counts", {}).items():
                    hist_failure_types[ftype] = hist_failure_types.get(ftype, 0) + count
            
            for ftype, count in sorted(hist_failure_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                brief.append(f"  * {ftype}: {count} (histórico)")

        # Estado de fatiga
        if fatigue_state["top_fatigued_families"]:
            brief.append(f"\nEstado de Fatiga Semántica:")
            for ftype, damage in fatigue_state["top_fatigued_families"]:
                brief.append(f"  * {ftype}: {damage:.2f} daño (decadencia aplicada)")
            
            if fatigue_state["critical_unsuppressed"]:
                brief.append(f"\n  [!] Señales Críticas Activas (no suprimidas):")
                for c in fatigue_state["critical_unsuppressed"]:
                    brief.append(f"      - {c}")
                    
        # Sistema Inmune
        if immune_state:
            brief.append(f"\nSistema Inmune / Corte Sano (Dry-Run):")
            levels = {1: "Observación", 2: "Validación", 3: "Inmunológica"}
            for level in [3, 2, 1]:
                items = [i for i in immune_state if i.get("recommended_quarantine_level") == level]
                if items:
                    brief.append(f"  Nivel {level} ({levels[level]}):")
                    for i in items:
                        brief.append(f"    * {i.get('item_id')} -> {i.get('recommended_action')}")
                        if i.get("reason_summary"):
                            brief.append(f"      [{i.get('reason_summary')}]")

        # Evolución Semántica
        if semantic_principles:
            brief.append(f"\nEvolución del Entendimiento Semántico:")
            for p in semantic_principles:
                brief.append(f"\n  Principio: {p.principle_name}")
                brief.append(f"  Dimensión: {p.context_dimension}")
                brief.append(f"  Interpretación: {p.interpretation_summary}")
                brief.append(f"  Aplicación: {p.suggested_application}")
                brief.append(f"  Confianza: {p.confidence:.2f}")

        # Mapas de Calor
        if heatmap_reports:
            brief.append(f"\nMapa de Calor Inmunológico:")
            for r in heatmap_reports:
                hist = ", ".join(r.dominant_historical_hotspots)
                recent = ", ".join(r.dominant_recent_hotspots)
                
                if hist or recent:
                    brief.append(f"  * {r.title}:")
                    if hist: brief.append(f"    - Histórico: {hist}")
                    if recent: brief.append(f"    - Reciente: {recent}")
                    
                    # Mostrar tendencias de los hotspots recientes
                    for rh in r.dominant_recent_hotspots:
                        cell = next((c for c in r.cells if c.axis_x == rh), None)
                        if cell and cell.trend_label != "stable":
                            brief.append(f"      [!] Tendencia {rh}: {cell.trend_label}")
                            
                    brief.append(f"    Foco: {r.recommended_focus}")

        # Estado de Dependencias (Genérico)
        if pending_dependencies:
            brief.append(f"\nEstado de Dependencias:")
            for d in pending_dependencies[:3]:
                brief.append(f"  * [!] {d.dependency_name} (PENDIENTE de revisión)")

        # Estado de Capacidades PDF (Refinado)
        brief.append("\nEstado de Capacidades PDF:")
        pypdf_state = self.state_resolver.resolve_dependency_state("pypdf")
        pdf_skill_state = self.state_resolver.resolve_skill_state("pdf_reader_basic")
        
        if pypdf_state.canonical_status == "approved_installed":
            brief.append("  * [DISPONIBLE] Lector PDF experimental instalado.")
        else:
            brief.append(f"  * [ALERTA] Dependencia pypdf: {pypdf_state.canonical_status}")

        if pdf_skill_state.canonical_status == "active_experimental":
            brief.append("  * [ACTIVO] Runtime PDF autorizado por allowlist.")
        elif pdf_skill_state.canonical_status == "disabled_by_global_config":
            brief.append("  * [INACTIVO] Runtime desactivado por configuración global.")
        elif pdf_skill_state.canonical_status == "disabled_by_allowlist":
            brief.append("  * [INACTIVO] Runtime desactivado por allowlist (pdf_reader_basic ausente).")

        # Última ejecución PDF
        pdf_events = [f for f in recent_failures if "pdf" in getattr(f, "payload_mime_type", "").lower() or "pdf" in getattr(f, "failure_type", "").lower()]
        if pdf_events:
            last_pdf = pdf_events[-1]
            brief.append(f"  * Última actividad PDF: {last_pdf.failure_type} (Metadata: {last_pdf.payload_size_bytes} bytes)")
        
        # Destilación de Experiencia DeepSeek
        distilled_patterns = self.distiller.load_distilled_patterns(limit=5)
        if distilled_patterns:
            brief.append("\nDestilación de Experiencia DeepSeek / Núcleo Local:")
            for p in distilled_patterns:
                human_label = " [REQUIERE REVISIÓN]" if p.requires_human_review else ""
                local_label = " (Puede ser Heurística)" if p.can_become_local_heuristic else ""
                brief.append(f"  * Patrón: {p.pattern_name}{human_label}")
                brief.append(f"    - Aplicación: {p.target_module}{local_label}")
                brief.append(f"    - Motivo: {p.local_rule_summary}")

        # Traducción de Alertas / Señales Intrusivas
        # Identificar señales para evaluar
        signals_to_assess = []
        # Fallos recurrentes o críticos
        for ftype in failure_counts:
            if ftype in ["llm_timeout", "host_stress_block", "unsafe_code_detected"]:
                signals_to_assess.append((ftype, "failure_ledger"))
        # Cuarentena nivel 3
        immune_evals = self._load_immune_state()
        for e in immune_evals:
            if e.get("recommended_quarantine_level", 0) >= 3:
                signals_to_assess.append(("candidate_unsafe", "immune_policy"))
                
        if signals_to_assess:
            brief.append("\nTraducción de Alertas / Señales Intrusivas:")
            seen_sigs = set()
            for stype, src in signals_to_assess:
                if stype in seen_sigs: continue
                seen_sigs.add(stype)
                
                assessment = self.signal_policy.assess_signal(stype, src, stype)
                narrative_res = self.narrative.explain_signal(stype)
                
                exe_label = "SÍ" if assessment.should_execute else "NO"
                q_label = "SÍ" if assessment.should_quarantine else "NO"
                
                brief.append(f"  * Señal: {stype} [{assessment.signal_type.upper()}]")
                brief.append(f"    - Resumen: {narrative_res.user_facing_summary}")
                brief.append(f"    - Técnico: {narrative_res.technical_summary}")
                brief.append(f"    - Acción: {assessment.recommended_action} -> {narrative_res.recommended_next_step}")
                brief.append(f"    - Ejecutar: {exe_label} | Cuarentena: {q_label} | Severidad: {narrative_res.severity.upper()}")

        # Evaluación en Sombra de Reflejos
        shadow_stats = self.shadow_evaluator.summarize_performance()
        if shadow_stats.get("total_evaluations", 0) > 0:
            brief.append("\nEvaluación en Sombra de Reflejos (Reflex Kernel):")
            brief.append(f"  * Observaciones totales: {shadow_stats['total_evaluations']}")
            brief.append(f"  * Tasa de coincidencia (Agreement): {shadow_stats['agreement_rate']*100}%")
            
            classes = shadow_stats.get("classifications", {})
            if "missing_pattern" in classes:
                brief.append(f"  * [!] Intenciones sin reflejo destilado: {classes['missing_pattern']}")
            
            if shadow_stats["risky_suggestions_count"] > 0:
                brief.append(f"  * [ALERTA] Sugerencias de alto riesgo: {shadow_stats['risky_suggestions_count']}")
                
            if classes.get("candidate_for_promotion", 0) > 0:
                brief.append(f"  * [OK] Candidatos para promoción activa: {classes['candidate_for_promotion']}")
            
            if shadow_stats["agreement_rate"] > 0.85:
                brief.append("  * RECOMENDACIÓN: El núcleo local es altamente confiable. Considerar activar ruteo autónomo.")
            else:
                brief.append("  * RECOMENDACIÓN: Mantener modo sombra para calibrar reflejos faltantes.")

        # Marco de Contexto Arquitectónico
        ctx_frame = self.context_engine.build_context_frame(target="autonomous_evolution_readiness")
        brief.append("\nMarco de Contexto Arquitectónico:")
        
        dims = [
            ("Entorno", ctx_frame.environment_context),
            ("Flujos", ctx_frame.flow_context),
            ("Humano", ctx_frame.human_context),
            ("Temporal", ctx_frame.temporal_context),
            ("Reglas", ctx_frame.constraint_context)
        ]
        
        # Encontrar dimensión más débil
        weakest = min(dims, key=lambda x: x[1].score)
        
        for name, dim in dims:
            status_label = f"[{dim.status.upper()}]" if dim.status != "stable" else "[OK]"
            brief.append(f"  * Dimensión {name}: {dim.score*100}% {status_label}")
            
        brief.append(f"  * Puntaje Contextual Global: {ctx_frame.overall_context_score*100}%")
        brief.append(f"  * Dimensión Crítica: {weakest[0]}")
        
        if ctx_frame.recommended_decision == "promote":
            brief.append("  * RECOMENDACIÓN: Contexto estable. Viable proceder con promoción de reflejos activos.")
        elif ctx_frame.recommended_decision == "block":
            brief.append(f"  * ALERTA: Bloqueo contextual detectado en {weakest[0]}. Detener evoluciones automáticas.")
        else:
            brief.append("  * RECOMENDACIÓN: Mantener observación. Calibrar dimensión crítica antes de automatizar.")

        # Madurez del Clasificador Local v1.2
        fixture_path = Path("tests/fixtures/local_classifier/synthetic_intents.json")
        matrix_data = None
        if fixture_path.exists():
            try:
                test_set = json.loads(fixture_path.read_text(encoding="utf-8"))
                matrix_data = self.local_classifier.evaluate_confusion_matrix(test_set)
            except Exception: pass

        soak_summary = self.classifier_soak.summarize_performance()
        has_shadow_data = self.classifier_shadow_path.exists()

        if matrix_data or soak_summary.total_candidates > 0 or has_shadow_data:
            brief.append("\nMadurez del Clasificador Local (Kernel Inmune):")
            
            if matrix_data:
                brief.append(f"  * Exactitud Balanceada (Sintético): {matrix_data['balanced_accuracy']*100}%")
                brief.append(f"  * Salud unknown_safe: {matrix_data['unknown_safe_rate']*100}%")
                if matrix_data.get("overconfidence_warning"):
                    brief.append("  * [ALERTA] Sobreconfianza detectada en dataset sintético.")
                
                conf = matrix_data.get("confusion_pairs", {})
                if conf:
                    brief.append(f"  * Pares de confusión: {', '.join([f'{k}({v})' for k,v in sorted(conf.items(), key=lambda x: x[1], reverse=True)[:2]])}")

            if soak_summary.total_candidates > 0:
                brief.append(f"  * Estabilidad en Inferencia (Soak): {soak_summary.total_candidates} muestras")
                brief.append(f"  * Confianza Promedio: {soak_summary.average_confidence*100}%")
                brief.append(f"  * Salud unknown_safe (Soak): {soak_summary.unknown_safe_rate*100}%")
                brief.append(f"  * Tasa de Duplicados: {soak_summary.duplicate_rate*100}%")
                
                # Recomendación de Madurez
                rec_map = {
                    "keep_observing": "Calibración en curso. Mantener modo sombra.",
                    "strengthen_unknown_safe": "Aumentar dataset de ruido para reducir sobreconfianza.",
                    "calibrate_margins": "Ajustar umbrales de margen para mejorar separación.",
                    "ready_for_v1_design": "Criterios de madurez alcanzados. Viable para diseño de v1 con pesos."
                }
                brief.append(f"  * RECOMENDACIÓN: {rec_map.get(soak_summary.recommended_action, soak_summary.recommended_action)}")

            # Métricas de Sombra (Real)
            if has_shadow_data:
                records = self.ledger_cache.get_records(str(self.classifier_shadow_path))
                total_s = len(records)
                agreements = sum(1 for r in records if r.get("agreement_with_router"))
                
                if total_s > 0:
                    brief.append(f"  * Predicciones totales (Sombra): {total_s}")
                    brief.append(f"  * Tasa de acuerdo con Router: {round(agreements/total_s, 2)*100}%")

        # Candidatos de Reflejo (Clasificador)
        classifier_candidates = self.classifier_bridge.summarize_candidates(limit=20)
        if classifier_candidates:
            brief.append("\nCandidatos de Reflejo (Generalización):")
            
            # Deduplicación visual de unknown_safe y generalized_*
            unique_candidates = []
            counts = {} # reflex_name -> count

            for c in classifier_candidates:
                name = c.proposed_reflex_name
                counts[name] = counts.get(name, 0) + 1
                if counts[name] == 1:
                    unique_candidates.append(c)

            for c in unique_candidates:
                name = c.proposed_reflex_name
                status = "SHADOW_ONLY"
                count_info = ""
                if c.predicted_intent == "unknown_safe":
                    status = "OBSERVE_ONLY"
                
                if counts[name] > 1:
                    count_info = f" ({counts[name]} ocurrencias agrupadas)"
                
                brief.append(f"  * Patrón: {name} [{status}]{count_info}")
                brief.append(f"    - Intención: {c.predicted_intent} | Confianza: {c.confidence*100}%")
                if status == "OBSERVE_ONLY":
                    brief.append("    - NOTA: Señal de no-acción; nunca se promoverá automáticamente.")
                else:
                    brief.append("    - RECOMENDACIÓN: Calibrar en Shadow Mode mediante ShadowEvaluator.")

        # Quorum de Promoción (Dry-Run)
        brief.append("\nQuorum de Promoción / Readiness Dry-Run:")
        if classifier_candidates:
            # Re-usar unique_candidates para evitar spam visual en Quorum
            for c in unique_candidates:
                name = c.proposed_reflex_name
                evidence = [
                    QuorumEvidence(
                        source="classifier_bridge", evidence_type="proposal",
                        candidate_id=c.candidate_id, signal_count=1, unique_signal_count=1,
                        duplicate_count=0, confidence=c.confidence, temporal_span_hours=1.0,
                        risk_score=c.risk_score, context_score=ctx_frame.overall_context_score,
                        human_approval_present=False, rollback_available=True
                    )
                ]
                
                assessment = self.quorum_readiness.assess_candidate(c.candidate_id, "reflex_proposal", evidence)
                
                status_color = assessment.readiness_state.upper()
                count_info = f" (Agrupado)" if counts[name] > 1 else ""
                brief.append(f"  * Candidato: {name} [{status_color}]{count_info}")
                brief.append(f"    - Readiness Score: {assessment.quorum_readiness_score} | Riesgo Falso Quorum: {assessment.false_quorum_risk*100}%")
                brief.append(f"    - RECOMENDACIÓN: {assessment.recommended_action} ({assessment.reason_summary})")
                brief.append("    - NOTA: Promoción real bloqueada por política dry-run.")
        else:
            brief.append("  * No hay candidatos recientes con suficiente quórum para evaluación.")

        # Promoción Supervisada de Reflejos
        patterns = self.neural_layer.patterns
        if patterns:
            brief.append("\nPromoción Supervisada de Reflejos:")
            active_ids = self.promotion_gate.get_active_reflexes()
            
            # Deduplicación visual por pattern_name
            pattern_groups = {}
            for p in patterns:
                name = p.get("pattern_name", "unknown")
                if name not in pattern_groups:
                    pattern_groups[name] = []
                pattern_groups[name].append(p)

            for name, group in pattern_groups.items():
                p = group[0] # Usar el primero como base
                pid = p.get("pattern_id")
                assessment = self.promotion_gate.assess_pattern_for_promotion(pid, ctx_frame)
                
                status_label = "SHADOW"
                if pid in active_ids:
                    status_label = "ACTIVE_LOCAL"
                elif assessment.promotion_allowed:
                    status_label = "CANDIDATE"
                
                count_info = f" ({len(group)} señales agrupadas)" if len(group) > 1 else ""
                brief.append(f"  * Reflejo: {name} [{status_label}]{count_info}")
                
                # Promediar métricas si hay grupo
                avg_agreement = sum(self.promotion_gate._get_pattern_shadow_stats(pi.get("pattern_id"))["agreement_rate"] for pi in group) / len(group)
                brief.append(f"    - Métricas: Agreement {avg_agreement*100}% | Contexto {assessment.context_score*100}% | Riesgo {assessment.risk_score}")
                
                if status_label == "CANDIDATE":
                    brief.append(f"    - ACCIÓN: Viable para promoción activa. Usa: /reflex-approve {pid}")
                elif status_label == "SHADOW" and not assessment.promotion_allowed:
                    brief.append(f"    - BLOQUEO: {assessment.reason_summary}")

        # Memoria Local / Ledger Cache
        cache_stats = self.ledger_cache.get_stats()
        if cache_stats.files_tracked > 0:
            brief.append("\nMemoria Local / Ledger Cache:")
            brief.append(f"  * Archivos trackeados: {cache_stats.files_tracked}")
            brief.append(f"  * Lecturas estimadas ahorradas: {cache_stats.estimated_reads_saved}")
            brief.append(f"  * Aciertos de caché (Hits): {cache_stats.cache_hits}")
            brief.append(f"  * Fallos de caché (Misses): {cache_stats.cache_misses}")
            brief.append(f"  * Invalidaciones: {cache_stats.invalidations}")

        # Patrones Bioinspirados / Arquitectura Orgánica
        bio_patterns = self.bio_atlas.list_patterns()
        if bio_patterns:
            brief.append("\nPatrones Bioinspirados / Arquitectura Orgánica:")
            # Heurística: El patrón más fuerte es el que tiene más módulos asociados y está activo
            brief.append(f"  * Patrón Dominante: Basket Cell Inhibition (IAFA + IntrusiveSignalPolicy)")
            
            risks = self.bio_atlas.summarize_risks()
            if risks:
                # Mostrar el primer riesgo crítico como advertencia
                brief.append(f"  * Riesgo Orgánico: {risks[1]['danger']}")
                brief.append(f"  * Anti-patrón a vigilar: {risks[1]['anti_pattern']}")
            
            brief.append("  * RECOMENDACIÓN: Investigar Quorum Sensing para automatizar la madurez del clasificador.")

        # Delegación Simbiótica (Dry Run)
        delegation_assessments = self.delegation_policy.summarize_recent()
        if delegation_assessments:
            brief.append("\nDelegación Simbiótica / Edge Stabilization (Dry-Run):")
            brief.append(f"  * Tareas Evaluadas: {len(delegation_assessments)}")
            
            routes = {}
            for a in delegation_assessments:
                routes[a.recommended_route] = routes.get(a.recommended_route, 0) + 1
            
            for route, count in routes.items():
                brief.append(f"  * Ruta Propuesta '{route}': {count}")
                
            brief.append("  * NOTA: Política operando en modo observador. No altera ruteo real.")

        # Ruta Mielinizada / Fast-Path
        fp_metrics = self.fast_path_gate.summarize_metrics()
        if fp_metrics:
            brief.append("\nRuta Mielinizada / Fast-Path:")
            brief.append(f"  * Ejecuciones Rápidas (Hits): {fp_metrics.get('fast_path_hits', 0)}")
            brief.append(f"  * Evaluaciones Bloqueadas: {fp_metrics.get('blocks', 0)}")
            brief.append(f"  * Ahorro Estimado: {fp_metrics.get('estimated_savings_ms', 0)} ms")
            if fp_metrics.get('reflex_usage'):
                brief.append("  * Reflejos Acelerados:")
                for r_name, count in fp_metrics.get('reflex_usage', {}).items():
                    brief.append(f"    - {r_name}: {count} veces")

        if not curated_options:
            brief.append("\n[Sistema]: No hay opciones evolutivas pendientes.")
        else:
            brief.append(f"\nBandeja de Evolución Curada ({len(curated_options)} temas únicos):")
            # Mostrar top 3 por prioridad (ya vienen deduplicados por familia en load_curated_pending)
            for i, opt in enumerate(curated_options[:3], 1):
                merged_info = f" ({opt.merged_count} señales fusionadas)" if opt.merged_count > 1 else ""
                brief.append(f"\n{i}. {opt.title}{merged_info}")
                brief.append(f"   [Familia: {opt.family} | Prioridad: {opt.priority_score}]")
                brief.append(f"   Propuesta: {opt.summary}")
                brief.append(f"   Sprint sugerido: {opt.best_suggested_micro_sprint}")
                brief.append(f"   ID Curado: {opt.curated_id}")

        brief.append("\n" + "=" * 40)
        brief.append("Para aprobar una opción curada, usa:")
        brief.append("/approve-curated <curated_id>")
        brief.append("=" * 40)
        
        return "\n".join(brief)

    def _load_immune_state(self) -> List[Dict[str, Any]]:
        records = self.ledger_cache.get_records(str(self.immune_ledger_path))
        if not records: return []
        
        latest_evals = {}
        for data in records:
            latest_evals[data.get("item_id")] = data
        return list(latest_evals.values())

    def _load_journal(self) -> List[Dict[str, Any]]:
        return self.ledger_cache.get_records(str(self.journal_path))

    def _load_pending_options(self) -> List[Dict[str, Any]]:
        records = self.ledger_cache.get_records(str(self.option_queue_path))
        options = [r for r in records if r.get("status") == "pending_human_review"]
        # Ordenar por prioridad real si es posible, aquí simplificamos
        return sorted(options, key=lambda x: x.get("priority_score", 0.0), reverse=True)

    def _split_journal_sessions(self, entries: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Divide las entradas del diario en histórico y última sesión (basado en gaps de tiempo)."""
        if not entries:
            return [], []
        
        # Encontrar el gap más reciente de más de 2 horas para identificar la última sesión
        gap_threshold = 7200 # 2 horas
        split_idx = 0
        
        for i in range(len(entries) - 1, 0, -1):
            t_curr = entries[i].get("timestamp", 0)
            t_prev = entries[i-1].get("timestamp", 0)
            if t_curr - t_prev > gap_threshold:
                split_idx = i
                break
        
        return entries[:split_idx], entries[split_idx:]
