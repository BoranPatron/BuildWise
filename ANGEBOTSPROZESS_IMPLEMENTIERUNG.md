# Angebotsprozess Implementierung

## Übersicht

Der Angebotsprozess ermöglicht es Dienstleistern, auf ausgeschriebene Gewerke zu reagieren und detaillierte Angebote abzugeben. Bauträger können diese Angebote dann annehmen oder ablehnen.

## 🔄 Workflow

### 1. **Dienstleister-Sicht**
1. **Gewerke finden** - Über Geo-Search oder Gewerke-Seite
2. **"Angebot abgeben"** - Button öffnet CostEstimateForm
3. **Angebot erstellen** - Detailliertes Formular ausfüllen
4. **Angebot einreichen** - Wird als "submitted" gespeichert

### 2. **Bauträger-Sicht**
1. **Angebote einsehen** - In CostEstimateDetailsModal
2. **Angebot prüfen** - Alle Details und Kalkulationen
3. **Entscheidung treffen** - "Annehmen" oder "Ablehnen"
4. **Feedback geben** - Optional bei Ablehnung

## 🏗️ Technische Implementierung

### Frontend-Komponenten

#### **ServiceProviderDashboard** (`Frontend/Frontend/src/pages/ServiceProviderDashboard.tsx`)
- ✅ **Button geändert**: "Bewerben" → "Angebot abgeben"
- ✅ **CostEstimateForm Integration**: Öffnet bei Klick
- ✅ **Angebot-Erstellung**: Vollständige API-Integration
- ✅ **State-Management**: `showCostEstimateForm`, `selectedTradeForQuote`

```typescript
const handleCreateQuote = (trade: TradeSearchResult) => {
  setSelectedTradeForQuote(trade);
  setShowCostEstimateForm(true);
};

const handleCostEstimateSubmit = async (costEstimateData: any) => {
  // Vollständige Quote-Erstellung mit allen Feldern
  const quoteData = {
    title: costEstimateData.title || `Angebot für ${selectedTradeForQuote.title}`,
    project_id: selectedTradeForQuote.project_id,
    milestone_id: selectedTradeForQuote.id,
    service_provider_id: user.id,
    total_amount: parseFloat(costEstimateData.total_amount) || 0,
    // ... weitere Felder
  };
  
  const newQuote = await createQuote(quoteData);
};
```

#### **CostEstimateForm** (`Frontend/Frontend/src/components/CostEstimateForm.tsx`)
- ✅ **Umfassendes Formular** mit allen Quote-Feldern
- ✅ **Validierung** und Benutzerfreundlichkeit
- ✅ **Dokument-Upload** für Angebots-PDFs
- ✅ **Automatische Vorausfüllung** mit User-Daten

#### **CostEstimateDetailsModal** (`Frontend/Frontend/src/components/CostEstimateDetailsModal.tsx`)
- ✅ **Angebot-Anzeige** für Bauträger
- ✅ **Accept/Reject Buttons**: "Kostenvoranschlag annehmen/ablehnen"
- ✅ **Ablehnungsgrund** mit Textfeld
- ✅ **Status-Management** (submitted, accepted, rejected)

### Backend-API

#### **Quote Model** (`app/models/quote.py`)
```python
class Quote(Base):
    # Basis-Informationen
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)
    
    # Beziehungen
    project_id = Column(Integer, ForeignKey("projects.id"))
    milestone_id = Column(Integer, ForeignKey("milestones.id"))
    service_provider_id = Column(Integer, ForeignKey("users.id"))
    
    # Finanzielle Details
    total_amount = Column(Float, nullable=False)
    labor_cost = Column(Float, nullable=True)
    material_cost = Column(Float, nullable=True)
    overhead_cost = Column(Float, nullable=True)
    
    # Zeitplan
    estimated_duration = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    
    # Dienstleister-Informationen
    company_name = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Status-Tracking
    submitted_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
```

