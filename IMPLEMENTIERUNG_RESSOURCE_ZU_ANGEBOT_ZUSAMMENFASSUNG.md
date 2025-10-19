# Ressource-zu-Angebot Workflow - Implementierungszusammenfassung

## ✅ Implementierte Backend-Komponenten

### 1. Neue API-Endpunkte (`app/api/resources.py`)

#### GET /api/v1/resources/allocations/my-pending
Holt alle wartenden Ressourcen-Zuweisungen für den aktuellen Dienstleister.
- Status: `PRE_SELECTED`
- Mit Resource und Trade Details

#### POST /api/v1/resources/allocations/{allocation_id}/submit-quote
Erstellt ein Angebot aus einer Ressourcen-Zuordnung.
- **Request Body**:
  ```json
  {
    "title": "string",
    "description": "string",
    "labor_cost": number,
    "material_cost": number,
    "overhead_cost": number,
    "total_amount": number,
    "currency": "EUR",
    "estimated_duration": number,
    "start_date": "2025-01-15",
    "notes": "string"
  }
  ```
- **Aktionen**:
  - Erstellt neues Quote mit status='submitted'
  - Setzt ResourceAllocation status auf `OFFER_SUBMITTED`
  - Setzt Resource status auf `ALLOCATED`
  - Sendet Benachrichtigung an Bauträger
- **Transaktionssicherheit**: Rollback bei Fehlern

#### POST /api/v1/resources/allocations/{allocation_id}/reject
Lehnt eine Ressourcen-Zuordnung ab.
- **Request Body**:
  ```json
  {
    "rejection_reason": "string"
  }
  ```
- **Aktionen**:
  - Setzt ResourceAllocation status auf `REJECTED`
  - Setzt Resource status zurück auf `AVAILABLE`
  - Speichert Ablehnungsgrund

### 2. Benachrichtigungssystem (`app/services/notification_service.py`)

Die Benachrichtigung wird automatisch erstellt bei:
- Ressourcen-Zuordnung (`RESOURCE_ALLOCATED`) - bereits implementiert
- Angebots-Einreichung (`QUOTE_SUBMITTED`) - bereits implementiert

## ✅ Implementierte Frontend-Komponenten

### 1. ResourceService API (`Frontend/src/api/resourceService.ts`)

Neue Methoden:
```typescript
// Hole wartende Zuordnungen
async getMyPendingAllocations(): Promise<ResourceAllocation[]>

// Angebot aus Allocation erstellen  
async submitQuoteFromAllocation(
  allocationId: number,
  quoteData: SubmitQuoteFromAllocationData
): Promise<Response>

// Allocation ablehnen
async rejectAllocation(
  allocationId: number,
  rejectionReason: string
): Promise<Response>
```

## 🔄 Noch zu implementieren

### Frontend-Komponenten

#### 1. ResourceManagementDashboard erweitern

**Pendente Allocations Section hinzufügen**:
```tsx
// Nach Stats, vor Ressourcen-Liste einfügen

{/* Pendente Angebotsanfragen */}
{pendingAllocations.length > 0 && (
  <div className="bg-[#ffbd59]/10 border border-[#ffbd59]/30 rounded-lg p-6">
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <AlertCircle className="w-6 h-6 text-[#ffbd59]" />
        <div>
          <h2 className="text-xl font-bold text-white">
            Aktion erforderlich
          </h2>
          <p className="text-gray-300 text-sm">
            {pendingAllocations.length} Bauträger {pendingAllocations.length === 1 ? 'hat' : 'haben'} Ihre Ressourcen für Ausschreibungen ausgewählt
          </p>
        </div>
      </div>
      <span className="px-3 py-1 bg-red-500 text-white rounded-full text-sm font-bold">
        {pendingAllocations.length}
      </span>
    </div>

    <div className="space-y-3">
      {pendingAllocations.map((allocation) => (
        <div key={allocation.id} className="bg-[#2a2a2a] rounded-lg p-4 border border-gray-700">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white mb-1">
                {allocation.trade?.title || 'Ausschreibung'}
              </h3>
              <p className="text-gray-400 text-sm">
                Projekt: {allocation.trade?.project?.name || 'Unbekannt'}
              </p>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                <span className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  {allocation.allocated_person_count} Personen
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {dayjs(allocation.allocated_start_date).format('DD.MM.YY')} - 
                  {dayjs(allocation.allocated_end_date).format('DD.MM.YY')}
                </span>
              </div>
            </div>
            <span className="px-3 py-1 bg-yellow-500/20 text-yellow-300 rounded-full text-xs font-medium">
              Wartet auf Angebot
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => handleSubmitQuote(allocation)}
              className="flex-1 px-4 py-2 bg-[#ffbd59] text-black rounded-lg hover:bg-[#f59e0b] transition-colors font-medium flex items-center justify-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Angebot abgeben
            </button>
            <button
              onClick={() => handleRejectAllocation(allocation)}
              className="flex-1 px-4 py-2 bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg hover:bg-red-500/30 transition-colors font-medium flex items-center justify-center gap-2"
            >
              <X className="w-4 h-4" />
              Ablehnen
            </button>
          </div>
        </div>
      ))}
    </div>
  </div>
)}
```

