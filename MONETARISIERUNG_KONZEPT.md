# BuildWise Monetarisierungskonzept

## Übersicht

BuildWise implementiert ein transparentes und faires Monetarisierungskonzept basierend auf einer 1%-Gebühr auf alle akzeptierten Angebote/Kostenvoranschläge. Dies stellt sicher, dass wir nur bei erfolgreichen Projekten verdienen.

## Gebührenmodell

### 1% Gebühr auf akzeptierte Angebote
- **Gebührensatz:** 1% des Angebotswerts
- **Berechnungszeitpunkt:** Bei Annahme eines Kostenvoranschlags
- **Transparenz:** Vollständige Offenlegung der Gebührenberechnung

### Beispiel
- Angebotswert: 10.000€
- BuildWise-Gebühr: 100€ (1%)
- Gesamtkosten für Kunde: 10.100€

## Technische Implementierung

### Backend-Architektur

#### 1. Datenbank-Modelle
```python
# BuildWiseFee - Haupttabelle für Gebühren
class BuildWiseFee(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    fee_month = Column(Integer)  # 1-12
    fee_year = Column(Integer)
    total_amount = Column(Float)
    fee_percentage = Column(Float, default=1.0)
    status = Column(String(20), default="open")
    # ... weitere Felder

# BuildWiseFeeItem - Einzelne Gebührenpositionen
class BuildWiseFeeItem(Base):
    id = Column(Integer, primary_key=True)
    buildwise_fee_id = Column(Integer, ForeignKey("buildwise_fees.id"))
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    quote_amount = Column(Float)
    fee_amount = Column(Float)
    fee_percentage = Column(Float, default=1.0)
    # ... weitere Felder
```

#### 2. API-Endpunkte
- `POST /api/v1/buildwise-fees/calculate-fee` - Berechne Gebühr für Angebot
- `GET /api/v1/buildwise-fees/` - Hole alle Gebühren
- `GET /api/v1/buildwise-fees/statistics` - Hole Statistiken
- `POST /api/v1/buildwise-fees/{fee_id}/mark-paid` - Markiere als bezahlt
- `POST /api/v1/buildwise-fees/{fee_id}/generate-invoice` - Generiere Rechnung

#### 3. Service-Logik
```python
def calculate_fee_for_quote(self, quote_id: int, user_id: int):
    # Prüfe ob Angebot akzeptiert wurde
    quote = self.db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.status == "accepted"
    ).first()
    
    # Berechne 1% Gebühr
    fee_amount = quote.total_amount * 0.01
    
    # Erstelle oder aktualisiere monatliche Gebühr
    fee = self._get_or_create_monthly_fee(user_id, quote.project_id)
    fee.total_amount += fee_amount
    
    # Erstelle Gebühren-Item
    fee_item = BuildWiseFeeItem(
        buildwise_fee_id=fee.id,
        quote_id=quote_id,
        quote_amount=quote.total_amount,
        fee_amount=fee_amount,
        fee_percentage=1.0
    )
    
    return fee_data
```

### Frontend-Integration

#### 1. Gebühren-Seite
- **Route:** `/buildwise-fees`
- **Funktionen:**
  - Monatliche Übersicht aller Gebühren
  - Statistiken und Auswertungen
  - Rechnungsgenerierung
  - Zahlungsstatus-Verwaltung

#### 2. Automatische Gebührenberechnung
```typescript
// In handleAcceptQuote-Funktion
const handleAcceptQuote = async (quoteId: number) => {
  // Angebot akzeptieren
  await acceptQuote(quoteId);
  
  // BuildWise-Gebühr berechnen
  try {
    const feeData = await calculateFeeForQuote(quoteId);
    setSuccess(`Kostenvoranschlag angenommen! BuildWise-Gebühr: ${feeData.fee_amount}€`);
  } catch (error) {
    console.error('Gebührenberechnung fehlgeschlagen:', error);
  }
};
```

## Monatliche Rechnungserstellung

