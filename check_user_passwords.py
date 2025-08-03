#!/usr/bin/env python3
import sqlite3

def check_user_passwords():
    print("🔍 Check: User Passwords in Database")
    print("=" * 40)
    
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # Check users and their password hashes
    cursor.execute('SELECT id, first_name, last_name, email, user_type, password_hash FROM users WHERE id IN (4, 6)')
    users = cursor.fetchall()
    
    print("👥 Test Users:")
    for user in users:
        print(f"  User {user[0]}: {user[1]} {user[2]}")
        print(f"    Email: {user[3]}")
        print(f"    Type: {user[4]}")
        print(f"    Password Hash: {user[5][:50]}..." if user[5] else "    Password Hash: None")
        print("    ---")
    
    conn.close()
    
    print("\n🔧 Password Test:")
    print("Das Frontend kann sich einloggen, also funktioniert das Passwort.")
    print("Mögliche Lösungen:")
    print("1. Passwort direkt aus dem Frontend-LocalStorage kopieren")
    print("2. Ein neues Passwort für den Test-User setzen")
    print("3. Den Login-Prozess aus dem Frontend nachvollziehen")

if __name__ == "__main__":
    check_user_passwords()