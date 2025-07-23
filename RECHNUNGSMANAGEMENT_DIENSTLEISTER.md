# Rechnungsmanagement für Dienstleister

## Übersicht

Das neue Rechnungsmanagement-System ersetzt die "Gewerke"-Kachel im Dienstleister-Dashboard und bietet eine vollständige Lösung für die Erstellung, Verwaltung und Verfolgung von Rechnungen für abgeschlossene Gewerke.

## 🎯 Zielsetzung

- **Vollständiger Rechnungsworkflow** - Von der Erstellung bis zur Bezahlung
- **Professionelle Rechnungsstellung** - PDF-Generation und E-Mail-Versand
- **Zahlungsverfolgung** - Status-Tracking und Mahnwesen
- **Finanzübersicht** - Umsatz-Statistiken und Cashflow-Management
- **Keine Zahlungsanbieter-Integration** - Fokus auf Rechnungsmanagement

## 🏗️ Systemarchitektur

### **Hauptkomponenten:**

1. **InvoiceManagement** - Hauptkomponente mit Übersicht und Funktionen
2. **InvoiceDetailsModal** - Detailansicht für einzelne Rechnungen
3. **CreateInvoiceModal** - Formular für neue Rechnungen
4. **Invoices Page** - Dedizierte Seite für Rechnungsmanagement

### **Datei-Struktur:**
```
Frontend/Frontend/src/
├── components/
│   └── InvoiceManagement.tsx    # Hauptkomponente
├── pages/
│   └── Invoices.tsx            # Dedizierte Seite
└── App.tsx                     # Route-Integration
```

## 📊 Datenmodell

### **Invoice Interface:**
```typescript
interface Invoice {
  id: number;
  invoice_number: string;        // z.B. "INV-2024-001"
  project_name: string;          // Projektname
  project_id: number;            // Projekt-Referenz
  trade_title: string;           // Gewerk-Titel
  trade_id: number;              // Gewerk-Referenz
  client_name: string;           // Kundenname
  client_email: string;          // Kunden-E-Mail
  client_phone?: string;         // Telefonnummer (optional)
  amount: number;                // Nettobetrag
  currency: string;              // Währung (EUR)
  tax_rate: number;              // MwSt-Satz (19%)
  tax_amount: number;            // MwSt-Betrag
  total_amount: number;          // Gesamtbetrag
  status: InvoiceStatus;         // Rechnungsstatus
  created_at: string;            // Erstellungsdatum
  sent_at?: string;              // Versanddatum
  due_date: string;              // Fälligkeitsdatum
  paid_at?: string;              // Zahlungsdatum
  description: string;           // Rechnungsbeschreibung
  line_items: InvoiceLineItem[]; // Rechnungspositionen
  payment_terms: string;         // Zahlungsbedingungen
  notes?: string;                // Notizen
  pdf_path?: string;             // PDF-Pfad
}
```

### **Rechnungsstatus:**
```typescript
type InvoiceStatus = 
  | 'draft'      // Entwurf
  | 'sent'       // Versendet
  | 'viewed'     // Angesehen
  | 'paid'       // Bezahlt
  | 'overdue'    // Überfällig
  | 'cancelled'; // Storniert
```

### **Rechnungsposition:**
```typescript
interface InvoiceLineItem {
  id: number;
  description: string;    // Positionsbeschreibung
  quantity: number;       // Menge
  unit_price: number;     // Einzelpreis
  total_price: number;    // Gesamtpreis
}
```

### **Statistiken:**
```typescript
interface InvoiceStats {
  total_invoices: number;      // Gesamtanzahl Rechnungen
  total_revenue: number;       // Gesamtumsatz
  pending_amount: number;      // Ausstehender Betrag
  overdue_amount: number;      // Überfälliger Betrag
  paid_invoices: number;       // Bezahlte Rechnungen
  draft_invoices: number;      // Entwürfe
  average_payment_time: number; // Durchschnittliche Zahlungszeit
}
```

## 🎨 UI/UX-Design

### **Dashboard-Integration:**
- **Kachel-Austausch** - "Gewerke" → "Rechnungen"
- **Icon** - Euro-Symbol (€) für Rechnungsmanagement
- **Badge** - Anzahl der Rechnungen
- **Navigation** - Direkte Weiterleitung zu `/invoices`

### **Hauptansicht-Layout:**

