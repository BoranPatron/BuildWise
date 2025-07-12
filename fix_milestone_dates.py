import sqlite3
import re

def fix_dates():
    db_path = "buildwise.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    date_fields = ["planned_date", "actual_date", "start_date", "end_date"]
    cursor.execute("SELECT id, planned_date, actual_date, start_date, end_date FROM milestones")
    rows = cursor.fetchall()

    iso_regex = re.compile(r"^(\d{4}-\d{2}-\d{2})[T ]")

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
        if updates_needed:
            set_clause = ", ".join([f"{field} = ?" for field in updates_needed])
            params = list(updates_needed.values()) + [id]
            cursor.execute(f"UPDATE milestones SET {set_clause} WHERE id = ?", params)
            updates += 1

    conn.commit()
    conn.close()
    print(f"✅ {updates} Milestones korrigiert.")

if __name__ == "__main__":
    fix_dates() 