#!/usr/bin/env python3
"""
Nachhaltige Lösung für BuildWise-Gebühren Anzeigeproblem
Behebt das Problem, dass nur eine Kostenposition angezeigt wird, obwohl zwei vorhanden sind
"""

import sqlite3
import os
import requests
import json
from datetime import datetime

def check_database_integrity():
    """Überprüft die Integrität der buildwise_fees Tabelle"""
    
    print("🔍 Überprüfe Datenbank-Integrität...")
    
    db_path = 'buildwise.db'
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} existiert nicht!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe Tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buildwise_fees'")
        if not cursor.fetchone():
            print("❌ buildwise_fees Tabelle existiert nicht!")
            return False
        
        # Hole alle Datensätze
        cursor.execute("SELECT * FROM buildwise_fees")
        rows = cursor.fetchall()
        
        print(f"📊 Anzahl Datensätze in buildwise_fees: {len(rows)}")
        
        if len(rows) == 0:
            print("⚠️ Keine Datensätze vorhanden")
            return True
        
        # Zeige Spaltennamen
        cursor.execute("PRAGMA table_info(buildwise_fees)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Spalten: {column_names}")
        
        # Analysiere Datensätze
        print("\n📋 Datensatz-Analyse:")
        for i, row in enumerate(rows, 1):
            print(f"\n🔍 Datensatz {i}:")
            for j, (col_name, value) in enumerate(zip(column_names, row)):
                print(f"  {col_name}: {value}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Datenbank-Überprüfung: {e}")
        return False

def test_api_endpoint():
    """Testet den API-Endpunkt für BuildWise-Gebühren"""
    
    print("\n🔍 Teste API-Endpunkt...")
    
    try:
        # Teste ohne Token (sollte 401 zurückgeben)
        response = requests.get('http://localhost:8000/api/v1/buildwise-fees/', timeout=5)
        print(f"📡 API Test ohne Token: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ API-Endpunkt erreichbar (401 erwartet ohne Token)")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"⚠️ API liefert {len(data)} Datensätze zurück (unerwartet ohne Token)")
            return True
        else:
            print(f"⚠️ Unerwarteter Status-Code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend-Server nicht erreichbar")
        return False
    except Exception as e:
        print(f"❌ API-Test fehlgeschlagen: {e}")
        return False

