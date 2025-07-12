#!/usr/bin/env python3
"""
Umfassendes Skript zur Korrektur aller Milestone-Probleme in der Datenbank.
Behebt Datumsformat, progress_percentage und Status-Werte nachhaltig.
"""

import sqlite3
import os
import re
from datetime import datetime

def fix_milestone_complete():
    """Behebt alle Milestone-Probleme nachhaltig"""
    
    db_path = "buildwise.db"
    if not os.path.exists(db_path):
        print(f"❌ Datenbank {db_path} nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Behebe alle Milestone-Probleme nachhaltig...")
    
    # 1. Prüfe aktuelle Probleme
    cursor.execute("SELECT id, planned_date, actual_date, start_date, end_date, status, progress_percentage FROM milestones")
    rows = cursor.fetchall()
    
    print(f"📋 Gefundene Milestones: {len(rows)}")
    
    # 2. Korrigiere Datumsfelder
    iso_regex = re.compile(r"^(\d{4}-\d{2}-\d{2})[T ]")
    date_fields = ["planned_date", "actual_date", "start_date", "end_date"]
    
    updates = 0
    for row in rows:
        id = row[0]
        updates_needed = {}
        
        for idx, field in enumerate(date_fields, start=1):
            value = row[idx]
            if value and isinstance(value, str):
                match = iso_regex.match(value)
                if match:
                    new_value = match.group(1)
                    updates_needed[field] = new_value
                    print(f"  🔧 Milestone {id}: {field} '{value}' → '{new_value}'")
        
        if updates_needed:
            set_clause = ", ".join([f"{field} = ?" for field in updates_needed.keys()])
            values = list(updates_needed.values()) + [id]
            cursor.execute(f"UPDATE milestones SET {set_clause} WHERE id = ?", values)
            updates += 1
    
    print(f"✅ {updates} Datumsfelder korrigiert")
    
    # 3. Korrigiere progress_percentage (NULL → 0)
    cursor.execute("UPDATE milestones SET progress_percentage = 0 WHERE progress_percentage IS NULL")
    null_progress_count = cursor.rowcount
    print(f"✅ {null_progress_count} progress_percentage-Werte auf 0 gesetzt")
    
    # 4. Korrigiere Status-Werte
    status_mapping = {
        'PLANNING': 'PLANNED',
        'planned': 'PLANNED',
        'in_progress': 'IN_PROGRESS',
        'completed': 'COMPLETED',
        'delayed': 'DELAYED',
        'cancelled': 'CANCELLED'
    }
    
    status_updates = 0
    for old_status, new_status in status_mapping.items():
        cursor.execute("UPDATE milestones SET status = ? WHERE status = ?", (new_status, old_status))
        if cursor.rowcount > 0:
            print(f"  🔧 Status '{old_status}' → '{new_status}': {cursor.rowcount} Milestones")
            status_updates += cursor.rowcount
    
    print(f"✅ {status_updates} Status-Werte korrigiert")
    
    # 5. Validiere alle Felder
    cursor.execute("""
        SELECT id, planned_date, actual_date, start_date, end_date, status, progress_percentage 
        FROM milestones 
        WHERE planned_date LIKE '%T%' 
           OR actual_date LIKE '%T%' 
           OR start_date LIKE '%T%' 
           OR end_date LIKE '%T%'
           OR progress_percentage IS NULL
    """)
    remaining_issues = cursor.fetchall()
    
    if remaining_issues:
        print(f"⚠️  {len(remaining_issues)} verbleibende Probleme gefunden")
        for issue in remaining_issues:
            print(f"  ⚠️  Milestone {issue[0]}: {issue[1:7]}")
    else:
        print("✅ Alle Probleme behoben!")
    
    # 6. Finale Validierung
    cursor.execute("SELECT COUNT(*) FROM milestones")
    total_milestones = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT status FROM milestones")
    current_statuses = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) FROM milestones WHERE progress_percentage IS NULL")
    null_progress = cursor.fetchone()[0]
    
    print(f"\n📊 Finale Validierung:")
    print(f"  • Gesamte Milestones: {total_milestones}")
    print(f"  • Aktuelle Status-Werte: {current_statuses}")
    print(f"  • NULL progress_percentage: {null_progress}")
    
    if null_progress == 0 and all(status in ['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', 'CANCELLED'] for status in current_statuses):
        print("✅ Alle Probleme nachhaltig behoben!")
    else:
        print("⚠️  Einige Probleme verbleiben")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Milestone-Korrektur abgeschlossen!")

if __name__ == "__main__":
    fix_milestone_complete() 