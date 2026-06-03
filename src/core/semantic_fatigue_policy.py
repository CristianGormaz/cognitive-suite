import os
import time
import math
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SemanticFatiguePolicy:
    """
    Política de fatiga semántica para evaluar si una propuesta evolutiva
    debe ser suprimida basándose en daño histórico, decay temporal, y criticidad.
    """
    
    CRITICAL_FAMILIES = {
        "llm_circuit_open",
        "host_stress_block",
        "ledger_write_error",
        "ledger_read_error",
        "experimental_skill_error",
        "skill_contract_error",
        "planner_contract_error"
    }
    
    MODERATE_FAMILIES = {
        "llm_timeout",
        "llm_transport_error",
        "llm_malformed_json",
        "dispatcher_unsupported_action",
        "ingestion_unsupported_file_type"
    }

    def __init__(self):
        self.decay_enabled = os.getenv("GREYS_SEMANTIC_FATIGUE_DECAY_ENABLED", "1") == "1"
        self.half_life_hours = float(os.getenv("GREYS_SEMANTIC_FATIGUE_HALF_LIFE_HOURS", "24"))
        self.critical_suppression_guard = os.getenv("GREYS_SEMANTIC_FATIGUE_CRITICAL_SUPPRESSION_GUARD", "1") == "1"

    def calculate_decayed_damage(self, damage: float, timestamp: float, now: float) -> float:
        if not self.decay_enabled or damage <= 0:
            return damage
            
        age_seconds = now - timestamp
        if age_seconds <= 0:
            return damage
            
        half_life_seconds = self.half_life_hours * 3600
        decay_factor = math.pow(0.5, age_seconds / half_life_seconds)
        return damage * decay_factor

    def evaluate(self, events: List[Any], signature: str, threshold: float = 2.0, has_new_evidence: bool = False) -> bool:
        """
        Evalúa si la firma debe ser suprimida.
        """
        now = time.time()
        total_damage = 0.0
        critical_found = False
        rejection_count = 0
        success_reduction = 0.0
        
        relevant_events = [e for e in events if getattr(e, "proposal_signature", None) == signature]
        
        for e in relevant_events:
            evt_type = getattr(e, "event_type", "")
            outcome = getattr(e, "user_outcome", "pending")
            raw_damage = getattr(e, "damage_delta", 0.0)
            
            if evt_type in self.CRITICAL_FAMILIES:
                critical_found = True
            
            if outcome == "rejected":
                rejection_count += 1
            if evt_type == "curated_option_completed" or outcome == "accepted":
                success_reduction += 0.5
                
            if evt_type in self.CRITICAL_FAMILIES:
                # Critical events decay 4x slower
                age_seconds = now - e.timestamp
                half_life_seconds = self.half_life_hours * 3600 * 4
                decay_factor = math.pow(0.5, max(0, age_seconds) / half_life_seconds) if self.decay_enabled else 1.0
                total_damage += (raw_damage * decay_factor)
            elif outcome == "rejected":
                # Rejections decay 2x slower
                age_seconds = now - e.timestamp
                half_life_seconds = self.half_life_hours * 3600 * 2
                decay_factor = math.pow(0.5, max(0, age_seconds) / half_life_seconds) if self.decay_enabled else 1.0
                total_damage += (raw_damage * decay_factor)
            else:
                total_damage += self.calculate_decayed_damage(raw_damage, e.timestamp, now)

        total_damage = max(0.0, total_damage - success_reduction)
        
        # 1. Critical + new evidence -> NEVER suppress
        if self.critical_suppression_guard and critical_found and has_new_evidence:
            return False
            
        # 2. High rejections + no new evidence -> Suppress
        if rejection_count >= 3 and not has_new_evidence:
            return True
            
        # 3. Default threshold check
        return total_damage >= threshold

    def get_fatigue_state(self, events: List[Any]) -> Dict[str, Any]:
        """Generates a summary of the fatigue state."""
        now = time.time()
        families_damage = {}
        critical_unsuppressed = set()
        
        for e in events:
            evt_type = getattr(e, "event_type", "unknown")
            raw_damage = getattr(e, "damage_delta", 0.0)
            
            decayed = self.calculate_decayed_damage(raw_damage, e.timestamp, now)
            if decayed > 0.01:
                families_damage[evt_type] = families_damage.get(evt_type, 0.0) + decayed
                
            if evt_type in self.CRITICAL_FAMILIES and decayed > 0.0:
                critical_unsuppressed.add(evt_type)
                
        sorted_families = sorted(families_damage.items(), key=lambda x: x[1], reverse=True)
        return {
            "top_fatigued_families": sorted_families[:5],
            "critical_unsuppressed": list(critical_unsuppressed)
        }
