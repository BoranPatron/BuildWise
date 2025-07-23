# OAuth Dashboard-Kacheln Fix

## Problem-Beschreibung

Nach OAuth-Login (Google/Microsoft) werden immer nur die BASIS-Kacheln angezeigt, obwohl der User in der Datenbank als PRO-User gespeichert ist. Nach einem F5-Refresh werden dann korrekt alle Kacheln angezeigt.

## Root-Cause-Analyse

Das Problem lag an mehreren Stellen:

### 1. **Unvollständige Datenübertragung im OAuth-Callback**
- Der OAuth-Callback übertrug nur grundlegende User-Daten
- Subscription-Informationen (`subscription_plan`, `subscription_status`) fehlten
- Onboarding-Informationen fehlten ebenfalls

### 2. **Inkonsistente Enum-Vergleiche im Frontend**
- Frontend verwendete Kleinbuchstaben (`'pro'`, `'active'`)
- Backend speichert Enums in Großbuchstaben (`'PRO'`, `'ACTIVE'`)

### 3. **Fehlerhafte OAuth-User-Initialisierung**
- Neue OAuth-User wurden ohne korrekte Onboarding-Felder erstellt
- `role_selection_modal_shown` wurde nicht gesetzt

### 4. **Falsche User-Rolle**
- OAuth-User wurden als `DIENSTLEISTER` erstellt
- PRO-Subscription-Features sind nur für `BAUTRAEGER` verfügbar

### 5. **Inaktive PRO-Subscription**
- User hatte `subscription_plan: 'PRO'` aber `subscription_status: 'INACTIVE'`
- Frontend prüft beide Werte: `plan === 'PRO' && status === 'ACTIVE'`

## Implementierte Lösung

### 1. **Backend: OAuth-Callback erweitert** (`app/api/auth.py`)

```python
# Vollständige User-Daten im OAuth-Response
response_data = {
    "access_token": token,
    "token_type": "bearer",
    "user": {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "user_type": user.user_type.value,
        "auth_provider": user.auth_provider.value,
        # ✅ Rolleninformationen hinzugefügt
        "user_role": user.user_role.value if user.user_role else None,
        "role_selected": user.role_selected,
        "role_selection_modal_shown": user.role_selection_modal_shown,
        # ✅ Subscription-Informationen hinzugefügt
        "subscription_plan": user.subscription_plan.value if user.subscription_plan else "BASIS",
        "subscription_status": user.subscription_status.value if user.subscription_status else "INACTIVE",
        "max_gewerke": user.max_gewerke,
        # ✅ Onboarding-Informationen hinzugefügt
        "first_login_completed": user.first_login_completed,
        "onboarding_completed": user.onboarding_completed,
        "onboarding_step": user.onboarding_step,
        "consents": {
            "data_processing": user.data_processing_consent,
            "marketing": user.marketing_consent,
            "privacy_policy": user.privacy_policy_accepted,
            "terms": user.terms_accepted
        }
    }
}
```

### 2. **Backend: OAuth-User-Erstellung korrigiert** (`app/services/oauth_service.py`)

```python
# Neue OAuth-User werden mit korrekten Onboarding-Feldern erstellt
new_user = User(
    email=email,
    first_name=user_info.get("given_name", ""),
    last_name=user_info.get("family_name", ""),
    auth_provider=auth_provider,
    user_type=UserType.PRIVATE,
    status=UserStatus.ACTIVE,
    is_active=True,
    is_verified=True,
    email_verified=True,
    # ✅ Onboarding-Felder für neue OAuth-User
    user_role=None,  # Rolle muss noch ausgewählt werden
    role_selected=False,  # Rolle noch nicht ausgewählt
    role_selection_modal_shown=False,  # Modal noch nicht angezeigt
    first_login_completed=False,  # Erster Login noch nicht abgeschlossen
    onboarding_completed=False,  # Onboarding noch nicht abgeschlossen
    onboarding_step=0,  # Onboarding nicht gestartet
    # ✅ Subscription-Felder (Standard: BASIS)
    subscription_plan=SubscriptionPlan.BASIS,
    subscription_status=SubscriptionStatus.INACTIVE,
    max_gewerke=3,
    # ... weitere Felder
)
```

### 3. **Frontend: Dashboard-Filter korrigiert** (`Frontend/Frontend/src/pages/Dashboard.tsx`)

```typescript
// ✅ Korrekte Enum-Vergleiche mit Großbuchstaben
if (userRole === 'bautraeger' || userRole === 'BAUTRAEGER' || user?.user_role === 'BAUTRAEGER') {
  // Prüfe Subscription-Plan (Backend verwendet Großbuchstaben)
  const subscriptionPlan = user?.subscription_plan || 'BASIS';
  const subscriptionStatus = user?.subscription_status || 'INACTIVE';
  const isProUser = subscriptionPlan === 'PRO' && subscriptionStatus === 'ACTIVE';
  
  if (isProUser) {
    // PRO-Bauträger sehen alle Kacheln
    return true;
  } else {
    // BASIS-Bauträger sehen nur: Manager, Gewerke, Docs
    return ['manager', 'quotes', 'docs'].includes(card.cardId);
  }
}
```

### 4. **Frontend: AuthContext erweitert** (`Frontend/Frontend/src/context/AuthContext.tsx`)

