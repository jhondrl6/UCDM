#!/usr/bin/env python3
"""
Validación Final del Sistema UCDM
Genera reporte completo del estado del sistema implementado
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Configurar path
sys.path.append(str(Path(__file__).parent))

def test_component_imports():
    """Test de importación de todos los componentes"""
    print("🔍 Verificando importación de componentes...")
    
    components = {}
    
    try:
        from validation.quality_validation_engine import QualityValidationEngine
        components["QualityValidationEngine"] = "✅ OK"
    except Exception as e:
        components["QualityValidationEngine"] = f"❌ Error: {e}"
    
    try:
        from validation.lesson_recognition_engine import LessonRecognitionEngine
        components["LessonRecognitionEngine"] = "✅ OK"
    except Exception as e:
        components["LessonRecognitionEngine"] = f"❌ Error: {e}"
    
    try:
        from validation.response_structure_validator import ResponseStructureValidator
        components["ResponseStructureValidator"] = "✅ OK"
    except Exception as e:
        components["ResponseStructureValidator"] = f"❌ Error: {e}"
    
    try:
        from validation.quality_report_manager import QualityReportManager
        components["QualityReportManager"] = "✅ OK"
    except Exception as e:
        components["QualityReportManager"] = f"❌ Error: {e}"
    
    try:
        from validation.comprehensive_validation_pipeline import ComprehensiveValidationPipeline
        components["ComprehensiveValidationPipeline"] = "✅ OK"
    except Exception as e:
        components["ComprehensiveValidationPipeline"] = f"❌ Error: {e}"
    
    try:
        from ucdm_cli import UCDMCLIInterface
        components["UCDMCLIInterface"] = "✅ OK"
    except Exception as e:
        components["UCDMCLIInterface"] = f"❌ Error: {e}"
    
    return components

def test_validation_pipeline():
    """Test del pipeline de validación"""
    print("🔧 Probando pipeline de validación...")
    
    try:
        from validation.comprehensive_validation_pipeline import ComprehensiveValidationPipeline, PipelineConfig
        
        config = PipelineConfig(
            enable_text_validation=True,
            enable_lesson_recognition=True,
            enable_structure_validation=True,
            enable_report_generation=True
        )
        
        pipeline = ComprehensiveValidationPipeline(config)
        
        # Test texto simple
        test_text = """
        Lección 1: Nada de lo que veo significa nada.
        Esta es una lección fundamental del Curso de Milagros.
        Los milagros ocurren naturalmente cuando elegimos el amor.
        """
        
        result = pipeline.validate_text_content(test_text, "test_validation")
        
        return {
            "pipeline_initialized": "✅ OK",
            "text_validation": "✅ OK" if result.get("success") else "❌ Failed",
            "processing_time": f"{result.get('processing_time', 0):.2f}s"
        }
        
    except Exception as e:
        return {
            "pipeline_initialized": f"❌ Error: {e}",
            "text_validation": "❌ Not tested",
            "processing_time": "N/A"
        }

def test_response_structure_validation():
    """Test del validador de estructura de respuestas"""
    print("📝 Probando validador de estructura...")
    
    try:
        from validation.response_structure_validator import ResponseStructureValidator
        
        validator = ResponseStructureValidator()
        
        # Respuesta de prueba perfecta
        test_response = """
        🎯 HOOK INICIAL:
        ¿Sabías que el amor es la única realidad?
        
        ⚡ APLICACIÓN PRÁCTICA:
        Paso 1: Recuerda tu verdadera naturaleza
        Paso 2: Elige el amor en cada momento
        Paso 3: Comparte tu luz con otros
        
        🌿 INTEGRACIÓN EXPERIENCIAL:
        Conecta con tu experiencia personal. El Curso nos enseña que los milagros son naturales.
        ¿Puedes sentir esta verdad en tu corazón?
        
        ✨ CIERRE MOTIVADOR:
        Estás listo para experimentar milagros. Comparte tu amor.
        """
        
        result = validator.validate_complete_response(
            test_response,
            "¿Cómo encuentro paz?",
            "test_response"
        )
        
        return {
            "validator_initialized": "✅ OK",
            "structure_validation": "✅ OK" if result.structure_validation.has_all_sections else "❌ Failed",
            "overall_score": f"{result.overall_score:.1f}%",
            "compliance_status": result.compliance_status
        }
        
    except Exception as e:
        return {
            "validator_initialized": f"❌ Error: {e}",
            "structure_validation": "❌ Not tested",
            "overall_score": "N/A",
            "compliance_status": "ERROR"
        }

def test_cli_functionality():
    """Test de funcionalidad CLI"""
    print("💻 Probando funcionalidad CLI...")
    
    try:
        from ucdm_cli import UCDMCLIInterface
        
        cli = UCDMCLIInterface()
        
        # Test comandos básicos
        commands_tested = {}
        
        # Test help
        try:
            cli.show_help_menu()
            commands_tested["help"] = "✅ OK"
        except Exception as e:
            commands_tested["help"] = f"❌ Error: {e}"
        
        # Test stats
        try:
            cli.show_system_stats()
            commands_tested["stats"] = "✅ OK"
        except Exception as e:
            commands_tested["stats"] = f"❌ Error: {e}"
        
        # Test comandos de validación
        try:
            if cli.validation_pipeline:
                cli.cmd_validate([])
                commands_tested["validate"] = "✅ OK"
            else:
                commands_tested["validate"] = "⚠️ Pipeline not available"
        except Exception as e:
            commands_tested["validate"] = f"❌ Error: {e}"
        
        return {
            "cli_initialized": "✅ OK",
            "commands": commands_tested,
            "validation_pipeline_available": "✅ OK" if cli.validation_pipeline else "❌ Not available"
        }
        
    except Exception as e:
        return {
            "cli_initialized": f"❌ Error: {e}",
            "commands": {},
            "validation_pipeline_available": "❌ Error"
        }

def check_system_files():
    """Verificar archivos del sistema"""
    print("📁 Verificando archivos del sistema...")
    
    critical_files = [
        "validation/quality_validation_engine.py",
        "validation/lesson_recognition_engine.py", 
        "validation/response_structure_validator.py",
        "validation/quality_report_manager.py",
        "validation/comprehensive_validation_pipeline.py",
        "ucdm_cli.py",
        "tests/test_validation_components.py",
        "tests/test_integration_validation_system.py",
        "config/settings.py"
    ]
    
    file_status = {}
    for file_path in critical_files:
        full_path = Path(file_path)
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            file_status[file_path] = f"✅ OK ({size_kb:.1f} KB)"
        else:
            file_status[file_path] = "❌ Missing"
    
    return file_status

def generate_final_report():
    """Generar reporte final completo"""
    print("=" * 70)
    print("🚀 VALIDACIÓN FINAL DEL SISTEMA UCDM")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test de componentes
    components = test_component_imports()
    print("📦 COMPONENTES:")
    for comp, status in components.items():
        print(f"   {comp}: {status}")
    print()
    
    # Test de archivos
    files = check_system_files()
    print("📁 ARCHIVOS CRÍTICOS:")
    for file_path, status in files.items():
        print(f"   {file_path}: {status}")
    print()
    
    # Test del pipeline
    pipeline_test = test_validation_pipeline()
    print("🔧 PIPELINE DE VALIDACIÓN:")
    for test, result in pipeline_test.items():
        print(f"   {test}: {result}")
    print()
    
    # Test de estructura
    structure_test = test_response_structure_validation()
    print("📝 VALIDADOR DE ESTRUCTURA:")
    for test, result in structure_test.items():
        print(f"   {test}: {result}")
    print()
    
    # Test CLI
    cli_test = test_cli_functionality()
    print("💻 INTERFAZ CLI:")
    print(f"   Inicialización: {cli_test['cli_initialized']}")
    print(f"   Pipeline disponible: {cli_test['validation_pipeline_available']}")
    print("   Comandos:")
    for cmd, status in cli_test['commands'].items():
        print(f"     {cmd}: {status}")
    print()
    
    # Resumen final
    total_components = len(components)
    ok_components = len([c for c in components.values() if "✅ OK" in c])
    
    total_files = len(files)
    ok_files = len([f for f in files.values() if "✅ OK" in f])
    
    print("=" * 70)
    print("📊 RESUMEN FINAL:")
    print(f"   Componentes: {ok_components}/{total_components} OK ({(ok_components/total_components)*100:.1f}%)")
    print(f"   Archivos: {ok_files}/{total_files} OK ({(ok_files/total_files)*100:.1f}%)")
    print(f"   Pipeline: {pipeline_test['pipeline_initialized']}")
    print(f"   Validador: {structure_test['validator_initialized']}")
    print(f"   CLI: {cli_test['cli_initialized']}")
    print()
    
    # Determinar estado general
    if ok_components == total_components and ok_files == total_files:
        if "✅ OK" in pipeline_test['pipeline_initialized'] and "✅ OK" in structure_test['validator_initialized']:
            status = "🎉 SISTEMA COMPLETAMENTE OPERATIVO"
            color = "🟢"
        else:
            status = "⚠️ SISTEMA PARCIALMENTE OPERATIVO"
            color = "🟡"
    else:
        status = "❌ SISTEMA REQUIERE ATENCIÓN"
        color = "🔴"
    
    print(f"{color} ESTADO GENERAL: {status}")
    print("=" * 70)
    
    # Crear archivo de reporte
    report = {
        "timestamp": datetime.now().isoformat(),
        "system_status": status,
        "components": components,
        "files": files,
        "pipeline_test": pipeline_test,
        "structure_test": structure_test,
        "cli_test": cli_test,
        "summary": {
            "components_ok": f"{ok_components}/{total_components}",
            "files_ok": f"{ok_files}/{total_files}",
            "overall_health": (ok_components + ok_files) / (total_components + total_files) * 100
        }
    }
    
    # Guardar reporte
    report_file = Path("final_validation_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Reporte guardado en: {report_file.absolute()}")
    
    return report

if __name__ == "__main__":
    try:
        report = generate_final_report()
        print(f"\n✅ Validación completada exitosamente")
        
        # Mostrar próximos pasos si hay issues
        if "❌" in str(report) or "⚠️" in str(report):
            print("\n🔧 PRÓXIMOS PASOS RECOMENDADOS:")
            print("1. Revisar errores específicos en el reporte")
            print("2. Ejecutar: python -m pip install -r requirements.txt")
            print("3. Verificar configuración de paths en config/settings.py")
            print("4. Ejecutar tests individuales para componentes con errores")
        else:
            print("\n🎉 SISTEMA LISTO PARA PRODUCCIÓN!")
            print("🚀 Puedes ejecutar: python ucdm_cli.py")
        
    except Exception as e:
        print(f"\n❌ Error durante validación: {e}")
        sys.exit(1)