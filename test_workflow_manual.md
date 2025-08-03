# 🔄 Manueller Test: Vollständiger Abnahme-Rechnung-Bewertung Workflow

## 📋 Vorbereitung

### 1. Backend und Frontend starten
```bash
# Terminal 1: Backend
cd BuildWise
python start_backend.py

# Terminal 2: Frontend  
cd Frontend/Frontend
npm run dev
```

### 2. Test-Daten vorbereiten
- Bauträger-Account: `bautraeger@test.com` / `password123`
- Dienstleister-Account: `dienstleister@test.com` / `password123`
- Projekt mit Gewerken erstellen
- Gewerk auf Status "completion_requested" setzen

## 🧪 Test-Szenarien

### Szenario 1: Abnahme ohne Mängel

#### Schritt 1: Als Bauträger einloggen
1. Frontend öffnen: `http://localhost:5173`
2. Login als Bauträger
3. Projekt mit Gewerken öffnen
4. Gewerk mit Status "completion_requested" wählen

#### Schritt 2: Abnahme starten
1. **CostEstimateDetailsModal** öffnen
2. **"Abnahme-Workflow"** Sektion finden
3. **"Abnahme starten"** Button klicken
4. **AcceptanceModal** sollte sich öffnen

#### Schritt 3: Abnahme durchführen
1. **Schritt 1: Checkliste**
   - Alle 6 Punkte abhaken:
     - [x] Arbeiten vollständig ausgeführt
     - [x] Qualität entspricht Anforderungen  
     - [x] Spezifikationen eingehalten
     - [x] Sicherheitsvorschriften beachtet
     - [x] Arbeitsplatz ordnungsgemäß gereinigt
     - [x] Erforderliche Dokumente übergeben
   - **"Weiter"** klicken

2. **Schritt 2: Mängel & Fotos dokumentieren**
   - Keine Mängel hinzufügen
   - **"Weiter"** klicken

3. **Schritt 3: Service Provider bewerten**
   - Qualität: ⭐⭐⭐⭐⭐ (5 Sterne)
   - Pünktlichkeit: ⭐⭐⭐⭐⭐ (5 Sterne)
   - Gesamtbewertung: ⭐⭐⭐⭐⭐ (5 Sterne)
   - Notizen: "Sehr zufrieden mit der Leistung"
   - **"Abnahme bestätigen"** klicken

#### Schritt 4: Ergebnis prüfen
- ✅ Status sollte auf "completed" wechseln
- ✅ "Rechnungsmanagement" Sektion sollte erscheinen
- ✅ Dienstleister kann jetzt Rechnung stellen

### Szenario 2: Abnahme unter Vorbehalt mit Mängeln

#### Schritt 1: Abnahme mit Mängeln
1. **Schritt 2: Mängel & Fotos dokumentieren**
   - **"Mangel hinzufügen"** klicken
   - Mangel-Details eingeben:
     - Titel: "Fliesen nicht gleichmäßig verlegt"
     - Beschreibung: "In der Ecke sind die Fliesen schief"
     - Schweregrad: "MAJOR"
     - Raum: "Badezimmer"
     - Position: "Ecke links"
   - Foto hochladen (optional)
   - **"Mangel speichern"** klicken
   - **"Abnahme unter Vorbehalt"** klicken

#### Schritt 2: Ergebnis prüfen
- ✅ Status sollte auf "completed_with_defects" wechseln
- ✅ Tasks sollten für Dienstleister erstellt werden
- ✅ "Finale Abnahme durchführen" Button sollte erscheinen

#### Schritt 3: Finale Abnahme
1. **"Finale Abnahme durchführen"** klicken
2. **FinalAcceptanceModal** öffnet sich
3. Mängel als behoben markieren
4. **"Finale Abnahme bestätigen"** klicken
5. Status sollte auf "completed" wechseln

### Szenario 3: Rechnungsstellung und Bewertung

#### Schritt 1: Als Dienstleister einloggen
1. Als Dienstleister einloggen
2. **TradeDetailsModal** öffnen
3. **"Rechnung stellen"** Button sollte sichtbar sein

#### Schritt 2: Rechnung erstellen
1. **"Rechnung stellen"** klicken
2. **InvoiceModal** öffnet sich
3. Rechnungsdetails eingeben:
   - Rechnungsnummer: "INV-2024-001"
   - Gesamtbetrag: 5000,00 €
   - Beschreibung: "Badezimmer-Renovierung"
   - PDF hochladen (optional)
4. **"Rechnung einreichen"** klicken

#### Schritt 3: Als Bauträger Rechnung bearbeiten
1. Als Bauträger einloggen
2. **CostEstimateDetailsModal** öffnen
3. **InvoiceManagement** Sektion finden
4. Rechnung anzeigen:
   - **"Ansehen"** klicken
   - **"Download"** klicken
5. **"Als bezahlt markieren"** klicken

#### Schritt 4: Service Provider bewerten
1. **ServiceProviderRating** Modal öffnet sich automatisch
2. Bewertung abgeben:
   - Qualität: ⭐⭐⭐⭐⭐
   - Pünktlichkeit: ⭐⭐⭐⭐⭐  
   - Kommunikation: ⭐⭐⭐⭐⭐
   - Gesamtbewertung: ⭐⭐⭐⭐⭐
   - Notizen: "Hervorragende Arbeit"
3. **"Bewertung abschicken"** klicken

## 🔍 Zu überprüfende Punkte

### Backend-Endpoints
- [ ] `POST /acceptance/complete` - Abnahme abschließen
- [ ] `GET /acceptance/{id}` - Abnahme abrufen
- [ ] `POST /invoices/create` - Rechnung erstellen
- [ ] `GET /invoices/milestone/{id}` - Rechnung abrufen
- [ ] `POST /invoices/{id}/mark-paid` - Rechnung bezahlen
- [ ] `POST /ratings/` - Bewertung erstellen

### Frontend-Komponenten
- [ ] `AcceptanceModalNew` - Abnahme-Workflow
- [ ] `FinalAcceptanceModal` - Finale Abnahme
- [ ] `InvoiceModal` - Rechnungserstellung
- [ ] `InvoiceManagement` - Rechnungsverwaltung
- [ ] `ServiceProviderRating` - Bewertung

### Datenbank-Tabellen
- [ ] `acceptances` - Abnahme-Protokolle
- [ ] `acceptance_defects` - Dokumentierte Mängel
- [ ] `invoices` - Rechnungen
- [ ] `tasks` - Automatisch erstellte Tasks
- [ ] `service_provider_ratings` - Bewertungen

## 🚨 Bekannte Probleme

### 1. Photo Upload
**Problem:** Fotos werden als Placeholder angezeigt
**Workaround:** Fotos optional lassen, Text-Beschreibung verwenden

### 2. Task-Anzeige
**Problem:** Tasks werden erstellt aber nicht im Kanban angezeigt
**Workaround:** Tasks manuell in `/tasks` überprüfen

### 3. PDF-Download
**Problem:** PDF-Dateien können nicht heruntergeladen werden
**Workaround:** Rechnung nur anzeigen, nicht herunterladen

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