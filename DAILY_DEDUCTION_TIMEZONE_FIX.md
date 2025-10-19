# Daily Deduction Timezone Fix

## Problem

Der tägliche Credit-Abzug für Bauträger wurde mehrmals am Tag ausgeführt, obwohl er nur einmal täglich stattfinden sollte. Dies führte zu:

- Mehrfachen Credit-Abzügen am selben Tag (siehe Screenshot: bis zu 29 Abzüge an einem Tag)
- Ungerechtfertigtem Verlust von Credits
- Inkonsistenten Daten in der `credit_events` Tabelle

## Ursachen-Analyse

### 1. Timezone-Inkonsistenz im Backend

**Problem in `app/services/credit_service.py` (Zeile 210)**:
```python
user_credits.last_daily_deduction = datetime.now()  # ❌ OHNE Timezone!
```

**Problem in `app/models/user_credits.py` (Zeile 95)**:
```python
today = datetime.now(timezone.utc).date()  # ✅ UTC
last_deduction_date = self.last_daily_deduction.date()  # ❌ Naive datetime!
```

**Resultat**: 
- Backend speichert `last_daily_deduction` als "naive datetime" (ohne Timezone-Info)
- Vergleich in `has_daily_deduction_today()` verwendet aber UTC
- Dies führt zu Fehlannahmen, ob der Abzug bereits heute stattfand

### 2. Fehlende Prüfung in `process_all_daily_deductions()`

Die Funktion `process_all_daily_deductions()` in `credit_service.py` hatte keine Prüfung, ob der tägliche Abzug bereits durchgeführt wurde. Sie setzte auch `last_daily_deduction` nicht.

### 3. Frontend-Backend Timezone-Mismatch

**Frontend (`AuthContext.tsx`)**:
```typescript
const today = new Date();  // ❌ Lokale Zeit (z.B. UTC+2 in Deutschland)
```

**Backend**:
```python
today = datetime.now(timezone.utc)  # ✅ UTC
```

**Resultat**:
- Frontend prüfte mit lokaler Zeit
- Backend prüfte mit UTC
- In verschiedenen Timezones führte dies zu unterschiedlichen "heute" Definitionen

## Implementierte Lösung

### 1. Backend Timezone-Fix

#### `app/services/credit_service.py`
```python
# ✅ VORHER
user_credits.last_daily_deduction = datetime.now()

# ✅ NACHHER
user_credits.last_daily_deduction = datetime.now(timezone.utc)
```

#### `app/models/user_credits.py`
```python
def has_daily_deduction_today(self) -> bool:
    """Prüft ob heute bereits ein täglicher Credit-Abzug stattgefunden hat"""
    if not self.last_daily_deduction:
        return False
    
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()
    
    # ✅ NEU: Stelle sicher dass last_deduction_date auch UTC verwendet
    # Falls last_daily_deduction naive datetime ist, behandle es als UTC
    if self.last_daily_deduction.tzinfo is None:
        last_deduction_date = self.last_daily_deduction.replace(tzinfo=timezone.utc).date()
    else:
        last_deduction_date = self.last_daily_deduction.astimezone(timezone.utc).date()
    
    return today == last_deduction_date
```

#### `app/services/credit_service.py` - `process_all_daily_deductions()`
```python
for user_credits in active_pro_users:
    try:
        # ✅ NEU: Prüfe ob heute bereits ein Credit abgezogen wurde
        if user_credits.has_daily_deduction_today():
            logger.info(f"User {user_credits.user_id} hat heute bereits einen Credit-Abzug erhalten - überspringe")
            continue
        
        # Verarbeite täglichen Abzug
        old_credits = user_credits.credits
        user_credits.credits -= CreditService.DAILY_CREDIT_DEDUCTION
        user_credits.total_pro_days += 1
        user_credits.last_daily_deduction = datetime.now(timezone.utc)  # ✅ NEU
        
        # ... Rest des Codes
```

### 2. Frontend Timezone-Fix

#### `Frontend/src/context/AuthContext.tsx`
```typescript
const hasDailyCreditDeductionBeenProcessed = (): boolean => {
  try {
    const lastProcessedDate = localStorage.getItem('lastDailyCreditDeduction');
    if (!lastProcessedDate) return false;
    
    // ✅ NEU: Verwende UTC für Vergleich (wie im Backend)
    const lastDate = new Date(lastProcessedDate);
    const today = new Date();
    
    // Vergleiche UTC-Datum (nicht lokales Datum)
    const lastDateUTC = new Date(Date.UTC(
      lastDate.getUTCFullYear(),
      lastDate.getUTCMonth(),
      lastDate.getUTCDate()
    ));
    const todayUTC = new Date(Date.UTC(
      today.getUTCFullYear(),
      today.getUTCMonth(),
      today.getUTCDate()
    ));
    
    return lastDateUTC.getTime() === todayUTC.getTime();
  } catch (error) {
    console.error('❌ Fehler beim Prüfen des täglichen Credit-Abzugs:', error);
    return false;
  }
};
```

## Datenbank-Bereinigung

### Verwendung des Fix-Skripts

Das Skript `fix_daily_deduction_timezone.py` behebt bestehende Daten:

```bash
cd C:\Users\user\Documents\04_Repo\BuildWise
python fix_daily_deduction_timezone.py
```

