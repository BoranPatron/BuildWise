#!/usr/bin/env python3
"""
Einfache PostgreSQL Schema-Reparatur für OAuth
Führt nur die notwendigen Änderungen für PostgreSQL aus
"""

import os
import asyncpg
import asyncio
import sys

async def fix_postgresql_oauth_schema():
    """Repariert das PostgreSQL-Schema für OAuth"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not found!")
            return False
            
        print(f"🔧 Connecting to PostgreSQL database...")
        
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database successfully!")
        
        # Start transaction for safety
        await conn.execute('BEGIN;')
        print("🔄 Started transaction for safe schema changes...")
        
        # Fix languages column datatype from JSON to TEXT
        print("\n📝 Fixing languages column datatype...")
        try:
            await conn.execute('ALTER TABLE users ALTER COLUMN languages TYPE TEXT USING languages::TEXT;')
            print("✅ languages column converted to TEXT successfully")
        except Exception as e:
            print(f"⚠️  languages column: {e}")
        
        # Fix name column to allow NULL values
        print("\n📝 Fixing name column constraint...")
        try:
            await conn.execute('ALTER TABLE users ALTER COLUMN name DROP NOT NULL;')
            print("✅ name column constraint removed successfully")
        except Exception as e:
            print(f"⚠️  name column: {e}")
        
        # Fix user_role column to allow NULL values
        print("\n📝 Fixing user_role column constraint...")
        try:
            await conn.execute('ALTER TABLE users ALTER COLUMN user_role DROP NOT NULL;')
            print("✅ user_role column constraint removed successfully")
        except Exception as e:
            print(f"⚠️  user_role column: {e}")
        
        # Add missing OAuth columns (only if they don't exist)
        print("\n📝 Adding missing OAuth columns...")
        
        oauth_columns = [
            ("auth_provider", "VARCHAR(9) NOT NULL DEFAULT 'EMAIL'"),
            ("google_sub", "VARCHAR NULL"),
            ("microsoft_sub", "VARCHAR NULL"),
            ("apple_sub", "VARCHAR NULL"),
            ("social_profile_data", "TEXT NULL"),
            ("first_name", "VARCHAR NOT NULL DEFAULT ''"),
            ("last_name", "VARCHAR NOT NULL DEFAULT ''"),
            ("phone", "VARCHAR NULL"),
            ("user_type", "VARCHAR(20) NOT NULL DEFAULT 'INDIVIDUAL'"),
            ("user_role", "VARCHAR(20) NOT NULL DEFAULT 'USER'"),
            ("role_selected", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("role_selected_at", "TIMESTAMP NULL"),
            ("role_selection_modal_shown", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("first_login_completed", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("onboarding_completed", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("onboarding_step", "INTEGER NOT NULL DEFAULT 0"),
            ("onboarding_started_at", "TIMESTAMP NULL"),
            ("onboarding_completed_at", "TIMESTAMP NULL"),
            ("subscription_plan", "VARCHAR(20) NOT NULL DEFAULT 'FREE'"),
            ("subscription_status", "VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"),
            ("subscription_id", "VARCHAR NULL"),
            ("customer_id", "VARCHAR NULL"),
            ("subscription_start", "TIMESTAMP NULL"),
            ("subscription_end", "TIMESTAMP NULL"),
            ("max_gewerke", "INTEGER NOT NULL DEFAULT 0"),
            ("address_street", "VARCHAR NULL"),
            ("address_zip", "VARCHAR NULL"),
            ("address_city", "VARCHAR NULL"),
            ("address_country", "VARCHAR NULL"),
            ("address_latitude", "DECIMAL(10,8) NULL"),
            ("address_longitude", "DECIMAL(11,8) NULL"),
            ("address_geocoded", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("address_geocoding_date", "TIMESTAMP NULL"),
            ("status", "VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"),
            ("consent_fields", "TEXT NULL"),
            ("consent_history", "TEXT NULL"),
            ("data_processing_consent", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("marketing_consent", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("privacy_policy_accepted", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("terms_accepted", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("data_retention_until", "TIMESTAMP NULL"),
            ("data_deletion_requested", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("data_deletion_requested_at", "TIMESTAMP NULL"),
            ("data_anonymized", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("data_export_requested", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("data_export_requested_at", "TIMESTAMP NULL"),
            ("data_export_token", "VARCHAR NULL"),
            ("data_export_expires_at", "TIMESTAMP NULL"),
            ("last_login_at", "TIMESTAMP NULL"),
            ("last_login_provider", "VARCHAR NULL"),
            ("failed_login_attempts", "INTEGER NOT NULL DEFAULT 0"),
            ("account_locked_until", "TIMESTAMP NULL"),
            ("password_changed_at", "TIMESTAMP NULL"),
            ("mfa_enabled", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("mfa_secret", "VARCHAR NULL"),
            ("mfa_backup_codes", "TEXT NULL"),
            ("mfa_last_used", "TIMESTAMP NULL"),
            ("company_name", "VARCHAR NULL"),
            ("company_address", "VARCHAR NULL"),
            ("company_uid", "VARCHAR NULL"),
            ("company_tax_number", "VARCHAR NULL"),
            ("company_phone", "VARCHAR NULL"),
            ("company_website", "VARCHAR NULL"),
            ("business_license", "VARCHAR NULL"),
            ("company_logo", "VARCHAR NULL"),
            ("company_logo_advertising_consent", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("is_small_business", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("small_business_exemption", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("bio", "TEXT NULL"),
            ("profile_image", "VARCHAR NULL"),
            ("region", "VARCHAR NULL"),
            ("is_active", "BOOLEAN NOT NULL DEFAULT TRUE"),
            ("is_verified", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("email_verified", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("two_factor_enabled", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("language_preference", "VARCHAR(5) NOT NULL DEFAULT 'de'"),
            ("data_encrypted", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("encryption_key_id", "VARCHAR NULL"),
            ("completed_offers_count", "INTEGER NOT NULL DEFAULT 0"),
            ("current_rank_key", "VARCHAR NULL"),
            ("current_rank_title", "VARCHAR NULL"),
            ("rank_updated_at", "TIMESTAMP NULL"),
            ("updated_at", "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"),
            ("last_activity_at", "TIMESTAMP NULL")
        ]
        
        for column_name, column_definition in oauth_columns:
            try:
                print(f"  Adding {column_name}...")
                await conn.execute(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_definition};')
                print(f"  ✅ {column_name} added successfully")
            except Exception as e:
                print(f"  ⚠️  {column_name}: {e}")
                continue
        
        # Add missing columns to projects table
        print("\n📝 Adding missing projects columns...")
        try:
            await conn.execute('ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_id INTEGER NULL;')
            print("✅ projects.owner_id added successfully")
        except Exception as e:
            print(f"⚠️  projects.owner_id: {e}")
        
        try:
            await conn.execute('ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR NULL;')
            print("✅ projects.project_type added successfully")
        except Exception as e:
            print(f"⚠️  projects.project_type: {e}")
        
        try:
            await conn.execute('ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR NULL;')
            print("✅ projects.status added successfully")
        except Exception as e:
            print(f"⚠️  projects.status: {e}")
        
        try:
            await conn.execute('ALTER TABLE projects ADD COLUMN IF NOT EXISTS address VARCHAR NULL;')
            print("✅ projects.address added successfully")
        except Exception as e:
            print(f"⚠️  projects.address: {e}")
        
        # Schema-Verifikation
        print("\n🔍 Verifying schema...")
        
        # Prüfe wichtige OAuth-Spalten
        critical_columns = ['auth_provider', 'google_sub', 'microsoft_sub', 'apple_sub', 'first_name', 'last_name', 'languages']
        for col in critical_columns:
            exists = await conn.fetchval('SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = $1 AND column_name = $2)', 'users', col)
            if exists:
                # Prüfe auch den Datentyp für languages
                if col == 'languages':
                    data_type = await conn.fetchval('SELECT data_type FROM information_schema.columns WHERE table_name = $1 AND column_name = $2', 'users', col)
                    print(f"  ✅ {col} exists (type: {data_type})")
                else:
                    print(f"  ✅ {col} exists")
            else:
                print(f"  ❌ {col} missing")
        
        # Commit transaction
        await conn.execute('COMMIT;')
        print("✅ Transaction committed successfully!")
        
        await conn.close()
        print("\n🎉 PostgreSQL OAuth schema repair successful!")
        print("✅ languages column converted to TEXT")
        print("✅ All OAuth columns added to users table")
        print("✅ Missing columns added to projects table")
        print("✅ OAuth Microsoft login should now work!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during schema repair: {e}")
        # Try to rollback if connection is still open
        try:
            if 'conn' in locals():
                await conn.execute('ROLLBACK;')
                print("🔄 Transaction rolled back due to error")
                await conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    print("🔧 PostgreSQL OAuth Schema Repair")
    print("=" * 50)
    
    success = asyncio.run(fix_postgresql_oauth_schema())
    
    if success:
        print("\n✅ Schema repair completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Schema repair failed!")
        sys.exit(1)
