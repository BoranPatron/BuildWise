#!/usr/bin/env python3
"""
Debug-Skript zur Analyse der Audit Trail-Probleme und Datenbank-Synchronisation
"""

import sqlite3
import os
from datetime import datetime, timedelta

def debug_audit_trail_analysis():
    """Analysiert die Audit Trail-Probleme und Datenbank-Synchronisation"""
    print("🔍 Analysiere Audit Trail-Probleme...")
    
    # Datenbank-Pfad
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return
    
    print(f"✅ Datenbank gefunden: {db_path}")
    print(f"📊 Größe: {os.path.getsize(db_path)} Bytes")
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Tabellen auflisten
        print("\n1️⃣ DATENBANK-TABELLEN:")
        print("-" * 25)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"   📋 Tabellen gefunden: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # 2. Audit Logs analysieren
        print("\n2️⃣ AUDIT LOGS ANALYSE:")
        print("-" * 25)
        
        # Prüfe ob audit_logs Tabelle existiert
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs';")
        if not cursor.fetchone():
            print("   ❌ audit_logs Tabelle nicht gefunden!")
            return
        
        # Gesamte Audit Logs
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total_audit_logs = cursor.fetchone()[0]
        print(f"   📊 Gesamte Audit Logs: {total_audit_logs}")
        
        # Audit Logs seit 14:38 Uhr
        target_time = "2024-07-19 14:38:00"
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE created_at >= ?", (target_time,))
        recent_audit_logs = cursor.fetchone()[0]
        print(f"   📊 Audit Logs seit {target_time}: {recent_audit_logs}")
        
        # Letzte 10 Audit Logs
        cursor.execute("SELECT id, user_id, action, description, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10")
        recent_logs = cursor.fetchall()
        print(f"   📋 Letzte 10 Audit Logs:")
        for log in recent_logs:
            print(f"   - ID {log[0]}: {log[2]} - {log[3]} (User: {log[1]}, Zeit: {log[4]})")
        
        # 3. Milestones analysieren
        print("\n3️⃣ MILESTONES ANALYSE:")
        print("-" * 25)
        
        cursor.execute("SELECT COUNT(*) FROM milestones")
        total_milestones = cursor.fetchone()[0]
        print(f"   🏗️ Gesamte Milestones: {total_milestones}")
        
        # Milestones seit 14:38 Uhr
        cursor.execute("SELECT COUNT(*) FROM milestones WHERE created_at >= ?", (target_time,))
        recent_milestones = cursor.fetchone()[0]
        print(f"   🏗️ Milestones seit {target_time}: {recent_milestones}")
        
        # Letzte 5 Milestones
        cursor.execute("SELECT id, title, project_id, status, created_at FROM milestones ORDER BY created_at DESC LIMIT 5")
        recent_milestones_data = cursor.fetchall()
        print(f"   📋 Letzte 5 Milestones:")
        for milestone in recent_milestones_data:
            print(f"   - ID {milestone[0]}: {milestone[1]} (Projekt: {milestone[2]}, Status: {milestone[3]}, Zeit: {milestone[4]})")
        
        # 4. Quotes analysieren
        print("\n4️⃣ QUOTES ANALYSE:")
        print("-" * 20)
        
        cursor.execute("SELECT COUNT(*) FROM quotes")
        total_quotes = cursor.fetchone()[0]
        print(f"   💰 Gesamte Quotes: {total_quotes}")
        
        # Quotes seit 14:38 Uhr
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE created_at >= ?", (target_time,))
        recent_quotes = cursor.fetchone()[0]
        print(f"   💰 Quotes seit {target_time}: {recent_quotes}")
        
        # 5. Users analysieren
        print("\n5️⃣ USERS ANALYSE:")
        print("-" * 18)
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"   👤 Gesamte Users: {total_users}")
        
        # Aktive Sessions
        cursor.execute("SELECT id, email, user_type, last_login FROM users ORDER BY last_login DESC LIMIT 5")
        recent_users = cursor.fetchall()
        print(f"   📋 Letzte 5 User-Logins:")
        for user in recent_users:
            print(f"   - ID {user[0]}: {user[1]} (Typ: {user[2]}, Login: {user[3]})")
        
        # 6. Datenbank-Integrität prüfen
        print("\n6️⃣ DATENBANK-INTEGRITÄT:")
        print("-" * 25)
        
        # Prüfe Foreign Key Constraints
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            print("   ✅ Foreign Key Constraints aktiviert")
        except Exception as e:
            print(f"   ❌ Foreign Key Fehler: {e}")
        
        # Prüfe Datenbank-Locks
        try:
            cursor.execute("PRAGMA busy_timeout=5000")
            print("   ✅ Datenbank-Lock-Timeout gesetzt")
        except Exception as e:
            print(f"   ❌ Lock-Timeout Fehler: {e}")
        
        # 7. Backend-Verbindung testen
        print("\n7️⃣ BACKEND-VERBINDUNG:")
        print("-" * 25)
        
        import requests
        try:
            response = requests.get("http://localhost:8000/docs", timeout=5)
            print(f"   ✅ Backend erreichbar: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Backend nicht erreichbar: {e}")
        
        # 8. Problem-Analyse
        print("\n8️⃣ PROBLEM-ANALYSE:")
        print("-" * 20)
        
        if recent_audit_logs == 0:
            print("   🚨 PROBLEM: Keine Audit Logs seit 14:38 Uhr!")
            print("   💡 Mögliche Ursachen:")
            print("   - Backend läuft nicht")
            print("   - API-Calls schlagen fehl")
            print("   - Datenbank-Lock-Probleme")
            print("   - Audit-Log-Service deaktiviert")
        
        if recent_milestones == 0:
            print("   🚨 PROBLEM: Keine neuen Milestones seit 14:38 Uhr!")
            print("   💡 Mögliche Ursachen:")
            print("   - Frontend-Cache zeigt alte Daten")
            print("   - API-Authentifizierung fehlschlägt")
            print("   - Datenbank-Transaktionen fehlschlagen")
            print("   - Backend-Service-Fehler")
        
        # 9. Lösungsvorschläge
        print("\n9️⃣ LÖSUNGSVORSCHLÄGE:")
        print("-" * 25)
        
        print("   🔧 Sofortige Maßnahmen:")
        print("   1. Backend neu starten")
        print("   2. Browser-Cache leeren")
        print("   3. Datenbank-Verbindung prüfen")
        print("   4. API-Logs überprüfen")
        print("   5. Audit-Log-Service testen")
        
        print("\n   📋 Debug-Schritte:")
        print("   1. Backend-Logs prüfen")
        print("   2. API-Calls im Browser debuggen")
        print("   3. Datenbank direkt testen")
        print("   4. Frontend/Backend-Synchronisation prüfen")
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_audit_trail_analysis() 