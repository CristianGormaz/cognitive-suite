import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from core.task_envelope import TaskEnvelope
from core.iafa_auditor import IafaAuditor
from cognition.llm_planner import CognitivePlan, CognitiveDecision, IafaFrictionEstimates, CognitiveExecutionPayload
import tempfile
from pathlib import Path

@pytest.mark.asyncio
async def test_consultor_tiempo_runtime_invocation():
    # Este test valida que una entrada de texto real invoque la skill si está habilitada
    with tempfile.TemporaryDirectory() as temp_dir:
        auditor = IafaAuditor(os.path.join(temp_dir, "audit.log"), secret_key="test")
        
        # Crear estructura de skills
        skills_dir = Path(temp_dir) / "skills"
        exp_dir = skills_dir / "experimental"
        exp_dir.mkdir(parents=True)
        
        # Copiar la skill real promovida (o crear mock compatible)
        skill_file = exp_dir / "skill_consultor_tiempo_local.py"
        skill_file.write_text("""
async def _generated_skill_impl(ctx):
    return {'status': 'ok', 'response_text': 'La hora es 12:00 (mock)'}
""", encoding="utf-8")

        with patch.dict(os.environ, {
            "GREYS_EXPERIMENTAL_SKILLS_ENABLED": "1",
            "GREYS_EXPERIMENTAL_SKILL_ALLOWLIST": "consultor_tiempo_local",
            "GREYS_OLLAMA_TIMEOUT": "60"
        }):
            with patch("main.DEFAULT_SKILLS_DIR", skills_dir):
                orchestrator = await MainOrchestrator.create_default()
                
                # RECREAR CognitivePlan real para pasar el check de isinstance en Dispatcher
                decision = CognitiveDecision(
                    intent_category="consultar_tiempo",
                    proposed_action="consultor_tiempo_local",
                    iafa_friction_estimates=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1),
                    execution_payload=CognitiveExecutionPayload(target_path="n/a", extracted_tags=())
                )
                mock_plan = CognitivePlan(
                    task_id="t1",
                    decision=decision,
                    thought_trace="thinking...",
                    raw_response_sha256="fake"
                )
                
                orchestrator.planner.plan = AsyncMock(return_value=mock_plan)
                orchestrator.iafa_engine.calculate_iafa_score = MagicMock(return_value=1.0)
                
                # EJECUCIÓN
                result = await orchestrator.process_input("qué hora es")
                
                # VERIFICACIÓN
                assert result.status == "executed"
                assert "12:00 (mock)" in result.details["response_text"]
                assert result.details["skill_result"]["status"] == "ok"
