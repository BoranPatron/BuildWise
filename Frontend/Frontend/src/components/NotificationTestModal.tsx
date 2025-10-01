import React, { useState } from 'react';
import { 
  X, 
  Mail,
  CheckSquare,
  Clock,
  Bell
} from 'lucide-react';

interface Message {
  id: number;
  text: string;
  sender: string;
  timestamp: string;
}

export default function NotificationTestModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'communication'>('overview');
  
  // Benachrichtigungssystem States
  const [hasUnreadMessages, setHasUnreadMessages] = useState(false);
  const [notificationBlink, setNotificationBlink] = useState(false);
  const [messageInput, setMessageInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);

  // Benachrichtigungssystem Funktionen
  const triggerNotification = () => {
    setHasUnreadMessages(true);
    setNotificationBlink(true);
    
    // Blink-Animation nach 3 Sekunden stoppen
    setTimeout(() => {
      setNotificationBlink(false);
    }, 3000);
  };

  const handleTabClick = (tabKey: 'overview' | 'communication') => {
    setActiveTab(tabKey);
    
    // Wenn der Kommunikations-Tab geklickt wird, Benachrichtigung zurücksetzen
    if (tabKey === 'communication') {
      setHasUnreadMessages(false);
      setNotificationBlink(false);
    }
  };

  const handleMessageSent = () => {
    if (messageInput.trim()) {
      // Neue Nachricht hinzufügen
      const newMessage: Message = {
        id: Date.now(),
        text: messageInput.trim(),
        sender: 'Test User',
        timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, newMessage]);
      setMessageInput('');
      
      // Benachrichtigung triggern
      triggerNotification();
    }
  };

  const testNotification = () => {
    triggerNotification();
  };

  if (!isOpen) {
    return (
      <div className="p-4">
        <h1 className="text-2xl font-bold text-white mb-4">
          Benachrichtigungstest
        </h1>
        <button
          onClick={() => setIsOpen(true)}
          className="px-6 py-3 bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold rounded-lg hover:shadow-lg transition-all duration-200"
        >
          Modal öffnen
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gradient-to-br from-[#1a1a2e] to-[#2c3539] rounded-2xl shadow-2xl border border-gray-600/30 max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-600/30">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-[#ffbd59] to-[#ffa726] rounded-xl flex items-center justify-center text-white font-bold shadow-lg">
              <Bell size={24} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-bold text-white">
                  Benachrichtigungstest
                </h2>
                
                {/* Benachrichtigungssymbol */}
                {hasUnreadMessages && (
                  <div className={`relative ${notificationBlink ? 'animate-pulse' : ''}`}>
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75"></div>
                  </div>
                )}
              </div>
              <p className="text-gray-400 text-sm">
                Test der Benachrichtigungsfunktionalität
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-gray-600/30 rounded-lg transition-colors"
          >
            <X size={24} className="text-gray-400" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 p-2 bg-[#111827] border-b border-gray-700/40">
          <button
            onClick={() => handleTabClick('overview')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === 'overview' 
                ? 'bg-[#ffbd59] text-[#1a1a2e] shadow-lg' 
                : 'bg-[#ffbd59]/10 text-gray-300 hover:bg-[#ffbd59]/20'
            }`}
          >
            <CheckSquare size={16} />
            Übersicht
          </button>
          <button
            onClick={() => handleTabClick('communication')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 relative ${
              activeTab === 'communication' 
                ? 'bg-[#ffbd59] text-[#1a1a2e] shadow-lg' 
                : 'bg-[#ffbd59]/10 text-gray-300 hover:bg-[#ffbd59]/20'
            } ${activeTab === 'communication' && hasUnreadMessages && notificationBlink ? 'animate-pulse' : ''}`}
          >
            <Mail size={16} />
            Fortschritt & Kommunikation
            {hasUnreadMessages && activeTab !== 'communication' && (
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
            )}
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <CheckSquare size={18} className="text-[#ffbd59]" />
                Übersicht
              </h3>

              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h4 className="text-md font-medium text-white mb-4 flex items-center gap-2">
                  <Clock size={16} className="text-[#ffbd59]" />
                  Test-Bereich
                </h4>
                
                <div className="space-y-4">
                  <p className="text-gray-300">
                    Klicken Sie auf den Button unten, um eine Test-Benachrichtigung zu triggern.
                    Der "Fortschritt & Kommunikation" Tab sollte dann blinken und das rote Symbol erscheinen.
                  </p>
                  
                  <button
                    onClick={testNotification}
                    className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-200 flex items-center gap-2"
                  >
                    <Bell size={16} />
                    Test-Benachrichtigung senden
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'communication' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <CheckSquare size={18} className="text-[#ffbd59]" />
                Fortschritt & Kommunikation
              </h3>

              {/* Fortschrittsanzeige */}
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h4 className="text-md font-medium text-white mb-4 flex items-center gap-2">
                  <Clock size={16} className="text-[#ffbd59]" />
                  Projektfortschritt
                </h4>
                
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-gray-400">Aktueller Fortschritt</span>
                    <span className="text-white font-bold">75%</span>
                  </div>
                  <div className="w-full bg-gray-600/30 rounded-full h-3">
                    <div 
                      className="bg-gradient-to-r from-[#ffbd59] to-[#ffa726] h-3 rounded-full transition-all duration-500"
                      style={{ width: '75%' }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Kommunikationsbereich */}
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h4 className="text-md font-medium text-white mb-4 flex items-center gap-2">
                  <Mail size={16} className="text-[#ffbd59]" />
                  Nachrichten
                </h4>
                
                {/* Nachrichtenliste */}
                <div className="bg-[#111827]/50 rounded-lg p-4 min-h-[200px] max-h-[300px] overflow-y-auto mb-4">
                  {messages.length === 0 ? (
                    <div className="text-center text-gray-400 text-sm py-8">
                      Keine Nachrichten vorhanden
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {messages.map((message) => (
                        <div key={message.id} className="bg-[#1a1a2e]/50 rounded-lg p-3 border border-gray-600/30">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-[#ffbd59]">{message.sender}</span>
                            <span className="text-xs text-gray-400">{message.timestamp}</span>
                          </div>
                          <p className="text-white text-sm">{message.text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Nachrichteneingabe */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleMessageSent();
                      }
                    }}
                    placeholder="Nachricht eingeben..."
                    className="flex-1 px-3 py-2 bg-[#111827]/50 border border-gray-600/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#ffbd59]/50"
                  />
                  <button
                    onClick={handleMessageSent}
                    disabled={!messageInput.trim()}
                    className="px-4 py-2 bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold rounded-lg hover:shadow-lg transition-all duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Mail size={16} />
                    Senden
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

