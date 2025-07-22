# 🎛️ BuildWise Environment Manager - Elegante Beta/Production Umschaltung

## Übersicht

Das **BuildWise Environment Manager System** bietet eine elegante und robuste Lösung zum Umschalten zwischen Beta- und Production-Modus **ohne die `.env` Datei zu überschreiben**. Dies schützt die Microsoft OAuth Credentials und andere wichtige Konfigurationen.

## 🎯 Problem-Lösung

### **Vorheriges Problem:**
- `.env` Datei wurde komplett überschrieben
- Microsoft OAuth Credentials gingen verloren
- Keine nachhaltige Lösung für Modus-Umschaltung

### **Neue Lösung:**
- Separate `environment_config.json` Datei
- `.env` Datei bleibt unverändert
- Elegante Umschaltung zwischen Beta (0%) und Production (4.7%)

## 🏗️ Architektur

### **Datei-Struktur:**
```
BuildWise/
├── .env                          # Unverändert (OAuth Credentials)
├── environment_config.json        # Modus-Konfiguration
├── environment_manager.py         # Management-Tool
├── app/core/config.py            # Erweiterte Settings-Klasse
└── test_environment_manager.py   # Test-Suite
```

### **Konfigurations-Flow:**
1. **Settings-Klasse** lädt `.env` (OAuth Credentials)
2. **Settings-Klasse** lädt `environment_config.json` (Modus)
3. **Gebühren-Berechnung** basiert auf aktuellem Modus
4. **BuildWiseFeeService** verwendet `settings.get_fee_percentage()`

## 🔧 Verwendung

### **1. Aktuellen Status anzeigen:**
```bash
python environment_manager.py --status
```

### **2. Zu Beta-Modus wechseln (0% Gebühr):**
```bash
python environment_manager.py --mode beta
```

### **3. Zu Production-Modus wechseln (4.7% Gebühr):**
```bash
python environment_manager.py --mode production
```

### **4. Detaillierte Informationen:**
```bash
python environment_manager.py --info
```

### **5. Konfiguration validieren:**
```bash
python environment_manager.py --validate
```

### **6. Zurücksetzen auf Standard:**
```bash
python environment_manager.py --reset
```

## 📊 Modus-Konfiguration

### **Beta-Modus:**
```json
{
  "environment_mode": "beta",
  "buildwise_fee_percentage": 0.0,
  "buildwise_fee_phase": "beta",
  "buildwise_fee_enabled": true
}
```
- **Gebühren:** 0.0%
- **Zweck:** Beta-Test-Phase
- **Features:** Kostenlos für Beta-Tester

### **Production-Modus:**
```json
{
  "environment_mode": "production",
  "buildwise_fee_percentage": 4.7,
  "buildwise_fee_phase": "production",
  "buildwise_fee_enabled": true
}
```
- **Gebühren:** 4.7%
- **Zweck:** Live-Betrieb
- **Features:** Vollständige Gebühren-Erhebung

## 🔄 Technische Implementierung

### **Settings-Klasse Erweiterung:**
```python
class Settings(BaseSettings):
    # Environment Mode
    environment_mode: Literal["beta", "production"] = "beta"
    
    # BuildWise Fee Configuration
    buildwise_fee_percentage: float = 0.0
    buildwise_fee_phase: Literal["beta", "production"] = "beta"
    buildwise_fee_enabled: bool = True
    
    def get_fee_percentage(self) -> float:
        """Gibt den aktuellen Gebühren-Prozentsatz basierend auf der Phase zurück."""
        if self.environment_mode == "beta":
            return 0.0
        elif self.environment_mode == "production":
            return 4.7
        return self.buildwise_fee_percentage
```

