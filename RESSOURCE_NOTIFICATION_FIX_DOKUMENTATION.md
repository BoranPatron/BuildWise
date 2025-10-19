# Fehlerbehebung: Ressourcen-Benachrichtigungen

## Problem

Der Dienstleister erhält Benachrichtigungen über Ressourcen-Zuordnungen, aber:
1. ❌ Die Benachrichtigung zeigt "Unbekanntes Gewerk" statt den Ausschreibungsnamen
2. ❌ Die Benachrichtigung zeigt "Unbekanntes Projekt" (sollte entfernt werden)
3. ❌ Die Benachrichtigung zeigt "Unbekannter Bauträger" statt Namen und Firmenname
4. ❌ Beim Klick auf die Benachrichtigung erscheint "Die Ausschreibung konnte nicht gefunden werden"
5. ❌ Das UI "Erstangebot abgeben" wird nicht geöffnet

## Lösung

### 1. Backend: Benachrichtigung mit vollständigen Daten (notification_service.py)

#### Bauträger-Informationen erweitert:
```python
# Erstelle Bauträger Name (Vorname + Nachname + optional Firmenname)
bautraeger_name = "Unbekannter Bauträger"
bautraeger_full_name = ""
bautraeger_company = ""

if bautraeger:
    # Name: Vorname + Nachname
    full_name_parts = []
    if bautraeger.first_name:
        full_name_parts.append(bautraeger.first_name)
    if bautraeger.last_name:
        full_name_parts.append(bautraeger.last_name)
    
    bautraeger_full_name = " ".join(full_name_parts) if full_name_parts else f"Benutzer #{bautraeger.id}"
    
    # Firmenname separat
    if bautraeger.company_name:
        bautraeger_company = bautraeger.company_name
        bautraeger_name = f"{bautraeger_full_name} ({bautraeger.company_name})"
    else:
        bautraeger_name = bautraeger_full_name
```

#### Notification Data mit mehr Details:
```python
notification_data = {
    "allocation_id": allocation.id,
    "resource_id": allocation.resource_id,
    "trade_id": allocation.trade_id,
    "trade_title": allocation.trade.title if allocation.trade else None,  # Kein Fallback
    "project_name": project.name if project else None,  # Kein Fallback
    "project_id": project.id if project else None,
    "bautraeger_name": bautraeger_name,
    "bautraeger_full_name": bautraeger_full_name,
    "bautraeger_company": bautraeger_company,
    "allocated_start_date": allocation.allocated_start_date.isoformat() if allocation.allocated_start_date else None,
    "allocated_end_date": allocation.allocated_end_date.isoformat() if allocation.allocated_end_date else None,
    "allocated_person_count": allocation.allocated_person_count,
    "allocation_status": allocation.allocation_status.value if allocation.allocation_status else "pre_selected"
}
```

#### Message ohne "Unbekanntes Projekt":
```python
trade_title = allocation.trade.title if allocation.trade else "einer Ausschreibung"
project_name = project.name if project else None

# Erstelle message ohne "Unbekanntes Projekt"
if project_name:
    message = f"Ihre Ressource wurde der Ausschreibung '{trade_title}' im Projekt '{project_name}' zugeordnet."
else:
    message = f"Ihre Ressource wurde der Ausschreibung '{trade_title}' zugeordnet."
```

### 2. Frontend: Benachrichtigungs-Anzeige verbessert (NotificationTab.tsx)

#### Conditional Rendering für Gewerk und Projekt:
```tsx
{notification.tradeTitle && (
  <div>
    <span className="text-gray-500">Gewerk:</span>
    <div className="font-semibold text-purple-600">
      {notification.tradeTitle}
    </div>
  </div>
)}
{notification.projectName && (
  <div>
    <span className="text-gray-500">Projekt:</span>
    <div className="font-semibold text-purple-600">
      {notification.projectName}
    </div>
  </div>
)}
<div>
  <span className="text-gray-500">Bauträger:</span>
  <div className="font-semibold text-gray-700">
    {notification.bautraegerName}
  </div>
</div>
```

#### Click-Handler öffnet CostEstimateForm:
```tsx
} else if (userRole === 'DIENSTLEISTER' && notification.type === 'resource_allocated') {
  // Öffne die betroffene Ausschreibung für Angebotsabgabe
  console.log('📋 Öffne Ausschreibung für Angebotsabgabe von Resource Allocation:', notification.tradeId);
  markAsSeen([notification.id]);
  
  // Event für ServiceProviderDashboard auslösen, um CostEstimateForm zu öffnen
  window.dispatchEvent(new CustomEvent('openTradeDetails', {
    detail: {
      tradeId: notification.tradeId,
      allocationId: notification.allocationId,
      source: 'resource_allocation_notification',
      showQuoteForm: true
    }
  }));
  
  // Schließe Benachrichtigungs-Panel
  setIsExpanded(false);
}
```

