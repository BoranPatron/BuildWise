import asyncio
import aiosqlite

async def check_user_table():
    """Überprüft die Struktur der users Tabelle"""
    
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Zeige die Tabellenstruktur
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        
        print("📋 Users Tabellenstruktur:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) - Nullable: {col[3]}, Default: {col[4]}, PK: {col[5]}")
        
        # Zeige einen Beispiel-Benutzer
        cursor = await db.execute("""
            SELECT * FROM users LIMIT 1
        """)
        user = await cursor.fetchone()
        
        if user:
            print(f"\n📋 Beispiel-Benutzer:")
            for i, col in enumerate(columns):
                print(f"  - {col[1]}: {user[i]}")

if __name__ == "__main__":
    asyncio.run(check_user_table()) 