### **BuildWiseFeeService Integration:**
```python
async def create_fee_from_quote(
    db: AsyncSession, 
    quote_id: int, 
    cost_position_id: int, 
    fee_percentage: Optional[float] = None
) -> BuildWiseFee:
    # Verwende den aktuellen Gebühren-Prozentsatz aus der Konfiguration
    if fee_percentage is None:
        fee_percentage = settings.get_fee_percentage()
    
    # Berechne die Gebühr
    quote_amount = float(quote.total_amount)
    fee_amount = quote_amount * (fee_percentage / 100.0)
```

## 🧪 Testing

### **Umfassender Test:**
```bash
python test_environment_manager.py
```

### **Test-Bereiche:**
- ✅ **Konfigurations-Loading:** Settings-Klasse lädt korrekt
- ✅ **Gebühren-Berechnung:** Korrekte Prozentsätze je Modus
- ✅ **Environment-Umschaltung:** Modus-Wechsel funktioniert
- ✅ **Konfigurationsdatei-Integration:** JSON-Datei wird korrekt gelesen
- ✅ **Service-Integration:** BuildWiseFeeService verwendet neue Konfiguration

## 🚀 Deployment-Workflow

### **1. Beta-Phase (Entwicklung):**
```bash
# Setze auf Beta-Modus
python environment_manager.py --mode beta

# Starte Backend
python -m uvicorn app.main:app --reload

# Teste ohne Gebühren
# Alle BuildWise Fees haben 0% Gebühr
```

### **2. Production-Phase (Go-Live):**
```bash
# Setze auf Production-Modus
python environment_manager.py --mode production

# Starte Backend neu
python -m uvicorn app.main:app --reload

# Alle neuen BuildWise Fees haben 4.7% Gebühr
```

### **3. Zurück zu Beta (falls nötig):**
```bash
# Setze zurück auf Beta-Modus
python environment_manager.py --mode beta

# Starte Backend neu
python -m uvicorn app.main:app --reload
```

## 🔒 Sicherheit & Best Practices

### **Schutz der OAuth Credentials:**
- ✅ `.env` Datei wird nie überschrieben
- ✅ Microsoft OAuth Credentials bleiben erhalten
- ✅ Separate Konfiguration für Modus-Umschaltung

### **Robustheit:**
- ✅ Validierung der Konfigurationsdatei
- ✅ Fallback auf Standard-Werte
- ✅ Fehlerbehandlung bei fehlender Datei

### **Nachhaltigkeit:**
- ✅ Keine manuellen `.env` Änderungen nötig
- ✅ Einfache Kommandozeilen-Schnittstelle
- ✅ Vollständige Dokumentation

## 📈 Vorteile

### **1. Elegante Lösung:**
- Keine `.env` Überschreibung
- Separate Konfigurationsdatei
- Einfache Kommandozeilen-Schnittstelle

### **2. Robustheit:**
- OAuth Credentials bleiben geschützt
- Validierung der Konfiguration
- Fehlerbehandlung

### **3. Flexibilität:**
- Schnelle Modus-Umschaltung
- Keine Server-Neustarts für Konfiguration
- Einfache Rollback-Möglichkeit

### **4. Nachhaltigkeit:**
- Best Practice-konform
- Vollständig dokumentiert
- Umfassend getestet

## 🎉 Ergebnis

**Das BuildWise Environment Manager System ist vollständig implementiert und funktionsfähig!**

- ✅ **Elegante Umschaltung** zwischen Beta und Production
- ✅ **Schutz der OAuth Credentials** durch separate Konfiguration
- ✅ **Robuste Implementierung** mit Validierung und Fehlerbehandlung
- ✅ **Umfassende Tests** bestätigen Funktionalität
- ✅ **Best Practice-konform** und nachhaltig

**Nächste Schritte:**
1. Verwenden Sie `python environment_manager.py --mode beta` für Beta-Phase
2. Verwenden Sie `python environment_manager.py --mode production` für Go-Live
3. Starten Sie den Backend-Server neu nach Modus-Wechsel

---

**Erstellt:** 22. Juli 2025  
**Status:** ✅ Vollständig implementiert und getestet  
**Nächster Schritt:** Production-Deployment vorbereiten 