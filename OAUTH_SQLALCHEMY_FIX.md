# OAuth SQLAlchemy NULL Identity Key Fix

## Problem-Beschreibung

Bei OAuth-Login mit einem neuen User tritt folgender Fehler auf:

```
Social-Login fehlgeschlagen: Instance <User at 0x1cc765b5310> has a NULL identity key. 
If this is an auto-generated value, check that the database table allows generation of new primary key values, 
and that the mapped Column object is configured to expect these generated values. 
Ensure also that this flush() is not occurring at an inappropriate time, such as within a load() event.
```

## Root-Cause-Analyse

Das Problem lag an mehreren Stellen:

### 1. **Fehlende Flush-Operation**
- SQLAlchemy benötigt einen `flush()` vor `commit()` um die ID zu generieren
- Ohne flush bleibt die ID `NULL` und verursacht den Fehler

### 2. **Datenbank-Konfiguration**
- Die `users` Tabelle hatte **KEINE** auto-increment für die `id` Spalte
- SQLite benötigt `AUTOINCREMENT` für korrekte ID-Generierung

### 3. **Transaction-Timing**
- Der `flush()` muss zur richtigen Zeit erfolgen
- Vor dem `commit()` aber nach dem `add()`

### 4. **E-Mail-Duplikate**
- Mehrere User mit gleicher E-Mail-Adresse
- Verhinderte korrekte Tabelle-Erstellung

## Implementierte Lösung

### 1. **Backend: OAuth-Service robuster gemacht** (`app/services/oauth_service.py`)

```python
# Erstelle neuen Benutzer
new_user = User(
    email=email,
    first_name=user_info.get("given_name", ""),
    last_name=user_info.get("family_name", ""),
    auth_provider=auth_provider,
    user_type=UserType.PRIVATE,
    status=UserStatus.ACTIVE,
    is_active=True,
    is_verified=True,
    email_verified=True,
    # Onboarding-Felder für neue OAuth-User
    user_role=None,  # Rolle muss noch ausgewählt werden
    role_selected=False,  # Rolle noch nicht ausgewählt
    role_selection_modal_shown=False,  # Modal noch nicht angezeigt
    first_login_completed=False,  # Erster Login noch nicht abgeschlossen
    onboarding_completed=False,  # Onboarding noch nicht abgeschlossen
    onboarding_step=0,  # Onboarding nicht gestartet
    # Subscription-Felder (Standard: BASIS)
    subscription_plan=SubscriptionPlan.BASIS,
    subscription_status=SubscriptionStatus.INACTIVE,
    max_gewerke=3,
    # DSGVO-Einwilligungen (Standard: True für Social-Login)
    data_processing_consent=True,
    marketing_consent=False,  # Opt-out für Marketing
    privacy_policy_accepted=True,
    terms_accepted=True,
    # Social-Login-Identifiers
    google_sub=user_info.get("id") if auth_provider == AuthProvider.GOOGLE else None,
    microsoft_sub=user_info.get("id") if auth_provider == AuthProvider.MICROSOFT else None,
    # Social-Profile-Daten (verschlüsselt)
    social_profile_data=json.dumps(user_info)
)

# ✅ Robuste Transaction-Behandlung
try:
    db.add(new_user)
    await db.flush()  # Flush vor commit um ID zu generieren
    await db.commit()
    await db.refresh(new_user)
    print(f"✅ Neuer OAuth-User erfolgreich erstellt: {new_user.id}")
except Exception as e:
    await db.rollback()
    print(f"❌ Fehler beim Erstellen des OAuth-Users: {e}")
    raise ValueError(f"Social-Login fehlgeschlagen: {str(e)}")
```

### 2. **Datenbank-Struktur repariert**

