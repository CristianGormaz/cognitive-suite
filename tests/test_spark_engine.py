import asyncio
import time
import pytest
from unittest.mock import MagicMock

from cognition.spark_engine import SparkEngine, SparkSignal


class DummyProbe:
    def __init__(self, is_idle=True):
        self._is_idle = is_idle
    async def __call__(self):
        return self._is_idle


class DummyAuditor:
    def __init__(self, signals=None):
        self.signals = [{"payload": s} if isinstance(s, dict) else s for s in (signals or [])]
    def iter_verified_entries(self):
        return iter(self.signals)
    async def get_recent_failures(self):
        return self.signals


class DummyPlanner:
    def __init__(self, intent="test_intent"):
        self.intent = intent
        self.calls = 0
    async def plan(self, envelope):
        self.calls += 1
        class MockDecision:
            def __init__(self, intent):
                self.intent_category = intent
                self.iafa_friction_estimates = type('F', (), {'to_dict': lambda s: {"R": 0.1, "I": 0.1, "N": 0.1}})()
        class MockPlan:
            def __init__(self, intent):
                self.decision = MockDecision(intent)
                self.thought_trace = "Test reasoning"
        return MockPlan(self.intent)


class DummyOrchestrator:
    def __init__(self):
        self.events = []
    def emit_event(self, payload):
        self.events.append(payload)


@pytest.mark.asyncio
async def test_spark_does_not_call_planner_if_no_signals():
    planner = DummyPlanner()
    engine = SparkEngine(
        idle_probe=DummyProbe(True),
        auditor=DummyAuditor([]),  # No signals
        planner=planner,
        dry_run=True,
        cooldown_seconds=0
    )
    await engine.pulse()
    assert planner.calls == 0


@pytest.mark.asyncio
async def test_spark_no_event_if_not_idle():
    orchestrator = DummyOrchestrator()
    engine = SparkEngine(
        idle_probe=DummyProbe(False),  # Not idle
        auditor=DummyAuditor(["error1"]),
        planner=DummyPlanner(),
        orchestrator=orchestrator,
        dry_run=True,
        cooldown_seconds=0
    )
    await engine.pulse()
    assert len(orchestrator.events) == 0


@pytest.mark.asyncio
async def test_spark_respects_cooldown():
    planner = DummyPlanner()
    engine = SparkEngine(
        idle_probe=DummyProbe(True),
        auditor=DummyAuditor(["error1"]),
        planner=planner,
        dry_run=True,
        cooldown_seconds=3600
    )
    
    # Simulate a proposal being sent
    engine._last_proposal_time = time.time()
    await engine.pulse()
    # It should not call planner because of cooldown
    assert planner.calls == 0


@pytest.mark.asyncio
async def test_spark_emits_evolutionary_doubt():
    orchestrator = DummyOrchestrator()
    # Mock failure ledger to return empty top capabilities
    mock_fail = MagicMock()
    mock_fail.get_top_missing_capabilities.return_value = []
    
    # Mock tension ledger to avoid suppression in tests
    mock_tension = MagicMock()
    mock_tension.should_suppress_proposal.return_value = False
    
    engine = SparkEngine(
        idle_probe=DummyProbe(True),
        auditor=DummyAuditor([{"content": "Fail 1"}]),
        planner=DummyPlanner("new_feature"),
        orchestrator=orchestrator,
        dry_run=True, # Bypass IAFA missing
        cooldown_seconds=0,
        failure_ledger=mock_fail,
        tension_ledger=mock_tension
    )
    await engine.pulse()
    
    assert len(orchestrator.events) == 1
    event = orchestrator.events[0]
    assert event["event_type"] == "evolutionary_doubt"
    assert event["source"] == "spark_engine"
    assert event["requires_user_approval"] is True


@pytest.mark.asyncio
async def test_spark_lifecycle():
    engine = SparkEngine(pulse_interval_seconds=1, dry_run=True)
    engine.start()
    assert engine._running is True
    assert engine._task is not None
    assert not engine._task.done()
    
    await engine.stop()
    assert engine._running is False
    assert engine._task is None
