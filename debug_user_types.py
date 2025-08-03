#!/usr/bin/env python3
import sqlite3

def debug_user_types():
    print("🔍 Debug: User Types in Database")
    print("=" * 40)
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Check all users and their types
    cursor.execute('SELECT id, first_name, last_name, email, user_type, user_role FROM users')
    users = cursor.fetchall()
    
    print("👥 All Users:")
    for user in users:
        print(f"  User {user[0]}: {user[1]} {user[2]} ({user[4]}) - Role: {user[5]} - Email: {user[5]}")
    
    print("\n🎯 Focus on Test Users:")
    cursor.execute('SELECT id, first_name, last_name, email, user_type, user_role FROM users WHERE id IN (4, 6)')
    test_users = cursor.fetchall()
    
    for user in test_users:
        print(f"  User {user[0]}: {user[1]} {user[2]}")
        print(f"    user_type: '{user[4]}'")
        print(f"    user_role: '{user[5]}'")
        print(f"    email: {user[3]}")
        
        # Check what projects this user should see
        if user[4] in ['PRIVATE', 'PROFESSIONAL', 'bautraeger', 'developer']:
            print(f"    → Bauträger Logic: Sieht nur eigene Projekte")
        elif user[4] == 'SERVICE_PROVIDER':
            print(f"    → Dienstleister Logic: Sieht alle Projekte")
        else:
            print(f"    → Fallback Logic: Sieht nur eigene Projekte")
        print("    ---")
    
    conn.close()

if __name__ == "__main__":
    debug_user_types()