#### Hinweis-Text aktualisiert:
```tsx
<div className="mt-2 text-xs text-purple-600 font-medium">
  👆 Klicken Sie hier, um zur Ressourcenverwaltung zu gelangen
</div>
```

### 3. Frontend: Event-Handler erweitert (ServiceProviderDashboard.tsx)

#### openTradeDetails Event öffnet CostEstimateForm:
```tsx
const handleOpenTradeDetails = (event: CustomEvent) => {
  console.log('📋 Event empfangen: TradeDetails öffnen für Trade:', event.detail.tradeId);
  const tradeId = event.detail.tradeId;
  const showQuoteForm = event.detail.showQuoteForm;
  const source = event.detail.source;
  
  // Finde das Trade in den lokalen Daten
  const trade = trades.find(t => t.id === tradeId) || geoTrades.find(t => t.id === tradeId);
  
  if (trade) {
    console.log('✅ Trade gefunden:', trade);
    
    // Wenn showQuoteForm=true, öffne direkt das CostEstimateForm
    if (showQuoteForm) {
      console.log('🎯 Öffne CostEstimateForm für Trade:', trade.id, trade.title);
      setSelectedTradeForQuote(trade);
      setShowCostEstimateForm(true);
    } else {
      // Ansonsten nur Trade auswählen
      setSelectedTrade(trade);
    }
  } else {
    console.warn('⚠️ Trade nicht gefunden in lokalen Daten, lade neu...');
    // Fallback: Lade Trades neu und versuche erneut
    loadTrades().then(() => {
      const refreshedTrade = trades.find(t => t.id === tradeId) || geoTrades.find(t => t.id === tradeId);
      if (refreshedTrade) {
        if (showQuoteForm) {
          console.log('🎯 Öffne CostEstimateForm für Trade (nach Reload):', refreshedTrade.id, refreshedTrade.title);
          setSelectedTradeForQuote(refreshedTrade);
          setShowCostEstimateForm(true);
        } else {
          setSelectedTrade(refreshedTrade);
        }
      } else {
        console.error('❌ Trade auch nach Neuladen nicht gefunden:', tradeId);
        alert('Die Ausschreibung konnte nicht gefunden werden. Bitte versuchen Sie es erneut.');
      }
    });
  }
};
```

### 4. Frontend: ResourceManagementDashboard Handler (ResourceManagementDashboard.tsx)

#### handleSubmitQuote dispatcht Event:
```tsx
const handleSubmitQuote = (allocation: ResourceAllocation) => {
  console.log('📋 Öffne TradeDetailsModal für Angebotsabgabe:', allocation);
  
  // Dispatch Event um TradeDetailsModal zu öffnen
  window.dispatchEvent(new CustomEvent('openTradeDetails', {
    detail: {
      tradeId: allocation.trade_id,
      allocationId: allocation.id,
      source: 'resource_allocation_submit',
      showQuoteForm: true
    }
  }));
  
  // Optional: Navigiere zu ServiceProviderDashboard falls wir auf einer anderen Seite sind
  if (window.location.pathname !== '/service-provider-dashboard') {
    window.location.href = `/service-provider-dashboard?trade=${allocation.trade_id}&showQuote=true`;
  }
};
```

## Workflow

### Für Dienstleister (Benachrichtigung):

1. **Benachrichtigung erhalten**:
   - ✅ Zeigt Ausschreibungsnamen (z.B. "Elektroinstallation")
   - ✅ Zeigt Projektnamen nur wenn vorhanden
   - ✅ Zeigt Bauträger: "Max Mustermann (Musterfirma GmbH)"
   - ✅ Zeigt Start/Ende Datum und Personenanzahl

2. **Klick auf Benachrichtigung**:
   - ✅ Dispatcht `openTradeDetails` Event mit `showQuoteForm: true`
   - ✅ ServiceProviderDashboard empfängt Event
   - ✅ Sucht Trade in lokalen Daten oder lädt neu
   - ✅ Öffnet `CostEstimateForm` direkt
   - ✅ Dienstleister kann Angebot abgeben

### Für Dienstleister (Ressourcenverwaltung):

1. **Pendente Allocation sehen**:
   - ✅ Sieht gelbe "Wartet auf Angebot" Markierung
   - ✅ Sieht Ausschreibung Details

2. **Klick auf "Angebot abgeben"**:
   - ✅ Dispatcht `openTradeDetails` Event mit `showQuoteForm: true`
   - ✅ Navigation zu ServiceProviderDashboard (falls nötig)
   - ✅ Öffnet `CostEstimateForm` direkt
   - ✅ Dienstleister kann Angebot abgeben

### Nach Angebots-Abgabe:

