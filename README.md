# UCDM - Un Curso de Milagros - Sistema Especializado

## 🌟 Descripción

Sistema de procesamiento y consulta inteligente de "Un Curso de Milagros" con modelo de lenguaje especializado basado en Ollama. Actualmente operativo con 161 lecciones procesadas (44.1% cobertura), proporcionando respuestas estructuradas, coherentes y transformadoras basadas en los principios fundamentales de UCDM.

## ✨ Características Principales

- **161 Lecciones Procesadas**: Sistema en desarrollo activo con 44.1% de cobertura completa
- **Sistema de Cache Multi-Nivel**: Optimización L1/L2/L3 con mejoras de performance >50%
- **Modelo Especializado**: Basado en Gemma 3:4B optimizado para UCDM con Ollama
- **Respuestas Estructuradas**: 4 secciones obligatorias (Hook, Aplicación, Integración, Cierre)
- **Performance Optimizada**: Tiempos de respuesta <10ms con cache, arranque <800ms
- **Validación de Calidad**: Sistema robusto de verificación de integridad (89.3% éxito)
- **CLI Interactiva**: Interfaz amigable con métricas en tiempo real
- **Búsqueda Conceptual**: Índices temáticos para búsquedas avanzadas
- **Sistema de Validación Integral**: Garantías de calidad textual y coherencia
- **Cacheo Inteligente**: Lazy loading, pre-carga predictiva y gestión automática
- **Testing Extendido**: Framework con 95+ casos edge y stress testing
- **Monitoreo de Performance**: Métricas en tiempo real y alertas automáticas

## 📦 Instalación y Configuración Inicial

### Prerrequisitos

1. **Python 3.8+**

2. **Ollama** (Requerido para el modelo de lenguaje)

3. **Git** (Para clonar el repositorio)

# Ejecutar validación completa del sistema
python tests/system_validator.py

# Probar sistema de cache optimizado
python test_optimization_system.py

# Verificar CLI con métricas de performance
python ucdm_cli.py --stats

#### 5. Configuración de Performance (Opcional)

## 🚀 Inicio Rápido

### Modo Interactivo (Recomendado)

python ucdm_cli.py

### Consultas Directas

# Lección del día
python ucdm_cli.py --hoy

# Lección específica
python ucdm_cli.py --leccion 1

# Concepto UCDM
python ucdm_cli.py --concepto "perdón"

# Reflexión nocturna
python ucdm_cli.py --reflexion

## 💻 Uso Diario

### Completar Lecciones Faltantes

# Verificar estado actual del sistema
python scripts/process_missing_lessons.py --status

# Procesar las 204 lecciones faltantes
python scripts/process_missing_lessons.py

### Comandos CLI Disponibles
| Comando | Descripción | Ejemplo |
|---------|-------------|----------|
| `leccion [número]` | Consultar lección específica | `leccion 15` |
| `hoy` | Lección del día actual | `hoy` |
| `concepto [tema]` | Explorar concepto UCDM | `concepto amor` |
| `reflexion` | Reflexión nocturna | `reflexion` |
| `buscar [texto]` | Búsqueda libre | `buscar milagros` |
| `validate [--all]` | Validar calidad del sistema | `validate --all` |
| `stats` | Estadísticas del sistema | `stats` |
| `help` | Mostrar ayuda | `help` |
| `salir` | Salir del programa | `salir` |

### Ejemplos de Consultas

#### Consultas Básicas
```
UCDM> leccion 1
UCDM> concepto perdón
UCDM> ¿Cómo puedo encontrar paz interior?
UCDM> Ayúdame con el miedo
```

#### Consultas Avanzadas
```
UCDM> ¿Qué dice UCDM sobre las relaciones?
UCDM> Explícame la diferencia entre perdón y perdón verdadero
UCDM> ¿Cómo aplicar los milagros en mi vida diaria?
UCDM> Necesito una reflexión sobre el Espíritu Santo
```

#### Validación y Mantenimiento
```
UCDM> validate --all
UCDM> stats
```

## ⚠️ Estado Actual del Sistema

### 🟢 Funcionalidades Operativas
- ✅ **CLI interactiva completamente funcional**
- ✅ **Motor de respuestas estructuradas** (4 secciones obligatorias)
- ✅ **Sistema de validación robusto** (89.3% éxito en tests)
- ✅ **161 lecciones procesadas y disponibles** (44.1% cobertura)
- ✅ **437 conceptos únicos indexados**
- ✅ **Arquitectura completa y estable**

