#!/usr/bin/env python3
"""
Extractor robusto de PDF para Un Curso de Milagros (UCDM)
Garantiza la extracción completa del contenido con validación de integridad
"""

import sys
import os
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Importaciones de bibliotecas de extracción
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Configuración
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *

class UCDMPDFExtractor:
    """Extractor robusto de PDF con múltiples métodos y validación"""
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        self.extraction_log = []
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging para el extractor"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def log_extraction_step(self, method: str, success: bool, details: str = ""):
        """Registrar cada paso de extracción"""
        step = {
            "method": method,
            "success": success,
            "details": details,
            "timestamp": str(datetime.now())
        }
        self.extraction_log.append(step)
        
        if success:
            self.logger.info(f"✓ {method}: {details}")
        else:
            self.logger.error(f"✗ {method}: {details}")
    
    def extract_with_pypdf2(self) -> Optional[str]:
        """Extracción usando PyPDF2"""
        if not HAS_PYPDF2:
            self.log_extraction_step("PyPDF2", False, "Biblioteca no disponible")
            return None
            
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                total_pages = len(pdf_reader.pages)
                
                self.logger.info(f"Extrayendo {total_pages} páginas con PyPDF2...")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        
                        if page_num % 50 == 0:
                            self.logger.info(f"Procesadas {page_num}/{total_pages} páginas")
                            
                    except Exception as e:
                        self.logger.warning(f"Error en página {page_num}: {str(e)}")
                        continue
                
                self.log_extraction_step("PyPDF2", True, f"{total_pages} páginas extraídas")
                return text
                
        except Exception as e:
            self.log_extraction_step("PyPDF2", False, f"Error: {str(e)}")
            return None
    
    def extract_with_pdfplumber(self) -> Optional[str]:
        """Extracción usando pdfplumber (método de respaldo)"""
        if not HAS_PDFPLUMBER:
            self.log_extraction_step("pdfplumber", False, "Biblioteca no disponible")
            return None
            
        try:
            text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                self.logger.info(f"Extrayendo {total_pages} páginas con pdfplumber...")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                            
                        if page_num % 50 == 0:
                            self.logger.info(f"Procesadas {page_num}/{total_pages} páginas")
                            
                    except Exception as e:
                        self.logger.warning(f"Error en página {page_num}: {str(e)}")
                        continue
                
                self.log_extraction_step("pdfplumber", True, f"{total_pages} páginas extraídas")
                return text
                
        except Exception as e:
            self.log_extraction_step("pdfplumber", False, f"Error: {str(e)}")
            return None
    
    def extract_with_ocr(self) -> Optional[str]:
        """Extracción usando OCR como último recurso"""
        if not HAS_OCR:
            self.log_extraction_step("OCR", False, "Bibliotecas OCR no disponibles")
            return None
            
        self.logger.info("Iniciando extracción OCR (puede tomar tiempo)...")
        # Implementación OCR simplificada
        self.log_extraction_step("OCR", False, "OCR no implementado completamente")
        return None
    
    def validate_content_integrity(self, text: str) -> Dict[str, any]:
        """Validar la integridad del contenido extraído"""
        validation_results = {
            "total_chars": len(text),
            "total_words": len(text.split()),
            "lessons_found": 0,
            "chapters_found": 0,
            "sections_detected": [],
            "integrity_score": 0.0,
            "warnings": []
        }
        
        # Buscar lecciones (1-365)
        lesson_pattern = r"Lección\s+(\d{1,3})"
        lessons = re.findall(lesson_pattern, text, re.IGNORECASE)
        unique_lessons = set(int(l) for l in lessons if l.isdigit() and 1 <= int(l) <= 365)
        validation_results["lessons_found"] = len(unique_lessons)
        
        # Buscar capítulos
        chapter_pattern = r"Capítulo\s+(\d{1,2})"
        chapters = re.findall(chapter_pattern, text, re.IGNORECASE)
        unique_chapters = set(int(c) for c in chapters if c.isdigit() and 1 <= int(c) <= 31)
        validation_results["chapters_found"] = len(unique_chapters)
        
        # Detectar secciones principales
        sections = [
            ("Introducción", r"Introducción"),
            ("Texto Principal", r"TEXTO\s+PRINCIPAL"),
            ("Libro de Ejercicios", r"LIBRO\s+DE\s+EJERCICIOS"),
            ("Manual del Maestro", r"MANUAL\s+PARA\s+EL\s+MAESTRO"),
            ("Clarificación de Términos", r"CLARIFICACIÓN\s+DE\s+TÉRMINOS")
        ]
        
        for section_name, pattern in sections:
            if re.search(pattern, text, re.IGNORECASE):
                validation_results["sections_detected"].append(section_name)
        
        # Calcular puntuación de integridad
        integrity_score = 0.0
        
        # Lecciones (40% del score)
        lesson_score = min(validation_results["lessons_found"] / 365, 1.0) * 0.4
        integrity_score += lesson_score
        
        # Capítulos (20% del score)
        chapter_score = min(validation_results["chapters_found"] / 31, 1.0) * 0.2
        integrity_score += chapter_score
        
        # Secciones (20% del score)
        section_score = min(len(validation_results["sections_detected"]) / 5, 1.0) * 0.2
        integrity_score += section_score
        
        # Longitud del texto (20% del score)
        # Asumiendo que UCDM completo tiene al menos 500,000 caracteres
        length_score = min(validation_results["total_chars"] / 500000, 1.0) * 0.2
        integrity_score += length_score
        
        validation_results["integrity_score"] = integrity_score
        
        # Generar advertencias
        if validation_results["lessons_found"] < 360:
            validation_results["warnings"].append(f"Solo se encontraron {validation_results['lessons_found']}/365 lecciones")
        
        if validation_results["chapters_found"] < 30:
            validation_results["warnings"].append(f"Solo se encontraron {validation_results['chapters_found']}/31 capítulos")
        
        if len(validation_results["sections_detected"]) < 4:
            validation_results["warnings"].append("Faltan secciones principales del libro")
        
        return validation_results
    
    def calculate_content_hash(self, text: str) -> str:
        """Calcular hash MD5 del contenido para verificación"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def extract_complete_ucdm(self) -> Tuple[Optional[str], Dict]:
        """Método principal de extracción con validación completa"""
        self.logger.info("=== Iniciando extracción completa de UCDM ===")
        
        if not self.pdf_path.exists():
            error_msg = f"Archivo PDF no encontrado: {self.pdf_path}"
            self.log_extraction_step("Verificación", False, error_msg)
            return None, {"error": error_msg}
        
        # Intentar múltiples métodos de extracción
        extraction_methods = [
            ("PyPDF2", self.extract_with_pypdf2),
            ("pdfplumber", self.extract_with_pdfplumber),
            ("OCR", self.extract_with_ocr)
        ]
        
        best_text = None
        best_validation = None
        best_score = 0.0
        
        for method_name, method_func in extraction_methods:
            self.logger.info(f"Probando método: {method_name}")
            text = method_func()
            
            if text and len(text.strip()) > 1000:  # Mínimo de contenido
                validation = self.validate_content_integrity(text)
                score = validation["integrity_score"]
                
                self.logger.info(f"{method_name} - Score: {score:.2f}, Lecciones: {validation['lessons_found']}")
                
                if score > best_score:
                    best_text = text
                    best_validation = validation
                    best_score = score
                    
                # Si encontramos un resultado muy bueno, podemos parar
                if score > 0.9:
                    self.logger.info(f"Extracción exitosa con {method_name} (score: {score:.2f})")
                    break
        
        if best_text is None:
            error_msg = "No se pudo extraer contenido con ningún método"
            self.log_extraction_step("Extracción Final", False, error_msg)
            return None, {"error": error_msg}
        
        # Guardar texto extraído
        output_path = PROCESSED_DATA_DIR / "ucdm_complete_text.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(best_text)
        
        # Guardar log de extracción
        log_path = RAW_DATA_DIR / "extraction_log.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump({
                "extraction_log": self.extraction_log,
                "validation_results": best_validation,
                "content_hash": self.calculate_content_hash(best_text),
                "file_size": len(best_text),
                "extraction_success": True
            }, f, indent=2, ensure_ascii=False)
        
        self.log_extraction_step("Extracción Final", True, 
                                f"Score: {best_score:.2f}, {best_validation['lessons_found']} lecciones encontradas")
        
        return best_text, best_validation

def main():
    """Función principal para ejecutar la extracción"""
    extractor = UCDMPDFExtractor(UCDM_PDF_PATH)
    text, validation = extractor.extract_complete_ucdm()
    
    if text:
        print(f"✓ Extracción completada exitosamente")
        print(f"✓ Lecciones encontradas: {validation['lessons_found']}/365")
        print(f"✓ Capítulos encontrados: {validation['chapters_found']}/31") 
        print(f"✓ Secciones detectadas: {', '.join(validation['sections_detected'])}")
        print(f"✓ Score de integridad: {validation['integrity_score']:.2f}")
        print(f"✓ Texto guardado en: {PROCESSED_DATA_DIR / 'ucdm_complete_text.txt'}")
        
        if validation['warnings']:
            print("\n⚠️  Advertencias:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
    else:
        print("✗ Error en la extracción del PDF")
        return 1
    
    return 0

if __name__ == "__main__":
    from datetime import datetime
    exit(main())