#!/usr/bin/env python3
"""
Test-Skript für PostgreSQL-Verbindung
"""

import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_postgresql_connection():
    """Testet die PostgreSQL-Verbindung"""
    
    print("🔍 TESTE POSTGRESQL-VERBINDUNG")
    print("=" * 50)
    
    # Test 1: Direkte asyncpg-Verbindung
    print("\n1️⃣ Teste direkte asyncpg-Verbindung:")
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="buildwise",
            user="buildwise_user",
            password="buildwise123"
        )
        
        # Teste Abfrage
        result = await conn.fetch("SELECT COUNT(*) FROM projects")
        project_count = result[0]['count']
        print(f"✅ PostgreSQL-Verbindung erfolgreich")
        print(f"📊 Projekte in PostgreSQL: {project_count}")
        
        # Teste Benutzer
        result = await conn.fetch("SELECT COUNT(*) FROM users")
        user_count = result[0]['count']
        print(f"📊 Benutzer in PostgreSQL: {user_count}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL-Verbindung fehlgeschlagen: {e}")
        return False
    
    # Test 2: SQLAlchemy-Engine
    print("\n2️⃣ Teste SQLAlchemy-Engine:")
    try:
        engine = create_async_engine(
            "postgresql+asyncpg://buildwise_user:buildwise123@localhost:5432/buildwise",
            echo=False
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM projects"))
            project_count = result.scalar()
            print(f"✅ SQLAlchemy-Engine erfolgreich")
            print(f"📊 Projekte in PostgreSQL: {project_count}")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ SQLAlchemy-Engine fehlgeschlagen: {e}")
        return False
    
    print("\n✅ PostgreSQL-Tests erfolgreich!")
    return True

async def main():
    """Hauptfunktion"""
    print("🚀 Starte PostgreSQL-Tests...")
    
    success = await test_postgresql_connection()
    
    if success:
        print("\n✅ PostgreSQL ist bereit!")
    else:
        print("\n❌ PostgreSQL-Verbindung fehlgeschlagen")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 