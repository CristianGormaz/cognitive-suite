import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from core.iafa_auditor import IafaAuditor
from cognition.llm_planner import CognitivePlan, CognitiveDecision, IafaFrictionEstimates, CognitiveExecutionPayload
import tempfile
from pathlib import Path

@pytest.mark.asyncio
async def test_experimental_iafa_registration():
    # Este test valida que el orquestador registre el perfil de riesgo IAFA experimental
    with tempfile.TemporaryDirectory() as temp_dir:
        auditor = IafaAuditor(os.path.join(temp_dir, "audit.log"), secret_key="test")
        
        # Crear estructura de skills
        skills_dir = Path(temp_dir) / "skills"
        exp_dir = skills_dir / "experimental"
        exp_dir.mkdir(parents=True)
        
        skill_file = exp_dir / "skill_consultor_tiempo_local.py"
        skill_file.write_text("async def _generated_skill_impl(ctx): return {'status': 'ok', 'response_text': 'ok'}", encoding="utf-8")

        with patch.dict(os.environ, {
            "GREYS_EXPERIMENTAL_SKILLS_ENABLED": "1",
            "GREYS_EXPERIMENTAL_SKILL_ALLOWLIST": "consultor_tiempo_local"
        }):
            with patch("main.DEFAULT_SKILLS_DIR", skills_dir):
                orchestrator = await MainOrchestrator.create_default()
                
                # Mock ledgers
                orchestrator.tension_ledger = MagicMock()
                orchestrator.stress_guard = MagicMock()
                orchestrator.stress_guard.get_stress_snapshot.return_value = {
                    "is_mem_stressed": False, "is_cpu_stressed": False, "load_1m": 0.1, "mem_available_mb": 1000
                }
                
                # Crear CognitivePlan real
                decision = CognitiveDecision(
                    intent_category="consultar_tiempo",
                    proposed_action="consultor_tiempo_local",
                    iafa_friction_estimates=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1),
                    execution_payload=CognitiveExecutionPayload(target_path="n/a", extracted_tags=())
                )
                mock_plan = CognitivePlan(
                    task_id="t1", decision=decision, thought_trace="thinking", raw_response_sha256="fake"
                )
                
                orchestrator.planner.plan = AsyncMock(return_value=mock_plan)
                orchestrator.iafa_engine.calculate_iafa_score = MagicMock(return_value=1.0)
                
                # EJECUCIÓN
                await orchestrator.process_input("qué hora es")
                
                # VERIFICACIÓN DE REGISTRO
                # Debe haber un evento de evaluación IAFA experimental
                orchestrator.tension_ledger.append_event.assert_called()
                eval_events = [
                    args[0] for args, _ in orchestrator.tension_ledger.append_event.call_args_list 
                    if args[0].event_type == "experimental_iafa_evaluated"
                ]
                assert len(eval_events) > 0
                assert eval_events[0].proposed_action == "consultor_tiempo_local"
                assert "Analysis:" in eval_events[0].notes or eval_events[0].notes == ""
