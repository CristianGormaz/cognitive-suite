from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.canonical_state_resolver import CanonicalStateResolver

logger = logging.getLogger("ImmuneHeatmap")

HEATMAP_LEDGER_VERSION = "immune-heatmap-report.v1"
DEFAULT_HEATMAP_LEDGER_PATH = "assets/memory/immune_heatmap_reports.jsonl"

@dataclass(frozen=True)
class HeatmapCell:
    axis_x: str
    axis_y: str
    historical_intensity: float # 0.0 to 1.0 (all loaded data)
    recent_intensity: float # 0.0 to 1.0 (recent window)
    value: float
    count: int
    trend_delta: float # recent - historical
    trend_label: str # rising, falling, stable, etc.
    risk_level: str # low, medium, high, critical
    evidence_refs: List[str]
    schema_version: str = "heatmap-cell.v2"

@dataclass(frozen=True)
class ImmuneHeatmapReport:
    event_id: str
    timestamp: float
    heatmap_type: str # failure_family, module_tension, candidate_iss, dependency_friction, semantic_principle
    title: str
    cells: List[HeatmapCell]
    dominant_historical_hotspots: List[str]
    dominant_recent_hotspots: List[str]
    recommended_focus: str
    generated_from_ledgers: List[str]
    schema_version: str = HEATMAP_LEDGER_VERSION

    def to_json(self) -> str:
        # We simplify to_json to only store summary metadata if needed for large reports
        # but for now we store the whole thing as it is expected to be small
        return json.dumps(asdict(self), ensure_ascii=False)