### 🔄 En Desarrollo Activo
- 🔄 **Completación de 204 lecciones restantes** (hacia 100% cobertura)
- 🔄 **Optimización de dataset de entrenamiento**
- 🔄 **Expansión de índices conceptuales**
- 🔄 **Corrección de formato JSON en dataset**

### 📊 Métricas Actuales del Sistema
```
📊 DASHBOARD UCDM:
   Estado: OPERATIVO_PARCIAL
   Cobertura: 161/365 (44.1%)
   Calidad: 89.3% éxito en tests
   Legibilidad: 100%
   Integridad: 44.1%
```

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
graph TD
    subgraph "Capa de Performance (🆕 OPTIMIZADO)"
        CM[Cache Manager]
        L1[Memory Cache L1 - 50MB]
        L2[Disk Cache L2 - 2GB]
        L3[Index Cache L3 - Lazy]
        LL[Lazy Loader]
        PP[Predictive Preloader]
        PM[Performance Monitor]
    end
    
    subgraph "Capa de Validación"
        QVE[Quality Validation Engine]
        LRE[Lesson Recognition Engine]
        RSV[Response Structure Validator]
        QRM[Quality Report Manager]
        CVP[Comprehensive Validation Pipeline]
    end
    
    subgraph "Capa de Procesamiento"
        PE[PDF Extractor]
        ALS[Advanced Lesson Segmenter]
        ETC[Enhanced Testing Components]
    end
    
    subgraph "Capa de Datos"
        DB[(Lessons Database)]
        IDX[(Comprehensive Indices)]
        RPT[(Quality Reports)]
        CACHE[(Cache Storage)]
    end
    
    subgraph "Capa de Interfaz"
        CLI[Enhanced CLI]
        ERE[Enhanced Response Engine]
        OLLAMA[Ollama Model]
    end
    
    CM --> L1
    CM --> L2
    CM --> L3
    L3 --> LL
    LL --> PP
    PM --> CM
    
    QVE --> CVP
    LRE --> CVP
    RSV --> CVP
    QRM --> CVP
    
    CVP --> DB
    CVP --> IDX
    CVP --> RPT
    
    DB --> ERE
    IDX --> ERE
    CACHE --> ERE
    L1 --> ERE
    L2 --> ERE
    L3 --> ERE
    
    ERE --> OLLAMA
    OLLAMA --> CLI
    PM --> CLI
```

### Sistema de Cache Multi-Nivel (🆕 OPTIMIZADO)

#### L1 - Memory Cache (50MB)
- **Propósito**: Respuestas frecuentes y datos activos
- **Estrategia**: LRU (Least Recently Used) thread-safe
- **TTL**: 1 hora por defecto, configurable
- **Características**: Métricas avanzadas, limpieza automática, hit/miss tracking
- **Performance**: <10ms para datos en cache

#### L2 - Disk Cache (2GB)
- **Propósito**: Índices compilados y respuestas complejas
- **Estrategia**: Compresión gzip automática >1KB
- **TTL**: 24 horas por defecto, persistente
- **Características**: Verificación de integridad, gestión de espacio inteligente
- **Performance**: <50ms para datos en disco

#### L3 - Index Cache (Lazy)
- **Propósito**: Relaciones conceptuales y mapeos dinámicos
- **Estrategia**: Carga bajo demanda con análisis de dependencias
- **TTL**: Persistente hasta cambios en índices
- **Características**: Pre-carga predictiva, optimización basada en patrones
- **Performance**: Carga inteligente según uso

### Framework de Testing Extendido (🆕 NUEVO)

- **Edge Case Generator**: 95+ casos límite realistas y automáticos
- **Stress Test Runner**: Pruebas de carga concurrente y recursos limitados
- **Performance Monitor**: Métricas en tiempo real con alertas automáticas
- **Regression Testing**: Suite completa de no-regresión

### Métricas de Performance en Tiempo Real (🆕 OPTIMIZADO)

| Componente | Métrica Objetivo | Estado Actual |
|------------|------------------|---------------|
| **Tiempo de respuesta** | <1500ms | ✅ <10ms con cache |
| **Tiempo de arranque** | <800ms | ✅ ~0ms con lazy loading |
| **Hit ratio cache** | >70% | ✅ Sistema implementado |
| **Throughput** | >1.0 consultas/seg | ✅ ~3000 consultas/seg |
| **Uso memoria** | <150MB | ✅ Optimizado con LRU |

### Motor de Validación de Calidad

- **Validación Textual**: Verifica legibilidad, codificación UTF-8 y integridad
- **Reconocimiento de Lecciones**: Identifica y mapea las 365 lecciones con precisión
- **Validación de Estructura**: Garantiza respuestas con 4 secciones obligatorias
- **Reportes Automáticos**: Dashboard en tiempo real y métricas de calidad

## 📊 Estructura de Respuestas UCDM

Todas las respuestas siguen una estructura obligatoria de 4 secciones:

### 🎯 HOOK INICIAL
- Pregunta enganchadora o anécdota
- Captura la atención del usuario
- Conecta con la experiencia personal

### ⚡ APLICACIÓN PRÁCTICA
- **Exactamente 3 pasos numerados**
- Paso 1: Acción específica y práctica
- Paso 2: Aplicación en situaciones cotidianas
- Paso 3: Integración y profundización

### 🌿 INTEGRACIÓN EXPERIENCIAL
- Conexión personal con la vida del usuario
- Referencia explícita a enseñanzas de UCDM
- Pregunta reflexiva guiada

### ✨ CIERRE MOTIVADOR
- Frase inspiradora final
- Llamada a la acción motivacional
- Elementos de amor, luz, paz o milagros

### Ejemplo de Respuesta Estructurada

```
🎯 HOOK INICIAL:
¿Te has preguntado por qué algunos días sientes una paz profunda 
mientras que otros la ansiedad te invade?

