#!/usr/bin/env python3
"""
Script Principal para Procesar las 250 Lecciones Faltantes UCDM
Ejecuta el procesamiento completo de las lecciones identificadas como faltantes
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))
from config.settings import *
from validation.missing_lessons_processor import MissingLessonsProcessor
from validation.comprehensive_validation_pipeline import ComprehensiveValidationPipeline

def main():
    """Función principal para ejecutar el procesamiento completo"""
    
    print("🚀 SISTEMA DE COMPLETACIÓN DE LECCIONES FALTANTES UCDM")
    print("=" * 65)
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Inicializar pipeline de validación
        print("🔧 Inicializando sistema de validación...")
        pipeline = ComprehensiveValidationPipeline()
        
        # 2. Crear procesador especializado
        print("🔧 Inicializando procesador de lecciones faltantes...")
        processor = MissingLessonsProcessor(validation_pipeline=pipeline)
        
        # 3. Cargar contenido fuente
        print("📖 Cargando contenido fuente...")
        if not processor.load_source_content():
            print("❌ ERROR: No se pudo cargar el contenido fuente")
            print("   Asegúrate de que existe: data/processed/ucdm_complete_text.txt")
            return 1
        
        # 4. Identificar lecciones faltantes
        print("🔍 Identificando lecciones faltantes...")
        missing_lessons = processor.identify_missing_lessons()
        
        if not missing_lessons:
            print("✅ ¡EXCELENTE! No hay lecciones faltantes por procesar")
            print("   El sistema ya tiene las 365 lecciones completas")
            return 0
        
        print(f"📊 Encontradas {len(missing_lessons)} lecciones faltantes")
        
        # Mostrar algunas lecciones faltantes como ejemplo
        if len(missing_lessons) <= 20:
            print(f"   Lecciones faltantes: {missing_lessons}")
        else:
            print(f"   Primeras 20: {missing_lessons[:20]}")
            print(f"   ... y {len(missing_lessons) - 20} más")
        
        print()
        
        # 5. Confirmar procesamiento si hay muchas lecciones
        if len(missing_lessons) > 50:
            response = input(f"¿Procesar {len(missing_lessons)} lecciones faltantes? (s/N): ")
            if response.lower() not in ['s', 'sí', 'si', 'y', 'yes']:
                print("Procesamiento cancelado por el usuario")
                return 0
        
        print(f"🚀 Iniciando procesamiento de {len(missing_lessons)} lecciones...")
        print("   Este proceso puede tomar varios minutos...")
        print()
        
        # 6. Ejecutar procesamiento completo
        start_time = datetime.now()
        result = processor.process_all_missing_lessons()
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # 7. Mostrar resultados
        if result["success"]:
            print("✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
            print("=" * 50)
            print(f"   Tiempo total: {processing_time:.1f} segundos")
            print(f"   Lecciones solicitadas: {result['total_requested']}")
            print(f"   Exitosamente procesadas: {result['total_processed']}")
            print(f"   Fallidas: {result['total_failed']}")
            print(f"   Tasa de éxito: {result['success_rate']:.1f}%")
            
            # Mostrar cobertura actualizada
            if "updated_coverage" in result:
                coverage = result["updated_coverage"]
                print(f"\n📊 COBERTURA ACTUALIZADA:")
                print(f"   Cobertura total: {coverage.get('coverage_percentage', 0):.1f}%")
                print(f"   Lecciones procesadas: {coverage.get('updated_count', 0)}/365")
                print(f"   Lecciones restantes: {coverage.get('remaining_lessons', 365)}")
                
                # Verificar si se cumplió el objetivo de 250 lecciones
                if result['total_processed'] >= 200:  # Al menos 200 de las 250 objetivo
                    print("\n🎯 ¡OBJETIVO PRINCIPAL ALCANZADO!")
                    print(f"   Se han procesado {result['total_processed']} lecciones")
                    print("   El sistema ha completado exitosamente el procesamiento de lecciones faltantes")
            
            # Mostrar recomendaciones
            recommendations = result.get("final_recommendations", [])
            if recommendations:
                print(f"\n💡 RECOMENDACIONES:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
            
            # 8. Ejecutar validación final del sistema
            print("\n🔍 Ejecutando validación final del sistema...")
            try:
                health_report = pipeline.generate_system_health_report()
                if health_report and "system_dashboard" in health_report:
                    dashboard = health_report["system_dashboard"]
                    system_status = dashboard.get("status", "DESCONOCIDO")
                    
                    print(f"   Estado del sistema: {system_status}")
                    
                    sections = dashboard.get("sections", {})
                    if "system_overview" in sections:
                        overview = sections["system_overview"]
                        coverage = overview.get("coverage", "N/A")
                        quality = overview.get("quality_score", "N/A")
                        print(f"   Cobertura general: {coverage}")
                        print(f"   Calidad general: {quality}")
                
                print("✅ Validación final completada")
                
            except Exception as e:
                print(f"⚠️  Advertencia: Error en validación final: {e}")
            
            print("\n" + "=" * 65)
            print("🎉 PROCESAMIENTO DE LECCIONES FALTANTES COMPLETADO")
            print("   El sistema UCDM ha sido actualizado exitosamente")
            print("   Revisa los archivos generados en data/processed/lessons/")
            print("=" * 65)
            
            return 0
            
        else:
            print("❌ ERROR EN EL PROCESAMIENTO")
            print(f"   Error: {result.get('error', 'Error desconocido')}")
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️  Procesamiento interrumpido por el usuario")
        return 1
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        import traceback
        print("\nDetalles del error:")
        traceback.print_exc()
        return 1

def show_status():
    """Mostrar estado actual del sistema sin procesar"""
    try:
        print("📊 ESTADO ACTUAL DEL SISTEMA UCDM")
        print("=" * 40)
        
        # Cargar índice actual
        index_file = INDICES_DIR / "365_lessons_indexed.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            current_count = len(index_data)
            coverage_percentage = (current_count / 365) * 100
            missing_count = 365 - current_count
            
            print(f"   Lecciones procesadas: {current_count}/365")
            print(f"   Cobertura actual: {coverage_percentage:.1f}%")
            print(f"   Lecciones faltantes: {missing_count}")
            
            if missing_count == 0:
                print("\n✅ ¡SISTEMA COMPLETO! Todas las 365 lecciones están procesadas")
            else:
                print(f"\n⚠️  Faltan {missing_count} lecciones por procesar")
                print("   Ejecuta 'python process_missing_lessons.py' para procesarlas")
        else:
            print("   No se encontró índice de lecciones")
            print("   El sistema parece no estar inicializado")
        
        # Verificar archivos de validación
        validation_file = PROCESSED_DATA_DIR / "lessons_validation.json"
        if validation_file.exists():
            print(f"\n📋 Último reporte de validación disponible")
        
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Error verificando estado: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_status()
    else:
        exit(main())