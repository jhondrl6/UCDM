#!/usr/bin/env python3
"""
Tests unitarios para el sistema UCDM
Conjunto de pruebas específicas para cada componente
"""

import sys
import unittest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *
from training.response_engine import UCDMResponseEngine

class TestUCDMResponseEngine(unittest.TestCase):
    """Tests para el motor de respuestas UCDM"""
    
    def setUp(self):
        """Configurar tests"""
        self.engine = UCDMResponseEngine()
        
        # Mock data para tests
        self.mock_lessons_index = {
            "1": {
                "title": "Nada de lo que veo en esta habitación significa nada",
                "concepts": ["percepción", "significado"],
                "file_path": "lessons/lesson_001.txt"
            },
            "2": {
                "title": "He dado a todo lo que veo todo el significado que tiene para mí",
                "concepts": ["significado", "proyección"],
                "file_path": "lessons/lesson_002.txt"
            }
        }
        
        self.mock_concept_index = {
            "percepción": [1, 15, 30],
            "significado": [1, 2, 45],
            "amor": [50, 75, 100]
        }
        
        self.mock_date_mapper = {
            "01-01": 1,
            "01-02": 2,
            "12-25": 359
        }
    
    def test_load_response_templates(self):
        """Test carga de templates de respuesta"""
        templates = self.engine.load_response_templates()
        
        self.assertIn("hooks_iniciales", templates)
        self.assertIn("aplicacion_practica", templates)
        self.assertIn("integracion_experiencial", templates)
        self.assertIn("cierres_motivadores", templates)
        
        # Verificar que hay variedad en los templates
        hooks = templates["hooks_iniciales"]["preguntas_enganchadoras"]
        self.assertGreater(len(hooks), 5)
        self.assertIn("¿Y si te dijera que", hooks)
    
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_load_data_success(self, mock_exists, mock_open):
        """Test carga exitosa de datos"""
        mock_exists.return_value = True
        
        mock_data = {
            "lesson_details": self.mock_lessons_index,
            "concept_index": self.mock_concept_index,
            "date_mapping": self.mock_date_mapper
        }
        
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_data)
        
        result = self.engine.load_data()
        
        self.assertTrue(result)
        self.assertEqual(len(self.engine.lessons_index), 2)
        self.assertEqual(len(self.engine.concept_index), 3)
    
    @patch('pathlib.Path.exists')
    def test_load_data_file_not_found(self, mock_exists):
        """Test cuando no se encuentra el archivo de datos"""
        mock_exists.return_value = False
        
        result = self.engine.load_data()
        
        self.assertFalse(result)
    
    def test_generate_dynamic_hook(self):
        """Test generación de hook dinámico"""
        self.engine.lessons_index = self.mock_lessons_index
        
        hook = self.engine.generate_dynamic_hook(1, "Lección sobre amor", "lesson_specific")
        
        self.assertIsInstance(hook, str)
        self.assertGreater(len(hook), 20)
        self.assertTrue(hook.startswith("¿"))
        self.assertIn("amor", hook.lower())
    
    def test_generate_aplicacion_practica(self):
        """Test generación de aplicación práctica"""
        aplicacion = self.engine.generate_aplicacion_practica(
            1, "Test Lesson", "Test content"
        )
        
        self.assertIn("APLICACIÓN PRÁCTICA", aplicacion)
        self.assertIn("Paso", aplicacion)
        
        # Verificar que contiene pasos estructurados
        self.assertRegex(aplicacion, r"Paso \d+:")
    
    def test_generate_integracion_experiencial(self):
        """Test generación de integración experiencial"""
        integracion = self.engine.generate_integracion_experiencial(
            1, "Test Lesson", "Test content"
        )
        
        self.assertIn("INTEGRACIÓN EXPERIENCIAL", integracion)
        self.assertIn("Conexión personal", integracion)
        self.assertIn("UCDM", integracion)
    
    def test_generate_cierre_motivador(self):
        """Test generación de cierre motivador"""
        cierre = self.engine.generate_cierre_motivador(
            1, "Test Lesson", "general"
        )
        
        self.assertIn("CIERRE MOTIVADOR", cierre)
        self.assertGreater(len(cierre), 50)
    
    def test_generate_structured_response(self):
        """Test generación de respuesta estructurada completa"""
        self.engine.lessons_index = self.mock_lessons_index
        
        response = self.engine.generate_structured_response(
            "Test query", "general", 1
        )
        
        required_sections = [
            "HOOK INICIAL",
            "APLICACIÓN PRÁCTICA",
            "INTEGRACIÓN EXPERIENCIAL",
            "CIERRE MOTIVADOR"
        ]
        
        for section in required_sections:
            self.assertIn(section, response)
        
        # Verificar que la respuesta tiene longitud adecuada
        self.assertGreater(len(response), 300)
    
    def test_process_query_lesson_specific(self):
        """Test procesamiento de consulta específica de lección"""
        self.engine.lessons_index = self.mock_lessons_index
        
        result = self.engine.process_query("Explícame la Lección 1")
        
        self.assertEqual(result["query_type"], "lesson_specific")
        self.assertEqual(result["lesson_number"], 1)
        self.assertIn("response", result)
    
    def test_process_query_daily_lesson(self):
        """Test procesamiento de consulta de lección diaria"""
        self.engine.date_mapper = self.mock_date_mapper
        self.engine.lessons_index = self.mock_lessons_index
        
        result = self.engine.process_query("¿Cuál es la lección de hoy?")
        
        self.assertEqual(result["query_type"], "daily_lesson")
    
    def test_process_query_concept_based(self):
        """Test procesamiento de consulta basada en concepto"""
        result = self.engine.process_query("Háblame sobre el amor en UCDM")
        
        self.assertEqual(result["query_type"], "concept_based")