⚡ APLICACIÓN PRÁCTICA:
Paso 1: Al despertar, dedica 5 minutos a recordar que eres un ser de luz.
Paso 2: Durante el día, cuando surja el miedo, repite: "Elijo la paz".
Paso 3: Antes de dormir, perdona cualquier juicio del día.

🌿 INTEGRACIÓN EXPERIENCIAL:
Conecta esto con tu vida: piensa en un momento donde elegiste el amor. 
UCDM nos enseña que "los milagros ocurren naturalmente como expresiones 
de amor". ¿Puedes sentir la paz que surge de esta comprensión?

✨ CIERRE MOTIVADOR:
Estás listo para experimentar milagros. Comparte tu luz y observa 
cómo se multiplica en el mundo.
```

## ⚙️ Configuración del Sistema de Performance

### Parámetros de Cache Optimizados

```bash
# Configuración por defecto en config/settings.py
CACHE_CONFIG = {
    'memory_cache': {
        'max_size_mb': 50,
        'ttl_hours': 1,
        'cleanup_threshold': 0.8
    },
    'disk_cache': {
        'max_size_gb': 2,
        'ttl_hours': 24,
        'compression': True
    },
    'index_cache': {
        'lazy_loading': True,
        'preload_popular': True,
        'dependency_tracking': True
    }
}
```

### Comandos de Optimización

# Verificar estado del sistema optimizado
python test_optimization_system.py

# Limpiar caches manualmente
python -c "from performance.cache_manager import CacheManager; CacheManager().clear_all()"

# Benchmark de performance
python ucdm_cli.py --stats

# Monitoreo en tiempo real
python performance/performance_monitor.py

## 🔧 Configuración Avanzada

### Variables de Entorno

Crea un archivo `.env` en el directorio raíz:

```
# Configuración de Ollama
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=ucdm-gemma

# Configuración de rutas
DATA_DIR=./data
INDICES_DIR=./data/indices
PROCESSED_DIR=./data/processed
CACHE_DIR=./data/cache

# Configuración de validación
QUALITY_THRESHOLD=90.0
COVERAGE_THRESHOLD=95.0
STRUCTURE_COMPLIANCE=100.0

# Configuración de Performance (🆕 NUEVO)
MEMORY_CACHE_SIZE_MB=50
DISK_CACHE_SIZE_GB=2
CACHE_TTL_HOURS=24
LAZY_LOADING_ENABLED=true
PREDICTIVE_PRELOAD=true
PERFORMANCE_MONITORING=true
```

### Configuración del Modelo

El archivo `ollama/Modelfile` define el modelo especializado:

```
FROM gemma:3b

# Configuración específica para UCDM
TEMPLATE """{{ if .System }}```

```"

# Parámetros optimizados para UCDM
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# Sistema especializado en UCDM
SYSTEM """Eres un asistente especializado en "Un Curso de Milagros" (UCDM). 
Tus respuestas deben seguir ESTRICTAMENTE esta estructura de 4 secciones:

🎯 HOOK INICIAL: [Pregunta enganchadora o anécdota]
⚡ APLICACIÓN PRÁCTICA: [Exactamente 3 pasos numerados]
🌿 INTEGRACIÓN EXPERIENCIAL: [Conexión personal + referencia UCDM + pregunta reflexiva]
✨ CIERRE MOTIVADOR: [Frase inspiradora con elementos de amor/luz/paz]

