#!/usr/bin/env python3
"""
Memory Cache (L1) - Cache en memoria con estrategia LRU
Implementa cache de alta velocidad para respuestas frecuentes y templates
"""

import time
import sys
import pickle
import logging
import threading
from collections import OrderedDict
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass 
class CacheEntry:
    """Entrada del cache en memoria"""
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_expires: Optional[datetime]
    size_bytes: int
    
    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado"""
        if self.ttl_expires is None:
            return False
        return datetime.now() > self.ttl_expires
    
    def touch(self):
        """Actualizar último acceso"""
        self.last_accessed = datetime.now()
        self.access_count += 1

class MemoryCache:
    """
    Cache en memoria L1 con estrategia LRU (Least Recently Used)
    
    Características:
    - Límite de memoria configurable
    - TTL por entrada
    - Estrategia de expulsión LRU
    - Métricas detalladas
    - Thread-safe
    """
    
    def __init__(self, max_size_mb: int = 50, default_ttl_hours: int = 1, 
                 cleanup_threshold: float = 0.8):
        """
        Inicializar cache en memoria
        
        Args:
            max_size_mb: Tamaño máximo en megabytes
            default_ttl_hours: TTL por defecto en horas
            cleanup_threshold: Umbral para limpieza automática (0.0-1.0)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.cleanup_threshold = cleanup_threshold
        
        # Almacenamiento thread-safe
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Métricas
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.current_size_bytes = 0
        self.created_at = datetime.now()
        
        # Logging
        self.logger = self._setup_logging()
        
        self.logger.info(f"MemoryCache inicializado - Límite: {max_size_mb}MB, TTL: {default_ttl_hours}h")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging específico"""
        logger = logging.getLogger(f"{__name__}.MemoryCache")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _calculate_size(self, obj: Any) -> int:
        """
        Calcular tamaño aproximado del objeto en bytes
        
        Args:
            obj: Objeto a medir
            
        Returns:
            int: Tamaño en bytes
        """
        try:
            # Usar pickle para estimación del tamaño
            return len(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))
        except (pickle.PickleError, TypeError):
            # Fallback para objetos no serializables
            return sys.getsizeof(obj)
    
    def _make_room(self, required_bytes: int) -> bool:
        """
        Hacer espacio expulsando entradas según estrategia LRU
        
        Args:
            required_bytes: Bytes necesarios
            
        Returns:
            bool: True si se liberó suficiente espacio
        """
        initial_size = self.current_size_bytes
        removed_count = 0
        
        # Primero: remover entradas expiradas
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
            removed_count += 1
        
        # Segundo: verificar si ya hay suficiente espacio
        if self.current_size_bytes + required_bytes <= self.max_size_bytes:
            if removed_count > 0:
                self.logger.debug(f"Liberado espacio removiendo {removed_count} entradas expiradas")
            return True
        
        # Tercero: expulsar entradas LRU hasta tener espacio
        while (self.current_size_bytes + required_bytes > self.max_size_bytes and 
               len(self._cache) > 0):
            # OrderedDict mantiene orden de inserción/acceso
            # El primer elemento es el menos usado recientemente
            lru_key = next(iter(self._cache))
            self._remove_entry(lru_key)
            self.evictions += 1
            removed_count += 1
        
        space_freed = initial_size - self.current_size_bytes
        self.logger.debug(f"Liberados {space_freed/1024:.1f}KB removiendo {removed_count} entradas")
        
        return self.current_size_bytes + required_bytes <= self.max_size_bytes
    
    def _remove_entry(self, key: str):
        """Remover entrada del cache"""
        if key in self._cache:
            entry = self._cache[key]
            self.current_size_bytes -= entry.size_bytes
            del self._cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del cache
        
        Args:
            key: Clave de búsqueda
            
        Returns:
            Optional[Any]: Valor si existe y no ha expirado, None en caso contrario
        """
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            
            entry = self._cache[key]
            
            # Verificar expiración
            if entry.is_expired():
                self._remove_entry(key)
                self.misses += 1
                return None
            
            # Actualizar acceso y reordenar (LRU)
            entry.touch()
            self._cache.move_to_end(key)  # Mover al final (más reciente)
            
            self.hits += 1
            return entry.value
    
    def put(self, key: str, value: Any, ttl_hours: Optional[int] = None) -> bool:
        """
        Almacenar valor en cache
        
        Args:
            key: Clave única
            value: Valor a almacenar
            ttl_hours: TTL personalizado en horas (usa default si es None)
            
        Returns:
            bool: True si se almacenó exitosamente
        """
        with self._lock:
            try:
                # Calcular tamaño y TTL
                size_bytes = self._calculate_size(value)
                ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
                expires_at = datetime.now() + ttl if ttl.total_seconds() > 0 else None
                
                # Verificar si el objeto es demasiado grande
                if size_bytes > self.max_size_bytes * 0.5:  # No más del 50% del cache
                    self.logger.warning(f"Objeto demasiado grande para cache: {size_bytes/1024:.1f}KB")
                    return False
                
                # Hacer espacio si es necesario
                if not self._make_room(size_bytes):
                    self.logger.warning("No se pudo hacer espacio en cache")
                    return False
                
                # Crear entrada
                entry = CacheEntry(
                    value=value,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    access_count=0,
                    ttl_expires=expires_at,
                    size_bytes=size_bytes
                )
                
                # Remover entrada existente si existe
                if key in self._cache:
                    self._remove_entry(key)
                
                # Almacenar nueva entrada
                self._cache[key] = entry
                self.current_size_bytes += size_bytes
                
                self.logger.debug(f"Almacenado en cache: {key} ({size_bytes/1024:.1f}KB)")
                return True
                
            except Exception as e:
                self.logger.error(f"Error almacenando en cache {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """
        Eliminar entrada específica del cache
        
        Args:
            key: Clave a eliminar
            
        Returns:
            bool: True si se eliminó, False si no existía
        """
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                self.logger.debug(f"Eliminado del cache: {key}")
                return True
            return False
    
    def clear(self):
        """Limpiar todo el cache"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            self.current_size_bytes = 0
            self.logger.info(f"Cache limpiado - {cleared_count} entradas removidas")
    
    def cleanup_expired(self) -> int:
        """
        Limpiar entradas expiradas
        
        Returns:
            int: Número de entradas removidas
        """
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key)
            
            if expired_keys:
                self.logger.debug(f"Limpiadas {len(expired_keys)} entradas expiradas")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas detalladas del cache
        
        Returns:
            Dict con métricas y estadísticas
        """
        with self._lock:
            total_requests = self.hits + self.misses
            hit_ratio = self.hits / total_requests if total_requests > 0 else 0.0
            
            # Estadísticas de entradas
            entry_ages = []
            entry_access_counts = []
            
            for entry in self._cache.values():
                age_seconds = (datetime.now() - entry.created_at).total_seconds()
                entry_ages.append(age_seconds)
                entry_access_counts.append(entry.access_count)
            
            avg_age = sum(entry_ages) / len(entry_ages) if entry_ages else 0
            avg_access_count = sum(entry_access_counts) / len(entry_access_counts) if entry_access_counts else 0
            
            uptime = datetime.now() - self.created_at
            
            return {
                "performance": {
                    "hits": self.hits,
                    "misses": self.misses,
                    "hit_ratio": round(hit_ratio, 3),
                    "evictions": self.evictions
                },
                "memory": {
                    "current_size_mb": round(self.current_size_bytes / 1024 / 1024, 2),
                    "max_size_mb": round(self.max_size_bytes / 1024 / 1024, 2),
                    "usage_percent": round((self.current_size_bytes / self.max_size_bytes) * 100, 1),
                    "entry_count": len(self._cache)
                },
                "entries": {
                    "avg_age_seconds": round(avg_age, 1),
                    "avg_access_count": round(avg_access_count, 1),
                    "oldest_entry_age": max(entry_ages) if entry_ages else 0,
                    "most_accessed_count": max(entry_access_counts) if entry_access_counts else 0
                },
                "config": {
                    "max_size_mb": round(self.max_size_bytes / 1024 / 1024, 2),
                    "default_ttl_hours": self.default_ttl.total_seconds() / 3600,
                    "cleanup_threshold": self.cleanup_threshold
                },
                "uptime_hours": round(uptime.total_seconds() / 3600, 2)
            }
    
    def get_top_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener entradas más accedidas
        
        Args:
            limit: Número máximo de entradas a retornar
            
        Returns:
            Lista de entradas con sus estadísticas
        """
        with self._lock:
            entries_info = []
            
            for key, entry in self._cache.items():
                entries_info.append({
                    "key": key,
                    "access_count": entry.access_count,
                    "size_kb": round(entry.size_bytes / 1024, 2),
                    "age_minutes": round((datetime.now() - entry.created_at).total_seconds() / 60, 1),
                    "last_access_minutes": round((datetime.now() - entry.last_accessed).total_seconds() / 60, 1),
                    "expires_in_minutes": round((entry.ttl_expires - datetime.now()).total_seconds() / 60, 1) if entry.ttl_expires else None
                })
            
            # Ordenar por número de accesos (descendente)
            entries_info.sort(key=lambda x: x["access_count"], reverse=True)
            
            return entries_info[:limit]
    
    def should_cleanup(self) -> bool:
        """
        Verificar si se debe ejecutar limpieza automática
        
        Returns:
            bool: True si se debe limpiar
        """
        usage_ratio = self.current_size_bytes / self.max_size_bytes
        return usage_ratio >= self.cleanup_threshold
    
    def contains(self, key: str) -> bool:
        """
        Verificar si una clave existe en el cache (sin afectar LRU)
        
        Args:
            key: Clave a verificar
            
        Returns:
            bool: True si existe y no ha expirado
        """
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            return not entry.is_expired()
    
    def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Obtener lista de claves en el cache
        
        Args:
            pattern: Patrón opcional para filtrar claves
            
        Returns:
            Lista de claves que coinciden
        """
        with self._lock:
            keys = list(self._cache.keys())
            
            if pattern:
                import fnmatch
                keys = [key for key in keys if fnmatch.fnmatch(key, pattern)]
            
            return keys


# Funciones de conveniencia
def create_memory_cache(max_size_mb: int = 50, ttl_hours: int = 1) -> MemoryCache:
    """
    Crear instancia de MemoryCache con configuración
    
    Args:
        max_size_mb: Tamaño máximo en MB
        ttl_hours: TTL por defecto en horas
        
    Returns:
        MemoryCache: Instancia configurada
    """
    return MemoryCache(max_size_mb=max_size_mb, default_ttl_hours=ttl_hours)