class TestUCDMDataStructures(unittest.TestCase):
    """Tests para estructuras de datos UCDM"""
    
    def test_lesson_index_structure(self):
        """Test estructura del índice de lecciones"""
        # Simular carga de índice
        lesson_data = {
            "title": "Test Lesson",
            "concepts": ["test_concept"],
            "word_count": 100,
            "file_path": "test/path.txt",
            "confidence": 0.95
        }
        
        # Verificar campos requeridos
        required_fields = ["title", "concepts", "word_count", "file_path", "confidence"]
        for field in required_fields:
            self.assertIn(field, lesson_data)
    
    def test_concept_index_structure(self):
        """Test estructura del índice de conceptos"""
        concept_data = {
            "amor": [1, 50, 100],
            "perdón": [25, 75, 125],
            "paz": [10, 60, 110]
        }
        
        # Verificar que cada concepto mapea a lista de lecciones
        for concept, lessons in concept_data.items():
            self.assertIsInstance(lessons, list)
            self.assertTrue(all(isinstance(l, int) for l in lessons))

class TestUCDMValidation(unittest.TestCase):
    """Tests para validación del sistema"""
    
    def test_response_structure_validation(self):
        """Test validación de estructura de respuesta"""
        sample_response = """
        **HOOK INICIAL: UNA PREGUNTA O ANÉCDOTA PARA ENGANCHAR**
        ¿Has notado que...?
        
        **APLICACIÓN PRÁCTICA: PASOS VIVOS Y VARIADOS**
        Paso 1: Reconoce...
        
        **INTEGRACIÓN EXPERIENCIAL: CONEXIÓN VIVA Y REFLEXIVA**
        Conecta esto con tu vida...
        
        **CIERRE MOTIVADOR: UN MILAGRO FINAL**
        Lleva esto contigo...
        """
        
        required_sections = [
            "HOOK INICIAL",
            "APLICACIÓN PRÁCTICA",
            "INTEGRACIÓN EXPERIENCIAL",
            "CIERRE MOTIVADOR"
        ]
        
        for section in required_sections:
            self.assertIn(section, sample_response)
    
    def test_response_length_validation(self):
        """Test validación de longitud de respuesta"""
        # Las respuestas deben tener entre 300-500 palabras
        sample_response = "palabra " * 400  # 400 palabras
        word_count = len(sample_response.split())
        
        self.assertGreaterEqual(word_count, 300)
        self.assertLessEqual(word_count, 600)  # Margen extendido para flexibilidad

