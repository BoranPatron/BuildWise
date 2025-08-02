import asyncio
import aiosqlite

async def check_user_password():
    """Überprüft das Passwort des Bauträger-Benutzers"""
    
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Finde den Bauträger-Benutzer
        cursor = await db.execute("""
            SELECT id, email, user_type, user_role, hashed_password 
            FROM users 
            WHERE email = ?
        """, ("janina.hankus@momentumvisual.de",))
        
        user = await cursor.fetchone()
        if user:
            print(f"📋 Benutzer gefunden: ID={user[0]}, Email={user[1]}, Type={user[2]}, Role={user[3]}")
            print(f"📋 Password Hash: {user[4][:20]}...")
        else:
            print("❌ Benutzer janina.hankus@momentumvisual.de nicht gefunden")
            
        # Zeige alle Benutzer
        print("\n📋 Alle Benutzer:")
        cursor = await db.execute("""
            SELECT id, email, user_type, user_role 
            FROM users 
            ORDER BY id
        """)
        
        all_users = await cursor.fetchall()
        for user in all_users:
            print(f"  - ID: {user[0]}, Email: {user[1]}, Type: {user[2]}, Role: {user[3]}")

if __name__ == "__main__":
    asyncio.run(check_user_password()) 