#!/usr/bin/env python3
"""
Datenbank-Behebung über das Backend mit korrekten Credentials
"""

import asyncio
import sys
import os
from datetime import datetime

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def fix_database_via_backend():
    """Behebt die Datenbank über das Backend"""
    print("🚀 DATENBANK-BEHEBUNG ÜBER BACKEND...")
    print(f"Zeitstempel: {datetime.now()}")
    
    try:
        # Importiere Backend-Komponenten
        from app.core.database import get_database_url
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # Verwende die Backend-Datenbank-URL
        database_url = get_database_url()
        print("Verwende Backend-Datenbank-URL:", database_url.replace("your_secure_password", "***"))
        
        # Erstelle Engine
        engine = create_async_engine(database_url)
        
        async with engine.begin() as conn:
            # 1. Zeige aktuelle Projekte
            print("\n=== AKTUELLE PROJEKTE ===")
            result = await conn.execute(text("""
                SELECT id, name, address, is_public, allow_quotes, 
                       address_latitude, address_longitude
                FROM projects 
                ORDER BY id
            """))
            projects = result.fetchall()
            
            for project in projects:
                print(f"Projekt {project[0]}: {project[1]}")
                print(f"  Adresse: {project[2]}")
                print(f"  Öffentlich: {project[3]}")
                print(f"  Quotes erlaubt: {project[4]}")
                print(f"  Koordinaten: {project[5]}, {project[6]}")
            
            # 2. Füge Adressen hinzu (AGGRESSIV)
            print("\n=== ADRESSEN HINZUFÜGEN (AGGRESSIV) ===")
            
            # Lösche alle bestehenden Adressen und setze neue
            await conn.execute(text("UPDATE projects SET address = NULL WHERE id IN (1, 2, 3, 4, 5)"))
            print("✅ Bestehende Adressen gelöscht")
            
            # Setze neue Adressen
            update_queries = [
                "UPDATE projects SET address = 'Hauptstraße 42, 80331 München, Deutschland' WHERE id = 1",
                "UPDATE projects SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland' WHERE id = 2",
                "UPDATE projects SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland' WHERE id = 3",
                "UPDATE projects SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland' WHERE id = 4",
                "UPDATE projects SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland' WHERE id = 5"
            ]
            
            for query in update_queries:
                await conn.execute(text(query))
                print(f"✅ Query ausgeführt: {query[:50]}...")
            
            # 3. Mache Projekte öffentlich (AGGRESSIV)
            print("\n=== PROJEKTE ÖFFENTLICH MACHEN (AGGRESSIV) ===")
            await conn.execute(text("UPDATE projects SET is_public = true, allow_quotes = true WHERE id IN (1, 2, 3, 4, 5)"))
            print("✅ Projekte öffentlich gemacht")
            
            # 4. Lösche bestehende Koordinaten (zwinge Neugenerierung)
            print("\n=== KOORDINATEN LÖSCHEN (Zwinge Neugenerierung) ===")
            await conn.execute(text("UPDATE projects SET address_latitude = NULL, address_longitude = NULL WHERE id IN (1, 2, 3, 4, 5)"))
            print("✅ Bestehende Koordinaten gelöscht")
            
            # 5. Zeige aktualisierte Projekte
            print("\n=== AKTUALISIERTE PROJEKTE ===")
            result = await conn.execute(text("""
                SELECT id, name, address, is_public, allow_quotes, 
                       address_latitude, address_longitude
                FROM projects 
                WHERE id IN (1, 2, 3, 4, 5)
                ORDER BY id
            """))
            updated_projects = result.fetchall()
            
            for project in updated_projects:
                print(f"Projekt {project[0]}: {project[1]}")
                print(f"  Adresse: {project[2]}")
                print(f"  Öffentlich: {project[3]}")
                print(f"  Quotes erlaubt: {project[4]}")
                print(f"  Koordinaten: {project[5]}, {project[6]}")
            
            # 6. Zeige Gewerke
            print("\n=== GEWERKE ===")
            result = await conn.execute(text("""
                SELECT m.id, m.title, m.category, m.status,
                       p.name as project_name, p.address as project_address,
                       p.is_public, p.allow_quotes
                FROM milestones m
                JOIN projects p ON m.project_id = p.id
                ORDER BY m.id
            """))
            trades = result.fetchall()
            
            for trade in trades:
                print(f"Gewerk {trade[0]}: {trade[1]}")
                print(f"  Kategorie: {trade[2]}")
                print(f"  Status: {trade[3]}")
                print(f"  Projekt: {trade[4]}")
                print(f"  Adresse: {trade[5]}")
                print(f"  Öffentlich: {trade[6]}")
                print(f"  Quotes erlaubt: {trade[7]}")
            
            print("\n✅ DATENBANK ERFOLGREICH BEHEBT!")
            return True
            
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Behebung: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_manual_instructions():
    """Erstellt manuelle Anweisungen"""
    print("\n=== MANUELLE ANWEISUNGEN ===")
    print("Falls das automatische Skript nicht funktioniert:")
    print("\n1. Öffnen Sie Ihre Datenbank-Verwaltung (pgAdmin, DBeaver, etc.)")
    print("2. Verbinden Sie sich mit der BuildWise-Datenbank")
    print("3. Führen Sie diese SQL-Befehle AUS:")
    print("\n-- Lösche bestehende Adressen")
    print("UPDATE projects SET address = NULL WHERE id IN (1, 2, 3, 4, 5);")
    print("\n-- Setze neue Adressen")
    print("UPDATE projects SET address = 'Hauptstraße 42, 80331 München, Deutschland' WHERE id = 1;")
    print("UPDATE projects SET address = 'Königsallee 15, 40212 Düsseldorf, Deutschland' WHERE id = 2;")
    print("UPDATE projects SET address = 'Neuer Wall 80, 20354 Hamburg, Deutschland' WHERE id = 3;")
    print("UPDATE projects SET address = 'Zeil 106, 60313 Frankfurt am Main, Deutschland' WHERE id = 4;")
    print("UPDATE projects SET address = 'Friedrichstraße 123, 10117 Berlin, Deutschland' WHERE id = 5;")
    print("\n-- Mache Projekte öffentlich")
    print("UPDATE projects SET is_public = true, allow_quotes = true WHERE id IN (1, 2, 3, 4, 5);")
    print("\n-- Lösche bestehende Koordinaten")
    print("UPDATE projects SET address_latitude = NULL, address_longitude = NULL WHERE id IN (1, 2, 3, 4, 5);")
    print("\n4. Starten Sie das Backend neu:")
    print("   python -m uvicorn app.main:app --reload")

async def main():
    """Hauptfunktion"""
    print("🚀 Starte Datenbank-Behebung über Backend...")
    
    try:
        # 1. Datenbank beheben
        db_success = await fix_database_via_backend()
        
        if db_success:
            print("\n📊 BEHEBUNG-ZUSAMMENFASSUNG:")
            print("✅ Datenbank erfolgreich behebt")
            print("✅ Adressen hinzugefügt")
            print("✅ Projekte öffentlich gemacht")
            print("✅ Koordinaten gelöscht (werden automatisch neu generiert)")
            print("\n📋 NÄCHSTE SCHRITTE:")
            print("1. Starten Sie das Backend neu: python -m uvicorn app.main:app --reload")
            print("2. Warten Sie 10-15 Sekunden bis das Backend vollständig gestartet ist")
            print("3. Testen Sie die Kartenansicht in der Dienstleisteransicht")
            print("4. Die Gewerke sollten jetzt als Marker auf der Karte erscheinen")
            
        else:
            print("❌ Datenbank-Behebung fehlgeschlagen")
            create_manual_instructions()
            
    except Exception as e:
        print(f"❌ Fehler bei der Behebung: {e}")
        create_manual_instructions()

if __name__ == "__main__":
    asyncio.run(main()) 