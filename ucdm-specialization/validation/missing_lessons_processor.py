#!/usr/bin/env python3
"""
Procesador Avanzado de Lecciones Faltantes UCDM
Implementa el procesamiento inteligente de las 250 lecciones identificadas como faltantes
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

# Importar componentes de validación
from validation.comprehensive_validation_pipeline import ComprehensiveValidationPipeline
from extraction.lesson_segmenter import UCDMLessonSegmenter, UCDMLesson

@dataclass
class LessonProcessingResult:
    """Resultado del procesamiento de una lección individual"""
    lesson_number: int
    success: bool
    extracted_content: Optional[str] = None
    quality_score: float = 0.0
    validation_report: Optional[Dict] = None
    processing_time: float = 0.0
    errors: List[str] = None
    source_location: Optional[str] = None

@dataclass
class BatchProcessingReport:
    """Reporte de procesamiento por lotes"""
    batch_id: str
    timestamp: str
    total_lessons: int
    successful_lessons: int
    failed_lessons: int
    average_quality_score: float
    processing_time: float
    lesson_results: List[LessonProcessingResult]
    recommendations: List[str]

class MissingLessonsProcessor:
    """Procesador especializado para lecciones faltantes del UCDM"""
    
    def __init__(self, validation_pipeline: ComprehensiveValidationPipeline = None):
        self.setup_logging()
        self.validation_pipeline = validation_pipeline or ComprehensiveValidationPipeline()
        self.segmenter = None
        self.source_content = ""
        self.processing_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_processing_time": 0.0,
            "quality_distribution": {}
        }
        
    def setup_logging(self):
        """Configurar logging del procesador"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_source_content(self) -> bool:
        """Cargar contenido fuente completo para extracción"""
        try:
            text_file = PROCESSED_DATA_DIR / "ucdm_complete_text.txt"
            if text_file.exists():
                with open(text_file, 'r', encoding='utf-8') as f:
                    self.source_content = f.read()
                self.logger.info(f"Contenido fuente cargado: {len(self.source_content)} caracteres")
                self.segmenter = UCDMLessonSegmenter(self.source_content)
                return True
            else:
                self.logger.error("No se encontró archivo de texto fuente")
                return False
        except Exception as e:
            self.logger.error(f"Error cargando contenido fuente: {e}")
            return False
    
    def identify_missing_lessons(self) -> List[int]:
        """Identificar lecciones faltantes basado en reportes existentes"""
        try:
            # Cargar desde reporte de validación
            validation_file = PROCESSED_DATA_DIR / "lessons_validation.json"
            if validation_file.exists():
                with open(validation_file, 'r', encoding='utf-8') as f:
                    validation_data = json.load(f)
                missing_lessons = validation_data.get("missing_lessons", [])
                self.logger.info(f"Identificadas {len(missing_lessons)} lecciones faltantes")
                return missing_lessons
            
            # Fallback: calcular basado en índice actual
            lessons_index_file = INDICES_DIR / "365_lessons_indexed.json"
            if lessons_index_file.exists():
                with open(lessons_index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                processed_numbers = set(int(k) for k in index_data.keys())
                all_lessons = set(range(1, 366))
                missing_lessons = sorted(all_lessons - processed_numbers)
                self.logger.info(f"Calculadas {len(missing_lessons)} lecciones faltantes desde índice")
                return missing_lessons
            
            return list(range(2, 252))  # Fallback
            
        except Exception as e:
            self.logger.error(f"Error identificando lecciones faltantes: {e}")
            return []
    
    def extract_specific_lesson(self, lesson_number: int) -> LessonProcessingResult:
        """Extraer una lección específica usando técnicas avanzadas"""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Procesando lección {lesson_number}...")
            
            # Buscar la lección con múltiples estrategias
            lesson_content = self._search_lesson_content(lesson_number)
            
            if not lesson_content:
                return LessonProcessingResult(
                    lesson_number=lesson_number,
                    success=False,
                    errors=[f"No se pudo localizar contenido de lección {lesson_number}"],
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Crear objeto de lección
            lesson = UCDMLesson(
                number=lesson_number,
                title=lesson_content.get("title", f"Lección {lesson_number}"),
                content=lesson_content.get("content", ""),
                position=lesson_content.get("source_page", 0)
            )
            
            # Validar calidad usando el pipeline
            validation_result = self.validation_pipeline.validate_text_content(
                lesson.content, 
                f"lesson_{lesson_number}"
            )
            
            # Extraer puntuación de calidad
            quality_score = 0.0
            if validation_result.get("success"):
                assessment = validation_result.get("assessment", {})
                quality_score = assessment.get("overall_score", 0.0)
            
            # Guardar lección si es de calidad aceptable
            if quality_score >= 70.0:
                self._save_extracted_lesson(lesson)
                success = True
            else:
                success = False
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return LessonProcessingResult(
                lesson_number=lesson_number,
                success=success,
                extracted_content=lesson.content,
                quality_score=quality_score,
                validation_report=validation_result,
                processing_time=processing_time,
                source_location=lesson_content.get("source_location", "")
            )
            
        except Exception as e:
            self.logger.error(f"Error procesando lección {lesson_number}: {e}")
            return LessonProcessingResult(
                lesson_number=lesson_number,
                success=False,
                errors=[str(e)],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _search_lesson_content(self, lesson_number: int) -> Optional[Dict]:
        """Buscar contenido de lección usando múltiples estrategias"""
        
        # Estrategia 1: Patrones directos de lección
        direct_patterns = [
            rf'Lección\s+{lesson_number}\s*\n([^L]*?)(?=Lección\s+\d+|\Z)',
            rf'LECCIÓN\s+{lesson_number}\s*\n([^L]*?)(?=LECCIÓN\s+\d+|\Z)',
            rf'{lesson_number}\.\s+([^\n]*)\n([^0-9]*?)(?=\d+\.|\Z)',
        ]
        
        for pattern in direct_patterns:
            matches = list(re.finditer(pattern, self.source_content, re.IGNORECASE | re.DOTALL))
            if matches:
                match = matches[0]
                content = match.group(1) if match.lastindex >= 1 else match.group(0)
                
                # Extraer título
                title_match = re.search(rf'Lección\s+{lesson_number}\s*\n\s*([^\n]+)', 
                                       self.source_content[max(0, match.start()-100):match.end()+100], 
                                       re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else f"Lección {lesson_number}"
                
                return {
                    "title": title,
                    "content": content.strip(),
                    "confidence": 0.9,
                    "source_location": f"Posición {match.start()}-{match.end()}",
                    "source_page": self._estimate_page_number(match.start())
                }
        
        # Estrategia 2: Búsqueda en sección del Libro de Ejercicios
        section_result = self._search_in_workbook_section(lesson_number)
        if section_result:
            return section_result
        
        # Estrategia 3: Búsqueda flexible con tolerancia a errores
        flexible_result = self._flexible_lesson_search(lesson_number)
        if flexible_result:
            return flexible_result
        
        return None
    
    def _search_in_workbook_section(self, lesson_number: int) -> Optional[Dict]:
        """Buscar específicamente en la sección del Libro de Ejercicios"""
        workbook_patterns = [
            r'LIBRO\s+DE\s+EJERCICIOS',
            r'WORKBOOK\s+FOR\s+STUDENTS',
            r'Libro\s+de\s+ejercicios'
        ]
        
        workbook_start = None
        for pattern in workbook_patterns:
            match = re.search(pattern, self.source_content, re.IGNORECASE)
            if match:
                workbook_start = match.end()
                break
        
        if not workbook_start:
            return None
        
        # Buscar en la sección del libro de ejercicios
        workbook_content = self.source_content[workbook_start:workbook_start + 1000000]
        
        lesson_pattern = rf'Lección\s+{lesson_number}[^\d].*?(?=Lección\s+(?:{lesson_number + 1}|\d{{1,3}})[^\d]|\Z)'
        match = re.search(lesson_pattern, workbook_content, re.IGNORECASE | re.DOTALL)
        
        if match:
            content = match.group(0)
            title_match = re.search(rf'Lección\s+{lesson_number}\s*\n?\s*([^\n]+)', content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else f"Lección {lesson_number}"
            
            return {
                "title": title,
                "content": content.strip(),
                "confidence": 0.8,
                "source_location": f"Libro de Ejercicios, posición {workbook_start + match.start()}",
                "source_page": self._estimate_page_number(workbook_start + match.start())
            }
        
        return None
    
    def _flexible_lesson_search(self, lesson_number: int) -> Optional[Dict]:
        """Búsqueda flexible con tolerancia a errores de OCR y formato"""
        flexible_patterns = [
            rf'Lecci[oó]n\s+{lesson_number}[^\d].*?(?=Lecci[oó]n\s+\d{{1,3}}[^\d]|\Z)',
            rf'LECCI[OÓ]N\s+{lesson_number}[^\d].*?(?=LECCI[OÓ]N\s+\d{{1,3}}[^\d]|\Z)',
            rf'{lesson_number}\s*[-\.]\s*[A-ZÁÉÍÓÚÑ].*?(?=\d{{1,3}}\s*[-\.]|\Z)',
            rf'Día\s+{lesson_number}[^\d].*?(?=Día\s+\d{{1,3}}[^\d]|\Z)',
        ]
        
        for pattern in flexible_patterns:
            matches = list(re.finditer(pattern, self.source_content, re.IGNORECASE | re.DOTALL))
            if matches:
                match = matches[0]
                content = match.group(0)
                content = self._clean_extracted_content(content)
                
                if len(content.split()) >= 50:  # Mínimo de contenido
                    title = self._extract_lesson_title(content, lesson_number)
                    
                    return {
                        "title": title,
                        "content": content,
                        "confidence": 0.6,
                        "source_location": f"Búsqueda flexible, posición {match.start()}",
                        "source_page": self._estimate_page_number(match.start())
                    }
        
        return None
    
    def _clean_extracted_content(self, content: str) -> str:
        """Limpiar contenido extraído"""
        # Remover caracteres de control extraños
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', content)
        # Corregir espaciado
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        return content.strip()
    
    def _extract_lesson_title(self, content: str, lesson_number: int) -> str:
        """Extraer título de lección del contenido"""
        title_patterns = [
            rf'Lección\s+{lesson_number}\s*\n\s*([^\n]+)',
            rf'{lesson_number}\.\s+([^\n]+)',
            rf'{lesson_number}\s*[-\.]\s*([^\n]+)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content[:200], re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ\.,;:¿¡!?()]', '', title)
                if len(title) > 10 and len(title) < 100:
                    return title
        
        return f"Lección {lesson_number}"
    
    def _estimate_page_number(self, position: int) -> int:
        """Estimar número de página basado en posición en el texto"""
        chars_per_page = 3000
        return max(1, (position // chars_per_page) + 1)
    
    def _save_extracted_lesson(self, lesson: UCDMLesson) -> bool:
        """Guardar lección extraída en el sistema"""
        try:
            # Crear directorio de lecciones
            lessons_dir = PROCESSED_DATA_DIR / "lessons"
            lessons_dir.mkdir(exist_ok=True)
            
            # Guardar archivo individual
            lesson_file = lessons_dir / f"lesson_{lesson.number:03d}.txt"
            with open(lesson_file, 'w', encoding='utf-8') as f:
                f.write(f"Lección {lesson.number}: {lesson.title}\n")
                f.write("=" * 50 + "\n\n")
                f.write(lesson.content)
            
            # Actualizar índice
            self._update_lessons_index(lesson)
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando lección {lesson.number}: {e}")
            return False
    
    def _update_lessons_index(self, lesson: UCDMLesson) -> None:
        """Actualizar índice de lecciones"""
        try:
            index_file = INDICES_DIR / "365_lessons_indexed.json"
            
            # Cargar índice existente
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            else:
                index_data = {}
            
            # Agregar/actualizar lección
            index_data[str(lesson.number)] = {
                "title": lesson.title,
                "word_count": lesson.word_count,
                "char_count": lesson.char_count,
                "file_path": f"lessons/lesson_{lesson.number:03d}.txt",
                "extraction_confidence": 0.8,  # Valor por defecto
                "last_updated": datetime.now().isoformat()
            }
            
            # Guardar índice actualizado
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error actualizando índice: {e}")
    
    def process_all_missing_lessons(self) -> Dict:
        """Procesar todas las lecciones faltantes identificadas"""
        if not self.load_source_content():
            return {"success": False, "error": "No se pudo cargar contenido fuente"}
        
        missing_lessons = self.identify_missing_lessons()
        if not missing_lessons:
            return {
                "success": True,
                "message": "No hay lecciones faltantes por procesar",
                "total_processed": 0
            }
        
        self.logger.info(f"Iniciando procesamiento completo de {len(missing_lessons)} lecciones faltantes")
        
        # Procesar en lotes
        batch_size = 25
        successful_count = 0
        failed_count = 0
        
        for i in range(0, len(missing_lessons), batch_size):
            batch_lessons = missing_lessons[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(missing_lessons) + batch_size - 1) // batch_size
            
            self.logger.info(f"Procesando lote {batch_num}/{total_batches}: lecciones {batch_lessons[0]}-{batch_lessons[-1]}")
            
            # Procesar lote actual
            for lesson_num in batch_lessons:
                result = self.extract_specific_lesson(lesson_num)
                if result.success:
                    successful_count += 1
                else:
                    failed_count += 1
        
        # Generar reporte final
        success_rate = (successful_count / len(missing_lessons)) * 100
        final_report = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "total_requested": len(missing_lessons),
            "total_processed": successful_count,
            "total_failed": failed_count,
            "success_rate": success_rate,
            "updated_coverage": self._calculate_updated_coverage(successful_count),
            "final_recommendations": self._generate_final_recommendations(success_rate)
        }
        
        # Guardar reporte
        self._save_processing_report(final_report)
        
        self.logger.info(f"Procesamiento completo terminado: {successful_count}/{len(missing_lessons)} exitosos ({success_rate:.1f}%)")
        
        return final_report
    
    def _calculate_updated_coverage(self, newly_processed: int) -> Dict:
        """Calcular cobertura actualizada después del procesamiento"""
        try:
            index_file = INDICES_DIR / "365_lessons_indexed.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            else:
                index_data = {}
            
            current_count = len(index_data)
            updated_count = current_count + newly_processed
            coverage_percentage = (updated_count / 365) * 100
            
            return {
                "previous_count": current_count,
                "newly_processed": newly_processed,
                "updated_count": updated_count,
                "coverage_percentage": coverage_percentage,
                "remaining_lessons": 365 - updated_count
            }
            
        except Exception as e:
            self.logger.error(f"Error calculando cobertura: {e}")
            return {"error": str(e), "newly_processed": newly_processed}
    
    def _generate_final_recommendations(self, success_rate: float) -> List[str]:
        """Generar recomendaciones finales del procesamiento completo"""
        recommendations = []
        
        if success_rate >= 90:
            recommendations.append("EXCELENTE: Procesamiento altamente exitoso")
            recommendations.append("Ejecutar validación completa del sistema")
        elif success_rate >= 75:
            recommendations.append("BUENO: Procesamiento mayormente exitoso")
            recommendations.append("Revisar lecciones fallidas específicas")
        elif success_rate >= 50:
            recommendations.append("MODERADO: Mejorar estrategias de extracción")
            recommendations.append("Considerar procesamiento manual de lecciones problemáticas")
        else:
            recommendations.append("CRÍTICO: Revisar completamente el sistema de extracción")
            recommendations.append("Evaluar calidad del documento fuente")
        
        return recommendations
    
    def _save_processing_report(self, report: Dict) -> None:
        """Guardar reporte completo de procesamiento"""
        try:
            report_file = PROCESSED_DATA_DIR / f"missing_lessons_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Reporte de procesamiento guardado: {report_file}")
        except Exception as e:
            self.logger.error(f"Error guardando reporte: {e}")


def main():
    """Función principal para ejecutar el procesamiento de lecciones faltantes"""
    processor = MissingLessonsProcessor()
    
    print("🚀 Iniciando procesamiento de lecciones faltantes UCDM...")
    print("=" * 60)
    
    # Ejecutar procesamiento completo
    result = processor.process_all_missing_lessons()
    
    if result["success"]:
        print(f"\n✅ PROCESAMIENTO COMPLETADO")
        print(f"   Total solicitado: {result['total_requested']}")
        print(f"   Exitosamente procesado: {result['total_processed']}")
        print(f"   Fallidas: {result['total_failed']}")
        print(f"   Tasa de éxito: {result['success_rate']:.1f}%")
        
        if "updated_coverage" in result:
            coverage = result["updated_coverage"]
            print(f"\n📊 COBERTURA ACTUALIZADA:")
            print(f"   Cobertura actual: {coverage.get('coverage_percentage', 0):.1f}%")
            print(f"   Lecciones totales: {coverage.get('updated_count', 0)}/365")
            print(f"   Lecciones restantes: {coverage.get('remaining_lessons', 365)}")
        
        print(f"\n💡 RECOMENDACIONES:")
        for rec in result.get("final_recommendations", []):
            print(f"   • {rec}")
            
    else:
        print(f"❌ ERROR: {result.get('error', 'Error desconocido')}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())