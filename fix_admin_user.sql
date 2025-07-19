-- Fix Admin User Script
-- Führt alle notwendigen Updates für den Admin-User durch

-- Aktualisiere Admin-User mit allen erforderlichen Feldern
UPDATE users 
SET 
    email_verified = true,
    email_verified_at = CURRENT_TIMESTAMP,
    data_processing_consent = true,
    marketing_consent = true,
    privacy_policy_accepted = true,
    terms_accepted = true,
    subscription_active = true,
    subscription_plan = 'pro',
    status = 'active',
    is_active = true,
    is_verified = true,
    roles = '["admin"]',
    permissions = '{"*": true}',
    language_preference = 'de',
    updated_at = CURRENT_TIMESTAMP
WHERE email = 'admin@buildwise.de';

-- Zeige das Ergebnis
SELECT 
    id,
    email,
    first_name,
    last_name,
    email_verified,
    data_processing_consent,
    subscription_active,
    status,
    roles,
    permissions
FROM users 
WHERE email = 'admin@buildwise.de'; 