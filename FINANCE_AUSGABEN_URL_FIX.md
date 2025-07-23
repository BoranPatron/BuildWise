# Finance Ausgaben - URL-Fix

## Problem

Beim Hinzufügen einer Ausgabe trat ein 404-Fehler auf:

```
XHRPOST http://localhost:8000/api/v1/api/v1/expenses
[HTTP/1.1 404 Not Found 1ms]
```

## Root-Cause

Die URL war doppelt: `/api/v1/api/v1/expenses` statt `/api/v1/expenses`

### **Ursache:**
- Die API-Konfiguration in `api.ts` verwendet bereits `/api/v1` als Base-URL
- Der ExpenseService fügte nochmal `/api/v1/expenses` hinzu
- Das führte zu `/api/v1/api/v1/expenses`

## Lösung

### **ExpenseService Base-URL korrigiert** (`Frontend/Frontend/src/api/expenseService.ts`)

```typescript
// ❌ Vorher (doppelte URL):
class ExpenseService {
  private baseUrl = '/api/v1/expenses';
}

// ✅ Nachher (korrekte URL):
class ExpenseService {
  private baseUrl = '/expenses';
}
```

## Erklärung

### **API-Konfiguration** (`api.ts`)
```typescript
const api = axios.create({
  baseURL: getApiBaseUrl(), // => 'http://localhost:8000/api/v1'
  // ...
});
```

### **ExpenseService**
```typescript
// Mit baseUrl = '/api/v1/expenses':
// Finale URL: 'http://localhost:8000/api/v1' + '/api/v1/expenses'
// = 'http://localhost:8000/api/v1/api/v1/expenses' ❌

// Mit baseUrl = '/expenses':
// Finale URL: 'http://localhost:8000/api/v1' + '/expenses'
// = 'http://localhost:8000/api/v1/expenses' ✅
```

## Status

✅ **URL-Fix implementiert**
✅ **Backend-Server läuft** (Port 8000)
✅ **API-Endpoints verfügbar**

## Testing

### **Frontend-Test**
1. Gehe zur Finance-Seite
2. Klicke "Ausgabe hinzufügen"
3. Fülle Formular aus
4. Bestätige Erstellung
5. Prüfe ob Ausgabe angezeigt wird

### **API-Test**
```bash
# Ausgaben für Projekt laden
curl -X GET "http://localhost:8000/api/v1/expenses/project/1" \
  -H "Authorization: Bearer <token>"

# Neue Ausgabe erstellen
curl -X POST "http://localhost:8000/api/v1/expenses/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Ausgabe",
    "amount": 100.00,
    "category": "material",
    "project_id": 1,
    "date": "2024-01-15T10:00:00"
  }'
```

## Fazit

Die URL-Dopplung wurde behoben. Das Finance-Ausgaben-System sollte jetzt vollständig funktional sein.

**Status: ✅ URL-FIX IMPLEMENTIERT** 