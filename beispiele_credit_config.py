#!/usr/bin/env python3
"""
Beispiel-Script für die Verwendung des BuildWise Credit-Konfigurationssystems

Dieses Script zeigt praktische Beispiele, wie die neue Konfiguration verwendet werden kann.
"""

import sys
import os

# Füge den BuildWise-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.config.credit_config import credit_config
from app.models.credit_event import CreditEventType


def beispiel_1_credit_belohnungen_anpassen():
    """Beispiel 1: Credit-Belohnungen für verschiedene Aktionen anpassen"""
    
    print("=== Beispiel 1: Credit-Belohnungen anpassen ===")
    print()
    
    print("Aktuelle Belohnungen:")
    actions = [
        CreditEventType.QUOTE_ACCEPTED,
        CreditEventType.INSPECTION_QUOTE_ACCEPTED,
        CreditEventType.PROJECT_COMPLETED,
        CreditEventType.DOCUMENT_UPLOADED
    ]
    
    for action in actions:
        reward = credit_config.get_credit_reward(action)
        print(f"  {action.value}: {reward} Credits")
    
    print()
    print("Anpassung der Belohnungen:")
    
    # Erhöhe Belohnung für Angebot annehmen
    credit_config.update_credit_reward(CreditEventType.QUOTE_ACCEPTED, 7)
    print(f"  Angebot annehmen: 5 -> 7 Credits")
    
    # Erhöhe Belohnung für Projektabschluss
    credit_config.update_credit_reward(CreditEventType.PROJECT_COMPLETED, 15)
    print(f"  Projekt abgeschlossen: 10 -> 15 Credits")
    
    # Reduziere Belohnung für Dokument-Upload
    credit_config.update_credit_reward(CreditEventType.DOCUMENT_UPLOADED, 0)
    print(f"  Dokument hochgeladen: 1 -> 0 Credits (deaktiviert)")
    
    print()
    print("Neue Belohnungen:")
    for action in actions:
        reward = credit_config.get_credit_reward(action)
        print(f"  {action.value}: {reward} Credits")
    
    print()


def beispiel_2_feature_flags_verwaltung():
    """Beispiel 2: Feature-Flags aktivieren/deaktivieren"""
    
    print("=== Beispiel 2: Feature-Flags verwalten ===")
    print()
    
    print("Aktuelle Feature-Status:")
    features = [
        'enable_inspection_bonus',
        'enable_loyalty_bonus',
        'enable_daily_deduction',
        'enable_auto_upgrade'
    ]
    
    for feature in features:
        status = credit_config.is_feature_enabled(feature)
        print(f"  {feature}: {'AKTIVIERT' if status else 'DEAKTIVIERT'}")
    
    print()
    print("Feature-Änderungen:")
    
    # Deaktiviere täglichen Abzug temporär
    credit_config.toggle_feature('enable_daily_deduction', False)
    print("  Täglicher Abzug: DEAKTIVIERT (für Wartung)")
    
    # Aktiviere automatisches Upgrade
    credit_config.toggle_feature('enable_auto_upgrade', True)
    print("  Automatisches Upgrade: AKTIVIERT")
    
    print()
    print("Neue Feature-Status:")
    for feature in features:
        status = credit_config.is_feature_enabled(feature)
        print(f"  {feature}: {'AKTIVIERT' if status else 'DEAKTIVIERT'}")
    
    print()


def beispiel_3_system_parameter_anpassen():
    """Beispiel 3: System-Parameter anpassen"""
    
    print("=== Beispiel 3: System-Parameter anpassen ===")
    print()
    
    print("Aktuelle System-Parameter:")
    print(f"  Täglicher Abzug: {credit_config.DAILY_CREDIT_DEDUCTION} Credits")
    print(f"  Warnschwelle: {credit_config.LOW_CREDIT_WARNING_THRESHOLD} Credits")
    print(f"  Max. Credits pro Tag: {credit_config.MAX_CREDITS_PER_DAY}")
    
    print()
    print("Anpassung der Parameter:")
    
    # Reduziere täglichen Abzug für bessere User Experience
    credit_config.DAILY_CREDIT_DEDUCTION = 0.5
    print(f"  Täglicher Abzug: 1 -> 0.5 Credits")
    
    # Erhöhe Warnschwelle
    credit_config.LOW_CREDIT_WARNING_THRESHOLD = 20
    print(f"  Warnschwelle: 10 -> 20 Credits")
    
    # Erhöhe tägliches Limit für Power-User
    credit_config.MAX_CREDITS_PER_DAY = 200
    print(f"  Max. Credits pro Tag: 100 -> 200")
    
    print()
    print("Neue System-Parameter:")
    print(f"  Täglicher Abzug: {credit_config.DAILY_CREDIT_DEDUCTION} Credits")
    print(f"  Warnschwelle: {credit_config.LOW_CREDIT_WARNING_THRESHOLD} Credits")
    print(f"  Max. Credits pro Tag: {credit_config.MAX_CREDITS_PER_DAY}")
    
    print()


