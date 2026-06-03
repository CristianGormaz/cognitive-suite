from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from core.iafa_auditor import IafaAuditor
from core.iafa_engine import IAFAEngine, IAFADecision


class IafaGatekeeper:
    """
    Coordination boundary for IAFA.

    The gatekeeper composes the pure engine with optional audit infrastructure.
    It does not contain scoring math and it does not decide how audit entries
    are persisted.
    """

    def __init__(self, engine: IAFAEngine, auditor: Optional[Union[IafaAuditor, str]] = None):
        self.engine = engine
        self.auditor = IafaAuditor(secret_key=auditor) if isinstance(auditor, str) else auditor

    async def evaluate_action(
        self,
        action_name: str,
        context: Dict[str, float],
        recent_intents: List[str],
        current_hz: float,
        threshold: float = 0.7,
    ) -> IAFADecision:
        decision = self.engine.evaluate_action(action_name, context, recent_intents, current_hz, threshold)
        if self.auditor:
            await self.auditor.log_decision(
                action_name=decision.action_name,
                score=decision.score,
                threshold=decision.threshold,
                allowed=decision.allowed,
                details={
                    "reason": decision.reason,
                    "breakdown": decision.breakdown.to_dict(),
                },
            )
        return decision

    async def authorize_action(
        self,
        action_name: str,
        context: Dict[str, float],
        recent_intents: List[str],
        current_hz: float,
        threshold: float = 0.7,
    ) -> bool:
        decision = await self.evaluate_action(action_name, context, recent_intents, current_hz, threshold)
        if not decision.allowed:
            raise PermissionError(f"IAFA Blocked: {decision.score:.3f} < {decision.threshold:.3f}")
        return True

    def require_iafa(self, threshold: float = 0.7):
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                await self.authorize_action(
                    func.__name__,
                    kwargs["context"],
                    kwargs["recent_intents"],
                    kwargs["current_hz"],
                    threshold,
                )
                return await func(*args, **kwargs)

            return wrapper

        return decorator
