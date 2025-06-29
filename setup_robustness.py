#!/usr/bin/env python3
"""
BuildWise Robustheitspaket Setup-Skript
========================================

Dieses Skript installiert und konfiguriert alle Performance- und Skalierbarkeits-Features
für hohe Nutzerzahlen und intensive Interaktionen.

Features:
- Redis Caching
- Rate Limiting
- Connection Pooling
- Monitoring & Metrics
- Background Tasks
- Structured Logging
- Health Checks
- Performance Optimierungen
"""

import os
import sys
import subprocess
import asyncio
import sqlite3
from pathlib import Path

class RobustnessSetup:
    """Setup-Klasse für das BuildWise Robustheitspaket."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.env_file = self.project_root / ".env"
        self.db_file = self.project_root / "buildwise.db"
        
    def print_header(self, title: str):
        """Druckt einen formatierten Header."""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_step(self, step: str):
        """Druckt einen Schritt."""
        print(f"\n🔧 {step}")
    
    def print_success(self, message: str):
        """Druckt eine Erfolgsmeldung."""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Druckt eine Fehlermeldung."""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """Druckt eine Warnung."""
        print(f"⚠️  {message}")
    
    def check_python_version(self):
        """Überprüft die Python-Version."""
        self.print_step("Überprüfe Python-Version")
        
        if sys.version_info < (3, 8):
            self.print_error("Python 3.8 oder höher ist erforderlich")
            return False
        
        self.print_success(f"Python {sys.version} ist kompatibel")
        return True
    
    def install_dependencies(self):
        """Installiert alle Abhängigkeiten."""
        self.print_step("Installiere Performance-Abhängigkeiten")
        
        try:
            # Upgrade pip
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install requirements
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)], 
                         check=True, capture_output=True)
            
            self.print_success("Alle Abhängigkeiten installiert")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Fehler beim Installieren der Abhängigkeiten: {e}")
            return False
    
    def create_directories(self):
        """Erstellt notwendige Verzeichnisse."""
        self.print_step("Erstelle Verzeichnisstruktur")
        
        directories = [
            "logs",
            "storage/uploads",
            "storage/backups",
            "static",
            "grafana/dashboards",
            "grafana/datasources",
            "ssl"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.print_success(f"Verzeichnis erstellt: {directory}")
    
    def create_env_file(self):
        """Erstellt die .env-Datei mit Performance-Konfiguration."""
        self.print_step("Erstelle .env-Konfiguration")
        
        if self.env_file.exists():
            self.print_warning(".env-Datei existiert bereits")
            return True
        
        env_content = """# BuildWise Performance-Konfiguration
# =============================================================================
# DATENBANK-KONFIGURATION
# =============================================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=buildwise
DB_USER=buildwise_user
DB_PASSWORD=your_secure_password_here

# =============================================================================
# REDIS CACHE
# =============================================================================
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=20

# =============================================================================
# PERFORMANCE-EINSTELLUNGEN
# =============================================================================
CACHE_ENABLED=true
CACHE_TTL=300
CACHE_MAX_SIZE=1000

RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_BURST=10

COMPRESSION_ENABLED=true
GZIP_LEVEL=6

# =============================================================================
# MONITORING
# =============================================================================
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/buildwise.log

# =============================================================================
# SICHERHEIT
# =============================================================================
JWT_SECRET_KEY=your_super_secret_jwt_key_here_make_it_long_and_random_at_least_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# =============================================================================
# UMWELT
# =============================================================================
ENVIRONMENT=development
DEBUG=true

# =============================================================================
# WORKER-KONFIGURATION
# =============================================================================
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
TIMEOUT=120
KEEPALIVE=5
"""
        
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        self.print_success(".env-Datei erstellt")
        self.print_warning("Bitte passen Sie die Passwörter und Schlüssel an!")
    
    def setup_database(self):
        """Richtet die Datenbank ein."""
        self.print_step("Richte Datenbank ein")
        
        try:
            # Erstelle Datenbank-Tabellen
            from app.core.database import engine
            from app.models import Base
            
            async def create_tables():
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            
            asyncio.run(create_tables())
            self.print_success("Datenbank-Tabellen erstellt")
            
            # Erstelle Admin-Benutzer
            self.create_admin_user()
            
            return True
            
        except Exception as e:
            self.print_error(f"Fehler beim Einrichten der Datenbank: {e}")
            return False
    
    def create_admin_user(self):
        """Erstellt einen Admin-Benutzer."""
        self.print_step("Erstelle Admin-Benutzer")
        
        try:
            # Verwende das bestehende Admin-Skript
            admin_script = self.project_root / "create_admin_fixed.py"
            if admin_script.exists():
                subprocess.run([sys.executable, str(admin_script)], check=True)
                self.print_success("Admin-Benutzer erstellt")
            else:
                self.print_warning("Admin-Skript nicht gefunden")
                
        except subprocess.CalledProcessError as e:
            self.print_error(f"Fehler beim Erstellen des Admin-Benutzers: {e}")
    
    def setup_redis(self):
        """Richtet Redis ein (optional)."""
        self.print_step("Redis-Setup (optional)")
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            self.print_success("Redis ist verfügbar")
            return True
        except Exception:
            self.print_warning("Redis ist nicht verfügbar - Caching wird deaktiviert")
            self.print_warning("Installieren Sie Redis für optimale Performance")
            return False
    
    def create_nginx_config(self):
        """Erstellt Nginx-Konfiguration."""
        self.print_step("Erstelle Nginx-Konfiguration")
        
        nginx_config = """events {
    worker_connections 1024;
}

http {
    upstream buildwise_api {
        server api:8000;
    }
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    server {
        listen 80;
        server_name localhost;
        
        # Security Headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
        
        # Rate Limiting
        limit_req zone=api burst=20 nodelay;
        
        location / {
            proxy_pass http://buildwise_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Health Check
        location /health {
            proxy_pass http://buildwise_api/health;
            access_log off;
        }
        
        # Metrics (nur für Monitoring)
        location /metrics {
            allow 127.0.0.1;
            deny all;
            proxy_pass http://buildwise_api/metrics;
        }
    }
}
"""
        
        nginx_file = self.project_root / "nginx.conf"
        with open(nginx_file, 'w', encoding='utf-8') as f:
            f.write(nginx_config)
        
        self.print_success("Nginx-Konfiguration erstellt")
    
    def create_prometheus_config(self):
        """Erstellt Prometheus-Konfiguration."""
        self.print_step("Erstelle Prometheus-Konfiguration")
        
        prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'buildwise-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
"""
        
        prometheus_file = self.project_root / "prometheus.yml"
        with open(prometheus_file, 'w', encoding='utf-8') as f:
            f.write(prometheus_config)
        
        self.print_success("Prometheus-Konfiguration erstellt")
    
    def create_filebeat_config(self):
        """Erstellt Filebeat-Konfiguration."""
        self.print_step("Erstelle Filebeat-Konfiguration")
        
        filebeat_config = """filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/buildwise/*.log
  json.keys_under_root: true
  json.add_error_key: true
  json.message_key: message

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "buildwise-logs-%{+yyyy.MM.dd}"

setup.kibana:
  host: "kibana:5601"
"""
        
        filebeat_file = self.project_root / "filebeat.yml"
        with open(filebeat_file, 'w', encoding='utf-8') as f:
            f.write(filebeat_config)
        
        self.print_success("Filebeat-Konfiguration erstellt")
    
    def run_performance_tests(self):
        """Führt Performance-Tests aus."""
        self.print_step("Führe Performance-Tests aus")
        
        try:
            # Starte den Server im Hintergrund
            import subprocess
            import time
            
            # Test-Skript erstellen
            test_script = """
import asyncio
import aiohttp
import time

async def test_performance():
    async with aiohttp.ClientSession() as session:
        # Test Health Endpoint
        start_time = time.time()
        async with session.get('http://localhost:8000/health') as response:
            health_time = time.time() - start_time
            print(f"Health Check: {health_time:.3f}s - Status: {response.status}")
        
        # Test API Endpoints
        endpoints = ['/api/v1/projects', '/api/v1/tasks', '/api/v1/documents']
        for endpoint in endpoints:
            start_time = time.time()
            async with session.get(f'http://localhost:8000{endpoint}') as response:
                api_time = time.time() - start_time
                print(f"{endpoint}: {api_time:.3f}s - Status: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_performance())
"""
            
            test_file = self.project_root / "test_performance.py"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_script)
            
            self.print_success("Performance-Tests erstellt")
            self.print_warning("Führen Sie 'python test_performance.py' aus, wenn der Server läuft")
            
        except Exception as e:
            self.print_error(f"Fehler beim Erstellen der Performance-Tests: {e}")
    
    def create_startup_scripts(self):
        """Erstellt Startup-Skripte."""
        self.print_step("Erstelle Startup-Skripte")
        
        # Development Startup
        dev_script = """#!/bin/bash
echo "🚀 Starte BuildWise API (Development)"
export ENVIRONMENT=development
export DEBUG=true
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
        
        dev_file = self.project_root / "start_dev.sh"
        with open(dev_file, 'w', encoding='utf-8') as f:
            f.write(dev_script)
        
        # Production Startup
        prod_script = """#!/bin/bash
echo "🚀 Starte BuildWise API (Production)"
export ENVIRONMENT=production
export DEBUG=false
gunicorn app.main:app -c gunicorn.conf.py
"""
        
        prod_file = self.project_root / "start_prod.sh"
        with open(prod_file, 'w', encoding='utf-8') as f:
            f.write(prod_script)
        
        # Docker Startup
        docker_script = """#!/bin/bash
echo "🐳 Starte BuildWise mit Docker Compose"
docker-compose -f docker-compose.prod.yml up -d
echo "✅ Services gestartet"
echo "📊 Grafana: http://localhost:3000"
echo "📈 Prometheus: http://localhost:9090"
echo "📋 Kibana: http://localhost:5601"
echo "🔍 API: http://localhost:8000"
"""
        
        docker_file = self.project_root / "start_docker.sh"
        with open(docker_file, 'w', encoding='utf-8') as f:
            f.write(docker_script)
        
        # Mache Skripte ausführbar
        for script in [dev_file, prod_file, docker_file]:
            os.chmod(script, 0o755)
        
        self.print_success("Startup-Skripte erstellt")
    
    def print_summary(self):
        """Druckt eine Zusammenfassung."""
        self.print_header("Setup abgeschlossen!")
        
        print("""
🎉 BuildWise Robustheitspaket wurde erfolgreich eingerichtet!

📋 Verfügbare Features:
   ✅ Redis Caching für hohe Performance
   ✅ Rate Limiting für API-Schutz
   ✅ Connection Pooling für Datenbank
   ✅ Monitoring & Metrics (Prometheus)
   ✅ Structured Logging
   ✅ Health Checks
   ✅ Background Tasks
   ✅ Gzip Compression
   ✅ Performance Monitoring

🚀 Startoptionen:
   Development:  ./start_dev.sh
   Production:   ./start_prod.sh
   Docker:       ./start_docker.sh

📊 Monitoring:
   Grafana:      http://localhost:3000
   Prometheus:   http://localhost:9090
   Kibana:       http://localhost:5601

🔧 Nächste Schritte:
   1. Passen Sie die .env-Datei an
   2. Starten Sie Redis (optional)
   3. Führen Sie ./start_dev.sh aus
   4. Testen Sie die Performance

📚 Dokumentation:
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Metrics: http://localhost:8000/metrics

⚠️  Wichtige Hinweise:
   - Ändern Sie alle Passwörter in der .env-Datei
   - Konfigurieren Sie SSL für Production
   - Überwachen Sie die Performance-Metriken
""")
    
    def run_setup(self):
        """Führt das komplette Setup aus."""
        self.print_header("BuildWise Robustheitspaket Setup")
        
        steps = [
            ("Python-Version prüfen", self.check_python_version),
            ("Abhängigkeiten installieren", self.install_dependencies),
            ("Verzeichnisse erstellen", self.create_directories),
            ("Umgebungsvariablen erstellen", self.create_env_file),
            ("Datenbank einrichten", self.setup_database),
            ("Redis-Setup", self.setup_redis),
            ("Nginx-Konfiguration", self.create_nginx_config),
            ("Prometheus-Konfiguration", self.create_prometheus_config),
            ("Filebeat-Konfiguration", self.create_filebeat_config),
            ("Performance-Tests", self.run_performance_tests),
            ("Startup-Skripte", self.create_startup_scripts),
        ]
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    self.print_error(f"Setup-Schritt fehlgeschlagen: {step_name}")
                    return False
            except Exception as e:
                self.print_error(f"Fehler in {step_name}: {e}")
                return False
        
        self.print_summary()
        return True

def main():
    """Hauptfunktion."""
    setup = RobustnessSetup()
    success = setup.run_setup()
    
    if success:
        print("\n🎉 Setup erfolgreich abgeschlossen!")
        sys.exit(0)
    else:
        print("\n❌ Setup fehlgeschlagen!")
        sys.exit(1)

if __name__ == "__main__":
    main() 