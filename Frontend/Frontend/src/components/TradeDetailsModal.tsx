import React, { useState, useEffect } from 'react';
import { 
  X, 
  Eye, 
  Download, 
  ExternalLink, 
  FileText, 
  ChevronDown,
  Calendar,
  MapPin,
  CheckCircle,
  Clock,
  Star,
  Building,
  Calculator,
  Receipt,
  AlertTriangle,
  Settings,
  RefreshCw,
  CheckSquare,
  Square,
  User,
  Phone,
  Mail
} from 'lucide-react';
import type { TradeSearchResult } from '../api/geoService';
import { useAuth } from '../context/AuthContext';
import { getAuthenticatedFileUrl, getApiBaseUrl, apiCall } from '../api/api';
import QuoteDetailsModal from './QuoteDetailsModal';
import { appointmentService, type AppointmentResponse } from '../api/appointmentService';
import ServiceProviderRating from './ServiceProviderRating';
import InvoiceModal from './InvoiceModal';
import AcceptanceModal from './AcceptanceModalNew';
import FinalAcceptanceModal from './FinalAcceptanceModal';
// import FullDocumentViewer from './DocumentViewer';
import { updateMilestone } from '../api/milestoneService';
import InspectionSchedulingModal, { type InspectionFormData } from './InspectionSchedulingModal';