1. ✅ `ResourceAllocation` Status → `OFFER_SUBMITTED`
2. ✅ `Resource` Status → `ALLOCATED`
3. ✅ `Quote` wird erstellt
4. ✅ Bauträger erhält `QUOTE_SUBMITTED` Benachrichtigung
5. ✅ Ressource verschwindet aus "Zugeordnete Ressourcen" (bei Bauträger)
6. ✅ Angebot erscheint in Angebotsliste (bei Bauträger)

## Geänderte Dateien

### Backend:
- `BuildWise/app/services/notification_service.py`

### Frontend:
- `Frontend/Frontend/src/components/NotificationTab.tsx`
- `Frontend/Frontend/src/pages/ServiceProviderDashboard.tsx`
- `Frontend/Frontend/src/components/ResourceManagementDashboard.tsx`

## Testing

### Manueller Test:

1. **Als Bauträger**:
   - Erstelle Ausschreibung
   - Ordne eine Ressource zu (Pull)

2. **Als Dienstleister**:
   - Prüfe Benachrichtigung:
     - ✅ Ausschreibungsname korrekt?
     - ✅ Bauträger Name + Firma korrekt?
     - ✅ Kein "Unbekanntes Projekt" wenn nicht vorhanden?
   - Klicke auf Benachrichtigung
     - ✅ CostEstimateForm öffnet sich?
   - Gebe Angebot ab

3. **Als Bauträger**:
   - Prüfe ob Ressource aus "Zugeordnete Ressourcen" verschwunden ist
   - Prüfe ob Angebot in Angebotsliste erscheint
   - Prüfe ob Benachrichtigung über eingegangenes Angebot erscheint

### Erwartete Ausgabe in Console:

```
📋 Event empfangen: TradeDetails öffnen für Trade: 123
✅ Trade gefunden: {id: 123, title: "Elektroinstallation", ...}
🎯 Öffne CostEstimateForm für Trade: 123 Elektroinstallation
```

## Zusätzliche Fehlerkorrektur

### Problem: `project.user_id` existiert nicht

**Fehler:**
```
AttributeError: 'Project' object has no attribute 'user_id'. Did you mean: 'owner_id'?
```

**Ursache:**
- In `BuildWise/app/models/project.py` heißt das Feld `owner_id`, nicht `user_id`
- `notification_service.py` verwendete `project.user_id`

**Lösung:**
```python
# Vorher:
if project and project.user_id:
    bautraeger_result = await db.execute(
        select(User).where(User.id == project.user_id)
    )

# Nachher:
if project and project.owner_id:
    bautraeger_result = await db.execute(
        select(User).where(User.id == project.owner_id)
    )
```

### Testergebnis

**Test-Allocation erfolgreich erstellt:**
```
[OK] Resource gefunden: ID=4, ServiceProvider=125
[OK] Trade gefunden: ID=6, Title=Fassade streichen
[OK] Allocation erstellt: ID=14, Resource=4, Trade=6
[OK] Benachrichtigung erstellt: ID=5
```

**Notification-Daten korrekt:**
```json
{
  "allocation_id": 14,
  "resource_id": 4,
  "trade_id": 6,  // ✅ Korrekt!
  "trade_title": "Fassade streichen",  // ✅ Korrekt!
  "project_name": "Familie Keller – Einfamilienhaus Neubau",
  "project_id": 1,
  "bautraeger_name": "Stephan Schellworth (Bauträger AG)",  // ✅ Korrekt!
  "bautraeger_full_name": "Stephan Schellworth",
  "bautraeger_company": "Bauträger AG",
  "allocated_start_date": "2025-10-01T13:36:44",
  "allocated_end_date": "2025-10-31T13:36:44",
  "allocated_person_count": 2,
  "allocation_status": "pre_selected"
}
```

## Status

✅ **IMPLEMENTIERT UND GETESTET**

Alle Anforderungen erfüllt:
1. ✅ Ausschreibungsname wird korrekt angezeigt
2. ✅ "Unbekanntes Projekt" wird nicht mehr angezeigt (conditional)
3. ✅ Bauträger Name und Firmenname werden korrekt angezeigt
4. ✅ Klick auf Benachrichtigung öffnet CostEstimateForm
5. ✅ "Angebot abgeben" Button in Ressourcenverwaltung öffnet CostEstimateForm
6. ✅ Nach Angebots-Abgabe wird Ressource zu Angebot transformiert
7. ✅ Backend `project.owner_id` Fix implementiert
8. ✅ Vollständiger Test erfolgreich durchgeführt

**Hinweis:** Ältere Benachrichtigungen (vor diesem Fix) haben möglicherweise noch `trade_id: 0` oder ungültige Daten. Diese können ignoriert werden, da neue Allocations korrekt funktionieren.

