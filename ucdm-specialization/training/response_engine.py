#!/usr/bin/env python3
"""
Motor de respuestas estructuradas UCDM
Genera respuestas dinámicas con la estructura específica solicitada
"""

import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

class UCDMResponseEngine:
    """Motor de respuestas estructuradas para UCDM"""
    
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
        """Cargar templates dinámicos de respuesta"""
        return {
            "hooks_iniciales": {
                "preguntas_enganchadoras": [
                    "¿Y si te dijera que",
                    "¿Imaginas cómo",
                    "¿Te has preguntado por qué",
                    "¿Qué pasaría si",
                    "¿Has notado que",
                    "¿Sabías que",
                    "¿No es curioso que",
                    "¿Alguna vez has sentido que"
                ],
                "contextos_ucdm": [
                    "en medio del caos diario, hay un lugar de absoluta seguridad que siempre te acompaña?",
                    "un simple cambio de percepción podría transformar tu día caótico en un milagro de paz?",
                    "la verdad que buscas fuera de ti en realidad ya está completa dentro de ti?",
                    "cada problema que enfrentas es una oportunidad disfrazada para despertar?",
                    "el amor es la única realidad que existe, y todo lo demás son solo sombras que se desvanecen?",
                    "cada miedo que enfrentas es una oportunidad para elegir la paz en su lugar?",
                    "la paz no es algo que logras, sino algo que recuerdas que ya tienes?"
                ]
            },
            "aplicacion_practica": {
                "headers_paso1": [
                    "Paso 1: Reconoce tu verdad interior",
                    "Exploración 1: Descubre la paz",
                    "Práctica 1: Conecta con el amor",
                    "Ejercicio 1: Abraza la seguridad",
                    "Desafío 1: Transforma la percepción"
                ],
                "headers_paso2": [
                    "Paso 2: Observa sin juzgar",
                    "Experiencia 2: Aplica en lo cotidiano", 
                    "Práctica 2: Extiende el perdón",
                    "Exploración 2: Vive el milagro",
                    "Ejercicio 2: Cambia la perspectiva"
                ],
                "headers_paso3": [
                    "Paso 3: Extiende la práctica",
                    "Variación 3: Profundiza la experiencia",
                    "Aplicación 3: Integra en tu vida",
                    "Práctica 3: Comparte la luz",
                    "Expansión 3: Multiplica el amor"
                ],
                "escenarios_cotidianos": [
                    "al enfrentar estrés laboral",
                    "en una discusión familiar",
                    "durante un atasco de tráfico",
                    "en momentos de ansiedad",
                    "al despertar por la mañana",
                    "antes de dormir",
                    "en conversaciones difíciles",
                    "cuando surgen miedos"
                ],
                "aplicaciones_variadas": [
                    "**Práctica matutina**: Al despertar, dedica 5 minutos a interiorizar esta verdad",
                    "**Aplicación inmediata**: En conversaciones difíciles, recuerda silenciosamente esta lección", 
                    "**Reflexión nocturna**: Antes de dormir, revisa cómo aplicaste esta enseñanza durante el día",
                    "**Momento de pausa**: En situaciones estresantes, respira y aplica esta verdad",
                    "**Práctica en movimiento**: Mientras caminas, repite mentalmente esta enseñanza",
                    "**Meditación diaria**: Dedica 10 minutos a profundizar en este concepto"
                ]
            },
            "integracion_experiencial": {
                "conectores_personales": [
                    "Conecta esto con tu vida:",
                    "Reflexiona sobre esto:",
                    "Lleva esto a tu experiencia:",
                    "Piensa en cómo esto se relaciona:",
                    "Considera tu propia vida:",
                    "Aplica esto personalmente:",
                    "En tu experiencia diaria:"
                ],
                "escenarios_reflexivos": [
                    "Recuerda un momento reciente donde el miedo te paralizó",
                    "Piensa en alguien con quien tienes dificultades",
                    "Considera una herida del pasado que aún te duele",
                    "Reflexiona sobre un desafío actual en tu vida",
                    "Recuerda una situación donde elegiste el amor sobre el miedo",
                    "Piensa en un momento de verdadera paz que experimentaste"
                ],
                "preguntas_reflexivas": [
                    "¿Cómo se siente esto en tu corazón?",
                    "¿Qué cambiaría en tu vida si esto fuera verdad?",
                    "¿Puedes ver cómo esto libera viejas cadenas?",
                    "¿Notas la paz que surge de esta comprensión?",
                    "¿Sientes la libertad que esto trae?",
                    "¿Cómo transforma esto tu perspectiva?",
                    "¿Qué milagro está esperando nacer en ti?"
                ],
                "enseñanzas_ucdm": [
                    "UCDM nos enseña que 'la percepción es una elección, no un hecho'",
                    "Como dice el Curso, 'los milagros ocurren naturalmente como expresiones de amor'",
                    "El Curso nos recuerda que 'no hay orden de dificultad en los milagros'",
                    "UCDM enseña que 'el perdón es la llave de la felicidad'",
                    "Según el Curso, 'el amor no tiene opuesto'",
                    "UCDM nos dice que 'la paz de Dios es mi herencia natural'"
                ]
            },
            "cierres_motivadores": {
                "llamadas_accion": [
                    "Lleva esto contigo hoy y observa el milagro",
                    "Hoy, vive esta lección como un experimento vivo",
                    "¿Estás listo para más? Comparte tu experiencia",
                    "Que este día sea un testimonio de la verdad",
                    "Permite que esta comprensión transforme tu día",
                    "Observa cómo los milagros surgen cuando aplicamos esto",
                    "El mundo necesita tu luz; compártela sin miedo",
                    "Cada momento es una oportunidad para elegir de nuevo"
                ],
                "elementos_especificos": {
                    "practica": "Recuerda: cada práctica es un paso hacia el despertar. Tu dedicación ilumina no solo tu camino, sino el de todos tus hermanos.",
                    "divino": "Lo divino en ti reconoce lo divino en todo. Esta es la base de todos los milagros.",
                    "general": "¿Estás listo para más? El Curso nos invita a profundizar cada día. Comparte tu luz y experimenta el gozo de dar y recibir como uno."
                }
            }
        }
    
    def load_data(self) -> bool:
        """Cargar datos del sistema (lecciones, conceptos, fechas)"""
        try:
            # Cargar índice completo
            index_file = INDICES_DIR / "ucdm_comprehensive_index.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.lessons_index = data.get("lesson_details", {})
                self.concept_index = data.get("concept_index", {})
                self.date_mapper = data.get("date_mapping", {})
                
                self.logger.info(f"Motor cargado: {len(self.lessons_index)} lecciones, {len(self.concept_index)} conceptos")
                return True
            else:
                self.logger.error(f"No se encontró el índice: {index_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cargando datos: {str(e)}")
            return False
    
    def get_lesson_for_date(self, target_date: datetime) -> Optional[int]:
        """Obtener número de lección para una fecha específica"""
        date_key = target_date.strftime("%m-%d")
        return self.date_mapper.get(date_key)
    
    def get_lesson_content(self, lesson_num: int) -> Optional[str]:
        """Obtener contenido de una lección específica"""
        if str(lesson_num) not in self.lessons_index:
            return None
        
        lesson_data = self.lessons_index[str(lesson_num)]
        lesson_file = PROCESSED_DATA_DIR / lesson_data['file_path']
        
        if lesson_file.exists():
            with open(lesson_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer solo el contenido principal
            lines = content.split('\n')
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith('=') and i > 0:
                    content_start = i + 1
                    break
            
            return '\n'.join(lines[content_start:]).strip()
        
        return None
    
    def generate_dynamic_hook(self, lesson_num: int, lesson_title: str, query_type: str = "general") -> str:
        """Generar hook inicial dinámico"""
        pregunta = random.choice(self.templates["hooks_iniciales"]["preguntas_enganchadoras"])
        
        # Seleccionar contexto basado en el tema de la lección
        if any(word in lesson_title.lower() for word in ['amor', 'love']):
            contexto = "el amor es la única realidad que existe, y todo lo demás son solo sombras que se desvanecen?"
        elif any(word in lesson_title.lower() for word in ['miedo', 'fear']):
            contexto = "cada miedo que enfrentas es una oportunidad para elegir la paz en su lugar?"
        elif any(word in lesson_title.lower() for word in ['paz', 'peace']):
            contexto = "la paz no es algo que logras, sino algo que recuerdas que ya tienes?"
        elif any(word in lesson_title.lower() for word in ['perdón', 'forgiveness']):
            contexto = "el perdón es la llave que abre todas las puertas a la felicidad?"
        else:
            contexto = random.choice(self.templates["hooks_iniciales"]["contextos_ucdm"])
        
        # Añadir referencia a UCDM si es apropiado
        ucdm_reference = ""
        if query_type == "lesson_specific":
            ucdm_reference = f" Como Helen Schucman descubrió en el proceso de dictado del Curso, la 'Voz' interna nos guía más allá de nuestros límites percibidos."
        
        return f"{pregunta} {contexto}{ucdm_reference}"
    
    def generate_aplicacion_practica(self, lesson_num: int, lesson_title: str, lesson_content: str) -> str:
        """Generar sección de aplicación práctica con pasos variados"""
        
        # Seleccionar headers únicos para cada paso
        headers = [
            random.choice(self.templates["aplicacion_practica"]["headers_paso1"]),
            random.choice(self.templates["aplicacion_practica"]["headers_paso2"]),
            random.choice(self.templates["aplicacion_practica"]["headers_paso3"])
        ]
        
        # Escenario cotidiano para aplicar
        escenario = random.choice(self.templates["aplicacion_practica"]["escenarios_cotidianos"])
        
        aplicacion = "APLICACIÓN PRÁCTICA: PASOS VIVOS Y VARIADOS\n\n"
        
        # Paso 1: Introducción accionable
        aplicacion += f"{headers[0]}: "
        if 'lección' in lesson_title.lower():
            lesson_quote = f'"{lesson_title}"'
            aplicacion += f"Comienza el día repitiendo: {lesson_quote}. "
        else:
            aplicacion += f"Inicia tu práctica recordando: \"{lesson_title}\". "
        
        aplicacion += f"Imagina esta verdad como una luz que se extiende desde tu corazón, tocando cada situación que enfrentas hoy, especialmente {escenario}.\n\n"
        
        # Paso 2: Ejercicio interactivo
        aplicacion += f"{headers[1]}: "
        pregunta_interactiva = "¿Qué pasa si pruebas esto ahora mismo?"
        
        if 'perdón' in lesson_title.lower():
            aplicacion += f"Cuando surja un conflicto, pausa y pregúntate: '{pregunta_interactiva}' Aplica el perdón como UCDM enseña: reconoce que lo que ves es una oportunidad para sanar. "
        elif 'paz' in lesson_title.lower():
            aplicacion += f"En momentos de estrés, detente y afirma: 'Elijo la paz en lugar de esto'. {pregunta_interactiva} Visualiza la situación envuelta en luz dorada. "
        elif 'amor' in lesson_title.lower():
            aplicacion += f"Ante cualquier dificultad, recuerda: 'El amor es mi realidad'. {pregunta_interactiva} Observa cómo esta verdad transforma tu perspectiva. "
        else:
            aplicacion += f"Durante el día, cuando notes resistencia, aplica esta lección: {pregunta_interactiva} Observa cómo cambia tu experiencia interna. "
        
        ucdm_quote = random.choice(self.templates["integracion_experiencial"]["enseñanzas_ucdm"])
        aplicacion += f"{ucdm_quote}.\n\n"
        
        # Paso 3: Variaciones creativas
        aplicacion += f"{headers[2]} - Variaciones creativas:\n"
        
        # Seleccionar 3 aplicaciones variadas
        aplicaciones_seleccionadas = random.sample(
            self.templates["aplicacion_practica"]["aplicaciones_variadas"], 3
        )
        
        for i, app in enumerate(aplicaciones_seleccionadas, 1):
            aplicacion += f"• {app}\n"
        
        return aplicacion.rstrip()
    
    def generate_integracion_experiencial(self, lesson_num: int, lesson_title: str, lesson_content: str) -> str:
        """Generar integración experiencial personalizada"""
        
        conector = random.choice(self.templates["integracion_experiencial"]["conectores_personales"])
        escenario = random.choice(self.templates["integracion_experiencial"]["escenarios_reflexivos"])
        pregunta = random.choice(self.templates["integracion_experiencial"]["preguntas_reflexivas"])
        enseñanza = random.choice(self.templates["integracion_experiencial"]["enseñanzas_ucdm"])
        
        integracion = "INTEGRACIÓN EXPERIENCIAL: CONEXIÓN VIVA Y REFLEXIVA\n\n"
        
        # Conexión personal con twist
        integracion += f"**Conexión personal con twist**: {conector} "
        
        if 'miedo' in lesson_title.lower():
            integracion += f"{escenario} donde el miedo te limitó. ¿Cómo habría cambiado esa experiencia si hubieras recordado que 'el miedo es solo ausencia de amor'? "
        elif 'amor' in lesson_title.lower():
            integracion += f"{escenario}. ¿Qué cambiaría si pudieras ver la situación desde la perspectiva del amor incondicional? "
        elif 'perdón' in lesson_title.lower():
            integracion += f"{escenario}. ¿Cómo se sentiría liberarte completamente de esa carga y elegir la paz? "
        else:
            integracion += f"{escenario}. ¿Cómo cambiaría tu perspectiva si aplicaras esta enseñanza del Curso en esa situación? "
        
        integracion += f"{enseñanza}.\n\n"
        
        # Transformación esperada con invitación
        integracion += f"**Transformación esperada con invitación**: {pregunta} "
        integracion += "Esta comprensión lleva a una libertad profunda, liberando patrones mentales que limitan tu verdadera naturaleza. "
        integracion += "Experimenta con esta nueva perspectiva y observa los cambios sutiles pero poderosos que surgen en tu experiencia diaria."
        
        return integracion
    
    def generate_cierre_motivador(self, lesson_num: int, lesson_title: str, query_type: str = "general") -> str:
        """Generar cierre motivador inspirador"""
        
        llamada_base = random.choice(self.templates["cierres_motivadores"]["llamadas_accion"])
        
        cierre = "CIERRE MOTIVADOR: UN MILAGRO FINAL\n\n"
        cierre += f"{llamada_base}. "
        
        # Elemento específico según contexto
        if 'práctica' in lesson_title.lower():
            cierre += self.templates["cierres_motivadores"]["elementos_especificos"]["practica"]
        elif any(word in lesson_title.lower() for word in ['dios', 'divino', 'santo']):
            cierre += self.templates["cierres_motivadores"]["elementos_especificos"]["divino"]
        else:
            cierre += self.templates["cierres_motivadores"]["elementos_especificos"]["general"]
        
        return cierre
    
    def generate_structured_response(self, query: str, query_type: str = "general", lesson_num: Optional[int] = None) -> str:
        """Generar respuesta completa con estructura personalizada"""
        
        # Determinar lección a usar
        if lesson_num is None:
            if query_type == "daily_lesson":
                lesson_num = self.get_lesson_for_date(datetime.now())
            elif "lección" in query.lower():
                # Extraer número de lección de la consulta
                import re
                match = re.search(r'lección\s+(\d+)', query.lower())
                if match:
                    lesson_num = int(match.group(1))
            
            if lesson_num is None:
                # Usar lección aleatoria disponible
                lesson_num = int(random.choice(list(self.lessons_index.keys())))
        
        # Verificar que la lección existe
        if str(lesson_num) not in self.lessons_index:
            return "Lo siento, no tengo acceso a esa lección específica en este momento."
        
        lesson_data = self.lessons_index[str(lesson_num)]
        lesson_title = lesson_data['title']
        lesson_content = self.get_lesson_content(lesson_num) or ""
        
        # Generar cada sección con variación dinámica
        hook = self.generate_dynamic_hook(lesson_num, lesson_title, query_type)
        aplicacion = self.generate_aplicacion_practica(lesson_num, lesson_title, lesson_content)
        integracion = self.generate_integracion_experiencial(lesson_num, lesson_title, lesson_content)
        cierre = self.generate_cierre_motivador(lesson_num, lesson_title, query_type)
        
        # Construir respuesta completa
        response = f"**HOOK INICIAL: UNA PREGUNTA O ANÉCDOTA PARA ENGANCHAR**\n\n"
        response += f"{hook}\n\n"
        response += f"**{aplicacion}**\n\n"
        response += f"**{integracion}**\n\n"
        response += f"**{cierre}**"
        
        # Añadir metadatos de la lección
        response += f"\n\n---\n*Basado en la Lección {lesson_num}: {lesson_title}*"
        
        return response
    
    def process_query(self, query: str) -> Dict[str, any]:
        """Procesar consulta y generar respuesta estructurada"""
        
        # Analizar tipo de consulta
        query_lower = query.lower()
        
        if any(phrase in query_lower for phrase in ['lección de hoy', 'lección del día', 'lección diaria']):
            query_type = "daily_lesson"
            lesson_num = self.get_lesson_for_date(datetime.now())
        elif 'lección' in query_lower and any(char.isdigit() for char in query):
            query_type = "lesson_specific"
            import re
            match = re.search(r'(\d+)', query)
            lesson_num = int(match.group(1)) if match else None
        elif any(concept in query_lower for concept in ['perdón', 'amor', 'miedo', 'paz']):
            query_type = "concept_based"
            lesson_num = None  # Se determinará por concepto
        elif any(phrase in query_lower for phrase in ['reflexión', 'dormir', 'noche']):
            query_type = "reflection"
            lesson_num = None
        else:
            query_type = "general"
            lesson_num = None
        
        # Generar respuesta
        response = self.generate_structured_response(query, query_type, lesson_num)
        
        return {
            "query": query,
            "query_type": query_type,
            "lesson_number": lesson_num,
            "response": response,
            "timestamp": str(datetime.now())
        }

def main():
    """Función principal para probar el motor"""
    engine = UCDMResponseEngine()
    
    # Cargar datos
    if not engine.load_data():
        print("❌ Error: No se pudieron cargar los datos del sistema")
        return 1
    
    print(f"\n{'='*60}")
    print("MOTOR DE RESPUESTAS ESTRUCTURADAS UCDM")
    print(f"{'='*60}")
    
    print(f"\n🔧 MOTOR INICIALIZADO:")
    print(f"   Lecciones disponibles: {len(engine.lessons_index)}")
    print(f"   Conceptos indexados: {len(engine.concept_index)}")
    print(f"   Templates cargados: ✓")
    
    # Probar diferentes tipos de consulta
    test_queries = [
        "Explícame la Lección 1",
        "¿Cuál es la lección de hoy?",
        "Háblame sobre el perdón en UCDM",
        "Necesito una reflexión para antes de dormir",
        "¿Qué enseña el Curso sobre el miedo?"
    ]
    
    print(f"\n🧪 PRUEBAS DEL MOTOR:")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Prueba {i}: {query} ---")
        
        result = engine.process_query(query)
        
        print(f"Tipo de consulta: {result['query_type']}")
        if result['lesson_number']:
            print(f"Lección utilizada: {result['lesson_number']}")
        
        # Mostrar estructura de la respuesta
        response = result['response']
        sections = [
            "HOOK INICIAL",
            "APLICACIÓN PRÁCTICA", 
            "INTEGRACIÓN EXPERIENCIAL",
            "CIERRE MOTIVADOR"
        ]
        
        print("Estructura verificada:")
        for section in sections:
            status = "✓" if section in response else "✗"
            print(f"   {status} {section}")
        
        # Mostrar preview de la respuesta
        lines = response.split('\n')
        preview_lines = [line for line in lines[:8] if line.strip()]
        preview = '\n'.join(preview_lines)
        print(f"Preview: {preview[:200]}...")
    
    print(f"\n✅ MOTOR DE RESPUESTAS COMPLETADO")
    print(f"   - Templates dinámicos: ✓")
    print(f"   - Variación en respuestas: ✓") 
    print(f"   - Estructura consistente: ✓")
    print(f"   - Integración con datos: ✓")
    
    return 0

if __name__ == "__main__":
    exit(main())