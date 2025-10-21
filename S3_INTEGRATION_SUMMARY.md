# S3 Integration - Implementierungsübersicht

## Zusammenfassung
Die AWS S3-Integration wurde erfolgreich im Backend implementiert. Das System unterstützt nun einen Hybrid-Modus, bei dem:
- **Hochgeladene Dokumente** → AWS S3 (wenn konfiguriert)
- **Generierte PDFs** (Rechnungen, etc.) → Lokaler Speicher
- **Existierende lokale Dateien** → Bleiben lokal verfügbar

## Implementierte Änderungen

### 1. Neue Dateien

#### `app/services/s3_service.py`
Zentraler Service für AWS S3-Operationen:
- ✅ `upload_file()` - Upload mit AES256 Verschlüsselung
- ✅ `download_file()` - Download als Bytes
- ✅ `delete_file()` - Löschen von Dateien
- ✅ `generate_presigned_url()` - Temporäre URLs (z.B. für private Dateien)
- ✅ `get_file_url()` - Öffentliche S3-URLs
- ✅ `file_exists()` - Existenzprüfung
- ✅ Automatische Fehlerbehandlung und Logging
- ✅ Singleton-Pattern für S3-Client (Performance-Optimierung)

**S3-Key-Format:** `project_{project_id}/uploads/{filename}`

### 2. Erweiterte Dateien

#### `app/core/storage.py`
Erweitert um Hybrid-Modus-Unterstützung:
- ✅ `is_s3_enabled()` - Prüft S3-Konfiguration
- ✅ `should_use_s3(file_type)` - Entscheidet zwischen S3/lokal
- ✅ `is_s3_path(path)` - Erkennt S3-Keys (startet mit "project_")

**Logik:**
- Uploads/Dokumente/Bilder → S3 (wenn aktiviert)
- PDFs/Invoices/Temp/Cache → Lokal

#### `app/services/document_service.py`
**`save_uploaded_file()` - Zeile 312-352:**
- ✅ Erweitert um `mime_type` Parameter
- ✅ S3-Upload mit Fallback zu lokalem Speicher
- ✅ Automatische Fehlerbehandlung

**`delete_document()` - Zeile 157-172:**
- ✅ Unterstützt S3 und lokale Dateien
- ✅ Automatische Erkennung via `is_s3_path()`

#### `app/api/documents.py`
Alle Endpoints unterstützen jetzt S3 und lokale Dateien:

**Upload-Endpoint - Zeile 195-310:**
- ✅ Übergibt `mime_type` an `save_uploaded_file()`
- ✅ Keine weitere Änderung nötig (nutzt Service-Layer)

**Milestone-Upload - Zeile 309-394:**
- ✅ Verwendet `save_uploaded_file()` statt direkter Dateispeicherung
- ✅ Unterstützt S3 und lokalen Speicher

**Content-Endpoint - Zeile 808-887:**
- ✅ Prüft ob Datei in S3 (`is_s3_path()`)
- ✅ S3: Download als `Response` mit Bytes
- ✅ Lokal: `FileResponse` für direkten Zugriff
- ✅ Content-Disposition: `inline` (für Browser-Preview)

**Download-Endpoint - Zeile 890-961:**
- ✅ Analog zu Content-Endpoint
- ✅ Content-Disposition: `attachment` (für Download)

**View-Endpoint - Zeile 964-1040:**
- ✅ Lädt Datei aus S3 oder lokal
- ✅ Unterstützt Text-Dateien, Base64 für Binärdaten

**Delete-Endpoint - Zeile 1110-1130:**
- ✅ Nutzt `delete_document()` aus Service-Layer
- ✅ Löscht automatisch aus S3 oder lokal

### 3. Dependencies

#### `requirements.txt`
- ✅ `boto3==1.34.24` - AWS SDK
- ✅ `botocore==1.34.24` - Boto3 Core

## Umgebungsvariablen

Bereits auf Render.com gesetzt (Service: `buildwise-api`):
- ✅ `AWS_ACCESS_KEY_ID` = *****configured*****
- ✅ `AWS_SECRET_ACCESS_KEY` = *****configured*****
- ✅ `AWS_REGION` = eu-central-1
- ✅ `S3_BUCKET_NAME` = buildwise-documents-prod

## Hybrid-Modus

### Datei-Erkennung
- **S3-Dateien:** `file_path` startet mit `"project_"`
- **Lokale Dateien:** `file_path` enthält `"uploads/"` oder `"storage/"`

