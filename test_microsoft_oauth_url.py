#!/usr/bin/env python3
"""
Test-Skript für Microsoft OAuth-URL-Generierung
"""

import asyncio
import sys
import os
from urllib.parse import urlparse, parse_qs

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.oauth_service import OAuthService

async def test_microsoft_oauth_url():
    """Testet die Microsoft OAuth-URL-Generierung."""
    
    print("🚀 Teste Microsoft OAuth-URL-Generierung...")
    print("=" * 60)
    
    try:
        # Generiere Microsoft OAuth-URL
        oauth_url = await OAuthService.get_oauth_url("microsoft")
        
        print(f"✅ Microsoft OAuth-URL generiert:")
        print(f"   URL: {oauth_url}")
        
        # Parse URL und zeige Parameter
        parsed_url = urlparse(oauth_url)
        params = parse_qs(parsed_url.query)
        
        print(f"\n📋 URL-Parameter:")
        for key, value in params.items():
            print(f"   - {key}: {value[0]}")
        
        # Prüfe wichtige Parameter
        required_params = [
            "client_id",
            "redirect_uri", 
            "response_type",
            "scope",
            "response_mode",
            "prompt",
            "login_hint",
            "domain_hint"
        ]
        
        print(f"\n🔍 Parameter-Prüfung:")
        for param in required_params:
            if param in params:
                print(f"   ✅ {param}: {params[param][0]}")
            else:
                print(f"   ❌ {param}: Fehlt")
        
        # Spezielle Prüfung für Account-Auswahl
        if "prompt" in params and params["prompt"][0] == "select_account":
            print(f"\n✅ Account-Auswahl erzwungen: prompt=select_account")
        else:
            print(f"\n❌ Account-Auswahl nicht erzwungen")
            
        if "login_hint" in params and params["login_hint"][0] == "":
            print(f"✅ Login-Hint leer gesetzt (verhindert automatische Anmeldung)")
        else:
            print(f"❌ Login-Hint nicht leer gesetzt")
            
        if "domain_hint" in params and params["domain_hint"][0] == "":
            print(f"✅ Domain-Hint leer gesetzt (verhindert automatische Anmeldung)")
        else:
            print(f"❌ Domain-Hint nicht leer gesetzt")
        
        print(f"\n🎯 Ergebnis:")
        print(f"   - URL generiert: ✅")
        print(f"   - Account-Auswahl erzwungen: {'✅' if 'prompt' in params and params['prompt'][0] == 'select_account' else '❌'}")
        print(f"   - Automatische Anmeldung verhindert: {'✅' if 'login_hint' in params and params['login_hint'][0] == '' else '❌'}")
        
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_microsoft_oauth_url()) 