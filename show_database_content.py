#!/usr/bin/env python3
"""
Zeigt den Inhalt der BuildWise-Datenbank an
"""

import sqlite3
import os
from datetime import datetime

def show_database_content():
    """Zeigt den kompletten Inhalt der Datenbank an"""
    print("🗄️ BUILDWISE DATENBANK INHALT")
    print("=" * 50)
    
    # Datenbank-Pfad
    db_path = "buildwise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return
    
    print(f"📁 Datenbank-Pfad: {os.path.abspath(db_path)}")
    print(f"📊 Größe: {os.path.getsize(db_path)} Bytes")
    print(f"📅 Letzte Änderung: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Tabellen auflisten
        print("\n📋 DATENBANK-TABELLEN:")
        print("-" * 30)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for i, table in enumerate(tables, 1):
            print(f"   {i}. {table[0]}")
        
        # 2. Audit Logs
        print("\n📊 AUDIT LOGS:")
        print("-" * 20)
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        audit_count = cursor.fetchone()[0]
        print(f"   Gesamt: {audit_count} Einträge")
        
        if audit_count > 0:
            cursor.execute("SELECT id, user_id, action, description, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10")
            recent_logs = cursor.fetchall()
            print("   Letzte 10 Einträge:")
            for log in recent_logs:
                print(f"   - ID {log[0]}: {log[2]} - {log[3]} (User: {log[1]}, Zeit: {log[4]})")
        
        # 3. Users
        print("\n👤 USERS:")
        print("-" * 10)
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        print(f"   Gesamt: {users_count} Benutzer")
        
        if users_count > 0:
            cursor.execute("SELECT id, email, user_type, created_at FROM users ORDER BY created_at DESC LIMIT 5")
            users = cursor.fetchall()
            print("   Letzte 5 Benutzer:")
            for user in users:
                print(f"   - ID {user[0]}: {user[1]} (Typ: {user[2]}, Erstellt: {user[3]})")
        
        # 4. Projects
        print("\n📋 PROJECTS:")
        print("-" * 15)
        cursor.execute("SELECT COUNT(*) FROM projects")
        projects_count = cursor.fetchone()[0]
        print(f"   Gesamt: {projects_count} Projekte")
        
        if projects_count > 0:
            cursor.execute("SELECT id, name, owner_id, created_at FROM projects ORDER BY created_at DESC LIMIT 5")
            projects = cursor.fetchall()
            print("   Letzte 5 Projekte:")
            for project in projects:
                print(f"   - ID {project[0]}: {project[1]} (Owner: {project[2]}, Erstellt: {project[3]})")
        
        # 5. Milestones (Gewerke)
        print("\n🏗️ MILESTONES (GEWERKE):")
        print("-" * 25)
        cursor.execute("SELECT COUNT(*) FROM milestones")
        milestones_count = cursor.fetchone()[0]
        print(f"   Gesamt: {milestones_count} Gewerke")
        
        if milestones_count > 0:
            cursor.execute("SELECT id, title, project_id, status, created_at FROM milestones ORDER BY created_at DESC LIMIT 10")
            milestones = cursor.fetchall()
            print("   Letzte 10 Gewerke:")
            for milestone in milestones:
                print(f"   - ID {milestone[0]}: {milestone[1]} (Projekt: {milestone[2]}, Status: {milestone[3]}, Erstellt: {milestone[4]})")
        
        # 6. Quotes (Angebote)
        print("\n💰 QUOTES (ANGEBOTE):")
        print("-" * 25)
        cursor.execute("SELECT COUNT(*) FROM quotes")
        quotes_count = cursor.fetchone()[0]
        print(f"   Gesamt: {quotes_count} Angebote")
        
        if quotes_count > 0:
            cursor.execute("SELECT id, title, milestone_id, status, total_amount, created_at FROM quotes ORDER BY created_at DESC LIMIT 10")
            quotes = cursor.fetchall()
            print("   Letzte 10 Angebote:")
            for quote in quotes:
                print(f"   - ID {quote[0]}: {quote[1]} (Milestone: {quote[2]}, Status: {quote[3]}, Betrag: {quote[4]}, Erstellt: {quote[5]})")
        
        # 7. Cost Positions
        print("\n💼 COST POSITIONS:")
        print("-" * 20)
        cursor.execute("SELECT COUNT(*) FROM cost_positions")
        cost_positions_count = cursor.fetchone()[0]
        print(f"   Gesamt: {cost_positions_count} Kostenpositionen")
        
        if cost_positions_count > 0:
            cursor.execute("SELECT id, title, amount, status, created_at FROM cost_positions ORDER BY created_at DESC LIMIT 10")
            cost_positions = cursor.fetchall()
            print("   Letzte 10 Kostenpositionen:")
            for cp in cost_positions:
                print(f"   - ID {cp[0]}: {cp[1]} (Betrag: {cp[2]}, Status: {cp[3]}, Erstellt: {cp[4]})")
        
        # 8. BuildWise Fees
        print("\n💳 BUILDWISE FEES:")
        print("-" * 20)
        cursor.execute("SELECT COUNT(*) FROM buildwise_fees")
        fees_count = cursor.fetchone()[0]
        print(f"   Gesamt: {fees_count} Gebühren")
        
        if fees_count > 0:
            cursor.execute("SELECT id, fee_amount, status, created_at FROM buildwise_fees ORDER BY created_at DESC LIMIT 10")
            fees = cursor.fetchall()
            print("   Letzte 10 Gebühren:")
            for fee in fees:
                print(f"   - ID {fee[0]}: Betrag {fee[1]}, Status: {fee[2]}, Erstellt: {fee[3]})")
        
        # 9. Documents
        print("\n📄 DOCUMENTS:")
        print("-" * 15)
        cursor.execute("SELECT COUNT(*) FROM documents")
        documents_count = cursor.fetchone()[0]
        print(f"   Gesamt: {documents_count} Dokumente")
        
        if documents_count > 0:
            cursor.execute("SELECT id, title, file_name, created_at FROM documents ORDER BY created_at DESC LIMIT 5")
            documents = cursor.fetchall()
            print("   Letzte 5 Dokumente:")
            for doc in documents:
                print(f"   - ID {doc[0]}: {doc[1]} ({doc[2]}, Erstellt: {doc[3]})")
        
        # 10. Messages
        print("\n💬 MESSAGES:")
        print("-" * 15)
        cursor.execute("SELECT COUNT(*) FROM messages")
        messages_count = cursor.fetchone()[0]
        print(f"   Gesamt: {messages_count} Nachrichten")
        
        if messages_count > 0:
            cursor.execute("SELECT id, content, sender_id, created_at FROM messages ORDER BY created_at DESC LIMIT 5")
            messages = cursor.fetchall()
            print("   Letzte 5 Nachrichten:")
            for msg in messages:
                print(f"   - ID {msg[0]}: {msg[1][:50]}... (Sender: {msg[2]}, Erstellt: {msg[3]})")
        
        # 11. Zusammenfassung
        print("\n📈 ZUSAMMENFASSUNG:")
        print("-" * 20)
        print(f"   📊 Audit Logs: {audit_count}")
        print(f"   👤 Users: {users_count}")
        print(f"   📋 Projects: {projects_count}")
        print(f"   🏗️ Milestones: {milestones_count}")
        print(f"   💰 Quotes: {quotes_count}")
        print(f"   💼 Cost Positions: {cost_positions_count}")
        print(f"   💳 BuildWise Fees: {fees_count}")
        print(f"   📄 Documents: {documents_count}")
        print(f"   💬 Messages: {messages_count}")
        
        print(f"\n🗄️ Datenbank-Pfad: {os.path.abspath(db_path)}")
        print(f"📁 Datei-Größe: {os.path.getsize(db_path)} Bytes")
        print(f"📅 Letzte Änderung: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_database_content() 