class ImmuneHeatmapEngine:
    """
    Motor de análisis estadístico para identificar zonas calientes (hotspots)
    de riesgo, tensión y fatiga en Greys-v3 con calibración temporal.
    """

    def __init__(
        self,
        memory_dir: str = "assets/memory",
        report_ledger_path: str = DEFAULT_HEATMAP_LEDGER_PATH,
        skills_dir: str = "src/skills"
    ):
        self.memory_dir = Path(memory_dir)
        self.report_ledger_path = Path(report_ledger_path)
        self.recent_window_seconds = int(os.getenv("GREYS_HEATMAP_RECENT_HOURS", "24")) * 3600
        self.state_resolver = CanonicalStateResolver(memory_dir=memory_dir, skills_dir=skills_dir)
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.report_ledger_path.parent.exists():
            self.report_ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(self) -> List[ImmuneHeatmapReport]:
        """Genera y persiste todos los tipos de mapas configurados."""
        reports = []
        now = time.time()
        
        # 1. Failure Family
        failures = self._load_ledger_metadata("ingestion_failure_ledger.jsonl")
        if failures:
            reports.append(self.build_failure_family_heatmap(failures, now))

        # 2. Module x Tension
        tension = self._load_ledger_metadata("semantic_tension_ledger.jsonl")
        if tension:
            reports.append(self.build_module_tension_heatmap(tension, now))

        # 3. Candidate x ISS
        immune = self._load_ledger_metadata("immune_quarantine_ledger.jsonl")
        if immune:
            reports.append(self.build_candidate_risk_heatmap(immune, now))
            
        # 4. Dependency x Friction
        deps = self._load_ledger_metadata("dependency_review_ledger.jsonl")
        if deps:
            reports.append(self.build_dependency_friction_heatmap(deps, now))
            
        # Persistir
        for r in reports:
            self._persist_report(r)
            
        return reports

    def _get_trend_label(self, delta: float) -> str:
        if abs(delta) < 0.1: return "stable"
        if delta > 0.2: return "rising_sharply"
        if delta > 0: return "rising"
        if delta < -0.2: return "falling_sharply"
        return "falling"

    def build_failure_family_heatmap(self, events: List[Dict[str, Any]], now: float) -> ImmuneHeatmapReport:
        hist_counts = Counter()
        recent_counts = Counter()
        evidence = {}
        
        cutoff = now - self.recent_window_seconds
        
        for e in events:
            f_type = e.get("failure_type", "unknown")
            ts = e.get("timestamp", 0.0)
            
            hist_counts[f_type] += 1
            if ts > cutoff:
                recent_counts[f_type] += 1
                
            if f_type not in evidence: evidence[f_type] = []
            if e.get("event_id"): evidence[f_type].append(e.get("event_id"))

        cells = []
        max_hist = max(hist_counts.values()) if hist_counts else 1
        max_recent = max(recent_counts.values()) if recent_counts else 1
        
        for f_type, h_count in hist_counts.items():
            r_count = recent_counts.get(f_type, 0)
            h_intensity = h_count / max_hist
            r_intensity = r_count / max_recent if recent_counts and max_recent > 0 else 0.0
            delta = r_intensity - h_intensity
            
            cells.append(HeatmapCell(
                axis_x=f_type, axis_y="frequency",
                historical_intensity=round(h_intensity, 3),
                recent_intensity=round(r_intensity, 3),
                value=float(h_count),
                count=h_count,
                trend_delta=round(delta, 3),
                trend_label=self._get_trend_label(delta),
                risk_level="high" if r_intensity > 0.7 else "medium" if r_intensity > 0.3 else "low",
                evidence_refs=evidence[f_type][:5]
            ))

        hist_hotspots = [
            c.axis_x for c in sorted(cells, key=lambda x: x.historical_intensity, reverse=True) 
            if c.historical_intensity > 0
        ][:3]
        recent_hotspots = [
            c.axis_x for c in sorted(cells, key=lambda x: x.recent_intensity, reverse=True)
            if c.recent_intensity > 0
        ][:3]
        
        # Lógica de foco recomendada
        focus = "Sistema estable"
        target_id = None
        
        if recent_hotspots:
            target_id = recent_hotspots[0]
        elif hist_hotspots:
            target_id = hist_hotspots[0]
            
        if target_id:
            top_cell = next(c for c in cells if c.axis_x == target_id)
            
            # Reconciliación canónica
            canon = self.state_resolver.resolve_failure_family_state(target_id)
            
            if canon.canonical_status == "active_failure":
                focus = f"Priorizar mitigación de {target_id} (falla ACTIVA)"
            elif canon.canonical_status == "recent_debt":
                focus = f"Monitorear {target_id} (deuda reciente, no detectada en la última hora)"
            elif canon.canonical_status == "historical_debt":
                focus = f"Monitorear {target_id} (deuda histórica)"
            elif top_cell.trend_label.startswith("rising"):
                focus = f"Priorizar mitigación de {target_id} (emergente)"
            elif top_cell.historical_intensity > 0.8 and top_cell.recent_intensity < 0.2:
                focus = f"Monitorear {target_id} tras mitigación histórica"
            else:
                focus = f"Investigar recurrencia de {target_id}"

        return ImmuneHeatmapReport(
            event_id=f"map_{os.urandom(4).hex()}",
            timestamp=now,
            heatmap_type="failure_family",
            title="Mapa de Calor: Familias de Fallo",
            cells=cells,
            dominant_historical_hotspots=hist_hotspots,
            dominant_recent_hotspots=recent_hotspots,
            recommended_focus=focus,
            generated_from_ledgers=["ingestion_failure_ledger.jsonl"]
        )

    def build_module_tension_heatmap(self, events: List[Dict[str, Any]], now: float) -> ImmuneHeatmapReport:
        hist_tension = {} # (mod, typ) -> value
        recent_tension = {}
        cutoff = now - self.recent_window_seconds
        
        for e in events:
            module = e.get("source", "unknown")
            evt_type = e.get("event_type", "unknown")
            damage = e.get("damage_delta", 0.0)
            ts = e.get("timestamp", 0.0)
            key = (module, evt_type)
            
            hist_tension[key] = hist_tension.get(key, 0.0) + damage
            if ts > cutoff:
                recent_tension[key] = recent_tension.get(key, 0.0) + damage

        cells = []
        if hist_tension:
            max_h = max(hist_tension.values()) or 1.0
            max_r = max(recent_tension.values()) if recent_tension else 0.0
            
            for (mod, typ), h_val in hist_tension.items():
                r_val = recent_tension.get((mod, typ), 0.0)
                h_int = h_val / max_h
                r_int = r_val / max_r if max_r > 0 else 0.0
                delta = r_int - h_int
                
                cells.append(HeatmapCell(
                    axis_x=mod, axis_y=typ,
                    historical_intensity=round(h_int, 3),
                    recent_intensity=round(r_int, 3),
                    value=round(h_val, 3),
                    count=0, # Not used here
                    trend_delta=round(delta, 3),
                    trend_label=self._get_trend_label(delta),
                    risk_level="high" if r_int > 0.8 else "medium" if r_int > 0.4 else "low",
                    evidence_refs=[]
                ))

        h_hotspots = sorted(list(set(c.axis_x for c in cells if c.historical_intensity > 0.5)))
        r_hotspots = sorted(list(set(c.axis_x for c in cells if c.recent_intensity > 0.5)))
        
        return ImmuneHeatmapReport(
            event_id=f"map_{os.urandom(4).hex()}",
            timestamp=now,
            heatmap_type="module_tension",
            title="Mapa de Calor: Tensión por Módulo",
            cells=cells,
            dominant_historical_hotspots=h_hotspots,
            dominant_recent_hotspots=r_hotspots,
            recommended_focus=f"Módulo con mayor tensión reciente: {r_hotspots[0]}" if r_hotspots else "Sistema balanceado",
            generated_from_ledgers=["semantic_tension_ledger.jsonl"]
        )

    def build_candidate_risk_heatmap(self, events: List[Dict[str, Any]], now: float) -> ImmuneHeatmapReport:
        cells = []
        cutoff = now - self.recent_window_seconds
        
        for e in events:
            iss = e.get("iss", 0.0)
            level = e.get("recommended_quarantine_level", 0)
            ts = e.get("timestamp", 0.0)
            
            h_int = min(1.0, iss / 5.0) if iss > 0 else 0.0
            r_int = h_int if ts > cutoff else 0.0
            delta = r_int - h_int # Candidates are usually one-off, but this works
            
            cells.append(HeatmapCell(
                axis_x=e.get("item_id", "unknown"),
                axis_y=f"Level {level}",
                historical_intensity=round(h_int, 3),
                recent_intensity=round(r_int, 3),
                value=iss,
                count=1,
                trend_delta=round(delta, 3),
                trend_label="active" if ts > cutoff else "stale",
                risk_level="critical" if level >= 3 else "high" if level == 2 else "medium" if level == 1 else "low",
                evidence_refs=[]
            ))
            
        h_hotspots = [c.axis_x for c in cells if c.historical_intensity > 0.6]
        r_hotspots = [c.axis_x for c in cells if c.recent_intensity > 0.6]
        
        return ImmuneHeatmapReport(
            event_id=f"map_{os.urandom(4).hex()}",
            timestamp=now,
            heatmap_type="candidate_iss",
            title="Mapa de Riesgo: Candidatos e ISS",
            cells=cells,
            dominant_historical_hotspots=h_hotspots,
            dominant_recent_hotspots=r_hotspots,
            recommended_focus="Revisar candidatos con riesgo activo" if r_hotspots else "Monitorear candidatos en cuarentena",
            generated_from_ledgers=["immune_quarantine_ledger.jsonl"]
        )

    def build_dependency_friction_heatmap(self, events: List[Dict[str, Any]], now: float) -> ImmuneHeatmapReport:
        cells = []
        cutoff = now - self.recent_window_seconds
        
        # Agrupar por dependencia para resolver estado canónico
        dep_names = {e.get("dependency_name") for e in events if e.get("dependency_name")}
        
        for d_name in dep_names:
            canon = self.state_resolver.resolve_dependency_state(d_name)
            
            # Buscamos el último evento de esta dependencia para el ISS base
            last_e = next((e for e in reversed(events) if e.get("dependency_name") == d_name), {})
            ts = last_e.get("timestamp", 0.0)
            
            h_int = 0.1
            risk = last_e.get("risk_level", "low")
            if risk == "high": h_int = 0.8
            elif risk == "medium": h_int = 0.5
            
            # Ajustar intensidad según estado canónico
            if canon.canonical_status == "pending_review":
                h_int = min(1.0, h_int + 0.3)
                trend = "needs_review"
            elif canon.canonical_status == "approved_installed":
                h_int = max(0.0, h_int - 0.4) # Reducir fricción si ya está aprobado
                trend = "stable"
            else:
                trend = canon.canonical_status
                
            r_int = h_int if ts > cutoff else (h_int * 0.5)
            
            cells.append(HeatmapCell(
                axis_x=d_name,
                axis_y=canon.canonical_status,
                historical_intensity=round(h_int, 3),
                recent_intensity=round(r_int, 3),
                value=h_int,
                count=1,
                trend_delta=round(r_int - h_int, 3),
                trend_label=trend,
                risk_level=risk,
                evidence_refs=[]
            ))
            
        return ImmuneHeatmapReport(
            event_id=f"map_{os.urandom(4).hex()}",
            timestamp=now,
            heatmap_type="dependency_friction",
            title="Mapa de Fricción: Dependencias Externas",
            cells=cells,
            dominant_historical_hotspots=[c.axis_x for c in sorted(cells, key=lambda x: x.historical_intensity, reverse=True) if c.historical_intensity > 0.5][:3],
            dominant_recent_hotspots=[c.axis_x for c in sorted(cells, key=lambda x: x.recent_intensity, reverse=True) if c.recent_intensity > 0.5][:3],
            recommended_focus="Priorizar aprobación de dependencias con alta fricción reciente",
            generated_from_ledgers=["dependency_review_ledger.jsonl"]
        )

    def _load_ledger_metadata(self, filename: str) -> List[Dict[str, Any]]:
        """Carga metadatos, prefiriendo compact summaries si existen."""
        # 1. Intentar cargar desde compact summary
        compact_path = self.memory_dir / "compact" / f"{Path(filename).stem}_summary.jsonl"
        raw_path = self.memory_dir / filename
        
        events = []
        
        # Primero leemos el crudo reciente (últimos 200)
        if raw_path.exists():
            try:
                with open(raw_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-200:]:
                        if line.strip(): events.append(json.loads(line))
            except Exception: pass

        # Si hay resumen compacto, agregamos su información (pero no como eventos individuales, 
        # aquí el motor debería ser capaz de procesar el objeto CompactSummary. 
        # Para esta v1, nos enfocamos en el crudo reciente para el mapa 'vivo').
        
        return events

    def _persist_report(self, report: ImmuneHeatmapReport):
        try:
            with open(self.report_ledger_path, "a", encoding="utf-8") as f:
                f.write(report.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to persist heatmap report: {e}")

    def load_latest_report(self, heatmap_type: str) -> Optional[ImmuneHeatmapReport]:
        if not self.report_ledger_path.exists(): return None
        try:
            with open(self.report_ledger_path, "r", encoding="utf-8") as f:
                latest = None
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("heatmap_type") == heatmap_type:
                        latest = data
                if latest:
                    # Reconstruir dataclass (simplificado)
                    return ImmuneHeatmapReport(**latest)
        except Exception: pass
        return None
