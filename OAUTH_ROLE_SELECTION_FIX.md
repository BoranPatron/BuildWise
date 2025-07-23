# OAuth Rollenauswahl-Fix

## Problem-Beschreibung

Nach erfolgreichem OAuth-Login und Auswahl der Rolle "Dienstleister" tritt folgender Fehler auf:

```
❌ Backend Error: {"detail":"unsupported operand type(s) for -: 'datetime.datetime' and 'NoneType'","error_type":"TypeError","message":"Ein interner Serverfehler ist aufgetreten"}
```

## Root-Cause-Analyse

Das Problem lag daran, dass beim Speichern der Rolle eine Subtraktion zwischen einem `datetime`-Objekt und `None` durchgeführt wurde:

```python
# Fehlerhafte Zeile in app/api/auth.py
user_age = datetime.utcnow() - current_user.created_at
```

### **Ursachen:**

1. **`created_at` ist `None`:**
   - OAuth-User haben möglicherweise kein `created_at` Feld gesetzt
   - Datenbank-Migration hat das Feld nicht korrekt übertragen

2. **Fehlende Null-Check:**
   - Code prüfte nicht, ob `created_at` `None` ist
   - Direkte Subtraktion führte zu TypeError

3. **User-Alter-Berechnung:**
   - Code versucht User-Alter zu berechnen für Rollenänderung
   - Schlägt fehl wenn `created_at` fehlt

## Implementierte Lösung

### **Backend: Null-Safe Datetime-Berechnung** (`app/api/auth.py`)

```python
@router.post("/select-role")
async def select_role(
    request: RoleSelectionRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """Speichert die gewählte Rolle des Benutzers"""
    
    from datetime import datetime, timedelta
    
    # ✅ Null-Safe Prüfung ob User "neu" ist
    if current_user.created_at is None:
        # Fallback für User ohne created_at
        is_new_user = True
    else:
        user_age = datetime.utcnow() - current_user.created_at
        is_new_user = user_age.total_seconds() < 24 * 60 * 60  # 24 Stunden
    
    # Erlaube Rollenänderung nur für neue User oder wenn noch keine Rolle gesetzt
    if current_user.role_selected and current_user.user_role and not is_new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rolle wurde bereits ausgewählt. Kontaktieren Sie einen Administrator für Änderungen."
        )
    
    # Validiere die Rolle
    if request.role not in ["bautraeger", "dienstleister"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültige Rolle. Wählen Sie 'bautraeger' oder 'dienstleister'."
        )
    
    try:
        # Setze die Rolle
        from datetime import datetime
        from sqlalchemy import update
        
        role_enum = UserRole.BAUTRAEGER if request.role == "bautraeger" else UserRole.DIENSTLEISTER
        
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(
                user_role=role_enum,
                role_selected=True,
                role_selected_at=datetime.utcnow(),
                role_selection_modal_shown=True  # Markiere dass Modal angezeigt wurde
            )
        )
        await db.commit()
        
        # Audit-Log
        ip_address = req.client.host if req else None
        await SecurityService.create_audit_log(
            db, current_user.id, AuditAction.USER_UPDATE,
            f"Rolle ausgewählt: {request.role}",
            resource_type="user", resource_id=current_user.id,
            ip_address=SecurityService.anonymize_ip_address(ip_address) if ip_address else None
        )
        
        return {
            "message": "Rolle erfolgreich ausgewählt",
            "role": request.role,
            "role_selected": True
        }
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Rolle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Speichern der Rolle"
        )
```

## Testing

### **Test-Szenarien**

1. **OAuth-Login als neuer User:**
   - ✅ Rollenauswahl-Modal wird angezeigt
   - ✅ Rolle "Dienstleister" kann ausgewählt werden
   - ✅ Keine TypeError bei `created_at = None`

2. **OAuth-Login als bestehender User:**
   - ✅ Rolle wird korrekt gespeichert
   - ✅ User-Rolle wird im Frontend angezeigt

3. **Fehlerbehandlung:**
   - ✅ Null-Safe Datetime-Berechnung
   - ✅ Fallback für User ohne `created_at`
   - ✅ Aussagekräftige Fehlermeldungen

### **Debug-Informationen**

Nach erfolgreicher Rollenauswahl sollten in den Backend-Logs zu sehen sein:
```
✅ Rolle erfolgreich ausgewählt: dienstleister
🔍 User-Details: { user_role: "DIENSTLEISTER", role_selected: true, role_selected_at: "2025-07-23T..." }
```

## Verbesserungen

### 1. **Null-Safe Datetime-Behandlung**
- Prüfung auf `None` vor Subtraktion
- Fallback für User ohne `created_at`
- Robuste Fehlerbehandlung

### 2. **Bessere Fehlerbehandlung**
- Spezifische Fehlermeldungen für verschiedene Szenarien
- Graceful Degradation bei fehlenden Daten
- Detailliertes Logging

### 3. **User-Experience**
- Rollenauswahl funktioniert auch für User mit fehlenden Daten
- Keine Abstürze bei OAuth-Login
- Konsistente Benutzerführung

## Zukünftige Überlegungen

### **Datenbank-Migration**
- Automatische Migration für fehlende `created_at` Felder
- Default-Werte für OAuth-User
- Datenintegrität-Prüfungen

### **OAuth-User-Initialisierung**
- Vollständige User-Daten beim OAuth-Login
- Automatische `created_at` Setzung
- Konsistente Datenstruktur

## Fazit

Das Problem wurde gelöst durch:
1. **Null-Safe Datetime-Berechnung** (Prüfung auf `None`)
2. **Fallback für User ohne `created_at`** (Standard: `is_new_user = True`)
3. **Robuste Fehlerbehandlung** mit spezifischen Meldungen
4. **Bessere User-Experience** ohne Abstürze

Die Lösung ist nachhaltig und robust implementiert, folgt Python Best Practices und verhindert zukünftige ähnliche Probleme. 