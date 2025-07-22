#!/usr/bin/env python3
"""
Skript zur Aktualisierung der .env-Datei mit dem echten Client Secret
"""

def update_env_with_real_secret():
    """Aktualisiert die .env-Datei mit dem echten Client Secret"""
    
    # Echtes Client Secret
    MICROSOFT_CLIENT_SECRET = "_Hl8Q~tx77qPXElvSyl.GmnjMXSJBwpDlpyWFaDt"
    
    env_content = f"""# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=c5247a29-0cb4-4cdf-9f4c-a091a3a42383
MICROSOFT_CLIENT_SECRET={MICROSOFT_CLIENT_SECRET}
MICROSOFT_REDIRECT_URI=http://localhost:5173/auth/microsoft/callback

# Bestehende Google OAuth
GOOGLE_CLIENT_ID=1039127200110-vav094cta93qmtleivdj63un5dne17eb.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./buildwise.db

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Security
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30

# DSGVO
DATA_RETENTION_DAYS=730
CONSENT_REQUIRED=true
"""
    
    # .env-Datei aktualisieren
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env-Datei mit echtem Client Secret aktualisiert!")
    print(f"📋 Client Secret: {MICROSOFT_CLIENT_SECRET[:10]}...")
    print("\n🚀 Nächste Schritte:")
    print("   1. Backend neu starten")
    print("   2. Microsoft OAuth testen")
    print("   3. Frontend Login testen")

if __name__ == "__main__":
    update_env_with_real_secret() 