/**
 * Notification Service für Echtzeit-Benachrichtigungen zwischen Bauträger und Dienstleister
 * 
 * Funktionsweise:
 * 1. Wenn eine Nachricht gesendet wird, wird sie in LocalStorage gespeichert
 * 2. Ein Event wird ausgelöst, das andere Tabs/Komponenten benachrichtigt
 * 3. Die Empfänger-Komponente reagiert auf das Event und zeigt die Benachrichtigung an
 */

export interface MessageNotification {
  id: string;
  tradeId: number;
  sender: 'bautraeger' | 'dienstleister';
  message: string;
  timestamp: string;
  read: boolean;
}

const NOTIFICATION_KEY_PREFIX = 'buildwise_message_notification_';
const NOTIFICATION_EVENT = 'buildwise_new_message';

class NotificationService {
  /**
   * Sende eine neue Nachricht und triggere Benachrichtigung
   */
  sendMessage(tradeId: number, sender: 'bautraeger' | 'dienstleister', message: string): void {
    const notification: MessageNotification = {
      id: `${tradeId}_${Date.now()}`,
      tradeId,
      sender,
      message,
      timestamp: new Date().toISOString(),
      read: false
    };

    // Speichere in LocalStorage
    const key = `${NOTIFICATION_KEY_PREFIX}${tradeId}`;
    const existing = this.getNotifications(tradeId);
    existing.push(notification);
    localStorage.setItem(key, JSON.stringify(existing));

    // Triggere Event für andere Tabs/Komponenten
    window.dispatchEvent(new CustomEvent(NOTIFICATION_EVENT, {
      detail: notification
    }));

    // Triggere auch Storage Event für andere Browser-Tabs
    window.dispatchEvent(new StorageEvent('storage', {
      key,
      newValue: JSON.stringify(existing),
      url: window.location.href
    }));

    console.log('📨 Nachricht gesendet:', notification);
  }

  /**
   * Hole alle Benachrichtigungen für ein Trade
   */
  getNotifications(tradeId: number): MessageNotification[] {
    const key = `${NOTIFICATION_KEY_PREFIX}${tradeId}`;
    const stored = localStorage.getItem(key);
    
    if (!stored) return [];
    
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.error('Fehler beim Parsen der Benachrichtigungen:', e);
      return [];
    }
  }

  /**
   * Hole ungelesene Benachrichtigungen für ein Trade und einen Empfänger
   */
  getUnreadNotifications(tradeId: number, recipient: 'bautraeger' | 'dienstleister'): MessageNotification[] {
    const all = this.getNotifications(tradeId);
    
    // Filtere Nachrichten, die vom anderen Nutzer gesendet wurden und noch nicht gelesen sind
    const sender = recipient === 'bautraeger' ? 'dienstleister' : 'bautraeger';
    return all.filter(n => n.sender === sender && !n.read);
  }

  /**
   * Markiere alle Benachrichtigungen als gelesen
   */
  markAsRead(tradeId: number, recipient: 'bautraeger' | 'dienstleister'): void {
    const all = this.getNotifications(tradeId);
    const sender = recipient === 'bautraeger' ? 'dienstleister' : 'bautraeger';
    
    // Markiere alle Nachrichten vom anderen Nutzer als gelesen
    const updated = all.map(n => {
      if (n.sender === sender && !n.read) {
        return { ...n, read: true };
      }
      return n;
    });

    const key = `${NOTIFICATION_KEY_PREFIX}${tradeId}`;
    localStorage.setItem(key, JSON.stringify(updated));

    console.log('✅ Benachrichtigungen als gelesen markiert für Trade:', tradeId);
  }

  /**
   * Registriere einen Listener für neue Nachrichten
   */
  onNewMessage(callback: (notification: MessageNotification) => void): () => void {
    const handler = (event: Event) => {
      const customEvent = event as CustomEvent<MessageNotification>;
      callback(customEvent.detail);
    };

    window.addEventListener(NOTIFICATION_EVENT, handler);

    // Auch Storage Events für Cross-Tab-Kommunikation
    const storageHandler = (event: StorageEvent) => {
      if (event.key?.startsWith(NOTIFICATION_KEY_PREFIX) && event.newValue) {
        try {
          const notifications: MessageNotification[] = JSON.parse(event.newValue);
          const latest = notifications[notifications.length - 1];
          if (latest) {
            callback(latest);
          }
        } catch (e) {
          console.error('Fehler beim Parsen der Storage-Benachrichtigung:', e);
        }
      }
    };

    window.addEventListener('storage', storageHandler);

    // Cleanup-Funktion
    return () => {
      window.removeEventListener(NOTIFICATION_EVENT, handler);
      window.removeEventListener('storage', storageHandler);
    };
  }

  /**
   * Lösche alle Benachrichtigungen für ein Trade
   */
  clearNotifications(tradeId: number): void {
    const key = `${NOTIFICATION_KEY_PREFIX}${tradeId}`;
    localStorage.removeItem(key);
    console.log('🗑️ Benachrichtigungen gelöscht für Trade:', tradeId);
  }

  /**
   * Lösche alte Benachrichtigungen (älter als 7 Tage)
   */
  cleanupOldNotifications(): void {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    // Durchlaufe alle LocalStorage-Keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      
      if (key?.startsWith(NOTIFICATION_KEY_PREFIX)) {
        const stored = localStorage.getItem(key);
        if (!stored) continue;

        try {
          const notifications: MessageNotification[] = JSON.parse(stored);
          const filtered = notifications.filter(n => {
            const timestamp = new Date(n.timestamp);
            return timestamp > sevenDaysAgo;
          });

          if (filtered.length === 0) {
            localStorage.removeItem(key);
          } else if (filtered.length !== notifications.length) {
            localStorage.setItem(key, JSON.stringify(filtered));
          }
        } catch (e) {
          console.error('Fehler beim Bereinigen der Benachrichtigungen:', e);
        }
      }
    }

    console.log('🧹 Alte Benachrichtigungen bereinigt');
  }
}

// Singleton-Instanz
export const notificationService = new NotificationService();

// Cleanup alte Benachrichtigungen beim Laden
if (typeof window !== 'undefined') {
  notificationService.cleanupOldNotifications();
}



