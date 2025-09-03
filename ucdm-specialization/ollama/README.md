# 🌟 Configuración de Ollama para UCDM

Esta guía te ayudará a configurar Ollama con el modelo especializado de Un Curso de Milagros.

## 📋 Requisitos Previos

1. **Ollama instalado** - Descarga desde [ollama.ai](https://ollama.ai)
2. **Python 3.8+** con las dependencias del proyecto
3. **Al menos 8GB de RAM** para el modelo Gemma 3B
4. **Datos de UCDM extraídos** (ejecutar primero los scripts de extracción)

## 🚀 Instalación Paso a Paso

### 1. Instalar Ollama

**Windows:**
```bash
# Descargar desde https://ollama.ai/download/windows
# Ejecutar el instalador OllamaSetup.exe
```

**macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Verificar Instalación

```bash
ollama version
ollama list  # Debe mostrar lista vacía inicialmente
```

### 3. Configurar Modelo UCDM

```bash
# Desde el directorio del proyecto
cd c:\Users\Jhond\Github\UCDM\ucdm-specialization

# Ejecutar configuración automática
python ollama\setup_model.py
```

El script automáticamente:
- ✓ Verifica que Ollama esté funcionando
- ✓ Descarga el modelo base Gemma 3B (si no existe)
- ✓ Crea el modelo especializado UCDM
- ✓ Prueba la funcionalidad
- ✓ Genera scripts de uso

## 🎯 Opciones de Configuración

### Opción 1: Modelo Básico (Rápido)
```bash
python ollama\setup_model.py
```
Crea modelo con prompt system optimizado para UCDM.

### Opción 2: Modelo con Fine-tuning (Avanzado)
```bash
# Generar datos de entrenamiento
python ollama\generate_training_data.py

# Entrenar modelo personalizado
python ollama\train_model.py
```
Crea modelo entrenado con ejemplos específicos de UCDM.

## 💻 Formas de Usar el Modelo

### 1. Línea de Comandos Directa
```bash
# Modo interactivo
ollama run ucdm-gemma

# Consulta directa
ollama run ucdm-gemma "Explícame la Lección 1"
```

### 2. Script Python
```bash
python ollama\query_ucdm.py "¿Cuál es la lección de hoy?"
```

### 3. CLI Interactiva del Proyecto
```bash
python ucdm_cli.py
```

### 4. Integración con API
```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'ucdm-gemma',
    'prompt': 'Háblame sobre el perdón en UCDM',
    'stream': False
})

print(response.json()['response'])
```

## 🛠️ Configuración Avanzada

### Parámetros del Modelo

El modelo viene preconfigurado con:

```
PARAMETER temperature 0.7      # Creatividad moderada
PARAMETER top_p 0.9           # Diversidad de respuestas
PARAMETER top_k 40            # Variedad de tokens
PARAMETER num_ctx 8192        # Contexto largo
PARAMETER num_predict 2048    # Respuestas detalladas
PARAMETER repeat_penalty 1.1  # Evita repetición
```

### Personalizar Configuración

Edita `ollama/Modelfile` para ajustar:

```dockerfile
# Cambiar temperatura para respuestas más creativas/conservadoras
PARAMETER temperature 0.8

# Ajustar longitud de respuestas
PARAMETER num_predict 1024

# Modificar el prompt del sistema
SYSTEM """Tu prompt personalizado aquí..."""
```

Luego recrea el modelo:
```bash
ollama create ucdm-gemma-custom -f ollama/Modelfile
```

## 🧪 Ejemplos de Uso

### Consultas de Lecciones
```bash
ollama run ucdm-gemma "Explícame la Lección 15"
ollama run ucdm-gemma "¿Cuál es la lección de hoy?"
```

### Conceptos del Curso
```bash
ollama run ucdm-gemma "Háblame sobre el perdón en UCDM"
ollama run ucdm-gemma "¿Qué significa 'milagro' según el Curso?"
```

### Aplicación Práctica
```bash
ollama run ucdm-gemma "¿Cómo puedo aplicar UCDM cuando tengo miedo?"
ollama run ucdm-gemma "Dame una reflexión nocturna del Curso"
```

### Respuesta Esperada

Todas las respuestas siguen esta estructura:

```
🎯 HOOK INICIAL: UNA PREGUNTA O ANÉCDOTA PARA ENGANCHAR
[Pregunta profunda que conecta emocionalmente]

⚡ APLICACIÓN PRÁCTICA: PASOS VIVOS Y VARIADOS
Paso 1: [Acción concreta con ejemplo]
Paso 2: [Aplicación intermedia]
Paso 3: [Integración avanzada]

🌿 INTEGRACIÓN EXPERIENCIAL: CONEXIÓN VIVA Y REFLEXIVA
[Conexión personal y preguntas reflexivas]

✨ CIERRE MOTIVADOR: UN MILAGRO FINAL
[Invitación inspiradora a la acción]
```

## 🔧 Solución de Problemas

### Error: "Ollama not found"
```bash
# Verificar instalación
which ollama  # Linux/macOS
where ollama  # Windows

# Reiniciar servicio
ollama serve
```

### Error: "Model not found"
```bash
# Listar modelos disponibles
ollama list

# Recrear modelo
python ollama\setup_model.py
```

### Error: "Out of memory"
```bash
# Verificar RAM disponible
ollama ps

# Usar modelo más pequeño
ollama pull gemma:2b
# Editar Modelfile: FROM gemma:2b
```

### Respuestas Inconsistentes
```bash
# Regenerar con fine-tuning
python ollama\generate_training_data.py
python ollama\train_model.py
```

## 📊 Monitoreo del Modelo

### Verificar Estado
```bash
ollama ps  # Modelos en ejecución
ollama list  # Modelos instalados
```

### Estadísticas de Uso
```bash
# Ver logs
ollama logs

# Rendimiento
time ollama run ucdm-gemma "test query"
```

## 🔄 Actualizaciones

### Actualizar Datos del Curso
```bash
# Re-extraer PDF si hay nueva versión
python extraction\pdf_extractor.py

# Regenerar índices
python extraction\lesson_indexer.py

# Recrear modelo
python ollama\setup_model.py
```

### Actualizar Ollama
```bash
# Backup modelo actual
ollama cp ucdm-gemma ucdm-gemma-backup

# Actualizar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Verificar compatibilidad
python ollama\setup_model.py
```

## 🎯 Mejores Prácticas

### Para Usuarios Diarios
1. **Usa CLI interactiva**: `python ucdm_cli.py`
2. **Consulta lección del día**: `ollama run ucdm-gemma "¿lección de hoy?"`
3. **Reflexiones nocturnas**: `ollama run ucdm-gemma "reflexión nocturna"`

### Para Desarrolladores
1. **API REST**: Integra con `http://localhost:11434/api`
2. **Fine-tuning**: Usa `generate_training_data.py`
3. **Monitoring**: Implementa logs de consultas

### Para Estudiantes del Curso
1. **Consultas regulares**: Establece rutina diaria
2. **Profundización**: Explora conceptos específicos
3. **Aplicación práctica**: Usa ejemplos cotidianos

## 📞 Soporte

Si encuentras problemas:

1. **Revisa logs**: `ollama logs`
2. **Verifica recursos**: RAM, espacio en disco
3. **Consulta documentación**: [ollama.ai/docs](https://ollama.ai/docs)
4. **Regenera modelo**: `python ollama\setup_model.py`

---

🌟 **¡Disfruta explorando Un Curso de Milagros con tu asistente especializado!** 🌟