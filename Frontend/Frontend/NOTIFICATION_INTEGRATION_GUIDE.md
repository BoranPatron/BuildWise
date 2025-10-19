# 🔔 Benachrichtigungssystem - Integrations-Anleitung

## Übersicht

Dieses System ermöglicht **Echtzeit-Benachrichtigungen** zwischen Bauträger und Dienstleister, wenn Nachrichten im "Fortschritt & Kommunikation" Tab gesendet werden.

## Funktionsweise

1. **Dienstleister** sendet Nachricht in `TradeDetailsModal` → Tab "Fortschritt & Kommunikation"
2. **Bauträger** sieht in `SimpleCostEstimateModal` → Tab "Kommunikation" blinkt + rotes Symbol mit Ping-Animation
3. **Bauträger** sendet Nachricht in `SimpleCostEstimateModal` → Tab "Kommunikation"
4. **Dienstleister** sieht in `TradeDetailsModal` → Tab "Fortschritt & Kommunikation" blinkt + rotes Symbol mit Ping-Animation

## Integration in SimpleCostEstimateModal (Bauträger)

### Schritt 1: Hook importieren und initialisieren

```tsx
import { useMessageNotifications } from '../hooks/useMessageNotifications';

export default function SimpleCostEstimateModal({ trade, ... }) {
  // ... bestehender Code ...

  // Benachrichtigungssystem initialisieren
  const {
    hasUnreadMessages,
    unreadCount,
    notificationBlink,
    markAsRead,
    sendMessage: sendNotification
  } = useMessageNotifications({
    tradeId: trade?.id || 0,
    userType: 'bautraeger',
    onNewMessage: (notification) => {
      console.log('📬 Neue Nachricht vom Dienstleister:', notification);
      // Optional: Toast-Benachrichtigung anzeigen
    }
  });

  // ... restlicher Code ...
}
```

### Schritt 2: Tab-Konfiguration anpassen

```tsx
const tabItems: TabItem[] = useMemo(() => {
  // ... bestehender Code ...
  
  return [
    {
      id: 'details',
      label: 'Übersicht',
      icon: Info,
      badge: undefined
    },
    {
      id: 'offers',
      label: 'Angebote',
      icon: FileText,
      badge: quotes.length > 0 ? quotes.length : undefined,
      disabled: false
    },
    {
      id: 'documents',
      label: 'Dokumente',
      icon: Download,
      badge: loadedDocuments.length > 0 ? loadedDocuments.length : undefined,
      disabled: false
    },
    {
      id: 'communication',
      label: 'Kommunikation',
      icon: MessageCircle,
      badge: hasUnreadMessages ? unreadCount : undefined,  // ✅ Ungelesene Nachrichten
      disabled: !acceptedQuote,
      urgent: hasUnreadMessages && notificationBlink  // ✅ Blink-Animation
    },
    {
      id: 'completion',
      label: 'Abnahme',
      icon: CheckCircle,
      badge: completionBadge,
      disabled: !acceptedQuote,
      urgent: invoiceUrgent
    }
  ];
}, [quotes, loadedDocuments.length, completionStatus, existingInvoice, hasUnreadMessages, unreadCount, notificationBlink]);
```

### Schritt 3: Benachrichtigungssymbol im Header hinzufügen

```tsx
{/* Enhanced Header */}
<div className="flex items-center justify-between p-6 border-b border-gray-600/30 flex-shrink-0">
  <div className="flex items-center gap-4">
    <div className="w-14 h-14 bg-gradient-to-br from-[#ffbd59] to-[#ffa726] rounded-xl flex items-center justify-center text-white font-bold shadow-lg">
      <Briefcase size={28} />
    </div>
    <div>
      <div className="flex items-center gap-3">
        <h2 className="text-2xl font-bold text-white leading-tight">
          {trade?.title || 'Gewerk Details'}
        </h2>
        
        {/* ✅ Benachrichtigungssymbol mit Ping-Animation */}
        {hasUnreadMessages && (
          <div className={`relative ${notificationBlink ? 'animate-pulse' : ''}`}>
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75"></div>
          </div>
        )}
      </div>
      {/* ... rest des Headers ... */}
    </div>
  </div>
  {/* ... rest des Headers ... */}
</div>
```

### Schritt 4: Tab-Klick Handler anpassen

