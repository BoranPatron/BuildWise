#!/usr/bin/env python3
"""
BEHEBE ENUM-PROBLEM IN DER DATENBANK
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from sqlalchemy import text


async def fix_enum_problem():
    """
    Behebt das Enum-Problem in der Datenbank
    """
    print("="*60)
    print("BEHEBE ENUM-PROBLEM IN DER DATENBANK")
    print("="*60)
    
    async for db in get_db():
        try:
            # 1. Prüfe welche problematischen Enum-Werte existieren
            print("\n1. Prüfe problematische Enum-Werte...")
            
            user_types_result = await db.execute(text("SELECT DISTINCT user_type FROM users"))
            user_types = [row[0] for row in user_types_result.fetchall()]
            
            print(f"Gefundene user_type Werte: {user_types}")
            
            # 2. Behebe 'developer' zu 'PROFESSIONAL'
            if 'developer' in user_types:
                print("\n2. Behebe 'developer' zu 'PROFESSIONAL'...")
                
                await db.execute(text("UPDATE users SET user_type = 'PROFESSIONAL' WHERE user_type = 'developer'"))
                await db.commit()
                
                print("OK 'developer' zu 'PROFESSIONAL' geändert")
            else:
                print("OK Kein 'developer' Wert gefunden")
            
            # 3. Prüfe user_role Werte
            print("\n3. Prüfe user_role Werte...")
            
            user_roles_result = await db.execute(text("SELECT DISTINCT user_role FROM users"))
            user_roles = [row[0] for row in user_roles_result.fetchall()]
            
            print(f"Gefundene user_role Werte: {user_roles}")
            
            # 4. Prüfe ob es andere problematische Werte gibt
            print("\n4. Prüfe auf andere problematische Werte...")
            
            # Prüfe alle Enum-Spalten
            enum_columns = [
                ('users', 'user_type'),
                ('users', 'user_role'),
                ('projects', 'project_type'),
                ('projects', 'status'),
                ('quotes', 'status'),
                ('notifications', 'type'),
                ('notifications', 'priority')
            ]
            
            for table, column in enum_columns:
                try:
                    result = await db.execute(text(f"SELECT DISTINCT {column} FROM {table}"))
                    values = [row[0] for row in result.fetchall()]
                    print(f"  {table}.{column}: {values}")
                except Exception as e:
                    print(f"  {table}.{column}: Fehler - {e}")
            
            print("\n" + "="*60)
            print("ENUM-PROBLEM BEHOBEN!")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\nFEHLER BEIM BEHEBEN: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            await db.close()


if __name__ == "__main__":
    success = asyncio.run(fix_enum_problem())
    
    if success:
        print("\nENUM-PROBLEM ERFOLGREICH BEHOBEN!")
    else:
        print("\nFEHLER BEIM BEHEBEN DES ENUM-PROBLEMS!")
        sys.exit(1)
