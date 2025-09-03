#!/usr/bin/env python3
"""
Cache Manager - Sistema de cacheo multi-nivel para UCDM
Coordina y gestiona estrategias de cacheo L1, L2 y L3
"""

import time
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class CacheConfig:
    """Configuración del sistema de cache"""
    # Memory Cache (L1) Config
    memory_max_size_mb: int = 50
    memory_ttl_hours: int = 1
    memory_cleanup_threshold: float = 0.8
    
    # Disk Cache (L2) Config  
    disk_path: str = "data/cache"
    disk_max_size_gb: int = 2
    disk_ttl_hours: int = 24
    disk_compression: bool = True
    
    # Index Cache (L3) Config
    index_preload_popular: bool = True
    index_dependency_tracking: bool = True
    index_lazy_threshold: float = 0.1
    
    # Performance Config
    metrics_enabled: bool = True
    cleanup_interval_minutes: int = 30
    background_cleanup: bool = True

@dataclass
class CacheMetrics:
    """Métricas del sistema de cache"""
    # Hit/Miss ratios
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    
    # Performance metrics
    total_requests: int = 0
    avg_response_time_ms: float = 0.0
    cache_size_mb: float = 0.0
    
    # Timestamps
    last_cleanup: Optional[datetime] = None
    started_at: Optional[datetime] = None
    
    def hit_ratio(self, level: str = "total") -> float:
        """Calcular hit ratio por nivel o total"""
        if level == "l1":
            total = self.l1_hits + self.l1_misses
            return self.l1_hits / total if total > 0 else 0.0
        elif level == "l2":
            total = self.l2_hits + self.l2_misses  
            return self.l2_hits / total if total > 0 else 0.0
        elif level == "l3":
            total = self.l3_hits + self.l3_misses
            return self.l3_hits / total if total > 0 else 0.0
        else:  # total
            total_hits = self.l1_hits + self.l2_hits + self.l3_hits
            total_misses = self.l1_misses + self.l2_misses + self.l3_misses
            total_requests = total_hits + total_misses
            return total_hits / total_requests if total_requests > 0 else 0.0