**State Management**:
```typescript
const [pendingAllocations, setPendingAllocations] = useState<ResourceAllocation[]>([]);
const [showQuoteModal, setShowQuoteModal] = useState(false);
const [selectedAllocation, setSelectedAllocation] = useState<ResourceAllocation | null>(null);
const [showRejectModal, setShowRejectModal] = useState(false);

// Lade pendente Allocations
useEffect(() => {
  loadPendingAllocations();
}, [user?.id]);

const loadPendingAllocations = async () => {
  try {
    const data = await resourceService.getMyPendingAllocations();
    console.log('Pending allocations:', data);
    setPendingAllocations(data);
  } catch (error) {
    console.error('Error loading pending allocations:', error);
  }
};
```

**Handler-Funktionen**:
```typescript
const handleSubmitQuote = (allocation: ResourceAllocation) => {
  setSelectedAllocation(allocation);
  setShowQuoteModal(true);
};

const handleRejectAllocation = (allocation: ResourceAllocation) => {
  setSelectedAllocation(allocation);
  setShowRejectModal(true);
};

const submitQuote = async (quoteData: SubmitQuoteFromAllocationData) => {
  if (!selectedAllocation) return;
  
  try {
    await resourceService.submitQuoteFromAllocation(
      selectedAllocation.id!,
      quoteData
    );
    
    // Erfolg
    setShowQuoteModal(false);
    setSelectedAllocation(null);
    
    // Reload
    await loadPendingAllocations();
    await loadResources();
    
    // Notification
    alert('✅ Angebot erfolgreich eingereicht!');
  } catch (error) {
    console.error('Error submitting quote:', error);
    alert('❌ Fehler beim Einreichen des Angebots');
  }
};

const rejectAllocation = async (reason: string) => {
  if (!selectedAllocation) return;
  
  try {
    await resourceService.rejectAllocation(
      selectedAllocation.id!,
      reason
    );
    
    // Erfolg
    setShowRejectModal(false);
    setSelectedAllocation(null);
    
    // Reload
    await loadPendingAllocations();
    await loadResources();
    
    // Notification
    alert('✅ Zuordnung erfolgreich abgelehnt');
  } catch (error) {
    console.error('Error rejecting allocation:', error);
    alert('❌ Fehler beim Ablehnen der Zuordnung');
  }
};
```

#### 2. Angebots-Modal erstellen

