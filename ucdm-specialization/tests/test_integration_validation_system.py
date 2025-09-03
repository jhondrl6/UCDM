#!/usr/bin/env python3
"""
Tests de integración para el Sistema Completo de Validación UCDM
Pruebas end-to-end del sistema integrado
"""

import sys
import json
import unittest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))

from validation.comprehensive_validation_pipeline import ComprehensiveValidationPipeline, PipelineConfig
from ucdm_cli import UCDMCLIInterface

class TestIntegrationValidationSystem(unittest.TestCase):
    """Tests de integración completa del sistema de validación"""
    
    def setUp(self):
        """Configurar entorno de pruebas integradas"""
        # Configurar pipeline completo
        self.config = PipelineConfig(
            enable_text_validation=True,
            enable_lesson_recognition=True,
            enable_structure_validation=True,
            enable_report_generation=True,
            parallel_processing=False
        )
        self.pipeline = ComprehensiveValidationPipeline(self.config)
        
        # CLI para tests de interfaz
        self.cli = UCDMCLIInterface()
        
        # Datos de prueba realistas
        self.sample_lesson_content = """
        Lección 15: Mis pensamientos son imágenes que he fabricado.
        
        Es porque los pensamientos que piensas que piensas aparecen como imágenes que no 
        reconoces su origen. No te das cuenta de que los fabricaste. No te das cuenta de 
        que las imágenes que ves fueron evocadas por ti mismo. 
        
        Esta lección de hoy te ayudará a empezar a reconocer que puedes ser el soñador de 
        tu sueño, y no una figura del sueño. Es posible vivir felizmente en un sueño mientras 
        estás soñando.
        
        Practica esta idea cada hora durante cinco minutos. Examina tu mente en busca de 
        pensamientos, sin hacer distinciones entre ellos. Aplica la idea de hoy por igual 
        a cada uno de ellos.
        """
        
        self.complete_ucdm_response = """
        🎯 HOOK INICIAL:
        ¿Te has preguntado alguna vez por qué tu mente parece estar constantemente creando 
        escenarios y situaciones que luego experimentas como reales? La respuesta está en 
        el poder creativo de tus pensamientos.
        
        ⚡ APLICACIÓN PRÁCTICA:
        Paso 1: Durante los próximos cinco minutos, observa tus pensamientos sin juzgarlos. 
        Simplemente nota cada pensamiento que surge y reconoce: "Este pensamiento es una imagen 
        que yo he fabricado".
        
        Paso 2: Cuando te encuentres reaccionando emocionalmente a alguna situación durante el día, 
        pausa y pregúntate: "¿Qué imagen mental estoy creando ahora que me hace sentir así?"
        
        Paso 3: Antes de dormir, revisa tu día y identifica tres momentos donde reconozcas que 
        tus pensamientos crearon la experiencia que tuviste, no los eventos externos.
        
        🌿 INTEGRACIÓN EXPERIENCIAL:
        Conecta esto con tu vida: piensa en una preocupación recurrente que tengas. UCDM nos 
        enseña que "los pensamientos que piensas que piensas aparecen como imágenes que no 
        reconoces su origen". ¿Puedes ver cómo esta preocupación es realmente una imagen mental 
        que tú mismo has creado? ¿Sientes la libertad que viene de reconocer que tú eres el 
        creador, no la víctima, de tus experiencias?
        
        ✨ CIERRE MOTIVADOR:
        Hoy puedes ser el soñador de tu sueño, no una figura dentro del sueño. Observa cómo 
        esta comprensión transforma tu día y comparte esta luz con todos los que encuentres.
        """
    
    def test_complete_lesson_processing_workflow(self):
        """Test completo del flujo de procesamiento de lecciones"""
        print("\n🔄 Testing complete lesson processing workflow...")
        
        # 1. Validar calidad del texto de la lección
        text_validation = self.pipeline.validate_text_content(
            self.sample_lesson_content, 
            "lesson_15"
        )
        
        self.assertTrue(text_validation["success"], "Text validation should succeed")
        self.assertIn("assessment", text_validation)
        
        # 2. Validar reconocimiento de estructura de lecciones
        lesson_validation = self.pipeline.validate_lesson_structure(
            self.sample_lesson_content
        )
        
        self.assertTrue(lesson_validation["success"], "Lesson structure validation should succeed")
        
        # 3. Ejecutar pipeline completo
        complete_validation = self.pipeline.run_complete_validation(
            self.sample_lesson_content,
            {"15": {"title": "Lección 15", "word_count": 200, "char_count": 1200}},
            "lesson_15_complete"
        )
        
        self.assertIsNotNone(complete_validation)
        self.assertTrue(complete_validation.success, "Complete validation should succeed")
        self.assertIsNotNone(complete_validation.overall_summary)
        
        print(f"✅ Workflow completed successfully - Quality Score: {complete_validation.overall_summary.get('overall_quality_score', 0):.1f}%")
    
    def test_response_structure_validation_workflow(self):
        """Test completo del flujo de validación de estructura de respuestas"""
        print("\n📝 Testing response structure validation workflow...")
        
        # 1. Validar formato de respuesta completa
        response_validation = self.pipeline.validate_response_format(
            self.complete_ucdm_response,
            "¿Cómo puedo entender mejor mis pensamientos?",
            "integration_test_response"
        )
        
        self.assertTrue(response_validation["success"], "Response validation should succeed")
        self.assertIn("validation_report", response_validation)
        
        validation_report = response_validation["validation_report"]
        
        # 2. Verificar que todas las secciones están presentes
        structure_validation = validation_report["structure_validation"]
        self.assertTrue(structure_validation["has_all_sections"], "All sections should be present")
        self.assertEqual(len(structure_validation["missing_sections"]), 0, "No sections should be missing")
        
        # 3. Verificar cumplimiento de longitud
        content_validation = validation_report["content_validation"]
        self.assertTrue(content_validation["length_valid"], "Response length should be valid")
        self.assertGreaterEqual(content_validation["word_count"], 300, "Should meet minimum word count")
        self.assertLessEqual(content_validation["word_count"], 500, "Should not exceed maximum word count")
        
        # 4. Verificar coherencia temática
        self.assertGreaterEqual(content_validation["thematic_coherence"], 80.0, "Should have good thematic coherence")
        
        # 5. Verificar puntuación general
        self.assertGreaterEqual(validation_report["overall_score"], 90.0, "Should have excellent overall score")
        self.assertIn(validation_report["compliance_status"], ["EXCELENTE", "BUENO"], "Should have good compliance")
        
        print(f"✅ Response validation completed - Score: {validation_report['overall_score']:.1f}% ({validation_report['compliance_status']})")
    
    def test_quality_report_generation_workflow(self):
        """Test completo del flujo de generación de reportes"""
        print("\n📊 Testing quality report generation workflow...")
        
        # 1. Generar reporte de salud del sistema
        health_report = self.pipeline.generate_system_health_report()
        
        self.assertIsNotNone(health_report)
        self.assertIn("report_metadata", health_report)
        self.assertIn("system_dashboard", health_report)
        
        # 2. Verificar estructura del dashboard
        dashboard = health_report["system_dashboard"]
        self.assertIn("title", dashboard)
        self.assertIn("status", dashboard)
        self.assertIn("sections", dashboard)
        
        sections = dashboard["sections"]
        required_sections = ["system_overview", "quality_metrics", "processing_status", "alerts"]
        for section in required_sections:
            self.assertIn(section, sections, f"Dashboard should contain {section} section")
        
        # 3. Verificar reporte de calidad
        if "quality_analysis" in health_report:
            quality_analysis = health_report["quality_analysis"]
            self.assertIn("executive_summary", quality_analysis)
            
        print(f"✅ Report generation completed - System Status: {dashboard.get('status', 'UNKNOWN')}")
    
    def test_missing_lessons_processing_workflow(self):
        """Test completo del flujo de procesamiento de lecciones faltantes"""
        print("\n🔧 Testing missing lessons processing workflow...")
        
        # 1. Simular identificación de lecciones faltantes
        missing_lessons = [1, 2, 5, 10, 15, 25, 50, 100, 200, 365]
        
        # 2. Procesar lecciones faltantes
        processing_result = self.pipeline.process_missing_lessons(missing_lessons)
        
        self.assertIsNotNone(processing_result)
        self.assertIn("total_requested", processing_result)
        self.assertIn("successfully_processed", processing_result)
        self.assertIn("failed_processing", processing_result)
        self.assertIn("processing_details", processing_result)
        
        # 3. Verificar que se procesaron todas las solicitadas
        self.assertEqual(processing_result["total_requested"], len(missing_lessons))
        
        # 4. Calcular tasa de éxito
        total_processed = processing_result["successfully_processed"] + processing_result["failed_processing"]
        self.assertEqual(total_processed, len(missing_lessons), "All lessons should be accounted for")
        
        success_rate = (processing_result["successfully_processed"] / len(missing_lessons)) * 100
        print(f"✅ Missing lessons processing completed - Success Rate: {success_rate:.1f}%")
    
    @patch('ucdm_cli.UCDMCLIInterface._initialize_validation_components')
    def test_cli_validation_commands_integration(self, mock_init):
        """Test de integración de comandos CLI de validación"""
        print("\n💻 Testing CLI validation commands integration...")
        
        # Mock the validation components initialization
        mock_init.return_value = None
        self.cli.validation_pipeline = self.pipeline
        self.cli.report_manager = self.pipeline.report_manager
        
        # Test validate command
        try:
            self.cli.cmd_validate(["--all"])
            print("✅ CLI validate command executed successfully")
        except Exception as e:
            self.fail(f"CLI validate command failed: {e}")
        
        # Test complete command  
        try:
            self.cli.cmd_complete(["--missing"])
            print("✅ CLI complete command executed successfully")
        except Exception as e:
            self.fail(f"CLI complete command failed: {e}")
        
        # Test report command
        try:
            self.cli.cmd_report(["--quality"])
            print("✅ CLI report command executed successfully")
        except Exception as e:
            self.fail(f"CLI report command failed: {e}")
        
        # Test metrics command
        try:
            self.cli.cmd_metrics(["--dashboard"])
            print("✅ CLI metrics command executed successfully")
        except Exception as e:
            self.fail(f"CLI metrics command failed: {e}")
    
    def test_error_handling_and_recovery(self):
        """Test de manejo de errores y recuperación del sistema"""
        print("\n🛡️ Testing error handling and recovery...")
        
        # 1. Test con texto corrupto
        corrupted_text = "LecciÃ³n corruptÃ¡ con caracteres malÃ³s y cortÃ©s abruptÃ³s en mitad de"
        
        text_validation = self.pipeline.validate_text_content(corrupted_text, "corrupted_test")
        self.assertIsNotNone(text_validation)
        # El sistema debe manejar texto corrupto sin fallar
        
        # 2. Test con respuesta malformada
        malformed_response = "Esta respuesta no tiene estructura ni secciones válidas."
        
        response_validation = self.pipeline.validate_response_format(
            malformed_response,
            "Test query",
            "malformed_test"
        )
        self.assertIsNotNone(response_validation)
        # Debe detectar y reportar problemas estructurales
        
        # 3. Test con datos vacíos
        empty_validation = self.pipeline.validate_text_content("", "empty_test")
        self.assertIsNotNone(empty_validation)
        
        print("✅ Error handling tests completed successfully")
    
    def test_performance_and_scalability(self):
        """Test de rendimiento y escalabilidad básica"""
        print("\n⚡ Testing performance and scalability...")
        
        # 1. Medir tiempo de procesamiento de múltiples validaciones
        start_time = datetime.now()
        
        for i in range(5):  # Procesar 5 validaciones
            result = self.pipeline.validate_text_content(
                self.sample_lesson_content,
                f"performance_test_{i}"
            )
            self.assertTrue(result["success"], f"Validation {i} should succeed")
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        avg_time_per_validation = total_time / 5
        
        # 2. Verificar que el tiempo promedio es razonable (< 10 segundos por validación)
        self.assertLess(avg_time_per_validation, 10.0, "Average validation time should be reasonable")
        
        print(f"✅ Performance test completed - Avg time per validation: {avg_time_per_validation:.2f}s")
    
    def test_data_consistency_and_integrity(self):
        """Test de consistencia e integridad de datos"""
        print("\n🔒 Testing data consistency and integrity...")
        
        # 1. Ejecutar múltiples validaciones del mismo contenido
        results = []
        for i in range(3):
            result = self.pipeline.validate_text_content(
                self.sample_lesson_content,
                f"consistency_test_{i}"
            )
            results.append(result)
        
        # 2. Verificar que los resultados son consistentes
        if len(results) > 1:
            first_assessment = results[0].get("assessment", {})
            for result in results[1:]:
                current_assessment = result.get("assessment", {})
                # Los puntajes de calidad deben ser idénticos para el mismo contenido
                if "overall_score" in first_assessment and "overall_score" in current_assessment:
                    self.assertEqual(
                        first_assessment["overall_score"],
                        current_assessment["overall_score"],
                        "Quality scores should be consistent for identical content"
                    )
        
        print("✅ Data consistency test completed successfully")
    
    def test_comprehensive_system_validation(self):
        """Test integral que valida todo el sistema funcionando en conjunto"""
        print("\n🎯 Running comprehensive system validation...")
        
        # Simular un flujo completo de validación del sistema
        test_lessons = {
            "1": {"title": "Lección 1", "word_count": 400, "char_count": 2000},
            "15": {"title": "Lección 15", "word_count": 350, "char_count": 1800},
            "100": {"title": "Lección 100", "word_count": 450, "char_count": 2300}
        }
        
        # 1. Validación completa del pipeline
        complete_result = self.pipeline.run_complete_validation(
            self.sample_lesson_content,
            test_lessons,
            "comprehensive_test"
        )
        
        self.assertIsNotNone(complete_result)
        self.assertIsNotNone(complete_result.overall_summary)
        
        # 2. Validación de respuesta estructurada
        response_result = self.pipeline.validate_response_format(
            self.complete_ucdm_response,
            "Test comprehensive query",
            "comprehensive_response_test"
        )
        
        self.assertTrue(response_result["success"])
        
        # 3. Generación de reporte de salud
        health_report = self.pipeline.generate_system_health_report()
        self.assertIsNotNone(health_report)
        
        # 4. Verificar que todos los componentes funcionan juntos
        overall_score = complete_result.overall_summary.get("overall_quality_score", 0)
        self.assertGreaterEqual(overall_score, 50.0, "System should achieve reasonable overall quality")
        
        print(f"✅ Comprehensive system validation completed - Overall Score: {overall_score:.1f}%")
        print(f"📊 System Status: {health_report.get('system_dashboard', {}).get('status', 'UNKNOWN')}")


