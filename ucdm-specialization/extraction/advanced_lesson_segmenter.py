#!/usr/bin/env python3
"""
Segmentador avanzado para las 365 lecciones de UCDM
Usa múltiples estrategias para extraer el máximo número de lecciones posible
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import logging
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

@dataclass
class UCDMLesson:
    """Estructura de datos para una lección de UCDM"""
    number: int
    title: str
    content: str
    position: int
    section: str = "Libro de Ejercicios"
    word_count: int = 0
    char_count: int = 0
    extraction_method: str = "pattern_matching"
    confidence: float = 1.0
    
    def __post_init__(self):
        self.word_count = len(self.content.split())
        self.char_count = len(self.content)

class AdvancedUCDMLessonSegmenter:
    """Segmentador avanzado con múltiples estrategias"""
    
    def __init__(self, content_text: str):
        self.content = content_text
        self.lessons = {}
        self.workbook_section = ""
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def extract_workbook_section(self) -> str:
        """Extraer específicamente la sección del Libro de Ejercicios"""
        # Buscar el inicio del Libro de Ejercicios
        workbook_patterns = [
            r"LIBRO\s+DE\s+EJERCICIOS",
            r"Libro\s+de\s+Ejercicios",
            r"SEGUNDA\s+PARTE",
            r"Segunda\s+Parte"
        ]
        
        start_pos = 0
        for pattern in workbook_patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                start_pos = match.start()
                self.logger.info(f"Libro de Ejercicios encontrado en posición {start_pos}")
                break
        
        # Buscar el final del Libro de Ejercicios
        end_patterns = [
            r"MANUAL\s+PARA\s+EL\s+MAESTRO",
            r"Manual\s+del\s+Maestro",
            r"TERCERA\s+PARTE",
            r"Tercera\s+Parte"
        ]
        
        end_pos = len(self.content)
        for pattern in end_patterns:
            match = re.search(pattern, self.content[start_pos:], re.IGNORECASE)
            if match:
                end_pos = start_pos + match.start()
                self.logger.info(f"Final del Libro de Ejercicios en posición {end_pos}")
                break
        
        workbook_content = self.content[start_pos:end_pos]
        self.logger.info(f"Sección del Libro de Ejercicios extraída: {len(workbook_content):,} caracteres")
        return workbook_content
    
    def find_lessons_strategy_1(self, text: str) -> Dict[int, Dict]:
        """Estrategia 1: Patrones tradicionales con 'Lección'"""
        patterns = [
            r"(?:\n|^)\s*Lección\s+(\d{1,3})\s*[\.:]?\s*(.*?)(?=\n)",
            r"(?:\n|^)\s*LECCIÓN\s+(\d{1,3})\s*[\.:]?\s*(.*?)(?=\n)",
            r"(?:\n|^)\s*Leccion\s+(\d{1,3})\s*[\.:]?\s*(.*?)(?=\n)"
        ]
        
        found_lessons = {}
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                try:
                    lesson_num = int(match.group(1))
                    lesson_title = match.group(2).strip() if match.group(2) else f"Lección {lesson_num}"
                    
                    if 1 <= lesson_num <= 365:
                        found_lessons[lesson_num] = {
                            'number': lesson_num,
                            'title': lesson_title,
                            'start_pos': match.start(),
                            'end_pos': match.end(),
                            'method': 'traditional_pattern',
                            'confidence': 0.9
                        }
                except (ValueError, IndexError):
                    continue
        
        self.logger.info(f"Estrategia 1: {len(found_lessons)} lecciones encontradas")
        return found_lessons
    
    def find_lessons_strategy_2(self, text: str) -> Dict[int, Dict]:
        """Estrategia 2: Números seguidos de texto descriptivo"""
        # Buscar números del 1-365 seguidos de texto que parezca un título de lección
        pattern = r"(?:\n|^)\s*(\d{1,3})\s*[\.:\-]?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ][^\n]{10,100})(?=\n)"
        
        found_lessons = {}
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            try:
                lesson_num = int(match.group(1))
                lesson_title = match.group(2).strip()
                
                if 1 <= lesson_num <= 365:
                    # Verificar que el título parece válido
                    if self.validate_lesson_title(lesson_title):
                        found_lessons[lesson_num] = {
                            'number': lesson_num,
                            'title': lesson_title,
                            'start_pos': match.start(),
                            'end_pos': match.end(),
                            'method': 'number_pattern',
                            'confidence': 0.7
                        }
            except (ValueError, IndexError):
                continue
        
        self.logger.info(f"Estrategia 2: {len(found_lessons)} lecciones encontradas")
        return found_lessons
    
    def find_lessons_strategy_3(self, text: str) -> Dict[int, Dict]:
        """Estrategia 3: Búsqueda secuencial en intervalos"""
        found_lessons = {}
        
        # Buscar lecciones en grupos secuenciales
        for start_num in range(1, 366, 10):  # Grupos de 10
            end_num = min(start_num + 9, 365)
            
            # Crear patrón para este rango
            numbers_pattern = '|'.join(str(i) for i in range(start_num, end_num + 1))
            pattern = rf"(?:\n|^)\s*({numbers_pattern})\s*[\.:\-]?\s*([^\n]{{5,100}})(?=\n)"
            
            matches = re.finditer(pattern, text, re.MULTILINE)
            
            for match in matches:
                try:
                    lesson_num = int(match.group(1))
                    lesson_title = match.group(2).strip()
                    
                    if self.validate_lesson_context(text, match.start(), match.end()):
                        found_lessons[lesson_num] = {
                            'number': lesson_num,
                            'title': lesson_title,
                            'start_pos': match.start(),
                            'end_pos': match.end(),
                            'method': 'sequential_search',
                            'confidence': 0.6
                        }
                except (ValueError, IndexError):
                    continue
        
        self.logger.info(f"Estrategia 3: {len(found_lessons)} lecciones encontradas")
        return found_lessons
    
    def validate_lesson_title(self, title: str) -> bool:
        """Validar si un título parece ser de una lección de UCDM"""
        if not title or len(title.strip()) < 5:
            return False
        
        # Palabras clave que aparecen frecuentemente en títulos de UCDM
        ucdm_keywords = [
            'dios', 'amor', 'paz', 'perdón', 'milagro', 'espíritu', 'santo',
            'cristo', 'luz', 'verdad', 'ilusión', 'miedo', 'culpa', 'salvación',
            'expiación', 'unidad', 'separación', 'ego', 'mente', 'corazón',
            'hermano', 'hijo', 'padre', 'bendición', 'gratitud', 'gozo',
            'felicidad', 'seguridad', 'protección', 'santidad', 'inocencia'
        ]
        
        title_lower = title.lower()
        
        # Al menos una palabra clave UCDM
        has_keyword = any(keyword in title_lower for keyword in ucdm_keywords)
        
        # No debe ser solo números o caracteres especiales
        has_meaningful_text = re.search(r'[a-záéíóúñ]{3,}', title_lower)
        
        # No debe parecer un número de página o referencia
        is_not_page_ref = not re.match(r'^\d+$', title.strip())
        
        return has_keyword or (has_meaningful_text and is_not_page_ref)
    
    def validate_lesson_context(self, text: str, start_pos: int, end_pos: int) -> bool:
        """Validar el contexto alrededor de una posible lección"""
        # Extraer contexto (100 caracteres antes y después)
        context_start = max(0, start_pos - 100)
        context_end = min(len(text), end_pos + 200)
        context = text[context_start:context_end]
        
        # Buscar indicadores de que es realmente una lección
        lesson_indicators = [
            r'ejercicio', r'práctica', r'repite', r'afirma', r'medita',
            r'reflexiona', r'recuerda', r'aplica', r'hoy', r'mañana',
            r'minuto', r'hora', r'tiempo', r'idea', r'pensamiento'
        ]
        
        indicator_count = sum(1 for indicator in lesson_indicators 
                             if re.search(indicator, context, re.IGNORECASE))
        
        return indicator_count >= 1
    
    def merge_lesson_findings(self, *strategies_results) -> Dict[int, Dict]:
        """Combinar resultados de múltiples estrategias"""
        merged_lessons = {}
        
        for strategy_results in strategies_results:
            for lesson_num, lesson_data in strategy_results.items():
                if lesson_num not in merged_lessons:
                    merged_lessons[lesson_num] = lesson_data
                else:
                    # Mantener la versión con mayor confianza
                    if lesson_data['confidence'] > merged_lessons[lesson_num]['confidence']:
                        merged_lessons[lesson_num] = lesson_data
        
        return merged_lessons
    
    def extract_lesson_content_advanced(self, lesson_data: Dict, all_lessons: Dict[int, Dict]) -> str:
        """Extraer contenido de lección con método avanzado"""
        lesson_num = lesson_data['number']
        start_pos = lesson_data['end_pos']
        
        # Encontrar la siguiente lección para determinar el final
        next_lesson_nums = [num for num in all_lessons.keys() if num > lesson_num]
        
        if next_lesson_nums:
            next_lesson_num = min(next_lesson_nums)
            end_pos = all_lessons[next_lesson_num]['start_pos']
        else:
            # Es la última lección, buscar el final del Libro de Ejercicios
            search_text = self.content[start_pos:start_pos + 20000]
            end_patterns = [
                r"MANUAL\s+PARA\s+EL\s+MAESTRO",
                r"Manual\s+del\s+Maestro",
                r"TERCERA\s+PARTE"
            ]
            
            end_pos = len(self.content)
            for pattern in end_patterns:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    end_pos = start_pos + match.start()
                    break
        
        # Extraer contenido
        raw_content = self.content[start_pos:end_pos].strip()
        
        # Limpiar contenido
        content = self.clean_content_advanced(raw_content)
        
        return content
    
    def clean_content_advanced(self, raw_content: str) -> str:
        """Limpieza avanzada de contenido"""
        content = raw_content
        
        # Remover números de página y encabezados
        content = re.sub(r'\n\s*\d+\s*\n', '\n', content)
        content = re.sub(r'^\s*\d+\s*\n', '', content)
        content = re.sub(r'\n\s*Lección\s+\d+.*?\n', '\n', content, flags=re.IGNORECASE)
        
        # Normalizar espacios y saltos de línea
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # Remover contenido de otras secciones que se haya colado
        unwanted_patterns = [
            r'MANUAL\s+PARA\s+EL\s+MAESTRO.*',
            r'TERCERA\s+PARTE.*',
            r'Manual\s+del\s+Maestro.*'
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Asegurar que el contenido no sea demasiado corto
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if len(lines) < 3:  # Muy pocas líneas
            return content.strip()
        
        return '\n'.join(lines)
    
    def segment_lessons_advanced(self) -> Dict[int, UCDMLesson]:
        """Método principal de segmentación avanzada"""
        self.logger.info("=== Iniciando segmentación avanzada de lecciones ===")
        
        # Extraer la sección específica del Libro de Ejercicios
        workbook_text = self.extract_workbook_section()
        
        if not workbook_text:
            self.logger.warning("No se pudo extraer la sección del Libro de Ejercicios")
            workbook_text = self.content
        
        # Aplicar múltiples estrategias
        strategy1_results = self.find_lessons_strategy_1(workbook_text)
        strategy2_results = self.find_lessons_strategy_2(workbook_text)
        strategy3_results = self.find_lessons_strategy_3(workbook_text)
        
        # Si las estrategias en el workbook no dan buenos resultados, intentar en todo el contenido
        if len(strategy1_results) + len(strategy2_results) + len(strategy3_results) < 100:
            self.logger.info("Pocas lecciones encontradas en Libro de Ejercicios, buscando en todo el contenido...")
            strategy1_full = self.find_lessons_strategy_1(self.content)
            strategy2_full = self.find_lessons_strategy_2(self.content)
            strategy3_full = self.find_lessons_strategy_3(self.content)
            
            # Usar los mejores resultados
            if len(strategy1_full) > len(strategy1_results):
                strategy1_results = strategy1_full
            if len(strategy2_full) > len(strategy2_results):
                strategy2_results = strategy2_full
            if len(strategy3_full) > len(strategy3_results):
                strategy3_results = strategy3_full
        
        # Combinar resultados
        merged_lessons = self.merge_lesson_findings(
            strategy1_results, 
            strategy2_results, 
            strategy3_results
        )
        
        self.logger.info(f"Total de lecciones únicas encontradas: {len(merged_lessons)}")
        
        # Extraer contenido para cada lección
        lessons = {}
        
        for lesson_num, lesson_data in merged_lessons.items():
            try:
                content = self.extract_lesson_content_advanced(lesson_data, merged_lessons)
                
                # Validar que el contenido es suficiente
                if len(content.split()) < 10:  # Menos de 10 palabras es muy poco
                    self.logger.warning(f"Lección {lesson_num}: contenido muy corto, omitiendo")
                    continue
                
                lesson = UCDMLesson(
                    number=lesson_num,
                    title=lesson_data['title'],
                    content=content,
                    position=lesson_data['start_pos'],
                    extraction_method=lesson_data['method'],
                    confidence=lesson_data['confidence']
                )
                
                lessons[lesson_num] = lesson
                
            except Exception as e:
                self.logger.error(f"Error extrayendo lección {lesson_num}: {str(e)}")
                continue
        
        self.logger.info(f"Segmentación completada: {len(lessons)} lecciones extraídas con contenido válido")
        return lessons

    def save_lessons_advanced(self, lessons: Dict[int, UCDMLesson]) -> None:
        """Guardar lecciones con metadatos avanzados"""
        # Crear directorio
        lessons_dir = PROCESSED_DATA_DIR / "lessons_advanced"
        lessons_dir.mkdir(exist_ok=True)
        
        # Preparar índice con metadatos completos
        lessons_index = {
            "metadata": {
                "total_lessons": len(lessons),
                "extraction_date": str(datetime.now()),
                "source": "Un Curso de Milagros - Libro de Ejercicios",
                "extraction_method": "advanced_multi_strategy",
                "coverage_percentage": (len(lessons) / 365) * 100
            },
            "lessons": {},
            "statistics": {
                "methods_used": {},
                "confidence_distribution": {},
                "quality_metrics": {}
            }
        }
        
        # Procesar cada lección
        method_counts = {}
        confidence_ranges = {"high": 0, "medium": 0, "low": 0}
        
        for lesson_num, lesson in lessons.items():
            # Guardar lección individual
            lesson_file = lessons_dir / f"lesson_{lesson_num:03d}.txt"
            with open(lesson_file, 'w', encoding='utf-8') as f:
                f.write(f"Lección {lesson_num}: {lesson.title}\n")
                f.write("=" * 60 + "\n")
                f.write(f"Método de extracción: {lesson.extraction_method}\n")
                f.write(f"Confianza: {lesson.confidence:.2f}\n")
                f.write(f"Palabras: {lesson.word_count}\n")
                f.write("=" * 60 + "\n\n")
                f.write(lesson.content)
            
            # Agregar al índice
            lessons_index["lessons"][lesson_num] = {
                "number": lesson.number,
                "title": lesson.title,
                "word_count": lesson.word_count,
                "char_count": lesson.char_count,
                "position": lesson.position,
                "extraction_method": lesson.extraction_method,
                "confidence": lesson.confidence,
                "file_path": str(lesson_file.relative_to(PROCESSED_DATA_DIR))
            }
            
            # Estadísticas
            method_counts[lesson.extraction_method] = method_counts.get(lesson.extraction_method, 0) + 1
            
            if lesson.confidence >= 0.8:
                confidence_ranges["high"] += 1
            elif lesson.confidence >= 0.6:
                confidence_ranges["medium"] += 1
            else:
                confidence_ranges["low"] += 1
        
        # Completar estadísticas
        lessons_index["statistics"]["methods_used"] = method_counts
        lessons_index["statistics"]["confidence_distribution"] = confidence_ranges
        
        # Guardar índice
        index_file = INDICES_DIR / "365_lessons_advanced.json"
        index_file.parent.mkdir(exist_ok=True)
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(lessons_index, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Lecciones avanzadas guardadas en: {lessons_dir}")
        self.logger.info(f"Índice avanzado guardado en: {index_file}")

def main():
    """Función principal del segmentador avanzado"""
    # Cargar contenido
    text_file = PROCESSED_DATA_DIR / "ucdm_complete_text.txt"
    
    if not text_file.exists():
        print("❌ Error: No se encontró el archivo de texto extraído")
        print(f"   Ejecuta primero: python extraction/pdf_extractor.py")
        return 1
    
    print("🔄 Cargando contenido de UCDM para segmentación avanzada...")
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crear segmentador avanzado
    segmenter = AdvancedUCDMLessonSegmenter(content)
    
    # Ejecutar segmentación
    lessons = segmenter.segment_lessons_advanced()
    
    if not lessons:
        print("❌ Error: No se pudieron extraer lecciones")
        return 1
    
    # Guardar resultados
    segmenter.save_lessons_advanced(lessons)
    
    # Mostrar estadísticas
    print(f"\n{'='*60}")
    print("SEGMENTACIÓN AVANZADA COMPLETADA")
    print(f"{'='*60}")
    
    coverage = (len(lessons) / 365) * 100
    print(f"\n📊 RESULTADOS GENERALES:")
    print(f"   Lecciones extraídas: {len(lessons)}/365 ({coverage:.1f}%)")
    print(f"   Rango: {min(lessons.keys())}-{max(lessons.keys())}")
    
    # Estadísticas por método
    methods = {}
    confidence_stats = {"high": 0, "medium": 0, "low": 0}
    
    for lesson in lessons.values():
        methods[lesson.extraction_method] = methods.get(lesson.extraction_method, 0) + 1
        
        if lesson.confidence >= 0.8:
            confidence_stats["high"] += 1
        elif lesson.confidence >= 0.6:
            confidence_stats["medium"] += 1
        else:
            confidence_stats["low"] += 1
    
    print(f"\n🔍 MÉTODOS DE EXTRACCIÓN:")
    for method, count in methods.items():
        print(f"   {method}: {count} lecciones")
    
    print(f"\n📈 CONFIANZA:")
    print(f"   Alta (≥0.8): {confidence_stats['high']}")
    print(f"   Media (0.6-0.8): {confidence_stats['medium']}")
    print(f"   Baja (<0.6): {confidence_stats['low']}")
    
    # Ejemplos de lecciones
    print(f"\n📖 EJEMPLOS EXTRAÍDOS:")
    example_nums = [1, 50, 100, 200, 365] if 365 in lessons else sorted(lessons.keys())[:5]
    
    for num in example_nums:
        if num in lessons:
            lesson = lessons[num]
            print(f"\n   Lección {num}: {lesson.title[:50]}...")
            print(f"   Método: {lesson.extraction_method}, Confianza: {lesson.confidence:.2f}")
            print(f"   Palabras: {lesson.word_count}")
    
    print(f"\n✅ ARCHIVOS GENERADOS:")
    print(f"   - Lecciones: {PROCESSED_DATA_DIR / 'lessons_advanced'}")
    print(f"   - Índice: {INDICES_DIR / '365_lessons_advanced.json'}")
    
    print(f"\n⭐ TASA DE ÉXITO: {coverage:.1f}%")
    
    return 0 if coverage > 50 else 1

if __name__ == "__main__":
    from datetime import datetime
    exit(main())