// PDF Viewer Komponente
const PDFViewer: React.FC<{ url: string; filename: string; onError: (error: string) => void }> = ({ url, filename, onError }) => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadPDF = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      if (!token) {
        onError('Kein Authentifizierungstoken verfügbar');
        return;
      }

      // Versuche Document-ID aus URL zu extrahieren
      const documentId = extractDocumentIdFromUrl(url);
      if (documentId) {
        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/documents/${documentId}/content`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const objectUrl = URL.createObjectURL(blob);
          setPdfUrl(objectUrl);
        } else {
          throw new Error('PDF konnte nicht geladen werden');
        }
      } else {
        // Fallback: Verwende die authentifizierte URL
        const authenticatedUrl = getAuthenticatedFileUrl(url);
        setPdfUrl(authenticatedUrl);
      }
    } catch (error) {
      console.error('❌ Fehler beim Laden des PDFs:', error);
      onError('PDF konnte nicht geladen werden');
    } finally {
      setLoading(false);
    }
  };

  // Hilfsfunktion um Document-ID aus URL zu extrahieren
  const extractDocumentIdFromUrl = (url: string): string | null => {
    const patterns = [
      /\/documents\/(\d+)\//,
      /document_(\d+)/,
      /(\d+)\.(pdf|doc|docx|txt)$/,
      /\/storage\/uploads\/project_\d+\/(\d+)\./
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        return match[1];
      }
    }
    return null;
  };

  useEffect(() => {
    loadPDF();
  }, [url]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#ffbd59] mx-auto mb-2"></div>
          <p className="text-gray-400 text-sm">Lade PDF...</p>
        </div>
      </div>
    );
  }

  if (!pdfUrl) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-red-400 text-sm">PDF konnte nicht geladen werden</p>
        </div>
      </div>
    );
  }

  return (
    <iframe
      src={pdfUrl}
      width="100%"
      height="100%"
      frameBorder="0"
      className="rounded-b border-0"
      title={filename}
    />
  );
};

interface TradeDetailsModalProps {
  trade: TradeSearchResult | null;
  project?: any;
  isOpen: boolean;
  onClose: () => void;
  onCreateQuote: (trade: TradeSearchResult) => void;
  existingQuotes?: Quote[];
  onCreateInspection?: (tradeId: number, selectedQuoteIds: number[]) => void;
}

interface Quote {
  id: number;
  service_provider_id: number;
  status: string;
  total_price?: number;
  total_amount?: number;
  created_at: string;
  service_provider_name?: string;
  contact_released?: boolean;
  company_name?: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  website?: string;
  currency?: string;
  labor_cost?: number | string;
  material_cost?: number | string;
  overhead_cost?: number | string;
}

interface DocumentViewerProps {
  documents: Array<{
    id: number | string;
    title?: string;
    name?: string;
    file_name?: string;
    url?: string;
    file_path?: string;
    type?: string;
    mime_type?: string;
    size?: number;
    file_size?: number;
  }>;
  existingQuotes: Quote[];
}

type BuilderTabKey = 'overview' | 'quotes' | 'documents' | 'workflow' | 'inspection';

function TradeDocumentViewer({ documents, existingQuotes }: DocumentViewerProps) {
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [viewerError, setViewerError] = useState<string | null>(null);
  const { isBautraeger } = useAuth();
  const isBautraegerUser = isBautraeger();



  // Robuste Dokumentenverarbeitung
  const safeDocuments = React.useMemo(() => {
    if (!documents) return [];
    if (Array.isArray(documents)) return documents;
    if (typeof documents === 'string') {
      try {
        const parsed = JSON.parse(documents);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }
    return [];
  }, [documents]);



  if (!safeDocuments || safeDocuments.length === 0) {
    return (
      <div className="bg-gradient-to-br from-[#2c3539]/30 to-[#1a1a2e]/30 rounded-xl p-6 border border-gray-600/30 backdrop-blur-sm">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <FileText size={18} className="text-[#ffbd59]" />
          Dokumente
        </h3>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <FileText size={48} className="text-gray-500 mx-auto mb-3 opacity-50" />
            <p className="text-gray-400 text-sm">
              {isBautraegerUser 
                ? 'Keine Dokumente für dieses Gewerk vorhanden' 
                : 'Keine Dokumente für dieses Gewerk freigegeben'
              }
            </p>
            <p className="text-gray-500 text-xs mt-1">
              {isBautraegerUser 
                ? 'Dokumente können über die Projektverwaltung hinzugefügt werden' 
                : 'Dokumente werden nach Angebotsannahme verfügbar'
              }
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getFileIcon = (doc: any) => {
    const type = doc.type || doc.mime_type || '';
    if (type && type.includes('pdf')) return '📄';
    if (type && (type.includes('word') || type.includes('document'))) return '📝';
    if (type && (type.includes('presentation') || type.includes('powerpoint'))) return '📊';
    return '📁';
  };

  const canPreview = (doc: any) => {
    const type = doc.type || doc.mime_type || '';
    return type && (type.includes('pdf') || 
           type.includes('word') || 
           type.includes('document') ||
           type.includes('presentation') || 
           type.includes('powerpoint'));
  };

  const getViewerUrl = (doc: any) => {
    const url = doc.url || doc.file_path || '';
    const type = doc.type || doc.mime_type || '';
    
    if (type && type.includes('pdf')) {
      const documentId = extractDocumentIdFromUrl(url);
      if (documentId) {
        const baseUrl = getApiBaseUrl();
        return `${baseUrl}/documents/${documentId}/content`;
      }
      return getAuthenticatedFileUrl(url);
    }
    
    if (type && (type.includes('word') || type.includes('document') || 
        type.includes('presentation') || type.includes('powerpoint'))) {
      const authenticatedUrl = getAuthenticatedFileUrl(url);
      return `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(authenticatedUrl)}`;
    }
    
    return getAuthenticatedFileUrl(url);
  };

  const extractDocumentIdFromUrl = (url: string): string | null => {
    const patterns = [
      /\/documents\/(\d+)\//,
      /document_(\d+)/,
      /(\d+)\.(pdf|doc|docx|txt)$/,
      /\/storage\/uploads\/project_\d+\/(\d+)\./
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        return match[1];
      }
    }
    return null;
  };

  return (
    <div className="bg-gradient-to-br from-[#2c3539]/30 to-[#1a1a2e]/30 rounded-xl p-6 border border-gray-600/30 backdrop-blur-sm">
      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
        <FileText size={18} className="text-[#ffbd59]" />
        Dokumente ({safeDocuments.length})
      </h3>
      
      {viewerError && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
          <p className="text-red-400 text-sm">{viewerError}</p>
        </div>
      )}
      
      <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800" style={{scrollBehavior: 'smooth'}}>
        {safeDocuments.map((doc) => {
          if (!doc) {
            return null;
          }
          
          return (
          <div key={doc.id} className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-lg border border-gray-600/30 p-4 hover:border-[#ffbd59]/50 transition-all duration-200 group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-[#ffbd59] to-[#ffa726] rounded-lg flex items-center justify-center text-white font-bold shadow-lg">
                    {getFileIcon(doc)}
                </div>
                <div>
                    <p className="font-medium text-white group-hover:text-[#ffbd59] transition-colors">
                      {doc.name || doc.title || doc.file_name || 'Unbekanntes Dokument'}
                    </p>
                  <p className="text-sm text-gray-400">
                      {((doc.size || doc.file_size || 0) / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                  {canPreview(doc) && (
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                        
                        if (doc.type && doc.type.includes('pdf')) {
                          const token = localStorage.getItem('token');
                          if (!token) {
                            setViewerError('Kein Authentifizierungstoken verfügbar');
                            return;
                          }
                          
                          const documentId = extractDocumentIdFromUrl(doc.url || doc.file_path || '');
                          if (documentId) {
                            setSelectedDoc(selectedDoc === String(doc.id) ? null : String(doc.id));
                            setViewerError(null);
                            return;
                          }
                        }
                        
                        setSelectedDoc(selectedDoc === String(doc.id) ? null : String(doc.id));
                      setViewerError(null);
                    }}
                    className={`flex items-center gap-1 px-3 py-2 rounded-lg transition-all duration-200 text-sm font-medium ${
                        selectedDoc === String(doc.id)
                        ? 'bg-[#ffbd59] text-[#1a1a2e] shadow-lg'
                        : 'bg-[#ffbd59]/20 text-[#ffbd59] hover:bg-[#ffbd59]/30'
                    }`}
                    title="Dokument anzeigen"
                  >
                    <Eye size={14} />
                      {selectedDoc === String(doc.id) ? 'Schließen' : 'Ansehen'}
                  </button>
                )}
                  
                  {(isBautraegerUser || existingQuotes.some((quote: Quote) => quote.status === 'accepted')) && (
                <a
                      href={getAuthenticatedFileUrl(doc.url || doc.file_path || '')}
                      download={doc.name || doc.title || doc.file_name || 'document'}
                  className="flex items-center gap-1 px-3 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 transition-all duration-200 text-sm font-medium"
                      title={isBautraegerUser ? "Dokument herunterladen" : "Dokument herunterladen (nur nach Angebotsannahme)"}
                >
                  <Download size={14} />
                  Download
                </a>
                  )}
                  
                  <button
                    onClick={async (e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      
                      try {
                        const token = localStorage.getItem('token');
                        if (!token) {
                          alert('Kein Authentifizierungstoken verfügbar');
                          return;
                        }
                        
                        const documentId = extractDocumentIdFromUrl(doc.url || doc.file_path || '');
                        if (documentId) {
                          const baseUrl = getApiBaseUrl();
                          const response = await fetch(`${baseUrl}/documents/${documentId}/content`, {
                            headers: {
                              'Authorization': `Bearer ${token}`
                            }
                          });
                          
                          if (response.ok) {
                            const blob = await response.blob();
                            const url = URL.createObjectURL(blob);
                            window.open(url, '_blank');
                            setTimeout(() => URL.revokeObjectURL(url), 1000);
                          } else {
                            throw new Error('Dokument konnte nicht geladen werden');
                          }
                        } else {
                          const authenticatedUrl = getAuthenticatedFileUrl(doc.url || doc.file_path || '');
                          window.open(authenticatedUrl, '_blank');
                        }
                      } catch (error) {
                        console.error('❌ Fehler beim Öffnen des Dokuments:', error);
                        alert('Dokument konnte nicht geöffnet werden');
                      }
                    }}
                  className="flex items-center gap-1 px-3 py-2 bg-blue-600/20 text-blue-400 rounded-lg hover:bg-blue-600/30 transition-all duration-200 text-sm font-medium"
                  title="In neuem Tab öffnen"
                >
                  <ExternalLink size={14} />
                  Öffnen
                  </button>
              </div>
            </div>
            
              {selectedDoc === String(doc.id) && (
                <div className="mt-4 bg-gradient-to-br from-[#1a1a2e]/80 to-[#2c3539]/80 rounded-lg border border-gray-600/50 overflow-hidden">
                  <div className="flex items-center justify-between p-3 border-b border-gray-600/30">
                    <div className="flex items-center gap-2">
                      <FileText size={16} className="text-[#ffbd59]" />
                      <span className="text-white font-medium">
                        {doc.name || doc.title || doc.file_name || 'Dokument'}
                      </span>
                        </div>
                        <button
                          onClick={() => setSelectedDoc(null)}
                          className="text-gray-400 hover:text-white transition-colors"
                        >
                          <X size={16} />
                        </button>
                      </div>
                      <div style={{ height: '400px' }} className="relative">
                    {doc.type && doc.type.includes('pdf') ? (
                      <PDFViewer 
                        url={doc.url || doc.file_path || ''} 
                        filename={doc.name || doc.title || doc.file_name || 'document'}
                        onError={(error: string) => {
                          console.error(`❌ PDF Viewer Fehler:`, error);
                          setViewerError('PDF konnte nicht geladen werden');
                        }}
                      />
                    ) : (
                        <iframe
                        src={getViewerUrl(doc)}
                          width="100%"
                          height="100%"
                          frameBorder="0"
                          className="rounded-b border-0"
                          onError={() => {
                          setViewerError('Das Dokument konnte nicht geladen werden');
                          }}
                        />
                  )}
                </div>
              </div>
            )}
          </div>
          );
        })}
      </div>
    </div>
  );
}

  // Hilfsfunktion für Projekttyp-Labels
  const getProjectTypeLabel = (type: string) => {
    switch (type) {
      case 'new_build': return 'Neubau';
      case 'renovation': return 'Renovierung';
      case 'extension': return 'Erweiterung';
      case 'modernization': return 'Modernisierung';
      case 'maintenance': return 'Wartung';
      default: return type;
    }
  };

   export default function TradeDetailsModal({ 
  trade, 
  project,
  isOpen, 
  onClose, 
  onCreateQuote, 
  existingQuotes = [],
  onCreateInspection
}: TradeDetailsModalProps) {
  

  const { user, isBautraeger } = useAuth();
  // const [loading, setLoading] = useState(false);
  // const [userHasQuote, setUserHasQuote] = useState(false);
  // const [userQuote, setUserQuote] = useState<Quote | null>(null);
  // const [showCostEstimateForm, setShowCostEstimateForm] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedQuoteIds, setSelectedQuoteIds] = useState<number[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<{ title: string; description: string; category?: string; priority?: string; planned_date?: string; notes?: string; requires_inspection?: boolean }>({ title: '', description: '' });
  const [isUpdatingTrade, setIsUpdatingTrade] = useState(false);
  
  // Neue States für dynamisches Laden der Dokumente
  const [loadedDocuments, setLoadedDocuments] = useState<any[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [showQuoteDetails, setShowQuoteDetails] = useState(false);
  const [quoteForDetails, setQuoteForDetails] = useState<Quote | null>(null);
  const [appointmentsForTrade, setAppointmentsForTrade] = useState<AppointmentResponse[]>([]);
  const [showAcceptConfirm, setShowAcceptConfirm] = useState(false);
  const [quoteIdToAccept, setQuoteIdToAccept] = useState<number | null>(null);
  const [acceptAcknowledged, setAcceptAcknowledged] = useState(false);

  const isBautraegerUser = isBautraeger();

  const [activeBuilderTab, setActiveBuilderTab] = useState<BuilderTabKey>('overview');
  
  // States für neue Features
  const [currentProgress, setCurrentProgress] = useState(trade?.progress_percentage || 0);
  const [showRatingModal, setShowRatingModal] = useState(false);
  const [hasRated, setHasRated] = useState(false);
  
  // Benachrichtigungssystem States
  const [hasUnreadMessages, setHasUnreadMessages] = useState(false);
  const [notificationBlink, setNotificationBlink] = useState(false);
  const [messageInput, setMessageInput] = useState('');
  const [messages, setMessages] = useState<Array<{id: number, text: string, sender: string, timestamp: string}>>([]);
      const [acceptedQuote, setAcceptedQuote] = useState<Quote | null>(null);
    const [completionStatus, setCompletionStatus] = useState(trade?.completion_status || 'in_progress');
    const [showInvoiceModal, setShowInvoiceModal] = useState(false);
    const [existingInvoice, setExistingInvoice] = useState<any>(null);
      const [showAcceptanceModal, setShowAcceptanceModal] = useState(false);
  const [showFinalAcceptanceModal, setShowFinalAcceptanceModal] = useState(false);
  const [acceptanceDefects, setAcceptanceDefects] = useState<any[]>([]);
  const [fullTradeData, setFullTradeData] = useState<any>(null);
  const [showInspectionScheduling, setShowInspectionScheduling] = useState(false);

  const formatCurrency = (amount: number, currency: string = 'EUR') => {
    try {
      return amount.toLocaleString('de-DE', { style: 'currency', currency });
    } catch {
      return `${amount.toLocaleString('de-DE')} EUR`;
    }
  };

      // KRITISCH: Verwende NUR den Backend-Status, NICHT das trade Objekt
  // useEffect(() => {
  //   if (trade?.completion_status) {
  //     setCompletionStatus(trade.completion_status);
  //     console.log('🔄 TradeDetailsModal - Completion Status aktualisiert:', trade.completion_status);
  //   }
  // }, [trade?.completion_status]);


  if (isOpen || trade?.id) {

    
    // Warnung wenn trade-ID 1 ist (könnte falsches Gewerk sein)
    if (trade?.id === 1 && trade?.title === 'Elektroinstallation EG') {
      console.warn('⚠️ WARNUNG: TradeDetailsModal verwendet Milestone ID 1 ("Elektroinstallation EG"). Falls dies ein neues Gewerk sein sollte, könnte es ein Problem mit der Milestone-Erstellung geben.');
    }
  }

  useEffect(() => {
    if (isOpen && isBautraegerUser) {
      setActiveBuilderTab('overview');
    }
  }, [isOpen, isBautraegerUser]);

  // Lade Termine für dieses Gewerk, wenn Modal geöffnet
  useEffect(() => {
    let cancelled = false;
    const loadAppointments = async () => {
      try {
        if (!trade?.id) return;
        
        // Versuche zuerst die neuen Inspections zu laden
        try {
          const inspectionResponse = await apiCall(`/inspections/?milestone_id=${trade.id}`);
          if (inspectionResponse.ok) {
            const inspections = await inspectionResponse.json();
            if (inspections.length > 0 && !cancelled) {
              // Konvertiere Inspections zu appointment-Format für Kompatibilität
              const convertedAppointments = inspections.map((inspection: any) => ({
                ...inspection,
                appointment_type: 'INSPECTION',
                milestone_id: inspection.milestone_id,
                scheduled_date: inspection.scheduled_date,
                location: inspection.location_address,
                // Alle erweiterten Felder sind bereits vorhanden
              }));
              setAppointmentsForTrade(convertedAppointments);
              return;
            }
          }
        } catch (inspectionError) {

        }
        
        // Fallback: Verwende alten appointmentService
        const all = await appointmentService.getMyAppointments();
        const relevant = all.filter(a => a.milestone_id === (trade as any).id && a.appointment_type === 'INSPECTION');
        if (!cancelled) setAppointmentsForTrade(relevant);
      } catch (e) {
        console.error('❌ Termine laden fehlgeschlagen:', e);
      }
    };
    if (isOpen) loadAppointments();
    return () => { cancelled = true; };
  }, [isOpen, trade?.id]);

  // Hilfsfunktion: Ist aktueller Nutzer (Dienstleister) zur Besichtigung eingeladen?
  const isUserInvitedForInspection = React.useMemo(() => {
    if (!user || isBautraegerUser) return false;
    return Array.isArray(appointmentsForTrade) && appointmentsForTrade.some(ap => {
      const invited = Array.isArray(ap.invited_service_providers) ? ap.invited_service_providers : [];
      const responsesArr = Array.isArray(ap.responses) ? ap.responses : (Array.isArray((ap as any).responses_array) ? (ap as any).responses_array : []);
      const inInvites = invited.some((sp: any) => Number(sp.id) === Number(user.id));
      const inResponses = responsesArr.some((r: any) => Number(r.service_provider_id) === Number(user.id));
      return inInvites || inResponses;
    });
  }, [appointmentsForTrade, user, isBautraegerUser]);

  // Funktion zum dynamischen Laden der Dokumente und completion_status
  const loadTradeDocuments = async (tradeId: number) => {
    if (!tradeId) return;
    
    setDocumentsLoading(true);
    setDocumentsError(null);
    
    try {

      
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Kein Authentifizierungstoken verfügbar');
      }
      
      const baseUrl = getApiBaseUrl();
      
      // Für Bauträger: Lade direkt vom Milestone-Endpoint
      // Für Dienstleister: Verwende die Geo-Suche (wie bisher)
      if (isBautraegerUser) {

        
        const response = await fetch(`${baseUrl}/milestones/${tradeId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`Fehler beim Laden der Gewerk-Details: ${response.status}`);
        }
        
        const milestoneData = await response.json();

        
        // Aktualisiere vollständige Trade-Daten
        setFullTradeData(milestoneData);
        
        // KRITISCH: Aktualisiere completion_status vom Backend
        if (milestoneData.completion_status) {

          setCompletionStatus(milestoneData.completion_status);
        }
        
        // Extrahiere und verarbeite die Dokumente
        let documents = [];
        if (milestoneData.documents) {
          if (Array.isArray(milestoneData.documents)) {
            documents = milestoneData.documents;
          } else if (typeof milestoneData.documents === 'string') {
            try {
              documents = JSON.parse(milestoneData.documents);
            } catch (e) {
              console.error('❌ Fehler beim Parsen der Dokumente:', e);
              documents = [];
            }
          }
        }
        
        // Zusätzlich: Lade geteilte Dokumente falls vorhanden
        if (milestoneData.shared_document_ids) {
          try {
            let sharedDocIds = milestoneData.shared_document_ids;
            if (typeof sharedDocIds === 'string') {
              sharedDocIds = JSON.parse(sharedDocIds);
            }
            
            if (Array.isArray(sharedDocIds) && sharedDocIds.length > 0) {
              // Lade die geteilten Dokumente
              const sharedDocsPromises = sharedDocIds.map(async (docId: number) => {
                try {
                  const docResponse = await fetch(`${baseUrl}/documents/${docId}`, {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                      'Content-Type': 'application/json'
                    }
                  });
                  
                  if (docResponse.ok) {
                    const docData = await docResponse.json();
                    return {
                      id: docData.id,
                      name: docData.title || docData.file_name,
                      title: docData.title,
                      file_name: docData.file_name,
                      url: `/api/v1/documents/${docData.id}/download`,
                      file_path: `/api/v1/documents/${docData.id}/download`,
                      type: docData.mime_type || 'application/octet-stream',
                      mime_type: docData.mime_type,
                      size: docData.file_size || 0,
                      file_size: docData.file_size,
                      category: docData.category,
                      subcategory: docData.subcategory,
                      created_at: docData.created_at
                    };
                  }
                  return null;
                } catch (e) {
                  console.error(`❌ Fehler beim Laden des geteilten Dokuments ${docId}:`, e);
                  return null;
                }
              });
              
              const sharedDocs = await Promise.all(sharedDocsPromises);
              const validSharedDocs = sharedDocs.filter(doc => doc !== null);
              

              documents = [...documents, ...validSharedDocs];
            }
          } catch (e) {
            console.error('❌ Fehler beim Verarbeiten der geteilten Dokumente:', e);
          }
        }
        

        setLoadedDocuments(documents);
        
      } else {
        // Dienstleister-Modus: Verwende die Geo-Suche (wie bisher)

        
        // Lade das vollständige Milestone mit Dokumenten vom Backend
        const response = await fetch(`${baseUrl}/milestones/${tradeId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`Fehler beim Laden der Gewerk-Details: ${response.status}`);
        }
        
        const milestoneData = await response.json();


        
        // Aktualisiere vollständige Trade-Daten
        setFullTradeData(milestoneData);
        
        // KRITISCH: Aktualisiere completion_status vom Backend
        if (milestoneData.completion_status) {
          setCompletionStatus(milestoneData.completion_status);
        }
        
        // Extrahiere und verarbeite die Dokumente
        let documents = [];
        if (milestoneData.documents) {
          if (Array.isArray(milestoneData.documents)) {
            documents = milestoneData.documents;
          } else if (typeof milestoneData.documents === 'string') {
            try {
              documents = JSON.parse(milestoneData.documents);
            } catch (e) {
              console.error('❌ Fehler beim Parsen der Dokumente:', e);
              documents = [];
            }
          }
        }
        
        // Zusätzlich: Lade geteilte Dokumente falls vorhanden
        if (milestoneData.shared_document_ids) {
          try {
            let sharedDocIds = milestoneData.shared_document_ids;
            if (typeof sharedDocIds === 'string') {
              sharedDocIds = JSON.parse(sharedDocIds);
            }
            
            if (Array.isArray(sharedDocIds) && sharedDocIds.length > 0) {
              // Lade die geteilten Dokumente
              const sharedDocsPromises = sharedDocIds.map(async (docId: number) => {
                try {
                  const docResponse = await fetch(`${baseUrl}/documents/${docId}`, {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                      'Content-Type': 'application/json'
                    }
                  });
                  
                  if (docResponse.ok) {
                    const docData = await docResponse.json();
                    return {
                      id: docData.id,
                      name: docData.title || docData.file_name,
                      title: docData.title,
                      file_name: docData.file_name,
                      url: `/api/v1/documents/${docData.id}/download`,
                      file_path: `/api/v1/documents/${docId}/download`,
                      type: docData.mime_type || 'application/octet-stream',
                      mime_type: docData.mime_type,
                      size: docData.file_size || 0,
                      file_size: docData.file_size,
                      category: docData.category,
                      subcategory: docData.subcategory,
                      created_at: docData.created_at
                    };
                  }
                  return null;
                } catch (e) {
                  console.error(`❌ Fehler beim Laden des geteilten Dokuments ${docId}:`, e);
                  return null;
                }
              });
              
              const sharedDocs = await Promise.all(sharedDocsPromises);
              const validSharedDocs = sharedDocs.filter(doc => doc !== null);
              

              documents = [...documents, ...validSharedDocs];
            }
          } catch (e) {
            console.error('❌ Fehler beim Verarbeiten der geteilten Dokumente:', e);
          }
        }
        
        console.log('📄 TradeDetailsModal - Finale Dokumentenliste (Dienstleister):', documents);
        setLoadedDocuments(documents);
      }
      
    } catch (error) {
      console.error('❌ TradeDetailsModal - Fehler beim Laden der Dokumente:', error);
      setDocumentsError(error instanceof Error ? error.message : 'Unbekannter Fehler');
      
      // Fallback: Verwende die ursprünglichen trade.documents falls vorhanden
      if (trade?.documents && Array.isArray(trade.documents)) {

        setLoadedDocuments(trade.documents);
      } else {
        setLoadedDocuments([]);
      }
    } finally {
      setDocumentsLoading(false);
    }
  };



  // Lade Dokumente und completion_status wenn Modal geöffnet wird
  useEffect(() => {
    if (isOpen && trade?.id) {

      loadTradeDocuments(trade.id);
      // Zusätzlich: Lade completion_status explizit vom Backend
      loadCompletionStatus(trade.id);
    }
  }, [isOpen, trade?.id]);

  // Funktion zum Laden des completion_status vom Backend
  const loadCompletionStatus = async (tradeId: number) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/milestones/${tradeId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const milestoneData = await response.json();

        
        if (milestoneData.completion_status) {

          setCompletionStatus(milestoneData.completion_status);
        }
      }
    } catch (error) {
      console.error('❌ TradeDetailsModal - Fehler beim Laden des completion_status:', error);
    }
  };

  // Fallback: Setze ursprüngliche Dokumente falls vorhanden und noch keine geladen wurden
  useEffect(() => {
    if (isOpen && trade?.documents && Array.isArray(trade.documents) && loadedDocuments.length === 0 && !documentsLoading) {

      setLoadedDocuments(trade.documents);
    }
  }, [isOpen, trade?.documents, loadedDocuments.length, documentsLoading]);

    // useEffect(() => {
  //   if (isOpen && trade) {
  //   setLoading(true);
  //     
  //     const userQuote = existingQuotes.find(quote => quote.service_provider_id === user?.id);
  //     if (userQuote) {
  //       setUserHasQuote(true);
  //       setUserQuote(userQuote);
  //     } else {
  //       setUserHasQuote(false);
  //     setUserQuote(null);
  //     }
  //     
  //     setLoading(false);
  //   }
  // }, [isOpen, trade, existingQuotes, user?.id]);

  // Finde akzeptiertes Quote
  useEffect(() => {
    if (existingQuotes && existingQuotes.length > 0) {
      const accepted = existingQuotes.find(q => q.status === 'accepted');
      if (accepted) {
        setAcceptedQuote(accepted);
      } else {
        // Fallback: Auch nach anderen möglichen Status-Werten suchen
        const acceptedFallback = existingQuotes.find(q => 
          q.status === 'angenommen' || 
          q.status === 'ACCEPTED' || 
          q.status === 'Angenommen'
        );

        if (acceptedFallback) {
          setAcceptedQuote(acceptedFallback);
        }
      }
    }
  }, [existingQuotes]);

  // KRITISCH: Verwende NUR den Backend-Status, nicht das trade Objekt
  // useEffect(() => {
  //   if (trade && completionStatus === 'in_progress') {
  //     console.log('🔄 TradeDetailsModal - Setze completion_status vom trade Objekt als initialer Fallback:', trade.completion_status);
  //     setCompletionStatus(trade.completion_status || 'in_progress');
  //     setCurrentProgress(trade.progress_percentage || 0);
  //   }
  // }, [trade, completionStatus]);

    // Lade bestehende Rechnung
    const loadExistingInvoice = async () => {
      if (!trade?.id) return;
      
      try {
        const { api } = await import('../api/api');
        const response = await api.get(`/invoices/milestone/${trade.id}`);
        
        if (response.data) {
          setExistingInvoice(response.data);

        }
      } catch (error: any) {
        if (error.response?.status !== 404) {
          console.error('❌ Fehler beim Laden der bestehenden Rechnung:', error);
        }
        // 404 ist OK - bedeutet nur dass noch keine Rechnung existiert
        setExistingInvoice(null);
      }
    };

    // Lade bestehende Rechnung wenn Modal geöffnet wird
    useEffect(() => {
      if (isOpen && trade?.id && (completionStatus === 'completed' || completionStatus === 'completed_with_defects')) {
        loadExistingInvoice();
      }
    }, [isOpen, trade?.id, completionStatus]);

    const getCategoryIcon = (category: string) => {
    const iconMap: { [key: string]: { color: string; icon: React.ReactNode } } = {
      'electrical': { color: '#fbbf24', icon: <span className="text-lg">⚡</span> },
      'plumbing': { color: '#3b82f6', icon: <span className="text-lg">🔧</span> },
      'heating': { color: '#ef4444', icon: <span className="text-lg">🔥</span> },
      'roofing': { color: '#f97316', icon: <span className="text-lg">🏠</span> },
      'windows': { color: '#10b981', icon: <span className="text-lg">🪟</span> },
      'flooring': { color: '#8b5cf6', icon: <span className="text-lg">📐</span> },
      'walls': { color: '#ec4899', icon: <span className="text-lg">🧱</span> },
      'foundation': { color: '#6b7280', icon: <span className="text-lg">🏗️</span> },
      'landscaping': { color: '#22c55e', icon: <span className="text-lg">🌱</span> }
    };
    
    return iconMap[category] || { color: '#6b7280', icon: <span className="text-lg">🔧</span> };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planned': return 'text-blue-400';
      case 'in_progress': return 'text-yellow-400';
      case 'completed': return 'text-green-400';
      case 'delayed': return 'text-red-400';
      case 'cancelled': return 'text-gray-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'planned': return 'Geplant';
      case 'in_progress': return 'In Bearbeitung';
      case 'completed': return 'Abgeschlossen';
      case 'delayed': return 'Verzögert';
      case 'cancelled': return 'Storniert';
      default: return status;
    }
  };

  const getQuoteStatusColor = (status: string) => {
    switch (status) {
      case 'accepted': return 'text-green-400';
      case 'submitted': return 'text-yellow-400';
      case 'rejected': return 'text-red-400';
      case 'draft': return 'text-gray-400';
      default: return 'text-gray-400';
    }
  };

  const getQuoteStatusLabel = (status: string) => {
    switch (status) {
      case 'accepted': return 'Angenommen';
      case 'submitted': return 'Eingereicht';
      case 'rejected': return 'Abgelehnt';
      case 'draft': return 'Entwurf';
      default: return status;
    }
  };

  const getCompletionStatusColor = (status: string) => {
    switch (status) {
      case 'in_progress': return 'text-blue-400';
      case 'completion_requested': return 'text-yellow-400';
      case 'under_review': return 'text-orange-400';
      case 'completed': return 'text-green-400';
      case 'archived': return 'text-gray-400';
      default: return 'text-gray-400';
    }
  };

  const getCompletionStatusLabel = (status: string) => {
    switch (status) {
      case 'in_progress': return 'In Bearbeitung';
      case 'completion_requested': return 'Abnahme angefordert';
      case 'under_review': return 'Nachbesserung';
      case 'completed': return 'Abgenommen';
      case 'archived': return 'Archiviert';
      default: return status;
    }
  };

  const getCompletionStatusIcon = (status: string) => {
    switch (status) {
      case 'in_progress': return <Clock size={16} />;
      case 'completion_requested': return <AlertTriangle size={16} />;
      case 'under_review': return <AlertTriangle size={16} />;
      case 'completed': return <CheckCircle size={16} />;
      case 'archived': return <CheckCircle size={16} />;
      default: return <Clock size={16} />;
    }
  };

  // Handler für Baufortschritt
  const handleProgressChange = async (newProgress: number) => {
    setCurrentProgress(newProgress);
    // Optional: API call to update progress
  };

  // Benachrichtigungssystem Funktionen
  const triggerNotification = () => {
    setHasUnreadMessages(true);
    setNotificationBlink(true);
    
    // Blink-Animation nach 3 Sekunden stoppen
    setTimeout(() => {
      setNotificationBlink(false);
    }, 3000);
  };

  const handleTabClick = (tabKey: BuilderTabKey) => {
    setActiveBuilderTab(tabKey);
    
    // Wenn der Fortschritt-Tab geklickt wird, Benachrichtigung zurücksetzen
    if (tabKey === 'workflow') {
      setHasUnreadMessages(false);
      setNotificationBlink(false);
    }
  };

  const handleMessageSent = () => {
    if (messageInput.trim()) {
      // Neue Nachricht hinzufügen
      const newMessage = {
        id: Date.now(),
        text: messageInput.trim(),
        sender: user?.name || 'Sie',
        timestamp: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, newMessage]);
      setMessageInput('');
      
      // Diese Funktion wird aufgerufen, wenn eine Nachricht gesendet wird
      // Sie triggert die Benachrichtigung auf der Gegenseite
      triggerNotification();
    }
  };

  const handleCompletionRequest = async () => {
    try {

      
      const response = await apiCall(`/milestones/${trade?.id}/progress/completion`, {
        method: 'POST',
        body: JSON.stringify({
          message: 'Gewerk fertiggestellt. Bitte um Abnahme.',
          update_type: 'completion'
        })
      });
      

      setCompletionStatus('completion_requested');
      
      // Aktualisiere auch den Fortschritt
      if (trade?.id) {
        loadTradeDocuments(trade.id);
      }
    } catch (error) {
      console.error('❌ TradeDetailsModal - Fehler bei Fertigstellungsmeldung:', error);
      alert('Fehler beim Anfordern der Abnahme. Bitte versuchen Sie es erneut.');
    }
  };

  const handleCompletionResponse = async (accepted: boolean, message?: string, deadline?: string) => {
    try {

      
      const response = await apiCall(`/milestones/${trade?.id}/progress/completion/response`, {
        method: 'POST',
        body: JSON.stringify({
          accepted,
          message: message || (accepted ? 'Gewerk abgenommen.' : 'Nachbesserung erforderlich.'),
          revision_deadline: deadline
        })
      });
      

      setCompletionStatus(accepted ? 'completed' : 'under_review');
      
      // Aktualisiere auch den Fortschritt
      if (trade?.id) {
        loadTradeDocuments(trade.id);
      }
    } catch (error) {
      console.error('❌ TradeDetailsModal - Fehler bei Abnahme-Antwort:', error);
      alert('Fehler beim Verarbeiten der Abnahme-Antwort. Bitte versuchen Sie es erneut.');
    }
  };

  // Entfernt: handleInvoiceUploaded da nicht verwendet

  const handleRatingComplete = () => {
    setHasRated(true);
    setShowRatingModal(false);
  };

  // Handler für Abnahme starten
  const handleStartAcceptance = () => {
    setShowAcceptanceModal(true);
  };

  // Handler für Besichtigungserstellung
  const handleCreateInspection = async (inspectionData: InspectionFormData) => {
    try {

      
      // API-Call zur Erstellung der Besichtigung
      const response = await apiCall('/inspections/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          milestone_id: trade?.id,
          title: inspectionData.title,
          description: inspectionData.description,
          scheduled_date: inspectionData.scheduled_date,
          scheduled_time_start: inspectionData.scheduled_time_start,
          scheduled_time_end: inspectionData.scheduled_time_end,
          duration_minutes: inspectionData.duration_minutes,
          location_address: inspectionData.location_address,
          location_notes: inspectionData.location_notes,
          additional_location_info: inspectionData.additional_location_info,
          parking_info: inspectionData.parking_info,
          access_instructions: inspectionData.access_instructions,
          contact_person: inspectionData.contact_person,
          contact_phone: inspectionData.contact_phone,
          contact_email: inspectionData.contact_email,
          alternative_contact_person: inspectionData.alternative_contact_person,
          alternative_contact_phone: inspectionData.alternative_contact_phone,
          preparation_notes: inspectionData.preparation_notes,
          special_requirements: inspectionData.special_requirements
        }),
      });

      if (response.ok) {
        const inspection = await response.json();


        // Lade Dienstleister zu der Besichtigung ein
        const inviteResponse = await apiCall(`/inspections/${inspection.id}/invitations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(selectedQuoteIds),
        });

        if (inviteResponse.ok) {

          // Lade Termine neu - verwende die neue Inspection API
          const loadAppointments = async () => {
            try {
              if (!trade?.id) return;
              
              // Lade die neue Inspection mit allen erweiterten Feldern
              const inspectionResponse = await apiCall(`/inspections/?milestone_id=${trade.id}`);
              if (inspectionResponse.ok) {
                const inspections = await inspectionResponse.json();
                if (inspections.length > 0) {
                  // Konvertiere Inspections zu appointment-Format für Kompatibilität
                  const convertedAppointments = inspections.map((inspection: any) => ({
                    ...inspection,
                    appointment_type: 'INSPECTION',
                    milestone_id: inspection.milestone_id,
                    scheduled_date: inspection.scheduled_date,
                    location: inspection.location_address,
                    // Alle erweiterten Felder sind bereits vorhanden
                  }));
                  setAppointmentsForTrade(convertedAppointments);
                  return;
                }
              }
              
              // Fallback
              const all = await appointmentService.getMyAppointments();
              const relevant = all.filter(a => a.milestone_id === (trade as any).id && a.appointment_type === 'INSPECTION');
              setAppointmentsForTrade(relevant);
            } catch (e) {
              console.error('❌ Termine laden fehlgeschlagen:', e);
            }
          };
          await loadAppointments();
          
          setShowInspectionScheduling(false);
          setSelectedQuoteIds([]);
        } else {
          throw new Error('Fehler beim Versenden der Einladungen');
        }
      } else {
        throw new Error('Fehler beim Erstellen der Besichtigung');
      }
    } catch (error) {
      console.error('❌ TradeDetailsModal - Fehler bei Besichtigungserstellung:', error);
      alert('Fehler beim Erstellen der Besichtigung. Bitte versuchen Sie es erneut.');
    }
  };

  // Handler für Abnahme-Abschluss
  const handleCompleteAcceptance = async (acceptanceData: any) => {
    try {

      
      const response = await apiCall(`/milestones/${trade?.id}/acceptance`, {
        method: 'POST',
        body: JSON.stringify({
          accepted: acceptanceData.accepted,
          defects: acceptanceData.defects || [],
          photos: acceptanceData.photos || [],
          notes: acceptanceData.notes || ''
        })
      });


      
      // Schließe Modal
      setShowAcceptanceModal(false);
      
      // Aktualisiere Trade-Status
      if (acceptanceData.accepted) {
        if (acceptanceData.defects && acceptanceData.defects.length > 0) {
          setCompletionStatus('completed_with_defects');
        } else {
          setCompletionStatus('completed');
        }
      } else {
        setCompletionStatus('in_progress');
      }
      
      // Wenn Mängel vorhanden sind, öffne das finale Abnahme-Modal
      if (acceptanceData.defects && acceptanceData.defects.length > 0) {
        setAcceptanceDefects(acceptanceData.defects);
        setTimeout(() => {

          setShowFinalAcceptanceModal(true);
        }, 1000);
      }
      
    } catch (error) {
      console.error('❌ TradeDetailsModal - Fehler bei Abnahme-Abschluss:', error);
      alert('Fehler beim Abschluss der Abnahme. Bitte versuchen Sie es erneut.');
    }
  };

  if (!isOpen || !trade) return null;



  const totalQuotes = existingQuotes?.length ?? 0;
  const builderDocumentsCount = loadedDocuments.length > 0 ? loadedDocuments.length : (Array.isArray(trade.documents) ? trade.documents.length : 0);
  const requiresInspectionFlag = trade?.requires_inspection === true ||
    trade?.requires_inspection === 'true' ||
    (trade as any)?.requires_inspection === true ||
    (trade as any)?.requires_inspection === 'true';
  const hasInspectionInfo = requiresInspectionFlag || appointmentsForTrade.length > 0;
  const builderTabs: Array<{ key: BuilderTabKey; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }> = React.useMemo(() => {
    if (!isBautraegerUser) return [];
    const tabs: Array<{ key: BuilderTabKey; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }> = [
      { key: 'overview', label: '\u00dcbersicht', icon: Eye },
      { key: 'quotes', label: totalQuotes ? `Angebote (${totalQuotes})` : 'Angebote', icon: Calculator },
      { key: 'documents', label: builderDocumentsCount ? `Dokumente (${builderDocumentsCount})` : 'Dokumente', icon: FileText },
      { key: 'workflow', label: 'Fortschritt', icon: CheckSquare },
    ];
    if (hasInspectionInfo) {
      tabs.push({ key: 'inspection', label: 'Besichtigung', icon: Calendar });
    }
    return tabs;
  }, [isBautraegerUser, totalQuotes, builderDocumentsCount, hasInspectionInfo]);

  return (
    <>
      {/* BESICHTIGUNGSTERMIN BANNER - ÜBER DEM MODAL */}
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-[60] w-full max-w-4xl px-4">
        <div className="p-4 bg-blue-600 rounded-xl shadow-2xl border border-blue-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                <Calendar className="text-white" size={20} />
              </div>
              <div>
                <div className="text-white font-semibold">Besichtigungstermin vereinbart2 </div>
                <div className="text-blue-100 text-sm">30.08.2025, 14:00</div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-blue-100 text-sm">202 Dienstleister eingeladen</div>
                <div className="text-blue-200 text-xs">Seestrasse 2, 8610 Uster, Schweiz</div>
              </div>
              <button
                onClick={() => {
                  const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BuildWise//Inspection Scheduler//DE
BEGIN:VEVENT
UID:inspection-30082025@buildwise.app
DTSTAMP:20241215T120000Z
DTSTART:20250830T140000Z
DTEND:20250830T160000Z
SUMMARY:Besichtigungstermin - Sanitär- und Heizungsinstallation
DESCRIPTION:Besichtigungstermin für Sanitär- und Heizungsinstallation\\n\\nOrt: Seestrasse 2, 8610 Uster, Schweiz\\nOrtshinweise: Haupteingang verwenden\\nZusätzliche Ortsangaben: Erdgeschoss, Raum 101\\nParkmöglichkeiten: Parkplätze vor dem Gebäude verfügbar\\nZugangshinweise: Klingel bei Familie Keller\\nAnsprechpartner: Max Mustermann\\nTelefon: +41 44 123 45 67\\nE-Mail: max.mustermann@beispiel.ch\\nAlternativer Kontakt: Anna Beispiel (+41 79 987 65 43)\\nVorbereitungshinweise: Bitte Sicherheitsschuhe und Helm mitbringen\\nBesondere Anforderungen: Zugang nur mit Baustellenausweis
LOCATION:Seestrasse 2, 8610 Uster, Schweiz
END:VEVENT
END:VCALENDAR`;
                  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
                  const link = document.createElement('a');
                  link.href = URL.createObjectURL(blob);
                  link.download = 'Besichtigung_Sanitaer_Heizung_30-08-2025.ics';
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}
                className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                title="Termin als ICS-Datei herunterladen"
              >
                <Download size={16} />
                ICS
              </button>
            </div>
          </div>
          
          {/* Erweiterte Informationen - ausklappbar */}
          <div className="mt-4 pt-4 border-t border-blue-400/50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div className="space-y-2">
                <h4 className="text-blue-100 font-semibold flex items-center gap-2">
                  <MapPin size={16} />
                  Zusätzliche Ortsangaben (Schritt 2)
                </h4>
                <div className="space-y-1 pl-6 text-blue-50">
                  <div><strong>Ortshinweise:</strong> Haupteingang verwenden</div>
                  <div><strong>Zusätzliche Ortsangaben:</strong> Erdgeschoss, Raum 101</div>
                  <div><strong>Parkmöglichkeiten:</strong> Parkplätze vor dem Gebäude verfügbar</div>
                  <div><strong>Zugangshinweise:</strong> Klingel bei Familie Keller</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="text-blue-100 font-semibold flex items-center gap-2">
                  <User size={16} />
                  Kontaktinformationen (Schritt 3)
                </h4>
                <div className="space-y-1 pl-6 text-blue-50">
                  <div className="flex items-center gap-2">
                    <User size={12} />
                    <span>Max Mustermann</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone size={12} />
                    <span>+41 44 123 45 67</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail size={12} />
                    <span>max.mustermann@beispiel.ch</span>
                  </div>
                  <div className="text-xs">
                    <strong>Alternativer Kontakt:</strong> Anna Beispiel (+41 79 987 65 43)
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-blue-400/50 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-50">
              <div>
                <strong>Vorbereitungshinweise:</strong><br/>
                Bitte Sicherheitsschuhe und Helm mitbringen
              </div>
              <div>
                <strong>Besondere Anforderungen:</strong><br/>
                Zugang nur mit Baustellenausweis
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-gradient-to-br from-[#1a1a2e] to-[#2c3539] rounded-2xl shadow-2xl border border-gray-600/30 max-w-6xl w-full max-h-[95vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-600/30">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-[#ffbd59] to-[#ffa726] rounded-xl flex items-center justify-center text-white font-bold shadow-lg">
              {getCategoryIcon(trade.category || '').icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-bold text-white">{trade.title}</h2>
                
                {/* Benachrichtigungssymbol */}
                {hasUnreadMessages && (
                  <div className={`relative ${notificationBlink ? 'animate-pulse' : ''}`}>
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping opacity-75"></div>
                  </div>
                )}
                
                {/* BESICHTIGUNGSTERMIN BANNER - DIREKT UNTER TITEL */}
                <div className="mt-3 p-3 bg-blue-600 rounded-lg flex items-center justify-between w-full">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                      <Calendar className="text-white" size={16} />
                    </div>
                    <div>
                      <div className="text-white font-semibold text-sm">Besichtigungstermin vereinbart</div>
                      <div className="text-blue-100 text-xs">30.08.2025, 14:00</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-blue-100 text-xs">202 Dienstleister eingeladen</div>
                      <div className="text-blue-200 text-xs">Seestrasse 2, 8610 Uster, Schweiz</div>
                    </div>
                    <button
                      onClick={() => {
                        const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BuildWise//Inspection Scheduler//DE
BEGIN:VEVENT
UID:inspection-30082025@buildwise.app
DTSTAMP:20241215T120000Z
DTSTART:20250830T140000Z
DTEND:20250830T160000Z
SUMMARY:Besichtigungstermin - Sanitär- und Heizungsinstallation
DESCRIPTION:Besichtigungstermin für Sanitär- und Heizungsinstallation\\n\\nOrt: Seestrasse 2, 8610 Uster, Schweiz\\n\\nZUSÄTZLICHE ORTSANGABEN (SCHRITT 2):\\nOrtshinweise: Haupteingang verwenden\\nZusätzliche Ortsangaben: Erdgeschoss, Raum 101\\nParkmöglichkeiten: Parkplätze vor dem Gebäude verfügbar\\nZugangshinweise: Klingel bei Familie Keller\\n\\nKONTAKTINFORMATIONEN (SCHRITT 3):\\nAnsprechpartner: Max Mustermann\\nTelefon: +41 44 123 45 67\\nE-Mail: max.mustermann@beispiel.ch\\nAlternativer Kontakt: Anna Beispiel (+41 79 987 65 43)\\nVorbereitungshinweise: Bitte Sicherheitsschuhe und Helm mitbringen\\nBesondere Anforderungen: Zugang nur mit Baustellenausweis
LOCATION:Seestrasse 2, 8610 Uster, Schweiz
END:VEVENT
END:VCALENDAR`;
                        const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = 'Besichtigung_Sanitaer_Heizung_30-08-2025.ics';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                      }}
                      className="px-2 py-1 bg-white/20 hover:bg-white/30 text-white rounded text-xs font-medium flex items-center gap-1"
                      title="Termin als ICS-Datei herunterladen mit allen Informationen aus Schritt 2 und 3"
                    >
                      <Download size={12} />
                      ICS
                    </button>
                  </div>
                </div>
                
                {/* Erweiterte Informationen - ausklappbar */}
                <div className="mt-2 p-3 bg-blue-500/20 rounded-lg border border-blue-400/30">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="space-y-1">
                      <h4 className="text-blue-200 font-semibold flex items-center gap-1">
                        <MapPin size={12} />
                        Zusätzliche Ortsangaben (Schritt 2)
                      </h4>
                      <div className="space-y-1 pl-4 text-blue-100">
                        <div><strong>Ortshinweise:</strong> Haupteingang verwenden</div>
                        <div><strong>Zusätzliche Ortsangaben:</strong> Erdgeschoss, Raum 101</div>
                        <div><strong>Parkmöglichkeiten:</strong> Parkplätze vor dem Gebäude verfügbar</div>
                        <div><strong>Zugangshinweise:</strong> Klingel bei Familie Keller</div>
                      </div>
                    </div>
                    
                    <div className="space-y-1">
                      <h4 className="text-blue-200 font-semibold flex items-center gap-1">
                        <User size={12} />
                        Kontaktinformationen (Schritt 3)
                      </h4>
                      <div className="space-y-1 pl-4 text-blue-100">
                        <div className="flex items-center gap-1">
                          <User size={10} />
                          <span>Max Mustermann</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Phone size={10} />
                          <span>+41 44 123 45 67</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Mail size={10} />
                          <span>max.mustermann@beispiel.ch</span>
                        </div>
                        <div><strong>Alt. Kontakt:</strong> Anna Beispiel (+41 79 987 65 43)</div>
                        <div><strong>Vorbereitung:</strong> Sicherheitsschuhe und Helm mitbringen</div>
                        <div><strong>Anforderungen:</strong> Zugang nur mit Baustellenausweis</div>
                      </div>
                    </div>
                  </div>
                </div>
                {/* Bearbeiten Button: nur wenn kein Angebot angenommen und keine Angebote vorliegen */}
                {(() => {
                  const hasAccepted = (existingQuotes || []).some(q => String(q.status).toLowerCase() === 'accepted');
                  const hasAnyQuote = (existingQuotes || []).length > 0;
                  const disabled = hasAnyQuote;
                  const title = hasAccepted ? 'Bearbeiten nicht möglich, Angebot wurde bereits angenommen' : (hasAnyQuote ? 'Bearbeiten nicht möglich, es liegen bereits Angebote vor' : 'Gewerk bearbeiten');
                  return (
                    <button
                      onClick={() => { if (!disabled) { setIsEditing(true); setEditForm({ title: trade.title || '', description: trade.description || '', category: (trade as any).category || '', priority: (trade as any).priority || 'medium', planned_date: (trade as any).planned_date || '', notes: (trade as any).notes || '', requires_inspection: (trade as any).requires_inspection || false }); }}}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${disabled ? 'bg-white/5 text-gray-400 cursor-not-allowed opacity-50' : 'bg-white/10 text-white hover:bg-white/20'}`}
                      title={title}
                      disabled={disabled}
                    >
                      <CheckSquare size={14} />
                      Bearbeiten
                    </button>
                  );
                })()}
                {(completionStatus === 'completed' || completionStatus === 'completed_with_defects') && (
                  <div className="inline-flex items-center gap-1 px-3 py-1 bg-green-500/20 border border-green-500/30 text-green-300 rounded-full text-sm font-medium">
                    <CheckCircle size={14} />
                    {completionStatus === 'completed_with_defects' ? 'Unter Vorbehalt' : 'Abgeschlossen'}
                  </div>
                )}
                {(trade as any).requires_inspection && (
                  <div className="inline-flex items-center gap-1 px-3 py-1 bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded-full text-sm font-medium">
                    <Eye size={14} />
                    Besichtigung erforderlich
                  </div>
                )}
              </div>
              <p className="text-gray-400 text-sm">{trade.category}</p>
              



              
              {/* Besichtigungstermin Banner - wenn Termin vereinbart */}
              {appointmentsForTrade.length > 0 && (() => {
                const appointment = appointmentsForTrade[0] || {
                  id: 1,
                  scheduled_date: '2025-08-30T14:00:00',
                  scheduled_time_start: '14:00',
                  title: 'Besichtigungstermin',
                  location_address: 'Seestrasse 2, 8610 Uster, Schweiz',
                  location_notes: 'Haupteingang verwenden',
                  additional_location_info: 'Erdgeschoss, Raum 101',
                  parking_info: 'Parkplätze vor dem Gebäude verfügbar',
                  access_instructions: 'Klingel bei Familie Keller',
                  contact_person: 'Max Mustermann',
                  contact_phone: '+41 44 123 45 67',
                  contact_email: 'max.mustermann@beispiel.ch',
                  alternative_contact_person: 'Anna Beispiel',
                  alternative_contact_phone: '+41 79 987 65 43',
                  preparation_notes: 'Bitte Sicherheitsschuhe und Helm mitbringen',
                  special_requirements: 'Zugang nur mit Baustellenausweis',
                  invitations: Array(202).fill(null)
                };
                
                const generateAppointmentICS = () => {
                  const startDate = new Date(appointment.scheduled_date);
                  const endDate = new Date(startDate.getTime() + (appointment.duration_minutes || 120) * 60000);
                  
                  const formatDate = (date: Date) => {
                    return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
                  };

                  const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BuildWise//Inspection Scheduler//DE
BEGIN:VEVENT
UID:${appointment.id}@buildwise.app
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(startDate)}
DTEND:${formatDate(endDate)}
SUMMARY:${appointment.title || 'Besichtigungstermin'}
DESCRIPTION:${appointment.description || ''}\\n\\nOrt: ${appointment.location_address || appointment.location || 'Wird noch bekannt gegeben'}${appointment.location_notes ? `\\nOrtshinweise: ${appointment.location_notes}` : ''}${appointment.additional_location_info ? `\\nZusätzliche Ortsangaben: ${appointment.additional_location_info}` : ''}${appointment.parking_info ? `\\nParkmöglichkeiten: ${appointment.parking_info}` : ''}${appointment.access_instructions ? `\\nZugangshinweise: ${appointment.access_instructions}` : ''}${appointment.contact_person ? `\\nAnsprechpartner: ${appointment.contact_person}` : ''}${appointment.contact_phone ? `\\nTelefon: ${appointment.contact_phone}` : ''}${appointment.contact_email ? `\\nE-Mail: ${appointment.contact_email}` : ''}${appointment.alternative_contact_person ? `\\nAlternativer Kontakt: ${appointment.alternative_contact_person}${appointment.alternative_contact_phone ? ` (${appointment.alternative_contact_phone})` : ''}` : ''}${appointment.preparation_notes ? `\\nVorbereitungshinweise: ${appointment.preparation_notes}` : ''}${appointment.special_requirements ? `\\nBesondere Anforderungen: ${appointment.special_requirements}` : ''}
LOCATION:${appointment.location_address || appointment.location || ''}${appointment.location_notes ? `, ${appointment.location_notes}` : ''}
END:VEVENT
END:VCALENDAR`;

                  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
                  const link = document.createElement('a');
                  link.href = URL.createObjectURL(blob);
                  link.download = `Besichtigung_${trade?.title?.replace(/[^a-zA-Z0-9]/g, '_')}_${appointment.scheduled_date?.split('T')[0]}.ics`;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                };

                return (
                  <div className="mt-3 mb-4 p-4 bg-blue-600/20 border border-blue-500/40 rounded-xl">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                          <Calendar className="text-white" size={20} />
                        </div>
                        <div>
                          <div className="text-white font-semibold">Besichtigungstermin vereinbart</div>
                          <div className="text-blue-200 text-sm">
                            {new Date(appointment.scheduled_date).toLocaleDateString('de-DE')} um {appointment.scheduled_time_start || '14:00'}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="text-blue-200 text-sm">
                            {appointmentsForTrade.length > 0 && `${(appointment.invitations || []).length || 202} Dienstleister eingeladen`}
                          </div>
                          <div className="text-blue-300 text-xs">
                            {appointment.location_address || appointment.location || 'Seestrasse 2, 8610 Uster, Schweiz'}
                          </div>
                        </div>
                        <button
                          onClick={generateAppointmentICS}
                          className="px-3 py-2 bg-blue-500 hover:bg-blue-400 text-white rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                          title="Termin als ICS-Datei herunterladen"
                        >
                          <Download size={16} />
                          ICS
                        </button>
                      </div>
                    </div>
                    
                    {/* Erweiterte Informationen - ausklappbar */}
                    <div className="mt-3 pt-3 border-t border-blue-500/30">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div className="space-y-2">
                          <h4 className="text-blue-200 font-medium">Ortsangaben</h4>
                          {appointment.location_notes && (
                            <div className="text-blue-100">
                              <strong>Ortshinweise:</strong> {appointment.location_notes}
                            </div>
                          )}
                          {appointment.additional_location_info && (
                            <div className="text-blue-100">
                              <strong>Zusätzliche Ortsangaben:</strong> {appointment.additional_location_info}
                            </div>
                          )}
                          {appointment.parking_info && (
                            <div className="text-blue-100">
                              <strong>Parkmöglichkeiten:</strong> {appointment.parking_info}
                            </div>
                          )}
                          {appointment.access_instructions && (
                            <div className="text-blue-100">
                              <strong>Zugangshinweise:</strong> {appointment.access_instructions}
                            </div>
                          )}
                        </div>
                        
                        <div className="space-y-2">
                          <h4 className="text-blue-200 font-medium">Kontaktinformationen</h4>
                          {appointment.contact_person && (
                            <div className="flex items-center gap-2 text-blue-100">
                              <User size={14} />
                              <span>{appointment.contact_person}</span>
                            </div>
                          )}
                          {appointment.contact_phone && (
                            <div className="flex items-center gap-2 text-blue-100">
                              <Phone size={14} />
                              <span>{appointment.contact_phone}</span>
                            </div>
                          )}
                          {appointment.contact_email && (
                            <div className="flex items-center gap-2 text-blue-100">
                              <Mail size={14} />
                              <span>{appointment.contact_email}</span>
                            </div>
                          )}
                          {appointment.alternative_contact_person && (
                            <div className="text-blue-100 text-xs">
                              <strong>Alternativer Kontakt:</strong> {appointment.alternative_contact_person}
                              {appointment.alternative_contact_phone && ` (${appointment.alternative_contact_phone})`}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {(appointment.preparation_notes || appointment.special_requirements) && (
                        <div className="mt-3 pt-3 border-t border-blue-500/30">
                          {appointment.preparation_notes && (
                            <div className="text-blue-100 text-sm mb-2">
                              <strong>Vorbereitungshinweise:</strong> {appointment.preparation_notes}
                            </div>
                          )}
                          {appointment.special_requirements && (
                            <div className="text-blue-100 text-sm">
                              <strong>Besondere Anforderungen:</strong> {appointment.special_requirements}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}

              {/* Ausschreibungsdetails - immer sichtbar */}
              <div className="mt-3">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                  {/* Projektinformationen - nur wenn project verfügbar */}
                  {project && (
                    <>
                      <div className="flex items-center gap-2 text-gray-300">
                        <Building size={14} className="text-[#ffbd59]" />
                        <span className="text-gray-400">Projekt:</span>
                        <span className="font-medium text-white">{project.name || 'Nicht angegeben'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-300">
                        <Settings size={14} className="text-[#ffbd59]" />
                        <span className="text-gray-400">Typ:</span>
                        <span className="font-medium text-white">{getProjectTypeLabel(project.project_type) || 'Nicht angegeben'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-300">
                        <MapPin size={14} className="text-[#ffbd59]" />
                        <span className="text-gray-400">Standort:</span>
                        <span className="font-medium text-white">{project.address || project.location || project.city || 'Projektadresse nicht verfügbar'}</span>
                      </div>
                    </>
                  )}
                  
                  {/* Geplantes Datum - mit Fallback auf fullTradeData */}
                  {(fullTradeData?.planned_date || trade.planned_date) && (
                    <div className="flex items-center gap-2 text-gray-300">
                      <Calendar size={14} className="text-[#ffbd59]" />
                      <span className="text-gray-400">Geplant:</span>
                      <span className="font-medium text-white">
                        {new Date(fullTradeData?.planned_date || trade.planned_date).toLocaleDateString('de-DE')}
                      </span>
                    </div>
                  )}
                  
                  {/* Fallback für Projektname wenn kein project Objekt aber project_name verfügbar */}
                  {!project && trade.project_name && (
                    <div className="flex items-center gap-2 text-gray-300">
                      <Building size={14} className="text-[#ffbd59]" />
                      <span className="text-gray-400">Projekt:</span>
                      <span className="font-medium text-white">{trade.project_name}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-white/10"
          >
            <X size={24} />
          </button>
        </div>

        {/* Besichtigungstermin Banner */}
        {appointmentsForTrade.length > 0 && (() => {
          const appointment = appointmentsForTrade[0] || {
            id: 1,
            scheduled_date: '2025-08-30T14:00:00',
            scheduled_time_start: '14:00',
            title: 'Besichtigungstermin',
            location_address: 'Seestrasse 2, 8610 Uster, Schweiz',
            location_notes: 'Haupteingang verwenden',
            additional_location_info: 'Erdgeschoss, Raum 101',
            parking_info: 'Parkplätze vor dem Gebäude verfügbar',
            access_instructions: 'Klingel bei Familie Keller',
            contact_person: 'Max Mustermann',
            contact_phone: '+41 44 123 45 67',
            contact_email: 'max.mustermann@beispiel.ch',
            alternative_contact_person: 'Anna Beispiel',
            alternative_contact_phone: '+41 79 987 65 43',
            preparation_notes: 'Bitte Sicherheitsschuhe und Helm mitbringen',
            special_requirements: 'Zugang nur mit Baustellenausweis',
            invitations: Array(202).fill(null)
          };
          
          const generateAppointmentICS = () => {
            const startDate = new Date(appointment.scheduled_date);
            const endDate = new Date(startDate.getTime() + (appointment.duration_minutes || 120) * 60000);
            
            const formatDate = (date: Date) => {
              return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
            };

            const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BuildWise//Inspection Scheduler//DE
BEGIN:VEVENT
UID:${appointment.id}@buildwise.app
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(startDate)}
DTEND:${formatDate(endDate)}
SUMMARY:${appointment.title || 'Besichtigungstermin'}
DESCRIPTION:${appointment.description || ''}\\n\\nOrt: ${appointment.location_address || 'Seestrasse 2, 8610 Uster, Schweiz'}${appointment.location_notes ? `\\nOrtshinweise: ${appointment.location_notes}` : ''}${appointment.additional_location_info ? `\\nZusätzliche Ortsangaben: ${appointment.additional_location_info}` : ''}${appointment.parking_info ? `\\nParkmöglichkeiten: ${appointment.parking_info}` : ''}${appointment.access_instructions ? `\\nZugangshinweise: ${appointment.access_instructions}` : ''}${appointment.contact_person ? `\\nAnsprechpartner: ${appointment.contact_person}` : ''}${appointment.contact_phone ? `\\nTelefon: ${appointment.contact_phone}` : ''}${appointment.contact_email ? `\\nE-Mail: ${appointment.contact_email}` : ''}${appointment.alternative_contact_person ? `\\nAlternativer Kontakt: ${appointment.alternative_contact_person}${appointment.alternative_contact_phone ? ` (${appointment.alternative_contact_phone})` : ''}` : ''}${appointment.preparation_notes ? `\\nVorbereitungshinweise: ${appointment.preparation_notes}` : ''}${appointment.special_requirements ? `\\nBesondere Anforderungen: ${appointment.special_requirements}` : ''}
LOCATION:${appointment.location_address || 'Seestrasse 2, 8610 Uster, Schweiz'}
END:VEVENT
END:VCALENDAR`;

            const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `Besichtigung_${trade?.title?.replace(/[^a-zA-Z0-9]/g, '_')}_30-08-2025.ics`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          };

          return (
            <div className="p-4 bg-blue-600/20 border-b border-blue-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                    <Calendar className="text-white" size={20} />
                  </div>
                  <div>
                    <div className="text-white font-semibold">Besichtigungstermin vereinbart1</div>
                    <div className="text-blue-200 text-sm">30.08.2025, 14:00</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-blue-200 text-sm">202 Dienstleister eingeladen</div>
                    <div className="text-blue-300 text-xs">Seestrasse 2, 8610 Uster, Schweiz</div>
                  </div>
                  <button
                    onClick={generateAppointmentICS}
                    className="px-3 py-2 bg-blue-500 hover:bg-blue-400 text-white rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                    title="Termin als ICS-Datei herunterladen"
                  >
                    <Download size={16} />
                    ICS
                  </button>
                </div>
              </div>
              
              {/* Erweiterte Informationen */}
              <div className="mt-4 pt-4 border-t border-blue-500/30">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                  <div className="space-y-3">
                    <h4 className="text-blue-200 font-semibold flex items-center gap-2">
                      <MapPin size={16} />
                      Ortsangaben (Schritt 2)
                    </h4>
                    <div className="space-y-2 pl-6">
                      <div className="text-blue-100">
                        <strong>Ortshinweise:</strong> {appointment.location_notes}
                      </div>
                      <div className="text-blue-100">
                        <strong>Zusätzliche Ortsangaben:</strong> {appointment.additional_location_info}
                      </div>
                      <div className="text-blue-100">
                        <strong>Parkmöglichkeiten:</strong> {appointment.parking_info}
                      </div>
                      <div className="text-blue-100">
                        <strong>Zugangshinweise:</strong> {appointment.access_instructions}
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="text-blue-200 font-semibold flex items-center gap-2">
                      <User size={16} />
                      Kontaktinformationen (Schritt 3)
                    </h4>
                    <div className="space-y-2 pl-6">
                      <div className="flex items-center gap-2 text-blue-100">
                        <User size={14} />
                        <span>{appointment.contact_person}</span>
                      </div>
                      <div className="flex items-center gap-2 text-blue-100">
                        <Phone size={14} />
                        <span>{appointment.contact_phone}</span>
                      </div>
                      <div className="flex items-center gap-2 text-blue-100">
                        <Mail size={14} />
                        <span>{appointment.contact_email}</span>
                      </div>
                      <div className="text-blue-100 text-sm">
                        <strong>Alternativer Kontakt:</strong><br/>
                        {appointment.alternative_contact_person} ({appointment.alternative_contact_phone})
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-blue-500/30">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="text-blue-100">
                      <strong>Vorbereitungshinweise:</strong><br/>
                      {appointment.preparation_notes}
                    </div>
                    <div className="text-blue-100">
                      <strong>Besondere Anforderungen:</strong><br/>
                      {appointment.special_requirements}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}

        <div className="h-[calc(95vh-120px)] overflow-y-auto p-6">
          {/* Edit Modal Inline */}
          {isEditing && (
            <div className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
              <h3 className="text-white font-semibold mb-3">Gewerk bearbeiten</h3>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  try {
                    setIsUpdatingTrade(true);
                    const payload: any = {
                      title: editForm.title,
                      description: editForm.description,
                      category: editForm.category || undefined,
                      priority: editForm.priority || undefined,
                      planned_date: editForm.planned_date || undefined,
                      notes: editForm.notes || undefined,
                      requires_inspection: !!editForm.requires_inspection,
                    };
                    await updateMilestone((trade as any).id, payload);
                    // Lokal aktualisieren
                    (trade as any).title = payload.title || (trade as any).title;
                    (trade as any).description = payload.description || (trade as any).description;
                    (trade as any).category = payload.category ?? (trade as any).category;
                    (trade as any).priority = payload.priority ?? (trade as any).priority;
                    (trade as any).planned_date = payload.planned_date ?? (trade as any).planned_date;
                    (trade as any).notes = payload.notes ?? (trade as any).notes;
                    (trade as any).requires_inspection = payload.requires_inspection;
                    setIsEditing(false);
                  } catch (err) {
                    console.error('❌ Fehler beim Aktualisieren des Gewerks:', err);
                    alert('Fehler beim Aktualisieren des Gewerks');
                  } finally {
                    setIsUpdatingTrade(false);
                  }
                }}
                className="space-y-3"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-300 mb-1">Titel</label>
                    <input value={editForm.title} onChange={(e)=>setEditForm(p=>({...p,title:e.target.value}))} className="w-full px-3 py-2 bg-[#1a1a2e] border border-gray-700 rounded-lg text-white" />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-300 mb-1">Kategorie</label>
                    <input value={editForm.category||''} onChange={(e)=>setEditForm(p=>({...p,category:e.target.value}))} className="w-full px-3 py-2 bg-[#1a1a2e] border border-gray-700 rounded-lg text-white" />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-300 mb-1">Beschreibung</label>
                  <textarea rows={3} value={editForm.description} onChange={(e)=>setEditForm(p=>({...p,description:e.target.value}))} className="w-full px-3 py-2 bg-[#1a1a2e] border border-gray-700 rounded-lg text-white" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs text-gray-300 mb-1">Priorität</label>
                    <select value={editForm.priority||'medium'} onChange={(e)=>setEditForm(p=>({...p,priority:e.target.value}))} className="w-full px-3 py-2 bg-[#1a1a2e] border border-gray-700 rounded-lg text-white">
                      <option value="low">Niedrig</option>
                      <option value="medium">Mittel</option>
                      <option value="high">Hoch</option>
                      <option value="critical">Kritisch</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-300 mb-1">Geplantes Datum</label>
                    <input type="date" value={editForm.planned_date||''} onChange={(e)=>setEditForm(p=>({...p,planned_date:e.target.value}))} className="w-full px-3 py-2 bg-[#1a1a2e] border border-gray-700 rounded-lg text-white" />
                  </div>
                  <div className="flex items-center gap-2 mt-6">
                    <input id="requires_inspection_td" type="checkbox" checked={!!editForm.requires_inspection} onChange={(e)=>setEditForm(p=>({...p,requires_inspection:e.target.checked}))} className="w-4 h-4 text-[#ffbd59] bg-[#2c3539]/50 border-gray-600 rounded" />
                    <label htmlFor="requires_inspection_td" className="text-xs text-gray-300">Besichtigung erforderlich</label>
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-300 mb-1">Notizen</label>
                  <textarea rows={2} value={editForm.notes||''} onChange={(e)=>setEditForm(p=>({...p,notes:e.target.value}))} className="w-full px-3 py-2 bg-[#1a1a2e] border border-gray-700 rounded-lg text-white" />
                </div>
                <div className="flex justify-end gap-2">
                  <button type="button" onClick={()=>setIsEditing(false)} className="px-4 py-2 text-gray-300 hover:text-white">Abbrechen</button>
                  <button type="submit" disabled={isUpdatingTrade} className="px-4 py-2 bg-[#ffbd59] text-[#2c3539] rounded-lg font-semibold hover:bg-[#ffa726] disabled:opacity-50">{isUpdatingTrade?'Speichern…':'Speichern'}</button>
                </div>
              </form>
            </div>
          )}
          <div className="space-y-6">
            {isBautraegerUser && builderTabs.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 p-2 bg-[#111827] border border-gray-700/40 rounded-xl">
                {builderTabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeBuilderTab === tab.key;
                  const isWorkflowTab = tab.key === 'workflow';
                  const shouldBlink = isWorkflowTab && hasUnreadMessages && notificationBlink;
                  
                  return (
                    <button
                      key={tab.key}
                      onClick={() => handleTabClick(tab.key)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 relative ${
                        isActive ? 'bg-[#ffbd59] text-[#1a1a2e] shadow-lg' : 'bg-[#ffbd59]/10 text-gray-300 hover:bg-[#ffbd59]/20'
                      } ${shouldBlink ? 'animate-pulse' : ''}`}
                    >
                      <Icon size={16} className={isActive ? 'text-[#1a1a2e]' : 'text-[#ffbd59]'} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            )}

            <div className={isBautraegerUser ? (activeBuilderTab === 'overview' ? 'space-y-6' : 'hidden') : 'space-y-6'}>
            {/* Priorität und Phase */}
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#ffbd59]/20 text-[#ffbd59]">
                {trade.priority}
              </span>
              {/* Phase-Anzeige für completion_status */}
              <span className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getCompletionStatusColor(completionStatus)}`}>
                {getCompletionStatusIcon(completionStatus)}
                {getCompletionStatusLabel(completionStatus)}
              </span>
            </div>

            {/* Beschreibung */}
            {trade.description && (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <FileText size={18} className="text-[#ffbd59]" />
           Beschreibung
                </h3>
                <p className="text-gray-300 leading-relaxed">{trade.description}</p>
       </div>
            )}

            {/* Angenommenes Angebot - Details Abschnitt */}
            {isBautraegerUser && acceptedQuote && (
              <div className="bg-gradient-to-br from-emerald-500/10 to-green-500/10 rounded-xl p-6 border border-emerald-500/30">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-emerald-500/20 rounded-lg">
                    <CheckCircle size={20} className="text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Angenommenes Angebot</h3>
                    <p className="text-emerald-300 text-sm">Verbindlich best?tigt</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-gray-400 mb-1">Dienstleister</div>
                    <div className="text-white font-semibold">
                      {acceptedQuote.contact_released ?
                        (acceptedQuote.company_name || acceptedQuote.service_provider_name || `Angebot #${acceptedQuote.id}`) :
                        (acceptedQuote.service_provider_name || `Angebot #${acceptedQuote.id}`)}
                    </div>
                    {acceptedQuote.contact_person && (
                      <div className="text-gray-300 text-sm">{acceptedQuote.contact_person}</div>
                    )}
                  </div>

                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-gray-400 mb-1">Angebotssumme</div>
                    <div className="text-emerald-400 font-bold text-xl">
                      {(() => {
                        const currency = (acceptedQuote as any).currency || 'EUR';
                        const amount =
                          (typeof (acceptedQuote as any).total_amount === 'number' && (acceptedQuote as any).total_amount) ??
                          (typeof (acceptedQuote as any).total_price === 'number' && (acceptedQuote as any).total_price) ??
                          (typeof (acceptedQuote as any).labor_cost === 'number' || typeof (acceptedQuote as any).material_cost === 'number' || typeof (acceptedQuote as any).overhead_cost === 'number'
                            ? ((Number((acceptedQuote as any).labor_cost) || 0) + (Number((acceptedQuote as any).material_cost) || 0) + (Number((acceptedQuote as any).overhead_cost) || 0))
                            : null);
                        if (amount == null) return 'N/A';
                        return formatCurrency(amount, currency);
                      })()}
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-gray-400 mb-1">Dauer</div>
                    <div className="text-white font-semibold">
                      {(acceptedQuote as any).estimated_duration || 'Nicht angegeben'} Tage
                    </div>
                    {(acceptedQuote as any).start_date && (
                      <div className="text-gray-300 text-sm">
                        Start: {new Date((acceptedQuote as any).start_date).toLocaleDateString('de-DE')}
                      </div>
                    )}
                  </div>

                  {acceptedQuote.contact_released && acceptedQuote.phone && (
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Kontakt</div>
                      <div className="text-white font-semibold">{acceptedQuote.phone}</div>
                      {acceptedQuote.email && (
                        <div className="text-gray-300 text-sm">{acceptedQuote.email}</div>
                      )}
                    </div>
                  )}

                  {((acceptedQuote as any).labor_cost || (acceptedQuote as any).material_cost || (acceptedQuote as any).overhead_cost) && (
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Kostenaufschl?sselung</div>
                      <div className="space-y-1 text-sm">
                        {(acceptedQuote as any).labor_cost && (
                          <div className="flex justify-between">
                            <span className="text-gray-300">Arbeitskosten:</span>
                            <span className="text-white">{formatCurrency(Number((acceptedQuote as any).labor_cost), (acceptedQuote as any).currency)}</span>
                          </div>
                        )}
                        {(acceptedQuote as any).material_cost && (
                          <div className="flex justify-between">
                            <span className="text-gray-300">Materialkosten:</span>
                            <span className="text-white">{formatCurrency(Number((acceptedQuote as any).material_cost), (acceptedQuote as any).currency)}</span>
                          </div>
                        )}
                        {(acceptedQuote as any).overhead_cost && (
                          <div className="flex justify-between">
                            <span className="text-gray-300">Nebenkosten:</span>
                            <span className="text-white">{formatCurrency(Number((acceptedQuote as any).overhead_cost), (acceptedQuote as any).currency)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {(acceptedQuote as any).notes && (
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Notizen</div>
                      <div className="text-gray-300 text-sm whitespace-pre-line">{(acceptedQuote as any).notes}</div>
                    </div>
                  )}
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-300">
                    Angenommen am: {new Date((acceptedQuote as any).updated_at || acceptedQuote.created_at).toLocaleDateString('de-DE')}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); setQuoteForDetails(acceptedQuote); setShowQuoteDetails(true); }}
                      className="px-3 py-1.5 text-sm rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30"
                    >
                      Vollst?ndige Details
                    </button>
                    {(acceptedQuote as any).pdf_upload_path && (
                      <a
                        href={getAuthenticatedFileUrl((acceptedQuote as any).pdf_upload_path)}
                        download
                        className="px-3 py-1.5 text-sm rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30 hover:bg-blue-500/30"
                      >
                        PDF herunterladen
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )}


          </div>

            <div className={isBautraegerUser ? (activeBuilderTab === 'quotes' ? 'space-y-6' : 'hidden') : 'space-y-6'}>
            {/* DEBUG UND TERMINE FÜR DIENSTLEISTER - VOR ANGEBOTEN */}
            {(user?.user_role === 'DIENSTLEISTER' || user?.user_role === 'dienstleister' || user?.user_role === 'SERVICE_PROVIDER' || user?.user_role === 'service_provider') && (
              <>
                {/* Mein abgegebenes Angebot anzeigen */}
                {(() => {
                  const myQuote = (existingQuotes || []).find(q => q.service_provider_id === user?.id);
                  if (myQuote) {
                    return (
                      <div className="mb-4 p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-xl border border-green-500/30">
                        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                          <FileText size={18} className="text-green-400" />
                          Mein abgegebenes Angebot
                        </h3>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Angebotssumme:</span>
                            <span className="text-xl font-bold text-green-400">
                              {new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(myQuote.total_amount || 0)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Status:</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              myQuote.status === 'accepted' ? 'bg-green-500/20 text-green-300' :
                              myQuote.status === 'rejected' ? 'bg-red-500/20 text-red-300' :
                              myQuote.status === 'submitted' ? 'bg-blue-500/20 text-blue-300' :
                              'bg-gray-500/20 text-gray-300'
                            }`}>
                              {myQuote.status === 'accepted' ? 'Angenommen' :
                               myQuote.status === 'rejected' ? 'Abgelehnt' :
                               myQuote.status === 'submitted' ? 'Eingereicht' :
                               'Entwurf'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Geschätzte Dauer:</span>
                            <span className="text-white">{myQuote.estimated_duration || '–'} Tage</span>
                          </div>
                        </div>
                      </div>
                    );
                  }
                  return null;
                })()}




                {/* Terminvorschlag für Dienstleister */}
                {appointmentsForTrade.length > 0 && (() => {
                  const appointment = appointmentsForTrade[0];
                  const serviceProviderId = user?.id;
                  
                  // Prüfe Einladungs- und Antwortstatus
                  let invitedRaw: any = (appointment as any).invited_service_providers;
                  if (typeof invitedRaw === 'string') {
                    try { invitedRaw = JSON.parse(invitedRaw); } catch { invitedRaw = []; }
                  }
                  const invited: any[] = Array.isArray(invitedRaw) ? invitedRaw : [];
                  
                  let responsesRaw: any = (appointment as any).responses ?? (appointment as any).responses_array;
                  if (typeof responsesRaw === 'string') {
                    try { responsesRaw = JSON.parse(responsesRaw); } catch { responsesRaw = []; }
                  }
                  const responsesArr: any[] = Array.isArray(responsesRaw) ? responsesRaw : [];
                  
                  const isInvited = invited.some((sp: any) => Number(sp?.id ?? sp) === Number(serviceProviderId));
                  const myResponse = responsesArr.find((r: any) => Number(r?.service_provider_id) === Number(serviceProviderId));
                  const responseStatus = myResponse ? String(myResponse.status).toLowerCase() : 'pending';
                  
                  if (!isInvited) return null;
                  
                  return (
                    <div className="mb-4 p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
                      <div className="flex items-center justify-between gap-3 mb-3">
                        <div>
                          <div className="text-sm text-blue-300">Besichtigungstermin vorgeschlagen</div>
                          <div className="text-white font-semibold">
                            {new Date(appointment.scheduled_date).toLocaleString('de-DE')}
                          </div>
                          <div className="text-sm text-gray-400 mt-1">
                            📍 {appointment.location || 'Ort wird noch bekannt gegeben'}
                          </div>
                        </div>
                        {responseStatus === 'accepted' && (
                          <div className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">
                            ✅ Zugesagt
                          </div>
                        )}
                        {responseStatus === 'rejected' && (
                          <div className="px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 border border-red-500/30 text-red-300">
                            ❌ Abgesagt
                          </div>
                        )}
                      </div>
                      
                      {responseStatus === 'pending' && (
                        <div className="flex items-center gap-3">
                          <div className="text-sm text-gray-300 flex-1">
                            Bitte antworten Sie auf die Einladung:
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={async () => {
                                try {
                                  await appointmentService.respondToAppointment({
                                    appointment_id: appointment.id,
                                    status: 'accepted'
                                  });
                                  // Termine neu laden
                                  const all = await appointmentService.getMyAppointments();
                                  const relevant = all.filter(a => a.milestone_id === (trade as any).id && a.appointment_type === 'INSPECTION');
                                  setAppointmentsForTrade(relevant);
                                } catch (error) {
                                  console.error('❌ Fehler beim Zusagen:', error);
                                  alert('Fehler beim Zusagen des Termins');
                                }
                              }}
                              className="px-4 py-2 text-sm rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
                            >
                              ✅ Zusagen
                            </button>
                            <button
                              onClick={async () => {
                                try {
                                  await appointmentService.respondToAppointment({
                                    appointment_id: appointment.id,
                                    status: 'rejected'
                                  });
                                  // Termine neu laden
                                  const all = await appointmentService.getMyAppointments();
                                  const relevant = all.filter(a => a.milestone_id === (trade as any).id && a.appointment_type === 'INSPECTION');
                                  setAppointmentsForTrade(relevant);
                                } catch (error) {
                                  console.error('❌ Fehler beim Absagen:', error);
                                  alert('Fehler beim Absagen des Termins');
                                }
                              }}
                              className="px-4 py-2 text-sm rounded-lg bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30 transition-colors"
                            >
                              ❌ Absagen
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {/* Neues Angebot hochladen Button - nach der Besichtigung */}
                      {(() => {
                        const today = new Date();
                        today.setHours(0, 0, 0, 0);
                        
                        const appointmentDate = new Date(appointment.scheduled_date);
                        appointmentDate.setHours(0, 0, 0, 0);
                        
                        const isInspectionDay = today.getTime() === appointmentDate.getTime();
                        const isAfterInspection = today.getTime() > appointmentDate.getTime();
                        


                        
                        // Zeige Button wenn:
                        // 1. Besichtigung ist heute ODER vorbei
                        // 2. Dienstleister hat zugesagt (responseStatus === 'accepted')
                        // 3. Noch kein Angebot vorhanden
                        if ((isInspectionDay || isAfterInspection) && 
                            responseStatus === 'accepted' && 
                            !existingQuotes.some(q => q.service_provider_id === user?.id)) {
                          return (
                            <div className="mt-4 p-3 bg-gradient-to-r from-[#ffbd59]/10 to-[#ffa726]/10 border border-[#ffbd59]/30 rounded-lg">
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="text-sm font-semibold text-[#ffbd59]">
                                    🏗️ {isInspectionDay ? 'Besichtigung heute' : 'Besichtigung abgeschlossen'}
                                  </div>
                                  <div className="text-xs text-gray-400 mt-1">
                                    {isInspectionDay 
                                      ? 'Nach der Besichtigung können Sie ein Angebot hochladen'
                                      : `Besichtigung war am ${appointmentDate.toLocaleDateString('de-DE')}`
                                    }
                                  </div>
                                </div>
                                <button
                                  onClick={(e) => { 
                                    e.stopPropagation(); 
                                    onCreateQuote && trade && onCreateQuote(trade as any); 
                                  }}
                                  className="px-4 py-2 rounded-lg font-medium bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-black hover:shadow-lg transition-all duration-200"
                                >
                                  📄 Neues Angebot hochladen
                                </button>
                              </div>
                            </div>
                          );
                        }
                        
                        return null;
                      })()}
                    </div>
                  );
                })()}
              </>
            )}

            {/* Angebote - WICHTIG: Direkt nach Beschreibung anzeigen */}
            {(() => {
              // Sichtbare Angebote abhängig von Rolle filtern
              const isBt = isBautraegerUser;
              const visibleQuotes = isBt
                ? (existingQuotes || [])
                : (existingQuotes || []).filter(q => q.service_provider_id === user?.id);
              
              // Prüfe ob Besichtigung erforderlich ist
              const requiresInspection = trade.requires_inspection === true || 
                                       trade.requires_inspection === 'true' || 
                                       (trade as any).requires_inspection === true || 
                                       (trade as any).requires_inspection === 'true';
              

              
              return visibleQuotes && visibleQuotes.length > 0 ? (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Eye size={18} className="text-[#ffbd59]" />
                  {isBt 
                    ? `Eingegangene Angebote (${visibleQuotes.length})`
                    : (visibleQuotes.length > 1 
                        ? `Meine abgegebenen Gebote (${visibleQuotes.length})`
                        : 'Mein abgegebenes Gebot')}
                </h3>
                




                {/* Terminvorschlag für Dienstleister - Antwort erforderlich */}
                {user?.user_role === 'DIENSTLEISTER' && appointmentsForTrade.length > 0 && (() => {
                  const appointment = appointmentsForTrade[0];
                  const serviceProviderId = user?.id;
                  
                  // Prüfe Einladungs- und Antwortstatus
                  let invitedRaw: any = (appointment as any).invited_service_providers;
                  if (typeof invitedRaw === 'string') {
                    try { invitedRaw = JSON.parse(invitedRaw); } catch { invitedRaw = []; }
                  }
                  const invited: any[] = Array.isArray(invitedRaw) ? invitedRaw : [];
                  
                  let responsesRaw: any = (appointment as any).responses ?? (appointment as any).responses_array;
                  if (typeof responsesRaw === 'string') {
                    try { responsesRaw = JSON.parse(responsesRaw); } catch { responsesRaw = []; }
                  }
                  const responsesArr: any[] = Array.isArray(responsesRaw) ? responsesRaw : [];
                  
                  const isInvited = invited.some((sp: any) => Number(sp?.id ?? sp) === Number(serviceProviderId));
                  const myResponse = responsesArr.find((r: any) => Number(r?.service_provider_id) === Number(serviceProviderId));
                  const responseStatus = myResponse ? String(myResponse.status).toLowerCase() : 'pending';
                  
                  if (!isInvited) return null;
                  
                  return (
                    <div className="mb-4 p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
                      <div className="flex items-center justify-between gap-3 mb-3">
                        <div>
                          <div className="text-sm text-blue-300">Besichtigungstermin vorgeschlagen</div>
                          <div className="text-white font-semibold">
                            {new Date(appointment.scheduled_date).toLocaleString('de-DE')}
                          </div>
                          <div className="text-sm text-gray-400 mt-1">
                            📍 {appointment.location || 'Ort wird noch bekannt gegeben'}
                          </div>
                        </div>
                        {responseStatus === 'accepted' && (
                          <div className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">
                            ✅ Zugesagt
                          </div>
                        )}
                        {responseStatus === 'rejected' && (
                          <div className="px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 border border-red-500/30 text-red-300">
                            ❌ Abgesagt
                          </div>
                        )}
                      </div>
                      
                      {responseStatus === 'pending' && (
                        <div className="flex items-center gap-3">
                          <div className="text-sm text-gray-300 flex-1">
                            Bitte antworten Sie auf die Einladung:
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={async () => {
                                try {
                                  await appointmentService.respondToAppointment({
                                    appointment_id: appointment.id,
                                    status: 'accepted'
                                  });
                                  // Termine neu laden
                                  const all = await appointmentService.getMyAppointments();
                                  const relevant = all.filter(a => a.milestone_id === (trade as any).id && a.appointment_type === 'INSPECTION');
                                  setAppointmentsForTrade(relevant);
                                } catch (error) {
                                  console.error('❌ Fehler beim Zusagen:', error);
                                  alert('Fehler beim Zusagen des Termins');
                                }
                              }}
                              className="px-4 py-2 text-sm rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
                            >
                              ✅ Zusagen
                            </button>
                            <button
                              onClick={async () => {
                                try {
                                  await appointmentService.respondToAppointment({
                                    appointment_id: appointment.id,
                                    status: 'rejected'
                                  });
                                  // Termine neu laden
                                  const all = await appointmentService.getMyAppointments();
                                  const relevant = all.filter(a => a.milestone_id === (trade as any).id && a.appointment_type === 'INSPECTION');
                                  setAppointmentsForTrade(relevant);
                                } catch (error) {
                                  console.error('❌ Fehler beim Absagen:', error);
                                  alert('Fehler beim Absagen des Termins');
                                }
                              }}
                              className="px-4 py-2 text-sm rounded-lg bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30 transition-colors"
                            >
                              ❌ Absagen
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {responseStatus === 'accepted' && (
                        <div className="flex items-center gap-2 mt-2">
                          <button
                            onClick={async (e) => { e.stopPropagation(); await appointmentService.downloadCalendarEvent(appointment.id); }}
                            className="px-3 py-2 text-sm rounded-lg bg-emerald-500/20 text-emerald-200 border border-emerald-500/30 hover:bg-emerald-500/30"
                          >
                            📅 .ics herunterladen
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* Vereinbarter Termin für Bauträger (falls vorhanden) */}
                {user?.user_role === 'BAUTRAEGER' && appointmentsForTrade.length > 0 && (
                  <div className="mb-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm text-emerald-300">Vereinbarter Besichtigungstermin</div>
                        <div className="text-white font-semibold">
                          {new Date(appointmentsForTrade[0].scheduled_date).toLocaleString('de-DE')}
                        </div>
                      </div>
                      <button
                        onClick={async (e) => { e.stopPropagation(); await appointmentService.downloadCalendarEvent(appointmentsForTrade[0].id); }}
                        className="px-3 py-2 text-sm rounded-lg bg-emerald-500/20 text-emerald-200 border border-emerald-500/30 hover:bg-emerald-500/30"
                      >
                        .ics herunterladen
                      </button>
                    </div>
                  </div>
                )}
                <div className="space-y-3">
                  {visibleQuotes.map((quote) => {
                    const selectableStatuses = ['draft', 'submitted', 'under_review'];
                    const statusLower = String(quote.status).toLowerCase();
                    const isSelectable = isBt && selectableStatuses.includes(statusLower);
                    const isSelected = selectedQuoteIds.includes(quote.id);
                    // Ermittele Antwort-Status (accepted | rejected | pending) für diesen Dienstleister
                    const responseStatus = (() => {
                      if (!Array.isArray(appointmentsForTrade) || appointmentsForTrade.length === 0) return null;
                      let status: 'accepted' | 'rejected' | 'pending' | null = null;
                      for (const ap of appointmentsForTrade) {
                        // Invites können als String (JSON) oder Array kommen
                        let invitedRaw: any = (ap as any).invited_service_providers;
                        if (typeof invitedRaw === 'string') {
                          try { invitedRaw = JSON.parse(invitedRaw); } catch { invitedRaw = []; }
                        }
                        const invited: any[] = Array.isArray(invitedRaw) ? invitedRaw : [];

                        // Responses können ebenfalls String oder Array sein
                        let responsesRaw: any = (ap as any).responses ?? (ap as any).responses_array;
                        if (typeof responsesRaw === 'string') {
                          try { responsesRaw = JSON.parse(responsesRaw); } catch { responsesRaw = []; }
                        }
                        const responsesArr: any[] = Array.isArray(responsesRaw) ? responsesRaw : [];

                        const serviceProviderId = Number((quote as any).service_provider_id);
                        const isInvited = invited.some((sp: any) => Number(sp?.id ?? sp) === serviceProviderId);
                        const rsp = responsesArr.find((r: any) => Number(r?.service_provider_id) === serviceProviderId);

                        if (rsp) {
                          const s = String(rsp.status).toLowerCase();
                          if (s === 'accepted') return 'accepted';
                          if (s === 'rejected' || s === 'rejected_with_suggestion') status = 'rejected';
                        } else if (isInvited) {
                          // eingeladen, aber keine Antwort
                          status = 'pending';
                        }
                      }
                      return status;
                    })();
                    return (
                      <div
                        key={quote.id}
                        className={`relative bg-gradient-to-br from-[#1a1a2e]/30 to-[#2c3539]/30 rounded-lg p-4 border transition-all duration-200 ${
                          requiresInspection && isSelectable ? 'cursor-pointer' : 'cursor-default'
                        } ${
                          isSelected ? 'border-emerald-400 ring-4 ring-emerald-400/30 shadow-lg shadow-emerald-500/30' : 'border-gray-600/20 hover:border-emerald-400/50'
                        } ${isSelectable ? '' : 'opacity-90'}`}
                        onClick={() => {
                          // Nur bei Besichtigung erforderlich und selektierbar
                          if (!requiresInspection || !isSelectable) return;
                          setSelectedQuoteIds(prev => prev.includes(quote.id) ? prev.filter(id => id !== quote.id) : [...prev, quote.id]);
                        }}
                      >
                        {requiresInspection && isSelected && (
                          <div className="pointer-events-none absolute -top-2 -right-2 w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-lg z-20">
                            <CheckCircle size={16} />
                          </div>
                        )}
                        <div className="flex items-center justify-between relative z-10">
                          <div>
                            <p className="text-white font-medium">
                              {quote.status === 'accepted' && quote.contact_released ? 
                                (quote.company_name || quote.service_provider_name || `Angebot #${quote.id}`) :
                                (quote.service_provider_name || `Angebot #${quote.id}`)}
                            </p>
                            <p className="text-gray-400 text-sm">
                              {new Date(quote.created_at).toLocaleDateString('de-DE')}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-white font-bold">
                              {(() => {
                                const currency = (quote as any).currency || 'EUR';
                                const amount =
                                  (typeof (quote as any).total_amount === 'number' && (quote as any).total_amount) ??
                                  (typeof (quote as any).total_price === 'number' && (quote as any).total_price) ??
                                  (typeof (quote as any).labor_cost === 'number' || typeof (quote as any).material_cost === 'number' || typeof (quote as any).overhead_cost === 'number'
                                    ? ((Number((quote as any).labor_cost) || 0) + (Number((quote as any).material_cost) || 0) + (Number((quote as any).overhead_cost) || 0))
                                    : null);
                                if (amount == null) return 'N/A';
                                try {
                                  return amount.toLocaleString('de-DE', { style: 'currency', currency });
                                } catch {
                                  return `${amount.toLocaleString('de-DE')} €`;
                                }
                              })()}
                            </p>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getQuoteStatusColor(quote.status)}`}>
                              {getQuoteStatusLabel(quote.status)}
                            </span>
                            {responseStatus === 'accepted' && (
                              <div className="mt-2">
                                <span className="px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/20 border border-emerald-500/30 text-emerald-300">Besichtigung zugesagt</span>
                              </div>
                            )}
                            {responseStatus === 'rejected' && (
                              <div className="mt-2">
                                <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-500/20 border border-red-500/30 text-red-300">Besichtigung abgelehnt</span>
                              </div>
                            )}
                            {responseStatus === 'pending' && (
                              <div className="mt-2">
                                <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 border border-blue-500/30 text-blue-300">Besichtigung: ausstehend</span>
                              </div>
                            )}
                            <div className="mt-2 flex flex-wrap gap-2 justify-end">
                              {/* Bauträger: Direktannahme/Ablehnung nur wenn KEINE Besichtigung erforderlich */}
                              {isBt && !requiresInspection && (
                                <>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); setQuoteIdToAccept(quote.id); setAcceptAcknowledged(false); setShowAcceptConfirm(true); }}
                                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30"
                                  >✅ Annehmen</button>
                                  <div className="relative group inline-block">
                                    <button
                                      onClick={(e) => { e.stopPropagation(); }}
                                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30"
                                    >❌ Ablehnen</button>
                                    <div className="absolute right-0 mt-2 w-64 bg-[#0f172a] border border-white/10 rounded-xl shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition p-3 z-20">
                                      <div className="text-xs text-gray-300 mb-2">Begründung (optional)</div>
                                      <textarea id={`reject-reason-${quote.id}`} className="w-full bg-white/5 border border-white/10 rounded-lg text-white text-xs p-2 outline-none focus:border-white/20" rows={3} placeholder="Kurze Begründung..." />
                                      <div className="mt-2 flex justify-end gap-2">
                                        <button className="px-2 py-1 text-xs bg-white/10 border border-white/10 rounded-lg text-white hover:bg-white/15" onClick={(e)=>{e.stopPropagation(); (document.getElementById(`reject-reason-${quote.id}`) as HTMLTextAreaElement).value='';}}>Zurücksetzen</button>
                                        <button className="px-3 py-1 text-xs bg-red-500/20 border border-red-500/30 text-red-300 rounded-lg hover:bg-red-500/30" onClick={(e)=>{ e.stopPropagation(); const reason=(document.getElementById(`reject-reason-${quote.id}`) as HTMLTextAreaElement).value; (window as any).__onRejectQuote && (window as any).__onRejectQuote(quote.id, reason); }}>Senden</button>
                                      </div>
                                    </div>
                                  </div>
                                </>
                              )}
                              
                              {/* Bauträger: Bei Besichtigung erforderlich - deaktivierte Buttons mit Hinweisen */}
                              {isBt && requiresInspection && (
                                <>
                                  {/* Prüfe ob bereits eine Besichtigung vereinbart wurde */}
                                  {appointmentsForTrade.length > 0 ? (
                                    <>
                                      <button
                                        onClick={(e) => { e.stopPropagation(); setQuoteIdToAccept(quote.id); setAcceptAcknowledged(false); setShowAcceptConfirm(true); }}
                                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30"
                                      >✅ Annehmen</button>
                                      <div className="relative group inline-block">
                                        <button
                                          onClick={(e) => { e.stopPropagation(); }}
                                          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30"
                                        >❌ Ablehnen</button>
                                        <div className="absolute right-0 mt-2 w-64 bg-[#0f172a] border border-white/10 rounded-xl shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition p-3 z-20">
                                          <div className="text-xs text-gray-300 mb-2">Begründung (optional)</div>
                                          <textarea id={`reject-reason-${quote.id}`} className="w-full bg-white/5 border border-white/10 rounded-lg text-white text-xs p-2 outline-none focus:border-white/20" rows={3} placeholder="Kurze Begründung..." />
                                          <div className="mt-2 flex justify-end gap-2">
                                            <button className="px-2 py-1 text-xs bg-white/10 border border-white/10 rounded-lg text-white hover:bg-white/15" onClick={(e)=>{e.stopPropagation(); (document.getElementById(`reject-reason-${quote.id}`) as HTMLTextAreaElement).value='';}}>Zurücksetzen</button>
                                            <button className="px-3 py-1 text-xs bg-red-500/20 border border-red-500/30 text-red-300 rounded-lg hover:bg-red-500/30" onClick={(e)=>{ e.stopPropagation(); const reason=(document.getElementById(`reject-reason-${quote.id}`) as HTMLTextAreaElement).value; (window as any).__onRejectQuote && (window as any).__onRejectQuote(quote.id, reason); }}>Senden</button>
                                          </div>
                                        </div>
                                      </div>
                                    </>
                                  ) : (
                                    <>
                                      {/* Deaktivierte Buttons mit Tooltips */}
                                      <div className="relative group inline-block">
                                        <button
                                          disabled
                                          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-500/20 text-gray-400 border border-gray-500/30 cursor-not-allowed opacity-60"
                                        >✅ Annehmen</button>
                                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 bg-[#0f172a] border border-[#ffbd59]/30 rounded-xl shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition p-3 z-20">
                                          <div className="flex items-center gap-2 mb-2">
                                            <Eye size={14} className="text-[#ffbd59]" />
                                            <span className="text-xs font-medium text-[#ffbd59]">Besichtigung erforderlich</span>
                                          </div>
                                          <p className="text-xs text-gray-300">
                                            Vereinbaren Sie zuerst eine Besichtigung über den Button "Besichtigung vereinbaren" unten, bevor Sie das Angebot annehmen können.
                                          </p>
                                        </div>
                                      </div>
                                      <div className="relative group inline-block">
                                        <button
                                          disabled
                                          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-500/20 text-gray-400 border border-gray-500/30 cursor-not-allowed opacity-60"
                                        >❌ Ablehnen</button>
                                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 bg-[#0f172a] border border-red-500/30 rounded-xl shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition p-3 z-20">
                                          <div className="flex items-center gap-2 mb-2">
                                            <Eye size={14} className="text-red-400" />
                                            <span className="text-xs font-medium text-red-400">Besichtigung erforderlich</span>
                                          </div>
                                          <p className="text-xs text-gray-300">
                                            Auch für eine Ablehnung sollte idealerweise eine Besichtigung stattgefunden haben. Vereinbaren Sie zuerst einen Termin.
                                          </p>
                                        </div>
                                      </div>
                                    </>
                                  )}
                                </>
                              )}

                              <button
                                onClick={(e) => { e.stopPropagation(); setQuoteForDetails(quote); setShowQuoteDetails(true); }}
                                className="group relative inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-white text-xs overflow-hidden"
                              >
                                <span className="absolute inset-0 bg-gradient-to-r from-[#ffbd59]/0 via-[#ffbd59]/20 to-[#ffbd59]/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500" />
                                <Eye size={14} className="text-[#ffbd59]" />
                                Details ansehen
                              </button>
                            </div>
                          </div>
                        </div>
                        {requiresInspection && isSelectable && (
                          <p className="mt-2 text-xs text-gray-400">💡 Karte anklicken, um für Besichtigung auszuwählen.</p>
                        )}
                        {requiresInspection && isBt && appointmentsForTrade.length === 0 && (
                          <div className="mt-2 p-2 bg-[#ffbd59]/10 border border-[#ffbd59]/20 rounded-lg">
                            <p className="text-xs text-[#ffbd59] font-medium flex items-center gap-1">
                              <Eye size={12} />
                              Besichtigung erforderlich: Wählen Sie Angebote aus und vereinbaren Sie unten einen Termin.
                            </p>
                          </div>
                        )}
                        {requiresInspection && isBt && appointmentsForTrade.length > 0 && (
                          <div className="mt-2 p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                            <p className="text-xs text-emerald-300 font-medium flex items-center gap-1">
                              ✅ Besichtigung vereinbart: Sie können nun Angebote annehmen oder ablehnen.
                            </p>
                          </div>
                        )}
                        {!requiresInspection && isBt && (
                          <p className="mt-2 text-xs text-gray-400">💡 Verwenden Sie die Buttons oben für direkte Annahme/Ablehnung.</p>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Auswahl-Aktionsleiste (nur Bauträger und nur bei Besichtigung erforderlich) */}
                {isBt && requiresInspection && (
                  <div className="mt-4 p-4 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-xl border border-blue-500/30">
                    <div className="flex items-center gap-2 mb-3">
                      <Eye size={16} className="text-blue-400" />
                      <h4 className="text-white font-semibold">Besichtigung erforderlich</h4>
                    </div>
                    
                    {/* Workflow-Hinweis */}
                    {appointmentsForTrade.length === 0 && (
                      <div className="mb-4 p-3 bg-[#ffbd59]/10 border border-[#ffbd59]/20 rounded-lg">
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 bg-[#ffbd59] text-black rounded-full flex items-center justify-center text-xs font-bold">1</div>
                          <div className="flex-1">
                            <p className="text-sm text-[#ffbd59] font-medium">Workflow: Besichtigung vor Annahme</p>
                            <p className="text-xs text-gray-300 mt-1">
                              Wählen Sie Angebote aus und vereinbaren Sie eine Besichtigung. Erst danach können Sie Angebote annehmen oder ablehnen.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-300">
                        {selectedQuoteIds.length > 0 ? 
                          `${selectedQuoteIds.length} Angebot${selectedQuoteIds.length > 1 ? 'e' : ''} für Besichtigung ausgewählt` : 
                          'Wählen Sie Angebote für die Besichtigung aus'
                        }
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          className="px-3 py-2 text-sm bg-white/10 border border-white/20 rounded-lg text-white hover:bg-white/15"
                          onClick={() => {
                            // Alle auswählbaren Angebote markieren
                            const selectable = (existingQuotes || [])
                              .filter(q => ['draft','submitted','under_review'].includes(String(q.status).toLowerCase()))
                              .map(q => q.id);
                            setSelectedQuoteIds(selectable);
                          }}
                        >Alle auswählen</button>
                        <button
                          className="px-3 py-2 text-sm bg-white/10 border border-white/20 rounded-lg text-white hover:bg-white/15"
                          onClick={() => setSelectedQuoteIds([])}
                        >Auswahl löschen</button>
                        {/* Besichtigung vereinbaren Button */}
                        <button
                          className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all duration-300 ${
                            appointmentsForTrade.length > 0 || selectedQuoteIds.length === 0 || !trade?.id
                              ? 'bg-gray-500/20 text-gray-400 border border-gray-500/30 cursor-not-allowed opacity-50'
                              : 'bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-black hover:shadow-lg hover:shadow-[#ffbd59]/30 animate-pulse'
                          }`}
                          disabled={appointmentsForTrade.length > 0 || selectedQuoteIds.length === 0 || !trade?.id}
                          onClick={() => setShowInspectionScheduling(true)}
                        >
                          🗓️ Besichtigung vereinbaren ({selectedQuoteIds.length})
                        </button>
                      </div>
                    </div>
                    {appointmentsForTrade.length > 0 && (() => {
                      const appointment = appointmentsForTrade[0];
                      
                      const generateAppointmentICS = () => {
                        const startDate = new Date(appointment.scheduled_date);
                        const endDate = new Date(startDate.getTime() + (appointment.duration_minutes || 120) * 60000);
                        
                        const formatDate = (date: Date) => {
                          return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
                        };

                        const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BuildWise//Inspection Scheduler//DE
BEGIN:VEVENT
UID:${appointment.id}@buildwise.app
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(startDate)}
DTEND:${formatDate(endDate)}
SUMMARY:${appointment.title || 'Besichtigungstermin'}
DESCRIPTION:${appointment.description || ''}\\n\\nOrt: ${appointment.location_address || appointment.location || 'Wird noch bekannt gegeben'}${appointment.location_notes ? `\\nOrtshinweise: ${appointment.location_notes}` : ''}${appointment.additional_location_info ? `\\nZusätzliche Ortsangaben: ${appointment.additional_location_info}` : ''}${appointment.parking_info ? `\\nParkmöglichkeiten: ${appointment.parking_info}` : ''}${appointment.access_instructions ? `\\nZugangshinweise: ${appointment.access_instructions}` : ''}${appointment.contact_person ? `\\nAnsprechpartner: ${appointment.contact_person}` : ''}${appointment.contact_phone ? `\\nTelefon: ${appointment.contact_phone}` : ''}${appointment.contact_email ? `\\nE-Mail: ${appointment.contact_email}` : ''}${appointment.alternative_contact_person ? `\\nAlternativer Kontakt: ${appointment.alternative_contact_person}${appointment.alternative_contact_phone ? ` (${appointment.alternative_contact_phone})` : ''}` : ''}${appointment.preparation_notes ? `\\nVorbereitungshinweise: ${appointment.preparation_notes}` : ''}${appointment.special_requirements ? `\\nBesondere Anforderungen: ${appointment.special_requirements}` : ''}
LOCATION:${appointment.location_address || appointment.location || ''}${appointment.location_notes ? `, ${appointment.location_notes}` : ''}
END:VEVENT
END:VCALENDAR`;

                        const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = `Besichtigung_${trade?.title?.replace(/[^a-zA-Z0-9]/g, '_')}_${appointment.scheduled_date?.split('T')[0]}.ics`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                      };

                      return (
                        <div className="mt-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-3">
                                <CheckCircle className="text-emerald-400" size={20} />
                                <span className="text-emerald-300 font-semibold">Besichtigungstermin vereinbart2</span>
                              </div>
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                <div className="space-y-2">
                                  <div className="flex items-center gap-2">
                                    <Calendar className="text-emerald-400" size={16} />
                                    <span className="text-white font-medium">
                                      {new Date(appointment.scheduled_date).toLocaleString('de-DE')}
                                    </span>
                                  </div>
                                  
                                  {(appointment.location_address || appointment.location) && (
                                    <div className="flex items-start gap-2">
                                      <MapPin className="text-emerald-400 mt-0.5" size={16} />
                                      <div>
                                        <div className="text-white">{appointment.location_address || appointment.location}</div>
                                        {appointment.location_notes && (
                                          <div className="text-gray-300 text-xs mt-1">
                                            <strong>Ortshinweise:</strong> {appointment.location_notes}
                                          </div>
                                        )}
                                        {appointment.additional_location_info && (
                                          <div className="text-gray-300 text-xs mt-1">
                                            <strong>Zusätzliche Ortsangaben:</strong> {appointment.additional_location_info}
                                          </div>
                                        )}
                                        {appointment.parking_info && (
                                          <div className="text-gray-300 text-xs mt-1">
                                            <strong>Parkmöglichkeiten:</strong> {appointment.parking_info}
                                          </div>
                                        )}
                                        {appointment.access_instructions && (
                                          <div className="text-gray-300 text-xs mt-1">
                                            <strong>Zugangshinweise:</strong> {appointment.access_instructions}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )}
                                </div>
                                
                                <div className="space-y-2">
                                  {appointment.contact_person && (
                                    <div className="flex items-center gap-2">
                                      <User className="text-emerald-400" size={16} />
                                      <span className="text-white">{appointment.contact_person}</span>
                                    </div>
                                  )}
                                  
                                  {appointment.contact_phone && (
                                    <div className="flex items-center gap-2">
                                      <Phone className="text-emerald-400" size={16} />
                                      <span className="text-white">{appointment.contact_phone}</span>
                                    </div>
                                  )}
                                  
                                  {appointment.contact_email && (
                                    <div className="flex items-center gap-2">
                                      <Mail className="text-emerald-400" size={16} />
                                      <span className="text-white">{appointment.contact_email}</span>
                                    </div>
                                  )}
                                  
                                  {appointment.alternative_contact_person && (
                                    <div className="text-xs text-gray-300 mt-2">
                                      <strong>Alternativer Kontakt:</strong> {appointment.alternative_contact_person}
                                      {appointment.alternative_contact_phone && ` (${appointment.alternative_contact_phone})`}
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                              {(appointment.preparation_notes || appointment.special_requirements) && (
                                <div className="mt-3 pt-3 border-t border-emerald-500/20">
                                  {appointment.preparation_notes && (
                                    <div className="text-xs text-gray-300 mb-2">
                                      <strong>Vorbereitungshinweise:</strong> {appointment.preparation_notes}
                                    </div>
                                  )}
                                  {appointment.special_requirements && (
                                    <div className="text-xs text-gray-300">
                                      <strong>Besondere Anforderungen:</strong> {appointment.special_requirements}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                            
                            <button
                              onClick={generateAppointmentICS}
                              className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                              title="Termin als ICS-Datei herunterladen"
                            >
                              <Download size={16} />
                              ICS
                            </button>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Hinweis für Direktannahme ohne Besichtigung */}
                {isBt && !requiresInspection && (
                  <div className="mt-4 p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-xl border border-green-500/30">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle size={16} className="text-green-400" />
                      <h4 className="text-white font-semibold">Direktannahme möglich</h4>
                    </div>
                    <p className="text-sm text-gray-300">
                      Für dieses Gewerk ist keine Besichtigung erforderlich. Sie können Angebote direkt über die "Annehmen" und "Ablehnen" Buttons verwalten.
                    </p>
                  </div>
                )}

                {/* Dienstleister: Nachbesichtigungs-Angebot hochladen */}
                {!isBt && (() => {
                  // Prüfe ob Besichtigung stattgefunden hat
                  const appointment = appointmentsForTrade[0];
                  if (!appointment) return false;
                  
                  const today = new Date();
                  today.setHours(0, 0, 0, 0);
                  
                  const appointmentDate = new Date(appointment.scheduled_date);
                  appointmentDate.setHours(0, 0, 0, 0);
                  
                  // Prüfe ob heute der Besichtigungstag ist ODER ob er bereits vorbei ist
                  const isInspectionDay = today.getTime() === appointmentDate.getTime();
                  const isAfterInspection = today.getTime() > appointmentDate.getTime();
                  const hasAcceptedAppointment = appointment.responses_array?.some((r: any) => 
                    r.service_provider_id === user?.id && r.status === 'accepted'
                  );
                  


                  
                  // Zeige Button wenn:
                  // 1. Heute ist der Besichtigungstag ODER die Besichtigung war bereits
                  // 2. Dienstleister hat den Termin zugesagt
                  // 3. Noch kein Angebot wurde angenommen
                  if ((isInspectionDay || isAfterInspection) && hasAcceptedAppointment && !acceptedQuote) {
                    return (
                      <div className="mt-4 p-4 bg-gradient-to-r from-[#ffbd59]/10 to-[#ffa726]/10 border border-[#ffbd59]/30 rounded-xl">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="text-sm font-semibold text-[#ffbd59] mb-1">
                              🏗️ {isInspectionDay ? 'Besichtigung heute' : 'Besichtigung abgeschlossen'}
                            </h4>
                            <p className="text-xs text-gray-400">
                              {isInspectionDay 
                                ? 'Nach der Besichtigung können Sie ein neues Angebot hochladen'
                                : `Besichtigung war am ${appointmentDate.toLocaleDateString('de-DE')} - Sie können jetzt ein neues Angebot hochladen`
                              }
                            </p>
                          </div>
                          <button
                            onClick={(e) => { 
                              e.stopPropagation(); 
                              onCreateQuote && trade && onCreateQuote(trade as any); 
                            }}
                            className="px-4 py-2 rounded-lg font-medium bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-black hover:shadow-lg transition-all duration-200"
                          >
                            📄 Neues Angebot hochladen
                          </button>
                        </div>
                      </div>
                    );
                  }
                  
                  // Zeige Info wenn Besichtigung noch bevorsteht
                  if (!isInspectionDay && !isAfterInspection && hasAcceptedAppointment && !acceptedQuote) {
                    return (
                      <div className="mt-4 p-4 bg-gray-500/10 border border-gray-500/30 rounded-xl">
                        <div className="flex items-center gap-2">
                          <Clock size={16} className="text-gray-400" />
                          <div>
                            <p className="text-sm text-gray-300">
                              Besichtigung geplant für {appointmentDate.toLocaleDateString('de-DE')}
                            </p>
                            <p className="text-xs text-gray-400">
                              Nach der Besichtigung können Sie ein neues Angebot hochladen
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  }
                  
                  return null;
                })()}
              </div>
              ) : null;
            })()}

            {/* Quote Details Modal */}
            <QuoteDetailsModal
              isOpen={showQuoteDetails}
              onClose={() => { setShowQuoteDetails(false); setQuoteForDetails(null); }}
              quote={quoteForDetails as any}
              trade={trade as any}
              project={{ id: (trade as any)?.project_id, name: (trade as any)?.project_name }}
              user={user}
              onEditQuote={() => {}}
              onDeleteQuote={() => {}}
            />

            {/* Annahme-Bestätigung */}
            {showAcceptConfirm && (
              <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex items-center justify-center p-4">
                <div className="bg-[#0f172a]/95 border border-white/10 rounded-2xl max-w-lg w-full p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <CheckCircle size={20} className="text-emerald-400" />
                    <h3 className="text-white text-lg font-semibold">Angebot verbindlich annehmen?</h3>
                  </div>
                  <p className="text-gray-300 text-sm mb-4">
                    Mit der Annahme wird dieses Angebot als verbindlich markiert. Der Dienstleister wird benachrichtigt
                    und Folgeschritte (z. B. Auftragsbestätigung) werden aktiviert.
                  </p>
                  {(() => {
                    const otherQuotes = (existingQuotes || []).filter(q => 
                      q.id !== quoteIdToAccept && 
                      !['accepted', 'rejected'].includes(String(q.status).toLowerCase())
                    );
                    
                    return (
                      <div className="bg-white/5 border border-white/10 rounded-lg p-3 text-xs text-gray-300 mb-5">
                        <ul className="list-disc list-inside space-y-1">
                          <li>Die bisherigen Angebote bleiben zur Dokumentation erhalten.</li>
                          <li>Du kannst die Annahme später über „Zurücksetzen" widerrufen.</li>
                          <li>Finanzübersicht und Status werden automatisch aktualisiert.</li>
                          {otherQuotes.length > 0 && (
                            <li className="text-yellow-300 font-medium">
                              ⚠️ {otherQuotes.length} andere Angebot{otherQuotes.length > 1 ? 'e' : ''} 
                              {otherQuotes.length > 1 ? ' werden' : ' wird'} automatisch abgelehnt.
                            </li>
                          )}
                        </ul>
                      </div>
                    );
                  })()}
                  <label className="flex items-start gap-3 mb-4 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      className="mt-0.5 w-4 h-4 accent-[#ffbd59]"
                      checked={acceptAcknowledged}
                      onChange={(e) => setAcceptAcknowledged(e.target.checked)}
                    />
                    <span className="text-sm text-gray-300">Ich habe verstanden, dass die Annahme verbindlich ist und entsprechende Folgeschritte ausgelöst werden.</span>
                  </label>
                  <div className="flex justify-end gap-2">
                    <button
                      className="px-4 py-2 rounded-lg bg-white/10 border border-white/10 text-white hover:bg-white/15"
                      onClick={() => { setShowAcceptConfirm(false); setQuoteIdToAccept(null); }}
                    >Abbrechen</button>
                    <button
                      disabled={!acceptAcknowledged}
                      className={`px-4 py-2 rounded-lg font-semibold transition-shadow ${acceptAcknowledged ? 'bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-black hover:shadow-lg' : 'bg-white/10 text-white/60 cursor-not-allowed border border-white/10'}`}
                      onClick={() => { if (!acceptAcknowledged) return; if (quoteIdToAccept != null) { (window as any).__onAcceptQuote && (window as any).__onAcceptQuote(quoteIdToAccept); } setShowAcceptConfirm(false); setQuoteIdToAccept(null); }}
                    >Verbindlich annehmen</button>
                  </div>
                </div>
       </div>
            )}





            {/* Zeitplan */}
            <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Calendar size={18} className="text-[#ffbd59]" />
                Zeitplan
           </h3>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             {trade.planned_date && (
               <div>
                    <span className="text-sm font-medium text-gray-400">Geplantes Datum</span>
                    <p className="text-white">
                   {new Date(trade.planned_date).toLocaleDateString('de-DE')}
                 </p>
               </div>
             )}
             {trade.start_date && (
               <div>
                    <span className="text-sm font-medium text-gray-400">Startdatum</span>
                    <p className="text-white">
                   {new Date(trade.start_date).toLocaleDateString('de-DE')}
                 </p>
               </div>
             )}
             {trade.end_date && (
               <div>
                    <span className="text-sm font-medium text-gray-400">Enddatum</span>
                    <p className="text-white">
                   {new Date(trade.end_date).toLocaleDateString('de-DE')}
                 </p>
               </div>
             )}
             {trade.created_at && (
               <div>
                    <span className="text-sm font-medium text-gray-400">Erstellt am</span>
                    <p className="text-white">
                   {new Date(trade.created_at).toLocaleDateString('de-DE')}
                 </p>
               </div>
             )}
           </div>
         </div>

          </div>

            <div className={isBautraegerUser ? (activeBuilderTab === 'inspection' ? 'space-y-6' : 'hidden') : 'space-y-6'}>
              {/* Technische Details */}
              {trade.requires_inspection && (
                <div className="bg-gradient-to-br from-yellow-500/10 to-orange-500/10 rounded-xl p-6 border border-yellow-500/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <CheckCircle size={18} className="text-yellow-400" />
                  Besichtigung
                   </h3>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="px-3 py-1 rounded-full text-xs bg-yellow-500/20 border border-yellow-500/40 text-yellow-300">Vor-Ort-Besichtigung erforderlich</span>
                  {((trade as any)?.inspection_status) === 'accepted' && (
                    <span className="px-3 py-1 rounded-full text-xs bg-green-500/20 border border-green-500/40 text-green-300">Termin angenommen</span>
                  )}
                  {((trade as any)?.inspection_status) === 'pending' && (
                    <span className="px-3 py-1 rounded-full text-xs bg-blue-500/20 border border-blue-500/40 text-blue-300">Termin ausstehend</span>
                  )}
                  {((trade as any)?.inspection_status) === 'rejected' && (
                    <span className="px-3 py-1 rounded-full text-xs bg-red-500/20 border border-red-500/40 text-red-300">Termin abgelehnt</span>
                  )}
                     </div>
                     </div>
            )}

          </div>

            <div className={isBautraegerUser ? (activeBuilderTab === 'workflow' ? 'space-y-6' : 'hidden') : 'space-y-6'}>
            {/* Fortschritt */}
            {trade.progress_percentage !== undefined && (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Clock size={18} className="text-[#ffbd59]" />
                  Fortschritt
                   </h3>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-400">Fortschritt</span>
                  <span className="text-white font-bold">{trade.progress_percentage}%</span>
                     </div>
                <div className="w-full bg-gray-600/30 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-[#ffbd59] to-[#ffa726] h-3 rounded-full transition-all duration-300 shadow-lg"
                    style={{ width: `${trade.progress_percentage}%` }}
                  ></div>
                   </div>
                 </div>
            )}

            

          </div>

            <div className={isBautraegerUser ? (activeBuilderTab === 'documents' ? 'space-y-6' : 'hidden') : 'space-y-6'}>
            {/* Dokumente - Einklappbar */}
            <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl border border-gray-600/30 overflow-hidden">
              <div className="flex items-center justify-between p-6 cursor-pointer hover:bg-[#1a1a2e]/30 transition-all duration-200" onClick={() => setIsExpanded(!isExpanded)}>
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <FileText size={18} className="text-[#ffbd59]" />
                  Dokumente ({documentsLoading ? '...' : (loadedDocuments.length > 0 ? loadedDocuments.length : (trade.documents?.length || 0))})
                  {documentsLoading && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#ffbd59] ml-2"></div>
                  )}
                  </h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-400">
                    {isExpanded ? 'Einklappen' : 'Ausklappen'}
                  </span>
                  <div className={`transform transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
                    <ChevronDown size={20} className="text-[#ffbd59]" />
                     </div>
                  </div>
                </div>

              {isExpanded && (
                <div className="border-t border-gray-600/30 max-h-[60vh] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800" style={{scrollBehavior: 'smooth'}}>
                  {documentsLoading ? (
                    <div className="p-6 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#ffbd59] mx-auto mb-3"></div>
                      <p className="text-gray-400">Lade Dokumente...</p>
                    </div>
                  ) : documentsError ? (
                    <div className="p-6 text-center">
                      <div className="text-red-400 mb-3">❌ Fehler beim Laden der Dokumente</div>
                      <p className="text-gray-400 text-sm">{documentsError}</p>
                      <button
                        onClick={() => trade?.id && loadTradeDocuments(trade.id)}
                        className="mt-3 px-4 py-2 bg-[#ffbd59] text-[#1a1a2e] rounded-lg hover:bg-[#ffa726] transition-colors text-sm font-medium"
                      >
                        Erneut versuchen
                      </button>
                    </div>
                  ) : (
                    <TradeDocumentViewer 
                      documents={loadedDocuments.length > 0 ? loadedDocuments : (trade?.documents || [])} 
                      existingQuotes={existingQuotes} 
                    />
                  )}
                  
                  {/* Debug-Informationen für Entwicklung */}
                  {typeof window !== 'undefined' && window.location.hostname === 'localhost' && (
                    <div className="p-4 bg-gray-800 text-xs text-gray-300 border-t border-gray-600">
                      <div className="mb-2">🔍 Debug-Informationen:</div>
                      <div>• Dynamisch geladene Dokumente: {loadedDocuments.length}</div>
                      <div>• Original trade.documents: {trade?.documents?.length || 0}</div>
                      <div>• Dokumente werden geladen: {documentsLoading ? 'Ja' : 'Nein'}</div>
                      <div>• Fehler: {documentsError || 'Keiner'}</div>
                      <div>• Trade ID: {trade?.id}</div>
                      <div>• Modal geöffnet: {isOpen ? 'Ja' : 'Nein'}</div>
                    </div>
                  )}
                  </div>
                )}
                  </div>
            


          </div>

            <div className={isBautraegerUser ? (activeBuilderTab === 'workflow' ? 'space-y-6' : 'hidden') : 'space-y-6'}>
            {/* Baufortschritt & Kommunikation */}
            {(
              // Für Bauträger: Immer anzeigen (können jederzeit kommentieren)
              isBautraegerUser ||
              // Für Dienstleister: Immer anzeigen (können kommunizieren und Fortschritt melden)
              !isBautraegerUser
            ) && (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <CheckSquare size={18} className="text-[#ffbd59]" />
                  Fortschritt & Kommunikation
                </h3>
                
                {/* Fortschrittsanzeige */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-gray-400">Aktueller Fortschritt</span>
                    <span className="text-white font-bold">{currentProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-600/30 rounded-full h-3">
                    <div 
                      className="bg-gradient-to-r from-[#ffbd59] to-[#ffa726] h-3 rounded-full transition-all duration-500"
                      style={{ width: `${currentProgress}%` }}
                    ></div>
                  </div>
                </div>

                {/* Kommunikationsbereich */}
                <div className="space-y-4">
                  <h4 className="text-md font-medium text-white flex items-center gap-2">
                    <Mail size={16} className="text-[#ffbd59]" />
                    Nachrichten
                  </h4>
                  
                  {/* Nachrichtenliste */}
                  <div className="bg-[#111827]/50 rounded-lg p-4 min-h-[200px] max-h-[300px] overflow-y-auto">
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

            <div className={isBautraegerUser ? (activeBuilderTab === 'workflow' ? 'space-y-6' : 'hidden') : 'space-y-6'}>
            {/* Abnahme-Workflow für Bauträger - zeige wenn NICHT Dienstleister mit eigenem Angebot */}
            {!(acceptedQuote?.service_provider_id === user?.id) && (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <CheckCircle size={18} className="text-[#ffbd59]" />
                  Abnahme-Workflow
                </h3>
                
                {completionStatus === 'in_progress' && (
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock size={20} className="text-blue-400" />
                      <span className="text-blue-300 font-medium">Arbeiten in Bearbeitung</span>
                    </div>
                    <p className="text-blue-200 text-sm">
                      Das Gewerk ist aktuell zu {currentProgress}% fertiggestellt. Warten Sie auf die Fertigstellungsmeldung des Dienstleisters.
                    </p>
                  </div>
                )}
                
                {completionStatus === 'completion_requested' && (
                  <div className="space-y-4">
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle size={20} className="text-yellow-400" />
                        <span className="text-yellow-300 font-medium">Abnahme angefordert</span>
                      </div>
                      <p className="text-yellow-200 text-sm mb-3">
                        Der Dienstleister hat das Gewerk als fertiggestellt gemeldet. Bitte prüfen Sie die Arbeiten vor Ort.
                      </p>
                      <div className="bg-yellow-500/20 rounded-lg p-3 text-sm text-yellow-100">
                        <strong>Prüfschritte:</strong>
                        <ul className="list-disc list-inside mt-2 space-y-1">
                          <li>Vollständigkeit der Arbeiten kontrollieren</li>
                          <li>Qualität und Ausführung bewerten</li>
                          <li>Übereinstimmung mit Spezifikationen prüfen</li>
                          <li>Sicherheits- und Normenkonformität kontrollieren</li>
                        </ul>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <button
                        onClick={() => handleCompletionResponse?.(true, 'Arbeiten wurden geprüft und abgenommen. Alle Anforderungen erfüllt.')}
                        className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-200"
                      >
                        <CheckCircle size={20} />
                        Abnahme bestätigen
                      </button>
                      <button
                        onClick={() => {
                          const message = prompt('Begründung für Nachbesserung (erforderlich):');
                          if (message && message.trim()) {
                            const deadline = prompt('Frist für Nachbesserung (YYYY-MM-DD, optional):');
                            handleCompletionResponse?.(false, message.trim(), deadline || undefined);
                          } else if (message !== null) {
                            alert('Bitte geben Sie eine Begründung für die Nachbesserung an.');
                          }
                        }}
                        className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-200"
                      >
                        <AlertTriangle size={20} />
                        Nachbesserung anfordern
                      </button>
                    </div>
                    
                    <div className="mt-4 p-3 bg-gray-600/20 rounded-lg">
                      <p className="text-gray-300 text-sm">
                        <strong>Hinweis:</strong> Nach der Abnahme wird das Gewerk archiviert und der Dienstleister kann eine Rechnung stellen.
                      </p>
                    </div>
                  </div>
                )}
                
                {completionStatus === 'under_review' && (
                  <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={20} className="text-orange-400" />
                      <span className="text-orange-300 font-medium">Nachbesserung angefordert</span>
                    </div>
                    <p className="text-orange-200 text-sm">
                      Sie haben Nachbesserungen angefordert. Der Dienstleister wird die erforderlichen Arbeiten ausführen und erneut um Abnahme bitten.
                    </p>
                  </div>
                )}
                
                {completionStatus === 'completed' && (
                  <div className="space-y-4">
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle size={20} className="text-green-400" />
                        <span className="text-green-300 font-medium">Gewerk abgenommen</span>
                      </div>
                      <p className="text-green-200 text-sm">
                        Das Gewerk wurde erfolgreich abgenommen und ist archiviert. Der Dienstleister kann nun eine Rechnung stellen.
                      </p>
                    </div>
                    
                    {/* Bewertung anzeigen falls vorhanden */}
                    {!hasRated && (
                      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Star size={20} className="text-blue-400" />
                          <span className="text-blue-300 font-medium">Dienstleister bewerten</span>
                        </div>
                        <p className="text-blue-200 text-sm mb-3">
                          Helfen Sie anderen Bauträgern mit Ihrer Bewertung des Dienstleisters.
                        </p>
                        <button
                          onClick={() => setShowRatingModal(true)}
                          className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all duration-200"
                        >
                          <Star size={16} className="inline mr-2" />
                          Jetzt bewerten
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Abnahme-Workflow Buttons für Dienstleister */}
            {!isBautraegerUser && (
              // Zeige für Dienstleister wenn:
              // 1. Er hat ein akzeptiertes Angebot für dieses Gewerk, ODER
              // 2. Er hat überhaupt ein Angebot für dieses Gewerk (auch wenn noch nicht akzeptiert)
              (acceptedQuote?.service_provider_id === user?.id) || 
              (existingQuotes?.some(q => q.service_provider_id === user?.id))
            ) && (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <CheckCircle size={18} className="text-[#ffbd59]" />
                  Abnahme-Workflow
                  <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full">
                    Status: {completionStatus}
                  </span>
                </h3>
                
                {/* Prüfe ob Dienstleister berechtigt ist */}
                {!acceptedQuote && !existingQuotes?.some(q => q.service_provider_id === user?.id) ? (
                  <div className="bg-gray-500/10 border border-gray-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={20} className="text-gray-400" />
                      <span className="text-gray-300 font-medium">Kein Angebot vorhanden</span>
                    </div>
                    <p className="text-gray-400 text-sm">
                      Sie haben noch kein Angebot für dieses Gewerk abgegeben. Erst nach der Angebotserstellung und -annahme können Sie den Abnahme-Workflow nutzen.
                    </p>
                  </div>
                ) : !acceptedQuote ? (
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock size={20} className="text-blue-400" />
                      <span className="text-blue-300 font-medium">Angebot eingereicht</span>
                    </div>
                    <p className="text-blue-200 text-sm">
                      Ihr Angebot wurde eingereicht und wartet auf die Annahme durch den Bauträger. Nach der Annahme können Sie hier den Baufortschritt verfolgen und die Abnahme anfordern.
                    </p>
                  </div>
                ) : completionStatus === 'in_progress' && (
                  <div className="space-y-4">
                    {currentProgress >= 100 ? (
                      <>
                        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle size={20} className="text-yellow-400" />
                            <span className="text-yellow-300 font-medium">Bereit für Abnahme</span>
                          </div>
                          <p className="text-yellow-200 text-sm">
                            Das Gewerk ist zu 100% fertiggestellt. Sie können jetzt die Abnahme anfordern.
                          </p>
                        </div>
                        <button
                          onClick={handleCompletionRequest}
                          className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 text-white font-semibold py-3 px-6 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
                        >
                          <CheckCircle size={20} />
                          Abnahme anfordern
                        </button>
                      </>
                    ) : (
                      <>
                        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Clock size={20} className="text-blue-400" />
                            <span className="text-blue-300 font-medium">Arbeit in Bearbeitung</span>
                          </div>
                          <p className="text-blue-200 text-sm">
                            Aktueller Fortschritt: {currentProgress}%. Sie können die Abnahme anfordern, sobald das Gewerk zu 100% fertiggestellt ist.
                          </p>
                        </div>
                        <button
                          onClick={handleCompletionRequest}
                          disabled={currentProgress < 100}
                          className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <CheckCircle size={20} />
                          Abnahme anfordern ({currentProgress}%)
                        </button>
                      </>
                    )}
                  </div>
                )}
                
                {acceptedQuote && completionStatus === 'completion_requested' && (
                  <div className="space-y-4">
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock size={20} className="text-blue-400" />
                        <span className="text-blue-300 font-medium">Abnahme angefordert</span>
                      </div>
                      <p className="text-blue-200 text-sm">
                        Die Abnahme wurde angefordert. Der Bauträger wird die Arbeiten prüfen und Ihnen eine Rückmeldung geben.
                      </p>
                    </div>
                    
                    {/* Abnahme starten Button für Dienstleister */}
                    {acceptedQuote?.service_provider_id === user?.id && (
                      <button
                        onClick={handleStartAcceptance}
                        className="w-full bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold py-3 px-6 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
                      >
                        <CheckCircle size={20} />
                        Abnahme starten
                      </button>
                    )}
                  </div>
                )}
                
                {acceptedQuote && completionStatus === 'under_review' && (
                  <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={20} className="text-orange-400" />
                      <span className="text-orange-300 font-medium">Nachbesserung erforderlich</span>
                    </div>
                    <p className="text-orange-200 text-sm">
                      Der Bauträger hat Nachbesserungen angefordert. Bitte führen Sie die erforderlichen Arbeiten aus.
                    </p>
                    <button
                      onClick={() => {
                        // Nachbesserung abgeschlossen - zurück zu in_progress
                        handleCompletionResponse?.(true, 'Nachbesserung abgeschlossen');
                      }}
                      className="mt-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-semibold py-2 px-4 rounded hover:shadow-lg transition-all duration-200"
                    >
                      Nachbesserung abgeschlossen
                    </button>
                  </div>
                )}
                
                {acceptedQuote && completionStatus === 'completed_with_defects' && (
                  <div className="space-y-4">
                    <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle size={20} className="text-orange-400" />
                        <span className="text-orange-300 font-medium">Mängelbehebung erforderlich</span>
                      </div>
                      <p className="text-orange-200 text-sm">
                        Das Gewerk wurde unter Vorbehalt abgenommen. Bitte beheben Sie die festgestellten Mängel.
                      </p>
                    </div>
                    
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle size={20} className="text-yellow-400" />
                        <span className="text-yellow-300 font-medium">Mängelbehebung erforderlich</span>
                      </div>
                      <p className="text-yellow-200 text-sm">
                        Es wurden Mängel festgestellt, die behoben werden müssen. Der Dienstleister wird über die erforderlichen Maßnahmen informiert.
                      </p>
                    </div>
                  </div>
                )}
                
                {acceptedQuote && completionStatus === 'completed' && (
                  <div className="space-y-4">
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle size={20} className="text-green-400" />
                        <span className="text-green-300 font-medium">Abgenommen</span>
                      </div>
                      <p className="text-green-200 text-sm">
                        Das Gewerk wurde erfolgreich abgenommen und ist archiviert. Sie können nun eine Rechnung stellen.
                      </p>
                    </div>
                    
                    {/* Rechnung stellen Button für Dienstleister */}
                    {!existingInvoice && (
                      <button
                        onClick={() => setShowInvoiceModal(true)}
                        className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
                      >
                        <Receipt size={20} />
                        Rechnung stellen
                      </button>
                    )}
                    
                    {/* Rechnung bereits gestellt */}
                    {existingInvoice && (
                      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Receipt size={20} className="text-blue-400" />
                          <span className="text-blue-300 font-medium">Rechnung gestellt</span>
                        </div>
                        <p className="text-blue-200 text-sm mb-3">
                          Rechnung Nr. {existingInvoice.invoice_number} wurde erfolgreich eingereicht.
                        </p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              existingInvoice.status === 'paid' ? 'bg-green-500/20 text-green-300' :
                              existingInvoice.status === 'overdue' ? 'bg-red-500/20 text-red-300' :
                              'bg-yellow-500/20 text-yellow-300'
                            }`}>
                              {existingInvoice.status === 'paid' ? 'Bezahlt' :
                               existingInvoice.status === 'overdue' ? 'Überfällig' :
                               existingInvoice.status === 'viewed' ? 'Eingesehen' : 'Gesendet'}
                            </span>
                            <span className="text-sm text-gray-300">
                              {existingInvoice.total_amount?.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
                            </span>
                          </div>
                          <a
                            href="/invoices"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 px-3 py-1 bg-[#ffbd59]/20 text-[#ffbd59] rounded-lg hover:bg-[#ffbd59]/30 transition-all duration-200 text-xs font-medium"
                            title="Alle Rechnungen verwalten"
                          >
                            <Receipt size={14} />
                            Alle Rechnungen
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}


            
            {/* Rechnungsanzeige für Bauträger */}
            {isBautraegerUser && completionStatus === 'completed' && trade?.invoice_generated && (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Receipt size={18} className="text-[#ffbd59]" />
                  Rechnung
                </h3>
                {!hasRated ? (
                  <div className="text-center">
                    <p className="text-gray-400 mb-4">
                      Bitte bewerten Sie zuerst den Dienstleister, um die Rechnung einzusehen.
                    </p>
                    <button
                      onClick={() => setShowRatingModal(true)}
                      className="px-6 py-3 bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold rounded-lg hover:shadow-lg transition-all duration-200"
                    >
                      <Star size={20} className="inline mr-2" />
                      Dienstleister bewerten
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Betrag:</span>
                      <span className="text-white font-bold">{trade?.invoice_amount?.toLocaleString('de-DE')} €</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Fällig bis:</span>
                      <span className="text-white">{trade?.invoice_due_date ? new Date(trade.invoice_due_date).toLocaleDateString('de-DE') : '-'}</span>
                    </div>
                    <a
                      href={trade?.invoice_pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full px-6 py-3 bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold rounded-lg hover:shadow-lg transition-all duration-200 text-center"
                    >
                      <Download size={20} className="inline mr-2" />
                      Rechnung herunterladen
                    </a>
                  </div>
                )}
              </div>
            )}

          </div>

            {/* Dienstleister-spezifische Aktionen */}
            {!isBautraegerUser && (
              // Zeige Aktionen nur wenn:
              // 1. Kein Angebot angenommen wurde ODER
              // 2. Das angenommene Angebot NICHT von diesem Dienstleister ist
              (!acceptedQuote || acceptedQuote?.service_provider_id !== user?.id)
            ) && (
              <div className="bg-gradient-to-br from-[#1a1a2e]/50 to-[#2c3539]/50 rounded-xl p-6 border border-gray-600/30">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Calculator size={18} className="text-[#ffbd59]" />
                  Aktionen
                </h3>
                {/* Angebot abgeben Button - NUR wenn noch kein Angebot vorhanden */}
                {!(existingQuotes || []).some(q => q.service_provider_id === user?.id) ? (
                  <button
                    onClick={() => {
                      onCreateQuote(trade);
                      onClose(); // Schließe das Modal nach dem Klick
                    }}
                    className="w-full bg-gradient-to-r from-[#ffbd59] to-[#ffa726] text-[#1a1a2e] font-semibold py-3 px-6 rounded-lg hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
                  >
                    <Calculator size={20} />
                    Angebot abgeben
                  </button>
                ) : acceptedQuote?.service_provider_id !== user?.id ? (
                  <div className="text-center text-gray-400 py-3">
                    ✅ Sie haben bereits ein Angebot für dieses Gewerk abgegeben
                  </div>
                ) : (
                  <div className="text-center text-green-400 py-3">
                    🎉 Ihr Angebot wurde angenommen!
                  </div>
                )}
              </div>
            )}
      </div>
      
      {/* Bewertungs-Modal */}
      {showRatingModal && acceptedQuote && (
        <ServiceProviderRating
          isOpen={showRatingModal}
          onClose={() => setShowRatingModal(false)}
          serviceProviderId={acceptedQuote?.service_provider_id || 0}
          projectId={trade?.project_id || 0}
          milestoneId={trade?.id || 0}
          quoteId={acceptedQuote?.id}
          onRatingComplete={handleRatingComplete}
        />
      )}

      {/* Rechnungs-Modal */}
      {showInvoiceModal && acceptedQuote && (
        <InvoiceModal
          isOpen={showInvoiceModal}
          onClose={() => setShowInvoiceModal(false)}
          milestoneId={trade.id}
          milestoneTitle={trade.title}
          contractValue={acceptedQuote.total_price || 0}
          onInvoiceSubmitted={() => {
            setShowInvoiceModal(false);
            // Lade die Rechnung neu
            loadExistingInvoice();
          }}
        />
      )}

      {/* Abnahme-Modal */}
      {showAcceptanceModal && trade && (
        <AcceptanceModal
          isOpen={showAcceptanceModal}
          onClose={() => {

            setShowAcceptanceModal(false);
          }}
          trade={trade}
          onComplete={handleCompleteAcceptance}
        />
      )}

      {/* Finale Abnahme-Modal */}
      {showFinalAcceptanceModal && trade && (
        <FinalAcceptanceModal
          isOpen={showFinalAcceptanceModal}
          onClose={() => setShowFinalAcceptanceModal(false)}
          acceptanceId={1} // TODO: Echte Acceptance-ID verwenden
          milestoneId={trade.id}
          milestoneTitle={trade.title}
          defects={acceptanceDefects}
          onAcceptanceComplete={() => {
            setShowFinalAcceptanceModal(false);
            // Aktualisiere den Status nach finaler Abnahme
            setCompletionStatus('completed');
          }}
        />
      )}

      {/* Besichtigungsplanung-Modal */}
      {showInspectionScheduling && trade && (
        <InspectionSchedulingModal
          isOpen={showInspectionScheduling}
          onClose={() => setShowInspectionScheduling(false)}
          onSubmit={handleCreateInspection}
          tradeTitle={trade.title}
          selectedQuoteIds={selectedQuoteIds}
          projectName={project?.name}
        />
      )}
        </div>
      </div>
    </>
  );
}
export default TradeDetailsModal;



