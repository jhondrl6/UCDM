#!/usr/bin/env python3
"""
Análisis de estructura de índices para optimización
"""

import json
import os
from pathlib import Path

def analyze_indices():
    indices_dir = Path("data/indices")
    total_size = 0
    files_info = []
    
    print("📊 ANÁLISIS DE ÍNDICES UCDM")
    print("=" * 50)
    
    # Analizar cada archivo
    for file_path in indices_dir.glob("*.json"):
        size = file_path.stat().st_size
        total_size += size
        
        # Cargar y analizar contenido
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                keys_count = len(data.keys())
                top_level_keys = list(data.keys())[:5]
            elif isinstance(data, list):
                keys_count = len(data)
                top_level_keys = ["array_items"]
            else:
                keys_count = 1
                top_level_keys = ["single_value"]
            
            files_info.append({
                'name': file_path.name,
                'size_kb': size / 1024,
                'keys_count': keys_count,
                'top_keys': top_level_keys
            })
            
        except Exception as e:
            print(f"❌ Error analizando {file_path.name}: {e}")
            files_info.append({
                'name': file_path.name,
                'size_kb': size / 1024,
                'keys_count': 0,
                'top_keys': ['ERROR'],
                'error': str(e)
            })
    
    # Ordenar por tamaño
    files_info.sort(key=lambda x: x['size_kb'], reverse=True)
    
    print(f"📈 Total de índices: {total_size/1024:.1f} KB")
    print(f"📁 Archivos analizados: {len(files_info)}")
    print("\n🔍 DESGLOSE POR ARCHIVO:")
    print("-" * 70)
    
    for info in files_info:
        print(f"📄 {info['name']}:")
        print(f"   📊 Tamaño: {info['size_kb']:.1f} KB")
        print(f"   🔑 Elementos: {info['keys_count']}")
        print(f"   📋 Estructura: {info['top_keys']}")
        if 'error' in info:
            print(f"   ❌ Error: {info['error']}")
        print()
    
    # Análisis de carga de respuesta actual
    print("⚡ ANÁLISIS DE CARGA ACTUAL:")
    print("-" * 40)
    
    comprehensive_file = indices_dir / "ucdm_comprehensive_index.json"
    if comprehensive_file.exists():
        print(f"✅ Archivo principal: {comprehensive_file.name}")
        print(f"   Tamaño: {comprehensive_file.stat().st_size / 1024:.1f} KB")
        print("   ➡️ Se carga COMPLETO en cada inicio")
        print("   ➡️ Contiene TODOS los datos necesarios")
        print("   ➡️ Estrategia actual: CARGA TOTAL")
        
        # Estimar tiempo de carga
        load_time_estimate = (comprehensive_file.stat().st_size / 1024) * 0.01  # ~0.01ms por KB
        print(f"   ⏱️ Tiempo estimado de carga: {load_time_estimate:.2f}ms")
    
    print("\n🎯 OPORTUNIDADES DE OPTIMIZACIÓN:")
    print("-" * 50)
    print("1. 💾 LAZY LOADING: Cargar índices solo cuando se necesiten")
    print("2. 🗂️ SEGMENTACIÓN: Dividir índices grandes por uso")
    print("3. 💿 CACHE EN MEMORIA: Mantener índices frecuentes en RAM")
    print("4. 🗜️ COMPRESIÓN: Reducir tamaño en disco")
    print("5. 📊 MÉTRICAS: Tracking de uso para optimización predictiva")

if __name__ == "__main__":
    analyze_indices()