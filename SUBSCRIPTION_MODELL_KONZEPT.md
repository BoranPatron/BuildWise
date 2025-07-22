# 🚀 Subscription-Modell mit Stripe-Integration - Konzept

## 📋 Übersicht

**Ziel:** Bauträger/Bauherr können zwischen Basis und Pro Modell wählen. Pro-Modell wird über Stripe abgerechnet und bietet erweiterte Funktionen.

## 🏗️ Subscription-Modelle

### **1. Basis-Modell (Kostenlos)**
- **Gewerke:** Maximal 3 Ausschreibungen
- **Dashboard-Kacheln:** Nur "Manager", "Gewerke", "Docs"
- **Einschränkungen:** Begrenzte Funktionalität
- **Zielgruppe:** Kleine Projekte, Testen der Plattform

### **2. Pro-Modell (Premium)**
- **Gewerke:** Unbegrenzte Ausschreibungen
- **Dashboard-Kacheln:** Alle verfügbaren Kacheln
- **Email/Kalender:** Google Mail/Calendar oder Microsoft Outlook
- **Preis:** 12.99 CHF/Monat oder 130 CHF/Jahr
- **Zielgruppe:** Professionelle Bauträger

## 💳 Stripe-Preismodell

### **Preise (CHF):**
- **Monatlich:** 12.99 CHF/Monat
- **Jährlich:** 130 CHF/Jahr (ca. 16% Ersparnis)

### **Stripe-Produkte:**
```
Product 1: BuildWise Pro Monthly
- Price: CHF 12.99/month
- Recurring: monthly
- Currency: CHF

Product 2: BuildWise Pro Yearly  
- Price: CHF 130.00/year
- Recurring: yearly
- Currency: CHF
```

## 🏗️ Architektur-Design

### **Backend-Änderungen:**

#### **1. User Model erweitern:**
```python
class SubscriptionPlan(enum.Enum):
    BASIS = "basis"
    PRO = "pro"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    CANCELED = "canceled"
    PAST_DUE = "past_due"

class User(Base):
    # Subscription-Felder
    subscription_plan = Column(Enum(SubscriptionPlan), default=SubscriptionPlan.BASIS)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE)
    subscription_id = Column(String, nullable=True)  # Stripe Subscription ID
    customer_id = Column(String, nullable=True)  # Stripe Customer ID
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    max_gewerke = Column(Integer, default=3)  # Basis: 3, Pro: unlimited (-1)
```

#### **2. Stripe Integration:**
```python
# Neue Services
- StripeService: Stripe API Integration
- SubscriptionService: Subscription Management
- PaymentService: Payment Processing

# API Endpoints
- POST /api/v1/subscriptions/create-checkout
- POST /api/v1/subscriptions/cancel
- GET /api/v1/subscriptions/status
- POST /api/v1/webhooks/stripe (Webhook Handler)
```

### **Frontend-Änderungen:**

#### **1. Subscription Context:**
```typescript
interface SubscriptionContextType {
  plan: 'basis' | 'pro';
  status: 'active' | 'inactive' | 'canceled' | 'past_due';
  maxGewerke: number;
  isProUser: () => boolean;
  upgradeToProMonthly: () => Promise<void>;
  upgradeToProYearly: () => Promise<void>;
  cancelSubscription: () => Promise<void>;
}
```

#### **2. Neue Komponenten:**
- **UpgradeModal:** Pro-Upgrade mit Preisauswahl
- **SubscriptionBadge:** Status-Anzeige in Navbar
- **ProFeatureCard:** Gesperrte Features für Basis-User
- **EmailCalendarButtons:** Google/Microsoft Integration (Pro only)

## 🎨 UI/UX Design

### **Navbar-Erweiterung:**
```
┌─────────────────────────────────────────────────────────────┐
│  🏗️ BuildWise    [Manager] [Gewerke] [Docs] ... [💎 Pro]   │
│                                                    [User ▼] │
└─────────────────────────────────────────────────────────────┘
```

### **UpgradeModal:**
```
┌─────────────────────────────────────────────────────────────┐
│                 Upgrade zu BuildWise Pro                    │
│                                                             │
│  ┌─────────────┐              ┌─────────────┐              │
│  │ Monatlich   │              │ Jährlich    │              │
│  │ 12.99 CHF   │              │ 130 CHF     │              │
│  │ pro Monat   │              │ pro Jahr    │              │
│  │             │              │ 16% sparen! │              │
│  │ [Wählen]    │              │ [Wählen]    │              │
│  └─────────────┘              └─────────────┘              │
│                                                             │
│  ✅ Unbegrenzte Gewerke                                     │
│  ✅ Alle Dashboard-Features                                 │
│  ✅ Email & Kalender Integration                            │
│  ✅ Priority Support                                        │
└─────────────────────────────────────────────────────────────┘
```

