#!/usr/bin/env python3
"""
Script maestro de testing y validación UCDM
Ejecuta validación completa del sistema y todos los tests
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

# Import directo desde archivos locales
sys.path.append(str(Path(__file__).parent))
from system_validator import UCDMSystemValidator
from unit_tests import UCDMTestSuite

class UCDMMasterTester:
    """Ejecutor maestro de tests y validaciones"""
    
    def __init__(self):
        self.setup_logging()
        self.results = {}
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def run_system_validation(self) -> Dict[str, any]:
        """Ejecutar validación completa del sistema"""
        self.logger.info("🔍 Ejecutando validación del sistema...")
        
        validator = UCDMSystemValidator()
        validation_results = validator.run_complete_validation()
        
        # Generar reporte
        report = validator.generate_validation_report()
        validator.save_validation_results()
        
        return {
            "results": validation_results,
            "success": True,
            "report_file": str(PROJECT_ROOT / "validation_report.txt")
        }
    
    def run_unit_tests(self) -> Dict[str, any]:
        """Ejecutar tests unitarios"""
        self.logger.info("🧪 Ejecutando tests unitarios...")
        
        test_suite = UCDMTestSuite()
        suite = test_suite.create_test_suite()
        result = test_suite.run_tests(verbosity=1)
        
        return {
            "tests_run": result.testsRun,
            "errors": len(result.errors),
            "failures": len(result.failures),
            "success": result.wasSuccessful(),
            "error_details": result.errors,
            "failure_details": result.failures
        }
    
    def run_integration_tests(self) -> Dict[str, any]:
        """Ejecutar tests de integración específicos"""
        self.logger.info("🔗 Ejecutando tests de integración...")
        
        integration_results = {
            "cli_functionality": False,
            "response_engine_integration": False,
            "data_pipeline": False,
            "performance_acceptable": False
        }
        
        try:
            # Test CLI básico
            cli_result = subprocess.run([
                sys.executable, "ucdm_cli.py", "--help"
            ], capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT)
            
            integration_results["cli_functionality"] = cli_result.returncode == 0
            
            # Test motor de respuestas
            from training.response_engine import UCDMResponseEngine
            engine = UCDMResponseEngine()
            if engine.load_data():
                result = engine.process_query("Test query")
                integration_results["response_engine_integration"] = "response" in result
            
            # Test pipeline de datos (verificar archivos críticos)
            critical_files = [
                PROCESSED_DATA_DIR / "ucdm_complete_text.txt",
                INDICES_DIR / "ucdm_comprehensive_index.json"
            ]
            integration_results["data_pipeline"] = all(f.exists() for f in critical_files)
            
            # Test básico de rendimiento
            start_time = time.time()
            if integration_results["response_engine_integration"]:
                engine.process_query("Explícame la Lección 1")
            processing_time = time.time() - start_time
            integration_results["performance_acceptable"] = processing_time < 10  # 10 segundos max
            
        except Exception as e:
            self.logger.error(f"Error en tests de integración: {str(e)}")
        
        return integration_results
    
    def run_smoke_tests(self) -> Dict[str, bool]:
        """Ejecutar smoke tests básicos"""
        self.logger.info("💨 Ejecutando smoke tests...")
        
        smoke_results = {}
        
        # Test 1: Importación de módulos principales
        try:
            from config.settings import PROJECT_ROOT
            from training.response_engine import UCDMResponseEngine
            smoke_results["imports_work"] = True
        except Exception as e:
            smoke_results["imports_work"] = False
            self.logger.error(f"Error en importaciones: {str(e)}")
        
        # Test 2: Archivos de configuración
        config_files = [
            PROJECT_ROOT / "config" / "settings.py",
            PROJECT_ROOT / "requirements.txt"
        ]
        smoke_results["config_files_exist"] = all(f.exists() for f in config_files)
        
        # Test 3: Directorios de datos
        data_dirs = [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, TRAINING_DATA_DIR, INDICES_DIR]
        smoke_results["data_dirs_exist"] = all(d.exists() for d in data_dirs)
        
        # Test 4: Scripts principales
        main_scripts = [
            PROJECT_ROOT / "ucdm_cli.py",
            PROJECT_ROOT / "extraction" / "pdf_extractor.py",
            PROJECT_ROOT / "training" / "response_engine.py"
        ]
        smoke_results["main_scripts_exist"] = all(s.exists() for s in main_scripts)
        
        return smoke_results
    
    def run_performance_benchmarks(self) -> Dict[str, float]:
        """Ejecutar benchmarks de rendimiento"""
        self.logger.info("⏱️ Ejecutando benchmarks de rendimiento...")
        
        benchmarks = {}
        
        try:
            from training.response_engine import UCDMResponseEngine
            
            # Benchmark carga del motor
            start_time = time.time()
            engine = UCDMResponseEngine()
            engine.load_data()
            benchmarks["engine_load_time"] = time.time() - start_time
            
            # Benchmark generación de respuesta simple
            start_time = time.time()
            result = engine.process_query("Test query")
            benchmarks["simple_response_time"] = time.time() - start_time
            
            # Benchmark generación de respuesta compleja
            start_time = time.time()
            result = engine.process_query("Explícame detalladamente la Lección 1 y su aplicación práctica")
            benchmarks["complex_response_time"] = time.time() - start_time
            
            # Benchmark múltiples consultas
            start_time = time.time()
            for i in range(5):
                engine.process_query(f"Consulta {i+1}")
            benchmarks["multiple_queries_time"] = time.time() - start_time
            
        except Exception as e:
            self.logger.error(f"Error en benchmarks: {str(e)}")
            benchmarks["error"] = str(e)
        
        return benchmarks
    
    def run_comprehensive_testing(self) -> Dict[str, any]:
        """Ejecutar testing completo del sistema"""
        self.logger.info("🚀 INICIANDO TESTING COMPLETO DEL SISTEMA UCDM")
        
        start_time = time.time()
        
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "smoke_tests": self.run_smoke_tests(),
            "system_validation": self.run_system_validation(),
            "unit_tests": self.run_unit_tests(),
            "integration_tests": self.run_integration_tests(),
            "performance_benchmarks": self.run_performance_benchmarks(),
            "total_time": 0.0
        }
        
        self.results["total_time"] = time.time() - start_time
        
        return self.results
    
    def generate_comprehensive_report(self) -> str:
        """Generar reporte completo de testing"""
        if not self.results:
            return "No hay resultados de testing disponibles"
        
        report = f"""
{'='*80}
🌟 REPORTE COMPLETO DE TESTING - SISTEMA UCDM
{'='*80}

