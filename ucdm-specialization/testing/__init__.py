"""
Framework de testing extendido para UCDM
Casos edge, stress testing y performance monitoring
"""

from .edge_case_generator import EdgeCaseGenerator
from .stress_test_runner import StressTestRunner
from .performance_monitor import PerformanceMonitor

__all__ = [
    'EdgeCaseGenerator',
    'StressTestRunner', 
    'PerformanceMonitor'
]