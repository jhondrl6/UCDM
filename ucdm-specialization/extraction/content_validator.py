#!/usr/bin/env python3
"""
Validador de integridad de contenido UCDM
Verifica que la extracción sea completa y precisa
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import Counter

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

class UCDMContentValidator:
    """Validador especializado para contenido de UCDM"""
    
    def __init__(self, text_content: str):
        self.content = text_content
        self.validation_results = {}
        
    def validate_lessons_completeness(self) -> Dict[str, any]:
        """Validar que las 365 lecciones estén completas"""
        # Buscar patrones de lecciones
        lesson_patterns = [
            r"Lección\s+(\d{1,3})",
            r"LECCIÓN\s+(\d{1,3})",
            r"Leccion\s+(\d{1,3})"  # Sin tilde
        ]
        
        found_lessons = set()
        lesson_details = []
        
        for pattern in lesson_patterns:
            matches = re.finditer(pattern, self.content, re.IGNORECASE)
            for match in matches:
                lesson_num = int(match.group(1))
                if 1 <= lesson_num <= 365:
                    found_lessons.add(lesson_num)
                    
                    # Extraer contexto alrededor de la lección
                    start = max(0, match.start() - 100)
                    end = min(len(self.content), match.end() + 200)
                    context = self.content[start:end].strip()
                    
                    lesson_details.append({
                        "number": lesson_num,
                        "position": match.start(),
                        "context": context[:100] + "..." if len(context) > 100 else context
                    })
        
        # Identificar lecciones faltantes
        all_lessons = set(range(1, 366))
        missing_lessons = sorted(all_lessons - found_lessons)
        
        return {
            "total_found": len(found_lessons),
            "found_lessons": sorted(found_lessons),
            "missing_lessons": missing_lessons,
            "lesson_details": lesson_details,
            "completeness_percentage": (len(found_lessons) / 365) * 100
        }
    
    def validate_chapters_structure(self) -> Dict[str, any]:
        """Validar estructura de capítulos del Texto Principal"""
        chapter_patterns = [
            r"Capítulo\s+(\d{1,2})",
            r"CAPÍTULO\s+(\d{1,2})",
            r"Capitulo\s+(\d{1,2})"  # Sin tilde
        ]
        
        found_chapters = set()
        chapter_details = []
        
        for pattern in chapter_patterns:
            matches = re.finditer(pattern, self.content, re.IGNORECASE)
            for match in matches:
                chapter_num = int(match.group(1))
                if 1 <= chapter_num <= 31:
                    found_chapters.add(chapter_num)
                    
                    # Extraer título del capítulo
                    start = match.end()
                    end = min(len(self.content), start + 200)
                    title_text = self.content[start:end]
                    
                    # Buscar el título (generalmente en la siguiente línea)
                    title_match = re.search(r'\n\s*([^\n]+)', title_text)
                    title = title_match.group(1).strip() if title_match else "Título no encontrado"
                    
                    chapter_details.append({
                        "number": chapter_num,
                        "title": title,
                        "position": match.start()
                    })
        
        missing_chapters = sorted(set(range(1, 32)) - found_chapters)
        
        return {
            "total_found": len(found_chapters),
            "found_chapters": sorted(found_chapters),
            "missing_chapters": missing_chapters,
            "chapter_details": chapter_details,
            "completeness_percentage": (len(found_chapters) / 31) * 100
        }
    
    def validate_key_sections(self) -> Dict[str, any]:
        """Validar presencia de secciones clave de UCDM"""
        key_sections = {
            "Introducción": [
                r"Introducción",
                r"INTRODUCCIÓN",
                r"Este\s+es\s+un\s+curso\s+de\s+milagros"
            ],
            "Texto Principal": [
                r"TEXTO\s+PRINCIPAL",
                r"Texto\s+Principal",
                r"PRIMERA\s+PARTE"
            ],
            "Libro de Ejercicios": [
                r"LIBRO\s+DE\s+EJERCICIOS",
                r"Libro\s+de\s+Ejercicios",
                r"SEGUNDA\s+PARTE"
            ],
            "Manual del Maestro": [
                r"MANUAL\s+PARA\s+EL\s+MAESTRO",
                r"Manual\s+del\s+Maestro",
                r"TERCERA\s+PARTE"
            ],
            "Clarificación de Términos": [
                r"CLARIFICACIÓN\s+DE\s+TÉRMINOS",
                r"Clarificación\s+de\s+Términos",
                r"CUARTA\s+PARTE"
            ]
        }
        
        section_results = {}
        
        for section_name, patterns in key_sections.items():
            found = False
            position = -1
            matched_pattern = None
            
            for pattern in patterns:
                match = re.search(pattern, self.content, re.IGNORECASE)
                if match:
                    found = True
                    position = match.start()
                    matched_pattern = pattern
                    break
            
            section_results[section_name] = {
                "found": found,
                "position": position,
                "pattern_matched": matched_pattern
            }
        
        return section_results
    
    def validate_key_concepts(self) -> Dict[str, any]:
        """Validar presencia de conceptos clave de UCDM"""
        key_concepts = {
            "milagro": [r"\bmilagro\b", r"\bmilagros\b"],
            "perdón": [r"\bperdón\b", r"\bperdonar\b", r"\bperdonas\b"],
            "ego": [r"\bego\b"],
            "Espíritu Santo": [r"Espíritu\s+Santo", r"ESPÍRITU\s+SANTO"],
            "Dios": [r"\bDios\b"],
            "Cristo": [r"\bCristo\b"],
            "Amor": [r"\bAmor\b"],
            "miedo": [r"\bmiedo\b", r"\bmiedos\b"],
            "culpa": [r"\bculpa\b", r"\bculpas\b"],
            "proyección": [r"\bproyección\b", r"\bproyectar\b"],
            "salvación": [r"\bsalvación\b"],
            "expiación": [r"\bexpiación\b"]
        }
        
        concept_results = {}
        
        for concept, patterns in key_concepts.items():
            total_occurrences = 0
            for pattern in patterns:
                matches = re.findall(pattern, self.content, re.IGNORECASE)
                total_occurrences += len(matches)
            
            concept_results[concept] = {
                "occurrences": total_occurrences,
                "found": total_occurrences > 0
            }
        
        return concept_results
    
    def generate_integrity_report(self) -> Dict[str, any]:
        """Generar reporte completo de integridad"""
        print("Validando integridad del contenido UCDM...")
        
        # Validaciones específicas
        lessons_validation = self.validate_lessons_completeness()
        chapters_validation = self.validate_chapters_structure()
        sections_validation = self.validate_key_sections()
        concepts_validation = self.validate_key_concepts()
        
        # Estadísticas generales
        total_chars = len(self.content)
        total_words = len(self.content.split())
        total_lines = len(self.content.split('\n'))
        
        # Calcular score de integridad global
        integrity_score = 0.0
        
        # Lecciones (40%)
        lessons_score = (lessons_validation["completeness_percentage"] / 100) * 0.4
        integrity_score += lessons_score
        
        # Capítulos (25%)
        chapters_score = (chapters_validation["completeness_percentage"] / 100) * 0.25
        integrity_score += chapters_score
        
        # Secciones clave (20%)
        sections_found = sum(1 for s in sections_validation.values() if s["found"])
        sections_score = (sections_found / len(sections_validation)) * 0.2
        integrity_score += sections_score
        
        # Conceptos clave (15%)
        concepts_found = sum(1 for c in concepts_validation.values() if c["found"])
        concepts_score = (concepts_found / len(concepts_validation)) * 0.15
        integrity_score += concepts_score
        
        # Compilar reporte final
        report = {
            "validation_timestamp": str(datetime.now()),
            "general_stats": {
                "total_characters": total_chars,
                "total_words": total_words,
                "total_lines": total_lines
            },
            "lessons_validation": lessons_validation,
            "chapters_validation": chapters_validation,
            "sections_validation": sections_validation,
            "concepts_validation": concepts_validation,
            "integrity_score": integrity_score,
            "overall_status": "COMPLETO" if integrity_score > 0.85 else "INCOMPLETO",
            "recommendations": []
        }
        
        # Generar recomendaciones
        if lessons_validation["completeness_percentage"] < 95:
            report["recommendations"].append(
                f"Faltan {len(lessons_validation['missing_lessons'])} lecciones del Libro de Ejercicios"
            )
        
        if chapters_validation["completeness_percentage"] < 90:
            report["recommendations"].append(
                f"Faltan {len(chapters_validation['missing_chapters'])} capítulos del Texto Principal"
            )
        
        missing_sections = [name for name, data in sections_validation.items() if not data["found"]]
        if missing_sections:
            report["recommendations"].append(
                f"Secciones faltantes: {', '.join(missing_sections)}"
            )
        
        return report

def main():
    """Función principal para validación"""
    # Cargar contenido extraído
    text_file = PROCESSED_DATA_DIR / "ucdm_complete_text.txt"
    
    if not text_file.exists():
        print("❌ Error: No se encontró el archivo de texto extraído")
        print(f"   Ejecuta primero: python extraction/pdf_extractor.py")
        return 1
    
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ejecutar validación
    validator = UCDMContentValidator(content)
    report = validator.generate_integrity_report()
    
    # Guardar reporte
    report_file = PROCESSED_DATA_DIR / "integrity_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Mostrar resultados
    print(f"\n{'='*60}")
    print("REPORTE DE INTEGRIDAD - UN CURSO DE MILAGROS")
    print(f"{'='*60}")
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   Caracteres: {report['general_stats']['total_characters']:,}")
    print(f"   Palabras: {report['general_stats']['total_words']:,}")
    print(f"   Líneas: {report['general_stats']['total_lines']:,}")
    
    print(f"\n📖 LIBRO DE EJERCICIOS:")
    lessons = report['lessons_validation']
    print(f"   Lecciones encontradas: {lessons['total_found']}/365 ({lessons['completeness_percentage']:.1f}%)")
    if lessons['missing_lessons']:
        print(f"   Lecciones faltantes: {lessons['missing_lessons'][:10]}..." if len(lessons['missing_lessons']) > 10 else f"   Lecciones faltantes: {lessons['missing_lessons']}")
    
    print(f"\n📚 TEXTO PRINCIPAL:")
    chapters = report['chapters_validation']
    print(f"   Capítulos encontrados: {chapters['total_found']}/31 ({chapters['completeness_percentage']:.1f}%)")
    if chapters['missing_chapters']:
        print(f"   Capítulos faltantes: {chapters['missing_chapters']}")
    
    print(f"\n📋 SECCIONES PRINCIPALES:")
    for section, data in report['sections_validation'].items():
        status = "✓" if data['found'] else "✗"
        print(f"   {status} {section}")
    
    print(f"\n🎯 CONCEPTOS CLAVE:")
    concepts = report['concepts_validation']
    found_concepts = sum(1 for c in concepts.values() if c['found'])
    print(f"   Conceptos encontrados: {found_concepts}/{len(concepts)}")
    
    print(f"\n⭐ PUNTUACIÓN DE INTEGRIDAD: {report['integrity_score']:.2f}/1.0")
    print(f"📋 ESTADO: {report['overall_status']}")
    
    if report['recommendations']:
        print(f"\n⚠️  RECOMENDACIONES:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    print(f"\n📄 Reporte completo guardado en: {report_file}")
    
    return 0 if report['integrity_score'] > 0.8 else 1

if __name__ == "__main__":
    from datetime import datetime
    exit(main())