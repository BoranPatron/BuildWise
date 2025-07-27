#!/usr/bin/env python3
"""
Test-Skript für die neue Kategorie-Aggregations-Funktionalität
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.milestone_service import aggregate_category_specific_fields

def test_aggregation():
    """Testet die Aggregations-Funktion mit verschiedenen Szenarien"""
    
    print("🧪 Teste Kategorie-Aggregations-Funktionalität")
    print("=" * 60)
    
    # Test 1: Elektro-Gewerk mit allen Feldern
    print("\n📋 Test 1: Elektro-Gewerk mit allen Feldern")
    print("-" * 40)
    
    result1 = aggregate_category_specific_fields(
        base_description="Elektroinstallation für das Erdgeschoss",
        category="elektro",
        category_specific_fields={
            "electrical_voltage": "230V/400V",
            "electrical_power": "15.5",
            "electrical_circuits": "8",
            "electrical_switches": "12",
            "electrical_outlets": "24",
            "electrical_lighting_points": "18"
        },
        technical_specifications="VDE-konforme Installation erforderlich",
        quality_requirements="Qualitätsstufe 1 nach DIN",
        safety_requirements="Brandschutz nach DIN 4102",
        environmental_requirements="Energieeffiziente LED-Beleuchtung",
        notes="Besondere Aufmerksamkeit auf Küchenbereich"
    )
    
    print("Ergebnis:")
    print(result1)
    
    # Test 2: Sanitär-Gewerk mit minimalen Feldern
    print("\n📋 Test 2: Sanitär-Gewerk mit minimalen Feldern")
    print("-" * 40)
    
    result2 = aggregate_category_specific_fields(
        base_description="Sanitäranlagen für Badezimmer",
        category="sanitaer",
        category_specific_fields={
            "plumbing_fixtures": "6",
            "plumbing_pipes_length": "45.5",
            "plumbing_water_heater": True,
            "plumbing_sewage_system": True,
            "plumbing_water_supply": False
        },
        technical_specifications="",
        quality_requirements="",
        safety_requirements="",
        environmental_requirements="",
        notes=""
    )
    
    print("Ergebnis:")
    print(result2)
    
    # Test 3: Dach-Gewerk mit gemischten Feldern
    print("\n📋 Test 3: Dach-Gewerk mit gemischten Feldern")
    print("-" * 40)
    
    result3 = aggregate_category_specific_fields(
        base_description="Dachsanierung mit neuer Dämmung",
        category="dach",
        category_specific_fields={
            "roof_material": "Ziegel",
            "roof_area": "120.5",
            "roof_pitch": "35",
            "roof_insulation": True,
            "roof_gutters": True,
            "roof_skylights": "2"
        },
        technical_specifications="Dämmung nach EnEV 2020",
        quality_requirements="",
        safety_requirements="Dachstuhl-Statik prüfen",
        environmental_requirements="",
        notes="Besichtigung vor Beginn erforderlich"
    )
    
    print("Ergebnis:")
    print(result3)
    
    # Test 4: Leere Felder
    print("\n📋 Test 4: Leere Felder")
    print("-" * 40)
    
    result4 = aggregate_category_specific_fields(
        base_description="",
        category="",
        category_specific_fields={},
        technical_specifications="",
        quality_requirements="",
        safety_requirements="",
        environmental_requirements="",
        notes=""
    )
    
    print("Ergebnis:")
    print(f"'{result4}'")
    
    print("\n✅ Alle Tests abgeschlossen!")

if __name__ == "__main__":
    test_aggregation() 