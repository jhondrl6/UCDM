#!/usr/bin/env python3
"""
Disk Cache (L2) - Cache en disco con compresión y TTL
Implementa almacenamiento persistente para índices compilados y datos de mediano plazo
"""

import os
import gzip
import json
import pickle
import hashlib
import logging
import threading
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class DiskCacheEntry:
    """Entrada del cache en disco"""
    key: str
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime]
    file_path: str
    size_bytes: int
    compressed: bool
    access_count: int
    checksum: str
    
    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'file_path': self.file_path,
            'size_bytes': self.size_bytes,
            'compressed': self.compressed,
            'access_count': self.access_count,
            'checksum': self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiskCacheEntry':
        """Crear instancia desde diccionario"""
        return cls(
            key=data['key'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            file_path=data['file_path'],
            size_bytes=data['size_bytes'],
            compressed=data['compressed'],
            access_count=data['access_count'],
            checksum=data['checksum']
        )

class DiskCache:
    """
    Cache en disco L2 con compresión automática y gestión de TTL
    
    Características:
    - Compresión gzip automática para archivos >1KB
    - TTL configurable por entrada
    - Verificación de integridad con checksums
    - Limpieza automática de archivos expirados
    - Gestión de espacio en disco
    - Thread-safe
    """
    
    def __init__(self, cache_dir: str = "data/cache", max_size_gb: int = 2,
                 default_ttl_hours: int = 24, compression_threshold_kb: int = 1,
                 auto_cleanup: bool = True):
        """
        Inicializar cache en disco
        
        Args:
            cache_dir: Directorio base para cache
            max_size_gb: Tamaño máximo en gigabytes
            default_ttl_hours: TTL por defecto en horas
            compression_threshold_kb: Umbral para compresión en KB
            auto_cleanup: Limpieza automática habilitada
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self.compression_threshold = compression_threshold_kb * 1024
        self.auto_cleanup = auto_cleanup
        
        # Archivos de control
        self.index_file = self.cache_dir / "cache_index.json"
        self.lock_file = self.cache_dir / "cache.lock"
        
        # Estado interno
        self._index: Dict[str, DiskCacheEntry] = {}
        self._lock = threading.RLock()
        self.current_size_bytes = 0
        
        # Métricas
        self.hits = 0
        self.misses = 0
        self.writes = 0
        self.deletes = 0
        self.compressions = 0
        self.created_at = datetime.now()
        
        # Logging
        self.logger = self._setup_logging()
        
        # Inicialización
        self._initialize_cache_dir()
        self._load_index()
        
        self.logger.info(f"DiskCache inicializado - Dir: {cache_dir}, Límite: {max_size_gb}GB")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging específico"""
        logger = logging.getLogger(f"{__name__}.DiskCache")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_cache_dir(self):
        """Crear estructura de directorios"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Crear subdirectorios por tipo
            (self.cache_dir / "responses").mkdir(exist_ok=True)
            (self.cache_dir / "indices").mkdir(exist_ok=True)
            (self.cache_dir / "temp").mkdir(exist_ok=True)
            
        except Exception as e:
            self.logger.error(f"Error creando directorio de cache: {e}")
            raise
    
    def _load_index(self):
        """Cargar índice desde disco"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                # Reconstruir índice
                for key, entry_data in index_data.get('entries', {}).items():
                    try:
                        entry = DiskCacheEntry.from_dict(entry_data)
                        
                        # Verificar que el archivo existe
                        file_path = self.cache_dir / entry.file_path
                        if file_path.exists():
                            self._index[key] = entry
                            self.current_size_bytes += entry.size_bytes
                        else:
                            self.logger.warning(f"Archivo de cache faltante: {entry.file_path}")
                    
                    except Exception as e:
                        self.logger.warning(f"Error cargando entrada de índice {key}: {e}")
                
                self.logger.info(f"Índice cargado - {len(self._index)} entradas, {self.current_size_bytes/1024/1024:.1f}MB")
            
            else:
                self.logger.info("Índice no existe, creando nuevo cache")
                self._save_index()
        
        except Exception as e:
            self.logger.error(f"Error cargando índice: {e}")
            self._index = {}
    
    def _save_index(self):
        """Guardar índice a disco"""
        try:
            index_data = {
                'metadata': {
                    'created_at': self.created_at.isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'entry_count': len(self._index),
                    'total_size_bytes': self.current_size_bytes
                },
                'entries': {key: entry.to_dict() for key, entry in self._index.items()}
            }
            
            # Escribir de forma atómica
            temp_file = self.index_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self.index_file)
            
        except Exception as e:
            self.logger.error(f"Error guardando índice: {e}")
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calcular checksum MD5 de los datos"""
        return hashlib.md5(data).hexdigest()
    
    def _generate_file_path(self, key: str, compressed: bool = False) -> str:
        """Generar ruta de archivo para la clave"""
        # Hash de la clave para evitar caracteres problemáticos
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        
        # Determinar subdirectorio basado en tipo
        if key.startswith('response_'):
            subdir = 'responses'
        elif key.startswith('index_'):
            subdir = 'indices'
        else:
            subdir = 'temp'
        
        extension = '.gz' if compressed else '.cache'
        filename = f"{key_hash}{extension}"
        
        return f"{subdir}/{filename}"
    
    def _compress_data(self, data: bytes) -> Tuple[bytes, bool]:
        """
        Comprimir datos si superan el umbral
        
        Returns:
            Tuple[bytes, bool]: (datos_finales, fue_comprimido)
        """
        if len(data) >= self.compression_threshold:
            try:
                compressed = gzip.compress(data)
                if len(compressed) < len(data) * 0.9:  # Solo si reduce al menos 10%
                    self.compressions += 1
                    return compressed, True
            except Exception as e:
                self.logger.warning(f"Error comprimiendo datos: {e}")
        
        return data, False
    
    def _decompress_data(self, data: bytes, compressed: bool) -> bytes:
        """Descomprimir datos si es necesario"""
        if compressed:
            try:
                return gzip.decompress(data)
            except Exception as e:
                self.logger.error(f"Error descomprimiendo datos: {e}")
                raise
        return data
    
    def _make_room(self, required_bytes: int) -> bool:
        """Hacer espacio expulsando entradas antiguas"""
        # Primero: limpiar expiradas
        expired_count = self._cleanup_expired()
        
        if self.current_size_bytes + required_bytes <= self.max_size_bytes:
            return True
        
        # Segundo: expulsar por antigüedad
        if len(self._index) == 0:
            return required_bytes <= self.max_size_bytes
        
        # Ordenar por última fecha de acceso (más antiguos primero)
        entries_by_age = sorted(
            self._index.items(),
            key=lambda x: x[1].last_accessed
        )
        
        removed_count = 0
        for key, entry in entries_by_age:
            if self.current_size_bytes + required_bytes <= self.max_size_bytes:
                break
            
            try:
                self._remove_entry(key)
                removed_count += 1
            except Exception as e:
                self.logger.warning(f"Error removiendo entrada {key}: {e}")
        
        if removed_count > 0:
            self.logger.debug(f"Removidas {removed_count} entradas para hacer espacio")
        
        return self.current_size_bytes + required_bytes <= self.max_size_bytes
    
    def _remove_entry(self, key: str):
        """Remover entrada del cache y disco"""
        if key in self._index:
            entry = self._index[key]
            
            # Remover archivo
            file_path = self.cache_dir / entry.file_path
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                self.logger.warning(f"Error removiendo archivo {file_path}: {e}")
            
            # Actualizar estado
            self.current_size_bytes -= entry.size_bytes
            del self._index[key]
            self.deletes += 1
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del cache en disco
        
        Args:
            key: Clave de búsqueda
            
        Returns:
            Optional[Any]: Valor si existe y no ha expirado
        """
        with self._lock:
            if key not in self._index:
                self.misses += 1
                return None
            
            entry = self._index[key]
            
            # Verificar expiración
            if entry.is_expired():
                self._remove_entry(key)
                self.misses += 1
                return None
            
            try:
                # Leer archivo
                file_path = self.cache_dir / entry.file_path
                if not file_path.exists():
                    self.logger.warning(f"Archivo de cache faltante: {entry.file_path}")
                    self._remove_entry(key)
                    self.misses += 1
                    return None
                
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                # Verificar integridad
                current_checksum = self._calculate_checksum(data)
                if current_checksum != entry.checksum:
                    self.logger.warning(f"Checksum inválido para {key}, removiendo")
                    self._remove_entry(key)
                    self.misses += 1
                    return None
                
                # Descomprimir si es necesario
                data = self._decompress_data(data, entry.compressed)
                
                # Deserializar
                value = pickle.loads(data)
                
                # Actualizar estadísticas de acceso
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                
                self.hits += 1
                
                # Guardar índice actualizado (de forma asíncrona en producción)
                if self.hits % 10 == 0:  # Cada 10 hits
                    self._save_index()
                
                return value
                
            except Exception as e:
                self.logger.error(f"Error leyendo cache {key}: {e}")
                self._remove_entry(key)
                self.misses += 1
                return None
    
    def put(self, key: str, value: Any, ttl_hours: Optional[int] = None) -> bool:
        """
        Almacenar valor en cache de disco
        
        Args:
            key: Clave única
            value: Valor a almacenar
            ttl_hours: TTL personalizado en horas
            
        Returns:
            bool: True si se almacenó exitosamente
        """
        with self._lock:
            try:
                # Serializar datos
                data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
                
                # Comprimir si es necesario
                final_data, compressed = self._compress_data(data)
                
                # Verificar tamaño
                if len(final_data) > self.max_size_bytes * 0.1:  # Max 10% del cache
                    self.logger.warning(f"Objeto demasiado grande para cache: {len(final_data)/1024/1024:.1f}MB")
                    return False
                
                # Hacer espacio si es necesario
                if not self._make_room(len(final_data)):
                    self.logger.warning("No se pudo hacer espacio en cache de disco")
                    return False
                
                # Generar ruta y checksum
                file_path_str = self._generate_file_path(key, compressed)
                file_path = self.cache_dir / file_path_str
                checksum = self._calculate_checksum(final_data)
                
                # Crear directorio si no existe
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Escribir archivo
                with open(file_path, 'wb') as f:
                    f.write(final_data)
                
                # Calcular TTL
                ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
                expires_at = datetime.now() + ttl if ttl.total_seconds() > 0 else None
                
                # Crear entrada
                entry = DiskCacheEntry(
                    key=key,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    expires_at=expires_at,
                    file_path=file_path_str,
                    size_bytes=len(final_data),
                    compressed=compressed,
                    access_count=0,
                    checksum=checksum
                )
                
                # Remover entrada anterior si existe
                if key in self._index:
                    self._remove_entry(key)
                
                # Agregar nueva entrada
                self._index[key] = entry
                self.current_size_bytes += len(final_data)
                self.writes += 1
                
                # Guardar índice
                self._save_index()
                
                self.logger.debug(f"Almacenado en cache: {key} ({len(final_data)/1024:.1f}KB, comprimido: {compressed})")
                return True
                
            except Exception as e:
                self.logger.error(f"Error almacenando en cache {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Eliminar entrada del cache"""
        with self._lock:
            if key in self._index:
                self._remove_entry(key)
                self._save_index()
                return True
            return False
    
    def _cleanup_expired(self) -> int:
        """Limpiar entradas expiradas"""
        expired_keys = []
        for key, entry in self._index.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
        
        if expired_keys:
            self._save_index()
            self.logger.debug(f"Limpiadas {len(expired_keys)} entradas expiradas")
        
        return len(expired_keys)
    
    def cleanup(self) -> Dict[str, int]:
        """
        Limpieza completa del cache
        
        Returns:
            Dict con estadísticas de limpieza
        """
        with self._lock:
            expired_count = self._cleanup_expired()
            
            # Verificar archivos huérfanos
            orphaned_count = 0
            for cache_subdir in ['responses', 'indices', 'temp']:
                subdir_path = self.cache_dir / cache_subdir
                if subdir_path.exists():
                    for file_path in subdir_path.glob('*'):
                        # Buscar si el archivo está en el índice
                        found = False
                        for entry in self._index.values():
                            if self.cache_dir / entry.file_path == file_path:
                                found = True
                                break
                        
                        if not found:
                            try:
                                file_path.unlink()
                                orphaned_count += 1
                            except Exception as e:
                                self.logger.warning(f"Error removiendo archivo huérfano {file_path}: {e}")
            
            return {
                'expired_removed': expired_count,
                'orphaned_removed': orphaned_count,
                'total_entries': len(self._index),
                'total_size_mb': round(self.current_size_bytes / 1024 / 1024, 2)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_ratio = self.hits / total_requests if total_requests > 0 else 0.0
            
            uptime = datetime.now() - self.created_at
            
            return {
                "performance": {
                    "hits": self.hits,
                    "misses": self.misses,
                    "hit_ratio": round(hit_ratio, 3),
                    "writes": self.writes,
                    "deletes": self.deletes,
                    "compressions": self.compressions
                },
                "storage": {
                    "current_size_mb": round(self.current_size_bytes / 1024 / 1024, 2),
                    "max_size_gb": round(self.max_size_bytes / 1024 / 1024 / 1024, 2),
                    "usage_percent": round((self.current_size_bytes / self.max_size_bytes) * 100, 1),
                    "entry_count": len(self._index),
                    "cache_dir": str(self.cache_dir)
                },
                "config": {
                    "default_ttl_hours": self.default_ttl.total_seconds() / 3600,
                    "compression_threshold_kb": self.compression_threshold / 1024,
                    "auto_cleanup": self.auto_cleanup
                },
                "uptime_hours": round(uptime.total_seconds() / 3600, 2)
            }
    
    def clear(self):
        """Limpiar todo el cache"""
        with self._lock:
            cleared_count = len(self._index)
            
            # Remover todos los archivos
            for key in list(self._index.keys()):
                self._remove_entry(key)
            
            self._save_index()
            self.logger.info(f"Cache de disco limpiado - {cleared_count} entradas removidas")


def create_disk_cache(cache_dir: str = "data/cache", max_size_gb: int = 2) -> DiskCache:
    """
    Crear instancia de DiskCache con configuración
    
    Args:
        cache_dir: Directorio para cache
        max_size_gb: Tamaño máximo en GB
        
    Returns:
        DiskCache: Instancia configurada
    """
    return DiskCache(cache_dir=cache_dir, max_size_gb=max_size_gb)