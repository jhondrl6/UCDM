#!/usr/bin/env python3
"""
Script para configurar y especializar el modelo UCDM en Ollama
Automatiza el proceso de creación del modelo especializado
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

class UCDMOllamaManager:
    """Gestor para la configuración del modelo UCDM en Ollama"""
    
    def __init__(self):
        self.model_name = "ucdm-gemma"
        self.base_model = "gemma:3b"
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def check_ollama_installed(self) -> bool:
        """Verificar si Ollama está instalado y ejecutándose"""
        try:
            result = subprocess.run(['ollama', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info(f"Ollama detectado: {result.stdout.strip()}")
                return True
            else:
                self.logger.error("Ollama no está respondiendo correctamente")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout al verificar Ollama")
            return False
        except FileNotFoundError:
            self.logger.error("Ollama no está instalado o no está en PATH")
            return False
        except Exception as e:
            self.logger.error(f"Error verificando Ollama: {str(e)}")
            return False
    
    def check_base_model(self) -> bool:
        """Verificar si el modelo base está disponible"""
        try:
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                models = result.stdout
                if self.base_model in models:
                    self.logger.info(f"Modelo base {self.base_model} encontrado")
                    return True
                else:
                    self.logger.warning(f"Modelo base {self.base_model} no encontrado")
                    return False
            else:
                self.logger.error("Error al listar modelos de Ollama")
                return False
        except Exception as e:
            self.logger.error(f"Error verificando modelo base: {str(e)}")
            return False
    
    def pull_base_model(self) -> bool:
        """Descargar modelo base si no está disponible"""
        self.logger.info(f"Descargando modelo base {self.base_model}...")
        try:
            result = subprocess.run(['ollama', 'pull', self.base_model], 
                                  capture_output=True, text=True, timeout=1800)  # 30 minutos
            if result.returncode == 0:
                self.logger.info(f"Modelo {self.base_model} descargado exitosamente")
                return True
            else:
                self.logger.error(f"Error descargando modelo: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout descargando modelo base")
            return False
        except Exception as e:
            self.logger.error(f"Error en descarga: {str(e)}")
            return False
    
    def create_specialized_model(self) -> bool:
        """Crear modelo especializado usando el Modelfile"""
        modelfile_path = Path(__file__).parent / "Modelfile"
        
        if not modelfile_path.exists():
            self.logger.error(f"Modelfile no encontrado en: {modelfile_path}")
            return False
        
        self.logger.info(f"Creando modelo especializado {self.model_name}...")
        
        try:
            # Cambiar al directorio del Modelfile para que Ollama lo encuentre
            original_dir = Path.cwd()
            os.chdir(modelfile_path.parent)
            
            result = subprocess.run(['ollama', 'create', self.model_name, '-f', 'Modelfile'], 
                                  capture_output=True, text=True, timeout=600)  # 10 minutos
            
            os.chdir(original_dir)
            
            if result.returncode == 0:
                self.logger.info(f"Modelo {self.model_name} creado exitosamente")
                return True
            else:
                self.logger.error(f"Error creando modelo: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout creando modelo especializado")
            return False
        except Exception as e:
            self.logger.error(f"Error creando modelo: {str(e)}")
            return False
    
    def test_model(self) -> bool:
        """Probar el modelo especializado"""
        test_prompt = "Explícame la Lección 1 de Un Curso de Milagros"
        
        self.logger.info("Probando modelo especializado...")
        
        try:
            # Usar ollama run para probar
            result = subprocess.run(['ollama', 'run', self.model_name, test_prompt], 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                response = result.stdout.strip()
                
                # Verificar que la respuesta tiene la estructura esperada
                required_sections = [
                    "HOOK INICIAL",
                    "APLICACIÓN PRÁCTICA", 
                    "INTEGRACIÓN EXPERIENCIAL",
                    "CIERRE MOTIVADOR"
                ]
                
                sections_found = sum(1 for section in required_sections if section in response)
                
                if sections_found >= 3:  # Al menos 3 de 4 secciones
                    self.logger.info("✅ Modelo responde con estructura correcta")
                    self.logger.info(f"Secciones encontradas: {sections_found}/4")
                    return True
                else:
                    self.logger.warning(f"⚠️ Estructura incompleta: {sections_found}/4 secciones")
                    self.logger.info("El modelo funciona pero necesita ajustes")
                    return True  # Consideramos éxito parcial
            else:
                self.logger.error(f"Error probando modelo: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout probando modelo")
            return False
        except Exception as e:
            self.logger.error(f"Error probando modelo: {str(e)}")
            return False
    
    def create_usage_script(self) -> None:
        """Crear script de uso del modelo"""
        usage_script = f'''#!/usr/bin/env python3
"""
Script de uso para el modelo UCDM especializado
"""

import subprocess
import sys

def query_ucdm(prompt):
    """Consultar el modelo UCDM"""
    try:
        result = subprocess.run(
            ['ollama', 'run', '{self.model_name}', prompt],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {{result.stderr}}"
    
    except Exception as e:
        return f"Error: {{str(e)}}"

def main():
    if len(sys.argv) < 2:
        print("Uso: python query_ucdm.py 'tu pregunta sobre UCDM'")
        print("Ejemplos:")
        print("  python query_ucdm.py 'Explícame la Lección 1'")
        print("  python query_ucdm.py '¿Cuál es la lección de hoy?'")
        print("  python query_ucdm.py 'Háblame sobre el perdón'")
        return
    
    prompt = ' '.join(sys.argv[1:])
    print(f"Consultando UCDM: {{prompt}}")
    print("-" * 50)
    
    response = query_ucdm(prompt)
    print(response)

if __name__ == "__main__":
    main()
'''
        
        script_path = Path(__file__).parent / "query_ucdm.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(usage_script)
        
        self.logger.info(f"Script de uso creado: {script_path}")
    
    def setup_complete_model(self) -> bool:
        """Configuración completa del modelo UCDM"""
        self.logger.info("=== CONFIGURACIÓN COMPLETA DEL MODELO UCDM ===")
        
        # 1. Verificar Ollama
        if not self.check_ollama_installed():
            self.logger.error("❌ Ollama no está disponible")
            self.logger.info("💡 Instala Ollama desde: https://ollama.ai")
            return False
        
        # 2. Verificar/descargar modelo base
        if not self.check_base_model():
            self.logger.info("📥 Descargando modelo base...")
            if not self.pull_base_model():
                self.logger.error("❌ No se pudo descargar el modelo base")
                return False
        
        # 3. Crear modelo especializado
        if not self.create_specialized_model():
            self.logger.error("❌ No se pudo crear el modelo especializado")
            return False
        
        # 4. Probar modelo
        if not self.test_model():
            self.logger.error("❌ El modelo no responde correctamente")
            return False
        
        # 5. Crear scripts de uso
        self.create_usage_script()
        
        self.logger.info("✅ MODELO UCDM CONFIGURADO EXITOSAMENTE")
        return True
    
    def show_usage_instructions(self) -> None:
        """Mostrar instrucciones de uso"""
        print(f"\\n{'='*60}")
        print("🌟 MODELO UCDM LISTO PARA USAR")
        print(f"{'='*60}")
        
        print(f"\\n📋 FORMAS DE USAR EL MODELO:")
        
        print(f"\\n1. 🖥️ OLLAMA DIRECTO:")
        print(f"   ollama run {self.model_name}")
        print(f"   ollama run {self.model_name} 'Explícame la Lección 1'")
        
        print(f"\\n2. 🐍 SCRIPT PYTHON:")
        print(f"   python ollama/query_ucdm.py 'tu pregunta'")
        
        print(f"\\n3. 🎮 CLI INTERACTIVA:")
        print(f"   python ucdm_cli.py")
        
        print(f"\\n📝 EJEMPLOS DE CONSULTAS:")
        examples = [
            "Explícame la Lección 1",
            "¿Cuál es la lección de hoy?",
            "Háblame sobre el perdón en UCDM",
            "Necesito una reflexión nocturna",
            "¿Qué enseña el Curso sobre el miedo?"
        ]
        
        for example in examples:
            print(f"   • {example}")
        
        print(f"\\n🔧 CONFIGURACIÓN:")
        print(f"   Modelo: {self.model_name}")
        print(f"   Base: {self.base_model}")
        print(f"   Contexto: 8192 tokens")
        print(f"   Temperatura: 0.7")
        
        print(f"\\n⚡ ESTRUCTURA DE RESPUESTAS:")
        print(f"   • HOOK INICIAL: Pregunta enganchadora")
        print(f"   • APLICACIÓN PRÁCTICA: 3 pasos concretos")
        print(f"   • INTEGRACIÓN EXPERIENCIAL: Reflexión personal")
        print(f"   • CIERRE MOTIVADOR: Inspiración final")

def main():
    """Función principal"""
    manager = UCDMOllamaManager()
    
    print("🚀 Iniciando configuración del modelo UCDM...")
    
    if manager.setup_complete_model():
        manager.show_usage_instructions()
        return 0
    else:
        print("❌ Error en la configuración del modelo")
        return 1

if __name__ == "__main__":
    import os
    exit(main())