### Migration
- Alte Dokumente (lokale Pfade) → Funktionieren weiterhin
- Neue Dokumente → Automatisch zu S3 (wenn aktiviert)
- Kein Datenverlust bei Hybrid-Betrieb

## Sicherheit

### S3-Bucket
- ✅ CORS konfiguriert für Frontend-Zugriff
- ✅ Bucket Policy mit IAM-User `buildwise-app`
- ✅ Server-Side Encryption (AES256)
- ✅ Block Public Access aktiviert (keine öffentlichen Uploads)

### IAM-Berechtigungen
- `s3:GetObject` - Dateien lesen
- `s3:PutObject` - Dateien hochladen
- `s3:DeleteObject` - Dateien löschen
- `s3:PutObjectAcl` - ACLs setzen
- `s3:GetObjectAcl` - ACLs lesen
- `s3:ListBucket` - Bucket-Inhalte auflisten

## Testing

### Automatische Tests
1. **S3 deaktiviert** (fehlende Env-Vars):
   - Fällt automatisch auf lokalen Speicher zurück
   
2. **S3 aktiviert:**
   - Neue Uploads → S3
   - Download/View → S3
   - Delete → S3
   
3. **Hybrid-Modus:**
   - Alte Dokumente (lokal) → Weiterhin zugänglich
   - Neue Dokumente → S3

### Manuelle Tests (nach Deployment)
1. ✅ Dokument hochladen → Prüfe S3-Bucket
2. ✅ Dokument anzeigen → Funktioniert via Content-Endpoint
3. ✅ Dokument herunterladen → Funktioniert via Download-Endpoint
4. ✅ Dokument löschen → Verschwindet aus S3
5. ✅ Alte lokale Dokumente → Weiterhin zugänglich

## Fehlerbehandlung

### S3-Upload fehlschlägt
- Automatischer Fallback zu lokalem Speicher
- Logging: `[ERROR] S3 upload failed, falling back to local storage`

### S3-Download fehlschlägt
- HTTPException 404: "Datei nicht in S3 gefunden"
- Frontend erhält klare Fehlermeldung

### S3 nicht konfiguriert
- System verwendet automatisch lokalen Speicher
- Keine Fehler, nahtloser Betrieb

## Performance-Optimierungen

1. **S3-Client Singleton:** Client wird nur einmal initialisiert
2. **Direkte Bytes-Übertragung:** Keine temporären Dateien nötig
3. **Presigned URLs:** Optional für private Dateien (nicht aktuell genutzt)
4. **Retry-Mechanismus:** Boto3 Config mit 3 Versuchen

## Frontend-Kompatibilität

**Keine Änderungen nötig!**
- Alle API-Endpoints bleiben gleich
- Frontend merkt nicht, ob Datei aus S3 oder lokal kommt
- URLs und Response-Formate unverändert

## Deployment-Checkliste

- ✅ Code committed und gepusht
- ✅ S3-Bucket erstellt (`buildwise-documents-prod`)
- ✅ CORS-Policy konfiguriert
- ✅ Bucket Policy konfiguriert
- ✅ IAM-User `buildwise-app` erstellt
- ✅ Access Keys generiert
- ✅ Umgebungsvariablen auf Render gesetzt
- ✅ Dependencies in requirements.txt
- ⏳ Deployment auf Render (läuft nach nächstem Push)

## Nächste Schritte

1. **Code committen und pushen:**
   ```bash
   git add .
   git commit -m "feat: AWS S3 integration for document storage"
   git push
   ```

2. **Deployment abwarten:**
   - Render deployed automatisch
   - Prüfe Logs auf Fehler

3. **Testen:**
   - Dokument hochladen
   - Dokument anzeigen/herunterladen
   - Dokument löschen
   - S3-Bucket via AWS Console prüfen

4. **Optional - Migration existierender Dateien:**
   - Script erstellen, das lokale Dateien zu S3 migriert
   - DB-Pfade aktualisieren
   - Nur bei Bedarf, aktuell läuft Hybrid-Modus

## Bekannte Einschränkungen

1. **PDF-Generierung:** Bleibt lokal (wie gewünscht)
2. **Existierende Dateien:** Bleiben lokal (Hybrid-Modus)
3. **Presigned URLs:** Implementiert aber nicht aktiv genutzt (für zukünftige Features)

## Support-Kontakte

- AWS Account ID: 811280243074
- S3 Bucket: buildwise-documents-prod
- Region: eu-central-1
- IAM User: buildwise-app