#### **Quote API** (`app/api/quotes.py`)
- ✅ **POST /quotes/** - Angebot erstellen
- ✅ **GET /quotes/** - Angebote abrufen
- ✅ **POST /quotes/{id}/accept** - Angebot annehmen
- ✅ **POST /quotes/{id}/reject** - Angebot ablehnen
- ✅ **POST /quotes/{id}/submit** - Angebot einreichen

#### **Quote Service** (`app/services/quote_service.py`)
- ✅ **create_quote()** - Angebot-Erstellung
- ✅ **accept_quote()** - Annahme-Logik
- ✅ **reject_quote()** - Ablehnungs-Logik
- ✅ **get_quotes_for_milestone()** - Gewerk-bezogene Angebote

### Frontend-Services

#### **quoteService.ts** (`Frontend/Frontend/src/api/quoteService.ts`)
```typescript
export async function createQuote(data: QuoteData) {
  const response = await api.post('/quotes/', data);
  return response.data;
}

export async function acceptQuote(id: number) {
  const response = await api.post(`/quotes/${id}/accept`);
  return response.data;
}

export async function rejectQuote(id: number, rejectionReason?: string) {
  const response = await api.post(`/quotes/${id}/reject`, {
    rejection_reason: rejectionReason
  });
  return response.data;
}
```

## 📊 Quote-Status-Workflow

```
DRAFT → SUBMITTED → ACCEPTED/REJECTED
  ↑         ↑            ↑
  |         |            |
Erstellt  Eingereicht  Entschieden
```

### Status-Definitionen:
- **DRAFT**: Angebot wird erstellt (nicht sichtbar für Bauträger)
- **SUBMITTED**: Angebot eingereicht (sichtbar für Bauträger)
- **UNDER_REVIEW**: In Prüfung (optional)
- **ACCEPTED**: Angenommen (Auftrag erteilt)
- **REJECTED**: Abgelehnt (mit Grund)
- **EXPIRED**: Abgelaufen (nach valid_until Datum)

## 🔐 Berechtigungen

### Dienstleister können:
- ✅ Angebote für öffentliche Gewerke erstellen
- ✅ Eigene Angebote einsehen und bearbeiten
- ✅ Angebote zurückziehen (löschen)
- ❌ Angebote anderer Dienstleister sehen

### Bauträger können:
- ✅ Alle Angebote für ihre Projekte sehen
- ✅ Angebote annehmen/ablehnen
- ✅ Ablehnungsgründe angeben
- ✅ Angebote zurücksetzen
- ❌ Angebote anderer Bauträger sehen

## 🚀 Integration Points

### 1. **Geo-Search Integration**
- ServiceProviderDashboard zeigt Geo-Gewerke
- "Angebot abgeben" Button startet Angebotsprozess
- Automatische Projekt-/Gewerk-Zuordnung

### 2. **Projekt-Integration**
- Angebote sind mit Projekten und Gewerken verknüpft
- Bauträger sehen Angebote in Projekt-Kontext
- Automatische Kostenposition-Erstellung bei Annahme

### 3. **Gebühren-Integration**
- BuildWise-Gebühren werden bei Angebot-Annahme berechnet
- Automatische Rechnungserstellung
- Integration mit Subscription-System

## 🎯 Verbesserungen implementiert

### ServiceProviderDashboard:
1. **Button-Text**: "Bewerben" → "Angebot abgeben"
2. **Direkter Workflow**: Klick öffnet sofort CostEstimateForm
3. **Vollständige Integration**: Alle Quote-Felder werden korrekt übertragen
4. **User-Daten**: Automatische Vorausfüllung mit Dienstleister-Informationen
5. **Fehlerbehandlung**: Umfassendes Error-Handling

### Robustheit:
- ✅ **Type-Safety**: TypeScript-Interfaces für alle Daten
- ✅ **Validation**: Frontend- und Backend-Validierung
- ✅ **Error-Handling**: Umfassendes Fehler-Management
- ✅ **Loading-States**: Benutzerfreundliche Lade-Anzeigen
- ✅ **State-Management**: Saubere Zustandsverwaltung

## 📝 Nächste Schritte (Optional)

1. **Angebot-Vergleich**: Side-by-side Vergleich mehrerer Angebote
2. **Bewertungssystem**: Dienstleister-Bewertungen nach Projektabschluss
3. **Benachrichtigungen**: Push-Notifications bei Angebot-Status-Änderungen
4. **Dokument-Management**: Bessere Verwaltung von Angebots-Dokumenten
5. **Mobile-Optimierung**: Responsive Design für mobile Geräte

## ✅ Status: Vollständig implementiert und funktional

Der Angebotsprozess ist vollständig implementiert und getestet. Dienstleister können über die Geo-Search Angebote abgeben, und Bauträger können diese in ihrer gewohnten Ansicht annehmen oder ablehnen. 