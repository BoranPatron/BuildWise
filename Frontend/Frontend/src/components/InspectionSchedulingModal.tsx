import React, { useState, useEffect } from 'react';
import { X, Calendar, MapPin, User, Phone, Mail, Clock, FileText, Download } from 'lucide-react';
import { getApiBaseUrl } from '../api/api';

interface InspectionSchedulingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: InspectionFormData) => void;
  tradeTitle: string;
  selectedQuoteIds: number[];
  projectName?: string;
}

export interface InspectionFormData {
  // Schritt 1: Grunddaten
  title: string;
  description: string;
  scheduled_date: string;
  scheduled_time_start: string;
  scheduled_time_end: string;
  duration_minutes: number;
  
  // Schritt 2: Ortsangaben
  location_address: string;
  location_notes: string;
  additional_location_info: string;
  parking_info: string;
  access_instructions: string;
  
  // Schritt 3: Kontaktinformationen
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  alternative_contact_person: string;
  alternative_contact_phone: string;
  preparation_notes: string;
  special_requirements: string;
}

const InspectionSchedulingModal: React.FC<InspectionSchedulingModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  tradeTitle,
  selectedQuoteIds,
  projectName
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [userDataLoaded, setUserDataLoaded] = useState(false);
  const [formData, setFormData] = useState<InspectionFormData>({
    title: `Besichtigung - ${tradeTitle}`,
    description: '',
    scheduled_date: '',
    scheduled_time_start: '09:00',
    scheduled_time_end: '11:00',
    duration_minutes: 120,
    location_address: '',
    location_notes: '',
    additional_location_info: '',
    parking_info: '',
    access_instructions: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    alternative_contact_person: '',
    alternative_contact_phone: '',
    preparation_notes: '',
    special_requirements: ''
  });

  // Lade Benutzerdaten beim Öffnen des Modals
  useEffect(() => {
    if (isOpen && !userDataLoaded) {
      loadUserData();
    }
  }, [isOpen, userDataLoaded]);

  const loadUserData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.warn('Kein Authentifizierungstoken verfügbar');
        setUserDataLoaded(true);
        return;
      }

      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/users/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        // Automatisches Befüllen der Kontaktdaten
        const fullName = `${userData.first_name} ${userData.last_name}`.trim();
        setFormData(prev => ({
          ...prev,
          contact_person: fullName,
          contact_phone: userData.phone || '',
          contact_email: userData.email || ''
        }));
        setUserDataLoaded(true);
      } else {
        console.warn('Fehler beim Laden der Benutzerdaten:', response.status);
        setUserDataLoaded(true);
      }
    } catch (error) {
      console.error('Fehler beim Laden der Benutzerdaten:', error);
      // Bei Fehler trotzdem als geladen markieren, um wiederholte Anfragen zu vermeiden
      setUserDataLoaded(true);
    }
  };

  const updateFormData = (field: keyof InspectionFormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = () => {
    onSubmit(formData);
  };

  const generateICSFile = () => {
    const startDate = new Date(`${formData.scheduled_date}T${formData.scheduled_time_start}`);
    const endDate = new Date(`${formData.scheduled_date}T${formData.scheduled_time_end}`);
    
    const formatDate = (date: Date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };

    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BuildWise//Inspection Scheduler//DE
BEGIN:VEVENT
UID:${Date.now()}@buildwise.app
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(startDate)}
DTEND:${formatDate(endDate)}
SUMMARY:${formData.title}
DESCRIPTION:${formData.description}\\n\\nOrt: ${formData.location_address}\\n${formData.location_notes ? `Ortshinweise: ${formData.location_notes}\\n` : ''}${formData.additional_location_info ? `Zusätzliche Ortsangaben: ${formData.additional_location_info}\\n` : ''}${formData.parking_info ? `Parken: ${formData.parking_info}\\n` : ''}${formData.access_instructions ? `Zugang: ${formData.access_instructions}\\n` : ''}\\nAnsprechpartner: ${formData.contact_person}\\nTelefon: ${formData.contact_phone}\\nE-Mail: ${formData.contact_email}${formData.alternative_contact_person ? `\\nAlternativer Kontakt: ${formData.alternative_contact_person} (${formData.alternative_contact_phone})` : ''}${formData.preparation_notes ? `\\nVorbereitungshinweise: ${formData.preparation_notes}` : ''}${formData.special_requirements ? `\\nBesondere Anforderungen: ${formData.special_requirements}` : ''}
LOCATION:${formData.location_address}${formData.location_notes ? `, ${formData.location_notes}` : ''}
END:VEVENT
END:VCALENDAR`;

    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `Besichtigung_${tradeTitle.replace(/[^a-zA-Z0-9]/g, '_')}_${formData.scheduled_date}.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!isOpen) return null;

  const isStep1Valid = formData.title && formData.scheduled_date && formData.scheduled_time_start && formData.scheduled_time_end;
  const isStep2Valid = formData.location_address;
  const isStep3Valid = formData.contact_person && formData.contact_phone && formData.contact_email;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1a2e] border border-gray-700 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div>
            <h2 className="text-xl font-bold text-white">Besichtigungstermin vereinbaren</h2>
            <p className="text-gray-400 text-sm mt-1">
              {projectName && `${projectName} - `}{tradeTitle} ({selectedQuoteIds.length} Angebote)
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between p-6 bg-[#16213e]/50">
          {[1, 2, 3].map((step) => (
            <div key={step} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === currentStep 
                  ? 'bg-[#ffbd59] text-black' 
                  : step < currentStep 
                    ? 'bg-green-500 text-white' 
                    : 'bg-gray-600 text-gray-300'
              }`}>
                {step < currentStep ? '✓' : step}
              </div>
              <div className="ml-3">
                <div className={`text-sm font-medium ${
                  step === currentStep ? 'text-[#ffbd59]' : step < currentStep ? 'text-green-400' : 'text-gray-400'
                }`}>
                  Schritt {step} von 3
                </div>
                <div className="text-xs text-gray-400">
                  {step === 1 && 'Termindetails'}
                  {step === 2 && 'Ortsangaben'}
                  {step === 3 && 'Kontaktinformationen'}
                </div>
              </div>
              {step < 3 && (
                <div className={`w-16 h-0.5 ml-4 ${
                  step < currentStep ? 'bg-green-500' : 'bg-gray-600'
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Form Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Schritt 1: Termindetails */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <Calendar className="text-[#ffbd59]" size={24} />
                <h3 className="text-lg font-semibold text-white">Termindetails festlegen</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Titel der Besichtigung *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => updateFormData('title', e.target.value)}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                  placeholder="z.B. Besichtigung Elektroinstallation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Beschreibung
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => updateFormData('description', e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none resize-none"
                  placeholder="Beschreibung der Besichtigung..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Datum *
                  </label>
                  <input
                    type="date"
                    value={formData.scheduled_date}
                    onChange={(e) => updateFormData('scheduled_date', e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white focus:border-[#ffbd59] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Startzeit *
                  </label>
                  <input
                    type="time"
                    value={formData.scheduled_time_start}
                    onChange={(e) => updateFormData('scheduled_time_start', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white focus:border-[#ffbd59] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Endzeit *
                  </label>
                  <input
                    type="time"
                    value={formData.scheduled_time_end}
                    onChange={(e) => updateFormData('scheduled_time_end', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white focus:border-[#ffbd59] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Geschätzte Dauer (Minuten)
                </label>
                <select
                  value={formData.duration_minutes}
                  onChange={(e) => updateFormData('duration_minutes', parseInt(e.target.value))}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white focus:border-[#ffbd59] focus:outline-none"
                >
                  <option value={60}>60 Minuten</option>
                  <option value={90}>90 Minuten</option>
                  <option value={120}>120 Minuten</option>
                  <option value={180}>180 Minuten</option>
                  <option value={240}>240 Minuten</option>
                </select>
              </div>
            </div>
          )}

          {/* Schritt 2: Ortsangaben */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <MapPin className="text-[#ffbd59]" size={24} />
                <h3 className="text-lg font-semibold text-white">Ortsangaben</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Adresse *
                </label>
                <input
                  type="text"
                  value={formData.location_address}
                  onChange={(e) => updateFormData('location_address', e.target.value)}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                  placeholder="Vollständige Adresse der Baustelle"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Zusätzliche Ortsangaben
                </label>
                <textarea
                  value={formData.additional_location_info}
                  onChange={(e) => updateFormData('additional_location_info', e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none resize-none"
                  placeholder="z.B. Gebäudeteil, Etage, spezifische Bereiche..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Ortshinweise
                </label>
                <textarea
                  value={formData.location_notes}
                  onChange={(e) => updateFormData('location_notes', e.target.value)}
                  rows={2}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none resize-none"
                  placeholder="Besondere Hinweise zum Ort..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Parkmöglichkeiten
                  </label>
                  <input
                    type="text"
                    value={formData.parking_info}
                    onChange={(e) => updateFormData('parking_info', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                    placeholder="Wo können Fahrzeuge geparkt werden?"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Zugangshinweise
                  </label>
                  <input
                    type="text"
                    value={formData.access_instructions}
                    onChange={(e) => updateFormData('access_instructions', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                    placeholder="Wie gelangt man zum Ort?"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Schritt 3: Kontaktinformationen */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <User className="text-[#ffbd59]" size={24} />
                <h3 className="text-lg font-semibold text-white">Kontaktinformationen</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Ansprechpartner *
                  </label>
                  <input
                    type="text"
                    value={formData.contact_person}
                    onChange={(e) => updateFormData('contact_person', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                    placeholder="Vor- und Nachname"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Telefonnummer *
                  </label>
                  <input
                    type="tel"
                    value={formData.contact_phone}
                    onChange={(e) => updateFormData('contact_phone', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                    placeholder="+49 123 456789"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    E-Mail-Adresse *
                  </label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => updateFormData('contact_email', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                    placeholder="kontakt@beispiel.de"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Alternativer Ansprechpartner
                  </label>
                  <input
                    type="text"
                    value={formData.alternative_contact_person}
                    onChange={(e) => updateFormData('alternative_contact_person', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                    placeholder="Vor- und Nachname (optional)"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Alternative Telefonnummer
                  </label>
                  <input
                    type="tel"
                    value={formData.alternative_contact_phone}
                    onChange={(e) => updateFormData('alternative_contact_phone', e.target.value)}
                    className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none"
                    placeholder="+49 123 456789 (optional)"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Vorbereitungshinweise
                </label>
                <textarea
                  value={formData.preparation_notes}
                  onChange={(e) => updateFormData('preparation_notes', e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none resize-none"
                  placeholder="Was sollten die Dienstleister mitbringen oder vorbereiten?"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Besondere Anforderungen
                </label>
                <textarea
                  value={formData.special_requirements}
                  onChange={(e) => updateFormData('special_requirements', e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 bg-[#2c3539] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-[#ffbd59] focus:outline-none resize-none"
                  placeholder="Sicherheitsbestimmungen, erforderliche Ausrüstung, etc."
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-700 bg-[#16213e]/30">
          <div className="flex items-center gap-3">
            {currentStep > 1 && (
              <button
                onClick={handlePrevious}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Zurück
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {currentStep === 3 && isStep3Valid && (
              <button
                onClick={generateICSFile}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Download size={16} />
                ICS-Datei
              </button>
            )}
            
            {currentStep < 3 ? (
              <button
                onClick={handleNext}
                disabled={
                  (currentStep === 1 && !isStep1Valid) ||
                  (currentStep === 2 && !isStep2Valid)
                }
                className="px-6 py-2 bg-[#ffbd59] hover:bg-[#ffa726] text-black font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Weiter
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!isStep3Valid}
                className="px-6 py-2 bg-[#ffbd59] hover:bg-[#ffa726] text-black font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Besichtigung vereinbaren
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InspectionSchedulingModal;