### **Pro-Features (Schritt 1):**
```
┌─────────────────────────────────────────────────────────────┐
│                Email & Kalender Integration                 │
│                                                             │
│  ┌─────────────┐              ┌─────────────┐              │
│  │ 📧 Google   │              │ 📧 Microsoft│              │
│  │ Gmail +     │              │ Outlook +   │              │
│  │ Calendar    │              │ Calendar    │              │
│  │ [Verbinden] │              │ [Verbinden] │              │
│  └─────────────┘              └─────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## 💳 Stripe-Konfiguration (Schritt-für-Schritt)

### **1. Stripe-Account Setup:**
1. Registrierung bei [stripe.com](https://stripe.com)
2. Schweizer Unternehmen verifizieren
3. CHF als Haupt-Währung einstellen

### **2. Produkte erstellen:**
```bash
# Stripe CLI Commands
stripe products create --name "BuildWise Pro Monthly" --description "Monatliches Pro-Abonnement"
stripe prices create --product prod_xxx --unit-amount 1299 --currency chf --recurring interval=month

stripe products create --name "BuildWise Pro Yearly" --description "Jährliches Pro-Abonnement" 
stripe prices create --product prod_yyy --unit-amount 13000 --currency chf --recurring interval=year
```

### **3. Webhook-Endpoints:**
```
Endpoint: https://yourdomain.com/api/v1/webhooks/stripe
Events:
- customer.subscription.created
- customer.subscription.updated  
- customer.subscription.deleted
- invoice.payment_succeeded
- invoice.payment_failed
```

### **4. Environment Variables:**
```env
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRO_MONTHLY_PRICE_ID=price_xxx
STRIPE_PRO_YEARLY_PRICE_ID=price_yyy
```

## 🔄 Subscription-Flow

### **Upgrade-Flow:**
1. **Basis-User** klickt "Pro" Button in Navbar
2. **UpgradeModal** öffnet sich mit Preisoptionen
3. **User wählt** Monatlich oder Jährlich
4. **Stripe Checkout** öffnet sich
5. **Zahlung** wird verarbeitet
6. **Webhook** aktiviert Pro-Features
7. **Dashboard** zeigt alle Kacheln

### **Downgrade-Flow:**
1. **Pro-User** kann Abo kündigen
2. **Subscription läuft** bis zum Ende weiter
3. **Automatischer Downgrade** zu Basis am Ende
4. **Dashboard** wird eingeschränkt

## 🔒 Sicherheit & Validierung

### **Backend-Validierung:**
- Stripe-Webhook-Signatur-Verifizierung
- Subscription-Status vor Feature-Zugriff prüfen
- Gewerke-Limit enforcing

### **Frontend-Schutz:**
- Pro-Features nur für aktive Abonnenten
- Graceful Degradation bei abgelaufenem Abo
- Loading-States für Stripe-Integration

## 📊 Datenbank-Schema

### **Neue Tabellen:**
```sql
-- Subscription-Felder zu users Tabelle
ALTER TABLE users ADD COLUMN subscription_plan VARCHAR(10) DEFAULT 'basis';
ALTER TABLE users ADD COLUMN subscription_status VARCHAR(20) DEFAULT 'inactive';
ALTER TABLE users ADD COLUMN subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN subscription_start TIMESTAMP;
ALTER TABLE users ADD COLUMN subscription_end TIMESTAMP;
ALTER TABLE users ADD COLUMN max_gewerke INTEGER DEFAULT 3;

-- Indices
CREATE INDEX idx_users_subscription ON users(subscription_plan, subscription_status);
CREATE INDEX idx_users_customer ON users(customer_id);
```

## 🧪 Test-Szenarien

### **1. Subscription-Tests:**
- Upgrade von Basis zu Pro (monatlich/jährlich)
- Successful payment webhook
- Failed payment webhook
- Subscription cancellation
- Automatic downgrade

### **2. Feature-Tests:**
- Gewerke-Limit für Basis-User
- Dashboard-Kacheln-Filterung
- Pro-Feature-Zugriff
- Email/Calendar-Button-Anzeige

## 🚀 Implementierungsschritte

### **Phase 1: Backend Foundation**
1. User Model erweitern
2. Subscription Services erstellen
3. Stripe Integration implementieren
4. API Endpoints erstellen
5. Webhook Handler implementieren

### **Phase 2: Frontend Integration**
1. SubscriptionContext erstellen
2. UpgradeModal implementieren
3. Navbar Pro-Button hinzufügen
4. Dashboard-Filterung erweitern
5. Pro-Feature-Guards

### **Phase 3: Email/Calendar Buttons**
1. ProFeatureCard Komponente
2. Email/Calendar-Button-UI
3. Integration-Vorbereitung
4. Responsive Design

### **Phase 4: Testing & Polish**
1. Stripe Test-Mode Testing
2. Webhook-Testing
3. Edge-Cases abdecken
4. Performance-Optimierung

## 💡 Besonderheiten

### **Schweizer Markt:**
- CHF als Währung
- Schweizer MwSt. berücksichtigen
- DSGVO/Datenschutz-Compliance

### **Graceful Degradation:**
- Basis-User sehen "Upgrade"-Hinweise
- Pro-Features werden elegant gesperrt
- Klare Kommunikation der Limits

### **Skalierbarkeit:**
- Weitere Pläne (Enterprise) möglich
- Add-on-Produkte erweiterbar
- Multi-Currency-Support vorbereitet

---

**Status:** 📋 Konzept erstellt  
**Nächster Schritt:** Backend-Implementation starten 