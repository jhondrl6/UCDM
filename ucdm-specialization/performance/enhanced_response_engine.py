#!/usr/bin/env python3
"""
Enhanced Response Engine - Motor de respuestas con optimizaciones de cache
Integra el sistema de cacheo multi-nivel con el ResponseEngine existente
"""

import sys
import json
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Importar módulos
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *
from performance.memory_cache import MemoryCache
from performance.disk_cache import DiskCache
from performance.index_cache import IndexCache

class EnhancedUCDMResponseEngine:
    """Motor de respuestas UCDM optimizado con cacheo multi-nivel"""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        
        # Sistema de cache
        if self.use_cache:
            self.memory_cache = MemoryCache(max_size_mb=50, default_ttl_hours=1)
            self.disk_cache = DiskCache(cache_dir="data/cache", max_size_gb=2)
            self.index_cache = IndexCache(indices_dir=str(INDICES_DIR))
        
        # Estado del motor
        self.lessons_index = {}
        self.concept_index = {}
        self.date_mapper = {}
        self.templates = self.load_response_templates()
        
        # Métricas
        self.cache_hits = 0
        self.cache_misses = 0
        self.response_times = []
        
        self.setup_logging()
        self.logger.info("Enhanced Response Engine inicializado")
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_response_templates(self) -> Dict:
        """Cargar templates con cache L1"""
        if self.use_cache:
            cached = self.memory_cache.get("response_templates")
            if cached:
                return cached
        
        # Templates básicos
        templates = {
            "hooks_iniciales": {
                "preguntas_enganchadoras": [
                    "¿Y si te dijera que", "¿Imaginas cómo", "¿Te has preguntado por qué"
                ],
                "contextos_ucdm": [
                    "la paz no es algo que logras, sino algo que recuerdas que ya tienes?",
                    "cada miedo es una oportunidad para elegir la paz en su lugar?"
                ]
            },
            "aplicacion_practica": {
                "headers_paso1": ["Paso 1: Reconoce", "Exploración 1: Descubre"],
                "aplicaciones_variadas": [
                    "**Práctica matutina**: Al despertar, dedica 5 minutos a esta verdad",
                    "**Aplicación inmediata**: En conversaciones difíciles, recuerda esta lección"
                ]
            },
            "integracion_experiencial": {
                "conectores_personales": ["Conecta esto con tu vida:", "Reflexiona sobre esto:"],
                "enseñanzas_ucdm": [
                    "UCDM nos enseña que 'la percepción es una elección, no un hecho'",
                    "Como dice el Curso, 'los milagros ocurren naturalmente como expresiones de amor'"
                ]
            },
            "cierres_motivadores": {
                "llamadas_accion": [
                    "Lleva esto contigo hoy y observa el milagro",
                    "Hoy, vive esta lección como un experimento vivo"
                ]
            }
        }
        
        if self.use_cache:
            self.memory_cache.put("response_templates", templates, ttl_hours=24)
        
        return templates
    
    def load_data(self) -> bool:
        """Cargar datos usando cache L3"""
        try:
            if self.use_cache:
                data = self.index_cache.get_index('ucdm_comprehensive_index')
                if data:
                    self.lessons_index = data.get("lesson_details", {})
                    self.concept_index = data.get("concept_index", {})
                    self.date_mapper = data.get("date_mapping", {})
                    self.logger.info(f"Datos cargados desde cache: {len(self.lessons_index)} lecciones")
                    return True
            
            # Fallback tradicional
            index_file = INDICES_DIR / "ucdm_comprehensive_index.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.lessons_index = data.get("lesson_details", {})
                self.concept_index = data.get("concept_index", {})
                self.date_mapper = data.get("date_mapping", {})
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error cargando datos: {e}")
            return False
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Procesar consulta con cache optimizado"""
        start_time = datetime.now()
        
        # Generar clave de cache
        cache_key = f"response_{hashlib.md5(query.encode()).hexdigest()[:16]}"
        
        # Verificar cache L1
        if self.use_cache:
            cached = self.memory_cache.get(cache_key)
            if cached:
                self.cache_hits += 1
                cached['cache_hit'] = True
                return cached
            
            # Verificar cache L2
            cached = self.disk_cache.get(cache_key)
            if cached:
                self.cache_hits += 1
                self.memory_cache.put(cache_key, cached, ttl_hours=1)
                cached['cache_hit'] = True
                return cached
        
        # Generar nueva respuesta
        self.cache_misses += 1
        query_type, lesson_num = self._analyze_query(query)
        response = self.generate_structured_response(query, query_type, lesson_num)
        
        result = {
            'query': query,
            'query_type': query_type,
            'lesson_number': lesson_num,
            'response': response,
            'generated_at': datetime.now().isoformat(),
            'cache_hit': False
        }
        
        # Almacenar en cache
        if self.use_cache:
            self.memory_cache.put(cache_key, result, ttl_hours=1)
            self.disk_cache.put(cache_key, result, ttl_hours=24)
        
        # Registrar tiempo
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
        
        return result
    
    def _analyze_query(self, query: str) -> Tuple[str, Optional[int]]:
        """Analizar tipo de consulta"""
        import re
        query_lower = query.lower()
        
        # Lección específica
        lesson_match = re.search(r'lecci[oó]n\s+(\d+)', query_lower)
        if lesson_match:
            return "lesson_specific", int(lesson_match.group(1))
        
        # Lección diaria
        if any(phrase in query_lower for phrase in ['hoy', 'diaria', 'día']):
            return "daily_lesson", self.get_lesson_for_date(datetime.now())
        
        # Por concepto
        if any(phrase in query_lower for phrase in ['sobre', 'acerca', 'explica']):
            return "concept_based", None
        
        return "general", None
    
    def get_lesson_for_date(self, target_date: datetime) -> Optional[int]:
        """Obtener lección para fecha"""
        date_key = target_date.strftime("%m-%d")
        return self.date_mapper.get(date_key)
    
    def generate_structured_response(self, query: str, query_type: str, lesson_num: Optional[int]) -> str:
        """Generar respuesta estructurada"""
        try:
            # Seleccionar lección
            if lesson_num and str(lesson_num) in self.lessons_index:
                lesson_data = self.lessons_index[str(lesson_num)]
                lesson_title = lesson_data.get('title', f'Lección {lesson_num}')
            elif self.lessons_index:
                lesson_num = int(random.choice(list(self.lessons_index.keys())))
                lesson_data = self.lessons_index[str(lesson_num)]
                lesson_title = lesson_data.get('title', f'Lección {lesson_num}')
            else:
                lesson_title = "Enseñanza del Curso de Milagros"
                lesson_num = 1
            
            # Generar secciones
            hook = self._generate_hook(lesson_title)
            aplicacion = self._generate_aplicacion(lesson_title)
            integracion = self._generate_integracion(lesson_title)
            cierre = self._generate_cierre()
            
            return f"""🌟 HOOK INICIAL: {hook}