Erstelle `ResourceQuoteModal.tsx`:
```tsx
interface ResourceQuoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  allocation: ResourceAllocation | null;
  onSubmit: (quoteData: SubmitQuoteFromAllocationData) => Promise<void>;
}

const ResourceQuoteModal: React.FC<ResourceQuoteModalProps> = ({
  isOpen,
  onClose,
  allocation,
  onSubmit
}) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    labor_cost: 0,
    material_cost: 0,
    overhead_cost: 0,
    total_amount: 0,
    currency: 'EUR',
    estimated_duration: 0,
    start_date: '',
    notes: ''
  });

  // Auto-berechne total_amount
  useEffect(() => {
    const total = (formData.labor_cost || 0) + 
                  (formData.material_cost || 0) + 
                  (formData.overhead_cost || 0);
    setFormData(prev => ({ ...prev, total_amount: total }));
  }, [formData.labor_cost, formData.material_cost, formData.overhead_cost]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  if (!isOpen || !allocation) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1a1a2e] rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Angebot abgeben</h2>
          <p className="text-gray-400 mt-1">
            {allocation.trade?.title}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Titel */}
          <div>
            <label className="block text-sm text-gray-300 mb-2">Titel *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full bg-[#2a2a2a] text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#ffbd59]"
              placeholder="z.B. Maurerarbeiten Neubau"
            />
          </div>

          {/* Beschreibung */}
          <div>
            <label className="block text-sm text-gray-300 mb-2">Beschreibung</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full bg-[#2a2a2a] text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#ffbd59]"
              placeholder="Detaillierte Beschreibung..."
            />
          </div>

          {/* Kosten */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-300 mb-2">Arbeitskosten</label>
              <input
                type="number"
                step="0.01"
                value={formData.labor_cost}
                onChange={(e) => setFormData(prev => ({ ...prev, labor_cost: parseFloat(e.target.value) || 0 }))}
                className="w-full bg-[#2a2a2a] text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#ffbd59]"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-2">Materialkosten</label>
              <input
                type="number"
                step="0.01"
                value={formData.material_cost}
                onChange={(e) => setFormData(prev => ({ ...prev, material_cost: parseFloat(e.target.value) || 0 }))}
                className="w-full bg-[#2a2a2a] text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#ffbd59]"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-2">Nebenkosten</label>
              <input
                type="number"
                step="0.01"
                value={formData.overhead_cost}
                onChange={(e) => setFormData(prev => ({ ...prev, overhead_cost: parseFloat(e.target.value) || 0 }))}
                className="w-full bg-[#2a2a2a] text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#ffbd59]"
              />
            </div>
          </div>

          {/* Gesamtbetrag */}
          <div className="bg-[#ffbd59]/10 border border-[#ffbd59]/30 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-300 font-medium">Gesamtbetrag:</span>
              <span className="text-2xl font-bold text-[#ffbd59]">
                {formData.total_amount.toLocaleString('de-DE', { style: 'currency', currency: formData.currency })}
              </span>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
            >
              Abbrechen
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-[#ffbd59] text-black rounded-lg hover:bg-[#f59e0b] transition-colors font-medium"
            >
              Angebot einreichen
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

#### 3. Ablehnungs-Modal erstellen

Erstelle `ResourceRejectModal.tsx` (analog zur Quote-Modal, aber einfacher mit nur Textfeld für Grund).

#### 4. Notification Tab erweitern

In `NotificationTab.tsx` oder entsprechender Komponente:

```tsx
// Spezielle Darstellung für RESOURCE_ALLOCATED Benachrichtigungen
{notification.type === 'RESOURCE_ALLOCATED' && (
  <div className="bg-[#ffbd59]/10 border border-[#ffbd59]/30 rounded-lg p-4">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-[#ffbd59]" />
        <div>
          <h4 className="text-white font-semibold">{notification.title}</h4>
          <p className="text-gray-300 text-sm">{notification.message}</p>
        </div>
      </div>
      <span className="px-2 py-1 bg-red-500 text-white rounded-full text-xs font-bold">
        Neu
      </span>
    </div>
    <button
      onClick={() => router.push('/resources')}
      className="w-full px-4 py-2 bg-[#ffbd59] text-black rounded-lg hover:bg-[#f59e0b] transition-colors font-medium flex items-center justify-center gap-2"
    >
      <Users className="w-4 h-4" />
      Zur Ressourcenverwaltung
    </button>
  </div>
)}
```

#### 5. TradeDetailsModal Filter

Im TradeDetailsModal die Ressourcen-Anzeige filtern:

```tsx
// In der Funktion die Ressourcen lädt
const allocatedResources = allocations.filter(
  allocation => allocation.allocation_status !== 'offer_submitted' && 
                allocation.allocation_status !== 'accepted'
);

// Nur gefilterte Ressourcen anzeigen
{allocatedResources.map((allocation) => (
  // ... Ressourcen-Card
))}
```

## 🧪 Testing-Checkliste

- [ ] Bauträger ordnet Ressource zu → Dienstleister erhält Benachrichtigung
- [ ] Dienstleister sieht Ressource unter "Angezogen" im Dashboard
- [ ] "Aktion erforderlich" Banner wird angezeigt
- [ ] Angebots-Modal öffnet sich korrekt
- [ ] Angebot wird erstellt und Status aktualisiert
- [ ] Ressource verschwindet aus "Zugeordnete Ressourcen" beim Bauträger
- [ ] Angebot erscheint beim Bauträger unter Angebote
- [ ] Ablehnung funktioniert und setzt Status zurück

## 📝 Nächste Schritte

1. ResourceManagementDashboard um Pending Allocations Section erweitern
2. ResourceQuoteModal und ResourceRejectModal erstellen
3. NotificationTab um RESOURCE_ALLOCATED Handler erweitern
4. TradeDetailsModal Filter für offer_submitted implementieren
5. End-to-End Testing durchführen