class CacheManager:
    """
    Gestor central del sistema de cacheo multi-nivel
    
    Coordina tres niveles de cache:
    - L1 (Memory): Cache en memoria para respuestas frecuentes
    - L2 (Disk): Cache en disco para índices compilados  
    - L3 (Index): Cache lazy para relaciones conceptuales
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.metrics = CacheMetrics(started_at=datetime.now())
        self.logger = self._setup_logging()
        
        # Inicializar caches (será implementado por cada cache específico)
        self.l1_cache = None  # MemoryCache
        self.l2_cache = None  # DiskCache  
        self.l3_cache = None  # IndexCache
        
        # Control de estado
        self.is_running = False
        self.cleanup_task = None
        
        self.logger.info("CacheManager inicializado con configuración multi-nivel")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging específico para cache"""
        logger = logging.getLogger(f"{__name__}.CacheManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def initialize(self) -> bool:
        """
        Inicializar todos los niveles de cache
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            self.logger.info("Inicializando sistema de cache multi-nivel...")
            
            # Crear directorio de cache si no existe
            cache_dir = Path(self.config.disk_path)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # TODO: Inicializar caches específicos cuando estén implementados
            # self.l1_cache = MemoryCache(self.config)
            # self.l2_cache = DiskCache(self.config)  
            # self.l3_cache = IndexCache(self.config)
            
            self.is_running = True
            
            # Iniciar limpieza en background si está habilitada
            if self.config.background_cleanup:
                self.cleanup_task = asyncio.create_task(self._background_cleanup())
            
            self.logger.info(f"✅ Cache manager inicializado - Directorio: {cache_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando cache manager: {e}")
            return False
    
    async def get_or_load(self, key: str, loader_func: Callable, 
                         cache_level: str = "auto", ttl_hours: Optional[int] = None) -> Any:
        """
        Obtener datos del cache o cargar usando función
        
        Args:
            key: Clave única para el cache
            loader_func: Función para cargar datos si no están en cache
            cache_level: Nivel de cache preferido ("l1", "l2", "l3", "auto")
            ttl_hours: TTL personalizado en horas
            
        Returns:
            Any: Datos solicitados
        """
        start_time = time.time()
        
        try:
            self.metrics.total_requests += 1
            
            # Estrategia de búsqueda en niveles
            if cache_level == "auto":
                # Buscar en L1 -> L2 -> L3 -> Cargar
                data = await self._search_multilevel(key)
                if data is not None:
                    return data
            else:
                # Buscar en nivel específico
                data = await self._search_specific_level(key, cache_level)
                if data is not None:
                    return data
            
            # Cache miss - cargar datos
            self.logger.debug(f"Cache miss para key: {key}, cargando...")
            data = await self._execute_loader(loader_func)
            
            # Almacenar en cache apropiado
            await self._store_in_cache(key, data, cache_level, ttl_hours)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error en get_or_load para key {key}: {e}")
            # En caso de error, intentar cargar directamente
            return await self._execute_loader(loader_func)
            
        finally:
            # Actualizar métricas de tiempo
            response_time = (time.time() - start_time) * 1000
            self.metrics.avg_response_time_ms = (
                (self.metrics.avg_response_time_ms * (self.metrics.total_requests - 1) + response_time) 
                / self.metrics.total_requests
            )
    
    async def _search_multilevel(self, key: str) -> Optional[Any]:
        """Buscar en múltiples niveles de cache"""
        # L1 Memory Cache (más rápido)
        if self.l1_cache:
            data = await self._get_from_l1(key)
            if data is not None:
                self.metrics.l1_hits += 1
                return data
            self.metrics.l1_misses += 1
        
        # L2 Disk Cache  
        if self.l2_cache:
            data = await self._get_from_l2(key)
            if data is not None:
                self.metrics.l2_hits += 1
                # Promover a L1 para acceso futuro más rápido
                await self._promote_to_l1(key, data)
                return data
            self.metrics.l2_misses += 1
        
        # L3 Index Cache
        if self.l3_cache:
            data = await self._get_from_l3(key)
            if data is not None:
                self.metrics.l3_hits += 1
                # Opcional: promover a L2 si es frecuente
                return data
            self.metrics.l3_misses += 1
        
        return None
    
    async def _search_specific_level(self, key: str, level: str) -> Optional[Any]:
        """Buscar en nivel específico de cache"""
        if level == "l1" and self.l1_cache:
            data = await self._get_from_l1(key)
            if data is not None:
                self.metrics.l1_hits += 1
                return data
            self.metrics.l1_misses += 1
        elif level == "l2" and self.l2_cache:
            data = await self._get_from_l2(key)
            if data is not None:
                self.metrics.l2_hits += 1
                return data
            self.metrics.l2_misses += 1
        elif level == "l3" and self.l3_cache:
            data = await self._get_from_l3(key)
            if data is not None:
                self.metrics.l3_hits += 1
                return data
            self.metrics.l3_misses += 1
        
        return None
    
    async def _execute_loader(self, loader_func: Callable) -> Any:
        """Ejecutar función de carga de datos"""
        if asyncio.iscoroutinefunction(loader_func):
            return await loader_func()
        else:
            return loader_func()
    
    async def _store_in_cache(self, key: str, data: Any, level: str, ttl_hours: Optional[int]):
        """Almacenar datos en cache apropiado"""
        # TODO: Implementar cuando los caches específicos estén disponibles
        pass
    
    # Métodos placeholder para caches específicos (implementar con caches reales)
    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """Obtener de L1 Memory Cache"""
        return None
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Obtener de L2 Disk Cache"""
        return None
    
    async def _get_from_l3(self, key: str) -> Optional[Any]:
        """Obtener de L3 Index Cache"""
        return None
    
    async def _promote_to_l1(self, key: str, data: Any):
        """Promover datos de L2/L3 a L1"""
        pass
    
    def invalidate_key(self, key: str, levels: List[str] = ["all"]) -> bool:
        """
        Invalidar clave específica en uno o más niveles
        
        Args:
            key: Clave a invalidar
            levels: Lista de niveles ("l1", "l2", "l3", "all")
            
        Returns:
            bool: True si la invalidación fue exitosa
        """
        try:
            if "all" in levels:
                levels = ["l1", "l2", "l3"]
            
            success = True
            for level in levels:
                if level == "l1" and self.l1_cache:
                    # TODO: Implementar invalidación L1
                    pass
                elif level == "l2" and self.l2_cache:
                    # TODO: Implementar invalidación L2
                    pass
                elif level == "l3" and self.l3_cache:
                    # TODO: Implementar invalidación L3
                    pass
            
            self.logger.info(f"Clave invalidada: {key} en niveles: {levels}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error invalidando clave {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str, levels: List[str] = ["all"]) -> int:
        """
        Invalidar claves que coincidan con patrón
        
        Args:
            pattern: Patrón de búsqueda (ej: "lesson_*", "*_index")
            levels: Lista de niveles a limpiar
            
        Returns:
            int: Número de claves invalidadas
        """
        try:
            invalidated_count = 0
            
            # TODO: Implementar invalidación por patrón en cada cache
            
            self.logger.info(f"Invalidadas {invalidated_count} claves con patrón: {pattern}")
            return invalidated_count
            
        except Exception as e:
            self.logger.error(f"Error invalidando patrón {pattern}: {e}")
            return 0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generar reporte completo de performance
        
        Returns:
            Dict con métricas detalladas del cache
        """
        uptime = datetime.now() - self.metrics.started_at if self.metrics.started_at else timedelta(0)
        
        report = {
            "overview": {
                "uptime_hours": uptime.total_seconds() / 3600,
                "total_requests": self.metrics.total_requests,
                "avg_response_time_ms": round(self.metrics.avg_response_time_ms, 2),
                "cache_size_mb": round(self.metrics.cache_size_mb, 2)
            },
            "hit_ratios": {
                "l1_hit_ratio": round(self.metrics.hit_ratio("l1"), 3),
                "l2_hit_ratio": round(self.metrics.hit_ratio("l2"), 3), 
                "l3_hit_ratio": round(self.metrics.hit_ratio("l3"), 3),
                "total_hit_ratio": round(self.metrics.hit_ratio("total"), 3)
            },
            "detailed_stats": {
                "l1": {"hits": self.metrics.l1_hits, "misses": self.metrics.l1_misses},
                "l2": {"hits": self.metrics.l2_hits, "misses": self.metrics.l2_misses},
                "l3": {"hits": self.metrics.l3_hits, "misses": self.metrics.l3_misses}
            },
            "config": asdict(self.config),
            "last_cleanup": self.metrics.last_cleanup.isoformat() if self.metrics.last_cleanup else None
        }
        
        return report
    
    async def _background_cleanup(self):
        """Tarea de limpieza en background"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
                
                if self.is_running:  # Verificar que aún esté activo
                    await self._cleanup_expired()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en background cleanup: {e}")
    
    async def _cleanup_expired(self):
        """Limpiar entradas expiradas de todos los caches"""
        try:
            self.logger.debug("Iniciando limpieza de cache...")
            
            # TODO: Implementar limpieza para cada cache específico
            
            self.metrics.last_cleanup = datetime.now()
            self.logger.debug("Limpieza de cache completada")
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de cache: {e}")
    
    async def shutdown(self):
        """Cerrar cache manager de forma segura"""
        try:
            self.logger.info("Cerrando cache manager...")
            
            self.is_running = False
            
            # Cancelar tarea de limpieza
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # TODO: Cerrar caches específicos de forma segura
            
            self.logger.info("✅ Cache manager cerrado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error cerrando cache manager: {e}")


# Función de conveniencia para crear instancia configurada
def create_cache_manager(config: Optional[Dict[str, Any]] = None) -> CacheManager:
    """
    Crear instancia de CacheManager con configuración opcional
    
    Args:
        config: Diccionario de configuración opcional
        
    Returns:
        CacheManager: Instancia configurada
    """
    if config:
        cache_config = CacheConfig(**config)
    else:
        cache_config = CacheConfig()
    
    return CacheManager(cache_config)