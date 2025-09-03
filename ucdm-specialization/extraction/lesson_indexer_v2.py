#!/usr/bin/env python3
"""
Indexador de lecciones UCDM con mapeo fecha-lección
Crea sistema de búsqueda por fecha, número y concepto
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

@dataclass
class LessonIndex:
    """Índice de una lección de UCDM"""
    number: int
    title: str
    key_concepts: List[str]
    word_count: int
    file_path: str
    extraction_method: str
    confidence: float
    daily_dates: List[str]  # Fechas cuando esta lección es "del día"

class UCDMLessonIndexer:
    """Indexador completo de lecciones UCDM"""
    
    def __init__(self):
        self.lessons = {}
        self.concept_index = {}
        self.date_mapper = {}
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_extracted_lessons(self) -> Dict[int, Dict]:
        """Cargar lecciones extraídas del segmentador avanzado"""
        index_file = INDICES_DIR / "365_lessons_advanced.json"
        
        if not index_file.exists():
            self.logger.error(f"No se encontró el índice de lecciones: {index_file}")
            return {}
        
        with open(index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.logger.info(f"Cargadas {len(data['lessons'])} lecciones del segmentador avanzado")
        return data['lessons']
    
    def extract_key_concepts(self, lesson_content: str, lesson_title: str) -> List[str]:
        """Extraer conceptos clave de una lección"""
        # Conceptos fundamentales de UCDM
        core_concepts = {
            'perdon': [r'\\bperdón\\b', r'\\bperdonar\\b', r'\\bperdonas\\b', r'\\bperdona\\b'],
            'milagro': [r'\\bmilagro\\b', r'\\bmilagros\\b'],
            'amor': [r'\\bamor\\b'],
            'dios': [r'\\bdios\\b'],
            'paz': [r'\\bpaz\\b'],
            'miedo': [r'\\bmiedo\\b', r'\\bmiedos\\b'],
            'espiritu_santo': [r'espíritu\\s+santo', r'espiritu\\s+santo'],
            'cristo': [r'\\bcristo\\b'],
            'ego': [r'\\bego\\b'],
            'culpa': [r'\\bculpa\\b', r'\\bculpas\\b'],
            'salvacion': [r'\\bsalvación\\b', r'\\bsalvacion\\b'],
            'expiacion': [r'\\bexpiación\\b', r'\\bexpiacion\\b'],
            'luz': [r'\\bluz\\b'],
            'verdad': [r'\\bverdad\\b'],
            'ilusion': [r'\\bilusión\\b', r'\\bilusion\\b', r'\\bilusiones\\b'],
            'separacion': [r'\\bseparación\\b', r'\\bseparacion\\b'],
            'unidad': [r'\\bunidad\\b'],
            'santidad': [r'\\bsantidad\\b'],
            'inocencia': [r'\\binocencia\\b'],
            'hermano': [r'\\bhermano\\b', r'\\bhermanos\\b'],
            'hijo': [r'\\bhijo\\b', r'\\bhijos\\b'],
            'padre': [r'\\bpadre\\b'],
            'bendicion': [r'\\bbendición\\b', r'\\bbendicion\\b'],
            'gratitud': [r'\\bgratitud\\b'],
            'gozo': [r'\\bgozo\\b'],
            'felicidad': [r'\\bfelicidad\\b'],
            'seguridad': [r'\\bseguridad\\b'],
            'proteccion': [r'\\bprotección\\b', r'\\bproteccion\\b']
        }
        
        # Combinar título y contenido para análisis
        full_text = f"{lesson_title} {lesson_content}".lower()
        
        found_concepts = []
        
        for concept, patterns in core_concepts.items():
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    found_concepts.append(concept)
                    break  # Una vez encontrado el concepto, no necesitamos más patrones
        
        # Agregar conceptos específicos del título si contiene palabras clave
        title_words = lesson_title.lower().split()
        for word in title_words:
            if len(word) > 4 and word not in ['lección', 'ejercicio', 'práctica']:
                # Verificar si es una palabra significativa
                if any(char.isalpha() for char in word):
                    found_concepts.append(f"titulo_{word}")
        
        return list(set(found_concepts))  # Eliminar duplicados
    
    def create_date_mapping(self, total_lessons: int) -> Dict[str, int]:
        """Crear mapeo de fechas a números de lección"""
        # El Libro de Ejercicios está diseñado para un año (365 días)
        # Tradicionalmente se comienza el 1 de enero
        
        date_mapping = {}
        
        # Año de referencia (usaremos 2024 como base para el mapeo)
        base_year = 2024
        start_date = datetime(base_year, 1, 1)
        
        for lesson_num in range(1, min(366, total_lessons + 1)):
            # Calcular la fecha correspondiente
            lesson_date = start_date + timedelta(days=lesson_num - 1)
            date_key = lesson_date.strftime("%m-%d")  # Formato MM-DD
            
            date_mapping[date_key] = lesson_num
        
        # Mapeo para años posteriores (el patrón se repite)
        self.logger.info(f"Creado mapeo de fechas para {len(date_mapping)} días del año")
        return date_mapping
    
    def get_lesson_for_date(self, target_date: datetime) -> Optional[int]:
        """Obtener número de lección para una fecha específica"""
        date_key = target_date.strftime("%m-%d")
        return self.date_mapper.get(date_key)
    
    def get_lesson_for_today(self) -> Optional[int]:
        """Obtener lección para hoy"""
        return self.get_lesson_for_date(datetime.now())
    
    def create_concept_index(self, lessons_data: Dict[int, Dict]) -> Dict[str, List[int]]:
        """Crear índice de conceptos a lecciones"""
        concept_to_lessons = {}
        
        for lesson_num, lesson_data in lessons_data.items():
            # Leer el contenido de la lección
            lesson_file = PROCESSED_DATA_DIR / lesson_data['file_path']
            
            if lesson_file.exists():
                with open(lesson_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extraer conceptos
                concepts = self.extract_key_concepts(content, lesson_data['title'])
                
                # Indexar conceptos
                for concept in concepts:
                    if concept not in concept_to_lessons:
                        concept_to_lessons[concept] = []
                    concept_to_lessons[concept].append(lesson_num)
        
        # Ordenar lecciones por número
        for concept in concept_to_lessons:
            concept_to_lessons[concept].sort()
        
        self.logger.info(f"Índice de conceptos creado: {len(concept_to_lessons)} conceptos únicos")
        return concept_to_lessons
    
    def search_lessons_by_concept(self, concept_query: str) -> List[int]:
        """Buscar lecciones por concepto"""
        concept_query = concept_query.lower().strip()
        
        # Búsqueda exacta
        if concept_query in self.concept_index:
            return self.concept_index[concept_query]
        
        # Búsqueda parcial
        matching_lessons = set()
        for concept, lessons in self.concept_index.items():
            if concept_query in concept or concept in concept_query:
                matching_lessons.update(lessons)
        
        return sorted(list(matching_lessons))
    
    def create_comprehensive_index(self) -> Dict:
        """Crear índice completo del sistema"""
        self.logger.info("=== Creando índice completo de lecciones UCDM ===")
        
        # Cargar lecciones extraídas
        lessons_data = self.load_extracted_lessons()
        
        if not lessons_data:
            self.logger.error("No se pudieron cargar las lecciones")
            return {}
        
        # Crear mapeo de fechas
        self.date_mapper = self.create_date_mapping(len(lessons_data))
        
        # Crear índice de conceptos
        self.concept_index = self.create_concept_index(lessons_data)
        
        # Crear estadísticas
        total_concepts = len(self.concept_index)
        avg_concepts_per_lesson = sum(len(lessons) for lessons in self.concept_index.values()) / len(lessons_data)
        
        # Compilar índice completo
        comprehensive_index = {
            "metadata": {
                "creation_date": str(datetime.now()),
                "total_lessons": len(lessons_data),
                "total_concepts": total_concepts,
                "avg_concepts_per_lesson": round(avg_concepts_per_lesson, 2),
                "coverage_percentage": (len(lessons_data) / 365) * 100
            },
            "date_mapping": self.date_mapper,
            "concept_index": self.concept_index,
            "lesson_details": {}
        }
        
        # Agregar detalles de cada lección
        for lesson_num, lesson_data in lessons_data.items():
            # Obtener fechas cuando esta lección es "del día"
            lesson_dates = []
            for date_key, mapped_lesson in self.date_mapper.items():
                if mapped_lesson == lesson_num:
                    lesson_dates.append(date_key)
            
            # Obtener conceptos de esta lección
            lesson_concepts = []
            for concept, lessons in self.concept_index.items():
                if lesson_num in lessons:
                    lesson_concepts.append(concept)
            
            comprehensive_index["lesson_details"][lesson_num] = {
                "title": lesson_data['title'],
                "word_count": lesson_data['word_count'],
                "concepts": lesson_concepts,
                "daily_dates": lesson_dates,
                "file_path": lesson_data['file_path'],
                "extraction_method": lesson_data['extraction_method'],
                "confidence": lesson_data['confidence']
            }
        
        return comprehensive_index
    
    def save_comprehensive_index(self, index_data: Dict) -> None:
        """Guardar índice completo"""
        # Guardar índice principal
        main_index_file = INDICES_DIR / "ucdm_comprehensive_index.json"
        main_index_file.parent.mkdir(exist_ok=True)
        
        with open(main_index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        # Guardar mapeo de fechas por separado (para acceso rápido)
        date_mapper_file = INDICES_DIR / "lesson_date_mapper.json"
        with open(date_mapper_file, 'w', encoding='utf-8') as f:
            json.dump({
                "date_to_lesson": index_data["date_mapping"],
                "lesson_to_date": {str(lesson): date for date, lesson in index_data["date_mapping"].items()},
                "usage_examples": {
                    "today": self.get_lesson_for_today(),
                    "new_year": index_data["date_mapping"].get("01-01"),
                    "christmas": index_data["date_mapping"].get("12-25")
                }
            }, f, indent=2, ensure_ascii=False)
        
        # Guardar índice de conceptos por separado
        concept_index_file = INDICES_DIR / "concept_to_lessons_index.json"
        with open(concept_index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "concept_index": index_data["concept_index"],
                "concept_statistics": {
                    "total_concepts": len(index_data["concept_index"]),
                    "most_common_concepts": sorted(
                        [(concept, len(lessons)) for concept, lessons in index_data["concept_index"].items()],
                        key=lambda x: x[1], reverse=True
                    )[:20]
                }
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Índice completo guardado en: {main_index_file}")
        self.logger.info(f"Mapeo de fechas guardado en: {date_mapper_file}")
        self.logger.info(f"Índice de conceptos guardado en: {concept_index_file}")
    
    def demonstrate_functionality(self, index_data: Dict) -> None:
        """Demostrar funcionalidad del indexador"""
        print(f"\\n{'='*60}")
        print("DEMOSTRACIÓN DE FUNCIONALIDAD DEL INDEXADOR")
        print(f"{'='*60}")
        
        # Lección de hoy
        today_lesson = self.get_lesson_for_today()
        if today_lesson and today_lesson in index_data["lesson_details"]:
            lesson_info = index_data["lesson_details"][today_lesson]
            print(f"\\n📅 LECCIÓN DE HOY ({datetime.now().strftime('%d/%m/%Y')}):")
            print(f"   Lección {today_lesson}: {lesson_info['title']}")
            if lesson_info['concepts']:
                print(f"   Conceptos: {', '.join(lesson_info['concepts'][:5])}...")
        
        # Búsqueda por conceptos
        test_concepts = ['perdon', 'amor', 'miedo', 'paz']
        print(f"\\n🔍 BÚSQUEDA POR CONCEPTOS:")
        
        for concept in test_concepts:
            lessons = self.search_lessons_by_concept(concept)
            if lessons:
                print(f"   '{concept}': {len(lessons)} lecciones encontradas (ej: {lessons[:3]}...)")
        
        # Estadísticas de conceptos más comunes
        if self.concept_index:
            concept_stats = sorted(
                [(concept, len(lessons)) for concept, lessons in self.concept_index.items()],
                key=lambda x: x[1], reverse=True
            )[:10]
            
            print(f"\\n📊 CONCEPTOS MÁS FRECUENTES:")
            for concept, count in concept_stats:
                print(f"   {concept}: {count} lecciones")
        
        # Ejemplos de fechas específicas
        special_dates = {
            "01-01": "Año Nuevo",
            "12-25": "Navidad",
            "06-21": "Solsticio de Verano",
            "09-21": "Equinoccio de Otoño"
        }
        
        print(f"\\n📅 LECCIONES EN FECHAS ESPECIALES:")
        for date_key, occasion in special_dates.items():
            lesson_num = self.date_mapper.get(date_key)
            if lesson_num and lesson_num in index_data["lesson_details"]:
                lesson_title = index_data["lesson_details"][lesson_num]['title']
                print(f"   {occasion} ({date_key}): Lección {lesson_num} - {lesson_title[:50]}...")

def main():
    """Función principal del indexador"""
    indexer = UCDMLessonIndexer()
    
    # Crear índice completo
    comprehensive_index = indexer.create_comprehensive_index()
    
    if not comprehensive_index:
        print("❌ Error: No se pudo crear el índice completo")
        return 1
    
    # Guardar índices
    indexer.save_comprehensive_index(comprehensive_index)
    
    # Mostrar estadísticas
    metadata = comprehensive_index["metadata"]
    print(f"\\n{'='*60}")
    print("INDEXACIÓN COMPLETA DE LECCIONES UCDM")
    print(f"{'='*60}")
    
    print(f"\\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   Total de lecciones indexadas: {metadata['total_lessons']}/365")
    print(f"   Cobertura: {metadata['coverage_percentage']:.1f}%")
    print(f"   Conceptos únicos identificados: {metadata['total_concepts']}")
    print(f"   Promedio de conceptos por lección: {metadata['avg_concepts_per_lesson']}")
    
    print(f"\\n📅 MAPEO DE FECHAS:")
    print(f"   Días del año mapeados: {len(comprehensive_index['date_mapping'])}")
    print(f"   Patrón: 1 enero = Lección 1, 31 diciembre = Lección 365")
    
    print(f"\\n🔍 ÍNDICE DE CONCEPTOS:")
    concept_count = len(comprehensive_index['concept_index'])
    print(f"   Conceptos indexados: {concept_count}")
    
    # Demostrar funcionalidad
    indexer.demonstrate_functionality(comprehensive_index)
    
    print(f"\\n✅ ARCHIVOS GENERADOS:")
    print(f"   - Índice principal: {INDICES_DIR / 'ucdm_comprehensive_index.json'}")
    print(f"   - Mapeo de fechas: {INDICES_DIR / 'lesson_date_mapper.json'}")
    print(f"   - Índice de conceptos: {INDICES_DIR / 'concept_to_lessons_index.json'}")
    
    coverage = metadata['coverage_percentage']
    print(f"\\n⭐ ÍNDICE COMPLETADO: {coverage:.1f}% de cobertura")
    
    return 0 if coverage > 40 else 1

if __name__ == "__main__":
    exit(main())