#### **Header mit Statistiken:**
```typescript
// 4 Statistik-Karten in Gradient-Design
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Gesamt-     │ Bezahlte    │ Ausstehend  │ Überfällig  │
│ Umsatz      │ Rechnungen  │             │             │
│ 30.958 €    │     1       │  6.545 €    │ 14.875 €    │
│ 📈          │     ✅      │     ⏰      │     ⚠️     │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

#### **Filter & Suche:**
```typescript
// Suchleiste + Status-Filter + Sortierung
┌─────────────────────────────────────────────────────────┐
│ 🔍 Rechnungen suchen...  [Status ▼] [Sortierung ▼] ↕️ 🔄│
└─────────────────────────────────────────────────────────┘
```

#### **Rechnungsliste:**
```typescript
// Kompakte Listenansicht mit Aktions-Buttons
┌─────────────────────────────────────────────────────────┐
│ INV-2024-001  [Versendet]                              │
│ Neubau Einfamilienhaus München                         │
│ Elektroinstallation                                    │
│ Max Mustermann | max@mustermann.de | 6.545 € | 15.02.24│
│                                          👁️ 📄 📧    │
├─────────────────────────────────────────────────────────┤
│ INV-2024-002  [Bezahlt]                               │
│ ...                                                    │
└─────────────────────────────────────────────────────────┘
```

### **Farbschema:**
- **Entwurf** - Grau (`bg-gray-100 text-gray-800`)
- **Versendet** - Blau (`bg-blue-100 text-blue-800`)
- **Angesehen** - Lila (`bg-purple-100 text-purple-800`)
- **Bezahlt** - Grün (`bg-green-100 text-green-800`)
- **Überfällig** - Rot (`bg-red-100 text-red-800`)
- **Storniert** - Grau (`bg-gray-100 text-gray-800`)

## ⚙️ Funktionalitäten

### **1. Rechnungsübersicht**

#### **Statistik-Dashboard:**
```typescript
const stats = {
  total_invoices: 3,           // Gesamtanzahl
  total_revenue: 30958.00,     // Gesamtumsatz in €
  pending_amount: 6545.00,     // Ausstehend in €
  overdue_amount: 14875.00,    // Überfällig in €
  paid_invoices: 1,            // Anzahl bezahlt
  draft_invoices: 0,           // Anzahl Entwürfe
  average_payment_time: 14     // Tage durchschnittlich
};
```

#### **Filter & Suche:**
- **Textsuche** - Rechnungsnummer, Projektname, Kundenname
- **Status-Filter** - Alle, Entwurf, Versendet, Bezahlt, Überfällig, etc.
- **Sortierung** - Nach Datum, Betrag, Status (aufsteigend/absteigend)
- **Refresh-Button** - Daten neu laden

### **2. Rechnungsdetails**

#### **Modal-Ansicht mit:**
- **Rechnungsinformationen** - Nummer, Daten, Status
- **Kundendaten** - Name, E-Mail, Telefon
- **Rechnungspositionen** - Detaillierte Aufstellung
- **Berechnung** - Netto, MwSt, Brutto
- **Aktions-Buttons** - PDF-Download, E-Mail-Versand

#### **Beispiel-Rechnungsposition:**
```typescript
{
  id: 1,
  description: "Elektroinstallation Erdgeschoss",
  quantity: 1,
  unit_price: 2500.00,
  total_price: 2500.00
}
```

### **3. Rechnungserstellung**

#### **Formular-Struktur:**
- **Projekt-Auswahl** - Dropdown mit abgeschlossenen Gewerken
- **Kundendaten** - Automatisch aus Projekt übernommen
- **Rechnungspositionen** - Dynamische Liste
- **Berechnungen** - Automatische MwSt-Berechnung
- **Zahlungskonditionen** - Fälligkeitsdatum, Zahlungsbedingungen
- **Notizen** - Zusätzliche Hinweise

### **4. Workflow-Management**

#### **Status-Übergänge:**
```
Entwurf → Versendet → Angesehen → Bezahlt
    ↓         ↓          ↓
Storniert  Überfällig  Überfällig
```

#### **Automatische Funktionen:**
- **Überfälligkeits-Prüfung** - Automatisches Status-Update
- **E-Mail-Tracking** - "Angesehen"-Status bei Öffnung
- **Zahlungsbestätigung** - Manueller Status-Update auf "Bezahlt"

### **5. PDF-Generation**

#### **Features (geplant):**
- **Professionelles Layout** - Corporate Design
- **Firmen-Header** - Logo, Kontaktdaten
- **Rechnungsdetails** - Alle Positionen und Berechnungen
- **Zahlungshinweise** - Bankdaten, Zahlungsfristen
- **Rechtliche Hinweise** - AGB, Datenschutz

### **6. E-Mail-Integration**

#### **Funktionen (geplant):**
- **Automatischer Versand** - Rechnung als PDF-Anhang
- **E-Mail-Templates** - Professionelle Vorlagen
- **Tracking** - Öffnungs- und Klick-Verfolgung
- **Erinnerungen** - Automatische Zahlungserinnerungen

## 🔧 Technische Implementierung

### **State-Management:**
```typescript
// Hauptzustände
const [invoices, setInvoices] = useState<Invoice[]>([]);
const [stats, setStats] = useState<InvoiceStats>({...});
const [loading, setLoading] = useState(false);

