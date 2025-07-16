#!/usr/bin/env python3
"""
Skript zur Erstellung der BuildWise-Fees-Tabellen
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.models.buildwise_fee import Base

async def create_buildwise_fees_tables():
    """Erstelle die BuildWise-Fees-Tabellen"""
    async with engine.begin() as conn:
        # Erstelle buildwise_fees Tabelle
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS buildwise_fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                fee_month INTEGER NOT NULL,
                fee_year INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                fee_percentage REAL DEFAULT 1.0,
                invoice_number VARCHAR(50) UNIQUE,
                invoice_date DATETIME,
                due_date DATETIME,
                status VARCHAR(20) DEFAULT 'open',
                payment_date DATETIME,
                invoice_pdf_path VARCHAR(255),
                invoice_pdf_generated BOOLEAN DEFAULT FALSE,
                fee_details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """))
        
        # Erstelle buildwise_fee_items Tabelle
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS buildwise_fee_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buildwise_fee_id INTEGER NOT NULL,
                quote_id INTEGER NOT NULL,
                cost_position_id INTEGER,
                quote_amount REAL NOT NULL,
                fee_amount REAL NOT NULL,
                fee_percentage REAL DEFAULT 1.0,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buildwise_fee_id) REFERENCES buildwise_fees (id),
                FOREIGN KEY (quote_id) REFERENCES quotes (id),
                FOREIGN KEY (cost_position_id) REFERENCES cost_positions (id)
            )
        """))
        
        print("✅ BuildWise-Fees-Tabellen erfolgreich erstellt!")

if __name__ == "__main__":
    asyncio.run(create_buildwise_fees_tables()) 