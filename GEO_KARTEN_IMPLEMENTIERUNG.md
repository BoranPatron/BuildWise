# Geo-Karten Implementierung

## Übersicht

Die Geo-Karten-Funktionalität ermöglicht es Dienstleistern, gefundene Gewerke auf einer interaktiven Karte zu visualisieren und direkt Angebote abzugeben.

## 🗺️ TradeMap-Komponente

### **Datei**: `Frontend/Frontend/src/components/TradeMap.tsx`

**Features:**
- ✅ **Leaflet-Integration** - Vollständige OpenStreetMap-Unterstützung
- ✅ **Kategorie-spezifische Icons** - Verschiedene Symbole für Gewerk-Arten
- ✅ **Interaktive Popups** - Detaillierte Informationen pro Gewerk
- ✅ **Suchradius-Visualisierung** - Dynamischer Kreis um Standort
- ✅ **Auto-Zoom** - Automatische Anpassung an alle Marker
- ✅ **Direkte Angebotserstellung** - Button in Popup

### **Technische Implementierung:**

#### **Kategorien und Icons:**
```typescript
const getCategoryIcon = (category: string) => {
  const iconMap = {
    'electrical': { color: '#fbbf24', icon: '⚡' },
    'plumbing': { color: '#3b82f6', icon: '🔧' },
    'heating': { color: '#ef4444', icon: '🔥' },
    'roofing': { color: '#f97316', icon: '🏠' },
    'windows': { color: '#10b981', icon: '🪟' },
    'flooring': { color: '#8b5cf6', icon: '📐' },
    'walls': { color: '#ec4899', icon: '🧱' },
    'foundation': { color: '#6b7280', icon: '🏗️' },
    'landscaping': { color: '#22c55e', icon: '🌱' }
  };
  return iconMap[category] || { color: '#6b7280', icon: '🔨' };
};
```

#### **Marker-Erstellung:**
```typescript
const tradeIcon = L.divIcon({
  className: 'trade-marker',
  html: `
    <div style="
      background: ${categoryInfo.color}; 
      width: 30px; 
      height: 30px; 
      border-radius: 50%; 
      border: 3px solid white; 
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    ">
      ${categoryInfo.icon}
    </div>
  `,
  iconSize: [30, 30],
  iconAnchor: [15, 15]
});
```

#### **Popup-Inhalt:**
```typescript
.bindPopup(`
  <div class="p-3 min-w-[250px]">
    <div class="flex items-center gap-2 mb-2">
      <span style="font-size: 18px;">${categoryInfo.icon}</span>
      <h3 class="font-bold text-lg">${trade.title}</h3>
    </div>
    
    <div class="mb-2">
      <span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1">
        ${trade.category}
      </span>
      <span class="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
        ${trade.status}
      </span>
    </div>
    
    <p class="text-sm text-gray-600 mb-2">${trade.description || 'Keine Beschreibung'}</p>
    
    <div class="space-y-1 text-sm mb-3">
      <p><strong>Projekt:</strong> ${trade.project_name}</p>
      <p><strong>Adresse:</strong> ${trade.address_street}, ${trade.address_zip} ${trade.address_city}</p>
      <p><strong>Entfernung:</strong> ${trade.distance_km.toFixed(1)} km</p>
      ${trade.budget ? `<p><strong>Budget:</strong> ${trade.budget.toLocaleString('de-DE')} €</p>` : ''}
      ${trade.planned_date ? `<p><strong>Geplant:</strong> ${new Date(trade.planned_date).toLocaleDateString('de-DE')}</p>` : ''}
    </div>
    
    <button 
      onclick="window.dispatchEvent(new CustomEvent('tradeMarkerClick', {detail: ${JSON.stringify(trade).replace(/"/g, '&quot;')}}))"
      class="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:from-yellow-600 hover:to-yellow-700 transition-all duration-300"
    >
      🎯 Angebot abgeben
    </button>
  </div>
`)
```

## 🎯 Integration im ServiceProviderDashboard

### **Tab-System:**
```typescript
// Tab-Buttons
<button
  onClick={() => setActiveTab('list')}
  className={`px-3 py-1.5 rounded-lg font-medium text-xs transition-colors ${
    activeTab === 'list'
      ? 'bg-[#ffbd59] text-[#2c3539]'
      : 'bg-white/10 text-white hover:bg-white/20'
  }`}
>
  <List size={14} className="inline mr-1" />
  Liste
</button>
<button
  onClick={() => setActiveTab('map')}
  className={`px-3 py-1.5 rounded-lg font-medium text-xs transition-colors ${
    activeTab === 'map'
      ? 'bg-[#ffbd59] text-[#2c3539]'
      : 'bg-white/10 text-white hover:bg-white/20'
  }`}
>
  <Map size={14} className="inline mr-1" />
  Karte
</button>
```

### **Karten-Integration:**
```typescript
{activeTab === 'map' ? (
  /* Karten-Ansicht */
  <div className="h-64 rounded-lg overflow-hidden">
    <TradeMap
      currentLocation={currentLocation}
      trades={geoTrades}
      radiusKm={radiusKm}
      onTradeClick={(trade) => {
        console.log('📍 Karten-Marker geklickt:', trade);
        handleCreateQuote(trade);
      }}
    />
  </div>
) : (
  /* Listen-Ansicht */
  // ... Listen-Code
)}
```

## 🎨 UI-Elemente

