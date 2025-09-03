#!/usr/bin/env python3
"""
Performance Monitor - Monitor de rendimiento en tiempo real
"""

import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import deque, defaultdict

class PerformanceMonitor:
    """Monitor básico de performance"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def record_metric(self, name: str, value: float):
        """Registrar métrica"""
        self.metrics[name].append((datetime.now(), value))
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {"metrics": len(self.metrics)}

def create_performance_monitor() -> PerformanceMonitor:
    """Crear monitor de performance"""
    return PerformanceMonitor()