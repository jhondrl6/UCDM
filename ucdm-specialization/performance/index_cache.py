#!/usr/bin/env python3
"""
Index Cache (L3) - Cache especializado para índices conceptuales y mapeos
Implementa lazy loading y gestión inteligente de relaciones UCDM
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

@dataclass
class IndexDependency:
    """Dependencia entre índices"""
    index_name: str
    dependent_on: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    load_priority: int = 0
    usage_frequency: float = 0.0
    last_used: Optional[datetime] = None

@dataclass
class IndexSegment:
    """Segmento de índice cargado"""
    name: str
    data: Any
    loaded_at: datetime
    size_bytes: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    
    def touch(self):
        """Actualizar acceso"""
        self.last_accessed = datetime.now()
        self.access_count += 1

class IndexCache:
    """
    Cache L3 especializado para índices UCDM con lazy loading
    
    Características:
    - Lazy loading basado en dependencias
    - Pre-carga predictiva de índices relacionados
    - Gestión de relaciones conceptuales
    - Tracking de patrones de uso
    - Segmentación inteligente de índices grandes
    """
    
    def __init__(self, indices_dir: str = "data/indices", 
                 preload_popular: bool = True, dependency_tracking: bool = True,
                 lazy_threshold: float = 0.1):
        """
        Inicializar cache de índices
        
        Args:
            indices_dir: Directorio de índices
            preload_popular: Pre-cargar índices populares
            dependency_tracking: Habilitar tracking de dependencias
            lazy_threshold: Umbral para lazy loading (0.0-1.0)
        """
        self.indices_dir = Path(indices_dir)
        self.preload_popular = preload_popular
        self.dependency_tracking = dependency_tracking
        self.lazy_threshold = lazy_threshold
        
        # Estado interno
        self._loaded_segments: Dict[str, IndexSegment] = {}
        self._dependencies: Dict[str, IndexDependency] = {}
        self._usage_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.RLock()
        
        # Cache de consultas frecuentes
        self._query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._query_cache_ttl = timedelta(minutes=30)
        
        # Métricas
        self.lazy_loads = 0
        self.preloads = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.dependency_loads = 0
        self.created_at = datetime.now()
        
        # Logging
        self.logger = self._setup_logging()
        
        # Inicialización
        self._discover_indices()
        self._build_dependency_graph()
        
        if self.preload_popular:
            self._preload_popular_indices()
        
        self.logger.info(f"IndexCache inicializado - {len(self._dependencies)} índices descubiertos")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging específico"""
        logger = logging.getLogger(f"{__name__}.IndexCache")
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
            
            # Determinar prioridad basada en el nombre
            priority = self._determine_priority(index_name)
            
            dependency = IndexDependency(
                index_name=index_name,
                load_priority=priority
            )
            
            self._dependencies[index_name] = dependency
            
        self.logger.debug(f"Descubiertos {len(self._dependencies)} archivos de índices")
    
    def _determine_priority(self, index_name: str) -> int:
        """Determinar prioridad de carga basada en el nombre del índice"""
        priority_map = {
            'ucdm_comprehensive_index': 10,  # Más alta
            'lesson_mapper': 8,
            'lesson_date_mapper': 8,
            'concepts_index': 7,
            'concept_to_lessons_index': 7,
            '365_lessons_indexed': 5,
            '365_lessons_advanced': 3
        }
        
        return priority_map.get(index_name, 1)
    
    def _build_dependency_graph(self):
        """Construir grafo de dependencias entre índices"""
        # Definir dependencias conocidas del sistema UCDM
        dependencies = {
            'ucdm_comprehensive_index': [],  # Índice raíz
            'lesson_mapper': ['ucdm_comprehensive_index'],
            'lesson_date_mapper': ['lesson_mapper'],
            'concepts_index': ['ucdm_comprehensive_index'],
            'concept_to_lessons_index': ['concepts_index'],
            '365_lessons_indexed': ['lesson_mapper'],
            '365_lessons_advanced': ['365_lessons_indexed']
        }
        
        # Actualizar dependencias
        for index_name, deps in dependencies.items():
            if index_name in self._dependencies:
                self._dependencies[index_name].dependent_on = deps
                
                # Actualizar dependientes
                for dep in deps:
                    if dep in self._dependencies:
                        if index_name not in self._dependencies[dep].dependents:
                            self._dependencies[dep].dependents.append(index_name)
        
        self.logger.debug("Grafo de dependencias construido")
    
    def _preload_popular_indices(self):
        """Pre-cargar índices populares basados en prioridad"""
        # Obtener índices de alta prioridad
        high_priority = [
            dep for dep in self._dependencies.values() 
            if dep.load_priority >= 7
        ]
        
        # Ordenar por prioridad
        high_priority.sort(key=lambda x: x.load_priority, reverse=True)
        
        preloaded_count = 0
        for dependency in high_priority:
            try:
                if self._load_index_segment(dependency.index_name):
                    preloaded_count += 1
                    self.preloads += 1
            except Exception as e:
                self.logger.warning(f"Error pre-cargando {dependency.index_name}: {e}")
        
        self.logger.info(f"Pre-cargados {preloaded_count} índices populares")
    
    def _load_index_segment(self, index_name: str, force_reload: bool = False) -> bool:
        """
        Cargar segmento de índice desde disco
        
        Args:
            index_name: Nombre del índice
            force_reload: Forzar recarga si ya está cargado
            
        Returns:
            bool: True si se cargó exitosamente
        """
        if not force_reload and index_name in self._loaded_segments:
            return True
        
        index_file = self.indices_dir / f"{index_name}.json"
        if not index_file.exists():
            self.logger.warning(f"Archivo de índice no encontrado: {index_file}")
            return False
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Calcular tamaño aproximado
            size_bytes = index_file.stat().st_size
            
            # Crear segmento
            segment = IndexSegment(
                name=index_name,
                data=data,
                loaded_at=datetime.now(),
                size_bytes=size_bytes,
                dependencies=self._dependencies.get(index_name, IndexDependency(index_name)).dependent_on
            )
            
            self._loaded_segments[index_name] = segment
            self.lazy_loads += 1
            
            self.logger.debug(f"Índice cargado: {index_name} ({size_bytes/1024:.1f}KB)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando índice {index_name}: {e}")
            return False
    
    def _ensure_dependencies_loaded(self, index_name: str) -> bool:
        """Asegurar que las dependencias estén cargadas"""
        if index_name not in self._dependencies:
            return True
        
        dependency = self._dependencies[index_name]
        
        for dep_name in dependency.dependent_on:
            if dep_name not in self._loaded_segments:
                if not self._load_index_segment(dep_name):
                    self.logger.warning(f"No se pudo cargar dependencia {dep_name} para {index_name}")
                    return False
                self.dependency_loads += 1
        
        return True
    
    def _update_usage_pattern(self, index_name: str):
        """Actualizar patrón de uso del índice"""
        now = datetime.now()
        self._usage_patterns[index_name].append(now)
        
        # Mantener solo últimas 100 entradas
        if len(self._usage_patterns[index_name]) > 100:
            self._usage_patterns[index_name] = self._usage_patterns[index_name][-100:]
        
        # Actualizar frecuencia de uso
        if index_name in self._dependencies:
            recent_usage = [
                timestamp for timestamp in self._usage_patterns[index_name]
                if now - timestamp <= timedelta(hours=24)
            ]
            self._dependencies[index_name].usage_frequency = len(recent_usage) / 24.0
            self._dependencies[index_name].last_used = now
    
    def get_index(self, index_name: str, auto_load: bool = True) -> Optional[Any]:
        """
        Obtener índice completo
        
        Args:
            index_name: Nombre del índice
            auto_load: Cargar automáticamente si no está disponible
            
        Returns:
            Optional[Any]: Datos del índice si está disponible
        """
        with self._lock:
            # Verificar cache de consultas
            cache_key = f"index_{index_name}"
            if cache_key in self._query_cache:
                cached_data, cached_at = self._query_cache[cache_key]
                if datetime.now() - cached_at <= self._query_cache_ttl:
                    self.cache_hits += 1
                    return cached_data
            
            # Verificar si está cargado
            if index_name not in self._loaded_segments:
                if not auto_load:
                    self.cache_misses += 1
                    return None
                
                # Cargar dependencias primero
                if not self._ensure_dependencies_loaded(index_name):
                    self.cache_misses += 1
                    return None
                
                # Cargar índice principal
                if not self._load_index_segment(index_name):
                    self.cache_misses += 1
                    return None
            
            segment = self._loaded_segments[index_name]
            segment.touch()
            
            # Actualizar patrón de uso
            self._update_usage_pattern(index_name)
            
            # Actualizar cache de consultas
            self._query_cache[cache_key] = (segment.data, datetime.now())
            
            self.cache_hits += 1
            return segment.data
    
    def get_index_subset(self, index_name: str, filter_func: Callable[[Any], bool]) -> Optional[Any]:
        """
        Obtener subconjunto filtrado de un índice
        
        Args:
            index_name: Nombre del índice
            filter_func: Función de filtrado
            
        Returns:
            Optional[Any]: Subconjunto filtrado
        """
        with self._lock:
            full_index = self.get_index(index_name)
            if full_index is None:
                return None
            
            try:
                # Aplicar filtro según el tipo de datos
                if isinstance(full_index, dict):
                    return {k: v for k, v in full_index.items() if filter_func((k, v))}
                elif isinstance(full_index, list):
                    return [item for item in full_index if filter_func(item)]
                else:
                    return full_index if filter_func(full_index) else None
                    
            except Exception as e:
                self.logger.error(f"Error filtrando índice {index_name}: {e}")
                return None
    
    def search_concepts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Buscar conceptos relacionados con la consulta
        
        Args:
            query: Término de búsqueda
            limit: Límite de resultados
            
        Returns:
            List[Dict]: Conceptos encontrados con metadata
        """
        with self._lock:
            concepts_index = self.get_index('concepts_index')
            if not concepts_index:
                return []
            
            query_lower = query.lower()
            results = []
            
            # Buscar en el índice de conceptos
            concept_data = concepts_index.get('concept_index', {})
            
            for concept, lessons in concept_data.items():
                if query_lower in concept.lower():
                    # Calcular relevancia basada en coincidencia y frecuencia
                    relevance = len(lessons) if isinstance(lessons, list) else 1
                    if concept.lower() == query_lower:
                        relevance *= 2  # Coincidencia exacta
                    
                    results.append({
                        'concept': concept,
                        'lessons': lessons,
                        'relevance': relevance,
                        'exact_match': concept.lower() == query_lower
                    })
            
            # Ordenar por relevancia y limitar
            results.sort(key=lambda x: x['relevance'], reverse=True)
            return results[:limit]
    
    def get_lesson_mappings(self, lesson_number: Optional[int] = None, 
                          date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Obtener mapeos de lección por número o fecha
        
        Args:
            lesson_number: Número de lección
            date: Fecha en formato MM-DD
            
        Returns:
            Optional[Dict]: Información de mapeo
        """
        with self._lock:
            if lesson_number:
                # Buscar por número de lección
                comprehensive_index = self.get_index('ucdm_comprehensive_index')
                if comprehensive_index:
                    lesson_details = comprehensive_index.get('lesson_details', {})
                    return lesson_details.get(str(lesson_number))
            
            elif date:
                # Buscar por fecha
                date_mapper = self.get_index('lesson_date_mapper')
                if date_mapper:
                    date_to_lesson = date_mapper.get('date_to_lesson', {})
                    lesson_num = date_to_lesson.get(date)
                    if lesson_num:
                        return self.get_lesson_mappings(lesson_number=lesson_num)
            
            return None
    
    def invalidate_index(self, index_name: str):
        """Invalidar índice específico"""
        with self._lock:
            if index_name in self._loaded_segments:
                del self._loaded_segments[index_name]
                self.logger.debug(f"Índice invalidado: {index_name}")
            
            # Limpiar cache de consultas relacionadas
            cache_keys_to_remove = [
                key for key in self._query_cache.keys() 
                if index_name in key
            ]
            for key in cache_keys_to_remove:
                del self._query_cache[key]
    
    def reload_index(self, index_name: str) -> bool:
        """Recargar índice desde disco"""
        with self._lock:
            self.invalidate_index(index_name)
            return self._load_index_segment(index_name, force_reload=True)
    
    def get_popular_indices(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtener índices más populares por uso reciente
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            List[Dict]: Índices populares con estadísticas
        """
        with self._lock:
            popular = []
            
            for name, dependency in self._dependencies.items():
                usage_info = {
                    'index_name': name,
                    'usage_frequency': dependency.usage_frequency,
                    'last_used': dependency.last_used,
                    'load_priority': dependency.load_priority,
                    'is_loaded': name in self._loaded_segments
                }
                
                if name in self._loaded_segments:
                    segment = self._loaded_segments[name]
                    usage_info.update({
                        'access_count': segment.access_count,
                        'size_kb': round(segment.size_bytes / 1024, 1),
                        'loaded_at': segment.loaded_at
                    })
                
                popular.append(usage_info)
            
            # Ordenar por frecuencia de uso
            popular.sort(key=lambda x: x['usage_frequency'], reverse=True)
            return popular[:limit]
    
    def cleanup_unused(self, unused_threshold_hours: int = 2) -> int:
        """
        Limpiar índices no usados recientemente
        
        Args:
            unused_threshold_hours: Horas sin uso para considerar limpieza
            
        Returns:
            int: Número de índices limpiados
        """
        with self._lock:
            threshold = datetime.now() - timedelta(hours=unused_threshold_hours)
            indices_to_remove = []
            
            for name, segment in self._loaded_segments.items():
                # No limpiar índices de alta prioridad
                dependency = self._dependencies.get(name)
                if dependency and dependency.load_priority >= 8:
                    continue
                
                # Verificar si no se ha usado recientemente
                last_used = segment.last_accessed or segment.loaded_at
                if last_used < threshold:
                    indices_to_remove.append(name)
            
            # Remover índices no usados
            for name in indices_to_remove:
                del self._loaded_segments[name]
            
            # Limpiar cache de consultas expirado
            now = datetime.now()
            expired_queries = [
                key for key, (_, cached_at) in self._query_cache.items()
                if now - cached_at > self._query_cache_ttl
            ]
            for key in expired_queries:
                del self._query_cache[key]
            
            if indices_to_remove:
                self.logger.debug(f"Limpiados {len(indices_to_remove)} índices no usados")
            
            return len(indices_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache de índices"""
        with self._lock:
            total_requests = self.cache_hits + self.cache_misses
            hit_ratio = self.cache_hits / total_requests if total_requests > 0 else 0.0
            
            loaded_size = sum(segment.size_bytes for segment in self._loaded_segments.values())
            uptime = datetime.now() - self.created_at
            
            return {
                "performance": {
                    "cache_hits": self.cache_hits,
                    "cache_misses": self.cache_misses,
                    "hit_ratio": round(hit_ratio, 3),
                    "lazy_loads": self.lazy_loads,
                    "preloads": self.preloads,
                    "dependency_loads": self.dependency_loads
                },
                "indices": {
                    "discovered": len(self._dependencies),
                    "loaded": len(self._loaded_segments),
                    "loaded_size_kb": round(loaded_size / 1024, 1),
                    "query_cache_size": len(self._query_cache)
                },
                "config": {
                    "preload_popular": self.preload_popular,
                    "dependency_tracking": self.dependency_tracking,
                    "lazy_threshold": self.lazy_threshold
                },
                "uptime_hours": round(uptime.total_seconds() / 3600, 2)
            }


def create_index_cache(indices_dir: str = "data/indices", 
                      preload_popular: bool = True) -> IndexCache:
    """
    Crear instancia de IndexCache con configuración
    
    Args:
        indices_dir: Directorio de índices
        preload_popular: Pre-cargar índices populares
        
    Returns:
        IndexCache: Instancia configurada
    """
    return IndexCache(indices_dir=indices_dir, preload_popular=preload_popular)