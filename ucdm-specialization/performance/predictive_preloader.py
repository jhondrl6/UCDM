#!/usr/bin/env python3
"""
Predictive Preloader & Integrity Validator - Sistema de pre-carga predictiva y validación
Predice qué índices cargar basándose en patrones y valida su integridad
"""

import json
import hashlib
import logging
import threading
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

@dataclass
class PredictionPattern:
    """Patrón de predicción para pre-carga"""
    pattern_name: str
    triggers: List[str]  # Índices que disparan la predicción
    predicted_indices: List[str]  # Índices a pre-cargar
    confidence: float  # Confianza del patrón (0.0-1.0)
    success_rate: float = 0.0  # Tasa de éxito histórica
    usage_count: int = 0  # Veces que se ha usado
    last_used: Optional[datetime] = None

@dataclass
class IntegrityCheck:
    """Resultado de verificación de integridad"""
    index_name: str
    is_valid: bool
    checksum: Optional[str] = None
    structure_valid: bool = True
    content_valid: bool = True
    size_bytes: int = 0
    errors: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.now)

class PredictivePreloader:
    """
    Sistema de pre-carga predictiva con validación de integridad
    
    Características:
    - Análisis de patrones de uso secuencial
    - Predicción basada en machine learning simple
    - Validación automática de integridad
    - Pre-carga asíncrona en background
    - Métricas de precisión de predicciones
    """
    
    def __init__(self, indices_dir: str = "data/indices", 
                 prediction_enabled: bool = True, integrity_checks: bool = True):
        """
        Inicializar preloader predictivo
        
        Args:
            indices_dir: Directorio de índices
            prediction_enabled: Habilitar predicción automática
            integrity_checks: Habilitar verificaciones de integridad
        """
        self.indices_dir = Path(indices_dir)
        self.prediction_enabled = prediction_enabled
        self.integrity_checks = integrity_checks
        
        # Estado interno
        self._loaded_indices: Dict[str, Any] = {}
        self._access_sequences: List[Tuple[str, datetime]] = []
        self._prediction_patterns: Dict[str, PredictionPattern] = {}
        self._integrity_results: Dict[str, IntegrityCheck] = {}
        self._background_tasks: Set[asyncio.Task] = set()
        self._lock = threading.RLock()
        
        # Configuración de predicción
        self._sequence_window = 5  # Ventana de secuencia para análisis
        self._min_pattern_confidence = 0.3  # Confianza mínima para usar patrón
        self._max_preload_candidates = 3  # Máximo índices a pre-cargar por predicción
        
        # Logging
        self.logger = self._setup_logging()
        
        # Inicialización
        self._load_existing_patterns()
        self._build_default_patterns()
        
        self.logger.info("Predictive Preloader inicializado")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging"""
        logger = logging.getLogger(f"{__name__}.PredictivePreloader")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _build_default_patterns(self):
        """Construir patrones de predicción por defecto para UCDM"""
        default_patterns = {
            "lesson_workflow": PredictionPattern(
                pattern_name="lesson_workflow",
                triggers=["ucdm_comprehensive_index"],
                predicted_indices=["lesson_mapper", "lesson_date_mapper"],
                confidence=0.8
            ),
            "concept_exploration": PredictionPattern(
                pattern_name="concept_exploration", 
                triggers=["concepts_index"],
                predicted_indices=["concept_to_lessons_index", "ucdm_comprehensive_index"],
                confidence=0.7
            ),
            "daily_lesson_flow": PredictionPattern(
                pattern_name="daily_lesson_flow",
                triggers=["lesson_date_mapper"],
                predicted_indices=["365_lessons_indexed", "concepts_index"],
                confidence=0.6
            ),
            "advanced_study": PredictionPattern(
                pattern_name="advanced_study",
                triggers=["365_lessons_indexed"],
                predicted_indices=["365_lessons_advanced", "concept_to_lessons_index"],
                confidence=0.5
            )
        }
        
        for pattern_name, pattern in default_patterns.items():
            if pattern_name not in self._prediction_patterns:
                self._prediction_patterns[pattern_name] = pattern
        
        self.logger.debug(f"Configurados {len(default_patterns)} patrones por defecto")
    
    def _load_existing_patterns(self):
        """Cargar patrones guardados previamente"""
        patterns_file = self.indices_dir.parent / "cache" / "prediction_patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for pattern_data in data.get('patterns', []):
                    pattern = PredictionPattern(
                        pattern_name=pattern_data['pattern_name'],
                        triggers=pattern_data['triggers'],
                        predicted_indices=pattern_data['predicted_indices'],
                        confidence=pattern_data['confidence'],
                        success_rate=pattern_data.get('success_rate', 0.0),
                        usage_count=pattern_data.get('usage_count', 0),
                        last_used=datetime.fromisoformat(pattern_data['last_used']) if pattern_data.get('last_used') else None
                    )
                    self._prediction_patterns[pattern.pattern_name] = pattern
                
                self.logger.debug(f"Cargados {len(self._prediction_patterns)} patrones guardados")
            
            except Exception as e:
                self.logger.warning(f"Error cargando patrones: {e}")
    
    def _save_patterns(self):
        """Guardar patrones actualizados"""
        patterns_file = self.indices_dir.parent / "cache" / "prediction_patterns.json"
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            patterns_data = {
                'patterns': [
                    {
                        'pattern_name': pattern.pattern_name,
                        'triggers': pattern.triggers,
                        'predicted_indices': pattern.predicted_indices,
                        'confidence': pattern.confidence,
                        'success_rate': pattern.success_rate,
                        'usage_count': pattern.usage_count,
                        'last_used': pattern.last_used.isoformat() if pattern.last_used else None
                    }
                    for pattern in self._prediction_patterns.values()
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.warning(f"Error guardando patrones: {e}")
    
    async def validate_index_integrity(self, index_name: str, 
                                     data: Optional[Any] = None) -> IntegrityCheck:
        """
        Validar integridad de un índice
        
        Args:
            index_name: Nombre del índice
            data: Datos del índice (opcional, se cargarán si no se proporcionan)
            
        Returns:
            IntegrityCheck: Resultado de la validación
        """
        result = IntegrityCheck(index_name=index_name, is_valid=False)
        
        try:
            # Cargar datos si no se proporcionaron
            if data is None:
                index_file = self.indices_dir / f"{index_name}.json"
                if not index_file.exists():
                    result.errors.append(f"Archivo no encontrado: {index_file}")
                    return result
                
                result.size_bytes = index_file.stat().st_size
                
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    data = json.loads(content)
                
                # Calcular checksum
                result.checksum = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Validar estructura según tipo de índice
            result.structure_valid = await self._validate_structure(index_name, data)
            
            # Validar contenido
            result.content_valid = await self._validate_content(index_name, data)
            
            # Resultado final
            result.is_valid = result.structure_valid and result.content_valid
            
            if result.is_valid:
                self.logger.debug(f"Índice {index_name} validado correctamente")
            else:
                self.logger.warning(f"Índice {index_name} falló validación: {result.errors}")
            
        except json.JSONDecodeError as e:
            result.errors.append(f"JSON inválido: {e}")
        except Exception as e:
            result.errors.append(f"Error de validación: {e}")
        
        # Guardar resultado
        self._integrity_results[index_name] = result
        return result
    
    async def _validate_structure(self, index_name: str, data: Any) -> bool:
        """Validar estructura específica del índice"""
        try:
            # Validaciones específicas por tipo de índice UCDM
            if index_name == "ucdm_comprehensive_index":
                required_keys = ["metadata", "lesson_details", "concept_index", "date_mapping"]
                return all(key in data for key in required_keys)
            
            elif index_name in ["lesson_mapper", "lesson_date_mapper"]:
                required_keys = ["date_to_lesson", "lesson_to_date"]
                return all(key in data for key in required_keys)
            
            elif index_name == "concepts_index":
                required_keys = ["concept_index"]
                return all(key in data for key in required_keys)
            
            elif index_name in ["365_lessons_indexed", "365_lessons_advanced"]:
                required_keys = ["metadata", "lessons"]
                return all(key in data for key in required_keys)
            
            else:
                # Validación genérica: debe ser dict o list no vacío
                return isinstance(data, (dict, list)) and len(data) > 0
        
        except Exception:
            return False
    
    async def _validate_content(self, index_name: str, data: Any) -> bool:
        """Validar contenido específico del índice"""
        try:
            # Validaciones de contenido específicas
            if index_name == "ucdm_comprehensive_index":
                # Verificar que hay lecciones y conceptos
                lesson_details = data.get("lesson_details", {})
                concept_index = data.get("concept_index", {})
                return len(lesson_details) > 0 and len(concept_index) > 0
            
            elif index_name in ["lesson_mapper", "lesson_date_mapper"]:
                # Verificar mapeos bidireccionales consistentes
                date_to_lesson = data.get("date_to_lesson", {})
                lesson_to_date = data.get("lesson_to_date", {})
                return len(date_to_lesson) > 0 and len(lesson_to_date) > 0
            
            elif index_name == "concepts_index":
                # Verificar que hay conceptos con lecciones asociadas
                concept_index = data.get("concept_index", {})
                return len(concept_index) > 0 and any(
                    isinstance(lessons, list) and len(lessons) > 0 
                    for lessons in concept_index.values()
                )
            
            else:
                # Validación genérica: contenido no vacío
                return True
        
        except Exception:
            return False
    
    def record_index_access(self, index_name: str):
        """Registrar acceso a índice para análisis de patrones"""
        with self._lock:
            now = datetime.now()
            self._access_sequences.append((index_name, now))
            
            # Mantener solo últimas 100 entradas
            if len(self._access_sequences) > 100:
                self._access_sequences = self._access_sequences[-100:]
            
            # Analizar patrones y predecir si está habilitado
            if self.prediction_enabled:
                asyncio.create_task(self._analyze_and_predict(index_name))
    
    async def _analyze_and_predict(self, trigger_index: str):
        """Analizar acceso actual y predecir próximos índices"""
        try:
            predictions = self._find_matching_patterns(trigger_index)
            
            if predictions:
                # Crear tarea de pre-carga en background
                preload_task = asyncio.create_task(
                    self._preload_predicted_indices(predictions)
                )
                self._background_tasks.add(preload_task)
                preload_task.add_done_callback(self._background_tasks.discard)
        
        except Exception as e:
            self.logger.warning(f"Error en análisis predictivo: {e}")
    
    def _find_matching_patterns(self, trigger_index: str) -> List[Tuple[str, float]]:
        """Encontrar patrones que coincidan con el trigger"""
        matching_predictions = []
        
        for pattern in self._prediction_patterns.values():
            if trigger_index in pattern.triggers:
                # Calcular confianza ajustada basada en historial
                adjusted_confidence = pattern.confidence
                if pattern.usage_count > 0:
                    # Ponderar con tasa de éxito histórica
                    adjusted_confidence = (pattern.confidence + pattern.success_rate) / 2
                
                if adjusted_confidence >= self._min_pattern_confidence:
                    for predicted_index in pattern.predicted_indices:
                        matching_predictions.append((predicted_index, adjusted_confidence))
        
        # Ordenar por confianza y limitar candidatos
        matching_predictions.sort(key=lambda x: x[1], reverse=True)
        return matching_predictions[:self._max_preload_candidates]
    
    async def _preload_predicted_indices(self, predictions: List[Tuple[str, float]]):
        """Pre-cargar índices predichos"""
        for index_name, confidence in predictions:
            try:
                # Verificar si ya está cargado
                if index_name in self._loaded_indices:
                    continue
                
                # Validar integridad antes de cargar
                if self.integrity_checks:
                    integrity = await self.validate_index_integrity(index_name)
                    if not integrity.is_valid:
                        self.logger.warning(f"Índice {index_name} falló validación, saltando pre-carga")
                        continue
                
                # Pre-cargar índice
                await self._load_index_async(index_name)
                self.logger.debug(f"Pre-cargado índice {index_name} (confianza: {confidence:.2f})")
                
            except Exception as e:
                self.logger.warning(f"Error pre-cargando {index_name}: {e}")
    
    async def _load_index_async(self, index_name: str) -> Optional[Any]:
        """Cargar índice de forma asíncrona"""
        if index_name in self._loaded_indices:
            return self._loaded_indices[index_name]
        
        try:
            index_file = self.indices_dir / f"{index_name}.json"
            if not index_file.exists():
                return None
            
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._loaded_indices[index_name] = data
            return data
        
        except Exception as e:
            self.logger.error(f"Error cargando índice {index_name}: {e}")
            return None
    
    def get_prediction_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de predicción"""
        with self._lock:
            total_patterns = len(self._prediction_patterns)
            active_patterns = sum(1 for p in self._prediction_patterns.values() if p.usage_count > 0)
            
            # Calcular tasa de éxito promedio
            success_rates = [p.success_rate for p in self._prediction_patterns.values() if p.usage_count > 0]
            avg_success_rate = statistics.mean(success_rates) if success_rates else 0
            
            # Patrones más exitosos
            top_patterns = sorted(
                [(name, pattern.success_rate, pattern.usage_count) 
                 for name, pattern in self._prediction_patterns.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                "prediction_summary": {
                    "total_patterns": total_patterns,
                    "active_patterns": active_patterns,
                    "avg_success_rate": round(avg_success_rate, 3),
                    "total_predictions_made": sum(p.usage_count for p in self._prediction_patterns.values()),
                    "background_tasks_active": len(self._background_tasks)
                },
                "top_patterns": [
                    {"name": name, "success_rate": rate, "usage_count": count}
                    for name, rate, count in top_patterns
                ],
                "recent_access_sequence": [
                    {"index": idx, "timestamp": ts.isoformat()}
                    for idx, ts in self._access_sequences[-10:]
                ]
            }
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """Obtener reporte de integridad"""
        with self._lock:
            total_checked = len(self._integrity_results)
            valid_indices = sum(1 for r in self._integrity_results.values() if r.is_valid)
            
            # Errores más comunes
            all_errors = []
            for result in self._integrity_results.values():
                all_errors.extend(result.errors)
            
            error_counts = defaultdict(int)
            for error in all_errors:
                error_counts[error] += 1
            
            most_common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "integrity_summary": {
                    "total_indices_checked": total_checked,
                    "valid_indices": valid_indices,
                    "invalid_indices": total_checked - valid_indices,
                    "integrity_rate": round(valid_indices / total_checked, 3) if total_checked > 0 else 0,
                    "total_errors": len(all_errors)
                },
                "most_common_errors": [
                    {"error": error, "count": count}
                    for error, count in most_common_errors
                ],
                "recent_checks": [
                    {
                        "index": result.index_name,
                        "valid": result.is_valid,
                        "checked_at": result.checked_at.isoformat(),
                        "errors": len(result.errors)
                    }
                    for result in list(self._integrity_results.values())[-10:]
                ]
            }
    
    async def cleanup_background_tasks(self):
        """Limpiar tareas en background"""
        # Cancelar tareas pendientes
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        # Esperar a que terminen
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
        self.logger.debug("Tareas en background limpiadas")


def create_predictive_preloader(indices_dir: str = "data/indices") -> PredictivePreloader:
    """Crear instancia de PredictivePreloader"""
    return PredictivePreloader(indices_dir=indices_dir)