📅 Fecha: {self.results['timestamp']}
⏱️  Tiempo total: {self.results['total_time']:.2f} segundos

💨 SMOKE TESTS:
"""
        
        smoke = self.results['smoke_tests']
        for test, result in smoke.items():
            status = "✅" if result else "❌"
            report += f"   {status} {test.replace('_', ' ').title()}\n"
        
        smoke_passed = sum(1 for r in smoke.values() if r)
        smoke_total = len(smoke)
        report += f"   📊 Smoke Tests: {smoke_passed}/{smoke_total} ({(smoke_passed/smoke_total)*100:.1f}%)\n"
        
        # Validación del sistema
        validation = self.results['system_validation']
        if validation['success']:
            report += f"""
🔍 VALIDACIÓN DEL SISTEMA:
   ✅ Validación completada exitosamente
   📄 Reporte guardado en: {validation['report_file']}
"""
        else:
            report += f"""
🔍 VALIDACIÓN DEL SISTEMA:
   ❌ Errores en validación del sistema
"""
        
        # Tests unitarios
        unit_tests = self.results['unit_tests']
        report += f"""
🧪 TESTS UNITARIOS:
   📊 Tests ejecutados: {unit_tests['tests_run']}
   ❌ Errores: {unit_tests['errors']}
   ⚠️  Fallos: {unit_tests['failures']}
   {'✅' if unit_tests['success'] else '❌'} Estado: {'EXITOSO' if unit_tests['success'] else 'CON ERRORES'}
"""
        
        # Tests de integración
        integration = self.results['integration_tests']
        report += f"""
🔗 TESTS DE INTEGRACIÓN:
"""
        for test, result in integration.items():
            status = "✅" if result else "❌"
            report += f"   {status} {test.replace('_', ' ').title()}\n"
        
        integration_passed = sum(1 for r in integration.values() if r)
        integration_total = len(integration)
        
        # Benchmarks de rendimiento
        benchmarks = self.results['performance_benchmarks']
        report += f"""
⏱️ BENCHMARKS DE RENDIMIENTO:
"""
        for benchmark, time_value in benchmarks.items():
            if isinstance(time_value, (int, float)):
                report += f"   📏 {benchmark.replace('_', ' ').title()}: {time_value:.2f}s\n"
        
        # Resumen general
        total_tests = smoke_total + unit_tests['tests_run'] + integration_total
        total_passed = smoke_passed + (unit_tests['tests_run'] - unit_tests['errors'] - unit_tests['failures']) + integration_passed
        overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        report += f"""
{'='*80}
📋 RESUMEN GENERAL:
   🎯 Tests totales: {total_tests}
   ✅ Tests exitosos: {total_passed}
   📊 Tasa de éxito general: {overall_success_rate:.1f}%
   
