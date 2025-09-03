#!/usr/bin/env python3
"""
Sistema de Reconocimiento de Lecciones UCDM
Garantiza identificación precisa y mapeo 1:1 de las 365 lecciones
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import Counter, defaultdict
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

@dataclass
class SequenceReport:
    """Reporte de validación de secuencia numérica"""
    total_expected: int
    total_found: int
    found_lessons: List[int]
    missing_lessons: List[int]
    duplicate_lessons: List[int]
    sequence_completeness: float
    sequence_integrity: bool
    timestamp: str

@dataclass
class DuplicateReport:
    """Reporte de duplicados encontrados"""
    duplicate_count: int
    duplicates_by_lesson: Dict[int, List[Dict]]
    resolution_suggestions: List[str]
    severity_level: str
    timestamp: str

@dataclass
class MappingReport:
    """Reporte de mapeo lección-contenido"""
    total_mappings: int
    successful_mappings: int
    failed_mappings: List[Dict]
    mapping_accuracy: float
    content_quality_issues: List[Dict]
    timestamp: str

@dataclass
class CoverageReport:
    """Reporte de cobertura completa"""
    coverage_percentage: float
    processed_lessons: int
    pending_lessons: List[int]
    problematic_lessons: List[Dict]
    extraction_quality: Dict[str, float]
    recommendations: List[str]
    timestamp: str

class LessonRecognitionEngine:
    """Motor de reconocimiento inteligente de lecciones UCDM"""
    
    def __init__(self):
        self.setup_logging()
        self.lesson_patterns = self._load_lesson_patterns()
        self.validation_rules = self._load_validation_rules()
        self.lesson_registry = {}
        self.processed_lessons = set()
        
    def setup_logging(self):
        """Configurar logging del motor de reconocimiento"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _load_lesson_patterns(self) -> Dict:
        """Cargar patrones avanzados de reconocimiento de lecciones"""
        return {
            "primary_patterns": [
                # Patrones principales con alta confianza
                r'(?:^|\n)\s*Lección\s+(\d{1,3})\s*\n',
                r'(?:^|\n)\s*LECCIÓN\s+(\d{1,3})\s*\n',
                r'(?:^|\n)\s*Leccion\s+(\d{1,3})\s*\n',  # Sin tilde
            ],
            "secondary_patterns": [
                # Patrones secundarios para casos especiales
                r'(?:^|\n)\s*(\d{1,3})\.\s+(?:[A-ZÁÉÍÓÚÑ][^.]*\.)',  # Número seguido de título
                r'Lección\s+número\s+(\d{1,3})',
                r'EJERCICIO\s+(\d{1,3})',
                r'Día\s+(\d{1,3})',
            ],
            "context_patterns": [
                # Patrones que requieren validación contextual
                r'(?:^|\n)\s*(\d{1,3})\s*(?:\n|\r\n)\s*[A-ZÁÉÍÓÚÑ]',
                r'(\d{1,3})\s*\n\s*["\']',  # Número seguido de comillas
            ],
            "lesson_title_patterns": [
                # Patrones para extraer títulos de lección
                r'Lección\s+\d{1,3}\s*\n\s*([^\n]+)',
                r'LECCIÓN\s+\d{1,3}\s*\n\s*([^\n]+)',
                r'\d{1,3}\.\s+([^\n]+)',
            ]
        }
    
    def _load_validation_rules(self) -> Dict:
        """Cargar reglas de validación específicas para UCDM"""
        return {
            "lesson_number_range": (1, 365),
            "minimum_content_length": 50,  # Mínimo de caracteres por lección
            "maximum_content_length": 50000,  # Máximo razonable
            "required_elements": [
                "content_text",  # Debe tener contenido textual
                "position_marker"  # Debe tener posición en documento fuente
            ],
            "quality_indicators": {
                "good_indicators": [
                    r'perdón', r'milagro', r'Espíritu Santo', r'Dios', r'Cristo',
                    r'Amor', r'paz', r'felicidad', r'salvación'
                ],
                "warning_indicators": [
                    r'[Ã¡-ÿ]{2,}',  # Codificación incorrecta
                    r'^[a-z]',  # Empieza con minúscula
                    r'\w+\s+\d+$'  # Termina abruptamente
                ]
            }
        }
    
    def extract_lesson_numbers(self, text: str) -> List[int]:
        """Extraer números de lección con alta precisión"""
        self.logger.info("Extrayendo números de lección del texto...")
        
        found_numbers = []
        confidence_scores = {}
        
        # Procesar patrones por orden de confianza
        for pattern_type, patterns in self.lesson_patterns.items():
            for i, pattern in enumerate(patterns):
                matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
                
                for match in matches:
                    try:
                        lesson_num = int(match.group(1))
                        
                        # Validar rango
                        if not (1 <= lesson_num <= 365):
                            continue
                        
                        # Calcular confianza basada en patrón y contexto
                        confidence = self._calculate_pattern_confidence(
                            pattern_type, i, match, text
                        )
                        
                        # Registrar o actualizar si tiene mayor confianza
                        if lesson_num not in confidence_scores or confidence > confidence_scores[lesson_num]["score"]:
                            confidence_scores[lesson_num] = {
                                "score": confidence,
                                "position": match.start(),
                                "pattern": pattern,
                                "context": self._extract_context(match, text)
                            }
                    
                    except (ValueError, IndexError):
                        continue
        
        # Filtrar por confianza mínima y ordenar
        min_confidence = 0.7  # 70% de confianza mínima
        found_numbers = [
            num for num, data in confidence_scores.items() 
            if data["score"] >= min_confidence
        ]
        
        # Actualizar registro interno
        self.lesson_registry.update(confidence_scores)
        
        self.logger.info(f"Extraídos {len(found_numbers)} números de lección con alta confianza")
        return sorted(found_numbers)
    
    def validate_sequence(self, numbers: List[int]) -> SequenceReport:
        """Validar secuencia numérica completa 1-365"""
        timestamp = datetime.now().isoformat()
        
        expected_lessons = set(range(1, 366))
        found_lessons = set(numbers)
        
        missing_lessons = sorted(expected_lessons - found_lessons)
        extra_lessons = sorted(found_lessons - expected_lessons)
        
        # Detectar duplicados en la lista original
        lesson_counts = Counter(numbers)
        duplicate_lessons = [num for num, count in lesson_counts.items() if count > 1]
        
        # Calcular métricas
        total_expected = 365
        total_found = len(found_lessons)
        sequence_completeness = (total_found / total_expected) * 100
        sequence_integrity = len(missing_lessons) == 0 and len(duplicate_lessons) == 0
        
        self.logger.info(f"Secuencia validada: {total_found}/{total_expected} lecciones ({sequence_completeness:.1f}%)")
        if missing_lessons:
            self.logger.warning(f"Faltan {len(missing_lessons)} lecciones")
        if duplicate_lessons:
            self.logger.warning(f"Encontrados {len(duplicate_lessons)} duplicados")
        
        return SequenceReport(
            total_expected=total_expected,
            total_found=total_found,
            found_lessons=sorted(found_lessons),
            missing_lessons=missing_lessons,
            duplicate_lessons=duplicate_lessons,
            sequence_completeness=sequence_completeness,
            sequence_integrity=sequence_integrity,
            timestamp=timestamp
        )
    
    def detect_duplicates(self, numbers: List[int]) -> DuplicateReport:
        """Identificar y analizar duplicados"""
        timestamp = datetime.now().isoformat()
        
        # Contar ocurrencias
        lesson_counts = Counter(numbers)
        duplicates_by_lesson = {}
        
        for lesson_num, count in lesson_counts.items():
            if count > 1:
                # Buscar todas las instancias de esta lección
                instances = []
                if lesson_num in self.lesson_registry:
                    registry_data = self.lesson_registry[lesson_num]
                    instances.append({
                        "position": registry_data["position"],
                        "confidence": registry_data["score"],
                        "pattern": registry_data["pattern"],
                        "context": registry_data["context"][:100]
                    })
                
                duplicates_by_lesson[lesson_num] = {
                    "count": count,
                    "instances": instances
                }
        
        # Determinar severidad
        total_duplicates = len(duplicates_by_lesson)
        if total_duplicates == 0:
            severity_level = "none"
        elif total_duplicates <= 3:
            severity_level = "low"
        elif total_duplicates <= 10:
            severity_level = "medium"
        else:
            severity_level = "high"
        
        # Generar sugerencias de resolución
        resolution_suggestions = self._generate_duplicate_resolutions(duplicates_by_lesson)
        
        return DuplicateReport(
            duplicate_count=total_duplicates,
            duplicates_by_lesson=duplicates_by_lesson,
            resolution_suggestions=resolution_suggestions,
            severity_level=severity_level,
            timestamp=timestamp
        )
    
    def map_lesson_content(self, lesson_data: Dict) -> MappingReport:
        """Mapear números de lección con su contenido específico"""
        timestamp = datetime.now().isoformat()
        
        total_mappings = len(lesson_data)
        successful_mappings = 0
        failed_mappings = []
        content_quality_issues = []
        
        for lesson_num, content_info in lesson_data.items():
            try:
                # Validar estructura básica
                if not self._validate_mapping_structure(lesson_num, content_info):
                    failed_mappings.append({
                        "lesson_number": lesson_num,
                        "error": "invalid_structure",
                        "details": "Estructura de datos inválida"
                    })
                    continue
                
                # Validar contenido
                content_validation = self._validate_lesson_content(content_info)
                if not content_validation["valid"]:
                    content_quality_issues.append({
                        "lesson_number": lesson_num,
                        "issues": content_validation["issues"],
                        "severity": content_validation["severity"]
                    })
                
                # Mapeo exitoso si pasa validaciones básicas
                successful_mappings += 1
                
            except Exception as e:
                failed_mappings.append({
                    "lesson_number": lesson_num,
                    "error": "processing_error",
                    "details": str(e)
                })
        
        mapping_accuracy = (successful_mappings / total_mappings * 100) if total_mappings > 0 else 0
        
        self.logger.info(f"Mapeo completado: {successful_mappings}/{total_mappings} exitosos ({mapping_accuracy:.1f}%)")
        
        return MappingReport(
            total_mappings=total_mappings,
            successful_mappings=successful_mappings,
            failed_mappings=failed_mappings,
            mapping_accuracy=mapping_accuracy,
            content_quality_issues=content_quality_issues,
            timestamp=timestamp
        )
    
    def generate_coverage_report(self, processed_lessons: Dict) -> CoverageReport:
        """Generar reporte completo de cobertura"""
        timestamp = datetime.now().isoformat()
        
        # Analizar cobertura
        total_lessons = 365
        processed_count = len(processed_lessons)
        coverage_percentage = (processed_count / total_lessons) * 100
        
        # Identificar lecciones pendientes
        processed_numbers = set(int(k) for k in processed_lessons.keys())
        all_lessons = set(range(1, 366))
        pending_lessons = sorted(all_lessons - processed_numbers)
        
        # Identificar lecciones problemáticas
        problematic_lessons = []
        for lesson_num, lesson_data in processed_lessons.items():
            issues = self._analyze_lesson_quality(lesson_num, lesson_data)
            if issues:
                problematic_lessons.append({
                    "lesson_number": int(lesson_num),
                    "issues": issues,
                    "quality_score": self._calculate_lesson_quality_score(lesson_data)
                })
        
        # Evaluar calidad de extracción
        extraction_quality = self._evaluate_extraction_quality(processed_lessons)
        
        # Generar recomendaciones
        recommendations = self._generate_coverage_recommendations(
            coverage_percentage, pending_lessons, problematic_lessons
        )
        
        self.logger.info(f"Cobertura actual: {coverage_percentage:.1f}% ({processed_count}/365)")
        
        return CoverageReport(
            coverage_percentage=coverage_percentage,
            processed_lessons=processed_count,
            pending_lessons=pending_lessons,
            problematic_lessons=problematic_lessons,
            extraction_quality=extraction_quality,
            recommendations=recommendations,
            timestamp=timestamp
        )
    
    def _calculate_pattern_confidence(self, pattern_type: str, pattern_index: int, 
                                    match: re.Match, text: str) -> float:
        """Calcular confianza del patrón de reconocimiento"""
        base_confidence = {
            "primary_patterns": 0.9,
            "secondary_patterns": 0.7,
            "context_patterns": 0.5,
            "lesson_title_patterns": 0.8
        }.get(pattern_type, 0.3)
        
        # Ajustar por posición del patrón en la lista (primeros son más confiables)
        position_factor = max(0.8, 1.0 - (pattern_index * 0.1))
        
        # Ajustar por contexto
        context_factor = self._evaluate_context_quality(match, text)
        
        # Calcular confianza final
        final_confidence = base_confidence * position_factor * context_factor
        return min(1.0, max(0.0, final_confidence))
    
    def _extract_context(self, match: re.Match, text: str, window: int = 200) -> str:
        """Extraer contexto alrededor de una coincidencia"""
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        return text[start:end]
    
    def _evaluate_context_quality(self, match: re.Match, text: str) -> float:
        """Evaluar calidad del contexto alrededor del número de lección"""
        context = self._extract_context(match, text, 100)
        
        quality_score = 1.0
        
        # Penalizar si hay muchos caracteres extraños
        strange_chars = len(re.findall(r'[^\w\s\.,;:¡¿!\?\-\n\r\t"\'()]', context))
        if strange_chars > 5:
            quality_score *= 0.8
        
        # Bonificar si hay palabras clave de UCDM cercanas
        ucdm_keywords = ['perdón', 'milagro', 'Espíritu', 'Dios', 'Cristo', 'paz']
        for keyword in ucdm_keywords:
            if keyword in context.lower():
                quality_score *= 1.1
                break
        
        # Penalizar si parece ser parte de una numeración diferente
        if re.search(r'\d+\s*[-\.]\s*\d+', context):
            quality_score *= 0.7
        
        return min(1.0, quality_score)
    
    def _validate_mapping_structure(self, lesson_num: str, content_info: Dict) -> bool:
        """Validar estructura básica del mapeo"""
        try:
            # Verificar que el número sea válido
            num = int(lesson_num)
            if not (1 <= num <= 365):
                return False
            
            # Verificar elementos requeridos
            required_fields = ["title", "word_count", "char_count"]
            for field in required_fields:
                if field not in content_info:
                    return False
            
            # Verificar tipos de datos
            if not isinstance(content_info.get("word_count", 0), int):
                return False
            if not isinstance(content_info.get("char_count", 0), int):
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _validate_lesson_content(self, content_info: Dict) -> Dict:
        """Validar calidad del contenido de una lección"""
        issues = []
        severity = "none"
        
        # Verificar longitud mínima
        word_count = content_info.get("word_count", 0)
        if word_count < self.validation_rules["minimum_content_length"]:
            issues.append(f"Contenido muy corto: {word_count} palabras")
            severity = "high"
        
        # Verificar longitud máxima
        if word_count > self.validation_rules["maximum_content_length"]:
            issues.append(f"Contenido excesivo: {word_count} palabras")
            severity = "medium"
        
        # Verificar título
        title = content_info.get("title", "")
        if not title or len(title) < 5:
            issues.append("Título faltante o muy corto")
            severity = max(severity, "medium", key=lambda x: ["none", "low", "medium", "high"].index(x))
        
        # Verificar indicadores de calidad en título
        for indicator in self.validation_rules["quality_indicators"]["warning_indicators"]:
            if re.search(indicator, title):
                issues.append(f"Título con problemas de codificación: {indicator}")
                severity = max(severity, "medium", key=lambda x: ["none", "low", "medium", "high"].index(x))
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "severity": severity
        }
    
    def _analyze_lesson_quality(self, lesson_num: str, lesson_data: Dict) -> List[str]:
        """Analizar calidad específica de una lección"""
        issues = []
        
        # Verificar consistencia de datos
        word_count = lesson_data.get("word_count", 0)
        char_count = lesson_data.get("char_count", 0)
        
        # Ratio caracteres/palabras debería estar en rango normal (4-8)
        if word_count > 0:
            char_ratio = char_count / word_count
            if char_ratio < 3 or char_ratio > 10:
                issues.append(f"Ratio caracteres/palabras anormal: {char_ratio:.1f}")
        
        # Verificar archivo de contenido
        file_path = lesson_data.get("file_path", "")
        if file_path:
            full_path = PROCESSED_DATA_DIR / file_path
            if not full_path.exists():
                issues.append("Archivo de contenido faltante")
            else:
                # Verificar contenido del archivo
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content) < 100:
                        issues.append("Contenido de archivo muy corto")
                    
                    # Buscar indicadores de problemas
                    for indicator in self.validation_rules["quality_indicators"]["warning_indicators"]:
                        if re.search(indicator, content):
                            issues.append(f"Problema en contenido: {indicator}")
                            
                except Exception as e:
                    issues.append(f"Error leyendo archivo: {str(e)}")
        
        return issues
    
    def _calculate_lesson_quality_score(self, lesson_data: Dict) -> float:
        """Calcular puntuación de calidad de una lección"""
        score = 100.0
        
        # Penalizar por problemas encontrados
        issues = self._analyze_lesson_quality("temp", lesson_data)
        score -= len(issues) * 15
        
        # Bonificar por indicadores positivos
        word_count = lesson_data.get("word_count", 0)
        if 200 <= word_count <= 2000:  # Rango normal para lecciones UCDM
            score += 10
        
        title = lesson_data.get("title", "")
        for indicator in self.validation_rules["quality_indicators"]["good_indicators"]:
            if re.search(indicator, title.lower()):
                score += 5
                break
        
        return max(0, min(100, score))
    
    def _evaluate_extraction_quality(self, processed_lessons: Dict) -> Dict[str, float]:
        """Evaluar calidad general de la extracción"""
        total_lessons = len(processed_lessons)
        if total_lessons == 0:
            return {
                "completeness": 0.0,
                "consistency": 0.0,
                "quality": 0.0,
                "overall": 0.0
            }
        
        # Calcular completeness
        completeness = (total_lessons / 365) * 100
        
        # Calcular consistencia (distribución de tamaños)
        word_counts = [data.get("word_count", 0) for data in processed_lessons.values()]
        if word_counts:
            avg_words = sum(word_counts) / len(word_counts)
            consistency = max(0, 100 - (len([w for w in word_counts if abs(w - avg_words) > avg_words * 0.5]) / len(word_counts) * 100))
        else:
            consistency = 0
        
        # Calcular calidad promedio
        quality_scores = [
            self._calculate_lesson_quality_score(data) 
            for data in processed_lessons.values()
        ]
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Calcular puntuación general
        overall = (completeness * 0.4 + consistency * 0.3 + average_quality * 0.3)
        
        return {
            "completeness": completeness,
            "consistency": consistency,
            "quality": average_quality,
            "overall": overall
        }
    
    def _generate_duplicate_resolutions(self, duplicates_by_lesson: Dict) -> List[str]:
        """Generar sugerencias para resolver duplicados"""
        if not duplicates_by_lesson:
            return ["No se encontraron duplicados"]
        
        suggestions = []
        
        # Sugerencias generales
        suggestions.append("Revisar manualmente las instancias duplicadas")
        suggestions.append("Seleccionar la instancia con mayor confianza de reconocimiento")
        
        # Sugerencias específicas basadas en patrones
        high_confidence_duplicates = sum(1 for data in duplicates_by_lesson.values() if len(data["instances"]) > 2)
        if high_confidence_duplicates > 0:
            suggestions.append("Considerar re-extracción con filtros más estrictos")
        
        suggestions.append("Implementar validación cruzada con contenido")
        
        return suggestions
    
    def _generate_coverage_recommendations(self, coverage_percentage: float, 
                                         pending_lessons: List[int], 
                                         problematic_lessons: List[Dict]) -> List[str]:
        """Generar recomendaciones basadas en cobertura"""
        recommendations = []
        
        # Recomendaciones por nivel de cobertura
        if coverage_percentage < 50:
            recommendations.append("CRÍTICO: Cobertura muy baja. Re-extraer documento completo con mejores parámetros")
        elif coverage_percentage < 80:
            recommendations.append("Re-procesar secciones faltantes con extractor avanzado")
        elif coverage_percentage < 95:
            recommendations.append("Procesar lecciones faltantes específicas")
        else:
            recommendations.append("Completar las pocas lecciones restantes")
        
        # Recomendaciones por lecciones problemáticas
        if len(problematic_lessons) > 10:
            recommendations.append("Revisar calidad de extracción - muchas lecciones con problemas")
        elif len(problematic_lessons) > 0:
            recommendations.append("Revisar manualmente lecciones problemáticas identificadas")
        
        # Recomendaciones específicas para rangos problemáticos conocidos
        problematic_ranges = [
            (360, 365),  # Rango final problemático conocido
            (68, 68),    # Lección específica problemática
            (91, 91),    # Lección específica problemática
            (168, 168)   # Lección específica problemática
        ]
        
        for start, end in problematic_ranges:
            missing_in_range = [l for l in pending_lessons if start <= l <= end]
            if missing_in_range:
                recommendations.append(f"Atención especial a lecciones {start}-{end}: conocidas como problemáticas")
        
        return recommendations
    
    def generate_comprehensive_recognition_report(self, text: str, existing_lessons: Dict = None) -> Dict:
        """Generar reporte completo de reconocimiento"""
        self.logger.info("Iniciando análisis completo de reconocimiento de lecciones...")
        
        # Extraer números de lección
        lesson_numbers = self.extract_lesson_numbers(text)
        
        # Generar reportes específicos
        sequence_report = self.validate_sequence(lesson_numbers)
        duplicate_report = self.detect_duplicates(lesson_numbers)
        
        # Mapeo si se proporcionan lecciones existentes
        mapping_report = None
        if existing_lessons:
            mapping_report = self.map_lesson_content(existing_lessons)
        
        # Reporte de cobertura
        coverage_report = self.generate_coverage_report(existing_lessons or {})
        
        # Reporte consolidado
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "text_analysis": {
                "text_length": len(text),
                "total_lessons_found": len(lesson_numbers),
                "unique_lessons": len(set(lesson_numbers))
            },
            "sequence_validation": sequence_report,
            "duplicate_analysis": duplicate_report,
            "mapping_analysis": mapping_report,
            "coverage_analysis": coverage_report,
            "summary": {
                "recognition_accuracy": sequence_report.sequence_completeness,
                "data_integrity": sequence_report.sequence_integrity,
                "processing_status": self._determine_processing_status(sequence_report, coverage_report),
                "next_actions": self._determine_next_actions(sequence_report, duplicate_report, coverage_report)
            }
        }
        
        self.logger.info(f"Análisis completado. Precisión: {sequence_report.sequence_completeness:.1f}%")
        
        return comprehensive_report
    
    def _determine_processing_status(self, sequence_report: SequenceReport, 
                                   coverage_report: CoverageReport) -> str:
        """Determinar estado general del procesamiento"""
        if sequence_report.sequence_completeness >= 99:
            return "COMPLETO"
        elif sequence_report.sequence_completeness >= 90:
            return "CASI_COMPLETO"
        elif sequence_report.sequence_completeness >= 70:
            return "EN_PROGRESO"
        elif sequence_report.sequence_completeness >= 50:
            return "PARCIAL"
        else:
            return "INICIAL"
    
    def _determine_next_actions(self, sequence_report: SequenceReport,
                              duplicate_report: DuplicateReport,
                              coverage_report: CoverageReport) -> List[str]:
        """Determinar siguientes acciones recomendadas"""
        actions = []
        
        # Acciones por cobertura
        if sequence_report.sequence_completeness < 100:
            missing_count = len(sequence_report.missing_lessons)
            actions.append(f"Procesar {missing_count} lecciones faltantes")
        
        # Acciones por duplicados
        if duplicate_report.severity_level in ["high", "medium"]:
            actions.append("Resolver duplicados encontrados")
        
        # Acciones por problemas de calidad
        if len(coverage_report.problematic_lessons) > 0:
            actions.append("Revisar lecciones con problemas de calidad")
        
        # Acción final
        if sequence_report.sequence_completeness >= 99 and duplicate_report.severity_level in ["none", "low"]:
            actions.append("Sistema listo para validación final")
        
        return actions