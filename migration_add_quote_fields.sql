-- Migration: Erweitere quotes-Tabelle um fehlende CostEstimateForm-Felder
-- Datum: 2024-12-19
-- Beschreibung: Fügt alle fehlenden Felder aus dem CostEstimateForm zur quotes-Tabelle hinzu

-- Angebotsnummer
ALTER TABLE quotes ADD COLUMN quote_number VARCHAR(255);

-- Qualifikationen und Referenzen
ALTER TABLE quotes ADD COLUMN qualifications TEXT;
ALTER TABLE quotes ADD COLUMN references TEXT;
ALTER TABLE quotes ADD COLUMN certifications TEXT;

-- Technische Details
ALTER TABLE quotes ADD COLUMN technical_approach TEXT;
ALTER TABLE quotes ADD COLUMN quality_standards TEXT;
ALTER TABLE quotes ADD COLUMN safety_measures TEXT;
ALTER TABLE quotes ADD COLUMN environmental_compliance TEXT;

-- Risiko-Bewertung
ALTER TABLE quotes ADD COLUMN risk_assessment TEXT;
ALTER TABLE quotes ADD COLUMN contingency_plan TEXT;

-- Zusätzliche Informationen
ALTER TABLE quotes ADD COLUMN additional_notes TEXT;

-- Kommentare für bessere Dokumentation
COMMENT ON COLUMN quotes.quote_number IS 'Eindeutige Angebotsnummer (z.B. ANB-2024-001)';
COMMENT ON COLUMN quotes.qualifications IS 'Qualifikationen und Zertifizierungen des Dienstleisters';
COMMENT ON COLUMN quotes.references IS 'Referenzprojekte des Dienstleisters';
COMMENT ON COLUMN quotes.certifications IS 'Spezifische Zertifizierungen';
COMMENT ON COLUMN quotes.technical_approach IS 'Technischer Ansatz für das Projekt';
COMMENT ON COLUMN quotes.quality_standards IS 'Qualitätsstandards und -verfahren';
COMMENT ON COLUMN quotes.safety_measures IS 'Geplante Sicherheitsmaßnahmen';
COMMENT ON COLUMN quotes.environmental_compliance IS 'Umweltschutz und Compliance-Maßnahmen';
COMMENT ON COLUMN quotes.risk_assessment IS 'Risikobewertung und identifizierte Risiken';
COMMENT ON COLUMN quotes.contingency_plan IS 'Notfallpläne und alternative Lösungsansätze';
COMMENT ON COLUMN quotes.additional_notes IS 'Zusätzliche Anmerkungen und Informationen';
