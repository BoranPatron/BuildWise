-- Füge Passwort-Reset-Felder zur users-Tabelle hinzu
-- Führe diese Befehle in der SQLite-Datenbank aus

-- Prüfe ob Felder bereits existieren
SELECT name FROM pragma_table_info('users') WHERE name IN ('password_reset_token', 'password_reset_sent_at', 'password_reset_expires_at');

-- Füge Felder hinzu (falls sie nicht existieren)
ALTER TABLE users ADD COLUMN password_reset_token VARCHAR;
ALTER TABLE users ADD COLUMN password_reset_sent_at DATETIME;
ALTER TABLE users ADD COLUMN password_reset_expires_at DATETIME;

-- Zeige aktualisierte Tabellenstruktur
SELECT name, type FROM pragma_table_info('users') ORDER BY cid; 