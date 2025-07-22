#!/usr/bin/env python3
"""
Test-Skript für Finance-Analytics API
"""

import requests
import json

def test_finance_api():
    """Testet die Finance-Analytics API-Endpunkte"""
    base_url = "http://localhost:8000/api/v1"
    
    # Teste ohne Authentication (für Debug-Zwecke)
    headers = {}
    
    print("🔍 TESTE FINANCE-ANALYTICS API")
    print("=" * 50)
    
    # Teste Summary-Endpunkt
    try:
        response = requests.get(f"{base_url}/finance-analytics/project/1/summary", headers=headers)
        print(f"📊 Summary-Endpunkt Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Gesamtbetrag: {data['summary']['total_amount']}€")
            print(f"   Bezahlt: {data['summary']['total_paid']}€")
            print(f"   Fortschritt: {data['summary']['completion_percentage']}%")
            print(f"   Anzahl Phasen: {len(data['phases']['phases'])}")
            print(f"   Anzahl Kategorien: {len(data['categories']['categories'])}")
            print(f"   Anzahl Status: {len(data['statuses']['statuses'])}")
        else:
            print(f"   Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    # Teste Phasen-Endpunkt
    try:
        response = requests.get(f"{base_url}/finance-analytics/project/1/costs-by-phase", headers=headers)
        print(f"\n🏗️  Phasen-Endpunkt Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Anzahl Phasen: {len(data['phases'])}")
            for phase in data['phases']:
                print(f"     {phase['phase']}: {phase['total_amount']}€ ({phase['total_paid']}€ bezahlt)")
        else:
            print(f"   Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    # Teste Zeit-Endpunkt
    try:
        response = requests.get(f"{base_url}/finance-analytics/project/1/costs-over-time?period=monthly&months=12", headers=headers)
        print(f"\n📈 Zeit-Endpunkt Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Anzahl Zeitpunkte: {len(data['time_data'])}")
            for time_point in data['time_data']:
                print(f"     {time_point['year']}-{time_point['period']}: {time_point['total_amount']}€")
        else:
            print(f"   Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    # Teste Kategorien-Endpunkt
    try:
        response = requests.get(f"{base_url}/finance-analytics/project/1/costs-by-category", headers=headers)
        print(f"\n📋 Kategorien-Endpunkt Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Anzahl Kategorien: {len(data['categories'])}")
            for category in data['categories']:
                print(f"     {category['category_name']}: {category['total_amount']}€")
        else:
            print(f"   Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    # Teste Status-Endpunkt
    try:
        response = requests.get(f"{base_url}/finance-analytics/project/1/costs-by-status", headers=headers)
        print(f"\n✅ Status-Endpunkt Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Anzahl Status: {len(data['statuses'])}")
            for status in data['statuses']:
                print(f"     {status['status_name']}: {status['total_amount']}€")
        else:
            print(f"   Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    # Teste Milestones-Endpunkt
    try:
        response = requests.get(f"{base_url}/finance-analytics/project/1/milestone-costs", headers=headers)
        print(f"\n🔧 Milestones-Endpunkt Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Anzahl Milestones: {len(data['milestones'])}")
            for milestone in data['milestones']:
                print(f"     {milestone['milestone_title']}: {milestone['total_amount']}€")
        else:
            print(f"   Fehler: {response.text}")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")

if __name__ == "__main__":
    test_finance_api() 