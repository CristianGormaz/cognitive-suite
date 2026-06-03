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

from cognition.genesis_engine import GenesisEngine, GENERATED_FUNCTION_NAME, GENESIS_SYSTEM_PROMPT
from cognition.genesis_sandbox import GenesisSandbox, SandboxResult
from core.task_envelope import TaskEnvelope

logger = logging.getLogger("GenesisAnalysis")

QUARANTINE_DIR = "assets/quarantine/genesis_candidates"

@dataclass(frozen=True)
class GenesisAnalysisResult:
    capability_signature: str
    proposed_skill_name: str
    problem_summary: str
    candidate_code: str
    code_hash: str
    ast_validation_status: bool
    sandbox_status: bool
    validation_errors: List[str]
    allowed_imports_detected: List[str]
    blocked_imports_detected: List[str]
    blocked_builtins_detected: List[str]
    risk_level: str  # low, medium, high
    recommendation: str
    requires_human_approval: bool = True
    installable: bool = False
    timestamp: float = field(default_factory=time.time)
    schema_version: str = "genesis-analysis.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class GenesisAnalysis:
    """
    Componente de análisis seguro para la evolución de Greys-v3.
    Permite generar y validar candidatos de habilidades en un entorno de cuarentena.
    """

    def __init__(self, genesis_engine: GenesisEngine):
        self.engine = genesis_engine
        self.sandbox = genesis_engine.sandbox
        self.quarantine_path = Path(QUARANTINE_DIR)
        self._ensure_quarantine()

    def _ensure_quarantine(self):
        if not self.quarantine_path.exists():
            self.quarantine_path.mkdir(parents=True, exist_ok=True)

    async def analyze_missing_capability(
        self,
        capability_signature: str,
        task_envelope: TaskEnvelope,
        context: Dict[str, Any]
    ) -> GenesisAnalysisResult:
        """
        Genera un candidato de código para una capacidad faltante, lo valida en sandbox
        y lo guarda en cuarentena. NUNCA lo instala.
        """
        logger.info(f"Starting sandbox analysis for capability: {capability_signature}")
        
        intent_name = capability_signature.split(":")[-1]
        safe_intent = self.engine._sanitize_intent_name(intent_name)
        
        # 1. Generar código candidato usando el motor de Genesis
        operator_instruction = self.engine._build_operator_instruction(
            safe_intent, task_envelope, context
        )
        
        try:
            raw_response = await self.engine.transceiver.query_llm(
                task_envelope,
                system_prompt=GENESIS_SYSTEM_PROMPT,
                operator_instruction=operator_instruction,
                json_format=False,
                max_payload_chars=2400
            )
            candidate_code = self.engine._normalize_generated_code(raw_response)
        except Exception as exc:
            logger.error(f"Failed to generate candidate code for {capability_signature}: {exc}")
            return self._failed_result(capability_signature, safe_intent, str(exc))

        # 2. Validación AST básica
        ast_errors = self.engine._validate_generated_shape_sync(candidate_code)
        
        # 3. Validación en Sandbox
        sandbox_result = await self.sandbox.validate_code_proposal(candidate_code, task_envelope.task_id)
        
        # 4. Guardar en cuarentena
        code_hash = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()
        filename = f"candidate_{safe_intent}_{code_hash[:12]}.py"
        target_path = self.quarantine_path / filename
        
        # Envolvemos el código como si fuera una skill real para el análisis técnico
        module_code = self.engine._build_skill_module(safe_intent, candidate_code)
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_quarantine_sync, target_path, module_code)
        
        # 5. Construir resultado de análisis
        if not sandbox_result.is_safe:
            risk_level = "high"
        elif "pdf_reader" in safe_intent or "docx_reader" in safe_intent:
            risk_level = "medium"
        else:
            risk_level = "low"
            
        if "eval" in candidate_code or "exec" in candidate_code: 
            risk_level = "critical"
        
        # Heurística de importaciones (extraída del sandbox visitor si fuera accesible, 
        # aquí hacemos un check simple para el reporte)
        blocked_imports = [imp for imp in ["os", "sys", "subprocess", "requests"] if imp in candidate_code]
        
        recommendation = "Candidato listo para revisión humana."
        if not sandbox_result.is_safe:
            recommendation = "Candidato RECHAZADO por sandbox. No recomendado para promoción."
        
        if "math:solve_integral" in capability_signature:
            recommendation += " Nota: Requiere sympy para cálculo simbólico; verificado que no está instalado."
        
        if "file:pdf_reader" in capability_signature:
            recommendation += " Nota: Requiere pypdf para extracción de texto; verificado que no está instalado."

        return GenesisAnalysisResult(
            capability_signature=capability_signature,
            proposed_skill_name=f"skill_{safe_intent}",
            problem_summary=f"Implementación proactiva para {capability_signature}",
            candidate_code=candidate_code,
            code_hash=code_hash,
            ast_validation_status=len(ast_errors) == 0,
            sandbox_status=sandbox_result.is_safe,
            validation_errors=ast_errors + sandbox_result.validation_errors,
            allowed_imports_detected=[], # Podríamos poblar esto analizando el AST
            blocked_imports_detected=blocked_imports,
            blocked_builtins_detected=[],
            risk_level=risk_level,
            recommendation=recommendation
        )

    def _write_quarantine_sync(self, path: Path, code: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

    def _failed_result(self, sig: str, intent: str, error: str) -> GenesisAnalysisResult:
        return GenesisAnalysisResult(
            capability_signature=sig,
            proposed_skill_name=f"skill_{intent}",
            problem_summary="Error en generación",
            candidate_code="",
            code_hash="",
            ast_validation_status=False,
            sandbox_status=False,
            validation_errors=[error],
            allowed_imports_detected=[],
            blocked_imports_detected=[],
            blocked_builtins_detected=[],
            risk_level="unknown",
            recommendation="Falló la generación del candidato."
        )
