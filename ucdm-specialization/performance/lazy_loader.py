#!/usr/bin/env python3
"""
Lazy Index Loader - Sistema de carga perezosa con análisis de dependencias
Optimiza la carga de índices basándose en patrones de uso y dependencias
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio

@dataclass
class LoadRequest:
    """Solicitud de carga de índice"""
    index_name: str
    priority: int
    requested_at: datetime
    requester: str
    callback: Optional[Callable] = None
    dependencies_resolved: bool = False

@dataclass
class LoadStats:
    """Estadísticas de carga de un índice"""
    index_name: str
    load_count: int = 0
    total_load_time_ms: float = 0.0
    avg_load_time_ms: float = 0.0
    last_loaded: Optional[datetime] = None
    last_access: Optional[datetime] = None
    access_frequency: float = 0.0
    dependency_level: int = 0

class LazyIndexLoader:
    """
    Cargador lazy de índices con análisis de dependencias
    
    Características:
    - Análisis de grafo de dependencias
    - Cola de prioridades para carga optimizada
    - Pre-carga predictiva basada en patrones
    - Métricas de uso para optimización automática
    - Carga asíncrona no bloqueante
    """
    
    def __init__(self, indices_dir: str = "data/indices", 
                 auto_preload: bool = True, dependency_analysis: bool = True):
        """
        Inicializar lazy loader
        
        Args:
            indices_dir: Directorio de índices
            auto_preload: Pre-cargar índices críticos automáticamente
            dependency_analysis: Habilitar análisis de dependencias
        """
        self.indices_dir = Path(indices_dir)
        self.auto_preload = auto_preload
        self.dependency_analysis = dependency_analysis
        
        # Estado interno
        self._loaded_indices: Dict[str, Any] = {}
        self._load_queue: deque[LoadRequest] = deque()
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._load_stats: Dict[str, LoadStats] = {}
        self._usage_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Configuration
        self._preload_threshold = 5  # Cargar automáticamente si se usa >5 veces/hora
        self._dependency_depth_limit = 3  # Máximo nivel de dependencias a resolver
        
        # Logging
        self.logger = self._setup_logging()
        
        # Inicialización
        self._discover_indices()
        if self.dependency_analysis:
            self._build_dependency_graph()
        if self.auto_preload:
            self._preload_critical_indices()
        
        self.logger.info(f"LazyIndexLoader inicializado - {len(self._load_stats)} índices descubiertos")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging"""
        logger = logging.getLogger(f"{__name__}.LazyIndexLoader")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _discover_indices(self):
        """Descubrir archivos de índices disponibles"""
        if not self.indices_dir.exists():
            self.logger.warning(f"Directorio de índices no existe: {self.indices_dir}")
            return
        
        index_files = list(self.indices_dir.glob("*.json"))
        
        for index_file in index_files:
            index_name = index_file.stem
            
            # Crear estadísticas iniciales
            self._load_stats[index_name] = LoadStats(
                index_name=index_name,
                dependency_level=self._calculate_dependency_level(index_name)
            )
        
        self.logger.debug(f"Descubiertos {len(self._load_stats)} archivos de índices")
    
    def _calculate_dependency_level(self, index_name: str) -> int:
        """Calcular nivel de dependencia basado en el nombre del índice"""
        # Mapeo de prioridades específicas para UCDM
        priority_map = {
            'ucdm_comprehensive_index': 0,  # Índice raíz
            'lesson_mapper': 1,
            'lesson_date_mapper': 1,
            'concepts_index': 1,
            'concept_to_lessons_index': 2,
            '365_lessons_indexed': 2,
            '365_lessons_advanced': 3
        }
        
        return priority_map.get(index_name, 2)  # Default nivel medio
    
    def _build_dependency_graph(self):
        """Construir grafo de dependencias entre índices"""
        # Definir dependencias conocidas del sistema UCDM
        known_dependencies = {
            'lesson_mapper': ['ucdm_comprehensive_index'],
            'lesson_date_mapper': ['lesson_mapper'],
            'concept_to_lessons_index': ['concepts_index'],
            '365_lessons_indexed': ['lesson_mapper'],
            '365_lessons_advanced': ['365_lessons_indexed'],
            'concepts_index': ['ucdm_comprehensive_index']
        }
        
        # Construir grafo directo y reverso
        for index_name, deps in known_dependencies.items():
            if index_name in self._load_stats:
                for dep in deps:
                    if dep in self._load_stats:
                        self._dependency_graph[index_name].add(dep)
                        self._reverse_dependencies[dep].add(index_name)
        
        self.logger.debug(f"Grafo de dependencias construido con {len(self._dependency_graph)} relaciones")
    
    def _preload_critical_indices(self):
        """Pre-cargar índices críticos automáticamente"""
        critical_indices = ['ucdm_comprehensive_index', 'lesson_mapper', 'concepts_index']
        
        for index_name in critical_indices:
            if index_name in self._load_stats:
                try:
                    self._load_index_sync(index_name, preload=True)
                except Exception as e:
                    self.logger.warning(f"Error pre-cargando {index_name}: {e}")
    
    async def load_index_async(self, index_name: str, requester: str = "default",
                              callback: Optional[Callable] = None) -> Optional[Any]:
        """
        Cargar índice de forma asíncrona
        
        Args:
            index_name: Nombre del índice
            requester: Identificador del solicitante
            callback: Función de callback opcional
            
        Returns:
            Optional[Any]: Datos del índice si está disponible
        """
        with self._lock:
            # Verificar si ya está cargado
            if index_name in self._loaded_indices:
                self._record_access(index_name, requester)
                return self._loaded_indices[index_name]
            
            # Crear solicitud de carga
            request = LoadRequest(
                index_name=index_name,
                priority=self._calculate_load_priority(index_name),
                requested_at=datetime.now(),
                requester=requester,
                callback=callback
            )
            
            # Agregar a cola de carga
            self._add_to_load_queue(request)
            
            # Procesar cola
            return await self._process_load_queue()
    
    def load_index_sync(self, index_name: str, requester: str = "default") -> Optional[Any]:
        """Cargar índice de forma síncrona"""
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.load_index_async(index_name, requester)
        )
    
    def _load_index_sync(self, index_name: str, preload: bool = False) -> Optional[Any]:
        """Carga síncrona interna"""
        if index_name in self._loaded_indices and not preload:
            return self._loaded_indices[index_name]
        
        start_time = datetime.now()
        
        try:
            # Resolver dependencias primero
            if self.dependency_analysis:
                dependencies = self._get_dependencies(index_name)
                for dep in dependencies:
                    if dep not in self._loaded_indices:
                        self._load_index_sync(dep, preload=False)
            
            # Cargar archivo
            index_file = self.indices_dir / f"{index_name}.json"
            if not index_file.exists():
                self.logger.warning(f"Archivo de índice no encontrado: {index_file}")
                return None
            
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Almacenar en memoria
            self._loaded_indices[index_name] = data
            
            # Actualizar estadísticas
            load_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_load_stats(index_name, load_time, preload)
            
            self.logger.debug(f"Índice {'pre-' if preload else ''}cargado: {index_name} ({load_time:.1f}ms)")
            return data
            
        except Exception as e:
            self.logger.error(f"Error cargando índice {index_name}: {e}")
            return None
    
    def _calculate_load_priority(self, index_name: str) -> int:
        """Calcular prioridad de carga"""
        base_priority = 10 - self._load_stats[index_name].dependency_level
        
        # Bonificación por frecuencia de acceso
        frequency_bonus = min(5, int(self._load_stats[index_name].access_frequency))
        
        # Bonificación por dependientes
        dependents_count = len(self._reverse_dependencies.get(index_name, set()))
        dependents_bonus = min(3, dependents_count)
        
        return base_priority + frequency_bonus + dependents_bonus
    
    def _add_to_load_queue(self, request: LoadRequest):
        """Agregar solicitud a cola ordenada por prioridad"""
        # Insertar manteniendo orden de prioridad (mayor prioridad primero)
        inserted = False
        for i, existing_request in enumerate(self._load_queue):
            if request.priority > existing_request.priority:
                self._load_queue.insert(i, request)
                inserted = True
                break
        
        if not inserted:
            self._load_queue.append(request)
    
    async def _process_load_queue(self) -> Optional[Any]:
        """Procesar cola de carga de forma asíncrona"""
        if not self._load_queue:
            return None
        
        # Procesar solicitud de mayor prioridad
        request = self._load_queue.popleft()
        
        # Cargar índice
        data = self._load_index_sync(request.index_name)
        
        # Ejecutar callback si existe
        if request.callback:
            try:
                if asyncio.iscoroutinefunction(request.callback):
                    await request.callback(request.index_name, data)
                else:
                    request.callback(request.index_name, data)
            except Exception as e:
                self.logger.warning(f"Error en callback para {request.index_name}: {e}")
        
        return data
    
    def _get_dependencies(self, index_name: str, visited: Optional[Set[str]] = None) -> List[str]:
        """Obtener lista de dependencias en orden de carga"""
        if visited is None:
            visited = set()
        
        if index_name in visited:
            return []  # Evitar ciclos
        
        visited.add(index_name)
        dependencies = []
        
        # Obtener dependencias directas
        direct_deps = self._dependency_graph.get(index_name, set())
        
        for dep in direct_deps:
            # Agregar dependencias de la dependencia (recursivo)
            sub_deps = self._get_dependencies(dep, visited.copy())
            dependencies.extend(sub_deps)
            
            # Agregar la dependencia misma
            if dep not in dependencies:
                dependencies.append(dep)
        
        return dependencies
    
    def _record_access(self, index_name: str, requester: str):
        """Registrar acceso para análisis de patrones"""
        now = datetime.now()
        
        # Actualizar patrón de uso
        self._usage_patterns[index_name].append(now)
        
        # Mantener solo últimas 50 entradas
        if len(self._usage_patterns[index_name]) > 50:
            self._usage_patterns[index_name] = self._usage_patterns[index_name][-50:]
        
        # Actualizar estadísticas
        if index_name in self._load_stats:
            self._load_stats[index_name].last_access = now
            
            # Calcular frecuencia de acceso (accesos por hora en las últimas 24h)
            recent_accesses = [
                access for access in self._usage_patterns[index_name]
                if now - access <= timedelta(hours=24)
            ]
            self._load_stats[index_name].access_frequency = len(recent_accesses) / 24.0
    
    def _update_load_stats(self, index_name: str, load_time_ms: float, preload: bool = False):
        """Actualizar estadísticas de carga"""
        if index_name not in self._load_stats:
            return
        
        stats = self._load_stats[index_name]
        
        if not preload:  # No contar preloads en estadísticas de uso
            stats.load_count += 1
            stats.total_load_time_ms += load_time_ms
            stats.avg_load_time_ms = stats.total_load_time_ms / stats.load_count
        
        stats.last_loaded = datetime.now()
    
    def predict_preload_candidates(self, limit: int = 3) -> List[str]:
        """
        Predecir índices candidatos para pre-carga
        
        Args:
            limit: Número máximo de candidatos
            
        Returns:
            List[str]: Nombres de índices candidatos
        """
        candidates = []
        
        for index_name, stats in self._load_stats.items():
            if index_name not in self._loaded_indices:
                # Calcular score de predicción
                frequency_score = min(10, stats.access_frequency * 2)
                dependency_score = len(self._reverse_dependencies.get(index_name, set()))
                recency_score = 0
                
                if stats.last_access:
                    hours_since_access = (datetime.now() - stats.last_access).total_seconds() / 3600
                    recency_score = max(0, 5 - hours_since_access)
                
                total_score = frequency_score + dependency_score + recency_score
                
                candidates.append((index_name, total_score))
        
        # Ordenar por score y retornar top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [name for name, score in candidates[:limit]]
    
    def unload_unused_indices(self, unused_threshold_hours: int = 2) -> List[str]:
        """
        Descargar índices no usados recientemente
        
        Args:
            unused_threshold_hours: Horas sin uso para considerar descarga
            
        Returns:
            List[str]: Nombres de índices descargados
        """
        threshold = datetime.now() - timedelta(hours=unused_threshold_hours)
        unloaded = []
        
        with self._lock:
            indices_to_unload = []
            
            for index_name in list(self._loaded_indices.keys()):
                stats = self._load_stats.get(index_name)
                if not stats:
                    continue
                
                # No descargar índices críticos (nivel 0-1)
                if stats.dependency_level <= 1:
                    continue
                
                # Verificar si no se ha usado recientemente
                last_used = stats.last_access or stats.last_loaded
                if last_used and last_used < threshold:
                    indices_to_unload.append(index_name)
            
            # Descargar índices
            for index_name in indices_to_unload:
                del self._loaded_indices[index_name]
                unloaded.append(index_name)
        
        if unloaded:
            self.logger.debug(f"Descargados {len(unloaded)} índices no usados")
        
        return unloaded
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas completas de carga"""
        with self._lock:
            total_loaded = len(self._loaded_indices)
            total_available = len(self._load_stats)
            
            # Calcular estadísticas agregadas
            total_load_time = sum(stats.total_load_time_ms for stats in self._load_stats.values())
            total_loads = sum(stats.load_count for stats in self._load_stats.values())
            avg_load_time = total_load_time / total_loads if total_loads > 0 else 0
            
            # Encontrar índices más usados
            most_used = sorted(
                self._load_stats.items(),
                key=lambda x: x[1].access_frequency,
                reverse=True
            )[:5]
            
            return {
                "summary": {
                    "indices_loaded": total_loaded,
                    "indices_available": total_available,
                    "load_efficiency": round(total_loaded / total_available, 2) if total_available > 0 else 0,
                    "avg_load_time_ms": round(avg_load_time, 2),
                    "total_loads": total_loads
                },
                "most_used_indices": [
                    {
                        "name": name,
                        "access_frequency": round(stats.access_frequency, 2),
                        "load_count": stats.load_count,
                        "avg_load_time_ms": round(stats.avg_load_time_ms, 2)
                    }
                    for name, stats in most_used
                ],
                "dependency_graph_size": len(self._dependency_graph),
                "queue_size": len(self._load_queue),
                "preload_candidates": self.predict_preload_candidates()
            }
    
    def is_loaded(self, index_name: str) -> bool:
        """Verificar si un índice está cargado"""
        return index_name in self._loaded_indices
    
    def get_loaded_indices(self) -> List[str]:
        """Obtener lista de índices cargados"""
        return list(self._loaded_indices.keys())


def create_lazy_loader(indices_dir: str = "data/indices", auto_preload: bool = True) -> LazyIndexLoader:
    """
    Crear instancia de LazyIndexLoader
    
    Args:
        indices_dir: Directorio de índices
        auto_preload: Pre-cargar índices críticos
        
    Returns:
        LazyIndexLoader: Instancia configurada
    """
    return LazyIndexLoader(indices_dir=indices_dir, auto_preload=auto_preload)