#!/usr/bin/env python3
"""
Korrigiert fehlende subcategories für bestehende Dokumente
"""

import sqlite3
import os
from datetime import datetime

def fix_document_subcategories():
    """Korrigiert fehlende subcategories für bestehende Dokumente"""
    
    print("🔧 Korrigiere fehlende subcategories für bestehende Dokumente...")
    
    # Verbinde zur Datenbank
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    # 1. Hole alle Dokumente ohne subcategory
    cursor.execute("SELECT id, title, document_type, category FROM documents WHERE subcategory IS NULL OR subcategory = ''")
    docs_without_subcategory = cursor.fetchall()
    
    print(f"📋 Gefundene Dokumente ohne subcategory: {len(docs_without_subcategory)}")
    
    if not docs_without_subcategory:
        print("✅ Alle Dokumente haben bereits subcategories!")
        conn.close()
        return
    
    # 2. Definiere Mapping für subcategories basierend auf document_type und category
    subcategory_mapping = {
        # CONTRACTS Kategorie
        ('CONTRACT', 'CONTRACTS'): 'Auftragsbestätigungen',
        ('CONTRACT', 'CONTRACTS'): 'Verträge',
        
        # FINANCE Kategorie
        ('PDF', 'FINANCE'): 'Rechnungen',
        ('INVOICE', 'FINANCE'): 'Rechnungen',
        ('QUOTE', 'FINANCE'): 'Kostenvoranschläge',
        
        # PLANNING Kategorie
        ('PLAN', 'PLANNING'): 'Baupläne',
        ('PERMIT', 'PLANNING'): 'Genehmigungen',
        ('BLUEPRINT', 'PLANNING'): 'Bauzeichnungen',
        
        # EXECUTION Kategorie
        ('PHOTO', 'EXECUTION'): 'Baufortschritt',
        ('VIDEO', 'EXECUTION'): 'Baufortschritt',
        ('REPORT', 'EXECUTION'): 'Bauberichte',
        
        # DOCUMENTATION Kategorie
        ('CERTIFICATE', 'DOCUMENTATION'): 'Zertifikate',
        ('REPORT', 'DOCUMENTATION'): 'Berichte',
        ('OTHER', 'DOCUMENTATION'): 'Sonstiges',
    }
    
    # 3. Korrigiere jedes Dokument
    updated_count = 0
    for doc_id, title, doc_type, category in docs_without_subcategory:
        print(f"\n🔧 Korrigiere Dokument ID {doc_id}: {title}")
        print(f"  - Document Type: {doc_type}")
        print(f"  - Category: {category}")
        
        # Bestimme subcategory basierend auf Mapping oder Titel-Analyse
        subcategory = None
        
        # 1. Versuche Mapping
        if (doc_type, category) in subcategory_mapping:
            subcategory = subcategory_mapping[(doc_type, category)]
            print(f"  - Mapping gefunden: {subcategory}")
        
        # 2. Fallback: Titel-Analyse
        if not subcategory:
            title_lower = title.lower()
            if 'auftragsbestätigung' in title_lower or 'auftrag' in title_lower:
                subcategory = 'Auftragsbestätigungen'
            elif 'rechnung' in title_lower or 'invoice' in title_lower:
                subcategory = 'Rechnungen'
            elif 'kostenvoranschlag' in title_lower or 'quote' in title_lower:
                subcategory = 'Kostenvoranschläge'
            elif 'bauplan' in title_lower or 'plan' in title_lower:
                subcategory = 'Baupläne'
            elif 'genehmigung' in title_lower or 'permit' in title_lower:
                subcategory = 'Genehmigungen'
            elif 'zertifikat' in title_lower or 'certificate' in title_lower:
                subcategory = 'Zertifikate'
            elif 'bericht' in title_lower or 'report' in title_lower:
                subcategory = 'Berichte'
            else:
                # Standard-Fallback basierend auf Category
                category_fallbacks = {
                    'CONTRACTS': 'Verträge',
                    'FINANCE': 'Rechnungen',
                    'PLANNING': 'Baupläne',
                    'EXECUTION': 'Baufortschritt',
                    'DOCUMENTATION': 'Berichte',
                    'ORDER_CONFIRMATIONS': 'Auftragsbestätigungen'
                }
                subcategory = category_fallbacks.get(category, 'Sonstiges')
            
            print(f"  - Titel-Analyse: {subcategory}")
        
        # 3. Update Datenbank
        cursor.execute("""
            UPDATE documents 
            SET subcategory = ?, updated_at = ?
            WHERE id = ?
        """, (subcategory, datetime.now().isoformat(), doc_id))
        
        print(f"  ✅ Subcategory gesetzt: {subcategory}")
        updated_count += 1
    
    # 4. Commit Änderungen
    conn.commit()
    
    # 5. Zeige Zusammenfassung
    print(f"\n📊 Zusammenfassung:")
    print(f"  - Dokumente korrigiert: {updated_count}")
    
    # 6. Zeige alle Dokumente mit Kategorien
    cursor.execute("SELECT id, title, category, subcategory FROM documents ORDER BY id")
    all_docs = cursor.fetchall()
    
    print(f"\n📄 Alle Dokumente mit Kategorien:")
    for doc_id, title, category, subcategory in all_docs:
        print(f"  - ID {doc_id}: {title}")
        print(f"    Category: {category} | Subcategory: {subcategory}")
    
    conn.close()
    
    print(f"\n✅ Subcategory-Korrektur abgeschlossen!")
    print(f"🎯 Nächste Schritte:")
    print(f"  1. Frontend neu laden")
    print(f"  2. Dokumente sollten jetzt in Kategorien angezeigt werden")
    print(f"  3. Ordner-Struktur funktioniert korrekt")

def create_category_structure():
    """Erstellt die Kategorie-Struktur für das Frontend"""
    
    print("\n📁 Erstelle Kategorie-Struktur...")
    
    # Definiere Standard-Kategorien und Unterkategorien
    category_structure = {
        'CONTRACTS': ['Auftragsbestätigungen', 'Verträge', 'Nachträge'],
        'FINANCE': ['Rechnungen', 'Kostenvoranschläge', 'Zahlungspläne'],
        'PLANNING': ['Baupläne', 'Genehmigungen', 'Bauzeichnungen'],
        'EXECUTION': ['Baufortschritt', 'Bauberichte', 'Fotos'],
        'DOCUMENTATION': ['Berichte', 'Zertifikate', 'Prüfprotokolle'],
        'ORDER_CONFIRMATIONS': ['Auftragsbestätigungen', 'Bestellungen']
    }
    
    print("📋 Verfügbare Kategorien und Unterkategorien:")
    for category, subcategories in category_structure.items():
        print(f"  - {category}:")
        for subcategory in subcategories:
            print(f"    * {subcategory}")
    
    return category_structure

if __name__ == "__main__":
    print("🚀 Starte Subcategory-Korrektur...")
    
    # Erstelle Kategorie-Struktur
    category_structure = create_category_structure()
    
    # Korrigiere subcategories
    fix_document_subcategories()
    
    print(f"\n✅ Subcategory-Korrektur vollständig abgeschlossen!")