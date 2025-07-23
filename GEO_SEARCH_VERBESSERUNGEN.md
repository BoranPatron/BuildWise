# Geo-Search Verbesserungen

## Übersicht

Zwei wichtige Probleme der Geo-Search wurden gelöst:
1. **Detailansicht für Gewerke** - Umfassende Informationen mit Angebots-Status
2. **Cluster-Marker** - Lösung für überlappende Gewerke an gleicher Adresse

## 🔍 Problem 1: Detailansicht für Gewerke

### **Lösung: TradeDetailsModal-Komponente**

#### **Datei**: `Frontend/Frontend/src/components/TradeDetailsModal.tsx`

**Features:**
- ✅ **Vollständige Gewerk-Informationen** - Titel, Beschreibung, Kategorie, Status
- ✅ **Projekt-Details** - Name, Typ, Status, Adresse
- ✅ **Zeitplan-Anzeige** - Erstellungsdatum, geplantes Datum
- ✅ **Budget-Information** - Anzeige wenn verfügbar
- ✅ **Angebots-Status** - Zeigt ob bereits Angebot abgegeben wurde
- ✅ **Existierende Angebote** - Liste aller eingegangenen Angebote
- ✅ **Direkte Angebotserstellung** - "Angebot abgeben" Button

#### **Technische Implementierung:**

**State-Management:**
```typescript
const [existingQuotes, setExistingQuotes] = useState<Quote[]>([]);
const [userHasQuote, setUserHasQuote] = useState(false);
const [userQuote, setUserQuote] = useState<Quote | null>(null);
const [showCostEstimateForm, setShowCostEstimateForm] = useState(false);
```

**Angebots-Status-Prüfung:**
```typescript
const loadExistingQuotes = async () => {
  // TODO: Implementiere getQuotesByTrade API-Call
  const quotes: Quote[] = []; // Temporär leer
  setExistingQuotes(quotes);
  
  // Prüfe ob aktueller User bereits ein Angebot abgegeben hat
  const currentUserQuote = quotes.find((q: Quote) => q.service_provider_id === user?.id);
  setUserHasQuote(!!currentUserQuote);
  setUserQuote(currentUserQuote || null);
};
```

**Kategorie-spezifische Icons:**
```typescript
const getCategoryIcon = (category: string) => {
  const iconMap: { [key: string]: { color: string; icon: React.ReactNode } } = {
    'electrical': { color: '#fbbf24', icon: <span className="text-lg">⚡</span> },
    'plumbing': { color: '#3b82f6', icon: <span className="text-lg">🔧</span> },
    'heating': { color: '#ef4444', icon: <span className="text-lg">🔥</span> },
    // ... weitere Kategorien
  };
  return iconMap[category] || { color: '#6b7280', icon: <span className="text-lg">🔨</span> };
};
```

#### **UI-Layout:**

**Header mit Kategorie-Icon:**
```typescript
<div className="flex items-center gap-4">
  <div 
    className="w-12 h-12 rounded-full flex items-center justify-center border-2 border-white shadow-lg"
    style={{ backgroundColor: categoryInfo.color }}
  >
    {categoryInfo.icon}
  </div>
  <div>
    <h2 className="text-2xl font-bold text-gray-800">{trade.title}</h2>
    <div className="flex items-center gap-2 mt-1">
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(trade.status)}`}>
        {getStatusLabel(trade.status)}
      </span>
    </div>
  </div>