def beispiel_4_anti_spam_limits():
    """Beispiel 4: Anti-Spam-Limits konfigurieren"""
    
    print("=== Beispiel 4: Anti-Spam-Limits konfigurieren ===")
    print()
    
    print("Aktuelle Anti-Spam-Limits:")
    limits = credit_config.MAX_CREDITS_PER_ACTION_PER_DAY
    
    for event_type, limit in limits.items():
        print(f"  {event_type.value}: max. {limit} Credits pro Tag")
    
    print()
    print("Anpassung der Limits:")
    
    # Erhöhe Limit für Angebot annehmen (häufige Aktion)
    credit_config.MAX_CREDITS_PER_ACTION_PER_DAY[CreditEventType.QUOTE_ACCEPTED] = 100
    print(f"  Angebot annehmen: 50 -> 100 Credits pro Tag")
    
    # Reduziere Limit für Projektabschluss (seltene Aktion)
    credit_config.MAX_CREDITS_PER_ACTION_PER_DAY[CreditEventType.PROJECT_COMPLETED] = 10
    print(f"  Projekt abgeschlossen: 20 -> 10 Credits pro Tag")
    
    print()
    print("Neue Anti-Spam-Limits:")
    for event_type, limit in limits.items():
        print(f"  {event_type.value}: max. {limit} Credits pro Tag")
    
    print()


def beispiel_5_konfiguration_exportieren():
    """Beispiel 5: Konfiguration exportieren und importieren"""
    
    print("=== Beispiel 5: Konfiguration exportieren ===")
    print()
    
    # Exportiere komplette Konfiguration
    config = credit_config.get_all_config()
    
    print("Exportierte Konfiguration:")
    print(f"  Credit-Rewards: {len(config['credit_rewards'])} Einträge")
    print(f"  Feature-Flags: {len(config['feature_flags'])} Einträge")
    print(f"  System-Parameter: {len([k for k in config.keys() if k not in ['credit_rewards', 'feature_flags', 'credit_packages', 'max_credits_per_action_per_day']])} Einträge")
    
    print()
    print("Beispiel für API-Integration:")
    print("  GET /api/credits/admin/config")
    print("  -> Gibt diese Konfiguration zurück")
    
    print()
    print("Beispiel für Konfigurationsdatei:")
    print("  Die Konfiguration kann in eine JSON-Datei exportiert werden")
    print("  und später wieder importiert werden")
    
    print()


def beispiel_6_saisonale_anpassungen():
    """Beispiel 6: Saisonale Anpassungen"""
    
    print("=== Beispiel 6: Saisonale Anpassungen ===")
    print()
    
    print("Sommer-Kampagne: Erhöhte Belohnungen")
    
    # Sommer-Kampagne: Erhöhe alle Belohnungen um 50%
    summer_multiplier = 1.5
    
    actions_to_boost = [
        CreditEventType.QUOTE_ACCEPTED,
        CreditEventType.INSPECTION_QUOTE_ACCEPTED,
        CreditEventType.PROJECT_COMPLETED,
        CreditEventType.DOCUMENT_UPLOADED
    ]
    
    print("Belohnungen vor Sommer-Kampagne:")
    for action in actions_to_boost:
        old_reward = credit_config.get_credit_reward(action)
        print(f"  {action.value}: {old_reward} Credits")
    
    print()
    print("Anpassung für Sommer-Kampagne:")
    for action in actions_to_boost:
        old_reward = credit_config.get_credit_reward(action)
        new_reward = int(old_reward * summer_multiplier)
        credit_config.update_credit_reward(action, new_reward)
        print(f"  {action.value}: {old_reward} -> {new_reward} Credits")
    
    print()
    print("Belohnungen nach Sommer-Kampagne:")
    for action in actions_to_boost:
        reward = credit_config.get_credit_reward(action)
        print(f"  {action.value}: {reward} Credits")
    
    print()
    print("Ende der Sommer-Kampagne: Zurücksetzen")
    # Setze auf Standardwerte zurück
    default_rewards = {
        CreditEventType.QUOTE_ACCEPTED: 5,
        CreditEventType.INSPECTION_QUOTE_ACCEPTED: 15,
        CreditEventType.PROJECT_COMPLETED: 10,
        CreditEventType.DOCUMENT_UPLOADED: 1,
    }
    
    for action, reward in default_rewards.items():
        credit_config.update_credit_reward(action, reward)
        print(f"  {action.value}: zurückgesetzt auf {reward} Credits")
    
    print()


def main():
    """Hauptfunktion für alle Beispiele"""
    
    print("BuildWise Credit-Konfigurationssystem - Praktische Beispiele")
    print("=" * 60)
    print()
    
    try:
        # Führe alle Beispiele aus
        beispiel_1_credit_belohnungen_anpassen()
        beispiel_2_feature_flags_verwaltung()
        beispiel_3_system_parameter_anpassen()
        beispiel_4_anti_spam_limits()
        beispiel_5_konfiguration_exportieren()
        beispiel_6_saisonale_anpassungen()
        
        print("=" * 60)
        print("Alle Beispiele erfolgreich ausgeführt!")
        print()
        print("Die neue Credit-Konfiguration bietet folgende Vorteile:")
        print("- Flexible Anpassung von Credit-Belohnungen")
        print("- Einfache Aktivierung/Deaktivierung von Features")
        print("- Konfigurierbare System-Parameter")
        print("- Anti-Spam-Schutz mit anpassbaren Limits")
        print("- Saisonale Kampagnen und A/B-Testing")
        print("- Zentrale Verwaltung über API")
        
    except Exception as e:
        print(f"Fehler beim Ausführen der Beispiele: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
