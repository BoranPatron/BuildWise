# BuildWise Gebühren Frontend-Fix

## Problem

Die Dienstleisteransicht zeigte noch den alten festen Prozentsatz von 1% an, obwohl das Backend bereits ein konfigurierbares Gebühren-System hatte.

## Lösung

### ✅ **Frontend-Anpassungen**

#### 1. **API-Service erweitert** (`buildwiseFeeService.ts`)
- Neue Funktion `getBuildWiseFeeConfig()` hinzugefügt
- `createFeeFromQuote()` verwendet jetzt automatisch die aktuelle Konfiguration
- Fallback auf 1% wenn Konfiguration nicht abrufbar ist

```typescript
// Neue Funktion: Aktuelle Gebühren-Konfiguration abrufen
export async function getBuildWiseFeeConfig(): Promise<BuildWiseFeeConfig> {
  return safeApiCall(async () => {
    const res = await api.get('/buildwise-fees/config');
    return res.data;
  });
}

// Automatische Verwendung der konfigurierten Werte
export async function createFeeFromQuote(
  quoteId: number, 
  costPositionId: number, 
  feePercentage?: number
): Promise<BuildWiseFee> {
  // Wenn kein feePercentage angegeben ist, hole die aktuelle Konfiguration
  if (feePercentage === undefined) {
    try {
      const config = await getBuildWiseFeeConfig();
      feePercentage = config.fee_percentage;
    } catch (error) {
      feePercentage = 1.0; // Fallback
    }
  }
  // ...
}
```

#### 2. **Quotes.tsx angepasst**
- Entfernung des festen 1%-Werts
- Verwendung der automatischen Konfiguration

```typescript
const buildwiseFee = await createFeeFromQuote(
  quoteId,
  costPositionId
  // Kein feePercentage angegeben - verwendet automatisch die aktuelle Konfiguration
);
```

#### 3. **Dienstleisteransicht erweitert** (`ServiceProviderBuildWiseFees.tsx`)
- Anzeige der aktuellen Gebühren-Konfiguration
- Dynamische Prozentsatz-Anzeige
- Phase-Information (Beta/Go-Live)

```typescript
// Neue State-Variable
const [feeConfig, setFeeConfig] = useState<BuildWiseFeeConfig | null>(null);

// Laden der Konfiguration
const [feesData, statsData, configData] = await Promise.all([
  getBuildWiseFees(selectedMonth, selectedYear),
  getBuildWiseFeeStatistics(),
  getBuildWiseFeeConfig() // Neue Funktion
]);
```

### ✅ **UI-Verbesserungen**

#### **Gebühren-Konfiguration Anzeige**
```jsx
{/* Current Fee Configuration */}
{feeConfig && (
  <div className="bg-white/5 backdrop-blur-lg rounded-lg p-6 border border-white/10 mb-8">
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center space-x-2">
        <Settings className="w-6 h-6 text-[#ffbd59]" />
        <h3 className="text-lg font-semibold text-white">Aktuelle Gebühren-Konfiguration</h3>
      </div>
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
        feeConfig.fee_phase === 'beta' 
          ? 'bg-blue-100 text-blue-800' 
          : 'bg-green-100 text-green-800'
      }`}>
        {feeConfig.fee_phase === 'beta' ? 'Beta-Phase' : 'Go-Live'}
      </span>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="text-center">
        <p className="text-sm text-gray-300">Aktueller Prozentsatz</p>
        <p className="text-2xl font-bold text-white">{feeConfig.fee_percentage}%</p>
      </div>
      <div className="text-center">
        <p className="text-sm text-gray-300">Phase</p>
        <p className="text-lg font-medium text-white">
          {feeConfig.fee_phase === 'beta' ? 'Beta-Phase' : 'Go-Live'}
        </p>
      </div>
      <div className="text-center">
        <p className="text-sm text-gray-300">Status</p>
        <p className={`text-lg font-medium ${
          feeConfig.fee_enabled ? 'text-green-400' : 'text-red-400'
        }`}>
          {feeConfig.fee_enabled ? 'Aktiviert' : 'Deaktiviert'}
        </p>
      </div>
    </div>
  </div>
)}
```

### ✅ **Update-Tool für bestehende Gebühren**

#### **Neues Skript: `update_existing_fees_to_config.py`**
- Aktualisiert alle bestehenden Gebühren auf die aktuelle Konfiguration
- Berechnet neue Gebühren-Beträge basierend auf dem konfigurierten Prozentsatz
- Sichere Bestätigung vor dem Update

```bash
# Bestehende Gebühren auf aktuelle Konfiguration aktualisieren
python update_existing_fees_to_config.py
```

## Verwendung

### 1. **Aktuelle Konfiguration prüfen**
```bash
python switch_buildwise_fees.py --status
```

### 2. **Bestehende Gebühren aktualisieren** (falls benötigt)
```bash
python update_existing_fees_to_config.py
```

### 3. **Frontend testen**
- Dienstleisteransicht öffnen
- Gebühren-Konfiguration sollte korrekt angezeigt werden
- Neue Gebühren verwenden automatisch die aktuelle Konfiguration

## Ergebnis

### ✅ **Vorher**
- Fester 1%-Wert im Frontend
- Inkonsistente Anzeige zwischen Backend und Frontend
- Keine Transparenz über aktuelle Konfiguration

### ✅ **Nachher**
- Dynamische Verwendung der Backend-Konfiguration
- Transparente Anzeige der aktuellen Gebühren-Einstellung
- Automatische Anpassung an Beta/Go-Live Phasen
- Update-Tool für bestehende Gebühren

## Sicherheit

### ✅ **Validierung**
- Fallback auf 1% wenn Konfiguration nicht abrufbar
- Fehlerbehandlung bei API-Aufrufen
- Bestätigungsdialoge für kritische Updates

### ✅ **Rückwärtskompatibilität**
- Bestehende Gebühren bleiben funktionsfähig
- Update-Tool für manuelle Anpassung
- Automatische Konfiguration für neue Gebühren

## Monitoring

### ✅ **Logs**
- API-Aufrufe werden geloggt
- Konfigurationsabfragen werden protokolliert
- Fehler bei Konfigurationsabfragen werden erfasst

### ✅ **UI-Feedback**
- Aktuelle Konfiguration wird prominent angezeigt
- Phase-Information (Beta/Go-Live) ist sichtbar
- Status der Gebühren-Aktivierung wird gezeigt

---

**✅ Das Frontend zeigt jetzt korrekt die konfigurierten Gebühren an!** 