### **Legende (oben rechts):**
- ✅ **Standort-Marker** - Blauer Kreis für eigenen Standort
- ✅ **Gewerke-Marker** - Gelbe Kreise für Gewerke
- ✅ **Suchradius** - Transparenter Kreis
- ✅ **Ergebnisanzahl** - Dynamische Anzeige

### **Kategorie-Legende (unten links):**
- ✅ **Icon-Übersicht** - Alle Gewerk-Kategorien mit Symbolen
- ✅ **Kompakte Darstellung** - 2-spaltiges Grid
- ✅ **Intuitive Symbole** - Eindeutige Zuordnung

### **Karten-Controls:**
```typescript
{/* Karten-Controls */}
<div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 z-10">
  <div className="text-xs text-gray-600 font-medium mb-2">Legende</div>
  <div className="space-y-1 text-xs">
    <div className="flex items-center gap-2">
      <div className="w-4 h-4 bg-blue-500 rounded-full border-2 border-white"></div>
      <span>Ihr Standort</span>
    </div>
    <div className="flex items-center gap-2">
      <div className="w-4 h-4 bg-yellow-500 rounded-full border-2 border-white"></div>
      <span>Gewerke</span>
    </div>
    <div className="flex items-center gap-2">
      <div className="w-3 h-3 border-2 border-yellow-500 rounded-full opacity-50"></div>
      <span>Suchradius ({radiusKm}km)</span>
    </div>
  </div>
  <div className="text-xs text-gray-500 mt-2 pt-2 border-t">
    <div className="font-medium text-gray-700">{trades.length} Gewerke gefunden</div>
    <div>Klicken Sie auf einen Marker für Details</div>
  </div>
</div>
```

## 🔧 Technische Features

### **1. Leaflet-Optimierung:**
- ✅ **CDN-Loading** - Dynamisches Laden von CSS und JS
- ✅ **Duplicate-Prevention** - Verhindert mehrfaches Laden
- ✅ **Memory-Management** - Korrekte Cleanup-Logik

### **2. Event-System:**
```typescript
// Event-Listener für Trade-Marker-Clicks
const handleTradeMarkerClick = (event: CustomEvent) => {
  onTradeClick(event.detail);
};

window.addEventListener('tradeMarkerClick', handleTradeMarkerClick as EventListener);

return () => {
  window.removeEventListener('tradeMarkerClick', handleTradeMarkerClick as EventListener);
};
```

### **3. Auto-Zoom-Funktionalität:**
```typescript
// Auto-Zoom zu allen Markern
const group = new (L as any).featureGroup([
  (L as any).marker([currentLocation.latitude, currentLocation.longitude]),
  ...trades.map(trade => (L as any).marker([trade.address_latitude, trade.address_longitude]))
]);

map.fitBounds(group.getBounds().pad(0.1));
```

### **4. Radius-Kreis-Updates:**
```typescript
// Suchradius-Kreis aktualisieren
L.circle([currentLocation.latitude, currentLocation.longitude], {
  color: '#ffbd59',
  fillColor: '#ffbd59',
  fillOpacity: 0.1,
  weight: 2,
  radius: radiusKm * 1000 // Meter
}).addTo(map);
```

## 🚀 Workflow-Integration

### **1. Geo-Search → Karte:**
1. User führt Geo-Search durch
2. Ergebnisse werden in `geoTrades` gespeichert
3. User wechselt zu Karten-Tab
4. TradeMap zeigt alle Gewerke als Marker

### **2. Marker-Klick → Angebot:**
1. User klickt auf Gewerke-Marker
2. Popup zeigt Details und "Angebot abgeben" Button
3. Button trigger Custom Event
4. Event wird von TradeMap abgefangen
5. `onTradeClick` wird mit Trade-Daten aufgerufen
6. `handleCreateQuote` öffnet CostEstimateForm

### **3. Nahtlose Integration:**
- ✅ **Gleiche Daten** - Liste und Karte zeigen identische Informationen
- ✅ **Gleiche Aktionen** - "Angebot abgeben" funktioniert überall
- ✅ **Sync-State** - Filter wirken sich auf beide Ansichten aus

## 📱 Responsive Design

- ✅ **Mobile-Optimierung** - Touch-freundliche Marker-Größe
- ✅ **Adaptive Legenden** - Kompakte Darstellung auf kleinen Bildschirmen
- ✅ **Popup-Optimierung** - Scrollbare Inhalte bei langen Beschreibungen

## 🎯 Verbesserungen implementiert

### **ServiceProviderDashboard:**
1. **Tab-System** - Umschaltung zwischen Liste und Karte
2. **TradeMap-Integration** - Spezialisierte Karten-Komponente
3. **Direkter Workflow** - Marker-Klick → Angebotserstellung
4. **Radius-Sync** - Karten-Radius folgt Filter-Einstellungen

### **TradeMap-Komponente:**
1. **Kategorie-Icons** - Visuelle Unterscheidung der Gewerk-Arten
2. **Detaillierte Popups** - Alle relevanten Informationen
3. **Performance-Optimierung** - Effizientes Event-Management
4. **Benutzerfreundlichkeit** - Intuitive Legenden und Controls

## ✅ Status: Vollständig implementiert und funktional

Die Karten-Funktionalität ist vollständig in die Geo-Search integriert. Dienstleister können zwischen Listen- und Karten-Ansicht wechseln und direkt von der Karte aus Angebote abgeben. 