import asyncio
import aiosqlite

async def check_user_projects():
    """Überprüft die Projekte des Benutzers"""
    
    async with aiosqlite.connect('buildwise.db') as db:
        print("🔧 Verbunden zur SQLite-Datenbank")
        
        # Finde den Benutzer test@buildwise.de
        cursor = await db.execute("""
            SELECT id, email, user_type, user_role 
            FROM users 
            WHERE email = ?
        """, ("test@buildwise.de",))
        
        user = await cursor.fetchone()
        if user:
            print(f"📋 Benutzer gefunden: ID={user[0]}, Email={user[1]}, Type={user[2]}, Role={user[3]}")
            
            # Hole alle Projekte dieses Benutzers
            cursor = await db.execute("""
                SELECT id, name, description, owner_id 
                FROM projects 
                WHERE owner_id = ?
            """, (user[0],))
            
            projects = await cursor.fetchall()
            print(f"📋 Anzahl Projekte: {len(projects)}")
            
            for project in projects:
                print(f"  - ID: {project[0]}, Name: {project[1]}, Owner: {project[3]}")
                
                # Hole Milestones für dieses Projekt
                cursor = await db.execute("""
                    SELECT id, title, category, status, documents 
                    FROM milestones 
                    WHERE project_id = ?
                """, (project[0],))
                
                milestones = await cursor.fetchall()
                print(f"    Milestones: {len(milestones)}")
                for milestone in milestones:
                    documents = milestone[4] if milestone[4] else "[]"
                    print(f"      - ID: {milestone[0]}, Titel: {milestone[1]}, Kategorie: {milestone[2]}, Status: {milestone[3]}, Documents: {documents[:50]}...")
        else:
            print("❌ Benutzer test@buildwise.de nicht gefunden")
            
        # Zeige auch alle Projekte
        print("\n📋 Alle Projekte:")
        cursor = await db.execute("""
            SELECT id, name, description, owner_id 
            FROM projects 
            ORDER BY id
        """)
        
        all_projects = await cursor.fetchall()
        for project in all_projects:
            print(f"  - ID: {project[0]}, Name: {project[1]}, Owner: {project[3]}")

if __name__ == "__main__":
    asyncio.run(check_user_projects()) 