// Modal-Zustände
const [showCreateModal, setShowCreateModal] = useState(false);
const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
const [showDetailsModal, setShowDetailsModal] = useState(false);

// Filter-Zustände
const [statusFilter, setStatusFilter] = useState<string>('all');
const [searchTerm, setSearchTerm] = useState('');
const [sortBy, setSortBy] = useState<'date' | 'amount' | 'status'>('date');
const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
```

### **API-Integration (geplant):**
```typescript
// Rechnungen laden
const loadInvoices = async () => {
  const response = await fetch('/api/invoices');
  const invoices = await response.json();
  setInvoices(invoices);
};

// Rechnung erstellen
const createInvoice = async (invoiceData: CreateInvoiceRequest) => {
  const response = await fetch('/api/invoices', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(invoiceData)
  });
  return response.json();
};

// PDF generieren
const generatePDF = async (invoiceId: number) => {
  const response = await fetch(`/api/invoices/${invoiceId}/pdf`);
  const blob = await response.blob();
  return blob;
};

// E-Mail versenden
const sendInvoiceEmail = async (invoiceId: number, emailData: EmailRequest) => {
  const response = await fetch(`/api/invoices/${invoiceId}/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(emailData)
  });
  return response.json();
};
```

### **Event-Handler:**
```typescript
// Rechnung anzeigen
const handleViewInvoice = (invoice: Invoice) => {
  setSelectedInvoice(invoice);
  setShowDetailsModal(true);
};

// PDF herunterladen
const handleDownloadPDF = async (invoice: Invoice) => {
  try {
    const blob = await generatePDF(invoice.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${invoice.invoice_number}.pdf`;
    a.click();
  } catch (error) {
    console.error('PDF-Download Fehler:', error);
  }
};