class TestSystemIntegrationWithRealData(unittest.TestCase):
    """Tests de integración con datos más realistas del sistema"""
    
    def setUp(self):
        """Configurar con datos de prueba más realistas"""
        self.config = PipelineConfig()
        self.pipeline = ComprehensiveValidationPipeline(self.config)
        
        # Simular datos de lecciones más realistas
        self.realistic_lesson_data = {
            str(i): {
                "title": f"Lección {i}",
                "word_count": 300 + (i * 5),  # Variación realista
                "char_count": (300 + (i * 5)) * 5,
                "file_path": f"lessons/lesson_{i:03d}.txt"
            }
            for i in range(1, 116)  # Primeras 115 lecciones como en el sistema actual
        }
    
    def test_realistic_coverage_analysis(self):
        """Test de análisis de cobertura con datos realistas"""
        print("\n📈 Testing realistic coverage analysis...")
        
        # Ejecutar análisis con los datos realistas
        lesson_validation = self.pipeline.validate_lesson_structure(
            "Texto simulado con múltiples lecciones...",
            self.realistic_lesson_data
        )
        
        self.assertTrue(lesson_validation["success"])
        
        # Verificar análisis de cobertura
        if "recognition_report" in lesson_validation:
            coverage_analysis = lesson_validation["recognition_report"].get("coverage_analysis", {})
            coverage_percentage = coverage_analysis.get("coverage_percentage", 0)
            
            # Con 115 lecciones de 365, esperamos ~31.5% de cobertura
            expected_coverage = (115 / 365) * 100
            self.assertAlmostEqual(coverage_percentage, expected_coverage, delta=5.0)
            
            print(f"✅ Coverage analysis completed - Coverage: {coverage_percentage:.1f}%")
    
    def test_realistic_quality_assessment(self):
        """Test de evaluación de calidad con datos realistas"""
        print("\n🔍 Testing realistic quality assessment...")
        
        # Simular contenido con calidad variable
        mixed_quality_content = """
        Lección 1: Nada de lo que veo en esta habitación significa nada.
        
        Esta lección es fundamental. Los milagros ocurren naturalmente.
        
        LecciÃ³n 2: Texto con problemas de codificaciÃ³n
        
        Lección 3: Contenido cortado en mitad de
        """
        
        validation_result = self.pipeline.validate_text_content(
            mixed_quality_content,
            "mixed_quality_test"
        )
        
        self.assertTrue(validation_result["success"])
        
        # El sistema debe detectar y reportar problemas de calidad
        assessment = validation_result.get("assessment", {})
        overall_score = assessment.get("overall_score", 100)
        
        # Con problemas de codificación y cortes, la puntuación debe ser menor a 100
        self.assertLess(overall_score, 100.0, "Should detect quality issues")
        
        print(f"✅ Quality assessment completed - Score: {overall_score:.1f}%")


if __name__ == '__main__':
    # Configurar y ejecutar tests de integración
    print("🚀 Starting UCDM Validation System Integration Tests...")
    print("=" * 70)
    
    # Ejecutar con verbosidad alta para mostrar progreso
    unittest.main(verbosity=2, exit=False)
    
    print("=" * 70)
    print("✅ All integration tests completed!")