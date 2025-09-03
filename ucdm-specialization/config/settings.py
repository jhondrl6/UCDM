# Configuración del Proyecto UCDM
import os
from pathlib import Path

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TRAINING_DATA_DIR = DATA_DIR / "training"
INDICES_DIR = DATA_DIR / "indices"

# Archivo PDF de UCDM
UCDM_PDF_PATH = RAW_DATA_DIR / "Un Curso de Milagros.pdf"

# Archivos de salida
UCDM_COMPLETE_TEXT = PROCESSED_DATA_DIR / "ucdm_complete_text.txt"
LESSONS_INDEX = INDICES_DIR / "365_lessons_indexed.json"
CHAPTERS_INDEX = INDICES_DIR / "31_chapters_indexed.json"
CONCEPTS_INDEX = INDICES_DIR / "concepts_index.json"
LESSON_MAPPER = INDICES_DIR / "lesson_mapper.json"

# Dataset de entrenamiento
EXTENDED_DATASET = TRAINING_DATA_DIR / "extended_dataset.jsonl"
LESSON_SPECIFIC_DATASET = TRAINING_DATA_DIR / "lesson_specific.jsonl"
VALIDATION_DATASET = TRAINING_DATA_DIR / "validation_set.jsonl"

# Configuración de extracción
EXTRACTION_CONFIG = {
    "verify_lessons_count": 365,
    "verify_chapters_count": 31,
    "backup_methods": ["pypdf2", "pdfplumber", "ocr"],
    "encoding": "utf-8"
}

# Configuración de templates
RESPONSE_TEMPLATES = {
    "leccion_diaria": {
        "hook_variants": [
            "¿Y si te dijera que",
            "¿Imaginas cómo",
            "¿Te has preguntado por qué",
            "¿Qué pasaría si"
        ],
        "aplicacion_headers": [
            "Paso 1: Reconoce",
            "Paso 2: Observa",
            "Paso 3: Extiende",
            "Exploración 1:",
            "Desafío 2:",
            "Práctica 3:"
        ],
        "cierre_variants": [
            "Lleva esto contigo hoy y observa el milagro",
            "Hoy, vive esta lección como un experimento vivo",
            "¿Estás listo para más? Comparte tu experiencia",
            "Que este día sea un testimonio de la verdad"
        ]
    }
}

# Configuración del modelo Ollama
OLLAMA_CONFIG = {
    "model_name": "ucdm-gemma",
    "base_model": "gemma:3b",
    "context_size": 8192,
    "max_tokens": 2048,
    "temperature": 0.7,
    "top_p": 0.9
}

# Patrones de extracción
LESSON_PATTERNS = {
    "lesson_number": r"Lección\s+(\d{1,3})",
    "lesson_title": r"Lección\s+\d{1,3}\s*[\.:]?\s*(.+?)(?=\n|\r)",
    "lesson_content_start": r"Lección\s+\d{1,3}",
    "lesson_end_markers": [
        r"Lección\s+\d{1,3}",
        r"TEXTO\s+PRINCIPAL",
        r"MANUAL\s+PARA\s+EL\s+MAESTRO"
    ]
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": PROJECT_ROOT / "logs" / "ucdm_specialization.log"
}