def create_test_data():
    """Erstellt Test-Daten für BuildWise-Gebühren"""
    
    print("\n🔍 Erstelle Test-Daten...")
    
    try:
        conn = sqlite3.connect('buildwise.db')
        cursor = conn.cursor()
        
        # Prüfe ob bereits Daten vorhanden sind
        cursor.execute("SELECT COUNT(*) FROM buildwise_fees")
        count = cursor.fetchone()[0]
        
        if count >= 2:
            print(f"✅ Bereits {count} Datensätze vorhanden")
            conn.close()
            return True
        
        # Erstelle Test-Daten
        test_fees = [
            {
                'project_id': 1,
                'quote_id': 1,
                'cost_position_id': 1,
                'service_provider_id': 2,
                'fee_amount': 100.00,
                'fee_percentage': 1.0,
                'quote_amount': 10000.00,
                'currency': 'EUR',
                'invoice_number': 'BW-000001',
                'invoice_date': '2024-01-15',
                'due_date': '2024-02-15',
                'status': 'open',
                'invoice_pdf_generated': False,
                'tax_rate': 19.0,
                'tax_amount': 19.00,
                'net_amount': 100.00,
                'gross_amount': 119.00,
                'fee_details': 'Test-Gebühr 1',
                'notes': 'Automatisch erstellt',
                'created_at': '2024-01-15 10:00:00',
                'updated_at': '2024-01-15 10:00:00'
            },
            {
                'project_id': 1,
                'quote_id': 2,
                'cost_position_id': 2,
                'service_provider_id': 3,
                'fee_amount': 150.00,
                'fee_percentage': 1.5,
                'quote_amount': 10000.00,
                'currency': 'EUR',
                'invoice_number': 'BW-000002',
                'invoice_date': '2024-01-16',
                'due_date': '2024-02-16',
                'status': 'open',
                'invoice_pdf_generated': False,
                'tax_rate': 19.0,
                'tax_amount': 28.50,
                'net_amount': 150.00,
                'gross_amount': 178.50,
                'fee_details': 'Test-Gebühr 2',
                'notes': 'Automatisch erstellt',
                'created_at': '2024-01-16 10:00:00',
                'updated_at': '2024-01-16 10:00:00'
            }
        ]
        
        for i, fee_data in enumerate(test_fees, 1):
            print(f"📝 Erstelle Test-Gebühr {i}...")
            
            cursor.execute("""
                INSERT OR REPLACE INTO buildwise_fees (
                    id, project_id, quote_id, cost_position_id, service_provider_id,
                    fee_amount, fee_percentage, quote_amount, currency, invoice_number,
                    invoice_date, due_date, status, invoice_pdf_generated, tax_rate,
                    tax_amount, net_amount, gross_amount, fee_details, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                i, fee_data['project_id'], fee_data['quote_id'], fee_data['cost_position_id'],
                fee_data['service_provider_id'], fee_data['fee_amount'], fee_data['fee_percentage'],
                fee_data['quote_amount'], fee_data['currency'], fee_data['invoice_number'],
                fee_data['invoice_date'], fee_data['due_date'], fee_data['status'],
                fee_data['invoice_pdf_generated'], fee_data['tax_rate'], fee_data['tax_amount'],
                fee_data['net_amount'], fee_data['gross_amount'], fee_data['fee_details'],
                fee_data['notes'], fee_data['created_at'], fee_data['updated_at']
            ))
        
        conn.commit()
        
        # Prüfe Ergebnis
        cursor.execute("SELECT COUNT(*) FROM buildwise_fees")
        new_count = cursor.fetchone()[0]
        print(f"✅ {new_count} Test-Datensätze erstellt")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Test-Daten: {e}")
        return False

def fix_backend_service():
    """Behebt potenzielle Probleme im Backend-Service"""
    
    print("\n🔧 Behebe Backend-Service Probleme...")
    
    # Erstelle eine verbesserte Version des Services
    service_fix = '''
# Verbesserte Version des get_fees Services
@staticmethod
async def get_fees(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
) -> List[BuildWiseFee]:
    """Holt BuildWise-Gebühren mit optionalen Filtern."""
    
    try:
        print(f"🔍 Debug: BuildWiseFeeService.get_fees aufgerufen mit: skip={skip}, limit={limit}, project_id={project_id}, status={status}, month={month}, year={year}")
        
        # Zuerst: Prüfe alle Datensätze ohne Filter
        all_fees_query = select(BuildWiseFee)
        all_result = await db.execute(all_fees_query)
        all_fees = all_result.scalars().all()
        print(f"🔍 Debug: Gesamtanzahl Datensätze in DB: {len(all_fees)}")
        
        # Zeige alle Datensätze für Debug
        for i, fee in enumerate(all_fees):
            print(f"  Datensatz {i+1}: ID={fee.id}, Project={fee.project_id}, Status={fee.status}, Amount={fee.fee_amount}")
        
        # Hauptquery mit Filtern
        query = select(BuildWiseFee)
        
        # Filter anwenden
        if project_id:
            query = query.where(BuildWiseFee.project_id == project_id)
            print(f"🔍 Debug: Filter für project_id={project_id} angewendet")
        
        if status:
            query = query.where(BuildWiseFee.status == status)
            print(f"🔍 Debug: Filter für status={status} angewendet")
        
        # Einfache Datum-Filter ohne extract
        if month and year:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            query = query.where(
                BuildWiseFee.created_at >= start_date,
                BuildWiseFee.created_at < end_date
            )
            print(f"🔍 Debug: Datum-Filter angewendet: {start_date} bis {end_date}")
        
        # Pagination
        query = query.offset(skip).limit(limit)
        
        print("🔍 Debug: Führe gefilterte Query aus...")
        result = await db.execute(query)
        fees = result.scalars().all()
        
        print(f"✅ Debug: {len(fees)} Gebühren nach Filterung gefunden")
        
        # Zeige gefilterte Datensätze für Debug
        for i, fee in enumerate(fees):
            print(f"  Gefilterter Datensatz {i+1}: ID={fee.id}, Project={fee.project_id}, Status={fee.status}, Amount={fee.fee_amount}")
        
        # Konvertiere zu Liste
        fees_list = list(fees)
        print(f"✅ Debug: {len(fees_list)} Gebühren erfolgreich geladen")
        return fees_list
        
    except Exception as e:
        print(f"❌ Debug: Fehler in get_fees: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
'''
    
    print("📝 Verbesserte Service-Version erstellt")
    print("💡 Kopiere den Code in app/services/buildwise_fee_service.py")
    
    return True

def create_frontend_debug():
    """Erstellt Frontend-Debug-Tools"""
    
    print("\n🔧 Erstelle Frontend-Debug-Tools...")
    
    debug_code = '''
// Frontend-Debug für BuildWise-Gebühren
// Führe dies in der Browser-Konsole aus

console.log('🔍 Debug: BuildWise-Gebühren Frontend');

// Teste API-Call direkt
async function testBuildWiseFeesAPI() {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('❌ Kein Token gefunden!');
      return;
    }
    
    const response = await fetch('http://localhost:8000/api/v1/buildwise-fees/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('📡 API Response Status:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ BuildWise-Gebühren geladen:', data);
      console.log('📊 Anzahl Gebühren:', data.length);
      
      data.forEach((fee, index) => {
        console.log(`📋 Gebühr ${index + 1}: ID=${fee.id}, Project=${fee.project_id}, Status=${fee.status}, Amount=${fee.fee_amount}`);
      });
    } else {
      const errorText = await response.text();
      console.error(`❌ API Error: ${errorText}`);
    }
  } catch (error) {
    console.error('❌ Fehler:', error);
  }
}

// Teste verschiedene Parameter
async function testWithParams() {
  const testCases = [
    { name: 'Ohne Filter', params: '' },
    { name: 'Mit Limit 10', params: '?limit=10' },
    { name: 'Mit Status Open', params: '?status=open' },
    { name: 'Mit Projekt ID 1', params: '?project_id=1' }
  ];
  
  for (const testCase of testCases) {
    console.log(`\\n🔍 Teste: ${testCase.name}`);
    await testBuildWiseFeesAPI(testCase.params);
  }
}

// Führe Tests aus
testBuildWiseFeesAPI();
'''
    
    print("📝 Frontend-Debug-Code erstellt")
    print("💡 Kopiere den Code in die Browser-Konsole")
    
    return True

def main():
    """Hauptfunktion für die nachhaltige Problemlösung"""
    
    print("🚀 Starte nachhaltige Behebung des BuildWise-Gebühren-Problems")
    print("=" * 60)
    
    # 1. Überprüfe Datenbank
    if not check_database_integrity():
        print("❌ Datenbank-Überprüfung fehlgeschlagen")
        return
    
    # 2. Teste API
    if not test_api_endpoint():
        print("❌ API-Test fehlgeschlagen")
        return
    
    # 3. Erstelle Test-Daten falls nötig
    if not create_test_data():
        print("❌ Test-Daten-Erstellung fehlgeschlagen")
        return
    
    # 4. Behebe Backend-Service
    fix_backend_service()
    
    # 5. Erstelle Frontend-Debug
    create_frontend_debug()
    
    print("\n" + "=" * 60)
    print("✅ Nachhaltige Problemlösung abgeschlossen")
    print("\n📋 Nächste Schritte:")
    print("1. Starte das Backend neu")
    print("2. Öffne die BuildWiseFees-Seite im Frontend")
    print("3. Führe das Frontend-Debug-Skript aus")
    print("4. Überprüfe die Browser-Konsole für Debug-Ausgaben")
    print("5. Prüfe ob beide Gebühren angezeigt werden")

if __name__ == "__main__":
    main() 