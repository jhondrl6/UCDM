#!/usr/bin/env python3
"""
Segmentador inteligente para las 365 lecciones de UCDM
Extrae cada lección individual con su título y contenido completo
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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
    
    def __post_init__(self):
        self.word_count = len(self.content.split())
        self.char_count = len(self.content)

class UCDMLessonSegmenter:
    """Segmentador inteligente para las lecciones de UCDM"""
    
    def __init__(self, content_text: str):
        self.content = content_text
        self.lessons = {}
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def find_lesson_boundaries(self) -> List[Dict]:
        """Encontrar los límites de cada lección en el texto"""
        # Patrones más específicos para identificar lecciones
        lesson_patterns = [
            r"(?:\n|^)\s*Lección\s+(\d{1,3})\s*[\.:]?\s*(.+?)(?=\n)",
            r"(?:\n|^)\s*LECCIÓN\s+(\d{1,3})\s*[\.:]?\s*(.+?)(?=\n)",
            r"(?:\n|^)\s*Leccion\s+(\d{1,3})\s*[\.:]?\s*(.+?)(?=\n)"  # Sin tilde
        ]
        
        lesson_boundaries = []
        
        for pattern_idx, pattern in enumerate(lesson_patterns):
            matches = re.finditer(pattern, self.content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                try:
                    lesson_num = int(match.group(1))
                    lesson_title = match.group(2).strip() if match.group(2) else f"Lección {lesson_num}"
                    
                    # Filtrar números válidos de lección
                    if 1 <= lesson_num <= 365:
                        # Validar que no sea solo un número de página
                        context = self.content[max(0, match.start()-50):match.end()+100]
                        
                        # Rechazar si parece ser solo un número de página
                        if len(lesson_title) < 3 and pattern_idx >= 3:
                            # Para patrones de solo números, verificar contexto
                            if not re.search(r'(ejercicio|práctica|repite|afirma)', context, re.IGNORECASE):
                                continue
                        
                        lesson_boundaries.append({
                            'number': lesson_num,
                            'title': lesson_title,
                            'start_pos': match.start(),
                            'end_pos': match.end(),
                            'full_match': match.group(0),
                            'pattern_used': pattern_idx
                        })
                except (ValueError, IndexError):
                    continue
        
        # Eliminar duplicados más inteligentemente
        # Agrupar por número de lección y elegir el mejor match
        lesson_groups = {}
        for boundary in lesson_boundaries:
            lesson_num = boundary['number']
            if lesson_num not in lesson_groups:
                lesson_groups[lesson_num] = []
            lesson_groups[lesson_num].append(boundary)
        
        unique_boundaries = []
        for lesson_num, candidates in lesson_groups.items():
            # Elegir el mejor candidato para esta lección
            # Preferir patrones más específicos (índices menores)
            best_candidate = min(candidates, key=lambda x: (x['pattern_used'], abs(len(x['title']) - 20)))
            unique_boundaries.append(best_candidate)
        
        # Ordenar por posición en el texto
        unique_boundaries.sort(key=lambda x: x['start_pos'])
        
        self.logger.info(f"Encontrados {len(unique_boundaries)} límites de lecciones")
        return unique_boundaries
    
    def extract_lesson_content(self, start_boundary: Dict, next_boundary: Optional[Dict] = None) -> str:
        """Extraer el contenido completo de una lección"""
        start_pos = start_boundary['end_pos']
        
        # Determinar dónde termina esta lección
        if next_boundary:
            # La lección termina donde empieza la siguiente
            end_pos = next_boundary['start_pos']
        else:
            # Es la última lección, buscar el final del Libro de Ejercicios
            # Buscar patrones que indiquen el final con ventana de búsqueda
            search_window = 10000  # Buscar en los próximos 10k caracteres
            search_text = self.content[start_pos:start_pos + search_window]
            
            end_patterns = [
                r"MANUAL\s+PARA\s+EL\s+MAESTRO",
                r"TERCERA\s+PARTE",
                r"EPÍLOGO",
                r"EPILOGO",
                r"Manual\s+del\s+Maestro",
                r"Tercera\s+Parte"
            ]
            
            end_pos = len(self.content)
            for pattern in end_patterns:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    end_pos = start_pos + match.start()
                    break
        
        # Extraer contenido
        raw_content = self.content[start_pos:end_pos].strip()
        
        # Limpiar el contenido
        content = self.clean_lesson_content(raw_content)
        
        return content
    
    def clean_lesson_content(self, raw_content: str) -> str:
        """Limpiar y formatear el contenido de la lección"""
        content = raw_content
        
        # Remover números de página aislados
        content = re.sub(r'\n\s*\d+\s*\n', '\n', content)
        content = re.sub(r'^\s*\d+\s*\n', '', content)
        
        # Remover saltos de línea excesivos
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Normalizar espacios pero mantener estructura
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Normalizar espacios en cada línea
            cleaned_line = re.sub(r' +', ' ', line.strip())
            if cleaned_line:  # Solo agregar líneas no vacías
                cleaned_lines.append(cleaned_line)
        
        content = '\n'.join(cleaned_lines)
        
        # Remover contenido que claramente no pertenece a la lección
        content = re.sub(r'.*?MANUAL\s+PARA\s+EL\s+MAESTRO.*', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'.*?TERCERA\s+PARTE.*', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        return content.strip()
    
    def segment_all_lessons(self) -> Dict[int, UCDMLesson]:
        """Segmentar todas las lecciones del Libro de Ejercicios"""
        self.logger.info("Iniciando segmentación de lecciones...")
        
        # Encontrar límites de todas las lecciones
        boundaries = self.find_lesson_boundaries()
        
        if not boundaries:
            self.logger.error("No se encontraron lecciones en el contenido")
            return {}
        
        self.logger.info(f"Encontrados {len(boundaries)} límites únicos de lecciones")
        
        # Extraer cada lección
        lessons = {}
        processed_count = 0
        
        for i, boundary in enumerate(boundaries):
            lesson_num = boundary['number']
            lesson_title = boundary['title']
            
            # Determinar el siguiente límite
            next_boundary = boundaries[i + 1] if i + 1 < len(boundaries) else None
            
            # Extraer contenido
            content = self.extract_lesson_content(boundary, next_boundary)
            
            # Validar que el contenido tenga sentido
            if len(content.strip()) < 20:  # Muy corto
                self.logger.warning(f"Lección {lesson_num} tiene contenido muy corto, omitiendo")
                continue
            
            # Crear objeto de lección
            lesson = UCDMLesson(
                number=lesson_num,
                title=lesson_title,
                content=content,
                position=boundary['start_pos']
            )
            
            lessons[lesson_num] = lesson
            processed_count += 1
            
            if processed_count % 50 == 0:
                self.logger.info(f"Procesadas {processed_count} lecciones válidas...")
        
        self.logger.info(f"Segmentación completada: {len(lessons)} lecciones extraídas")
        return lessons
    
    def validate_lesson_quality(self, lessons: Dict[int, UCDMLesson]) -> Dict[str, any]:
        """Validar la calidad de las lecciones extraídas"""
        validation_results = {
            "total_lessons": len(lessons),
            "lesson_numbers": sorted(lessons.keys()),
            "missing_lessons": [],
            "quality_issues": [],
            "statistics": {
                "avg_word_count": 0,
                "min_word_count": float('inf'),
                "max_word_count": 0,
                "total_words": 0
            }
        }
        
        # Identificar lecciones faltantes
        all_lessons = set(range(1, 366))
        found_lessons = set(lessons.keys())
        validation_results["missing_lessons"] = sorted(all_lessons - found_lessons)
        
        # Calcular estadísticas
        if lessons:
            word_counts = [lesson.word_count for lesson in lessons.values()]
            validation_results["statistics"]["avg_word_count"] = sum(word_counts) / len(word_counts)
            validation_results["statistics"]["min_word_count"] = min(word_counts)
            validation_results["statistics"]["max_word_count"] = max(word_counts)
            validation_results["statistics"]["total_words"] = sum(word_counts)
        
        # Identificar lecciones con posibles problemas de calidad
        for lesson_num, lesson in lessons.items():
            # Lecciones muy cortas (menos de 50 palabras)
            if lesson.word_count < 50:
                validation_results["quality_issues"].append({
                    "lesson": lesson_num,
                    "issue": "Contenido muy corto",
                    "word_count": lesson.word_count
                })
            
            # Lecciones sin título claro
            if not lesson.title or len(lesson.title.strip()) < 3:
                validation_results["quality_issues"].append({
                    "lesson": lesson_num,
                    "issue": "Título vacío o muy corto",
                    "title": lesson.title
                })
        
        return validation_results
    
    def save_lessons_to_files(self, lessons: Dict[int, UCDMLesson]) -> None:
        """Guardar lecciones en archivos individuales y en índice"""
        # Crear directorio para lecciones individuales
        lessons_dir = PROCESSED_DATA_DIR / "lessons"
        lessons_dir.mkdir(exist_ok=True)
        
        # Preparar datos para el índice
        lessons_index = {}
        
        for lesson_num, lesson in lessons.items():
            # Guardar lección individual
            lesson_file = lessons_dir / f"lesson_{lesson_num:03d}.txt"
            with open(lesson_file, 'w', encoding='utf-8') as f:
                f.write(f"Lección {lesson_num}: {lesson.title}\n")
                f.write("=" * 50 + "\n\n")
                f.write(lesson.content)
            
            # Agregar al índice
            lessons_index[lesson_num] = {
                "number": lesson.number,
                "title": lesson.title,
                "word_count": lesson.word_count,
                "char_count": lesson.char_count,
                "position": lesson.position,
                "section": lesson.section,
                "file_path": str(lesson_file.relative_to(PROCESSED_DATA_DIR))
            }
        
        # Guardar índice completo
        index_file = INDICES_DIR / "365_lessons_indexed.json"
        index_file.parent.mkdir(exist_ok=True)
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "total_lessons": len(lessons),
                    "extraction_date": str(datetime.now()),
                    "source": "Un Curso de Milagros - Libro de Ejercicios"
                },
                "lessons": lessons_index
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Lecciones guardadas en: {lessons_dir}")
        self.logger.info(f"Índice guardado en: {index_file}")

def main():
    """Función principal para ejecutar la segmentación"""
    # Cargar contenido extraído
    text_file = PROCESSED_DATA_DIR / "ucdm_complete_text.txt"
    
    if not text_file.exists():
        print("❌ Error: No se encontró el archivo de texto extraído")
        print(f"   Ejecuta primero: python extraction/pdf_extractor.py")
        return 1
    
    print("Cargando contenido de UCDM...")
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crear segmentador
    segmenter = UCDMLessonSegmenter(content)
    
    # Segmentar lecciones
    lessons = segmenter.segment_all_lessons()
    
    if not lessons:
        print("❌ Error: No se pudieron extraer lecciones")
        return 1
    
    # Validar calidad
    validation = segmenter.validate_lesson_quality(lessons)
    
    # Guardar resultados
    segmenter.save_lessons_to_files(lessons)
    
    # Guardar reporte de validación
    validation_file = PROCESSED_DATA_DIR / "lessons_validation.json"
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation, f, indent=2, ensure_ascii=False)
    
    # Mostrar resultados
    print(f"\n{'='*60}")
    print("SEGMENTACIÓN DE LECCIONES COMPLETADA")
    print(f"{'='*60}")
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Lecciones extraídas: {validation['total_lessons']}/365")
    print(f"   Rango de lecciones: {min(validation['lesson_numbers'])}-{max(validation['lesson_numbers'])}")
    
    if validation['missing_lessons']:
        missing_count = len(validation['missing_lessons'])
        print(f"   Lecciones faltantes: {missing_count}")
        if missing_count <= 10:
            print(f"   Números faltantes: {validation['missing_lessons']}")
        else:
            print(f"   Algunos faltantes: {validation['missing_lessons'][:10]}...")
    
    print(f"\n📈 ESTADÍSTICAS:")
    stats = validation['statistics']
    print(f"   Promedio de palabras por lección: {stats['avg_word_count']:.0f}")
    print(f"   Lección más corta: {stats['min_word_count']} palabras")
    print(f"   Lección más larga: {stats['max_word_count']} palabras")
    print(f"   Total de palabras: {stats['total_words']:,}")
    
    if validation['quality_issues']:
        print(f"\n⚠️  PROBLEMAS DE CALIDAD: {len(validation['quality_issues'])}")
        for issue in validation['quality_issues'][:5]:  # Mostrar solo los primeros 5
            print(f"   - Lección {issue['lesson']}: {issue['issue']}")
    
    print(f"\n✅ Archivos generados:")
    print(f"   - Lecciones individuales: {PROCESSED_DATA_DIR / 'lessons'}")
    print(f"   - Índice de lecciones: {INDICES_DIR / '365_lessons_indexed.json'}")
    print(f"   - Reporte de validación: {validation_file}")
    
    # Mostrar algunas lecciones de ejemplo
    print(f"\n📖 EJEMPLOS DE LECCIONES EXTRAÍDAS:")
    example_lessons = [1, 50, 100, 200, 365] if 365 in lessons else [1, 50, 100, 200]
    
    for lesson_num in example_lessons:
        if lesson_num in lessons:
            lesson = lessons[lesson_num]
            print(f"\n   Lección {lesson_num}: {lesson.title}")
            print(f"   Palabras: {lesson.word_count}, Caracteres: {lesson.char_count}")
            # Mostrar inicio del contenido
            preview = lesson.content[:100].replace('\n', ' ')
            print(f"   Inicio: {preview}...")
    
    success_rate = (validation['total_lessons'] / 365) * 100
    print(f"\n⭐ TASA DE ÉXITO: {success_rate:.1f}%")
    
    # Si el éxito es bajo, intentar análisis adicional
    if success_rate < 50:
        print(f"\n🔍 ANÁLISIS ADICIONAL (debido a baja tasa de éxito):")
        
        # Buscar patrones de lecciones más generales
        general_patterns = [
            r'Lección\s+\d+',
            r'LECCIÓN\s+\d+',
            r'\d+\s*[\.-]\s*[A-Z]'
        ]
        
        for i, pattern in enumerate(general_patterns):
            matches = re.findall(pattern, content, re.IGNORECASE)
            print(f"   Patrón {i+1} ('{pattern[:20]}...'): {len(matches)} coincidencias")
        
        # Buscar contenido del Libro de Ejercicios específicamente
        workbook_match = re.search(r'LIBRO\s+DE\s+EJERCICIOS', content, re.IGNORECASE)
        if workbook_match:
            workbook_start = workbook_match.end()
            workbook_content = content[workbook_start:workbook_start + 50000]  # Primeros 50k chars
            lesson_count = len(re.findall(r'Lección\s+\d+', workbook_content, re.IGNORECASE))
            print(f"   En sección 'Libro de Ejercicios': {lesson_count} lecciones encontradas")
    
    return 0 if success_rate > 30 else 1  # Reducir umbral para desarrollo

if __name__ == "__main__":
    from datetime import datetime
    import re  # Agregar import faltante
    exit(main())