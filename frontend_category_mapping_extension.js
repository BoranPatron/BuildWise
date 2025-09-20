/**
 * Frontend Kategorie-Mapping Erweiterung
 * =======================================
 * 
 * Erweitert das bestehende Kategorie-Mapping um:
 * - PROJECT_MANAGEMENT (Projektmanagement)
 * - PROCUREMENT (Ausschreibungen & Angebote)
 * 
 * Diese Datei sollte in die entsprechende Frontend-Komponente integriert werden.
 */

// Erweiterte Kategorie-Mapping Konfiguration
export const EXTENDED_CATEGORY_MAPPING = {
  // Bestehende Kategorien (beibehalten)
  'PLANNING': 'planning',
  'CONTRACTS': 'contracts', 
  'FINANCE': 'finance',
  'EXECUTION': 'execution',
  'DOCUMENTATION': 'documentation',
  'ORDER_CONFIRMATIONS': 'contracts', // Auftragsbestätigungen gehören zu Verträgen
  
  // Neue Kategorien
  'PROJECT_MANAGEMENT': 'project_management',  // Projektmanagement
  'PROCUREMENT': 'procurement'                 // Ausschreibungen & Angebote
};

// Kategorie-Icons für neue Kategorien
export const CATEGORY_ICONS_EXTENDED = {
  // Bestehende Icons (beibehalten)
  'planning': '📋',
  'contracts': '📄',
  'finance': '💰',
  'execution': '🔨',
  'documentation': '📚',
  
  // Neue Icons
  'project_management': '📊',  // Projektmanagement
  'procurement': '📋'          // Ausschreibungen & Angebote
};

// Deutsche Kategorie-Namen für UI
export const CATEGORY_NAMES_GERMAN = {
  // Bestehende Namen
  'planning': 'Planung & Genehmigung',
  'contracts': 'Verträge & Rechtliches', 
  'finance': 'Finanzen & Abrechnung',
  'execution': 'Ausführung & Handwerk',
  'documentation': 'Dokumentation & Medien',
  
  // Neue Namen
  'project_management': 'Projektmanagement',
  'procurement': 'Ausschreibungen & Angebote'
};

// Unterkategorien für neue Hauptkategorien
export const SUBCATEGORIES_EXTENDED = {
  // Bestehende Unterkategorien (hier nicht alle aufgeführt)
  'planning': [
    'Baupläne & Grundrisse',
    'Baugenehmigungen', 
    'Statische Berechnungen'
  ],
  'contracts': [
    'Bauverträge',
    'Nachträge',
    'Versicherungen'
  ],
  'finance': [
    'Rechnungen',
    'Bezahlte Rechnungen',
    'Kostenvoranschläge',
    'Zahlungsbelege'
  ],
  
  // Neue Unterkategorien
  'project_management': [
    'Projektpläne',
    'Terminplanung', 
    'Budgetplanung',
    'Projektsteuerung',
    'Risikomanagement',
    'Qualitätsmanagement',
    'Ressourcenplanung',
    'Projektdokumentation'
  ],
  'procurement': [
    'Ausschreibungsunterlagen',
    'Technische Spezifikationen',
    'Angebote',
    'Angebotsbewertung', 
    'Vergabedokumentation',
    'Verhandlungen'
  ]
};

// Hilfsfunktionen für Kategorie-Konvertierung
export const CategoryHelpers = {
  /**
   * Konvertiert Backend-Kategorie zu Frontend-Kategorie
   * @param {string} backendCategory - Backend Kategorie (GROSSGESCHRIEBEN)
   * @returns {string} Frontend Kategorie (kleingeschrieben)
   */
  convertBackendToFrontend(backendCategory) {
    return EXTENDED_CATEGORY_MAPPING[backendCategory] || 'documentation';
  },

  /**
   * Holt Icon für Kategorie
   * @param {string} frontendCategory - Frontend Kategorie
   * @returns {string} Icon Emoji
   */
  getCategoryIcon(frontendCategory) {
    return CATEGORY_ICONS_EXTENDED[frontendCategory] || '📄';
  },

  /**
   * Holt deutschen Namen für Kategorie
   * @param {string} frontendCategory - Frontend Kategorie
   * @returns {string} Deutscher Kategorie-Name
   */
  getCategoryDisplayName(frontendCategory) {
    return CATEGORY_NAMES_GERMAN[frontendCategory] || frontendCategory;
  },

  /**
   * Holt Unterkategorien für Hauptkategorie
   * @param {string} frontendCategory - Frontend Kategorie
   * @returns {string[]} Array von Unterkategorien
   */
  getSubcategories(frontendCategory) {
    return SUBCATEGORIES_EXTENDED[frontendCategory] || [];
  },

  /**
   * Konvertiert Kategorie-Statistiken von Backend zu Frontend
   * @param {Array} backendStats - Backend Statistiken
   * @returns {Array} Frontend Statistiken
   */
  convertCategoryStats(backendStats) {
    const frontendStats = {};
    
    // Aggregiere Backend-Kategorien zu Frontend-Kategorien
    backendStats.forEach(stat => {
      const frontendCategory = this.convertBackendToFrontend(stat.category);
      
      if (!frontendStats[frontendCategory]) {
        frontendStats[frontendCategory] = {
          category: frontendCategory,
          displayName: this.getCategoryDisplayName(frontendCategory),
          icon: this.getCategoryIcon(frontendCategory),
          count: 0,
          totalSize: 0,
          subcategories: {}
        };
      }
      
      // Aggregiere Zählungen
      frontendStats[frontendCategory].count += stat.count || 0;
      frontendStats[frontendCategory].totalSize += stat.totalSize || 0;
      
      // Aggregiere Unterkategorien
      if (stat.subcategories) {
        Object.entries(stat.subcategories).forEach(([subcat, count]) => {
          if (!frontendStats[frontendCategory].subcategories[subcat]) {
            frontendStats[frontendCategory].subcategories[subcat] = 0;
          }
          frontendStats[frontendCategory].subcategories[subcat] += count;
        });
      }
    });
    
    // Berechne Durchschnittsgrößen
    Object.values(frontendStats).forEach(stat => {
      stat.averageSize = stat.count > 0 ? Math.round(stat.totalSize / stat.count) : 0;
    });
    
    return Object.values(frontendStats);
  }
};