```tsx
const handleTabClick = (tabId: string) => {
  setActiveTab(tabId);
  
  // ✅ Wenn Kommunikations-Tab geklickt wird, Benachrichtigungen als gelesen markieren
  if (tabId === 'communication' && hasUnreadMessages) {
    markAsRead();
  }
};

// Tab Navigation mit neuem Handler
<Tabs 
  tabs={tabItems} 
  activeTab={activeTab} 
  onTabChange={handleTabClick}  // ✅ Verwende den neuen Handler
  className="px-6 pt-4"
/>
```

### Schritt 5: Nachricht senden mit Benachrichtigung

```tsx
const sendMessage = async () => {
  if (!newMessage.trim() || !trade?.id) return;
  
  setCommunicationLoading(true);
  try {
    const { api } = await import('../api/api');
    const response = await api.post('/messages', {
      trade_id: trade.id,
      message: newMessage.trim(),
      sender_type: 'bautraeger',
      recipient_type: 'service_provider',
      recipient_id: acceptedQuote?.service_provider_id || acceptedQuote?.user_id
    });

    console.log('✅ Nachricht gesendet:', response.data);
    
    // ✅ Sende Benachrichtigung an Dienstleister
    sendNotification(newMessage.trim());
    
    setNewMessage('');
    
    // Nachrichten neu laden
    await loadMessages();
    
  } catch (error) {
    console.error('❌ Fehler beim Senden der Nachricht:', error);
    alert('Fehler beim Senden der Nachricht. Bitte versuchen Sie es erneut.');
  } finally {
    setCommunicationLoading(false);
  }
};
```

## Integration in TradeDetailsModal (Dienstleister)

### Schritt 1: Hook importieren und initialisieren

```tsx
import { useMessageNotifications } from '../hooks/useMessageNotifications';

export default function TradeDetailsModal({ trade, ... }) {
  // ... bestehender Code ...

  // Benachrichtigungssystem initialisieren
  const {
    hasUnreadMessages,
    unreadCount,
    notificationBlink,
    markAsRead,
    sendMessage: sendNotification
  } = useMessageNotifications({
    tradeId: trade?.id || 0,
    userType: 'dienstleister',
    onNewMessage: (notification) => {
      console.log('📬 Neue Nachricht vom Bauträger:', notification);
      // Optional: Toast-Benachrichtigung anzeigen
    }
  });

  // ... restlicher Code ...
}
```

### Schritt 2: Tab-Konfiguration anpassen

Die TradeDetailsModal verwendet bereits ein `builderTabs`-Array. Fügen Sie die Benachrichtigungslogik hinzu:

```tsx
const builderTabs: Array<{ key: BuilderTabKey; label: string; icon: React.ComponentType; badge?: string | number; urgent?: boolean }> = React.useMemo(() => {
  if (!isBautraegerUser) return [];
  const tabs: Array<{ key: BuilderTabKey; label: string; icon: React.ComponentType; badge?: string | number; urgent?: boolean }> = [
    { key: 'overview', label: 'Übersicht', icon: Eye },
    { key: 'quotes', label: totalQuotes ? `Angebote (${totalQuotes})` : 'Angebote', icon: Calculator },
    { key: 'documents', label: builderDocumentsCount ? `Dokumente (${builderDocumentsCount})` : 'Dokumente', icon: FileText },
    { 
      key: 'workflow', 
      label: 'Fortschritt & Kommunikation',  // ⚠️ Wichtig: Dieser Tab heißt "workflow"!
      icon: CheckSquare,
      badge: hasUnreadMessages ? unreadCount : undefined,  // ✅ Ungelesene Nachrichten
      urgent: hasUnreadMessages && notificationBlink  // ✅ Blink-Animation
    },
  ];
  if (hasInspectionInfo) {
    tabs.push({ key: 'inspection', label: 'Besichtigung', icon: Calendar });
  }
  return tabs;
}, [isBautraegerUser, totalQuotes, builderDocumentsCount, hasInspectionInfo, hasUnreadMessages, unreadCount, notificationBlink]);
```

### Schritt 3: Benachrichtigungssymbol im Header hinzufügen

```tsx
<div className="flex items-center gap-3 mb-1">
  <h2 className="text-xl font-bold text-white">{trade.title}</h2>
  
  {/* ✅ Benachrichtigungssymbol mit Ping-Animation */}
  {hasUnreadMessages && (
    <div className={`relative ${notificationBlink ? 'animate-pulse' : ''}`}>
      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
      <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75"></div>
    </div>
  )}
</div>
```

### Schritt 4: Tab-Klick Handler anpassen