### Automatisierter Prozess
1. **Monatsende:** Automatische Erstellung von Rechnungen
2. **Rechnungsinhalt:**
   - Alle Gebühren des Monats
   - Detaillierte Aufschlüsselung
   - Fälligkeitsdatum (28. des Folgemonats)
3. **Dokumentenbereich:** Rechnungen werden automatisch im Dokumentenbereich abgelegt

### Rechnungsbeispiel
```
BUILDWISE GMBH
Gebührenrechnung

Rechnungsnummer: BW-202412-0001
Rechnungsdatum: 31.12.2024
Fälligkeitsdatum: 28.01.2025

Rechnung an:
Max Mustermann
max@example.com

Gebühren für Dezember 2024

Gesamtbetrag: 250,00€
Anzahl Gebühren: 3

- Angebot "Elektroinstallation": 15.000€ → 150,00€
- Angebot "Sanitär": 8.000€ → 80,00€
- Angebot "Heizung": 2.000€ → 20,00€

Bitte überweisen Sie den Betrag innerhalb von 14 Tagen.
```

## Zahlungsabwicklung

### Status-System
- **open:** Offen, noch nicht bezahlt
- **paid:** Bezahlt
- **overdue:** Überfällig (nach 28 Tagen)
- **cancelled:** Storniert

### Zahlungsmethoden
- Banküberweisung
- Automatische Mahnung bei Überfälligkeit
- Zahlungserinnerungen per E-Mail

## Transparenz und Compliance

### Offenlegung
- **Gebührensatz:** Immer 1%, keine versteckten Kosten
- **Berechnungsgrundlage:** Nur akzeptierte Angebote
- **Rechnungsstellung:** Monatlich, transparent

### Datenschutz
- **DSGVO-konform:** Alle Daten werden DSGVO-konform verarbeitet
- **Datenminimierung:** Nur notwendige Daten werden gespeichert
- **Löschung:** Daten werden nach gesetzlichen Fristen gelöscht

## Vorteile des Modells

### Für Kunden
- **Transparenz:** Klare 1%-Gebühr, keine versteckten Kosten
- **Erfolgsbasiert:** Nur bei erfolgreichen Projekten
- **Flexibilität:** Keine monatlichen Grundgebühren
- **Kontrolle:** Vollständige Übersicht aller Gebühren

### Für BuildWise
- **Skalierbarkeit:** Wachstum mit Kundenprojekten
- **Nachhaltigkeit:** Langfristige Kundenbeziehungen
- **Transparenz:** Vertrauensvolle Geschäftsbeziehung
- **Automatisierung:** Effiziente Prozesse

## Technische Features

### Automatisierung
- **Automatische Gebührenberechnung** bei Angebotsannahme
- **Monatliche Rechnungserstellung** am Monatsende
- **Überfälligkeitsprüfung** für offene Rechnungen
- **Dokumentenintegration** im bestehenden System

### Monitoring
- **Echtzeit-Statistiken** für Gebühren
- **Zahlungsstatus-Tracking**
- **Automatische Benachrichtigungen**

### Integration
- **Nahtlose Integration** in bestehende Workflows
- **Dokumentenbereich** für Rechnungen
- **Finance-Bereich** für Kostenpositionen
- **Benachrichtigungssystem** für wichtige Ereignisse

## Zukunftsperspektiven

### Erweiterte Features
- **Automatische Zahlungsabwicklung** via SEPA-Lastschrift
- **Differenzierte Gebührensätze** für verschiedene Projekttypen
- **Rabattsystem** für Stammkunden
- **API-Integration** für externe Buchhaltungssysteme

### Skalierung
- **Multi-Tenant-Architektur** für verschiedene Organisationen
- **Internationale Expansion** mit lokalen Zahlungsmethoden
- **Mobile App** für Zahlungsverwaltung

## Fazit

Das BuildWise-Monetarisierungskonzept bietet eine faire, transparente und nachhaltige Lösung für die Finanzierung der Plattform. Durch die 1%-Gebühr auf akzeptierte Angebote profitieren sowohl Kunden als auch BuildWise von erfolgreichen Projekten, während die vollständige Transparenz das Vertrauen stärkt. 