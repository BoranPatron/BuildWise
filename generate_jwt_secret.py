#!/usr/bin/env python3
"""
Skript zum Generieren eines sicheren JWT Secret Keys
"""

import secrets
import string

def generate_jwt_secret(length=64):
    """Generiert einen sicheren JWT Secret Key"""
    # Verwende Buchstaben, Zahlen und Sonderzeichen
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Generiere zufälligen String
    secret = ''.join(secrets.choice(characters) for _ in range(length))
    
    return secret

if __name__ == "__main__":
    print("🔐 Sicheren JWT Secret Key generieren...")
    print("=" * 50)
    
    # Generiere mehrere Optionen
    for i in range(3):
        secret = generate_jwt_secret(64)
        print(f"Option {i+1}: {secret}")
        print()
    
    print("=" * 50)
    print("📋 Kopiere einen der Keys und setze ihn als JWT_SECRET_KEY in Render.com")
    print("⚠️  WICHTIG: Bewahre diesen Key sicher auf und teile ihn nicht!") 