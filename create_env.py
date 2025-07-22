#!/usr/bin/env python3
"""
Skript zur Erstellung der .env-Datei für Microsoft OAuth
"""

env_content = """# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=c5247a29-0cb4-4cdf-9f4c-a091a3a42383
MICROSOFT_CLIENT_SECRET=PLACEHOLDER_CLIENT_SECRET
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

# .env-Datei erstellen
with open('.env', 'w') as f:
    f.write(env_content)

print("✅ .env-Datei erstellt!")
print("⚠️  WICHTIG: Ersetzen Sie 'PLACEHOLDER_CLIENT_SECRET' mit Ihrem echten Client Secret aus dem Azure Portal!")
print("📝 Nächste Schritte:")
print("   1. Client Secret aus Azure Portal kopieren")
print("   2. PLACEHOLDER_CLIENT_SECRET in .env-Datei ersetzen")
print("   3. Backend neu starten") 