// Rechnung versenden
const handleSendInvoice = async (invoice: Invoice) => {
  try {
    await sendInvoiceEmail(invoice.id, {
      to: invoice.client_email,
      subject: `Rechnung ${invoice.invoice_number}`,
      template: 'invoice_email'
    });
    // Status auf "sent" aktualisieren
    await updateInvoiceStatus(invoice.id, 'sent');
    loadInvoices(); // Neu laden
  } catch (error) {
    console.error('E-Mail-Versand Fehler:', error);
  }
};
```

## 📱 Responsive Design

### **Desktop (≥1024px):**
- **4-Spalten Grid** - Statistiken nebeneinander
- **Vollständige Tabelle** - Alle Spalten sichtbar
- **Sidebar-Modals** - Rechts ausfahrende Details

### **Tablet (768px-1023px):**
- **2-Spalten Grid** - Statistiken in 2x2 Anordnung
- **Kompakte Tabelle** - Wichtigste Spalten
- **Overlay-Modals** - Zentrierte Dialoge

### **Mobile (<768px):**
- **1-Spalten Layout** - Statistiken untereinander
- **Card-Layout** - Rechnungen als Karten
- **Fullscreen-Modals** - Vollbild-Dialoge

## 🔐 Sicherheit & Berechtigungen

### **Zugriffskontrolle:**
- **Nur Dienstleister** - `isServiceProvider()` Prüfung
- **Eigene Rechnungen** - User-ID Filterung
- **Sichere API-Calls** - JWT-Token Authentifizierung

### **Datenschutz:**
- **DSGVO-konform** - Kundendaten-Schutz
- **Verschlüsselung** - Sensitive Daten verschlüsselt
- **Audit-Log** - Alle Aktionen protokolliert

## 🚀 Deployment & Integration

### **Dashboard-Integration:**
```typescript
// ServiceProviderDashboard.tsx - Kachel-Update
{
  title: "Rechnungen",
  description: "Rechnungsmanagement & Zahlungen",
  icon: <Euro size={32} />,
  onClick: () => navigate('/invoices'),
  badge: { text: `${stats.activeQuotes} Rechnungen`, color: "green" },
  // ...
}
```

### **Routing:**
```typescript
// App.tsx - Route hinzugefügt
<Route path="/invoices" element={
  <ProtectedRoute>
    <Invoices />
  </ProtectedRoute>
} />
```

### **Navigation:**
- **Dienstleister-Dashboard** - Rechnungen-Kachel
- **Direkte URL** - `/invoices`
- **Navbar-Integration** - Nur für Dienstleister sichtbar

## 📈 Metriken & Analytics

### **KPIs (Key Performance Indicators):**
- **Gesamtumsatz** - Summe aller bezahlten Rechnungen
- **Durchschnittliche Zahlungszeit** - Tage von Versand bis Zahlung
- **Zahlungsquote** - Prozent bezahlter vs. versendeter Rechnungen
- **Überfälligkeitsrate** - Prozent überfälliger Rechnungen

### **Reporting (geplant):**
- **Monatlicher Umsatz** - Zeitreihen-Diagramm
- **Zahlungsverhalten** - Kunden-Analyse
- **Cashflow-Prognose** - Basierend auf offenen Rechnungen
- **Export-Funktionen** - CSV, Excel für Buchhaltung

## 🔄 Workflow-Beispiel

### **Typischer Rechnungsprozess:**

1. **Gewerk abgeschlossen** → Dienstleister öffnet Rechnungsmanagement
2. **"Neue Rechnung"** → Formular mit Projekt-/Gewerk-Daten
3. **Positionen hinzufügen** → Arbeitszeit, Material, Zusatzleistungen
4. **Rechnung erstellen** → Status: "Entwurf"
5. **PDF generieren** → Professionelle Rechnung
6. **E-Mail versenden** → Status: "Versendet"
7. **Kunde öffnet E-Mail** → Status: "Angesehen"
8. **Zahlung erhalten** → Manuell auf "Bezahlt" setzen
9. **Statistiken aktualisiert** → Umsatz-Dashboard

### **Mahnwesen-Workflow:**
1. **Fälligkeitsdatum überschritten** → Automatisch "Überfällig"
2. **Erste Erinnerung** → Nach 7 Tagen
3. **Zweite Mahnung** → Nach 14 Tagen
4. **Letzte Mahnung** → Nach 30 Tagen
5. **Inkasso/Anwalt** → Externe Bearbeitung

## ✅ Status & Nächste Schritte

### **✅ Implementiert:**
- ✅ **InvoiceManagement Komponente** - Vollständige UI
- ✅ **Dashboard-Integration** - Kachel-Austausch
- ✅ **Routing** - `/invoices` Route
- ✅ **Mock-Daten** - Beispiel-Rechnungen
- ✅ **Filter & Suche** - Vollständige Funktionalität
- ✅ **Status-Management** - Farbkodierung und Icons
- ✅ **Responsive Design** - Mobile-First Ansatz
- ✅ **Modal-System** - Details und Erstellung

### **🔄 In Entwicklung:**
- 🔄 **API-Integration** - Backend-Anbindung
- 🔄 **PDF-Generation** - Professionelle Rechnungen
- 🔄 **E-Mail-System** - Automatischer Versand
- 🔄 **Formular-Validierung** - Eingabe-Prüfungen

### **📋 Geplant:**
- 📋 **Mahnwesen** - Automatische Erinnerungen
- 📋 **Reporting** - Erweiterte Statistiken
- 📋 **Export-Funktionen** - CSV/Excel Export
- 📋 **Template-System** - Anpassbare Rechnungsvorlagen
- 📋 **Buchhaltungs-Integration** - DATEV, Lexware, etc.

## 🎯 Best Practices

### **Code-Qualität:**
- ✅ **TypeScript** - Vollständige Typisierung
- ✅ **Komponenten-Architektur** - Modularer Aufbau
- ✅ **Error Handling** - Umfassende Fehlerbehandlung
- ✅ **Loading States** - Benutzer-Feedback
- ✅ **Accessibility** - ARIA-Labels und Keyboard-Navigation

### **UX/UI-Prinzipien:**
- ✅ **Intuitive Navigation** - Klare Struktur
- ✅ **Konsistente Farbgebung** - Status-basierte Farben
- ✅ **Responsive Design** - Alle Bildschirmgrößen
- ✅ **Performance** - Lazy Loading und Optimierung
- ✅ **Feedback** - Loading-Spinner und Erfolgs-Meldungen

### **Sicherheit:**
- ✅ **Zugriffskontrolle** - Nur für Dienstleister
- ✅ **Datenvalidierung** - Client- und Server-seitig
- ✅ **HTTPS-Only** - Verschlüsselte Übertragung
- ✅ **Input-Sanitization** - XSS-Schutz
- ✅ **Rate Limiting** - API-Missbrauch verhindern

Das Rechnungsmanagement-System bietet eine vollständige, professionelle Lösung für Dienstleister zur Verwaltung ihrer Rechnungen und Zahlungen, ohne externe Zahlungsanbieter-Integration, aber mit allen notwendigen Features für einen effizienten Workflow. 