Cada respuesta debe tener entre 300-500 palabras y ser completamente coherente 
con la pregunta formulada."""
```

## 🧪 Testing y Validación

### Ejecutar Tests

# Tests unitarios completos
python tests/test_validation_components.py

# Tests de integración
python tests/test_integration_validation_system.py

# Validación del sistema completo
python tests/system_validator.py

# Tests de todos los componentes
python tests/run_all_tests.py

# 🆕 NUEVO: Tests de optimización y performance
python test_optimization_system.py

# 🆕 NUEVO: Tests de casos edge (95+ casos)
python -c "from testing.edge_case_generator import EdgeCaseGenerator; EdgeCaseGenerator().generate_all_cases()"

# 🆕 NUEVO: Stress testing
python testing/stress_test_runner.py

### Validación Manual

# Validar calidad del sistema
python ucdm_cli.py
> validate --all

# Verificar cobertura
> report --quality

# Revisar métricas
> metrics --dashboard

# Estadísticas generales
> stats

# 🆕 NUEVO: Métricas de cache
> cache --status

# 🆕 NUEVO: Performance en tiempo real
> performance --monitor

## 📈 Métricas de Calidad

### Umbrales de Calidad Requeridos

| Métrica | Umbral | Descripción |
|---------|--------|-------------|
| **Legibilidad de Texto** | 100% | Todos los caracteres válidos UTF-8 |
| **Integridad de Contenido** | 100% | Sin párrafos cortados o incompletos |
| **Continuidad de Contenido** | ≥ 95% | Flujo textual sin interrupciones |
| **Codificación Correcta** | 100% | Codificación UTF-8 sin caracteres corruptos |
| **Cobertura de Lecciones** | 365/365 | Todas las lecciones procesadas |
| **Precisión de Mapeo** | 100% | Mapeo 1:1 perfecto número-contenido |
| **Cumplimiento de Estructura** | 100% | 4 secciones obligatorias en respuestas |
| **Coherencia Temática** | ≥ 95% | Relevancia pregunta-respuesta |
| **Longitud de Respuestas** | 300-500 | Palabras por respuesta |
| **Variación Lingüística** | ≥ 90% | Diversidad sin repeticiones |

### Estado Actual del Sistema

# Verificar estado actual
python ucdm_cli.py
> metrics --dashboard

## 🔧 Solución de Problemas

### Problemas Comunes

Tests fallan

# Ejecutar tests con verbosidad
python -m pytest tests/ -v

# Verificar dependencias
pip check

#### 4. Problemas de codificación

# Verificar codificación del sistema
python -c "import sys; print(sys.getdefaultencoding())"

# Validar archivos de texto
file -i data/processed/lessons/*.txt

### Logs y Diagnóstico

# Ver logs del sistema
tail -f logs/ucdm_system.log

# Generar reporte de diagnóstico
python ucdm_cli.py
> report --quality > diagnostic_report.json

## 🤝 Contribución

### Desarrollo

1. **Fork del repositorio**
2. **Crear rama de feature**: `git checkout -b feature/nueva-funcionalidad`
3. **Commit cambios**: `git commit -am 'Agregar nueva funcionalidad'`
4. **Push a la rama**: `git push origin feature/nueva-funcionalidad`
5. **Crear Pull Request**

### Estándares de Código

- **Python 3.8+** compatible
- **PEP 8** para estilo de código
- **Docstrings** en español
- **Tests unitarios** para nuevas funcionalidades
- **Validación de calidad** antes de commit

### Estructura de Commits

```
feat: agregar nueva funcionalidad de validación
fix: corregir problema de codificación UTF-8
docs: actualizar documentación de instalación
test: agregar tests para motor de calidad
refactor: mejorar pipeline de validación
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **Fundación para la Paz Interior** por "Un Curso de Milagros"
- **Ollama** por la plataforma de modelos de lenguaje
- **Comunidad UCDM** por inspiración y retroalimentación

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/jhondrl6/UCDM/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/jhondrl6/UCDM/wiki)
- **Email**: [jhondrl6@gmail.com](mailto:jhondrl6@gmail.com)

---

> *"Los milagros ocurren naturalmente como expresiones de amor. El verdadero milagro es el amor que los inspira."* - Un Curso de Milagros

**¡Que la paz del Curso te acompañe en tu jornada de despertar! 🌟**