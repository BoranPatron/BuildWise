import asyncio
import aiosqlite
from passlib.context import CryptContext

async def set_bautraeger_password():
    """Setzt das Passwort für den Bauträger-Benutzer"""
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Setze Passwort für Bauträger-Benutzer
        hashed_password = pwd_context.hash("test123")
        
        cursor = await db.execute("""
            UPDATE users 
            SET hashed_password = ? 
            WHERE email = ?
        """, (hashed_password, "janina.hankus@momentumvisual.de"))
        
        await db.commit()
        print("✅ Passwort für Bauträger-Benutzer gesetzt")
        
        # Überprüfe das Update
        cursor = await db.execute("""
            SELECT id, email, user_type, user_role, hashed_password 
            FROM users 
            WHERE email = ?
        """, ("janina.hankus@momentumvisual.de",))
        
        user = await cursor.fetchone()
        if user:
            print(f"📋 Benutzer gefunden: ID={user[0]}, Email={user[1]}, Type={user[2]}, Role={user[3]}")
            print(f"📋 Password Hash gesetzt: {user[4][:20]}...")
        else:
            print("❌ Benutzer nicht gefunden")

if __name__ == "__main__":
    asyncio.run(set_bautraeger_password()) 