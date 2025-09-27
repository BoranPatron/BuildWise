#!/usr/bin/env python3

"""
Script: Geocode bestehende Ressourcen
Geocodiert alle Ressourcen mit Adressen und speichert die Koordinaten in der Datenbank.
"""

import sqlite3
import requests
import time
import sys
from datetime import datetime

def geocode_address(address):
    """Geocode eine Adresse mit OpenStreetMap Nominatim"""
    try:
        # Bereinige die Adresse
        clean_address = address.strip().replace('\n', ' ').replace('\r', ' ')
        
        # Nominatim API URL
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': clean_address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'ch,de',  # Schweiz und Deutschland
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'BuildWise-Geocoding/1.0'
        }
        
        print(f"🌍 Geocoding: {clean_address}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            
            print(f"✅ Gefunden: {lat:.6f}, {lon:.6f}")
            return lat, lon
        else:
            print(f"❌ Keine Ergebnisse für: {clean_address}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Netzwerkfehler: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Geocoding-Fehler: {e}")
        return None, None

def geocode_resources(conn):
    """Geocode alle Ressourcen ohne Koordinaten"""
    
    cursor = conn.cursor()
    
    print("🔍 Suche Ressourcen ohne Koordinaten...")
    
    # Finde Ressourcen ohne Koordinaten aber mit Adressen
    cursor.execute("""
        SELECT id, address_street, address_city, address_postal_code, address_country
        FROM resources 
        WHERE (latitude IS NULL OR longitude IS NULL)
        AND (address_street IS NOT NULL OR address_city IS NOT NULL)
        AND address_street != '' AND address_city != ''
    """)
    
    resources = cursor.fetchall()
    
    if not resources:
        print("✅ Alle Ressourcen haben bereits Koordinaten!")
        return
    
    print(f"📋 Gefunden: {len(resources)} Ressourcen ohne Koordinaten")
    
    success_count = 0
    error_count = 0
    
    for i, resource in enumerate(resources, 1):
        resource_id, street, city, postal_code, country = resource
        
        # Erstelle vollständige Adresse
        address_parts = []
        if street:
            address_parts.append(street)
        if city:
            address_parts.append(city)
        if postal_code:
            address_parts.append(postal_code)
        if country:
            address_parts.append(country)
        
        full_address = ', '.join(address_parts)
        
        print(f"\n📍 [{i}/{len(resources)}] Resource ID {resource_id}: {full_address}")
        
        # Geocode die Adresse
        lat, lon = geocode_address(full_address)
        
        if lat is not None and lon is not None:
            # Speichere Koordinaten in der Datenbank
            try:
                cursor.execute("""
                    UPDATE resources 
                    SET latitude = ?, longitude = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (lat, lon, resource_id))
                
                conn.commit()
                print(f"✅ Koordinaten gespeichert: {lat:.6f}, {lon:.6f}")
                success_count += 1
                
            except sqlite3.Error as e:
                print(f"❌ Datenbankfehler: {e}")
                error_count += 1
        else:
            print(f"❌ Geocoding fehlgeschlagen")
            error_count += 1
        
        # Rate limiting - 1 Sekunde Pause zwischen Anfragen
        if i < len(resources):
            print("⏳ Warte 1 Sekunde...")
            time.sleep(1)
    
    print(f"\n📊 Zusammenfassung:")
    print(f"  ✅ Erfolgreich geocodiert: {success_count}")
    print(f"  ❌ Fehlgeschlagen: {error_count}")
    print(f"  📋 Gesamt: {len(resources)}")

def verify_geocoding(conn):
    """Verifiziere die Geocoding-Ergebnisse"""
    
    cursor = conn.cursor()
    
    print("\n🔍 Verifikation der Geocoding-Ergebnisse:")
    
    # Zähle Ressourcen mit Koordinaten
    cursor.execute("SELECT COUNT(*) FROM resources WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    with_coords = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM resources WHERE latitude IS NULL OR longitude IS NULL")
    without_coords = cursor.fetchone()[0]
    
    print(f"📊 Koordinaten-Status:")
    print(f"  ✅ Mit Koordinaten: {with_coords}")
    print(f"  ❌ Ohne Koordinaten: {without_coords}")
    
    # Zeige alle Ressourcen mit Koordinaten
    cursor.execute("""
        SELECT id, address_city, latitude, longitude 
        FROM resources 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY id
    """)
    
    resources_with_coords = cursor.fetchall()
    
    if resources_with_coords:
        print(f"\n📍 Ressourcen mit Koordinaten:")
        for resource in resources_with_coords:
            print(f"  ID {resource[0]}: {resource[1]} - {resource[2]:.6f}, {resource[3]:.6f}")
    else:
        print("\n❌ Keine Ressourcen mit Koordinaten gefunden!")

def main():
    """Hauptfunktion"""
    
    print("🚀 Starte Geocoding bestehender Ressourcen...")
    print(f"📅 Zeitstempel: {datetime.now()}")
    
    # Verbinde zur Datenbank
    try:
        conn = sqlite3.connect('buildwise.db')
        print("✅ Datenbankverbindung hergestellt")
        
        # Führe Geocoding aus
        geocode_resources(conn)
        
        # Verifiziere Ergebnisse
        verify_geocoding(conn)
        
        print("\n🎉 Geocoding abgeschlossen!")
        
    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            print("🔐 Datenbankverbindung geschlossen")

if __name__ == "__main__":
    main()
