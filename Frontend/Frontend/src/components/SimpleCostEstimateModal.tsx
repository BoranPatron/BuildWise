import React, { useState, useEffect } from 'react';
import { 
  X, 
  Calculator,
  Mail,
  CheckSquare,
  Clock,
  AlertTriangle,
  User,
  Phone,
  Building
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SimpleCostEstimateModalProps {
  isOpen: boolean;
  onClose: () => void;
  tradeId?: number;
  tradeTitle?: string;
  projectId?: number;
}

interface Message {
  id: number;
  text: string;
  sender: string;
  timestamp: string;
}

export default function SimpleCostEstimateModal({ 
  isOpen, 
  onClose, 
  tradeId,
  tradeTitle,
  projectId 
}: SimpleCostEstimateModalProps) {
  const { user, isBautraeger } = useAuth();
  const isBautraegerUser = isBautraeger();

  // States für Kostenschätzung
  const [laborCost, setLaborCost] = useState<number>(0);
  const [materialCost, setMaterialCost] = useState<number>(0);
  const [overheadCost, setOverheadCost] = useState<number>(0);
  const [totalCost, setTotalCost] = useState<number>(0);
  const [notes, setNotes] = useState<string>('');

  // Benachrichtigungssystem States
  const [hasUnreadMessages, setHasUnreadMessages] = useState(false);
  const [notificationBlink, setNotificationBlink] = useState(false);
  const [messageInput, setMessageInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);

  // Tab Management
  const [activeTab, setActiveTab] = useState<'estimate' | 'communication'>('estimate');

  // Berechne Gesamtkosten automatisch
  useEffect(() => {
    setTotalCost(laborCost + materialCost + overheadCost);
  }, [laborCost, materialCost, overheadCost]);

  // Benachrichtigungssystem Funktionen
  const triggerNotification = () => {
    setHasUnreadMessages(true);
    setNotificationBlink(true);
    
    // Blink-Animation nach 3 Sekunden stoppen
    setTimeout(() => {
      setNotificationBlink(false);
    }, 3000);
  };

  const handleTabClick = (tabKey: 'estimate' | 'communication') => {
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
        sender: user?.name || 'Sie',
        timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, newMessage]);
      setMessageInput('');
      
      // Benachrichtigung triggern
      triggerNotification();
    }
  };

  const handleSaveEstimate = () => {
    // Hier würde normalerweise die API-Call für das Speichern der Kostenschätzung erfolgen
    console.log('Kostenschätzung speichern:', {
      tradeId,
      laborCost,
      materialCost,
      overheadCost,
      totalCost,
      notes
    });
    
    // Nach dem Speichern eine Nachricht senden
    const saveMessage: Message = {
      id: Date.now(),
      text: `Kostenschätzung gespeichert: ${totalCost.toLocaleString('de-DE')} €`,
      sender: user?.name || 'System',
      timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
    };
    
    setMessages(prev => [...prev, saveMessage]);
    triggerNotification();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gradient-to-br from-[#1a1a2e] to-[#2c3539] rounded-2xl shadow-2xl border border-gray-600/30 max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-600/30">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-[#ffbd59] to-[#ffa726] rounded-xl flex items-center justify-center text-white font-bold shadow-lg">
              <Calculator size={24} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-bold text-white">
                  Kostenschätzung - {tradeTitle || 'Gewerk'}
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
                {isBautraegerUser ? 'Bauträger' : 'Dienstleister'} - Kostenschätzung erstellen
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-600/30 rounded-lg transition-colors"
          >
            <X size={24} className="text-gray-400" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 p-2 bg-[#111827] border-b border-gray-700/40">
          <button
            onClick={() => handleTabClick('estimate')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === 'estimate' 
                ? 'bg-[#ffbd59] text-[#1a1a2e] shadow-lg' 
                : 'bg-[#ffbd59]/10 text-gray-300 hover:bg-[#ffbd59]/20'
            }`}
          >
            <Calculator size={16} />
            Kostenschätzung
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
          {activeTab === 'estimate' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Calculator size={18} className="text-[#ffbd59]" />
                Kostenschätzung Details
              </h3>

              {/* Kostenfelder */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-4 border border-gray-600/30">
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Arbeitskosten (€)
                  </label>
                  <input
                    type="number"
                    value={laborCost}
                    onChange={(e) => setLaborCost(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-[#111827]/50 border border-gray-600/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#ffbd59]/50"
                    placeholder="0.00"
                  />
                </div>

                <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-4 border border-gray-600/30">
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Materialkosten (€)
                  </label>
                  <input
                    type="number"
                    value={materialCost}
                    onChange={(e) => setMaterialCost(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-[#111827]/50 border border-gray-600/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#ffbd59]/50"
                    placeholder="0.00"
                  />
                </div>

                <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-4 border border-gray-600/30">
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Gemeinkosten (€)
                  </label>
                  <input
                    type="number"
                    value={overheadCost}
                    onChange={(e) => setOverheadCost(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-[#111827]/50 border border-gray-600/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#ffbd59]/50"
                    placeholder="0.00"
                  />
                </div>
              </div>

              {/* Gesamtkosten */}
              <div className="bg-gradient-to-br from-[#ffbd59]/10 to-[#ffa726]/10 rounded-xl p-6 border border-[#ffbd59]/30">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-semibold text-[#ffbd59]">Gesamtkosten</h4>
                  <div className="text-2xl font-bold text-white">
                    {totalCost.toLocaleString('de-DE')} €
                  </div>
                </div>
              </div>

              {/* Notizen */}
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-4 border border-gray-600/30">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Notizen zur Kostenschätzung
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 bg-[#111827]/50 border border-gray-600/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#ffbd59]/50 resize-none"
                  placeholder="Zusätzliche Informationen zur Kostenschätzung..."
                />
              </div>

              {/* Speichern Button */}
              <div className="flex justify-end">
                <button
                  onClick={handleSaveEstimate}
                  className="px-6 py-3 bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold rounded-lg hover:shadow-lg transition-all duration-200 flex items-center gap-2"
                >
                  <Calculator size={20} />
                  Kostenschätzung speichern
                </button>
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

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-400">Planung abgeschlossen</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-[#ffbd59] rounded-full"></div>
                    <span className="text-gray-400">In Bearbeitung</span>
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


