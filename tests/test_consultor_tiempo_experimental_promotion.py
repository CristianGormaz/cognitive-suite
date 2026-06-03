import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from core.iafa_auditor import IafaAuditor
from cognition.skill_candidate_review import SkillCandidateReview, SkillCandidateSummary
import tempfile

@pytest.mark.asyncio
async def test_consultor_tiempo_experimental_promotion():
    # Este test valida el flujo completo de promoción para el caso piloto
    with tempfile.TemporaryDirectory() as temp_dir:
        auditor_log = os.path.join(temp_dir, "audit.log")
        auditor = IafaAuditor(auditor_log, secret_key="test")
        
        # Paths
        quarantine_dir = Path(temp_dir) / "quarantine"
        experimental_dir = Path(temp_dir) / "experimental"
        backup_dir = Path(temp_dir) / "backups"
        review_ledger = Path(temp_dir) / "review.jsonl"
        promotion_ledger = Path(temp_dir) / "promotion.jsonl"
        
        quarantine_dir.mkdir()
        experimental_dir.mkdir()
        backup_dir.mkdir()
        
        # 1. Crear el candidato en la cuarentena temporal
        cid = "candidate_consultor_tiempo_local.py"
        cand_file = quarantine_dir / cid
        cand_file.write_text("def _generated_skill_impl(context): return {}", encoding="utf-8")
        
        # 2. Crear el test asociado
        # El gate busca tests/test_<candidate_id>
        # En el entorno de test real, 'tests' ya existe.
        os.makedirs("tests", exist_ok=True)
        test_file = Path("tests") / f"test_{cid}"
        test_file.touch()
        
        try:
            # 3. Setup Reviewer mockeado para devolver aprobación
            mock_reviewer = MagicMock(spec=SkillCandidateReview)
            mock_reviewer.quarantine_path = quarantine_dir
            mock_reviewer.ledger_path = review_ledger
            
            summary = SkillCandidateSummary(
                candidate_id=cid,
                capability_signature="time:local_query",
                code_sha256="fake",
                file_size=10,
                created_at=1.0,
                dangerous_calls_detected=[],
                current_status="approved_for_future_promotion"
            )
            mock_reviewer.list_candidates.return_value = [summary]
            
            # 4. Instanciar orquestador con paths temporales
            from cognition.skill_promotion_gate import SkillPromotionGate
            from cognition.skill_experimental_promoter import SkillExperimentalPromoter
            
            gate = SkillPromotionGate(reviewer=mock_reviewer, ledger_path=str(promotion_ledger))
            promoter = SkillExperimentalPromoter(
                gate=gate, 
                experimental_dir=str(experimental_dir),
                backup_dir=str(backup_dir)
            )
            
            # Bypass MainOrchestrator isinstance checks
            orchestrator = MainOrchestrator(
                MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), auditor,
                skill_reviewer=mock_reviewer,
                skill_promoter=gate,
                experimental_promoter=promoter,
                stress_guard=MagicMock(),
                tension_ledger=MagicMock(),
                failure_ledger=MagicMock(),
                genesis_analysis=MagicMock()
            )
            
            # 5. Ejecutar promoción experimental
            result = await orchestrator.experimental_promoter.promote_to_experimental(cid)
            
            # 6. Validaciones
            assert result["status"] == "success"
            assert (experimental_dir / "skill_consultor_tiempo_local.py").exists()

            assert (experimental_dir / "skill_consultor_tiempo_local.py").read_text() == cand_file.read_text()
            
            # Verificar que el ledger de promoción tiene el registro físico
            promotion_history = promotion_ledger.read_text().splitlines()
            assert any("physical_promotion" in line for line in promotion_history)
            
        finally:
            if test_file.exists(): os.remove(test_file)
