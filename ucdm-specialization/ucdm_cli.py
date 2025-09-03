#!/usr/bin/env python3
"""
CLI Interactiva para UCDM
Interfaz de línea de comandos para consultas interactivas sobre Un Curso de Milagros
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Importar rich para interfaz mejorada
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

sys.path.append(str(Path(__file__).parent))
from config.settings import *
from training.response_engine import UCDMResponseEngine

class UCDMCLIInterface:
    """Interfaz CLI interactiva para UCDM"""
    
    def __init__(self):
        self.engine = UCDMResponseEngine()
        self.console = Console() if HAS_RICH else None
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(level=logging.WARNING)  # Solo warnings para CLI
        self.logger = logging.getLogger(__name__)
    
    def print_styled(self, text: str, style: str = "default") -> None:
        """Imprimir texto con estilo (con o sin rich)"""
        if self.console and HAS_RICH:
            if style == "title":
                self.console.print(text, style="bold blue")
            elif style == "success":
                self.console.print(text, style="bold green")
            elif style == "error":
                self.console.print(text, style="bold red")
            elif style == "warning":
                self.console.print(text, style="bold yellow")
            elif style == "info":
                self.console.print(text, style="cyan")
            else:
                self.console.print(text)
        else:
            print(text)
    
    def show_welcome_message(self) -> None:
        """Mostrar mensaje de bienvenida"""
        if self.console and HAS_RICH:
            welcome_text = """
# 🌟 UCDM - Un Curso de Milagros 🌟

**Bienvenido al asistente interactivo de Un Curso de Milagros**

Este sistema te permite:
• 📖 Consultar lecciones específicas del Curso
• 📅 Obtener la lección del día
• 🔍 Explorar conceptos como perdón, amor, paz
• 🌙 Reflexiones nocturnas y aplicaciones prácticas
• ✨ Respuestas estructuradas con la metodología UCDM

