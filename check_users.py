#!/usr/bin/env python3
"""
Skript um verfügbare Benutzer in der Datenbank zu prüfen
"""

import asyncio
import aiosqlite

async def check_users():
    """Überprüft die existierenden Benutzer in der Datenbank"""
    
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Prüfe ob die users Tabelle existiert
        cursor = await db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        table_exists = await cursor.fetchone()
        
        if not table_exists:
            print("❌ users Tabelle existiert nicht!")
            return
        
        print("✅ users Tabelle existiert")
        
        # Zeige alle Benutzer
        cursor = await db.execute("""
            SELECT id, email, first_name, last_name, user_type, is_active, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        users = await cursor.fetchall()
        
        print(f"📊 Anzahl Benutzer: {len(users)}")
        print("📋 Alle Benutzer:")
        for user in users:
            print(f"  - ID: {user[0]}, Email: {user[1]}, Name: {user[2]} {user[3]}, Type: {user[4]}, Active: {user[5]}, Created: {user[6]}")

if __name__ == "__main__":
    asyncio.run(check_users()) 