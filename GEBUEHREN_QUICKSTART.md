# BuildWise Gebühren - Quickstart

## 🚀 Sofortige Verwendung

### 1. Aktuellen Status prüfen
```bash
python switch_buildwise_fees.py --status
```

### 2. Zu Beta-Phase wechseln (0% Gebühr)
```bash
python switch_buildwise_fees.py --phase beta
```

### 3. Zu Go-Live wechseln (4% Gebühr)
```bash
python switch_buildwise_fees.py --phase production
```

### 4. System testen
```bash
python test_fee_configuration.py
```

## 📋 Was wurde implementiert?

### ✅ Konfigurierbare Gebühren
- **Beta-Phase**: 0% Gebühr (kostenlos für Beta-Tester)
- **Go-Live**: 4% Gebühr (kommerzielle Nutzung)
- **Flexibel**: Beliebig zwischen 0% und 100% einstellbar

### ✅ Admin-Tool
- Einfache Kommandozeilen-Umschaltung
- Status-Anzeige und Statistiken
- Bestätigungsdialoge für Sicherheit

### ✅ API-Endpunkte
- `GET /api/v1/buildwise-fees/config` - Konfiguration abrufen
- `PUT /api/v1/buildwise-fees/config` - Konfiguration ändern (Admin only)

### ✅ Service-Integration
- Automatische Verwendung der konfigurierten Werte
- Validierung und Sicherheitsprüfungen
- Rückwärtskompatibilität mit bestehenden Gebühren

## 🔧 Technische Details

### Umgebungsvariablen
```bash
BUILDWISE_FEE_PERCENTAGE=0.0    # 0% für Beta, 4.0 für Go-Live
BUILDWISE_FEE_PHASE=beta        # "beta" oder "production"
BUILDWISE_FEE_ENABLED=true      # true/false
```

### Service-Methoden
```python
# Aktuelle Konfiguration abrufen
percentage = BuildWiseFeeService.get_current_fee_percentage()
phase = BuildWiseFeeService.get_current_fee_phase()
enabled = BuildWiseFeeService.is_fee_enabled()

# Gebühr erstellen (verwendet automatisch aktuelle Konfiguration)
fee = await BuildWiseFeeService.create_fee_from_quote(
    db=db,
    quote_id=quote_id,
    cost_position_id=cost_position_id
)
```

## 🛡️ Sicherheit

### Admin-Berechtigungen
- Nur Administratoren können die Konfiguration ändern
- API-Endpunkte prüfen Admin-Status
- Tool erfordert manuelle Bestätigung

### Validierung
- Prozentsatz muss zwischen 0 und 100 liegen
- Phase muss "beta" oder "production" sein
- Gebühren können komplett deaktiviert werden

## 📊 Monitoring

### Status prüfen
```bash
python switch_buildwise_fees.py --status
```

### Statistiken anzeigen
```bash
python switch_buildwise_fees.py --stats
```

### System testen
```bash
python test_fee_configuration.py
```

## 🔄 Migration

### Bestehende Gebühren
- **Keine Änderungen**: Bestehende Gebühren bleiben unverändert
- **Neue Gebühren**: Verwenden automatisch die aktuelle Konfiguration
- **Rückwärtskompatibilität**: Vollständig kompatibel mit bestehenden Daten

### Manuelle Anpassung (falls benötigt)
```sql
-- Alle bestehenden Gebühren auf 0% setzen (Beta-Phase)
UPDATE buildwise_fees 
SET fee_percentage = 0.0, 
    fee_details = CONCAT(fee_details, ' (Beta-Phase)')
WHERE fee_percentage > 0;
```

## 🎯 Nächste Schritte

### 1. Beta-Phase starten
```bash
python switch_buildwise_fees.py --phase beta
python switch_buildwise_fees.py --status
```

### 2. System testen
```bash
python test_fee_configuration.py
```

### 3. Go-Live vorbereiten
```bash
# Testen der Production-Konfiguration
python switch_buildwise_fees.py --phase production
python switch_buildwise_fees.py --status
```

### 4. Go-Live durchführen
```bash
python switch_buildwise_fees.py --phase production
```

## 📚 Weitere Dokumentation

- **Vollständige Dokumentation**: `BUILDWISE_GEBUEHREN_KONFIGURATION.md`
- **API-Dokumentation**: FastAPI Auto-Docs unter `/docs`
- **Admin-Tool Hilfe**: `python switch_buildwise_fees.py --help`

## 🆘 Support

### Häufige Probleme

**Gebühren werden nicht erstellt:**
```bash
python switch_buildwise_fees.py --status
# Prüfen Sie ob Gebühren aktiviert sind
```

**Falsche Gebühren-Höhe:**
```bash
python switch_buildwise_fees.py --status
# Prüfen Sie die aktuelle Konfiguration
```

**Admin-Berechtigungen:**
```bash
# Verwenden Sie das Admin-Tool für direkte Änderungen
python switch_buildwise_fees.py --phase beta
```

### Logs prüfen
- Alle Konfigurationsänderungen werden geloggt
- Gebühren-Erstellung mit Phase-Information
- Fehler bei deaktivierten Gebühren

---

**✅ Das System ist bereit für die Beta-Phase!** 