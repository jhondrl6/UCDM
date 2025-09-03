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
            'perdón': [r'\bperdón\b', r'\bperdonar\b', r'\bperdonas\b', r'\bperdona\b'],
            'milagro': [r'\bmilagro\b', r'\bmilagros\b'],
            'amor': [r'\bamor\b'],
            'dios': [r'\bdios\b'],
            'paz': [r'\bpaz\b'],
            'miedo': [r'\bmiedo\b', r'\bmiedos\b'],
            'espíritu_santo': [r'espíritu\s+santo', r'espiritu\s+santo'],
            'cristo': [r'\bcristo\b'],
            'ego': [r'\bego\b'],
            'culpa': [r'\bculpa\b', r'\bculpas\b'],
            'salvación': [r'\bsalvación\b', r'\bsalvacion\b'],
            'expiación': [r'\bexpiación\b', r'\bexpiacion\b'],
            'luz': [r'\bluz\b'],
            'verdad': [r'\bverdad\b'],
            'ilusión': [r'\bilusión\b', r'\bilusion\b', r'\bilusiones\b'],
            'separación': [r'\bseparación\b', r'\bseparacion\b'],
            'unidad': [r'\bunidad\b'],
            'santidad': [r'\bsantidad\b'],
            'inocencia': [r'\binocencia\b'],
            'hermano': [r'\bhermano\b', r'\bhermanos\b'],
            'hijo': [r'\bhijo\b', r'\bhijos\b'],
            'padre': [r'\bpadre\b'],
            'bendición': [r'\bbendición\b', r'\bbendicion\b'],
            'gratitud': [r'\bgratitud\b'],
            'gozo': [r'\bgozo\b'],
            'felicidad': [r'\bfelicidad\b'],
            'seguridad': [r'\bseguridad\b'],
            'protección': [r'\bprotección\b', r'\bproteccion\b']
        }\n        \n        # Combinar título y contenido para análisis\n        full_text = f\"{lesson_title} {lesson_content}\".lower()\n        \n        found_concepts = []\n        \n        for concept, patterns in core_concepts.items():\n            for pattern in patterns:\n                if re.search(pattern, full_text, re.IGNORECASE):\n                    found_concepts.append(concept)\n                    break  # Una vez encontrado el concepto, no necesitamos más patrones\n        \n        # Agregar conceptos específicos del título si contiene palabras clave\n        title_words = lesson_title.lower().split()\n        for word in title_words:\n            if len(word) > 4 and word not in ['lección', 'ejercicio', 'práctica']:\n                # Verificar si es una palabra significativa\n                if any(char.isalpha() for char in word):\n                    found_concepts.append(f\"título_{word}\")\n        \n        return list(set(found_concepts))  # Eliminar duplicados\n    \n    def create_date_mapping(self, total_lessons: int) -> Dict[str, int]:\n        \"\"\"Crear mapeo de fechas a números de lección\"\"\"\n        # El Libro de Ejercicios está diseñado para un año (365 días)\n        # Tradicionalmente se comienza el 1 de enero\n        \n        date_mapping = {}\n        \n        # Año de referencia (usaremos 2024 como base para el mapeo)\n        base_year = 2024\n        start_date = datetime(base_year, 1, 1)\n        \n        for lesson_num in range(1, min(366, total_lessons + 1)):\n            # Calcular la fecha correspondiente\n            lesson_date = start_date + timedelta(days=lesson_num - 1)\n            date_key = lesson_date.strftime(\"%m-%d\")  # Formato MM-DD\n            \n            date_mapping[date_key] = lesson_num\n        \n        # Mapeo para años posteriores (el patrón se repite)\n        self.logger.info(f\"Creado mapeo de fechas para {len(date_mapping)} días del año\")\n        return date_mapping\n    \n    def get_lesson_for_date(self, target_date: datetime) -> Optional[int]:\n        \"\"\"Obtener número de lección para una fecha específica\"\"\"\n        date_key = target_date.strftime(\"%m-%d\")\n        return self.date_mapper.get(date_key)\n    \n    def get_lesson_for_today(self) -> Optional[int]:\n        \"\"\"Obtener lección para hoy\"\"\"\n        return self.get_lesson_for_date(datetime.now())\n    \n    def create_concept_index(self, lessons_data: Dict[int, Dict]) -> Dict[str, List[int]]:\n        \"\"\"Crear índice de conceptos a lecciones\"\"\"\n        concept_to_lessons = {}\n        \n        for lesson_num, lesson_data in lessons_data.items():\n            # Leer el contenido de la lección\n            lesson_file = PROCESSED_DATA_DIR / lesson_data['file_path']\n            \n            if lesson_file.exists():\n                with open(lesson_file, 'r', encoding='utf-8') as f:\n                    content = f.read()\n                \n                # Extraer conceptos\n                concepts = self.extract_key_concepts(content, lesson_data['title'])\n                \n                # Indexar conceptos\n                for concept in concepts:\n                    if concept not in concept_to_lessons:\n                        concept_to_lessons[concept] = []\n                    concept_to_lessons[concept].append(lesson_num)\n        \n        # Ordenar lecciones por número\n        for concept in concept_to_lessons:\n            concept_to_lessons[concept].sort()\n        \n        self.logger.info(f\"Índice de conceptos creado: {len(concept_to_lessons)} conceptos únicos\")\n        return concept_to_lessons\n    \n    def search_lessons_by_concept(self, concept_query: str) -> List[int]:\n        \"\"\"Buscar lecciones por concepto\"\"\"\n        concept_query = concept_query.lower().strip()\n        \n        # Búsqueda exacta\n        if concept_query in self.concept_index:\n            return self.concept_index[concept_query]\n        \n        # Búsqueda parcial\n        matching_lessons = set()\n        for concept, lessons in self.concept_index.items():\n            if concept_query in concept or concept in concept_query:\n                matching_lessons.update(lessons)\n        \n        return sorted(list(matching_lessons))\n    \n    def create_comprehensive_index(self) -> Dict:\n        \"\"\"Crear índice completo del sistema\"\"\"\n        self.logger.info(\"=== Creando índice completo de lecciones UCDM ===\")\n        \n        # Cargar lecciones extraídas\n        lessons_data = self.load_extracted_lessons()\n        \n        if not lessons_data:\n            self.logger.error(\"No se pudieron cargar las lecciones\")\n            return {}\n        \n        # Crear mapeo de fechas\n        self.date_mapper = self.create_date_mapping(len(lessons_data))\n        \n        # Crear índice de conceptos\n        self.concept_index = self.create_concept_index(lessons_data)\n        \n        # Crear estadísticas\n        total_concepts = len(self.concept_index)\n        avg_concepts_per_lesson = sum(len(lessons) for lessons in self.concept_index.values()) / len(lessons_data)\n        \n        # Compilar índice completo\n        comprehensive_index = {\n            \"metadata\": {\n                \"creation_date\": str(datetime.now()),\n                \"total_lessons\": len(lessons_data),\n                \"total_concepts\": total_concepts,\n                \"avg_concepts_per_lesson\": round(avg_concepts_per_lesson, 2),\n                \"coverage_percentage\": (len(lessons_data) / 365) * 100\n            },\n            \"date_mapping\": self.date_mapper,\n            \"concept_index\": self.concept_index,\n            \"lesson_details\": {}\n        }\n        \n        # Agregar detalles de cada lección\n        for lesson_num, lesson_data in lessons_data.items():\n            # Obtener fechas cuando esta lección es \"del día\"\n            lesson_dates = []\n            for date_key, mapped_lesson in self.date_mapper.items():\n                if mapped_lesson == lesson_num:\n                    lesson_dates.append(date_key)\n            \n            # Obtener conceptos de esta lección\n            lesson_concepts = []\n            for concept, lessons in self.concept_index.items():\n                if lesson_num in lessons:\n                    lesson_concepts.append(concept)\n            \n            comprehensive_index[\"lesson_details\"][lesson_num] = {\n                \"title\": lesson_data['title'],\n                \"word_count\": lesson_data['word_count'],\n                \"concepts\": lesson_concepts,\n                \"daily_dates\": lesson_dates,\n                \"file_path\": lesson_data['file_path'],\n                \"extraction_method\": lesson_data['extraction_method'],\n                \"confidence\": lesson_data['confidence']\n            }\n        \n        return comprehensive_index\n    \n    def save_comprehensive_index(self, index_data: Dict) -> None:\n        \"\"\"Guardar índice completo\"\"\"\n        # Guardar índice principal\n        main_index_file = INDICES_DIR / \"ucdm_comprehensive_index.json\"\n        main_index_file.parent.mkdir(exist_ok=True)\n        \n        with open(main_index_file, 'w', encoding='utf-8') as f:\n            json.dump(index_data, f, indent=2, ensure_ascii=False)\n        \n        # Guardar mapeo de fechas por separado (para acceso rápido)\n        date_mapper_file = INDICES_DIR / \"lesson_date_mapper.json\"\n        with open(date_mapper_file, 'w', encoding='utf-8') as f:\n            json.dump({\n                \"date_to_lesson\": index_data[\"date_mapping\"],\n                \"lesson_to_date\": {str(lesson): date for date, lesson in index_data[\"date_mapping\"].items()},\n                \"usage_examples\": {\n                    \"today\": self.get_lesson_for_today(),\n                    \"new_year\": index_data[\"date_mapping\"].get(\"01-01\"),\n                    \"christmas\": index_data[\"date_mapping\"].get(\"12-25\")\n                }\n            }, f, indent=2, ensure_ascii=False)\n        \n        # Guardar índice de conceptos por separado\n        concept_index_file = INDICES_DIR / \"concept_to_lessons_index.json\"\n        with open(concept_index_file, 'w', encoding='utf-8') as f:\n            json.dump({\n                \"concept_index\": index_data[\"concept_index\"],\n                \"concept_statistics\": {\n                    \"total_concepts\": len(index_data[\"concept_index\"]),\n                    \"most_common_concepts\": sorted(\n                        [(concept, len(lessons)) for concept, lessons in index_data[\"concept_index\"].items()],\n                        key=lambda x: x[1], reverse=True\n                    )[:20]\n                }\n            }, f, indent=2, ensure_ascii=False)\n        \n        self.logger.info(f\"Índice completo guardado en: {main_index_file}\")\n        self.logger.info(f\"Mapeo de fechas guardado en: {date_mapper_file}\")\n        self.logger.info(f\"Índice de conceptos guardado en: {concept_index_file}\")\n    \n    def demonstrate_functionality(self, index_data: Dict) -> None:\n        \"\"\"Demostrar funcionalidad del indexador\"\"\"\n        print(f\"\\n{'='*60}\")\n        print(\"DEMOSTRACIÓN DE FUNCIONALIDAD DEL INDEXADOR\")\n        print(f\"{'='*60}\")\n        \n        # Lección de hoy\n        today_lesson = self.get_lesson_for_today()\n        if today_lesson and today_lesson in index_data[\"lesson_details\"]:\n            lesson_info = index_data[\"lesson_details\"][today_lesson]\n            print(f\"\\n📅 LECCIÓN DE HOY ({datetime.now().strftime('%d/%m/%Y')}):\")\n            print(f\"   Lección {today_lesson}: {lesson_info['title']}\")\n            print(f\"   Conceptos: {', '.join(lesson_info['concepts'][:5])}...\")\n        \n        # Búsqueda por conceptos\n        test_concepts = ['perdón', 'amor', 'miedo', 'paz']\n        print(f\"\\n🔍 BÚSQUEDA POR CONCEPTOS:\")\n        \n        for concept in test_concepts:\n            lessons = self.search_lessons_by_concept(concept)\n            if lessons:\n                print(f\"   '{concept}': {len(lessons)} lecciones encontradas (ej: {lessons[:3]}...)\")\n        \n        # Estadísticas de conceptos más comunes\n        concept_stats = sorted(\n            [(concept, len(lessons)) for concept, lessons in self.concept_index.items()],\n            key=lambda x: x[1], reverse=True\n        )[:10]\n        \n        print(f\"\\n📊 CONCEPTOS MÁS FRECUENTES:\")\n        for concept, count in concept_stats:\n            print(f\"   {concept}: {count} lecciones\")\n        \n        # Ejemplos de fechas específicas\n        special_dates = {\n            \"01-01\": \"Año Nuevo\",\n            \"12-25\": \"Navidad\",\n            \"06-21\": \"Solsticio de Verano\",\n            \"09-21\": \"Equinoccio de Otoño\"\n        }\n        \n        print(f\"\\n📅 LECCIONES EN FECHAS ESPECIALES:\")\n        for date_key, occasion in special_dates.items():\n            lesson_num = self.date_mapper.get(date_key)\n            if lesson_num and lesson_num in index_data[\"lesson_details\"]:\n                lesson_title = index_data[\"lesson_details\"][lesson_num]['title']\n                print(f\"   {occasion} ({date_key}): Lección {lesson_num} - {lesson_title[:50]}...\")\n\ndef main():\n    \"\"\"Función principal del indexador\"\"\"\n    indexer = UCDMLessonIndexer()\n    \n    # Crear índice completo\n    comprehensive_index = indexer.create_comprehensive_index()\n    \n    if not comprehensive_index:\n        print(\"❌ Error: No se pudo crear el índice completo\")\n        return 1\n    \n    # Guardar índices\n    indexer.save_comprehensive_index(comprehensive_index)\n    \n    # Mostrar estadísticas\n    metadata = comprehensive_index[\"metadata\"]\n    print(f\"\\n{'='*60}\")\n    print(\"INDEXACIÓN COMPLETA DE LECCIONES UCDM\")\n    print(f\"{'='*60}\")\n    \n    print(f\"\\n📊 ESTADÍSTICAS GENERALES:\")\n    print(f\"   Total de lecciones indexadas: {metadata['total_lessons']}/365\")\n    print(f\"   Cobertura: {metadata['coverage_percentage']:.1f}%\")\n    print(f\"   Conceptos únicos identificados: {metadata['total_concepts']}\")\n    print(f\"   Promedio de conceptos por lección: {metadata['avg_concepts_per_lesson']}\")\n    \n    print(f\"\\n📅 MAPEO DE FECHAS:\")\n    print(f\"   Días del año mapeados: {len(comprehensive_index['date_mapping'])}\")\n    print(f\"   Patrón: 1 enero = Lección 1, 31 diciembre = Lección 365\")\n    \n    print(f\"\\n🔍 ÍNDICE DE CONCEPTOS:\")\n    concept_count = len(comprehensive_index['concept_index'])\n    print(f\"   Conceptos indexados: {concept_count}\")\n    \n    # Demostrar funcionalidad\n    indexer.demonstrate_functionality(comprehensive_index)\n    \n    print(f\"\\n✅ ARCHIVOS GENERADOS:\")\n    print(f\"   - Índice principal: {INDICES_DIR / 'ucdm_comprehensive_index.json'}\")\n    print(f\"   - Mapeo de fechas: {INDICES_DIR / 'lesson_date_mapper.json'}\")\n    print(f\"   - Índice de conceptos: {INDICES_DIR / 'concept_to_lessons_index.json'}\")\n    \n    coverage = metadata['coverage_percentage']\n    print(f\"\\n⭐ ÍNDICE COMPLETADO: {coverage:.1f}% de cobertura\")\n    \n    return 0 if coverage > 40 else 1\n\nif __name__ == \"__main__\":\n    exit(main())