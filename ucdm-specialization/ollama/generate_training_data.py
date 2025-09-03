#!/usr/bin/env python3
"""
Generador de dataset para fine-tuning con Ollama
Crea datasets específicos para entrenar el modelo con el contenido real de UCDM
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *
from training.response_engine import UCDMResponseEngine

class OllamaFineTuningDatasetGenerator:
    """Generador de dataset específico para fine-tuning en Ollama"""
    
    def __init__(self):
        self.engine = UCDMResponseEngine()
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def generate_training_conversations(self) -> List[Dict]:
        """Generar conversaciones de entrenamiento para Ollama"""
        conversations = []
        
        # Cargar datos
        if not self.engine.load_data():
            self.logger.error("No se pudieron cargar los datos")
            return []
        
        self.logger.info("Generando conversaciones de entrenamiento...")
        
        # Patterns de consultas variadas
        query_patterns = [
            "Explícame la Lección {num}",
            "¿Qué enseña la Lección {num}?",
            "Háblame sobre la Lección {num} del UCDM",
            "Quiero estudiar la Lección {num}",
            "¿Cuál es el mensaje de la Lección {num}?",
            "Ayúdame a entender la Lección {num}",
            "¿Cómo puedo aplicar la Lección {num}?",
            "Dame una reflexión sobre la Lección {num}"
        ]
        
        # Generar para lecciones disponibles
        lesson_nums = list(self.engine.lessons_index.keys())[:50]  # Primeras 50 para el ejemplo
        
        for lesson_num_str in lesson_nums:
            lesson_num = int(lesson_num_str)
            lesson_data = self.engine.lessons_index[lesson_num_str]
            
            # Generar múltiples variaciones para cada lección
            for pattern in query_patterns[:3]:  # 3 variaciones por lección
                query = pattern.format(num=lesson_num)
                response = self.engine.generate_structured_response(query, "lesson_specific", lesson_num)
                
                if response:
                    conversations.append({
                        "prompt": query,
                        "response": response,
                        "metadata": {
                            "lesson_number": lesson_num,
                            "lesson_title": lesson_data['title'],
                            "type": "lesson_specific"
                        }
                    })
        
        # Consultas generales sobre conceptos
        concept_queries = [
            ("perdón", "Háblame sobre el perdón según Un Curso de Milagros"),
            ("amor", "¿Qué enseña UCDM sobre el amor?"),
            ("miedo", "¿Cómo entiende el Curso el concepto del miedo?"),
            ("paz", "Explícame qué es la paz según UCDM"),
            ("milagros", "¿Qué son los milagros en Un Curso de Milagros?"),
            ("espíritu santo", "¿Quién es el Espíritu Santo en UCDM?"),
            ("ego", "¿Qué enseña el Curso sobre el ego?"),
            ("dios", "¿Cómo presenta UCDM a Dios?"),
            ("cristo", "¿Quién es Cristo según Un Curso de Milagros?"),
            ("culpa", "¿Qué dice UCDM sobre la culpa?")
        ]
        
        for concept, query in concept_queries:
            response = self.engine.generate_structured_response(query, "concept_based")
            if response:
                conversations.append({
                    "prompt": query,
                    "response": response,
                    "metadata": {
                        "concept": concept,
                        "type": "concept_based"
                    }
                })
        
        # Consultas de aplicación práctica
        practical_queries = [
            "¿Cómo puedo aplicar UCDM en mi vida diaria?",
            "Necesito ayuda para perdonar a alguien según el Curso",
            "¿Qué me recomienda UCDM cuando tengo miedo?",
            "¿Cómo puedo encontrar paz en momentos difíciles?",
            "Dame una reflexión de UCDM para antes de dormir",
            "¿Cómo puedo transformar mi perspectiva según el Curso?",
            "¿Qué hacer cuando me siento culpable según UCDM?",
            "¿Cómo puedo ver milagros en mi vida cotidiana?",
            "Ayúdame a entender una relación difícil desde UCDM",
            "¿Qué dice el Curso sobre el sufrimiento?"
        ]
        
        for query in practical_queries:
            response = self.engine.generate_structured_response(query, "practical")
            if response:
                conversations.append({
                    "prompt": query,
                    "response": response,
                    "metadata": {
                        "type": "practical_application"
                    }
                })
        
        self.logger.info(f"Generadas {len(conversations)} conversaciones de entrenamiento")
        return conversations
    
    def create_ollama_training_file(self, conversations: List[Dict]) -> str:
        """Crear archivo de entrenamiento en formato Ollama"""
        training_data = []
        
        for conv in conversations:
            # Formato específico para Ollama fine-tuning
            training_example = {
                "prompt": f"<|im_start|>user\n{conv['prompt']}<|im_end|>\n<|im_start|>assistant\n",
                "completion": f"{conv['response']}<|im_end|>"
            }
            training_data.append(training_example)
        
        # Guardar archivo JSONL
        output_path = Path(__file__).parent / "ucdm_training_data.jsonl"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in training_data:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        self.logger.info(f"Archivo de entrenamiento guardado: {output_path}")
        return str(output_path)
    
    def create_modelfile_with_training(self, training_file: str) -> str:
        """Crear Modelfile con datos de entrenamiento incluidos"""
        
        modelfile_content = f'''# Modelfile para UCDM con Fine-tuning
FROM gemma:3b

# Parámetros optimizados
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 8192
PARAMETER num_predict 2048
PARAMETER repeat_penalty 1.1

# Sistema especializado en UCDM
SYSTEM """Eres un asistente especializado en "Un Curso de Milagros" (UCDM). 

