#!/usr/bin/env python3
"""
Generador de dataset UCDM con estructura template personalizada
Crea dataset de entrenamiento con la estructura específica solicitada:
- HOOK INICIAL: Pregunta o anécdota enganchadora
- APLICACIÓN PRÁCTICA: Pasos vivos y variados
- INTEGRACIÓN EXPERIENCIAL: Conexión viva y reflexiva
- CIERRE MOTIVADOR: Un milagro final
"""

import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

class UCDMDatasetGenerator:
    """Generador de dataset con estructura template UCDM"""
    
    def __init__(self):
        self.lessons_index = {}
        self.concept_index = {}
        self.date_mapper = {}
        self.templates = self.load_response_templates()
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_response_templates(self) -> Dict:
        """Cargar templates de respuesta personalizados"""
        return {
            "hooks_iniciales": [
                "¿Y si te dijera que",
                "¿Imaginas cómo",
                "¿Te has preguntado por qué",
                "¿Qué pasaría si",
                "¿Has notado que",
                "¿Sabías que",
                "¿No es curioso que",
                "¿Alguna vez has sentido que"
            ],
            "aplicacion_headers": [
                "Paso 1: Reconoce",
                "Paso 2: Observa", 
                "Paso 3: Extiende",
                "Exploración 1:",
                "Desafío 2:",
                "Práctica 3:",
                "Ejercicio 1:",
                "Experiencia 2:",
                "Aplicación 3:"
            ],
            "integracion_conectores": [
                "Conecta esto con tu vida:",
                "Reflexiona sobre esto:",
                "Lleva esto a tu experiencia:",
                "Piensa en cómo esto se relaciona:",
                "Considera tu propia vida:",
                "Aplica esto personalmente:",
                "En tu experiencia diaria:"
            ],
            "cierres_motivadores": [
                "Lleva esto contigo hoy y observa el milagro",
                "Hoy, vive esta lección como un experimento vivo",
                "¿Estás listo para más? Comparte tu experiencia",
                "Que este día sea un testimonio de la verdad",
                "Permite que esta comprensión transforme tu día",
                "Observa cómo los milagros surgen cuando aplicamos esto",
                "El mundo necesita tu luz; compártela sin miedo",
                "Cada momento es una oportunidad para elegir de nuevo"
            ],
            "preguntas_reflexivas": [
                "¿Cómo se siente esto en tu corazón?",
                "¿Qué cambiaría en tu vida si esto fuera verdad?",
                "¿Puedes ver cómo esto libera viejas cadenas?",
                "¿Notas la paz que surge de esta comprensión?",
                "¿Sientes la libertad que esto trae?",
                "¿Cómo transforma esto tu perspectiva?",
                "¿Qué milagro está esperando nacer en ti?"
            ]
        }
    
    def load_extracted_data(self) -> bool:
        """Cargar datos extraídos (lecciones, conceptos, fechas)"""
        try:
            # Cargar índice completo
            index_file = INDICES_DIR / "ucdm_comprehensive_index.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.lessons_index = data.get("lesson_details", {})
                self.concept_index = data.get("concept_index", {})
                self.date_mapper = data.get("date_mapping", {})
                
                self.logger.info(f"Cargados: {len(self.lessons_index)} lecciones, {len(self.concept_index)} conceptos")
                return True
            else:
                self.logger.error(f"No se encontró el índice: {index_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cargando datos: {str(e)}")
            return False
    
    def get_lesson_content(self, lesson_num: int) -> Optional[str]:
        """Obtener contenido de una lección específica"""
        if str(lesson_num) not in self.lessons_index:
            return None
        
        lesson_data = self.lessons_index[str(lesson_num)]
        lesson_file = PROCESSED_DATA_DIR / lesson_data['file_path']
        
        if lesson_file.exists():
            with open(lesson_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer solo el contenido de la lección (después de las líneas de metadatos)
            lines = content.split('\\n')
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith('=') and i > 0:
                    content_start = i + 1
                    break
            
            return '\\n'.join(lines[content_start:]).strip()
        
        return None
    
    def generate_hook_inicial(self, lesson_num: int, lesson_title: str, lesson_content: str) -> str:
        """Generar HOOK INICIAL personalizado"""
        hook_start = random.choice(self.templates["hooks_iniciales"])
        
        # Extraer conceptos clave de la lección
        key_concepts = []
        if str(lesson_num) in self.lessons_index:
            key_concepts = self.lessons_index[str(lesson_num)].get('concepts', [])
        
        # Crear hooks contextualizados según el contenido
        if 'amor' in lesson_title.lower() or 'amor' in key_concepts:
            hook_examples = [
                f"{hook_start} el amor es la única realidad que existe, y todo lo demás son solo sombras que se desvanecen?",
                f"{hook_start} cada momento de amor que experimentas es un destello de tu verdadera naturaleza infinita?",
                f"{hook_start} el amor no es algo que buscas fuera, sino algo que reconoces que ya eres?"
            ]
        elif 'miedo' in lesson_title.lower() or 'miedo' in key_concepts:
            hook_examples = [
                f"{hook_start} el miedo es simplemente amor pidiendo ser reconocido y sanado?",
                f"{hook_start} cada miedo que enfrentas es una oportunidad para elegir la paz en su lugar?",
                f"{hook_start} el miedo es solo una ilusión que se disuelve ante la presencia del amor?"
            ]
        elif 'paz' in lesson_title.lower() or 'paz' in key_concepts:
            hook_examples = [
                f"{hook_start} la paz no es algo que logras, sino algo que recuerdas que ya tienes?",
                f"{hook_start} en cada momento caótico, hay un centro de perfecta calma esperando ser descubierto?",
                f"{hook_start} la paz de Dios está siempre presente, solo cubierta por nuestros pensamientos agitados?"
            ]
        else:
            # Hook genérico basado en principios de UCDM
            hook_examples = [
                f"{hook_start} un simple cambio de percepción podría transformar tu día caótico en un milagro de paz?",
                f"{hook_start} la verdad que buscas fuera de ti en realidad ya está completa dentro de ti?",
                f"{hook_start} cada problema que enfrentas es una oportunidad disfrazada para despertar?"
            ]
        
        return random.choice(hook_examples)
    
    def generate_aplicacion_practica(self, lesson_num: int, lesson_title: str, lesson_content: str) -> str:
        """Generar APLICACIÓN PRÁCTICA con pasos variados"""
        
        # Obtener 3 headers diferentes para los pasos
        available_headers = self.templates["aplicacion_headers"].copy()
        random.shuffle(available_headers)
        step_headers = available_headers[:3]
        
        aplicacion = "APLICACIÓN PRÁCTICA: PASOS VIVOS Y VARIADOS\\n\\n"
        
        # Paso 1: Introducción accionable con ejemplo
        aplicacion += f"{step_headers[0]} - Introducción accionable: "
        
        if 'lección' in lesson_title.lower():
            lesson_quote = f'"{lesson_title}"'
            aplicacion += f"Comienza el día repitiendo: {lesson_quote}. "
        else:
            aplicacion += f"Inicia tu práctica recordando: \"{lesson_title}\". "
        
        aplicacion += "Imagina esta verdad como una luz que se extiende desde tu corazón, tocando cada situación que enfrentas hoy.\\n\\n"
        
        # Paso 2: Ejercicio interactivo
        aplicacion += f"{step_headers[1]} - Ejercicio interactivo: "
        pregunta_interactiva = "¿Qué pasa si pruebas esto ahora mismo?"
        
        if 'perdón' in lesson_title.lower():
            aplicacion += f"Cuando surja un conflicto, pausa y pregúntate: '{pregunta_interactiva}' Aplica el perdón como UCDM enseña: reconoce que lo que ves es proyección de tu mente. "
        elif 'paz' in lesson_title.lower():
            aplicacion += f"En momentos de estrés, detente y afirma: 'Elijo la paz en lugar de esto'. {pregunta_interactiva} Visualiza la situación envuelta en luz dorada. "
        else:
            aplicacion += f"Durante el día, cuando notes resistencia, aplica esta lección: {pregunta_interactiva} Observa cómo cambia tu experiencia. "
        
        aplicacion += "Como dice el Curso, 'Los milagros ocurren naturalmente como expresiones de amor'.\\n\\n"
        
        # Paso 3: Variaciones creativas
        aplicacion += f"{step_headers[2]} - Variaciones creativas:\\n"
        aplicacion += "• **Práctica matutina**: Al despertar, dedica 5 minutos a interiorizar esta verdad\\n"
        aplicacion += "• **Aplicación inmediata**: En conversaciones difíciles, recuerda silenciosamente esta lección\\n"
        aplicacion += "• **Reflexión nocturna**: Antes de dormir, revisa cómo aplicaste esta enseñanza durante el día"
        
        return aplicacion
    
    def generate_integracion_experiencial(self, lesson_num: int, lesson_title: str, lesson_content: str) -> str:
        """Generar INTEGRACIÓN EXPERIENCIAL personalizada"""
        
        conector = random.choice(self.templates["integracion_conectores"])
        pregunta_reflexiva = random.choice(self.templates["preguntas_reflexivas"])
        
        integracion = "INTEGRACIÓN EXPERIENCIAL: CONEXIÓN VIVA Y REFLEXIVA\\n\\n"
        
        # Conexión personal con twist
        integracion += f"**Conexión personal con twist**: {conector} "
        
        if 'miedo' in lesson_title.lower():
            integracion += "Recuerda un momento reciente donde el miedo te paralizó. ¿Cómo habría cambiado esa experiencia si hubieras recordado que 'no hay nada que temer'? "
        elif 'amor' in lesson_title.lower():
            integracion += "Piensa en alguien con quien tienes dificultades. ¿Qué cambiaría si pudieras ver más allá de sus defensas hacia su esencia amorosa? "
        elif 'perdón' in lesson_title.lower():
            integracion += "Considera una herida del pasado que aún te duele. ¿Cómo se sentiría liberarte de esa carga y elegir la paz en su lugar? "
        else:
            integracion += "Reflexiona sobre un desafío actual en tu vida. ¿Cómo cambiaria tu perspectiva si aplicaras esta enseñanza del Curso? "
        
        integracion += "UCDM nos recuerda que 'la percepción es una elección, no un hecho'.\\n\\n"
        
        # Transformación esperada con invitación
        integracion += f"**Transformación esperada con invitación**: {pregunta_reflexiva} "
        integracion += "Esta comprensión lleva a una libertad profunda, liberando patrones viejos que ya no te sirven. "
        integracion += "Experimenta con esta nueva perspectiva y observa los cambios sutiles pero poderosos que surgen."
        
        return integracion
    
    def generate_cierre_motivador(self, lesson_num: int, lesson_title: str, lesson_content: str) -> str:
        """Generar CIERRE MOTIVADOR inspirador"""
        
        cierre_base = random.choice(self.templates["cierres_motivadores"])
        
        cierre = "CIERRE MOTIVADOR: UN MILAGRO FINAL\\n\\n"
        cierre += f"{cierre_base}. "
        
        # Agregar elemento específico según el tema
        if 'práctica' in lesson_title.lower():
            cierre += "Recuerda: cada práctica es un paso hacia el despertar. Tu dedicación ilumina no solo tu camino, sino el de todos tus hermanos."
        elif any(word in lesson_title.lower() for word in ['dios', 'divino', 'santo']):
            cierre += "Lo divino en ti reconoce lo divino en todo. Esta es la base de todos los milagros."
        else:
            cierre += "¿Estás listo para más? El Curso nos invita a profundizar cada día. Comparte tu luz y experimenta el gozo de dar y recibir como uno."
        
        return cierre
    
    def generate_complete_response(self, lesson_num: int, query_type: str = "leccion_diaria") -> str:
        """Generar respuesta completa con estructura template"""
        
        if str(lesson_num) not in self.lessons_index:
            return None
        
        lesson_data = self.lessons_index[str(lesson_num)]
        lesson_title = lesson_data['title']
        lesson_content = self.get_lesson_content(lesson_num) or ""
        
        # Generar cada sección
        hook = self.generate_hook_inicial(lesson_num, lesson_title, lesson_content)
        aplicacion = self.generate_aplicacion_practica(lesson_num, lesson_title, lesson_content)
        integracion = self.generate_integracion_experiencial(lesson_num, lesson_title, lesson_content)
        cierre = self.generate_cierre_motivador(lesson_num, lesson_title, lesson_content)
        
        # Construir respuesta completa
        response = f"**HOOK INICIAL: UNA PREGUNTA O ANÉCDOTA PARA ENGANCHAR**\\n\\n"
        response += f"{hook}\\n\\n"
        response += f"**{aplicacion}**\\n\\n"
        response += f"**{integracion}**\\n\\n"
        response += f"**{cierre}**"
        
        return response
    
    def generate_training_examples(self) -> List[Dict]:
        """Generar ejemplos de entrenamiento completos"""
        
        training_examples = []
        
        # Tipo 1: Lecciones diarias por número
        for lesson_num in self.lessons_index.keys():
            lesson_num_int = int(lesson_num)
            lesson_data = self.lessons_index[lesson_num]
            
            # Generar múltiples variaciones de pregunta para cada lección
            queries = [
                f"Explícame la Lección {lesson_num_int}",
                f"¿Qué enseña la Lección {lesson_num_int} del UCDM?",
                f"Háblame sobre la Lección {lesson_num_int}",
                f"Quiero estudiar la Lección {lesson_num_int}",
                f"Lección {lesson_num_int} del Curso de Milagros"
            ]
            
            for query in queries:
                response = self.generate_complete_response(lesson_num_int)
                if response:
                    training_examples.append({
                        "instruction": query,
                        "input": "",
                        "output": response,
                        "metadata": {
                            "lesson_number": lesson_num_int,
                            "lesson_title": lesson_data['title'],
                            "query_type": "lesson_specific",
                            "concepts": lesson_data.get('concepts', [])
                        }
                    })
        
        # Tipo 2: Lección del día (por fecha)
        date_queries = [
            "¿Cuál es la lección de hoy?",
            "Lección del día",
            "¿Qué lección del UCDM corresponde a hoy?",
            "Quiero la lección de hoy del Curso de Milagros",
            "Enséñame la lección diaria de UCDM"
        ]
        
        # Generar para diferentes fechas del año
        for date_key, lesson_num in list(self.date_mapper.items())[:20]:  # Primeras 20 fechas como ejemplo
            for query in date_queries:
                response = self.generate_complete_response(lesson_num)
                if response:
                    training_examples.append({
                        "instruction": query,
                        "input": f"Fecha: {date_key}",
                        "output": response,
                        "metadata": {
                            "lesson_number": lesson_num,
                            "date": date_key,
                            "query_type": "daily_lesson"
                        }
                    })
        
        # Tipo 3: Búsqueda por conceptos
        concept_queries = [
            "Háblame sobre el perdón en UCDM",
            "¿Qué enseña el Curso sobre el amor?",
            "Explícame el concepto de miedo según UCDM",
            "¿Cómo entender la paz según el Curso de Milagros?",
            "¿Qué dice UCDM sobre los milagros?"
        ]
        
        for concept, lessons in list(self.concept_index.items())[:10]:  # Primeros 10 conceptos
            if lessons and concept in ['amor', 'perdon', 'miedo', 'paz', 'milagro']:
                lesson_num = lessons[0]  # Tomar la primera lección del concepto
                query = f"Háblame sobre {concept} en UCDM"
                response = self.generate_complete_response(lesson_num)
                if response:
                    training_examples.append({
                        "instruction": query,
                        "input": f"Concepto: {concept}",
                        "output": response,
                        "metadata": {
                            "concept": concept,
                            "lesson_number": lesson_num,
                            "query_type": "concept_based"
                        }
                    })
        
        # Tipo 4: Reflexiones especiales
        reflection_queries = [
            "Necesito una reflexión de UCDM para antes de dormir",
            "Dame una enseñanza del Curso para momentos difíciles",
            "¿Qué me puede enseñar UCDM sobre la ansiedad?",
            "Quiero una reflexión nocturna del Curso de Milagros",
            "¿Cómo puedo aplicar UCDM en mi vida diaria?"
        ]
        
        for query in reflection_queries:
            # Usar una lección aleatoria para generar la reflexión
            random_lesson = random.choice(list(self.lessons_index.keys()))
            response = self.generate_complete_response(int(random_lesson))
            if response:
                training_examples.append({
                    "instruction": query,
                    "input": "",
                    "output": response,
                    "metadata": {
                        "query_type": "reflection",
                        "lesson_number": int(random_lesson)
                    }
                })
        
        self.logger.info(f"Generados {len(training_examples)} ejemplos de entrenamiento")
        return training_examples
    
    def save_training_dataset(self, examples: List[Dict]) -> None:
        """Guardar dataset de entrenamiento en formato JSONL"""
        
        # Crear dataset principal
        dataset_file = TRAINING_DATA_DIR / "ucdm_structured_dataset.jsonl"
        dataset_file.parent.mkdir(exist_ok=True)
        
        with open(dataset_file, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\\n')
        
        # Crear dataset para Ollama (formato simplificado)
        ollama_dataset_file = TRAINING_DATA_DIR / "ucdm_ollama_dataset.jsonl"
        
        with open(ollama_dataset_file, 'w', encoding='utf-8') as f:
            for example in examples:
                ollama_format = {
                    "prompt": example["instruction"],
                    "response": example["output"]
                }
                f.write(json.dumps(ollama_format, ensure_ascii=False) + '\\n')
        
        # Crear estadísticas del dataset
        stats = {
            "total_examples": len(examples),
            "query_types": {},
            "lessons_covered": set(),
            "concepts_covered": set(),
            "creation_date": str(datetime.now())
        }
        
        for example in examples:
            metadata = example.get("metadata", {})
            query_type = metadata.get("query_type", "unknown")
            stats["query_types"][query_type] = stats["query_types"].get(query_type, 0) + 1
            
            if "lesson_number" in metadata:
                stats["lessons_covered"].add(metadata["lesson_number"])
            
            if "concept" in metadata:
                stats["concepts_covered"].add(metadata["concept"])
            
            if "concepts" in metadata:
                stats["concepts_covered"].update(metadata["concepts"])
        
        # Convertir sets a listas para JSON
        stats["lessons_covered"] = sorted(list(stats["lessons_covered"]))
        stats["concepts_covered"] = sorted(list(stats["concepts_covered"]))
        
        stats_file = TRAINING_DATA_DIR / "dataset_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Dataset guardado en: {dataset_file}")
        self.logger.info(f"Dataset Ollama en: {ollama_dataset_file}")
        self.logger.info(f"Estadísticas en: {stats_file}")

def main():
    """Función principal del generador de dataset"""
    generator = UCDMDatasetGenerator()
    
    # Cargar datos extraídos
    if not generator.load_extracted_data():
        print("❌ Error: No se pudieron cargar los datos extraídos")
        print("   Ejecuta primero los scripts de extracción e indexación")
        return 1
    
    print("🔄 Generando dataset de entrenamiento con estructura template...")
    
    # Generar ejemplos de entrenamiento
    training_examples = generator.generate_training_examples()
    
    if not training_examples:
        print("❌ Error: No se pudieron generar ejemplos de entrenamiento")
        return 1
    
    # Guardar dataset
    generator.save_training_dataset(training_examples)
    
    # Mostrar estadísticas
    print(f"\\n{'='*60}")
    print("GENERACIÓN DE DATASET COMPLETADA")
    print(f"{'='*60}")
    
    print(f"\\n📊 ESTADÍSTICAS DEL DATASET:")
    
    # Contar por tipos
    query_types = {}
    for example in training_examples:
        qtype = example.get("metadata", {}).get("query_type", "unknown")
        query_types[qtype] = query_types.get(qtype, 0) + 1
    
    print(f"   Total de ejemplos: {len(training_examples)}")
    print(f"   Tipos de consulta:")
    for qtype, count in query_types.items():
        print(f"     - {qtype}: {count} ejemplos")
    
    # Mostrar ejemplo de la estructura
    if training_examples:
        example = training_examples[0]
        print(f"\\n📝 EJEMPLO DE ESTRUCTURA GENERADA:")
        print(f"   Consulta: {example['instruction']}")
        print(f"   Respuesta (primeras 200 chars): {example['output'][:200]}...")
        
        # Verificar que contiene todas las secciones
        response = example['output']
        sections_check = {
            "HOOK INICIAL": "✓" if "HOOK INICIAL" in response else "✗",
            "APLICACIÓN PRÁCTICA": "✓" if "APLICACIÓN PRÁCTICA" in response else "✗", 
            "INTEGRACIÓN EXPERIENCIAL": "✓" if "INTEGRACIÓN EXPERIENCIAL" in response else "✗",
            "CIERRE MOTIVADOR": "✓" if "CIERRE MOTIVADOR" in response else "✗"
        }
        
        print(f"\\n📋 VERIFICACIÓN DE ESTRUCTURA:")
        for section, status in sections_check.items():
            print(f"   {status} {section}")
    
    print(f"\\n✅ ARCHIVOS GENERADOS:")
    print(f"   - Dataset principal: {TRAINING_DATA_DIR / 'ucdm_structured_dataset.jsonl'}")
    print(f"   - Dataset Ollama: {TRAINING_DATA_DIR / 'ucdm_ollama_dataset.jsonl'}")
    print(f"   - Estadísticas: {TRAINING_DATA_DIR / 'dataset_statistics.json'}")
    
    success_rate = len(training_examples) / (len(generator.lessons_index) * 3)  # Promedio 3 ejemplos por lección
    print(f"\\n⭐ DATASET COMPLETADO: {len(training_examples)} ejemplos generados")
    
    return 0

if __name__ == "__main__":
    exit(main())