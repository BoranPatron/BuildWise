import { useState, useEffect, useCallback } from 'react';
import { notificationService, type MessageNotification } from '../services/notificationService';

interface UseMessageNotificationsProps {
  tradeId: number;
  userType: 'bautraeger' | 'dienstleister';
  onNewMessage?: (notification: MessageNotification) => void;
}

interface UseMessageNotificationsReturn {
  hasUnreadMessages: boolean;
  unreadCount: number;
  notificationBlink: boolean;
  markAsRead: () => void;
  sendMessage: (message: string) => void;
}

/**
 * Hook für Echtzeit-Benachrichtigungen
 * 
 * @param tradeId - Die ID des Trades
 * @param userType - Der Typ des aktuellen Benutzers ('bautraeger' oder 'dienstleister')
 * @param onNewMessage - Callback, der bei neuen Nachrichten aufgerufen wird
 * 
 * @returns {UseMessageNotificationsReturn} Benachrichtigungs-State und Funktionen
 */
export function useMessageNotifications({
  tradeId,
  userType,
  onNewMessage
}: UseMessageNotificationsProps): UseMessageNotificationsReturn {
  const [hasUnreadMessages, setHasUnreadMessages] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notificationBlink, setNotificationBlink] = useState(false);

  // Prüfe initial auf ungelesene Nachrichten
  useEffect(() => {
    const checkUnread = () => {
      const unread = notificationService.getUnreadNotifications(tradeId, userType);
      setUnreadCount(unread.length);
      setHasUnreadMessages(unread.length > 0);
    };

    checkUnread();
  }, [tradeId, userType]);

  // Registriere Listener für neue Nachrichten
  useEffect(() => {
    const cleanup = notificationService.onNewMessage((notification) => {
      console.log('🔔 Neue Nachricht empfangen:', notification);

      // Prüfe ob die Nachricht für dieses Trade ist
      if (notification.tradeId !== tradeId) {
        return;
      }

      // Prüfe ob die Nachricht vom anderen Nutzer kommt
      if (notification.sender === userType) {
        // Eigene Nachricht - ignorieren
        return;
      }

      // Neue Nachricht vom anderen Nutzer!
      console.log(`📬 Neue Nachricht für ${userType} in Trade ${tradeId}`);

      // Aktualisiere ungelesene Nachrichten
      const unread = notificationService.getUnreadNotifications(tradeId, userType);
      setUnreadCount(unread.length);
      setHasUnreadMessages(true);

      // Starte Blink-Animation
      setNotificationBlink(true);

      // Stoppe Blink-Animation nach 5 Sekunden
      setTimeout(() => {
        setNotificationBlink(false);
      }, 5000);

      // Rufe optionalen Callback auf
      if (onNewMessage) {
        onNewMessage(notification);
      }
    });

    return cleanup;
  }, [tradeId, userType, onNewMessage]);

  // Markiere Nachrichten als gelesen
  const markAsRead = useCallback(() => {
    notificationService.markAsRead(tradeId, userType);
    setHasUnreadMessages(false);
    setUnreadCount(0);
    setNotificationBlink(false);
    console.log(`✅ Nachrichten als gelesen markiert für ${userType} in Trade ${tradeId}`);
  }, [tradeId, userType]);

  // Sende eine neue Nachricht
  const sendMessage = useCallback((message: string) => {
    notificationService.sendMessage(tradeId, userType, message);
    console.log(`📤 Nachricht gesendet von ${userType} in Trade ${tradeId}`);
  }, [tradeId, userType]);

  return {
    hasUnreadMessages,
    unreadCount,
    notificationBlink,
    markAsRead,
    sendMessage
  };
}