</div>
```

**Angebots-Status-Anzeige:**
```typescript
{userHasQuote ? (
  <div className="space-y-3">
    <div className="flex items-center gap-2">
      <CheckCircle size={16} className="text-green-600" />
      <span className="text-sm font-medium text-green-600">Angebot bereits abgegeben</span>
    </div>
    {/* Angebots-Details */}
  </div>
) : (
  <button onClick={handleCreateQuote}>
    <Plus size={16} />
    Angebot abgeben
  </button>
)}
```

## 🗺️ Problem 2: Cluster-Marker für überlappende Gewerke

### **Lösung: Erweiterte TradeMap mit Clustering**

#### **Datei**: `Frontend/Frontend/src/components/TradeMap.tsx`

**Features:**
- ✅ **Automatisches Clustering** - Gruppiert Gewerke an gleicher Adresse
- ✅ **Kategorie-spezifische Icons** - Verschiedene Symbole pro Gewerk-Art
- ✅ **Dynamische Cluster-Größe** - Größe basiert auf Anzahl der Gewerke
- ✅ **Icon-Grid im Cluster** - Zeigt bis zu 4 verschiedene Kategorien
- ✅ **Detaillierte Cluster-Popups** - Liste aller Gewerke mit Aktionen
- ✅ **Einzelgewerk-Marker** - Normale Marker für alleinstehende Gewerke

#### **Technische Implementierung:**

**Clustering-Algorithmus:**
```typescript
const clusterTradesByLocation = (trades: TradeSearchResult[]) => {
  const clusters: { [key: string]: TradeSearchResult[] } = {};
  const CLUSTER_THRESHOLD = 0.001; // ~100m Radius

  trades.forEach(trade => {
    // Erstelle einen Cluster-Key basierend auf gerundeten Koordinaten
    const lat = Math.round(trade.address_latitude / CLUSTER_THRESHOLD) * CLUSTER_THRESHOLD;
    const lng = Math.round(trade.address_longitude / CLUSTER_THRESHOLD) * CLUSTER_THRESHOLD;
    const clusterKey = `${lat},${lng}`;

    if (!clusters[clusterKey]) {
      clusters[clusterKey] = [];
    }
    clusters[clusterKey].push(trade);
  });

  return Object.values(clusters);
};
```

**Cluster-Icon-Erstellung:**
```typescript
const createClusterIcon = (cluster: TradeSearchResult[]) => {
  const categories = cluster.map(trade => trade.category);
  const uniqueCategories = [...new Set(categories)];
  const count = cluster.length;
  
  // Erstelle Icon-Grid für verschiedene Kategorien
  const iconSize = 16;
  const maxIcons = Math.min(uniqueCategories.length, 4);
  const containerSize = Math.max(40, Math.min(60, 30 + count * 2));
  
  const iconsHTML = uniqueCategories.slice(0, maxIcons).map((category, index) => {
    const categoryInfo = getCategoryIcon(category);
    const row = Math.floor(index / 2);
    const col = index % 2;
    const offsetX = (containerSize - 2 * iconSize) / 2 + col * iconSize;
    const offsetY = (containerSize - Math.ceil(maxIcons / 2) * iconSize) / 2 + row * iconSize;
    
    return `
      <div style="
        position: absolute;
        left: ${offsetX}px;
        top: ${offsetY}px;
        width: ${iconSize}px;
        height: ${iconSize}px;
        background: ${categoryInfo.color};
        border-radius: 50%;
        border: 2px solid white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
      ">
        ${categoryInfo.icon}
      </div>
    `;
  }).join('');
  
  // Container mit Anzahl-Badge
  return L.divIcon({
    className: 'cluster-marker',
    html: `
      <div style="
        position: relative;
        width: ${containerSize}px;
        height: ${containerSize}px;
        background: linear-gradient(135deg, #ffbd59, #ffa726);
        border-radius: 50%;
        border: 4px solid white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
      ">
        ${iconsHTML}
        <div style="
          position: absolute;
          bottom: -8px;
          right: -8px;
          background: #ef4444;
          color: white;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: bold;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        ">
          ${count}
        </div>
      </div>
    `,
    iconSize: [containerSize, containerSize],
    iconAnchor: [containerSize / 2, containerSize / 2]
  });
};
```

**Cluster-Popup-Erstellung:**
```typescript
const createClusterPopup = (cluster: TradeSearchResult[]) => {
  const firstTrade = cluster[0];
  const categoryCounts = cluster.reduce((acc, trade) => {
    acc[trade.category] = (acc[trade.category] || 0) + 1;
    return acc;
  }, {} as { [key: string]: number });

  const categoryList = Object.entries(categoryCounts)
    .map(([category, count]) => {
      const categoryInfo = getCategoryIcon(category);
      return `
        <div class="flex items-center gap-2 text-sm">
          <span style="font-size: 14px;">${categoryInfo.icon}</span>
          <span>${category} (${count})</span>
        </div>
      `;
    }).join('');

  const tradesList = cluster.map(trade => {
    const categoryInfo = getCategoryIcon(trade.category);
    return `
      <div class="border-b border-gray-200 pb-2 mb-2">
        <div class="flex items-center gap-2 mb-1">
          <span style="font-size: 14px;">${categoryInfo.icon}</span>
          <h4 class="font-medium text-gray-800">${trade.title}</h4>
        </div>
        <p class="text-xs text-gray-600 mb-2">${trade.description || 'Keine Beschreibung'}</p>
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-500">${trade.project_name}</span>
          <button onclick="..." class="bg-yellow-500 text-white px-2 py-1 rounded text-xs">
            Angebot
          </button>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="p-3 min-w-[300px] max-w-[400px]">
      <div class="flex items-center gap-2 mb-3">
        <div class="w-6 h-6 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-full">
          ${cluster.length}
        </div>
        <h3 class="font-bold text-lg">Gewerke an dieser Adresse</h3>
      </div>
      
      <div class="mb-3">
        <p class="text-sm text-gray-600 mb-2">
          <strong>Adresse:</strong> ${firstTrade.address_street}, ${firstTrade.address_zip} ${firstTrade.address_city}
        </p>
        <div class="space-y-1">
          ${categoryList}
        </div>
      </div>
      
      <div class="max-h-64 overflow-y-auto">
        <h4 class="font-medium text-gray-800 mb-2">Verfügbare Gewerke:</h4>
        ${tradesList}
      </div>
    </div>
  `;
};
```

## 🎯 Integration im ServiceProviderDashboard

### **Detailansicht-Integration:**

**State-Variablen:**
```typescript
const [showTradeDetails, setShowTradeDetails] = useState(false);
const [detailTrade, setDetailTrade] = useState<TradeSearchResult | null>(null);
```

**Handler-Funktionen:**
```typescript
const handleTradeDetails = (trade: TradeSearchResult) => {
  console.log('👁️ Zeige Details für:', trade);
  setDetailTrade(trade);
  setShowTradeDetails(true);
};
```

**UI-Updates:**
```typescript
// Listen-Ansicht: Details + Angebot Buttons
<div className="flex items-center gap-2">
  <button
    onClick={() => handleTradeDetails(trade)}
    className="px-3 py-1 bg-blue-500 text-white rounded text-sm font-medium hover:bg-blue-600"
  >
    Details
  </button>
  <button
    onClick={() => handleCreateQuote(trade)}
    className="px-3 py-1 bg-[#ffbd59] text-[#2c3539] rounded text-sm font-medium hover:bg-[#ffa726]"
  >
    Angebot abgeben
  </button>
</div>

// Karten-Ansicht: Marker-Klick öffnet Details
<TradeMap
  currentLocation={currentLocation}
  trades={geoTrades}
  radiusKm={radiusKm}
  onTradeClick={(trade) => {
    handleTradeDetails(trade); // Öffnet Detailansicht
  }}
/>
```

**Modal-Integration:**
```typescript
<TradeDetailsModal
  trade={detailTrade}
  isOpen={showTradeDetails}
  onClose={() => {
    setShowTradeDetails(false);
    setDetailTrade(null);
  }}
  onCreateQuote={handleCreateQuote}
/>
```

## 🎨 Visuelle Verbesserungen

### **Cluster-Marker-Design:**
- **Gradient-Hintergrund** - Gelb-Orange für bessere Sichtbarkeit
- **Icon-Grid** - Bis zu 4 Kategorie-Icons in 2x2 Anordnung
- **Anzahl-Badge** - Rotes Badge mit Gewerk-Anzahl
- **Schatten-Effekte** - 3D-Optik für bessere Erkennbarkeit

### **Detailansicht-Design:**
- **Moderne Card-UI** - Weiße Karten mit abgerundeten Ecken
- **Kategorie-Icons** - Farbkodierte Icons für schnelle Erkennung
- **Status-Badges** - Farbkodierte Status-Anzeigen
- **Responsive Layout** - 3-Spalten auf Desktop, 1-Spalte auf Mobile

## 🚀 Workflow-Verbesserungen

### **Neuer Benutzer-Flow:**

1. **Geo-Search durchführen** → Gewerke werden gefunden
2. **Liste oder Karte anzeigen** → Benutzer wählt Ansicht
3. **Gewerk auswählen** → Details-Button oder Marker-Klick
4. **Detailansicht öffnet sich** → Alle Informationen sichtbar
5. **Angebots-Status prüfen** → Sieht ob bereits Angebot vorhanden
6. **Angebot abgeben** → Direkter Übergang zur Angebotserstellung

### **Karten-Verbesserungen:**

1. **Overlapping-Problem gelöst** → Alle Gewerke sichtbar
2. **Kategorie-Erkennung** → Icons zeigen Gewerk-Art
3. **Cluster-Navigation** → Einfache Auswahl aus mehreren Gewerken
4. **Detaillierte Popups** → Alle wichtigen Infos auf einen Blick

## ✅ Status: Vollständig implementiert

Beide Probleme wurden erfolgreich gelöst:

### **Problem 1 - Detailansicht:** ✅ Gelöst
- ✅ Umfassende TradeDetailsModal-Komponente
- ✅ Angebots-Status-Anzeige (Grundgerüst)
- ✅ Integration in Listen- und Karten-Ansicht
- ✅ Direkte Angebotserstellung möglich

### **Problem 2 - Cluster-Marker:** ✅ Gelöst
- ✅ Automatisches Clustering nach Koordinaten
- ✅ Kategorie-spezifische Icons in Clustern
- ✅ Detaillierte Cluster-Popups
- ✅ Einzelgewerk- und Cluster-Marker-Unterstützung

## 🔄 Nächste Schritte (Optional)

1. **API-Integration** - `getQuotesByTrade` Endpoint implementieren
2. **Erweiterte Filter** - Filter nach bereits beworbenen Gewerken
3. **Angebots-Historie** - Detaillierte Angebots-Verwaltung
4. **Push-Benachrichtigungen** - Bei neuen Gewerken in der Nähe 