*"Los milagros ocurren naturalmente como expresiones de amor"*
            """
            
            panel = Panel(
                Markdown(welcome_text),
                title="Un Curso de Milagros - CLI",
                border_style="blue"
            )
            self.console.print(panel)
        else:
            print("=" * 60)
            print("🌟 UCDM - Un Curso de Milagros 🌟")
            print("=" * 60)
            print("\nBienvenido al asistente interactivo de Un Curso de Milagros")
            print("\nEste sistema te permite:")
            print("• Consultar lecciones específicas del Curso")
            print("• Obtener la lección del día")
            print("• Explorar conceptos como perdón, amor, paz")
            print("• Reflexiones nocturnas y aplicaciones prácticas")
            print("• Respuestas estructuradas con la metodología UCDM")
            print("\n\"Los milagros ocurren naturalmente como expresiones de amor\"")
            print("=" * 60)
    
    def show_help_menu(self) -> None:
        """Mostrar menú de ayuda"""
        if self.console and HAS_RICH:
            help_table = Table(title="Comandos Disponibles")
            help_table.add_column("Comando", style="cyan", width=20)
            help_table.add_column("Descripción", style="white")
            help_table.add_column("Ejemplo", style="green")
            
            commands = [
                ("leccion [número]", "Consultar lección específica", "leccion 1"),
                ("hoy", "Lección del día actual", "hoy"),
                ("concepto [tema]", "Explorar concepto UCDM", "concepto perdón"),
                ("reflexion", "Reflexión nocturna", "reflexion"),
                ("buscar [texto]", "Búsqueda libre", "buscar milagros"),
                ("stats", "Estadísticas del sistema", "stats"),
                ("help", "Mostrar esta ayuda", "help"),
                ("salir", "Salir del programa", "salir")
            ]
            
            for cmd, desc, example in commands:
                help_table.add_row(cmd, desc, example)
            
            self.console.print(help_table)
        else:
            print("\n📋 COMANDOS DISPONIBLES:")
            print("leccion [número] - Consultar lección específica (ej: leccion 1)")
            print("hoy              - Lección del día actual")
            print("concepto [tema]  - Explorar concepto UCDM (ej: concepto perdón)")
            print("reflexion        - Reflexión nocturna")
            print("buscar [texto]   - Búsqueda libre (ej: buscar milagros)")
            print("stats            - Estadísticas del sistema")
            print("help             - Mostrar esta ayuda")
            print("salir            - Salir del programa")
    
    def show_system_stats(self) -> None:
        """Mostrar estadísticas del sistema"""
        stats = {
            "lecciones_disponibles": len(self.engine.lessons_index),
            "conceptos_indexados": len(self.engine.concept_index),
            "fecha_carga": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        if self.console and HAS_RICH:
            stats_table = Table(title="Estadísticas del Sistema UCDM")
            stats_table.add_column("Métrica", style="cyan")
            stats_table.add_column("Valor", style="green")
            
            stats_table.add_row("Lecciones Disponibles", str(stats["lecciones_disponibles"]))
            stats_table.add_row("Conceptos Indexados", str(stats["conceptos_indexados"]))
            stats_table.add_row("Última Actualización", stats["fecha_carga"])
            stats_table.add_row("Cobertura", f"{(stats['lecciones_disponibles']/365)*100:.1f}%")
            
            self.console.print(stats_table)
        else:
            print(f"\n📊 ESTADÍSTICAS DEL SISTEMA:")
            print(f"   Lecciones disponibles: {stats['lecciones_disponibles']}")
            print(f"   Conceptos indexados: {stats['conceptos_indexados']}")
            print(f"   Última actualización: {stats['fecha_carga']}")
            print(f"   Cobertura: {(stats['lecciones_disponibles']/365)*100:.1f}%")
    
    def format_response(self, response: str) -> None:
        """Formatear y mostrar respuesta"""
        if self.console and HAS_RICH:
            # Separar la respuesta en secciones
            sections = response.split("**")
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                if section.startswith("HOOK INICIAL"):
                    self.console.print(f"\n🎯 {section}", style="bold blue")
                elif section.startswith("APLICACIÓN PRÁCTICA"):
                    self.console.print(f"\n⚡ {section}", style="bold green")
                elif section.startswith("INTEGRACIÓN EXPERIENCIAL"):
                    self.console.print(f"\n🌿 {section}", style="bold cyan")
                elif section.startswith("CIERRE MOTIVADOR"):
                    self.console.print(f"\n✨ {section}", style="bold magenta")
                else:
                    self.console.print(section)
        else:
            print(f"\n{response}")
    
    def process_command(self, command: str) -> bool:
        """Procesar comando ingresado. Retorna False si debe salir"""
        command = command.strip().lower()
        
        if not command:
            return True
        
        if command in ['salir', 'exit', 'quit']:
            self.print_styled("\n🙏 Que la paz del Curso te acompañe. ¡Hasta pronto!", "success")
            return False
        
        elif command == 'help':
            self.show_help_menu()
        
        elif command == 'stats':
            self.show_system_stats()
        
        elif command == 'hoy':
            self.print_styled("\n🌅 Consultando la lección del día...", "info")
            result = self.engine.process_query("¿Cuál es la lección de hoy?")
            self.format_response(result['response'])
        
        elif command == 'reflexion':
            self.print_styled("\n🌙 Generando reflexión nocturna...", "info")
            result = self.engine.process_query("Necesito una reflexión para antes de dormir")
            self.format_response(result['response'])
        
        elif command.startswith('leccion '):
            try:
                lesson_num = int(command.split()[1])
                if 1 <= lesson_num <= 365:
                    self.print_styled(f"\n📖 Consultando Lección {lesson_num}...", "info")
                    result = self.engine.process_query(f"Explícame la Lección {lesson_num}")
                    self.format_response(result['response'])
                else:
                    self.print_styled("❌ Error: El número de lección debe estar entre 1 y 365", "error")
            except (ValueError, IndexError):
                self.print_styled("❌ Error: Formato incorrecto. Usa: leccion [número]", "error")
        
        elif command.startswith('concepto '):
            concept = ' '.join(command.split()[1:])
            self.print_styled(f"\n🔍 Explorando concepto: {concept}...", "info")
            result = self.engine.process_query(f"Háblame sobre {concept} en UCDM")
            self.format_response(result['response'])
        
        elif command.startswith('buscar '):
            query = ' '.join(command.split()[1:])
            self.print_styled(f"\n🔎 Buscando: {query}...", "info")
            result = self.engine.process_query(query)
            self.format_response(result['response'])
        
        else:
            # Tratar como consulta libre
            self.print_styled(f"\n💭 Procesando consulta...", "info")
            result = self.engine.process_query(command)
            self.format_response(result['response'])
        
        return True
    
    def run_interactive_mode(self) -> None:
        """Ejecutar modo interactivo"""
        self.show_welcome_message()
        
        # Cargar datos del sistema
        self.print_styled("\n🔄 Cargando datos del sistema...", "info")
        if not self.engine.load_data():
            self.print_styled("❌ Error: No se pudieron cargar los datos del sistema", "error")
            self.print_styled("   Asegúrate de haber ejecutado primero los scripts de extracción", "warning")
            return
        
        self.print_styled("✅ Sistema cargado exitosamente", "success")
        self.print_styled("\n💡 Escribe 'help' para ver los comandos disponibles", "info")
        
        # Loop principal
        while True:
            try:
                if self.console and HAS_RICH:
                    command = Prompt.ask("\n[bold blue]UCDM[/bold blue]", default="help")
                else:
                    command = input("\nUCDM> ").strip()
                
                if not self.process_command(command):
                    break
                    
            except KeyboardInterrupt:
                self.print_styled("\n\n🙏 Que la paz del Curso te acompañe. ¡Hasta pronto!", "success")
                break
            except Exception as e:
                self.print_styled(f"\n❌ Error inesperado: {str(e)}", "error")
                self.print_styled("💡 Escribe 'help' si necesitas ayuda", "info")

def create_argument_parser():
    """Crear parser de argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="CLI Interactiva para Un Curso de Milagros",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python ucdm_cli.py                    # Modo interactivo
  python ucdm_cli.py --leccion 1        # Consultar lección específica
  python ucdm_cli.py --hoy              # Lección del día
  python ucdm_cli.py --concepto perdón  # Explorar concepto
  python ucdm_cli.py --query "¿Qué es el amor?"  # Consulta libre
        """
    )
    
    parser.add_argument('--leccion', '-l', type=int, metavar='N',
                       help='Consultar lección específica (1-365)')
    
    parser.add_argument('--hoy', action='store_true',
                       help='Mostrar lección del día')
    
    parser.add_argument('--concepto', '-c', type=str, metavar='CONCEPTO',
                       help='Explorar concepto específico de UCDM')
    
    parser.add_argument('--reflexion', '-r', action='store_true',
                       help='Generar reflexión nocturna')
    
    parser.add_argument('--query', '-q', type=str, metavar='CONSULTA',
                       help='Realizar consulta libre')
    
    parser.add_argument('--stats', action='store_true',
                       help='Mostrar estadísticas del sistema')
    
    parser.add_argument('--no-interactive', action='store_true',
                       help='No entrar en modo interactivo después de ejecutar comando')
    
    return parser

def main():
    """Función principal"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    cli = UCDMCLIInterface()
    
    # Si no hay argumentos, ir directo a modo interactivo
    if len(sys.argv) == 1:
        cli.run_interactive_mode()
        return 0
    
    # Procesar argumentos específicos
    if not cli.engine.load_data():
        cli.print_styled("❌ Error: No se pudieron cargar los datos del sistema", "error")
        cli.print_styled("   Ejecuta primero: python extraction/pdf_extractor.py", "warning")
        return 1
    
    command_executed = False
    
    if args.stats:
        cli.show_system_stats()
        command_executed = True
    
    if args.hoy:
        cli.print_styled("🌅 Lección del día:", "title")
        result = cli.engine.process_query("¿Cuál es la lección de hoy?")
        cli.format_response(result['response'])
        command_executed = True
    
    if args.leccion:
        if 1 <= args.leccion <= 365:
            cli.print_styled(f"📖 Lección {args.leccion}:", "title")
            result = cli.engine.process_query(f"Explícame la Lección {args.leccion}")
            cli.format_response(result['response'])
            command_executed = True
        else:
            cli.print_styled("❌ Error: El número de lección debe estar entre 1 y 365", "error")
            return 1
    
    if args.concepto:
        cli.print_styled(f"🔍 Concepto: {args.concepto}", "title")
        result = cli.engine.process_query(f"Háblame sobre {args.concepto} en UCDM")
        cli.format_response(result['response'])
        command_executed = True
    
    if args.reflexion:
        cli.print_styled("🌙 Reflexión nocturna:", "title")
        result = cli.engine.process_query("Necesito una reflexión para antes de dormir")
        cli.format_response(result['response'])
        command_executed = True
    
    if args.query:
        cli.print_styled(f"💭 Consulta: {args.query}", "title")
        result = cli.engine.process_query(args.query)
        cli.format_response(result['response'])
        command_executed = True
    
    # Si se ejecutó un comando y no se especificó --no-interactive, entrar en modo interactivo
    if command_executed and not args.no_interactive:
        cli.print_styled("\n" + "="*50, "info")
        cli.print_styled("💡 Entrando en modo interactivo. Escribe 'salir' para terminar.", "info")
        cli.run_interactive_mode()
    elif not command_executed:
        # Si no se ejecutó ningún comando, mostrar ayuda y entrar en modo interactivo
        parser.print_help()
        cli.print_styled("\n💡 Entrando en modo interactivo...", "info")
        cli.run_interactive_mode()
    
    return 0

if __name__ == "__main__":
    exit(main())