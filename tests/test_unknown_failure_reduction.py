import pytest
from core.ingestion_failure_ledger import IngestionFailureLedger

def test_ingestion_failure_ledger_reduces_unknowns():
    # Previous behavior returned "unknown_failure" for almost everything not timeout/mime/unsupported
    
    class RandomLibError(Exception): pass
    
    # Contract error
    err = ValueError("planner contract missing")
    res = IngestionFailureLedger.classify_failure(err)
    assert res == "planner_contract_error"
    
    # Skill error
    err = RuntimeError("skill execution failed")
    res = IngestionFailureLedger.classify_failure(err)
    assert res == "skill_contract_error"

    # Ledger error
    err = IOError("failed to read ledger")
    res = IngestionFailureLedger.classify_failure(err)
    assert res == "ledger_read_error"
    
    # True unknown
    err = RandomLibError("quantum fluctuation detected")
    res = IngestionFailureLedger.classify_failure(err)
    assert res == "unknown_failure"