```tsx
const handleTabClick = (tabKey: BuilderTabKey) => {
  setActiveBuilderTab(tabKey);
  
  // ✅ Wenn Workflow-Tab (Fortschritt & Kommunikation) geklickt wird, Benachrichtigungen als gelesen markieren
  if (tabKey === 'workflow' && hasUnreadMessages) {
    markAsRead();
  }
};

// In der Tab-Rendering-Logik den neuen Handler verwenden
<button
  key={tab.key}
  onClick={() => handleTabClick(tab.key)}  // ✅ Verwende den neuen Handler
  className={`
    flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 relative
    ${isActive ? 'bg-[#ffbd59] text-[#1a1a2e] shadow-lg' : 'bg-[#ffbd59]/10 text-gray-300 hover:bg-[#ffbd59]/20'}
    ${tab.urgent ? 'animate-pulse' : ''}  // ✅ Blink-Animation
  `}
>
  <Icon size={16} className={isActive ? 'text-[#1a1a2e]' : 'text-[#ffbd59]'} />
  {tab.label}
  {tab.badge && (
    <span className={`
      px-2 py-0.5 text-xs rounded-full font-semibold
      ${isActive ? 'bg-[#1a1a2e] text-[#ffbd59]' : 'bg-[#ffbd59] text-[#1a1a2e]'}
      ${tab.urgent ? 'animate-pulse' : ''}  // ✅ Badge blinkt auch
    `}>
      {tab.badge}
    </span>
  )}
</button>
```

### Schritt 5: Nachricht senden mit Benachrichtigung (in TradeProgress-Komponente)

Falls Sie die TradeProgress-Komponente verwenden, übergeben Sie `sendNotification` als Prop:

```tsx
<TradeProgress
  milestoneId={trade.id}
  currentProgress={currentProgress}
  onProgressChange={handleProgressChange}
  isBautraeger={isBautraegerUser}
  isServiceProvider={!isBautraegerUser && (acceptedQuote?.service_provider_id === user?.id)}
  completionStatus={completionStatus}
  onCompletionRequest={handleCompletionRequest}
  onCompletionResponse={handleCompletionResponse}
  onMessageSent={(message) => {
    sendNotification(message);  // ✅ Sende Benachrichtigung an Bauträger
  }}
/>
```

## CSS-Anpassungen (falls noch nicht vorhanden)

Stellen Sie sicher, dass die Tailwind-Klassen `animate-pulse` und `animate-ping` verfügbar sind:

```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}

@keyframes ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.animate-ping {
  animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite;
}
```

## Testing

1. Öffnen Sie `SimpleCostEstimateModal` als Bauträger
2. Öffnen Sie in einem anderen Tab/Fenster `TradeDetailsModal` als Dienstleister für dasselbe Trade
3. Senden Sie eine Nachricht als Dienstleister
4. Beobachten Sie, dass beim Bauträger der "Kommunikation" Tab blinkt und das rote Symbol erscheint
5. Klicken Sie auf den Tab - Benachrichtigung verschwindet
6. Senden Sie eine Nachricht als Bauträger
7. Beobachten Sie, dass beim Dienstleister der "Fortschritt & Kommunikation" Tab blinkt

## Wichtige Hinweise

- ✅ Das System funktioniert auch über mehrere Browser-Tabs hinweg
- ✅ Benachrichtigungen werden in LocalStorage gespeichert und bleiben nach Reload erhalten
- ✅ Alte Benachrichtigungen (>7 Tage) werden automatisch gelöscht
- ✅ Das System ist vollständig typsicher (TypeScript)
- ✅ Keine Backend-Integration erforderlich (Frontend-only Lösung)

## Troubleshooting

**Problem**: Benachrichtigungen werden nicht angezeigt
- Lösung: Überprüfen Sie die Browser-Konsole auf Fehler
- Lösung: Prüfen Sie ob `tradeId` korrekt übergeben wird
- Lösung: Prüfen Sie LocalStorage: `buildwise_message_notification_*`

**Problem**: Blink-Animation funktioniert nicht
- Lösung: Prüfen Sie ob `urgent` Property im Tab-Object gesetzt ist
- Lösung: Prüfen Sie Tailwind-Konfiguration für `animate-pulse`

**Problem**: Cross-Tab-Benachrichtigungen funktionieren nicht
- Lösung: Storage Events funktionieren nur zwischen verschiedenen Tabs der gleichen Domain
- Lösung: Innerhalb des gleichen Tabs werden Custom Events verwendet



