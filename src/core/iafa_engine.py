from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence


IAFA_VARIABLES = ("O", "M", "P", "V", "K", "R", "I", "N", "A")


class IAFAInputError(ValueError):
    """Raised when IAFA receives non-numeric or non-finite input."""


def _finite_float(name: str, value: Any) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise IAFAInputError(f"{name} must be numeric") from exc

    if not math.isfinite(numeric_value):
        raise IAFAInputError(f"{name} must be finite")
    return numeric_value


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class IAFAPenaltyConfig:
    success_alpha: float = 1.0
    success_gamma: float = 0.5
    red_herring_base_hz: float = 0.5
    red_herring_sigma: float = 0.3
    red_herring_gamma: float = 2.0
    epsilon: float = 1e-6

    def __post_init__(self) -> None:
        for field_name, value in asdict(self).items():
            _finite_float(field_name, value)

        if self.red_herring_base_hz <= 0:
            raise IAFAInputError("red_herring_base_hz must be greater than zero")
        if self.epsilon <= 0:
            raise IAFAInputError("epsilon must be greater than zero")


@dataclass(frozen=True)
class IAFAScoreBreakdown:
    score: float
    base_score: float
    success_penalty: float
    red_herring_penalty: float
    entropy: float
    current_hz: float
    variables: Dict[str, float] = field(default_factory=dict)
    recent_intents_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IAFADecision:
    action_name: str
    score: float
    threshold: float
    allowed: bool
    reason: str
    breakdown: IAFAScoreBreakdown

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IAFAEngine:
    """
    Pure IAFA scoring engine.

    This class is intentionally deterministic: no IO, no logging, no network,
    no audit writes, and no hidden exception swallowing.
    """

    def __init__(
        self,
        weights: Mapping[str, float],
        bias: float = 0.0,
        penalty_config: Optional[IAFAPenaltyConfig] = None,
    ) -> None:
        self.weights = self._normalize_weights(weights)
        self.bias = _finite_float("bias", bias)
        self.penalty_config = penalty_config or IAFAPenaltyConfig()

    @staticmethod
    def _normalize_weights(weights: Mapping[str, float]) -> Dict[str, float]:
        if not weights:
            raise IAFAInputError("weights cannot be empty")

        normalized: Dict[str, float] = {}
        for variable, weight in weights.items():
            if not isinstance(variable, str) or not variable:
                raise IAFAInputError("weight keys must be non-empty strings")
            normalized[variable] = _finite_float(f"weight[{variable}]", weight)
        return normalized

    @staticmethod
    def _normalize_variables(current_variables: Mapping[str, float]) -> Dict[str, float]:
        if current_variables is None:
            raise IAFAInputError("current_variables cannot be None")

        normalized: Dict[str, float] = {}
        for variable, value in current_variables.items():
            if not isinstance(variable, str) or not variable:
                raise IAFAInputError("variable keys must be non-empty strings")
            normalized[variable] = _finite_float(f"variable[{variable}]", value)
        return normalized

    @staticmethod
    def _normalize_intents(recent_intents: Sequence[str]) -> Sequence[str]:
        if recent_intents is None:
            raise IAFAInputError("recent_intents cannot be None")
        return [str(intent) for intent in recent_intents]

    @staticmethod
    def shannon_entropy(recent_intents: Sequence[str]) -> float:
        intents = IAFAEngine._normalize_intents(recent_intents)
        if not intents:
            return 0.0

        total_count = len(intents)
        frequency_count = Counter(intents)

        entropy = 0.0
        for count in frequency_count.values():
            probability = count / total_count
            entropy -= probability * math.log2(probability)
        return entropy

    def success_paradox_penalty(self, current_a: float, current_p: float, current_v: float) -> float:
        config = self.penalty_config
        current_a = _finite_float("current_a", current_a)
        current_p = _finite_float("current_p", current_p)
        current_v = _finite_float("current_v", current_v)

        denominator = current_p + current_v + config.epsilon
        if denominator <= 0:
            denominator = config.epsilon

        diff = max(0.0, current_a - (config.success_alpha * (current_p + current_v)))
        return config.success_gamma * (diff / denominator) ** 2

    def red_herring_penalty(self, recent_intents: Sequence[str], current_hz: float) -> float:
        config = self.penalty_config
        intents = self._normalize_intents(recent_intents)
        current_hz = _finite_float("current_hz", current_hz)
        entropy = self.shannon_entropy(intents)
        factor = max(0.0, current_hz / config.red_herring_base_hz)
        return config.red_herring_sigma * (entropy * factor) ** config.red_herring_gamma

    def score(self, current_variables: Mapping[str, float], recent_intents: Sequence[str], current_hz: float) -> IAFAScoreBreakdown:
        variables = self._normalize_variables(current_variables)
        intents = self._normalize_intents(recent_intents)
        current_hz = _finite_float("current_hz", current_hz)

        base_score = self.bias
        for variable, weight in self.weights.items():
            base_score += variables.get(variable, 0.0) * weight

        entropy = self.shannon_entropy(intents)
        success_penalty = self.success_paradox_penalty(
            variables.get("A", 0.0),
            variables.get("P", 0.0),
            variables.get("V", 0.0),
        )
        red_herring_penalty = self.red_herring_penalty(intents, current_hz)
        penalized_score = base_score - success_penalty - red_herring_penalty

        return IAFAScoreBreakdown(
            score=float(_clamp_01(penalized_score)),
            base_score=float(base_score),
            success_penalty=float(success_penalty),
            red_herring_penalty=float(red_herring_penalty),
            entropy=float(entropy),
            current_hz=float(current_hz),
            variables=dict(variables),
            recent_intents_count=len(intents),
        )

    def evaluate_action(
        self,
        action_name: str,
        current_variables: Mapping[str, float],
        recent_intents: Sequence[str],
        current_hz: float,
        threshold: float = 0.7,
    ) -> IAFADecision:
        if not action_name:
            raise IAFAInputError("action_name cannot be empty")

        threshold = _finite_float("threshold", threshold)
        if not 0.0 <= threshold <= 1.0:
            raise IAFAInputError("threshold must be between 0.0 and 1.0")

        breakdown = self.score(current_variables, recent_intents, current_hz)
        allowed = breakdown.score >= threshold
        reason = "score_meets_threshold" if allowed else "score_below_threshold"

        return IAFADecision(
            action_name=action_name,
            score=breakdown.score,
            threshold=threshold,
            allowed=allowed,
            reason=reason,
            breakdown=breakdown,
        )

    def calculate_iafa_score(
        self,
        current_variables: Mapping[str, float],
        recent_intents: Sequence[str],
        current_hz: float,
    ) -> float:
        return self.score(current_variables, recent_intents, current_hz).score

    def _calculate_shannon_entropy(self, recent_intents: Sequence[str]) -> float:
        return self.shannon_entropy(recent_intents)

    def _apply_success_paradox_penalty(
        self,
        current_A: float,
        current_P: float,
        current_V: float,
        alpha: float = 1.0,
        gamma: float = 0.5,
    ) -> float:
        config = IAFAPenaltyConfig(
            success_alpha=alpha,
            success_gamma=gamma,
            red_herring_base_hz=self.penalty_config.red_herring_base_hz,
            red_herring_sigma=self.penalty_config.red_herring_sigma,
            red_herring_gamma=self.penalty_config.red_herring_gamma,
            epsilon=self.penalty_config.epsilon,
        )
        return IAFAEngine(self.weights, self.bias, config).success_paradox_penalty(current_A, current_P, current_V)

    def _apply_red_herring_penalty(
        self,
        recent_intents: Sequence[str],
        current_hz: float,
        base_hz: float = 0.5,
        sigma: float = 0.3,
        gamma: float = 2.0,
    ) -> float:
        config = IAFAPenaltyConfig(
            success_alpha=self.penalty_config.success_alpha,
            success_gamma=self.penalty_config.success_gamma,
            red_herring_base_hz=base_hz,
            red_herring_sigma=sigma,
            red_herring_gamma=gamma,
            epsilon=self.penalty_config.epsilon,
        )
        return IAFAEngine(self.weights, self.bias, config).red_herring_penalty(recent_intents, current_hz)


class IafaCore(IAFAEngine):
    """Backward-compatible name for the IAFA engine."""
