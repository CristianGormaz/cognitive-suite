from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("LocalLedgerCache")

@dataclass
class CachedLedgerSnapshot:
    path: str
    loaded_at: float
    file_mtime: float
    file_size: int
    total_records: int
    records: List[Dict[str, Any]]
    cache_hit: bool = False
    schema_version: str = "ledger-cache.v1"

@dataclass
class LedgerCacheStats:
    cache_hits: int = 0
    cache_misses: int = 0
    invalidations: int = 0
    files_tracked: int = 0
    total_records_cached: int = 0
    estimated_reads_saved: int = 0
    schema_version: str = "ledger-cache.stats.v1"

class LocalLedgerCache:
    """
    Read-through cache for local JSONL ledgers.
    Reduces I/O load by keeping recent snapshots in memory and invalidating
    them based on file modification time (mtime) and size.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir).resolve()
        self.cache: Dict[str, CachedLedgerSnapshot] = {}
        self.stats = LedgerCacheStats()

    def _is_safe_path(self, file_path: str | Path) -> bool:
        """Asegura que el archivo está dentro del directorio de memoria."""
        try:
            resolved = Path(file_path).resolve()
            return str(resolved).startswith(str(self.memory_dir))
        except Exception:
            return False

    def is_cache_valid(self, file_path: str | Path) -> bool:
        """Verifica si la caché es válida para el archivo dado."""
        path_str = str(file_path)
        if path_str not in self.cache:
            return False
            
        snapshot = self.cache[path_str]
        try:
            stat = os.stat(path_str)
            return stat.st_mtime == snapshot.file_mtime and stat.st_size == snapshot.file_size
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.warning(f"Error checking cache validity for {path_str}: {e}")
            return False

    def invalidate(self, file_path: str | Path):
        """Invalida la caché de un archivo."""
        path_str = str(file_path)
        if path_str in self.cache:
            del self.cache[path_str]
            self.stats.invalidations += 1

    def invalidate_all(self):
        """Invalida toda la caché."""
        self.cache.clear()
        self.stats.invalidations += 1

    def refresh_if_changed(self, file_path: str | Path) -> Optional[CachedLedgerSnapshot]:
        """Recarga el archivo si ha cambiado y retorna el snapshot. Retorna None si no se puede leer."""
        path_str = str(file_path)
        
        if not self._is_safe_path(file_path):
            logger.warning(f"Intento de cachear ruta insegura: {path_str}")
            return None

        if self.is_cache_valid(file_path):
            self.stats.cache_hits += 1
            self.stats.estimated_reads_saved += 1
            snapshot = self.cache[path_str]
            snapshot.cache_hit = True
            return snapshot

        self.stats.cache_misses += 1
        
        try:
            stat = os.stat(path_str)
            records = []
            
            with open(path_str, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Línea JSON corrupta ignorada en {path_str}")
                        
            snapshot = CachedLedgerSnapshot(
                path=path_str,
                loaded_at=os.times().elapsed if hasattr(os.times(), 'elapsed') else 0.0, # Just using 0.0 or time.time()
                file_mtime=stat.st_mtime,
                file_size=stat.st_size,
                total_records=len(records),
                records=records,
                cache_hit=False
            )
            
            self.cache[path_str] = snapshot
            self._update_stats()
            return snapshot
            
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error cargando caché para {path_str}: {e}")
            return None

    def get_records(self, file_path: str | Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retorna todos los registros, usando la caché si es válida."""
        import time
        
        path_str = str(file_path)
        
        if not self._is_safe_path(file_path):
            logger.warning(f"Intento de leer ruta insegura: {path_str}")
            return []

        if self.is_cache_valid(file_path):
            self.stats.cache_hits += 1
            self.stats.estimated_reads_saved += 1
            records = self.cache[path_str].records
            return records[-limit:] if limit is not None else records

        self.stats.cache_misses += 1
        
        try:
            stat = os.stat(path_str)
            records = []
            
            with open(path_str, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Línea JSON corrupta ignorada en {path_str}")
                        
            snapshot = CachedLedgerSnapshot(
                path=path_str,
                loaded_at=time.time(),
                file_mtime=stat.st_mtime,
                file_size=stat.st_size,
                total_records=len(records),
                records=records,
                cache_hit=False
            )
            
            self.cache[path_str] = snapshot
            self._update_stats()
            
            return records[-limit:] if limit is not None else records
            
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error(f"Error cargando caché para {path_str}: {e}")
            return []

    def get_recent(self, file_path: str | Path, limit: int = 100) -> List[Dict[str, Any]]:
        """Alias para obtener los últimos registros."""
        return self.get_records(file_path, limit=limit)

    def get_stats(self) -> LedgerCacheStats:
        """Devuelve las estadísticas actuales de la caché."""
        self._update_stats()
        return self.stats

    def clear(self):
        """Limpia la caché manualmente."""
        self.cache.clear()
        
    def _update_stats(self):
        self.stats.files_tracked = len(self.cache)
        self.stats.total_records_cached = sum(s.total_records for s in self.cache.values())