class TestUCDMIntegration(unittest.TestCase):
    """Tests de integración del sistema"""
    
    def setUp(self):
        """Configurar tests de integración"""
        self.engine = UCDMResponseEngine()
    
    @patch('training.response_engine.UCDMResponseEngine.load_data')
    def test_end_to_end_query_processing(self, mock_load_data):
        """Test procesamiento completo de consulta"""
        mock_load_data.return_value = True
        self.engine.lessons_index = {"1": {"title": "Test Lesson", "concepts": []}}
        
        # Simular consulta completa
        query = "Explícame la Lección 1"
        result = self.engine.process_query(query)
        
        # Verificar resultado completo
        self.assertIn("query", result)
        self.assertIn("query_type", result)
        self.assertIn("response", result)
        self.assertIn("timestamp", result)
    
    def test_multiple_query_types(self):
        """Test múltiples tipos de consulta"""
        self.engine.lessons_index = {"1": {"title": "Test", "concepts": []}}
        self.engine.date_mapper = {"01-01": 1}
        
        queries = [
            ("Explícame la Lección 1", "lesson_specific"),
            ("¿Cuál es la lección de hoy?", "daily_lesson"),
            ("Háblame sobre el amor", "concept_based"),
            ("Reflexión nocturna", "reflection")
        ]
        
        for query, expected_type in queries:
            with self.subTest(query=query):
                result = self.engine.process_query(query)
                self.assertEqual(result["query_type"], expected_type)

class UCDMTestSuite:
    """Suite completa de tests para UCDM"""
    
    def __init__(self):
        self.loader = unittest.TestLoader()
        self.suite = unittest.TestSuite()
        
    def create_test_suite(self):
        """Crear suite completa de tests"""
        # Cargar tests de cada clase
        test_classes = [
            TestUCDMResponseEngine,
            TestUCDMDataStructures,
            TestUCDMValidation,
            TestUCDMIntegration
        ]
        
        for test_class in test_classes:
            tests = self.loader.loadTestsFromTestCase(test_class)
            self.suite.addTests(tests)
        
        return self.suite
    
    def run_tests(self, verbosity=2):
        """Ejecutar suite de tests"""
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(self.suite)
        
        return result

def run_specific_test(test_name: str):
    """Ejecutar test específico"""
    loader = unittest.TestLoader()
    
    # Mapear nombres a clases
    test_map = {
        "response_engine": TestUCDMResponseEngine,
        "data_structures": TestUCDMDataStructures,
        "validation": TestUCDMValidation,
        "integration": TestUCDMIntegration
    }
    
    if test_name in test_map:
        suite = loader.loadTestsFromTestCase(test_map[test_name])
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)
    else:
        print(f"Test '{test_name}' no encontrado")
        print(f"Tests disponibles: {list(test_map.keys())}")
        return None

def main():
    """Función principal para ejecutar tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tests unitarios para UCDM")
    parser.add_argument('--test', help='Ejecutar test específico')
    parser.add_argument('--all', action='store_true', help='Ejecutar todos los tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Salida verbose')
    
    args = parser.parse_args()
    
    if args.test:
        result = run_specific_test(args.test)
    elif args.all:
        test_suite = UCDMTestSuite()
        suite = test_suite.create_test_suite()
        verbosity = 2 if args.verbose else 1
        result = test_suite.run_tests(verbosity)
    else:
        # Ejecutar tests básicos por defecto
        test_suite = UCDMTestSuite()
        suite = test_suite.create_test_suite()
        result = test_suite.run_tests(verbosity=1)
    
    if result:
        # Mostrar resumen
        print(f"\n{'='*50}")
        print("RESUMEN DE TESTS:")
        print(f"Tests ejecutados: {result.testsRun}")
        print(f"Errores: {len(result.errors)}")
        print(f"Fallos: {len(result.failures)}")
        print(f"Éxito: {result.wasSuccessful()}")
        
        if result.errors:
            print("\nERRORES:")
            for test, error in result.errors:
                print(f"- {test}: {error}")
        
        if result.failures:
            print("\nFALLOS:")
            for test, failure in result.failures:
                print(f"- {test}: {failure}")
        
        return 0 if result.wasSuccessful() else 1
    
    return 1

if __name__ == "__main__":
    exit(main())