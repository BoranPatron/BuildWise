#!/usr/bin/env python3
"""
Umfassendes Debug-Skript für das Angebot/Kostenposition-Problem
"""

import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

def debug_database():
    """Analysiert die Datenbank und zeigt alle relevanten Informationen"""
    print("🔍 Umfassende Datenbank-Analyse")
    print("=" * 60)
    
    # Direkte SQLite-Verbindung
    DATABASE_URL = "sqlite:///buildwise.db"
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Prüfe alle Tabellen
        print("\n📋 Verfügbare Tabellen:")
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = result.fetchall()
        
        for table in tables:
            print(f"  - {table[0]}")
        
        # 2. Prüfe Quotes-Tabelle
        print("\n💼 Quotes-Tabelle:")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM quotes"))
            quote_count_result = result.fetchone()
            quote_count = quote_count_result[0] if quote_count_result else 0
            print(f"  - Anzahl Quotes: {quote_count}")
            
            if quote_count > 0:
                result = conn.execute(text("SELECT id, title, status, project_id, created_at FROM quotes LIMIT 5"))
                quotes = result.fetchall()
                for quote in quotes:
                    print(f"    * ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}, Projekt: {quote[3]}, Erstellt: {quote[4]}")
            else:
                print("  - Keine Quotes vorhanden")
        except Exception as e:
            print(f"  - Fehler beim Lesen der Quotes-Tabelle: {e}")
        
        # 3. Prüfe Cost_Positions-Tabelle
        print("\n💰 Cost_Positions-Tabelle:")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM cost_positions"))
            cp_count_result = result.fetchone()
            cp_count = cp_count_result[0] if cp_count_result else 0
            print(f"  - Anzahl Cost Positions: {cp_count}")
            
            if cp_count > 0:
                result = conn.execute(text("SELECT id, title, quote_id, project_id, created_at FROM cost_positions LIMIT 5"))
                cost_positions = result.fetchall()
                for cp in cost_positions:
                    print(f"    * ID: {cp[0]}, Titel: {cp[1]}, Quote-ID: {cp[2]}, Projekt: {cp[3]}, Erstellt: {cp[4]}")
            else:
                print("  - Keine Cost Positions vorhanden")
        except Exception as e:
            print(f"  - Fehler beim Lesen der Cost_Positions-Tabelle: {e}")
        
        # 4. Prüfe Milestones-Tabelle
        print("\n🏗️ Milestones-Tabelle:")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM milestones"))
            milestone_count_result = result.fetchone()
            milestone_count = milestone_count_result[0] if milestone_count_result else 0
            print(f"  - Anzahl Milestones: {milestone_count}")
            
            if milestone_count > 0:
                result = conn.execute(text("SELECT id, title, project_id, status FROM milestones LIMIT 5"))
                milestones = result.fetchall()
                for milestone in milestones:
                    print(f"    * ID: {milestone[0]}, Titel: {milestone[1]}, Projekt: {milestone[2]}, Status: {milestone[3]}")
            else:
                print("  - Keine Milestones vorhanden")
        except Exception as e:
            print(f"  - Fehler beim Lesen der Milestones-Tabelle: {e}")
        
        # 5. Prüfe Projects-Tabelle
        print("\n📁 Projects-Tabelle:")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM projects"))
            project_count_result = result.fetchone()
            project_count = project_count_result[0] if project_count_result else 0
            print(f"  - Anzahl Projects: {project_count}")
            
            if project_count > 0:
                result = conn.execute(text("SELECT id, name, status FROM projects LIMIT 5"))
                projects = result.fetchall()
                for project in projects:
                    print(f"    * ID: {project[0]}, Name: {project[1]}, Status: {project[2]}")
            else:
                print("  - Keine Projects vorhanden")
        except Exception as e:
            print(f"  - Fehler beim Lesen der Projects-Tabelle: {e}")
        
        # 6. Prüfe Users-Tabelle
        print("\n👥 Users-Tabelle:")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count_result = result.fetchone()
            user_count = user_count_result[0] if user_count_result else 0
            print(f"  - Anzahl Users: {user_count}")
            
            if user_count > 0:
                result = conn.execute(text("SELECT id, email, user_type FROM users LIMIT 5"))
                users = result.fetchall()
                for user in users:
                    print(f"    * ID: {user[0]}, Email: {user[1]}, Type: {user[2]}")
            else:
                print("  - Keine Users vorhanden")
        except Exception as e:
            print(f"  - Fehler beim Lesen der Users-Tabelle: {e}")
        
        # 7. Analyse der Beziehungen
        print("\n🔗 Beziehungs-Analyse:")
        
        # Quotes mit Milestones
        try:
            result = conn.execute(text("""
                SELECT q.id, q.title, q.status, m.title as milestone_title 
                FROM quotes q 
                LEFT JOIN milestones m ON q.milestone_id = m.id 
                LIMIT 5
            """))
            quote_milestone_relations = result.fetchall()
            if quote_milestone_relations:
                print("  - Quotes mit Milestones:")
                for rel in quote_milestone_relations:
                    print(f"    * Quote: {rel[1]} (Status: {rel[2]}) -> Milestone: {rel[3] or 'Kein Milestone'}")
            else:
                print("  - Keine Quote-Milestone-Beziehungen gefunden")
        except Exception as e:
            print(f"  - Fehler bei Quote-Milestone-Analyse: {e}")
        
        # Cost Positions mit Quotes
        try:
            result = conn.execute(text("""
                SELECT cp.id, cp.title, q.title as quote_title, q.status as quote_status
                FROM cost_positions cp 
                LEFT JOIN quotes q ON cp.quote_id = q.id 
                LIMIT 5
            """))
            cp_quote_relations = result.fetchall()
            if cp_quote_relations:
                print("  - Cost Positions mit Quotes:")
                for rel in cp_quote_relations:
                    print(f"    * Cost Position: {rel[1]} -> Quote: {rel[2] or 'Kein Quote'} (Status: {rel[3] or 'N/A'})")
            else:
                print("  - Keine Cost Position-Quote-Beziehungen gefunden")
        except Exception as e:
            print(f"  - Fehler bei Cost Position-Quote-Analyse: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 Analyse abgeschlossen")

if __name__ == "__main__":
    debug_database() 