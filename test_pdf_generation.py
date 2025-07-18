#!/usr/bin/env python3
"""
Testskript für PDF-Generierung und Download in BuildWise-Gebühren
"""

import os
import sys
import asyncio
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_storage_directory():
    """Prüft das Storage-Verzeichnis"""
    
    print("🔍 Prüfe Storage-Verzeichnis...")
    
    storage_dirs = [
        "storage",
        "storage/invoices",
        "storage/uploads",
        "storage/documents"
    ]
    
    for dir_path in storage_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} existiert")
            
            # Prüfe Schreibrechte
            try:
                test_file = os.path.join(dir_path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"✅ {dir_path} ist beschreibbar")
            except Exception as e:
                print(f"❌ {dir_path} ist nicht beschreibbar: {e}")
        else:
            print(f"❌ {dir_path} existiert nicht")
            
            # Erstelle Verzeichnis
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ {dir_path} erstellt")
            except Exception as e:
                print(f"❌ Konnte {dir_path} nicht erstellen: {e}")

def test_pdf_generator():
    """Testet den PDF-Generator direkt"""
    
    print("\n🔍 Teste PDF-Generator...")
    
    try:
        from app.services.pdf_generator import BuildWisePDFGenerator
        
        # Erstelle Test-Daten
        fee_data = {
            'id': 1,
            'invoice_number': 'BW-000001',
            'invoice_date': '2024-01-15',
            'due_date': '2024-02-15',
            'status': 'open',
            'fee_amount': 100.0,
            'fee_percentage': 1.0,
            'tax_rate': 19.0,
            'notes': 'Test-Gebühr'
        }
        
        project_data = {
            'id': 1,
            'name': 'Test-Projekt',
            'project_type': 'renovation',
            'status': 'active',
            'budget': 10000.0,
            'address': 'Teststraße 123, 12345 Teststadt'
        }
        
        quote_data = {
            'id': 1,
            'title': 'Test-Angebot',
            'total_amount': 10000.0,
            'currency': 'EUR',
            'valid_until': '2024-12-31',
            'company_name': 'Test-Dienstleister',
            'contact_person': 'Max Mustermann',
            'email': 'test@example.com',
            'phone': '+49 123 456789'
        }
        
        cost_position_data = {
            'title': 'Test-Kostenposition',
            'description': 'Test-Beschreibung',
            'amount': 10000.0,
            'category': 'construction',
            'status': 'active',
            'contractor_name': 'Test-Dienstleister'
        }
        
        # Erstelle PDF-Generator
        pdf_generator = BuildWisePDFGenerator()
        
        # Erstelle Ausgabepfad
        invoices_dir = "storage/invoices"
        os.makedirs(invoices_dir, exist_ok=True)
        output_path = f"{invoices_dir}/test_invoice.pdf"
        
        # Generiere PDF
        success = pdf_generator.generate_invoice_pdf(
            fee_data=fee_data,
            project_data=project_data,
            quote_data=quote_data,
            cost_position_data=cost_position_data,
            output_path=output_path
        )
        
        if success:
            print("✅ PDF-Generierung erfolgreich!")
            
            # Prüfe ob Datei existiert
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ PDF-Datei existiert, Größe: {file_size} Bytes")
                
                if file_size > 0:
                    print("✅ PDF-Datei ist nicht leer!")
                else:
                    print("⚠️ PDF-Datei ist leer!")
            else:
                print(f"❌ PDF-Datei existiert nicht: {output_path}")
        else:
            print("❌ PDF-Generierung fehlgeschlagen")
            
    except Exception as e:
        print(f"❌ Fehler beim Testen des PDF-Generators: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Hauptfunktion"""
    
    print("🚀 Starte PDF-Generierung Tests...")
    
    # 1. Prüfe Storage-Verzeichnis
    check_storage_directory()
    
    # 2. Teste PDF-Generator
    test_pdf_generator()
    
    print("\n✅ Tests abgeschlossen!")

if __name__ == "__main__":
    main() 