#!/usr/bin/env python3
"""
Test-Skript um zu prüfen, welche Datenbank der Server verwendet
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_server_database():
    """Testet, welche Datenbank der Server verwendet"""
    
    print("🔍 TESTE SERVER-DATENBANK")
    print("=" * 50)
    
    # Test 1: Öffentliche Projekte-API
    print("\n1️⃣ Teste öffentliche Projekte-API:")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/api/v1/projects/public") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Projekte gefunden: {len(data)}")
                    for i, project in enumerate(data[:3]):
                        print(f"  {i+1}. {project.get('name', 'Unbekannt')} (ID: {project.get('id', 'N/A')})")
                else:
                    text = await response.text()
                    print(f"Response: {text[:200]}...")
        except Exception as e:
            print(f"❌ Fehler: {e}")
    
    # Test 2: Server-Info (falls verfügbar)
    print("\n2️⃣ Teste Server-Info:")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    text = await response.text()
                    print(f"Response: {text[:200]}...")
                else:
                    print("Server läuft, aber Root-Endpunkt nicht verfügbar")
        except Exception as e:
            print(f"❌ Fehler: {e}")
    
    # Test 3: Health Check (falls verfügbar)
    print("\n3️⃣ Teste Health Check:")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/health") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Health Check: {data}")
                else:
                    print("Health Check nicht verfügbar")
        except Exception as e:
            print(f"❌ Fehler: {e}")

async def test_database_connection():
    """Testet die direkte Datenbankverbindung"""
    
    print("\n🔍 TESTE DIREKTE DATENBANKVERBINDUNG")
    print("=" * 50)
    
    # Test PostgreSQL
    print("\n1️⃣ Teste PostgreSQL:")
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="buildwise",
            user="buildwise_user",
            password="buildwise123"
        )
        
        result = await conn.fetch("SELECT COUNT(*) FROM projects")
        project_count = result[0]['count']
        print(f"✅ PostgreSQL: {project_count} Projekte")
        
        await conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL-Fehler: {e}")
    
    # Test SQLite
    print("\n2️⃣ Teste SQLite:")
    try:
        import sqlite3
        conn = sqlite3.connect("buildwise.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        print(f"✅ SQLite: {project_count} Projekte")
        
        conn.close()
    except Exception as e:
        print(f"❌ SQLite-Fehler: {e}")

async def main():
    """Hauptfunktion"""
    print("🚀 Starte Server-Datenbank-Tests...")
    
    await test_server_database()
    await test_database_connection()
    
    print("\n✅ Tests abgeschlossen")

if __name__ == "__main__":
    asyncio.run(main()) 