#!/usr/bin/env python3
"""
Umfassendes Test-Skript für BuildWise
Erstellt vollständige Test-Daten mit Projekten, Milestones, Quotes und Cost Positions
"""

import sys
import os
from datetime import datetime, timedelta

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

def create_test_data():
    """Erstellt umfassende Test-Daten"""
    print("🚀 Erstelle umfassende Test-Daten für BuildWise")
    print("=" * 60)
    
    # Direkte SQLite-Verbindung
    DATABASE_URL = "sqlite:///buildwise.db"
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Prüfe existierende Daten
        print("\n📊 Aktuelle Datenbank-Status:")
        
        # Projekte
        result = conn.execute(text("SELECT COUNT(*) FROM projects"))
        project_count_result = result.fetchone()
        project_count = project_count_result[0] if project_count_result else 0
        print(f"  - Projekte: {project_count}")
        
        # Milestones
        result = conn.execute(text("SELECT COUNT(*) FROM milestones"))
        milestone_count_result = result.fetchone()
        milestone_count = milestone_count_result[0] if milestone_count_result else 0
        print(f"  - Milestones: {milestone_count}")
        
        # Quotes
        result = conn.execute(text("SELECT COUNT(*) FROM quotes"))
        quote_count_result = result.fetchone()
        quote_count = quote_count_result[0] if quote_count_result else 0
        print(f"  - Quotes: {quote_count}")
        
        # Cost Positions
        result = conn.execute(text("SELECT COUNT(*) FROM cost_positions"))
        cp_count_result = result.fetchone()
        cp_count = cp_count_result[0] if cp_count_result else 0
        print(f"  - Cost Positions: {cp_count}")
        
        # 2. Erstelle Test-Milestones für Projekt 4 (Hausbau Boran)
        print("\n🏗️ Erstelle Test-Milestones...")
        
        milestones_data = [
            {
                'title': 'Elektroinstallation',
                'description': 'Vollständige Elektroinstallation inkl. Beleuchtung und Steckdosen',
                'project_id': 4,
                'status': 'PLANNING',
                'priority': 'HIGH',
                'planned_date': (datetime.now() + timedelta(days=30)).isoformat(),
                'category': 'elektro',
                'budget': 38000,
                'is_critical': True,
                'notify_on_completion': True
            },
            {
                'title': 'Sanitäranlagen',
                'description': 'Badezimmer und Küche mit hochwertigen Armaturen',
                'project_id': 4,
                'status': 'PLANNING',
                'priority': 'HIGH',
                'planned_date': (datetime.now() + timedelta(days=45)).isoformat(),
                'category': 'sanitär',
                'budget': 42000,
                'is_critical': True,
                'notify_on_completion': True
            },
            {
                'title': 'Dach neu',
                'description': 'Komplett neues Dach mit Dämmung und Dachfenstern',
                'project_id': 4,
                'status': 'PLANNING',
                'priority': 'CRITICAL',
                'planned_date': (datetime.now() + timedelta(days=60)).isoformat(),
                'category': 'dach',
                'budget': 32000,
                'is_critical': True,
                'notify_on_completion': True
            },
            {
                'title': 'Fussbodenheizung',
                'description': 'Moderne Fussbodenheizung für alle Räume',
                'project_id': 4,
                'status': 'PLANNING',
                'priority': 'MEDIUM',
                'planned_date': (datetime.now() + timedelta(days=75)).isoformat(),
                'category': 'heizung',
                'budget': 32000,
                'is_critical': False,
                'notify_on_completion': True
            }
        ]
        
        created_milestones = []
        for milestone_data in milestones_data:
            conn.execute(text("""
                INSERT INTO milestones (
                    title, description, project_id, status, priority, 
                    planned_date, category, budget, is_critical, notify_on_completion,
                    created_at, updated_at
                ) VALUES (
                    :title, :description, :project_id, :status, :priority,
                    :planned_date, :category, :budget, :is_critical, :notify_on_completion,
                    :created_at, :updated_at
                )
            """), {
                **milestone_data,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
            
            # Hole die ID des erstellten Milestones
            result = conn.execute(text("SELECT last_insert_rowid()"))
            milestone_id = result.fetchone()[0]
            created_milestones.append(milestone_id)
            print(f"  ✅ Milestone erstellt: {milestone_data['title']} (ID: {milestone_id})")
        
        conn.commit()
        
        # 3. Erstelle Test-Quotes für die Milestones
        print("\n💼 Erstelle Test-Quotes...")
        
        quotes_data = [
            # Elektroinstallation
            {
                'title': 'Elektroinstallation - Premium',
                'description': 'Vollständige Elektroinstallation mit Smart-Home-System',
                'project_id': 4,
                'milestone_id': created_milestones[0],
                'service_provider_id': 3,  # Dienstleister
                'total_amount': 42000,
                'currency': 'EUR',
                'valid_until': (datetime.now() + timedelta(days=30)).isoformat(),
                'labor_cost': 28000,
                'material_cost': 12000,
                'overhead_cost': 2000,
                'estimated_duration': 14,
                'start_date': (datetime.now() + timedelta(days=30)).isoformat(),
                'completion_date': (datetime.now() + timedelta(days=44)).isoformat(),
                'payment_terms': '30 Tage nach Rechnung',
                'warranty_period': 24,
                'status': 'SUBMITTED',
                'company_name': 'Elektro Meier GmbH',
                'contact_person': 'Hans Meier',
                'phone': '+49 123 456789',
                'email': 'hans.meier@elektro-meier.de',
                'website': 'www.elektro-meier.de'
            },
            {
                'title': 'Elektroinstallation - Standard',
                'description': 'Standard Elektroinstallation ohne Smart-Home',
                'project_id': 4,
                'milestone_id': created_milestones[0],
                'service_provider_id': 3,
                'total_amount': 38000,
                'currency': 'EUR',
                'valid_until': (datetime.now() + timedelta(days=30)).isoformat(),
                'labor_cost': 25000,
                'material_cost': 11000,
                'overhead_cost': 2000,
                'estimated_duration': 12,
                'start_date': (datetime.now() + timedelta(days=30)).isoformat(),
                'completion_date': (datetime.now() + timedelta(days=42)).isoformat(),
                'payment_terms': '30 Tage nach Rechnung',
                'warranty_period': 24,
                'status': 'SUBMITTED',
                'company_name': 'Elektro Schmidt',
                'contact_person': 'Peter Schmidt',
                'phone': '+49 123 456790',
                'email': 'peter.schmidt@elektro-schmidt.de',
                'website': 'www.elektro-schmidt.de'
            },
            # Sanitäranlagen
            {
                'title': 'Sanitäranlagen - Premium',
                'description': 'Luxuriöse Badezimmer mit Designer-Armaturen',
                'project_id': 4,
                'milestone_id': created_milestones[1],
                'service_provider_id': 3,
                'total_amount': 48000,
                'currency': 'EUR',
                'valid_until': (datetime.now() + timedelta(days=30)).isoformat(),
                'labor_cost': 32000,
                'material_cost': 14000,
                'overhead_cost': 2000,
                'estimated_duration': 18,
                'start_date': (datetime.now() + timedelta(days=45)).isoformat(),
                'completion_date': (datetime.now() + timedelta(days=63)).isoformat(),
                'payment_terms': '30 Tage nach Rechnung',
                'warranty_period': 36,
                'status': 'SUBMITTED',
                'company_name': 'Sanitär Luxus GmbH',
                'contact_person': 'Maria Weber',
                'phone': '+49 123 456791',
                'email': 'maria.weber@sanitaer-luxus.de',
                'website': 'www.sanitaer-luxus.de'
            },
            {
                'title': 'Sanitäranlagen - Standard',
                'description': 'Standard Sanitäranlagen mit hochwertigen Armaturen',
                'project_id': 4,
                'milestone_id': created_milestones[1],
                'service_provider_id': 3,
                'total_amount': 42000,
                'currency': 'EUR',
                'valid_until': (datetime.now() + timedelta(days=30)).isoformat(),
                'labor_cost': 28000,
                'material_cost': 12000,
                'overhead_cost': 2000,
                'estimated_duration': 15,
                'start_date': (datetime.now() + timedelta(days=45)).isoformat(),
                'completion_date': (datetime.now() + timedelta(days=60)).isoformat(),
                'payment_terms': '30 Tage nach Rechnung',
                'warranty_period': 24,
                'status': 'SUBMITTED',
                'company_name': 'Sanitär Standard',
                'contact_person': 'Klaus Müller',
                'phone': '+49 123 456792',
                'email': 'klaus.mueller@sanitaer-standard.de',
                'website': 'www.sanitaer-standard.de'
            }
        ]
        
        created_quotes = []
        for quote_data in quotes_data:
            conn.execute(text("""
                INSERT INTO quotes (
                    title, description, project_id, milestone_id, service_provider_id,
                    total_amount, currency, valid_until, labor_cost, material_cost, overhead_cost,
                    estimated_duration, start_date, completion_date, payment_terms, warranty_period,
                    status, company_name, contact_person, phone, email, website,
                    created_at, updated_at
                ) VALUES (
                    :title, :description, :project_id, :milestone_id, :service_provider_id,
                    :total_amount, :currency, :valid_until, :labor_cost, :material_cost, :overhead_cost,
                    :estimated_duration, :start_date, :completion_date, :payment_terms, :warranty_period,
                    :status, :company_name, :contact_person, :phone, :email, :website,
                    :created_at, :updated_at
                )
            """), {
                **quote_data,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
            
            # Hole die ID des erstellten Quotes
            result = conn.execute(text("SELECT last_insert_rowid()"))
            quote_id = result.fetchone()[0]
            created_quotes.append(quote_id)
            print(f"  ✅ Quote erstellt: {quote_data['title']} (ID: {quote_id})")
        
        conn.commit()
        
        # 4. Akzeptiere ein Quote und erstelle Cost Position
        print("\n✅ Akzeptiere ein Quote und erstelle Cost Position...")
        
        # Akzeptiere das erste Quote (Elektroinstallation Premium)
        quote_to_accept = created_quotes[0]
        
        # Setze Quote auf 'accepted'
        conn.execute(text("""
            UPDATE quotes 
            SET status = 'accepted', accepted_at = :accepted_at, updated_at = :updated_at
            WHERE id = :quote_id
        """), {
            'quote_id': quote_to_accept,
            'accepted_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        
        # Hole Quote-Daten für Cost Position
        result = conn.execute(text("""
            SELECT title, description, total_amount, currency, project_id, milestone_id,
                   company_name, contact_person, email, payment_terms, warranty_period,
                   estimated_duration, start_date, completion_date, labor_cost, material_cost, overhead_cost
            FROM quotes WHERE id = :quote_id
        """), {'quote_id': quote_to_accept})
        
        quote_data = result.fetchone()
        
        # Erstelle Cost Position
        conn.execute(text("""
            INSERT INTO cost_positions (
                title, description, amount, currency, project_id, milestone_id, quote_id,
                contractor_name, contractor_contact, contractor_email, payment_terms, warranty_period,
                estimated_duration, start_date, completion_date, labor_cost, material_cost, overhead_cost,
                status, cost_type, category, created_at, updated_at
            ) VALUES (
                :title, :description, :amount, :currency, :project_id, :milestone_id, :quote_id,
                :contractor_name, :contractor_contact, :contractor_email, :payment_terms, :warranty_period,
                :estimated_duration, :start_date, :completion_date, :labor_cost, :material_cost, :overhead_cost,
                'ACTIVE', 'QUOTE_ACCEPTED', 'ELECTRICAL', :created_at, :updated_at
            )
        """), {
            'title': f"Kostenposition: {quote_data[0]}",
            'description': quote_data[1] or f"Kostenposition für {quote_data[0]}",
            'amount': quote_data[2],
            'currency': quote_data[3],
            'project_id': quote_data[4],
            'milestone_id': quote_data[5],
            'quote_id': quote_to_accept,
            'contractor_name': quote_data[6],
            'contractor_contact': quote_data[7],
            'contractor_email': quote_data[8],
            'payment_terms': quote_data[9],
            'warranty_period': quote_data[10],
            'estimated_duration': quote_data[11],
            'start_date': quote_data[12],
            'completion_date': quote_data[13],
            'labor_cost': quote_data[14],
            'material_cost': quote_data[15],
            'overhead_cost': quote_data[16],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        
        conn.commit()
        print(f"  ✅ Quote akzeptiert und Cost Position erstellt (Quote ID: {quote_to_accept})")
        
        # 5. Finale Übersicht
        print("\n📊 Finale Datenbank-Status:")
        
        result = conn.execute(text("SELECT COUNT(*) FROM milestones"))
        milestone_count = result.fetchone()[0]
        print(f"  - Milestones: {milestone_count}")
        
        result = conn.execute(text("SELECT COUNT(*) FROM quotes"))
        quote_count = result.fetchone()[0]
        print(f"  - Quotes: {quote_count}")
        
        result = conn.execute(text("SELECT COUNT(*) FROM cost_positions"))
        cp_count = result.fetchone()[0]
        print(f"  - Cost Positions: {cp_count}")
        
        # Zeige akzeptierte Quotes
        result = conn.execute(text("SELECT id, title, status FROM quotes WHERE status = 'accepted'"))
        accepted_quotes = result.fetchall()
        if accepted_quotes:
            print("\n✅ Akzeptierte Quotes:")
            for quote in accepted_quotes:
                print(f"  - ID: {quote[0]}, Titel: {quote[1]}, Status: {quote[2]}")
        
        print("\n" + "=" * 60)
        print("🎯 Test-Daten erfolgreich erstellt!")
        print("\n💡 Nächste Schritte:")
        print("  1. Starte das Backend neu")
        print("  2. Gehe ins Frontend und prüfe die Gewerke")
        print("  3. Teste das Akzeptieren von Angeboten")
        print("  4. Prüfe die Finanzübersicht für Kostenpositionen")

if __name__ == "__main__":
    create_test_data() 