ESTRUCTURA OBLIGATORIA DE RESPUESTA:

**HOOK INICIAL: UNA PREGUNTA O ANÉCDOTA PARA ENGANCHAR**
- Pregunta profunda que conecte emocionalmente
- Ejemplos: "¿Y si te dijera que...", "¿Has notado que..."

**APLICACIÓN PRÁCTICA: PASOS VIVOS Y VARIADOS**
- Exactamente 3 pasos concretos y accionables
- Incluye ejemplos cotidianos reales
- Varía títulos: "Paso 1/2/3", "Exploración", "Práctica"

**INTEGRACIÓN EXPERIENCIAL: CONEXIÓN VIVA Y REFLEXIVA**
- Conecta con experiencias personales
- Incluye preguntas reflexivas profundas
- Referencias a enseñanzas del Curso

**CIERRE MOTIVADOR: UN MILAGRO FINAL**
- Invitación inspiradora a la acción
- Motivación para práctica continua
- Elementos de esperanza y transformación

PRINCIPIOS UCDM:
- El perdón es la llave de la felicidad
- Los milagros ocurren como expresiones de amor
- La percepción es una elección, no un hecho
- Solo el amor es real; el miedo es ilusión
- La paz de Dios es nuestra herencia

Responde siempre en español, 300-500 palabras, con tono cálido pero profundo."""

# Datos de entrenamiento específicos
ADAPTER {training_file}
'''
        
        modelfile_path = Path(__file__).parent / "Modelfile_with_training"
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        self.logger.info(f"Modelfile con entrenamiento creado: {modelfile_path}")
        return str(modelfile_path)
    
    def generate_complete_training_setup(self) -> bool:
        """Generar setup completo de entrenamiento"""
        self.logger.info("=== GENERANDO SETUP COMPLETO DE ENTRENAMIENTO ===")
        
        # 1. Generar conversaciones
        conversations = self.generate_training_conversations()
        if not conversations:
            self.logger.error("No se pudieron generar conversaciones")
            return False
        
        # 2. Crear archivo de entrenamiento
        training_file = self.create_ollama_training_file(conversations)
        
        # 3. Crear Modelfile con entrenamiento
        modelfile_with_training = self.create_modelfile_with_training(training_file)
        
        # 4. Crear script de entrenamiento
        self.create_training_script(training_file, modelfile_with_training)
        
        # 5. Mostrar estadísticas
        self.show_training_statistics(conversations)
        
        return True
    
    def create_training_script(self, training_file: str, modelfile_path: str) -> None:
        """Crear script para ejecutar el entrenamiento"""
        
        script_content = f'''#!/usr/bin/env python3
"""
Script para entrenar el modelo UCDM con fine-tuning
"""

import subprocess
import sys
from pathlib import Path

def train_ucdm_model():
    """Entrenar modelo UCDM con datos específicos"""
    
    print("🚀 Iniciando entrenamiento del modelo UCDM...")
    
    try:
        # Crear modelo con fine-tuning
        result = subprocess.run([
            'ollama', 'create', 'ucdm-gemma-trained', 
            '-f', '{modelfile_path}'
        ], capture_output=True, text=True, timeout=3600)  # 1 hora
        
        if result.returncode == 0:
            print("✅ Modelo entrenado exitosamente: ucdm-gemma-trained")
            
            # Probar modelo
            print("🧪 Probando modelo entrenado...")
            test_result = subprocess.run([
                'ollama', 'run', 'ucdm-gemma-trained',
                'Explícame la Lección 1 de UCDM'
            ], capture_output=True, text=True, timeout=120)
            
            if test_result.returncode == 0:
                print("✅ Modelo respondiendo correctamente")
                print("📝 Respuesta de prueba:")
                print("-" * 50)
                print(test_result.stdout)
                return True
            else:
                print(f"❌ Error probando modelo: {{test_result.stderr}}")
                return False
        else:
            print(f"❌ Error entrenando modelo: {{result.stderr}}")
            return False
            
    except Exception as e:
        print(f"❌ Error en entrenamiento: {{str(e)}}")
        return False

def main():
    print("="*60)
    print("🌟 ENTRENAMIENTO DEL MODELO UCDM")
    print("="*60)
    
    print(f"📊 Datos de entrenamiento: {training_file}")
    print(f"🔧 Configuración: {modelfile_path}")
    print(f"💾 Tamaño del dataset: {{Path('{training_file}').stat().st_size // 1024}} KB")
    
    if train_ucdm_model():
        print("\\n🎉 ENTRENAMIENTO COMPLETADO")
        print("💡 Usa: ollama run ucdm-gemma-trained")
    else:
        print("\\n❌ ENTRENAMIENTO FALLIDO")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
'''
        
        script_path = Path(__file__).parent / "train_model.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        self.logger.info(f"Script de entrenamiento creado: {script_path}")
    
    def show_training_statistics(self, conversations: List[Dict]) -> None:
        """Mostrar estadísticas del dataset de entrenamiento"""
        print(f"\n{'='*60}")
        print("📊 ESTADÍSTICAS DEL DATASET DE ENTRENAMIENTO")
        print(f"{'='*60}")
        
        # Contar por tipos
        type_counts = {}
        total_tokens = 0
        
        for conv in conversations:
            conv_type = conv['metadata'].get('type', 'unknown')
            type_counts[conv_type] = type_counts.get(conv_type, 0) + 1
            
            # Estimar tokens (aproximadamente 4 chars = 1 token)
            text_length = len(conv['prompt']) + len(conv['response'])
            total_tokens += text_length // 4
        
        print(f"\n📈 COMPOSICIÓN DEL DATASET:")
        print(f"   Total de conversaciones: {len(conversations)}")
        print(f"   Tokens estimados: {total_tokens:,}")
        
        print(f"\n📋 POR TIPO DE CONSULTA:")
        for conv_type, count in type_counts.items():
            percentage = (count / len(conversations)) * 100
            print(f"   {conv_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n🎯 OBJETIVOS DEL ENTRENAMIENTO:")
        print("   • Estructura consistente de respuestas")
        print("   • Integración del contenido real de UCDM")
        print("   • Variación en lenguaje y ejemplos")
        print("   • Aplicación práctica personalizada")
        
        print(f"\n📝 ARCHIVOS GENERADOS:")
        print(f"   • ucdm_training_data.jsonl - Dataset principal")
        print(f"   • Modelfile_with_training - Configuración")
        print(f"   • train_model.py - Script de entrenamiento")

def main():
    """Función principal"""
    generator = OllamaFineTuningDatasetGenerator()
    
    if generator.generate_complete_training_setup():
        print("\n✅ SETUP DE ENTRENAMIENTO COMPLETADO")
        print("\n🚀 PASOS SIGUIENTES:")
        print("1. Ejecuta: python ollama/train_model.py")
        print("2. Espera a que complete el entrenamiento")
        print("3. Prueba: ollama run ucdm-gemma-trained")
        return 0
    else:
        print("\n❌ ERROR EN SETUP DE ENTRENAMIENTO")
        return 1

if __name__ == "__main__":
    exit(main())