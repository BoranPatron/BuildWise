#!/usr/bin/env python3
"""
DMS-Kategorien-Erweiterung Migration
====================================

Erweitert das Dokumentenmanagementsystem um:
- Projektmanagement-Dokumente (PROJECT_MANAGEMENT)
- Ausschreibungen und Angebote (PROCUREMENT)

Diese Migration:
1. Fügt neue Dokumentkategorien hinzu
2. Migriert bestehende Dokumente bei Bedarf
3. Aktualisiert das Kategorie-System
"""

import sqlite3
import os
from datetime import datetime

def add_dms_categories_enhancement():
    """Erweitert DMS-Kategorien um Projektmanagement und Procurement"""
    
    print("🚀 Starte DMS-Kategorien-Erweiterung...")
    
    # Datenbankverbindung
    db_path = 'buildwise.db'
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Prüfe aktuelle Dokumente-Struktur
        print("📋 Prüfe bestehende Dokumente-Struktur...")
        cursor.execute("PRAGMA table_info(documents)")
        table_info = cursor.fetchall()
        
        has_category = any(column[1] == 'category' for column in table_info)
        has_subcategory = any(column[1] == 'subcategory' for column in table_info)
        
        if not has_category or not has_subcategory:
            print("❌ Dokumente-Tabelle hat nicht die erwartete Struktur!")
            return False
        
        # 2. Zeige aktuellen Status
        cursor.execute("SELECT DISTINCT category FROM documents WHERE category IS NOT NULL")
        existing_categories = [row[0] for row in cursor.fetchall()]
        print(f"📊 Bestehende Kategorien: {existing_categories}")
        
        # 3. Teste intelligente Kategorisierung für neue Kategorien
        print("\n🧠 Teste intelligente Kategorisierung...")
        
        # Simuliere Testdokumente für neue Kategorien
        test_documents = [
            ("Projektplan_Wohnbau_2024.pdf", "project_management"),
            ("Terminplan_Neubau_Gantt.xlsx", "project_management"),
            ("Budgetplan_Quartalsauswertung.pdf", "project_management"),
            ("Risikomanagement_Analyse.docx", "project_management"),
            ("Ausschreibung_Elektroinstallation.pdf", "procurement"),
            ("Leistungsverzeichnis_Sanitär.xlsx", "procurement"),
            ("Angebot_Bauunternehmen_Schmidt.pdf", "procurement"),
            ("Vergabeprotokoll_Dachdecker.docx", "procurement"),
            ("Preisspiegel_Vergleich.xlsx", "procurement")
        ]
        
        # Importiere DocumentCategorizer für Tests
        import sys
        sys.path.append('app/utils')
        from document_categorizer import DocumentCategorizer
        
        print("🔍 Teste automatische Kategorisierung:")
        correct_categorizations = 0
        for filename, expected_category in test_documents:
            detected_category = DocumentCategorizer.categorize_document(filename)
            subcategory = DocumentCategorizer.suggest_subcategory(detected_category, filename)
            
            status = "✅" if detected_category == expected_category else "❌"
            print(f"  {status} {filename}")
            print(f"    Erwartet: {expected_category} | Erkannt: {detected_category}")
            print(f"    Subcategory: {subcategory}")
            
            if detected_category == expected_category:
                correct_categorizations += 1
        
        success_rate = (correct_categorizations / len(test_documents)) * 100
        print(f"\n📈 Erkennungsrate: {success_rate:.1f}% ({correct_categorizations}/{len(test_documents)})")
        
        # 4. Suche nach Dokumenten, die neue Kategorien erhalten könnten
        print("\n🔍 Suche bestehende Dokumente für Rekategorisierung...")
        
        cursor.execute("SELECT id, title, category, subcategory FROM documents")
        all_documents = cursor.fetchall()
        
        recategorization_candidates = []
        
        for doc_id, title, current_category, current_subcategory in all_documents:
            if title:
                # Teste neue Kategorisierung
                detected_category = DocumentCategorizer.categorize_document(title)
                
                if detected_category in ['project_management', 'procurement']:
                    suggested_subcategory = DocumentCategorizer.suggest_subcategory(detected_category, title)
                    recategorization_candidates.append({
                        'id': doc_id,
                        'title': title,
                        'old_category': current_category,
                        'old_subcategory': current_subcategory,
                        'new_category': detected_category,
                        'new_subcategory': suggested_subcategory
                    })
        
        print(f"📋 Gefundene Kandidaten für Rekategorisierung: {len(recategorization_candidates)}")
        
        if recategorization_candidates:
            print("\n🔄 Rekategorisierungs-Vorschläge:")
            for candidate in recategorization_candidates:
                print(f"  📄 ID {candidate['id']}: {candidate['title']}")
                print(f"    Alt: {candidate['old_category']} → {candidate['old_subcategory']}")
                print(f"    Neu: {candidate['new_category']} → {candidate['new_subcategory']}")
        
        # 5. Optional: Automatische Rekategorisierung (nur wenn explizit gewünscht)
        auto_recategorize = input("\n❓ Sollen die Dokumente automatisch rekategorisiert werden? (y/N): ").lower() == 'y'
        
        if auto_recategorize and recategorization_candidates:
            print("🔄 Führe automatische Rekategorisierung durch...")
            
            recategorized_count = 0
            for candidate in recategorization_candidates:
                cursor.execute("""
                    UPDATE documents 
                    SET category = ?, subcategory = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    candidate['new_category'].upper(),  # Backend verwendet UPPERCASE
                    candidate['new_subcategory'],
                    datetime.utcnow().isoformat(),
                    candidate['id']
                ))
                recategorized_count += 1
            
            print(f"✅ {recategorized_count} Dokumente erfolgreich rekategorisiert!")
        
        # 6. Erstelle Kategorie-Übersicht
        print("\n📊 Erstelle erweiterte Kategorie-Übersicht...")
        
        cursor.execute("""
            SELECT 
                category,
                subcategory,
                COUNT(*) as count
            FROM documents 
            WHERE category IS NOT NULL AND subcategory IS NOT NULL
            GROUP BY category, subcategory
            ORDER BY category, subcategory
        """)
        
        category_stats = cursor.fetchall()
        
        print("\n📈 Kategorie-Statistiken nach Erweiterung:")
        current_category = None
        for category, subcategory, count in category_stats:
            if category != current_category:
                print(f"\n🗂️  {category}:")
                current_category = category
            print(f"    └─ {subcategory}: {count} Dokument(e)")
        
        # 7. Validierung der Erweiterung
        print("\n✅ Validierung der DMS-Erweiterung:")
        
        # Prüfe alle Kategorien
        cursor.execute("SELECT DISTINCT category FROM documents WHERE category IS NOT NULL")
        all_categories = [row[0] for row in cursor.fetchall()]
        
        expected_categories = ['PLANNING', 'CONTRACTS', 'FINANCE', 'EXECUTION', 
                             'DOCUMENTATION', 'ORDER_CONFIRMATIONS', 
                             'PROJECT_MANAGEMENT', 'PROCUREMENT']
        
        print(f"📋 Verfügbare Kategorien: {sorted(all_categories)}")
        
        new_categories_present = any(cat in all_categories for cat in ['PROJECT_MANAGEMENT', 'PROCUREMENT'])
        if new_categories_present:
            print("✅ Neue Kategorien erfolgreich im System verfügbar!")
        else:
            print("ℹ️  Neue Kategorien bereit für erste Dokumente")
        
        # Commit Änderungen
        conn.commit()
        
        print("\n🎉 DMS-Kategorien-Erweiterung erfolgreich abgeschlossen!")
        print("\n📋 Neue Kategorien verfügbar:")
        print("  🎯 PROJECT_MANAGEMENT - Projektmanagement-Dokumente")
        print("     └─ Projektpläne, Terminplanung, Budgetplanung, etc.")
        print("  🛒 PROCUREMENT - Ausschreibungen und Angebote")
        print("     └─ Ausschreibungsunterlagen, Angebote, Vergabedokumentation, etc.")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei DMS-Erweiterung: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("DMS-KATEGORIEN-ERWEITERUNG")
    print("Erweitert BuildWise DMS um Projektmanagement & Procurement")
    print("=" * 60)
    
    success = add_dms_categories_enhancement()
    
    if success:
        print("\n✅ Migration erfolgreich abgeschlossen!")
        print("\n📝 Nächste Schritte:")
        print("1. Frontend-Kategorie-Mapping aktualisieren")
        print("2. Neue Kategorien in der Benutzeroberfläche testen")
        print("3. Dokumentation für Benutzer aktualisieren")
    else:
        print("\n❌ Migration fehlgeschlagen!")
        print("Prüfen Sie die Fehlerdetails und versuchen Sie es erneut.")

if __name__ == "__main__":
    main()