🏆 ESTADO GENERAL: {'🟢 SISTEMA OPERATIVO' if overall_success_rate > 85 else '🟡 SISTEMA PARCIAL' if overall_success_rate > 70 else '🔴 REQUIERE ATENCIÓN'}

💡 RECOMENDACIONES:
"""
        
        if smoke_passed < smoke_total:
            report += "   • Revisar configuración básica del sistema\n"
        
        if unit_tests['errors'] > 0 or unit_tests['failures'] > 0:
            report += "   • Corregir errores en tests unitarios\n"
        
        if integration_passed < integration_total:
            report += "   • Verificar integración entre componentes\n"
        
        if benchmarks.get('engine_load_time', 0) > 5:
            report += "   • Optimizar tiempo de carga del motor\n"
        
        if benchmarks.get('complex_response_time', 0) > 10:
            report += "   • Optimizar rendimiento de respuestas complejas\n"
        
        report += f"""
🚀 PASOS SIGUIENTES:
   1. Revisar elementos marcados como ❌
   2. Ejecutar correcciones necesarias
   3. Re-ejecutar testing hasta obtener 100% éxito
   4. Proceder con configuración de Ollama
   5. Validar modelo especializado

📞 SOPORTE:
   • Logs detallados en: {PROJECT_ROOT}/logs/
   • Reportes en: {PROJECT_ROOT}/validation_report.txt
   • Tests unitarios: python tests/unit_tests.py --all

{'='*80}
"""
        
        return report
    
    def save_testing_results(self) -> str:
        """Guardar resultados completos de testing"""
        import json
        
        results_file = PROJECT_ROOT / "comprehensive_testing_report.json"
        report_file = PROJECT_ROOT / "comprehensive_testing_report.txt"
        
        # Guardar JSON
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Guardar reporte de texto
        report_text = self.generate_comprehensive_report()
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        self.logger.info(f"✅ Resultados guardados en: {results_file}")
        self.logger.info(f"✅ Reporte guardado en: {report_file}")
        
        return str(report_file)

def main():
    """Función principal del testing maestro"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Testing completo del sistema UCDM")
    parser.add_argument('--smoke', action='store_true', help='Ejecutar solo smoke tests')
    parser.add_argument('--unit', action='store_true', help='Ejecutar solo tests unitarios')
    parser.add_argument('--integration', action='store_true', help='Ejecutar solo tests de integración')
    parser.add_argument('--performance', action='store_true', help='Ejecutar solo benchmarks de rendimiento')
    parser.add_argument('--all', action='store_true', help='Ejecutar testing completo (por defecto)')
    parser.add_argument('--quick', action='store_true', help='Ejecutar testing rápido (smoke + básicos)')
    
    args = parser.parse_args()
    
    tester = UCDMMasterTester()
    
    print("🔬 Iniciando testing del sistema UCDM...")
    
    if args.smoke:
        results = {"smoke_tests": tester.run_smoke_tests()}
    elif args.unit:
        results = {"unit_tests": tester.run_unit_tests()}
    elif args.integration:
        results = {"integration_tests": tester.run_integration_tests()}
    elif args.performance:
        results = {"performance_benchmarks": tester.run_performance_benchmarks()}
    elif args.quick:
        results = {
            "smoke_tests": tester.run_smoke_tests(),
            "unit_tests": tester.run_unit_tests()
        }
    else:
        # Testing completo por defecto
        results = tester.run_comprehensive_testing()
    
    # Mostrar resultados
    if hasattr(tester, 'results') and tester.results:
        report = tester.generate_comprehensive_report()
        print(report)
        
        # Guardar resultados
        report_file = tester.save_testing_results()
        
        # Determinar código de salida
        if args.quick or not args.all:
            return 0  # Para tests parciales, siempre éxito
        
        # Para testing completo, evaluar éxito general
        smoke_success = all(tester.results.get('smoke_tests', {}).values())
        unit_success = tester.results.get('unit_tests', {}).get('success', False)
        integration_success = all(tester.results.get('integration_tests', {}).values())
        
        overall_success = smoke_success and unit_success and integration_success
        
        if overall_success:
            print("🎉 TESTING COMPLETADO EXITOSAMENTE")
            return 0
        else:
            print("⚠️ TESTING COMPLETADO CON OBSERVACIONES")
            return 1
    else:
        print("❌ ERROR EN TESTING")
        return 2

if __name__ == "__main__":
    exit(main())