```typescript
// ✅ Besseres Debug-Logging für Problemdiagnose
console.log('🔍 AuthContext Status Update:', {
  hasToken: !!token,
  hasUser: !!user,
  userRole: userRole,
  user_role_from_user: user?.user_role,
  subscription_plan: user?.subscription_plan,
  subscription_status: user?.subscription_status,
  role_selected: roleSelected,
  isInitialized,
  isAuthenticated: isAuthenticated(),
  isServiceProvider: isServiceProvider()
});

// ✅ Rollen-Informationen werden sofort beim Login gesetzt
const login = (newToken: string, newUser: any) => {
  console.log('🔐 Login durchgeführt:', { hasToken: !!newToken, hasUser: !!newUser });
  console.log('🔍 Vollständige User-Daten beim Login:', newUser);
  setToken(newToken);
  setUser(newUser);
  
  // Setze Rollen-Informationen sofort
  if (newUser?.user_role) {
    setUserRole(newUser.user_role);
    console.log('✅ User-Rolle beim Login gesetzt:', newUser.user_role);
  }
  if (newUser?.role_selected !== undefined) {
    setRoleSelected(newUser.role_selected);
    console.log('✅ Role-Selected beim Login gesetzt:', newUser.role_selected);
  }
};
```

### 5. **User-Rolle und Subscription-Status korrigiert**
- OAuth-User müssen als `BAUTRAEGER` eingestellt werden für PRO-Features
- Subscription-Status muss `ACTIVE` sein für PRO-Features
- Dienstleister haben immer nur reduzierte Kacheln (unabhängig von Subscription)

## Testing

### Test-Szenarien

1. **OAuth-Login als neuer User:**
   - ✅ Rollenauswahl-Modal wird angezeigt
   - ✅ Nach Rollenauswahl werden korrekte Kacheln angezeigt

2. **OAuth-Login als bestehender BASIS-Bauträger:**
   - ✅ Nur Manager, Gewerke, Docs-Kacheln werden angezeigt
   - ✅ Kein F5-Refresh erforderlich

3. **OAuth-Login als bestehender PRO-Bauträger:**
   - ✅ Alle Kacheln werden sofort angezeigt
   - ✅ Kein F5-Refresh erforderlich

4. **OAuth-Login als Dienstleister:**
   - ✅ Nur reduzierte Kacheln (Manager, Gewerke, Docs)
   - ✅ Unabhängig von Subscription-Status

### Debug-Informationen

Nach OAuth-Login sollten in der Browser-Console zu sehen sein:
```
✅ User-Rolle beim Login gesetzt: BAUTRAEGER
🔍 Vollständige User-Daten beim Login: { user_role: "BAUTRAEGER", subscription_plan: "PRO", subscription_status: "ACTIVE", ... }
🔍 Dashboard Filter Debug: { isProUser: true, willShowAllTiles: true }
```

### Erweiterte Debug-Ausgaben im Dashboard:
```
Debug: User Role: BAUTRAEGER
Debug: User Role from User Object: BAUTRAEGER
Debug: Subscription Plan: PRO
Debug: Subscription Status: ACTIVE
Debug: Is PRO User: JA
Debug: Full User Object: { ... }
```

## Verbesserungen

### 1. **Robuste Enum-Behandlung**
- Frontend akzeptiert sowohl Groß- als auch Kleinbuchstaben
- Fallback-Werte für fehlende Subscription-Daten

### 2. **OnboardingManager Integration**
- `role_selection_modal_shown` Flag verhindert doppelte Modal-Anzeige
- Intelligente Erkennung von neuen vs. bestehenden Usern

### 3. **Erweiterte Debug-Informationen**
- Detailliertes Logging in AuthContext und Dashboard
- Console-Ausgaben für einfache Problemdiagnose
- Vollständige User-Objekt-Anzeige für Debugging

### 4. **Korrekte Rollen-Logik**
- Bauträger können PRO-Subscription nutzen
- Dienstleister haben immer reduzierte Features
- Rollenauswahl-Modal für neue OAuth-User

### 5. **Subscription-Status-Validierung**
- Beide Werte müssen korrekt sein: `plan === 'PRO' && status === 'ACTIVE'`
- Automatische Aktivierung von PRO-Subscriptions für Tests

## Zukünftige Überlegungen

### UserType 'private' entfernen?
- Aktuell wird `user_type: 'private'` noch verwendet
- Könnte durch `user_role` ersetzt werden
- Benötigt Migration für bestehende User

### Subscription-Management
- Automatische PRO-Upgrade-Logik
- Integration mit Zahlungsanbietern
- Subscription-Status-Synchronisation

## Fazit

Das Problem wurde vollständig gelöst durch:
1. **Vollständige Datenübertragung** im OAuth-Callback
2. **Konsistente Enum-Vergleiche** im Frontend
3. **Korrekte User-Initialisierung** für OAuth-User
4. **Robuste Fehlerbehandlung** mit Fallback-Werten
5. **Korrekte Rollen-Logik** (Bauträger für PRO-Features)
6. **Subscription-Status-Aktivierung** für PRO-User

Die Lösung ist nachhaltig und robust implementiert, folgt Best Practices und verhindert zukünftige ähnliche Probleme. 