**Was das Skript tut:**
1. Konvertiert alle naive datetime Einträge zu UTC-aware datetimes
2. Identifiziert Benutzer mit mehrfachen Abzügen am selben Tag
3. Korrigiert `last_daily_deduction` auf das letzte Event des Tages
4. Zeigt detaillierte Statistiken

**Beispiel-Output:**
```
📊 Statistiken über tägliche Credit-Abzüge:
============================================================
Gesamt: 374 tägliche Abzüge in der Datenbank

Abzüge nach Datum (letzte 10 Tage):
  2025-10-08: 29 Abzüge
    ⚠️  Mehrfache Abzüge an diesem Tag!
      User-Credits-ID 1: 8 Abzüge
      User-Credits-ID 2: 7 Abzüge
      User-Credits-ID 3: 14 Abzüge
```

## Testing

### Unit-Tests

Tests für verschiedene Timezone-Szenarien:

```bash
cd C:\Users\user\Documents\04_Repo\BuildWise
python test_daily_deduction_timezone.py
```

**Test-Fälle:**
- ✅ Naive datetime vom gleichen Tag
- ✅ Naive datetime von gestern
- ✅ UTC-aware datetime vom gleichen Tag
- ✅ UTC-aware datetime von gestern
- ✅ Nicht-UTC timezone vom gleichen Tag
- ✅ None last_daily_deduction
- ✅ Edge-Case: Mitternacht UTC
- ✅ Edge-Case: Kurz vor Mitternacht

## Verifikation

### 1. Backend-Logs prüfen

Nach dem Fix sollten die Logs zeigen:
```
User {user_id} hat heute bereits einen Credit-Abzug erhalten
```

### 2. Datenbank-Abfrage

```sql
-- Prüfe Anzahl der täglichen Abzüge pro Tag und User
SELECT 
    DATE(created_at) as date,
    user_credits_id,
    COUNT(*) as deduction_count
FROM credit_events
WHERE event_type = 'DAILY_DEDUCTION'
GROUP BY DATE(created_at), user_credits_id
HAVING COUNT(*) > 1
ORDER BY date DESC;
```

Nach dem Fix sollten keine mehrfachen Abzüge mehr auftreten.

### 3. Frontend-Verhalten

- Bauträger loggt sich ein → Credit-Abzug
- Bauträger loggt sich erneut ein (gleicher Tag) → Kein Credit-Abzug
- Console zeigt: `⏭️ Kein Credit-Abzug nötig: Kein Credit-Abzug nötig (nicht im Pro-Status oder bereits heute abgezogen)`

## Wichtige Hinweise

### ⚠️ Timezone-Konsistenz

**Alle Datetime-Operationen MÜSSEN UTC verwenden:**

```python
# ✅ RICHTIG
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# ❌ FALSCH
now = datetime.now()
```

### ⚠️ Datenbank-Schema

Die Spalte `last_daily_deduction` ist als `DateTime(timezone=True)` definiert:

```python
last_daily_deduction = Column(DateTime(timezone=True), nullable=True)
```

Dies bedeutet, dass die Datenbank Timezone-Informationen speichert. Aber naive datetimes werden trotzdem akzeptiert (sie werden als UTC interpretiert).

### ⚠️ Frontend LocalStorage

Das Frontend speichert den letzten Abzug als ISO-String:
```typescript
localStorage.setItem('lastDailyCreditDeduction', new Date().toISOString());
```

`toISOString()` liefert immer UTC Zeit (z.B. `2025-10-08T20:02:41.000Z`).

## Verhinderte Probleme

Mit diesem Fix werden folgende Probleme verhindert:

1. ✅ Mehrfache Credit-Abzüge am selben Tag
2. ✅ Ungerechtfertigter Verlust von Credits
3. ✅ Inkonsistente Daten in der Datenbank
4. ✅ Timezone-bedingte Bugs in verschiedenen Regionen
5. ✅ Falsche Pro-Status Downgrade-Zeitpunkte

## Weiterführende Maßnahmen

### Empfohlene Überwachung

1. **Logging erweitern**: Füge detailliertes Logging hinzu für jeden Credit-Abzug
2. **Monitoring**: Überwache die Anzahl der täglichen Abzüge pro User
3. **Alerts**: Setze Alerts für mehrfache Abzüge am selben Tag

### Code-Review-Checkliste

Bei zukünftigen Änderungen an Credit-Funktionen:

- [ ] Verwendet alle datetime-Operationen UTC?
- [ ] Wird `last_daily_deduction` korrekt gesetzt?
- [ ] Wird `has_daily_deduction_today()` verwendet?
- [ ] Sind Frontend und Backend Timezone-konsistent?
- [ ] Wurden Unit-Tests aktualisiert?

## Zusammenfassung

| **Aspekt** | **Vorher** | **Nachher** |
|------------|------------|-------------|
| Backend datetime | Naive (keine Timezone) | UTC-aware |
| Frontend datetime | Lokale Zeit | UTC |
| Prüfung in `process_all_daily_deductions()` | ❌ Keine | ✅ Implementiert |
| Timezone-Handling in `has_daily_deduction_today()` | ❌ Inkonsistent | ✅ Robust |
| Mehrfache Abzüge pro Tag | ❌ Möglich | ✅ Verhindert |

---

**Autor**: AI Assistant  
**Datum**: 2025-10-08  
**Version**: 1.0


