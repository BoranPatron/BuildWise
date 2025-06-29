import time
import psutil
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = None
    Histogram = None
    Gauge = None
    generate_latest = None

from .database import check_db_connection, get_db_stats
from .cache import cache_service
from .config import get_settings

settings = get_settings()

# Prometheus metrics
if PROMETHEUS_AVAILABLE:
    REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
    ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')
    DB_CONNECTION_POOL_SIZE = Gauge('db_connection_pool_size', 'Database connection pool size')
    DB_CONNECTION_POOL_OVERFLOW = Gauge('db_connection_pool_overflow', 'Database connection pool overflow')
    CACHE_HIT_RATIO = Gauge('cache_hit_ratio', 'Cache hit ratio')
    SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_bytes', 'System memory usage in bytes')
    SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
else:
    # Dummy metrics for when prometheus is not available
    class DummyMetric:
        def labels(self, **kwargs): return self
        def inc(self): pass
        def observe(self, value): pass
        def set(self, value): pass
    
    REQUEST_COUNT = DummyMetric()
    REQUEST_DURATION = DummyMetric()
    ACTIVE_CONNECTIONS = DummyMetric()
    DB_CONNECTION_POOL_SIZE = DummyMetric()
    DB_CONNECTION_POOL_OVERFLOW = DummyMetric()
    CACHE_HIT_RATIO = DummyMetric()
    SYSTEM_MEMORY_USAGE = DummyMetric()
    SYSTEM_CPU_USAGE = DummyMetric()

class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_times: list = []
        self.error_counts: Dict[str, int] = {}
        self.last_metrics_update = time.time()
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        if PROMETHEUS_AVAILABLE:
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        self.request_times.append(duration)
        if len(self.request_times) > 1000:  # Keep only last 1000 requests
            self.request_times.pop(0)
    
    def record_error(self, error_type: str):
        """Record error metrics."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    async def update_system_metrics(self):
        """Update system-level metrics."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            if PROMETHEUS_AVAILABLE:
                SYSTEM_MEMORY_USAGE.set(memory.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if PROMETHEUS_AVAILABLE:
                SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # Database metrics
            if settings.environment == "production":
                db_stats = await get_db_stats()
                if PROMETHEUS_AVAILABLE:
                    DB_CONNECTION_POOL_SIZE.set(db_stats.get("pool_size", 0))
                    DB_CONNECTION_POOL_OVERFLOW.set(db_stats.get("overflow", 0))
            
            # Cache metrics
            cache_stats = await cache_service.get_stats()
            if cache_stats.get("enabled") and not cache_stats.get("error"):
                hits = cache_stats.get("keyspace_hits", 0)
                misses = cache_stats.get("keyspace_misses", 0)
                total = hits + misses
                if total > 0 and PROMETHEUS_AVAILABLE:
                    hit_ratio = hits / total
                    CACHE_HIT_RATIO.set(hit_ratio)
            
            self.last_metrics_update = time.time()
            
        except Exception as e:
            print(f"Error updating system metrics: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        if not self.request_times:
            return {"error": "No request data available"}
        
        sorted_times = sorted(self.request_times)
        return {
            "total_requests": len(self.request_times),
            "average_response_time": sum(self.request_times) / len(self.request_times),
            "median_response_time": sorted_times[len(sorted_times) // 2],
            "p95_response_time": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_response_time": sorted_times[int(len(sorted_times) * 0.99)],
            "min_response_time": min(self.request_times),
            "max_response_time": max(self.request_times),
            "error_counts": self.error_counts,
            "uptime_seconds": time.time() - self.start_time
        }

# Global monitor instance
performance_monitor = PerformanceMonitor()

class HealthChecker:
    """Health check service for all system components."""
    
    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """Check database health."""
        try:
            is_healthy = await check_db_connection()
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "component": "database",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "connection": "ok" if is_healthy else "failed"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "component": "database",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    @staticmethod
    async def check_cache() -> Dict[str, Any]:
        """Check cache health."""
        try:
            stats = await cache_service.get_stats()
            is_healthy = stats.get("enabled") and not stats.get("error")
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "component": "cache",
                "timestamp": datetime.utcnow().isoformat(),
                "details": stats
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "component": "cache",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    @staticmethod
    async def check_system() -> Dict[str, Any]:
        """Check system resources."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            is_healthy = (
                memory.percent < 90 and
                cpu_percent < 90 and
                disk.percent < 90
            )
            
            return {
                "status": "healthy" if is_healthy else "warning",
                "component": "system",
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "memory_percent": memory.percent,
                    "cpu_percent": cpu_percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "component": "system",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    @staticmethod
    async def comprehensive_health_check() -> Dict[str, Any]:
        """Perform comprehensive health check of all components."""
        checks = await asyncio.gather(
            HealthChecker.check_database(),
            HealthChecker.check_cache(),
            HealthChecker.check_system(),
            return_exceptions=True
        )
        
        overall_status = "healthy"
        for check in checks:
            if isinstance(check, Exception):
                overall_status = "unhealthy"
                break
            if isinstance(check, dict) and check.get("status") == "unhealthy":
                overall_status = "unhealthy"
            elif isinstance(check, dict) and check.get("status") == "warning" and overall_status == "healthy":
                overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": checks[0] if not isinstance(checks[0], Exception) else {"error": str(checks[0])},
                "cache": checks[1] if not isinstance(checks[1], Exception) else {"error": str(checks[1])},
                "system": checks[2] if not isinstance(checks[2], Exception) else {"error": str(checks[2])}
            }
        }

# Metrics endpoint for Prometheus
async def get_metrics():
    """Get Prometheus metrics."""
    await performance_monitor.update_system_metrics()
    if PROMETHEUS_AVAILABLE and generate_latest:
        return generate_latest()
    return "Prometheus metrics not available"

# Health check endpoint
async def get_health():
    """Get comprehensive health status."""
    return await HealthChecker.comprehensive_health_check() 