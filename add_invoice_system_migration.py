#!/usr/bin/env python3
"""
Migration script to add invoice system tables and relationships
"""

import sqlite3
import sys
from datetime import datetime

def create_invoice_tables():
    """Create invoice system tables"""
    
    # Connect to database
    conn = sqlite3.connect('buildwise.db')
    cursor = conn.cursor()
    
    try:
        print("🔧 Creating invoice system tables...")
        
        # Create invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                milestone_id INTEGER NOT NULL,
                service_provider_id INTEGER NOT NULL,
                invoice_number VARCHAR(100) NOT NULL UNIQUE,
                invoice_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                due_date DATETIME NOT NULL,
                net_amount REAL NOT NULL DEFAULT 0.0,
                vat_rate REAL NOT NULL DEFAULT 19.0,
                vat_amount REAL NOT NULL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                material_costs REAL DEFAULT 0.0,
                labor_costs REAL DEFAULT 0.0,
                additional_costs REAL DEFAULT 0.0,
                description TEXT,
                work_period_from DATETIME,
                work_period_to DATETIME,
                status VARCHAR(20) NOT NULL DEFAULT 'draft',
                type VARCHAR(20) NOT NULL,
                pdf_file_path VARCHAR(500),
                pdf_file_name VARCHAR(255),
                notes TEXT,
                paid_at DATETIME,
                payment_reference VARCHAR(255),
                rating_quality INTEGER,
                rating_timeliness INTEGER,
                rating_overall INTEGER,
                rating_notes TEXT,
                rated_by INTEGER,
                rated_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                FOREIGN KEY (milestone_id) REFERENCES milestones (id) ON DELETE CASCADE,
                FOREIGN KEY (service_provider_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (rated_by) REFERENCES users (id) ON DELETE SET NULL
            )
        ''')
        print("✅ Created invoices table")
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_invoices_project_id ON invoices(project_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_invoices_milestone_id ON invoices(milestone_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_invoices_service_provider_id ON invoices(service_provider_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON invoices(invoice_number)
        ''')
        print("✅ Created invoice indexes")
        
        # Create storage directory for invoices
        import os
        os.makedirs('storage/invoices', exist_ok=True)
        print("✅ Created storage/invoices directory")
        
        # Commit changes
        conn.commit()
        print("✅ Invoice system migration completed successfully!")
        
        # Test the tables
        cursor.execute("SELECT COUNT(*) FROM invoices")
        count = cursor.fetchone()[0]
        print(f"📊 Invoices table created with {count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    """Main migration function"""
    print("🚀 Starting invoice system migration...")
    print("=" * 50)
    
    success = create_invoice_tables()
    
    print("=" * 50)
    if success:
        print("✅ Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your application to include invoice functionality")
        print("2. Test invoice creation and PDF upload")
        print("3. Configure payment processing")
        print("4. Set up invoice notifications")
        return 0
    else:
        print("❌ Migration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())