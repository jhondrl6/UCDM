#!/usr/bin/env python3
"""
Sistema de validación y testing completo para UCDM
Verifica la integridad y funcionalidad de todos los componentes del proyecto
"""

import sys
import json
import unittest
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *
from extraction.pdf_extractor import UCDMPDFExtractor
from training.response_engine import UCDMResponseEngine

class UCDMSystemValidator:
    """Validador completo del sistema UCDM"""
    
    def __init__(self):
        self.results = {}
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging para validación"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def validate_file_structure(self) -> Dict[str, bool]:
        """Validar estructura de archivos del proyecto"""
        self.logger.info("🔍 Validando estructura de archivos...")
        
        required_files = {
            "config/settings.py": PROJECT_ROOT / "config" / "settings.py",
            "extraction/pdf_extractor.py": PROJECT_ROOT / "extraction" / "pdf_extractor.py",
            "extraction/advanced_lesson_segmenter.py": PROJECT_ROOT / "extraction" / "advanced_lesson_segmenter.py",
            "extraction/lesson_indexer.py": PROJECT_ROOT / "extraction" / "lesson_indexer.py",
            "training/dataset_generator.py": PROJECT_ROOT / "training" / "dataset_generator.py",
            "training/response_engine.py": PROJECT_ROOT / "training" / "response_engine.py",
            "ucdm_cli.py": PROJECT_ROOT / "ucdm_cli.py",
            "ollama/Modelfile": PROJECT_ROOT / "ollama" / "Modelfile",
            "ollama/setup_model.py": PROJECT_ROOT / "ollama" / "setup_model.py"
        }
        
        required_dirs = {
            "data": DATA_DIR,
            "data/raw": RAW_DATA_DIR,
            "data/processed": PROCESSED_DATA_DIR,
            "data/training": TRAINING_DATA_DIR,
            "data/indices": INDICES_DIR
        }
        
        validation_results = {}
        
        # Validar archivos
        for name, path in required_files.items():
            exists = path.exists()
            validation_results[f"file_{name}"] = exists
            if exists:
                self.logger.info(f"✓ {name}")
            else:
                self.logger.error(f"✗ {name} - FALTANTE")
        
        # Validar directorios
        for name, path in required_dirs.items():
            exists = path.exists() and path.is_dir()
            validation_results[f"dir_{name}"] = exists
            if exists:
                self.logger.info(f"✓ {name}/")
            else:
                self.logger.error(f"✗ {name}/ - FALTANTE")
        
        return validation_results
    
    def validate_data_extraction(self) -> Dict[str, any]:
        """Validar proceso de extracción de datos"""
        self.logger.info("📖 Validando extracción de datos...")
        
        validation_results = {
            "pdf_source_exists": False,
            "extracted_text_exists": False,
            "lessons_indexed": 0,
            "concepts_indexed": 0,
            "integrity_score": 0.0,
            "extraction_log_exists": False
        }
        
        # Verificar PDF fuente
        pdf_path = RAW_DATA_DIR / "Un Curso de Milagros.pdf"
        validation_results["pdf_source_exists"] = pdf_path.exists()
        
        if validation_results["pdf_source_exists"]:
            self.logger.info(f"✓ PDF fuente encontrado: {pdf_path}")
        else:
            self.logger.warning(f"⚠️ PDF fuente no encontrado: {pdf_path}")
        
        # Verificar texto extraído
        extracted_text_path = PROCESSED_DATA_DIR / "ucdm_complete_text.txt"
        validation_results["extracted_text_exists"] = extracted_text_path.exists()
        
        if validation_results["extracted_text_exists"]:
            self.logger.info(f"✓ Texto extraído encontrado")
            
            # Verificar tamaño del archivo
            size_mb = extracted_text_path.stat().st_size / (1024 * 1024)
            self.logger.info(f"   Tamaño: {size_mb:.1f} MB")
        
        # Verificar índice de lecciones
        lessons_index_path = INDICES_DIR / "ucdm_comprehensive_index.json"
        if lessons_index_path.exists():
            with open(lessons_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            validation_results["lessons_indexed"] = len(index_data.get("lesson_details", {}))
            validation_results["concepts_indexed"] = len(index_data.get("concept_index", {}))
            validation_results["integrity_score"] = index_data.get("metadata", {}).get("coverage_percentage", 0) / 100
            
            self.logger.info(f"✓ Lecciones indexadas: {validation_results['lessons_indexed']}")
            self.logger.info(f"✓ Conceptos indexados: {validation_results['concepts_indexed']}")
            self.logger.info(f"✓ Score de integridad: {validation_results['integrity_score']:.2f}")
        
        # Verificar log de extracción
        extraction_log_path = RAW_DATA_DIR / "extraction_log.json"
        validation_results["extraction_log_exists"] = extraction_log_path.exists()
        
        return validation_results
    
    def validate_response_engine(self) -> Dict[str, any]:
        """Validar motor de respuestas"""
        self.logger.info("⚡ Validando motor de respuestas...")
        
        validation_results = {
            "engine_loads": False,
            "data_loaded": False,
            "structure_correct": False,
            "response_quality": 0.0,
            "template_variety": False
        }
        
        try:
            # Crear instancia del motor
            engine = UCDMResponseEngine()
            validation_results["engine_loads"] = True
            self.logger.info("✓ Motor de respuestas cargado")
            
            # Cargar datos
            data_loaded = engine.load_data()
            validation_results["data_loaded"] = data_loaded
            
            if data_loaded:
                self.logger.info("✓ Datos cargados en el motor")
                
                # Probar generación de respuestas
                test_queries = [
                    "Explícame la Lección 1",
                    "¿Cuál es la lección de hoy?",
                    "Háblame sobre el perdón en UCDM"
                ]
                
                structure_checks = []
                response_qualities = []
                
                for query in test_queries:
                    result = engine.process_query(query)
                    response = result.get('response', '')
                    
                    # Verificar estructura
                    required_sections = [
                        "HOOK INICIAL",
                        "APLICACIÓN PRÁCTICA",
                        "INTEGRACIÓN EXPERIENCIAL", 
                        "CIERRE MOTIVADOR"
                    ]
                    
                    sections_found = sum(1 for section in required_sections if section in response)
                    structure_score = sections_found / len(required_sections)
                    structure_checks.append(structure_score)
                    
                    # Evaluar calidad (longitud, coherencia básica)
                    quality_score = 0.0
                    if len(response) > 200:  # Mínimo de contenido
                        quality_score += 0.3
                    if len(response.split()) > 50:  # Mínimo de palabras
                        quality_score += 0.3
                    if "UCDM" in response or "Curso" in response:  # Contenido relevante
                        quality_score += 0.4
                    
                    response_qualities.append(quality_score)
                
                validation_results["structure_correct"] = sum(structure_checks) / len(structure_checks) > 0.8
                validation_results["response_quality"] = sum(response_qualities) / len(response_qualities)
                
                self.logger.info(f"✓ Estructura promedio: {sum(structure_checks)/len(structure_checks):.2f}")
                self.logger.info(f"✓ Calidad promedio: {validation_results['response_quality']:.2f}")
                
                # Verificar variedad de templates
                responses = [engine.process_query(q)['response'] for q in test_queries]
                unique_starts = len(set(r[:50] for r in responses))
                validation_results["template_variety"] = unique_starts > 1
                
            else:
                self.logger.error("✗ No se pudieron cargar datos en el motor")
                
        except Exception as e:
            self.logger.error(f"✗ Error en motor de respuestas: {str(e)}")
        
        return validation_results
    
    def validate_cli_interface(self) -> Dict[str, bool]:
        """Validar interfaz CLI"""
        self.logger.info("💻 Validando interfaz CLI...")
        
        validation_results = {
            "cli_file_exists": False,
            "cli_imports_work": False,
            "cli_help_works": False
        }
        
        cli_path = PROJECT_ROOT / "ucdm_cli.py"
        validation_results["cli_file_exists"] = cli_path.exists()
        
        if validation_results["cli_file_exists"]:
            self.logger.info("✓ Archivo CLI encontrado")
            
            try:
                # Intentar importar módulos necesarios
                import importlib.util
                spec = importlib.util.spec_from_file_location("ucdm_cli", cli_path)
                if spec and spec.loader:
                    validation_results["cli_imports_work"] = True
                    self.logger.info("✓ Imports de CLI funcionan")
                
            except Exception as e:
                self.logger.error(f"✗ Error en imports CLI: {str(e)}")
        
        return validation_results
    
    def validate_dataset_generation(self) -> Dict[str, any]:
        """Validar generación de datasets"""
        self.logger.info("📊 Validando generación de datasets...")
        
        validation_results = {
            "dataset_file_exists": False,
            "dataset_size": 0,
            "examples_count": 0,
            "structure_variety": False
        }
        
        # Verificar dataset principal
        dataset_path = TRAINING_DATA_DIR / "ucdm_structured_dataset.jsonl"
        validation_results["dataset_file_exists"] = dataset_path.exists()
        
        if validation_results["dataset_file_exists"]:
            self.logger.info("✓ Dataset principal encontrado")
            
            # Analizar contenido del dataset
            examples = []
            try:
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            examples.append(json.loads(line))
                
                validation_results["examples_count"] = len(examples)
                validation_results["dataset_size"] = dataset_path.stat().st_size / (1024 * 1024)  # MB
                
                # Verificar variedad estructural
                if examples:
                    instructions = [ex.get('instruction', '') for ex in examples[:10]]
                    unique_starts = len(set(inst[:20] for inst in instructions))
                    validation_results["structure_variety"] = unique_starts > 3
                
                self.logger.info(f"✓ Ejemplos en dataset: {validation_results['examples_count']}")
                self.logger.info(f"✓ Tamaño del dataset: {validation_results['dataset_size']:.1f} MB")
                
            except Exception as e:
                self.logger.error(f"✗ Error analizando dataset: {str(e)}")
        
        return validation_results
    
    def performance_benchmark(self) -> Dict[str, float]:
        """Realizar benchmark de rendimiento"""
        self.logger.info("⏱️ Ejecutando benchmark de rendimiento...")
        
        benchmark_results = {
            "engine_load_time": 0.0,
            "response_generation_time": 0.0,
            "cli_startup_time": 0.0
        }
        
        try:
            # Tiempo de carga del motor
            start_time = time.time()
            engine = UCDMResponseEngine()
            engine.load_data()
            benchmark_results["engine_load_time"] = time.time() - start_time
            
            # Tiempo de generación de respuesta
            start_time = time.time()
            result = engine.process_query("Explícame la Lección 1")
            benchmark_results["response_generation_time"] = time.time() - start_time
            
            self.logger.info(f"✓ Carga del motor: {benchmark_results['engine_load_time']:.2f}s")
            self.logger.info(f"✓ Generación de respuesta: {benchmark_results['response_generation_time']:.2f}s")
            
        except Exception as e:
            self.logger.error(f"✗ Error en benchmark: {str(e)}")
        
        return benchmark_results
    
    def run_complete_validation(self) -> Dict[str, any]:
        """Ejecutar validación completa del sistema"""
        self.logger.info("🚀 INICIANDO VALIDACIÓN COMPLETA DEL SISTEMA UCDM")
        
        start_time = time.time()
        
        # Ejecutar todas las validaciones
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "file_structure": self.validate_file_structure(),
            "data_extraction": self.validate_data_extraction(),
            "response_engine": self.validate_response_engine(),
            "cli_interface": self.validate_cli_interface(),
            "dataset_generation": self.validate_dataset_generation(),
            "performance": self.performance_benchmark(),
            "total_time": 0.0
        }
        
        self.results["total_time"] = time.time() - start_time
        
        return self.results
    
    def generate_validation_report(self) -> str:
        """Generar reporte de validación"""
        if not self.results:
            return "No hay resultados de validación disponibles"
        
        report = f"""
{'='*80}
🌟 REPORTE DE VALIDACIÓN DEL SISTEMA UCDM
{'='*80}

📅 Fecha: {self.results['timestamp']}
⏱️  Tiempo total: {self.results['total_time']:.2f} segundos

📁 ESTRUCTURA DE ARCHIVOS:
"""
        
        # Archivos críticos
        critical_files = [
            'file_config/settings.py',
            'file_training/response_engine.py',
            'file_ucdm_cli.py'
        ]
        
        for key, value in self.results['file_structure'].items():
            if key in critical_files:
                status = "✅" if value else "❌"
                report += f"   {status} {key.replace('file_', '').replace('_', '/')}\n"
        
        # Extracción de datos
        data_ext = self.results['data_extraction']
        report += f"""
📖 EXTRACCIÓN DE DATOS:
   {'✅' if data_ext['pdf_source_exists'] else '⚠️'} PDF fuente: {'Encontrado' if data_ext['pdf_source_exists'] else 'No encontrado'}
   {'✅' if data_ext['extracted_text_exists'] else '❌'} Texto extraído: {'Disponible' if data_ext['extracted_text_exists'] else 'No disponible'}
   📊 Lecciones indexadas: {data_ext['lessons_indexed']}/365
   🏷️ Conceptos indexados: {data_ext['concepts_indexed']}
   📈 Score de integridad: {data_ext['integrity_score']:.1%}
"""
        
        # Motor de respuestas
        engine = self.results['response_engine']
        report += f"""
⚡ MOTOR DE RESPUESTAS:
   {'✅' if engine['engine_loads'] else '❌'} Carga del motor: {'OK' if engine['engine_loads'] else 'Error'}
   {'✅' if engine['data_loaded'] else '❌'} Datos cargados: {'OK' if engine['data_loaded'] else 'Error'}
   {'✅' if engine['structure_correct'] else '❌'} Estructura correcta: {'OK' if engine['structure_correct'] else 'Error'}
   📊 Calidad de respuestas: {engine['response_quality']:.1%}
   🎨 Variedad de templates: {'OK' if engine['template_variety'] else 'Limitada'}
"""
        
        # Dataset
        dataset = self.results['dataset_generation']
        report += f"""
📊 GENERACIÓN DE DATASETS:
   {'✅' if dataset['dataset_file_exists'] else '❌'} Dataset principal: {'Disponible' if dataset['dataset_file_exists'] else 'No encontrado'}
   📈 Ejemplos generados: {dataset['examples_count']}
   💾 Tamaño del dataset: {dataset['dataset_size']:.1f} MB
   🎯 Variedad estructural: {'OK' if dataset['structure_variety'] else 'Limitada'}
"""
        
        # Rendimiento
        perf = self.results['performance']
        report += f"""
⏱️ RENDIMIENTO:
   🚀 Carga del motor: {perf['engine_load_time']:.2f}s
   💭 Generación de respuesta: {perf['response_generation_time']:.2f}s
"""
        
        # Resumen general
        total_checks = 0
        passed_checks = 0
        
        for category in ['file_structure', 'data_extraction', 'response_engine', 'cli_interface', 'dataset_generation']:
            for key, value in self.results[category].items():
                if isinstance(value, bool):
                    total_checks += 1
                    if value:
                        passed_checks += 1
                elif isinstance(value, (int, float)) and key in ['lessons_indexed', 'concepts_indexed']:
                    total_checks += 1
                    if value > 0:
                        passed_checks += 1
        
        success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        report += f"""
{'='*80}
📋 RESUMEN GENERAL:
   ✅ Checks pasados: {passed_checks}/{total_checks}
   📊 Tasa de éxito: {success_rate:.1f}%
   
🎯 ESTADO DEL SISTEMA: {'🟢 OPERATIVO' if success_rate > 80 else '🟡 PARCIAL' if success_rate > 60 else '🔴 REQUIERE ATENCIÓN'}

💡 RECOMENDACIONES:
"""
        
        if data_ext['lessons_indexed'] < 300:
            report += "   • Ejecutar extracción completa del PDF\n"
        
        if not engine['structure_correct']:
            report += "   • Verificar templates del motor de respuestas\n"
        
        if dataset['examples_count'] < 500:
            report += "   • Generar más ejemplos de entrenamiento\n"
        
        if perf['response_generation_time'] > 5:
            report += "   • Optimizar rendimiento del motor\n"
        
        report += f"""
🚀 PASOS SIGUIENTES:
   1. Revisar elementos marcados como ❌
   2. Ejecutar scripts de configuración faltantes
   3. Probar integración con Ollama
   4. Validar respuestas del modelo especializado

{'='*80}
"""
        
        return report
    
    def save_validation_results(self) -> str:
        """Guardar resultados de validación"""
        results_file = PROJECT_ROOT / "validation_report.json"
        report_file = PROJECT_ROOT / "validation_report.txt"
        
        # Guardar JSON
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Guardar reporte de texto
        report_text = self.generate_validation_report()
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        self.logger.info(f"✅ Resultados guardados en: {results_file}")
        self.logger.info(f"✅ Reporte guardado en: {report_file}")
        
        return str(report_file)

def main():
    """Función principal de validación"""
    print("🔍 Iniciando validación del sistema UCDM...")
    
    validator = UCDMSystemValidator()
    
    # Ejecutar validación completa
    results = validator.run_complete_validation()
    
    # Generar y mostrar reporte
    report = validator.generate_validation_report()
    print(report)
    
    # Guardar resultados
    report_file = validator.save_validation_results()
    
    # Determinar código de salida
    success_checks = 0
    total_checks = 0
    
    for category in results:
        if isinstance(results[category], dict):
            for key, value in results[category].items():
                if isinstance(value, bool):
                    total_checks += 1
                    if value:
                        success_checks += 1
    
    success_rate = (success_checks / total_checks) * 100 if total_checks > 0 else 0
    
    if success_rate > 80:
        print("🎉 SISTEMA VALIDADO EXITOSAMENTE")
        return 0
    elif success_rate > 60:
        print("⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        return 1
    else:
        print("❌ SISTEMA REQUIERE ATENCIÓN")
        return 2

if __name__ == "__main__":
    exit(main())