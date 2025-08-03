# 🔄 Vollständiger Abnahme-Rechnung-Bewertung Workflow Test

## 📋 Test-Übersicht

Dieser Test überprüft den vollständigen Workflow von der Abnahme bis zur Bewertung:

1. **Abnahme starten** → 2. **Mängel dokumentieren** → 3. **Abnahme unter Vorbehalt** → 4. **Rechnung stellen** → 5. **Rechnung bezahlen** → 6. **Service Provider bewerten**

## 🧪 Test-Szenarien

### Szenario 1: Erfolgreiche Abnahme ohne Mängel
**Ziel:** Vollständiger Workflow ohne Mängel

**Schritte:**
1. **Als Bauträger:** Gewerk öffnen → "Abnahme starten" klicken
2. **Abnahme-Modal:** Checkliste durchgehen → Alle Punkte abhaken
3. **Schritt 2:** Keine Mängel dokumentieren → Weiter
4. **Schritt 3:** Service Provider bewerten (5 Sterne) → "Abnahme bestätigen"
5. **Ergebnis:** Status → "completed" → Rechnungsstellung verfügbar

### Szenario 2: Abnahme unter Vorbehalt mit Mängeln
**Ziel:** Workflow mit Mängeln und finaler Abnahme

**Schritte:**
1. **Als Bauträger:** Gewerk öffnen → "Abnahme starten" klicken
2. **Abnahme-Modal:** Checkliste durchgehen → Mängel dokumentieren
3. **Schritt 2:** Mängel mit Fotos dokumentieren → "Abnahme unter Vorbehalt"
4. **Ergebnis:** Status → "completed_with_defects" → Tasks erstellt
5. **Finale Abnahme:** "Finale Abnahme durchführen" → Mängel als behoben markieren
6. **Ergebnis:** Status → "completed" → Rechnungsstellung verfügbar

### Szenario 3: Rechnungsstellung und Bewertung
**Ziel:** Vollständiger Rechnungs- und Bewertungsprozess

**Schritte:**
1. **Als Dienstleister:** "Rechnung stellen" → PDF hochladen oder manuell erstellen
2. **Als Bauträger:** Rechnung anzeigen → "Als bezahlt markieren"
3. **Bewertung:** Service Provider Rating Modal öffnet sich
4. **Bewertung:** Qualität, Pünktlichkeit, Gesamtbewertung → Bestätigen
5. **Ergebnis:** Bewertung gespeichert → Workflow abgeschlossen

## 🔍 Zu testende Funktionen

### Backend-Endpoints
- ✅ `POST /acceptance/complete` - Abnahme abschließen
- ✅ `POST /invoices/create` - Rechnung erstellen
- ✅ `POST /invoices/upload` - PDF-Rechnung hochladen
- ✅ `GET /invoices/milestone/{id}` - Rechnung für Meilenstein abrufen
- ✅ `POST /invoices/{id}/mark-paid` - Rechnung als bezahlt markieren
- ✅ `POST /ratings/` - Service Provider bewerten

### Frontend-Komponenten
- ✅ `AcceptanceModalNew` - Abnahme-Workflow
- ✅ `FinalAcceptanceModal` - Finale Abnahme nach Mängeln
- ✅ `InvoiceModal` - Rechnungserstellung für Dienstleister
- ✅ `InvoiceManagement` - Rechnungsverwaltung für Bauträger
- ✅ `ServiceProviderRating` - Bewertung nach Rechnungsstellung

### Datenbank-Tabellen
- ✅ `acceptances` - Abnahme-Protokolle
- ✅ `acceptance_defects` - Dokumentierte Mängel
- ✅ `invoices` - Rechnungen
- ✅ `tasks` - Automatisch erstellte Mängel-Tasks
- ✅ `service_provider_ratings` - Bewertungen

## 🚨 Bekannte Probleme zu beheben

### 1. Photo Upload in Mängel-Dokumentation
**Problem:** Fotos werden als Placeholder angezeigt
**Lösung:** Storage-Zugriff überprüfen und korrigieren

### 2. Task-Erstellung für Mängel
**Problem:** Tasks werden erstellt aber nicht im Kanban angezeigt
**Lösung:** Task-Status und Anzeige-Logik korrigieren

### 3. Rechnungs-PDF Download
**Problem:** PDF-Dateien können nicht heruntergeladen werden
**Lösung:** File-Serving und Pfad-Konfiguration überprüfen

## 📊 Erfolgs-Kriterien

### ✅ Workflow-Komplettierung
- [ ] Abnahme kann gestartet werden
- [ ] Mängel können dokumentiert werden
- [ ] "Abnahme unter Vorbehalt" funktioniert
- [ ] Tasks werden automatisch erstellt
- [ ] Finale Abnahme funktioniert
- [ ] Rechnungsstellung ist verfügbar
- [ ] Rechnung kann bezahlt werden
- [ ] Bewertung wird ausgelöst

### ✅ Daten-Integrität
- [ ] Alle Daten werden in DB gespeichert
- [ ] Status-Updates funktionieren korrekt
- [ ] PDFs werden korrekt gespeichert
- [ ] Bewertungen werden verknüpft

### ✅ UI/UX
- [ ] Modals öffnen/schließen korrekt
- [ ] Status-Updates werden angezeigt
- [ ] Fehlerbehandlung funktioniert
- [ ] Loading-States sind implementiert

## 🛠️ Test-Ausführung

### Vorbereitung
1. Backend starten: `python start_backend.py`
2. Frontend starten: `cd Frontend/Frontend && npm run dev`
3. Datenbank überprüfen: `buildwise.db` sollte existieren

### Test-Ausführung
1. Als Bauträger einloggen
2. Projekt mit Gewerken öffnen
3. Gewerk mit "completion_requested" Status wählen
4. Workflow systematisch durchgehen
5. Als Dienstleister einloggen und Rechnung stellen
6. Als Bauträger Rechnung bezahlen und bewerten

### Debugging
- Browser DevTools für Frontend-Fehler
- Backend-Logs für API-Fehler
- Datenbank-Abfragen für Daten-Integrität

## 📝 Test-Protokoll

**Datum:** [Aktuelles Datum]
**Tester:** [Name]
**Version:** BuildWise v1.0.0

### Szenario 1: ✅/❌
- [ ] Abnahme starten funktioniert
- [ ] Checkliste kann ausgefüllt werden
- [ ] Bewertung kann abgegeben werden
- [ ] Status wird auf "completed" gesetzt

### Szenario 2: ✅/❌
- [ ] Mängel können dokumentiert werden
- [ ] Fotos können hochgeladen werden
- [ ] "Abnahme unter Vorbehalt" funktioniert
- [ ] Tasks werden erstellt
- [ ] Finale Abnahme funktioniert

### Szenario 3: ✅/❌
- [ ] Rechnung kann erstellt werden
- [ ] PDF kann hochgeladen werden
- [ ] Rechnung kann angezeigt werden
- [ ] Rechnung kann als bezahlt markiert werden
- [ ] Bewertungs-Modal öffnet sich
- [ ] Bewertung wird gespeichert

### Bekannte Probleme:
- [ ] Photo Upload funktioniert
- [ ] Task-Anzeige funktioniert
- [ ] PDF-Download funktioniert

## 🎯 Nächste Schritte

Nach erfolgreichem Test:
1. Bekannte Probleme beheben
2. Performance-Optimierungen
3. Erweiterte Features implementieren
4. Dokumentation aktualisieren 