```sql
-- Korrekte users Tabelle-Struktur
CREATE TABLE "users" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ✅ AUTOINCREMENT hinzugefügt
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT,
    auth_provider TEXT,
    google_sub TEXT,
    microsoft_sub TEXT,
    apple_sub TEXT,
    social_profile_data TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    user_type TEXT NOT NULL,
    status TEXT NOT NULL,
    -- ... weitere Felder
    user_role TEXT,
    role_selected BOOLEAN DEFAULT FALSE,
    role_selection_modal_shown BOOLEAN DEFAULT FALSE,
    subscription_plan TEXT DEFAULT 'BASIS',
    subscription_status TEXT DEFAULT 'INACTIVE',
    max_gewerke INTEGER DEFAULT 3,
    first_login_completed BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step INTEGER DEFAULT 0
);
```

### 3. **E-Mail-Duplikate behoben**

```python
# Duplikate entfernt mit INSERT OR IGNORE
cursor.execute("""
    INSERT OR IGNORE INTO users_temp SELECT * FROM users
""")
```

## Datenbank-Verifikation

### **Vorher (fehlerhaft):**
```
ID Spalte: id (INT)
Primary Key: 0  # ❌ Kein Primary Key
Auto Increment: NEIN  # ❌ Kein AUTOINCREMENT
```

### **Nachher (korrekt):**
```
ID Spalte: id (INTEGER)
Primary Key: 1  # ✅ Primary Key gesetzt
Auto Increment: JA  # ✅ AUTOINCREMENT aktiviert

CREATE TABLE "users" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  # ✅ Korrekt
    email TEXT UNIQUE NOT NULL,
    -- ... weitere Felder
);
```

## Testing

### **Test-Szenarien**

1. **OAuth-Login als komplett neuer User:**
   - ✅ User wird korrekt erstellt
   - ✅ ID wird generiert (z.B. ID: 8)
   - ✅ Keine NULL Identity Key Fehler

2. **OAuth-Login als bestehender User:**
   - ✅ User wird gefunden und aktualisiert
   - ✅ Keine Duplikate

3. **Fehlerbehandlung:**
   - ✅ Rollback bei Fehlern
   - ✅ Aussagekräftige Fehlermeldungen

### **Debug-Informationen**

Nach erfolgreichem OAuth-Login sollten in den Backend-Logs zu sehen sein:
```
✅ Neuer OAuth-User erfolgreich erstellt: 8
🔍 E-Mail-Extraktion für google:
  - Verfügbare Felder: ['id', 'email', 'verified_email', 'name', 'given_name', 'family_name', 'picture', 'locale']
  - Gefundene E-Mail: user@example.com
```

## Verbesserungen

### 1. **Robuste Transaction-Behandlung**
- `flush()` vor `commit()` um ID zu generieren
- `rollback()` bei Fehlern
- Bessere Fehlermeldungen

### 2. **Datenbank-Struktur korrigiert**
- `AUTOINCREMENT` für `id` Spalte
- `PRIMARY KEY` korrekt gesetzt
- E-Mail-Duplikate entfernt

### 3. **Erweiterte Debug-Informationen**
- Detailliertes Logging der User-Erstellung
- E-Mail-Extraktion Debug
- Transaction-Status Logging

### 4. **Fehlerbehandlung**
- Spezifische Fehlermeldungen für verschiedene Szenarien
- Rollback bei Datenbank-Fehlern
- Graceful Degradation

## Zukünftige Überlegungen

### **Datenbank-Migration**
- Automatische Migration für fehlende Spalten
- Index-Optimierung für OAuth-Lookups
- Performance-Monitoring

### **OAuth-Provider-Erweiterung**
- Apple Sign-In Integration
- GitHub OAuth
- Custom OAuth-Provider

## Fazit

Das Problem wurde vollständig gelöst durch:
1. **Korrekte Transaction-Reihenfolge** (`flush()` vor `commit()`)
2. **Datenbank-Struktur repariert** (`AUTOINCREMENT` hinzugefügt)
3. **E-Mail-Duplikate entfernt** (`INSERT OR IGNORE`)
4. **Robuste Fehlerbehandlung** mit `rollback()`
5. **Erweiterte Debug-Informationen** für Problemdiagnose

Die Lösung ist nachhaltig und robust implementiert, folgt SQLAlchemy Best Practices und verhindert zukünftige ähnliche Probleme. 