APLICACIÓN PRÁCTICA: {aplicacion}

INTEGRACIÓN EXPERIENCIAL: {integracion}

CIERRE MOTIVADOR: {cierre}"""
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta: {e}")
            return "Error generando respuesta. Por favor, intenta de nuevo."
    
    def _generate_hook(self, lesson_title: str) -> str:
        """Generar hook inicial"""
        pregunta = random.choice(self.templates["hooks_iniciales"]["preguntas_enganchadoras"])
        contexto = random.choice(self.templates["hooks_iniciales"]["contextos_ucdm"])
        return f"{pregunta} {contexto}"
    
    def _generate_aplicacion(self, lesson_title: str) -> str:
        """Generar aplicación práctica"""
        header = random.choice(self.templates["aplicacion_practica"]["headers_paso1"])
        aplicacion = random.choice(self.templates["aplicacion_practica"]["aplicaciones_variadas"])
        return f"{header}: {aplicacion}"
    
    def _generate_integracion(self, lesson_title: str) -> str:
        """Generar integración experiencial"""
        conector = random.choice(self.templates["integracion_experiencial"]["conectores_personales"])
        enseñanza = random.choice(self.templates["integracion_experiencial"]["enseñanzas_ucdm"])
        return f"{conector} {enseñanza}"
    
    def _generate_cierre(self) -> str:
        """Generar cierre motivador"""
        llamada = random.choice(self.templates["cierres_motivadores"]["llamadas_accion"])
        return f"{llamada} ¿Estás listo para más? El Curso nos invita a profundizar cada día."
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de performance"""
        avg_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        total_requests = self.cache_hits + self.cache_misses
        hit_ratio = self.cache_hits / total_requests if total_requests > 0 else 0
        
        metrics = {
            "response_performance": {
                "avg_response_time_ms": round(avg_time, 2),
                "total_responses": len(self.response_times)
            },
            "cache_performance": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_ratio": round(hit_ratio, 3)
            }
        }
        
        if self.use_cache:
            metrics["cache_details"] = {
                "memory_cache": self.memory_cache.get_stats(),
                "disk_cache": self.disk_cache.get_stats(),
                "index_cache": self.index_cache.get_stats()
            }
        
        return metrics


def create_enhanced_engine(use_cache: bool = True) -> EnhancedUCDMResponseEngine:
    """Crear instancia del motor optimizado"""
    return EnhancedUCDMResponseEngine(use_cache=use_cache)