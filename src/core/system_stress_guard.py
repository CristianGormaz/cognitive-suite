from __future__ import annotations

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SystemStressGuard:
    """
    Guardian metabólico para Greys-v3.
    Monitorea la carga del sistema y la memoria disponible para evitar
    saturación física del host.
    """

    def __init__(
        self,
        min_available_mb: int = 1500,
        max_load_1m: Optional[float] = None,
        max_load_rel: float = 2.0,  # Max load per core
    ):
        self.min_available_mb = int(os.getenv("GREYS_MIN_AVAILABLE_MB", str(min_available_mb)))
        
        env_load = os.getenv("GREYS_MAX_LOAD_1M")
        self.max_load_1m = float(env_load) if env_load else max_load_1m
        self.max_load_rel = float(os.getenv("GREYS_MAX_LOAD_REL", str(max_load_rel)))

    def get_available_memory_mb(self) -> int:
        """Lee /proc/meminfo para obtener la memoria disponible en MB."""
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        # MemAvailable:    17564756 kB
                        parts = line.split()
                        return int(parts[1]) // 1024
        except Exception as exc:
            logger.warning(f"No se pudo leer /proc/meminfo: {exc}")
        return 999999  # Fallback seguro (optimista)

    def get_load_avg(self) -> tuple[float, float, float]:
        """Obtiene el load average del sistema."""
        try:
            return os.getloadavg()
        except Exception:
            return (0.0, 0.0, 0.0)

    def get_cpu_count(self) -> int:
        """Obtiene la cantidad de núcleos de CPU."""
        return os.cpu_count() or 1

    def get_stress_snapshot(self) -> Dict[str, Any]:
        """Devuelve un resumen del estado de estrés actual."""
        mem_avail = self.get_available_memory_mb()
        loads = self.get_load_avg()
        cpu_count = self.get_cpu_count()
        
        load_1m = loads[0]
        # Si no hay un límite absoluto, usamos el relativo por núcleo
        limit_load = self.max_load_1m if self.max_load_1m is not None else (cpu_count * self.max_load_rel)

        return {
            "mem_available_mb": mem_avail,
            "mem_threshold_mb": self.min_available_mb,
            "load_1m": load_1m,
            "load_limit": limit_load,
            "cpu_count": cpu_count,
            "is_mem_stressed": mem_avail < self.min_available_mb,
            "is_cpu_stressed": load_1m > limit_load,
        }

    def is_host_under_stress(self) -> bool:
        """Determina si el sistema está bajo estrés según los umbrales."""
        snapshot = self.get_stress_snapshot()
        return snapshot["is_mem_stressed"] or snapshot["is_cpu_stressed"]

    def log_stress_status(self):
        """Loguea el estado de estrés si es relevante."""
        snapshot = self.get_stress_snapshot()
        if snapshot["is_mem_stressed"]:
            logger.warning(f"SISTEMA BAJO ESTRÉS (MEMORIA): {snapshot['mem_available_mb']}MB < {snapshot['mem_threshold_mb']}MB")
        if snapshot["is_cpu_stressed"]:
            logger.warning(f"SISTEMA BAJO ESTRÉS (CPU): Load {snapshot['load_1m']} > Límite {snapshot['load_limit']}")