// Beispiel-Integration für React-Komponenten
export const CategoryFilterComponent = {
  /**
   * Filtert Dokumente nach Frontend-Kategorie
   * @param {Array} documents - Array von Dokumenten
   * @param {string} selectedCategory - Ausgewählte Frontend-Kategorie
   * @returns {Array} Gefilterte Dokumente
   */
  filterDocumentsByCategory(documents, selectedCategory) {
    if (selectedCategory === 'all') {
      return documents;
    }
    
    return documents.filter(doc => {
      const frontendCategory = CategoryHelpers.convertBackendToFrontend(doc.category || '');
      return frontendCategory === selectedCategory;
    });
  },

  /**
   * Filtert Dokumente nach Unterkategorie
   * @param {Array} documents - Array von Dokumenten  
   * @param {string} selectedSubcategory - Ausgewählte Unterkategorie
   * @returns {Array} Gefilterte Dokumente
   */
  filterDocumentsBySubcategory(documents, selectedSubcategory) {
    if (!selectedSubcategory || selectedSubcategory === 'all') {
      return documents;
    }
    
    return documents.filter(doc => doc.subcategory === selectedSubcategory);
  }
};

// Integration-Beispiel für bestehende TradeDetailsModal-Komponente
export const TradeDetailsModalIntegration = `
// Beispiel-Code für Integration in TradeDetailsModal.tsx

import { 
  EXTENDED_CATEGORY_MAPPING,
  CategoryHelpers,
  CategoryFilterComponent 
} from './frontend_category_mapping_extension.js';

// In der Komponente:
const convertedStats = CategoryHelpers.convertCategoryStats(categoryStats);

// Für Dokument-Filterung:
const filteredDocuments = CategoryFilterComponent.filterDocumentsByCategory(
  documents, 
  selectedCategory
);

// Für Kategorie-Anzeige:
const categoryDisplayName = CategoryHelpers.getCategoryDisplayName(category);
const categoryIcon = CategoryHelpers.getCategoryIcon(category);
`;

// Validierung der Erweiterung
export const ValidationHelpers = {
  /**
   * Überprüft ob alle neuen Kategorien korrekt gemappt sind
   * @returns {boolean} Validierung erfolgreich
   */
  validateCategoryMapping() {
    const requiredCategories = [
      'PLANNING', 'CONTRACTS', 'FINANCE', 'EXECUTION', 
      'DOCUMENTATION', 'ORDER_CONFIRMATIONS',
      'PROJECT_MANAGEMENT', 'PROCUREMENT'
    ];
    
    const mappedCategories = Object.keys(EXTENDED_CATEGORY_MAPPING);
    const missingCategories = requiredCategories.filter(
      cat => !mappedCategories.includes(cat)
    );
    
    if (missingCategories.length > 0) {
      console.warn('Fehlende Kategorie-Mappings:', missingCategories);
      return false;
    }
    
    console.log('✅ Alle Kategorien korrekt gemappt');
    return true;
  },

  /**
   * Überprüft ob alle Frontend-Kategorien Icons haben
   * @returns {boolean} Validierung erfolgreich
   */
  validateCategoryIcons() {
    const frontendCategories = Object.values(EXTENDED_CATEGORY_MAPPING);
    const iconCategories = Object.keys(CATEGORY_ICONS_EXTENDED);
    const missingIcons = frontendCategories.filter(
      cat => !iconCategories.includes(cat)
    );
    
    if (missingIcons.length > 0) {
      console.warn('Fehlende Icons für Kategorien:', missingIcons);
      return false;
    }
    
    console.log('✅ Alle Kategorien haben Icons');
    return true;
  }
};

// Export für direkte Verwendung
export default {
  EXTENDED_CATEGORY_MAPPING,
  CATEGORY_ICONS_EXTENDED,
  CATEGORY_NAMES_GERMAN,
  SUBCATEGORIES_EXTENDED,
  CategoryHelpers,
  CategoryFilterComponent,
  ValidationHelpers
};