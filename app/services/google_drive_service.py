import os
from typing import Optional, Tuple


class GoogleDriveUnavailable(Exception):
    pass


class GoogleDriveService:
    """
    Minimaler Wrapper um Dateien in einen Google-Drive-Ordner zu laden.

    Unterstützt Service-Accounts über JSON (env GOOGLE_SERVICE_ACCOUNT_JSON)
    oder Pfad (env GOOGLE_SERVICE_ACCOUNT_FILE). Der Zielordner wird über
    env DRIVE_ROOT_FOLDER_ID gesetzt (Default: bereitgestellte Folder-ID).
    
    Fallback: Wenn keine gültigen Credentials vorhanden sind, wird eine
    GoogleDriveUnavailable-Exception geworfen – der aufrufende Code kann
    auf lokalen Storage ausweichen.
    """

    def __init__(self) -> None:
        self._client = None
        self._drive = None
        self.root_folder_id = os.getenv(
            "DRIVE_ROOT_FOLDER_ID",
            "1dgjIm0Jtl0cBIWCHBOK9yTUnq0J_tq1L",
        )

        # Lazy Init: erst beim ersten Upload initialisieren

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except Exception as exc:  # Bibliotheken fehlen
            raise GoogleDriveUnavailable(
                f"Google Drive Bibliotheken nicht verfügbar: {exc}"
            )

        scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
        ]

        credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

        credentials = None
        try:
            if credentials_json:
                import json

                info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    info, scopes=scopes
                )
            elif credentials_file and os.path.exists(credentials_file):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_file, scopes=scopes
                )
            else:
                raise GoogleDriveUnavailable(
                    "Keine Service-Account-Credentials gefunden (GOOGLE_SERVICE_ACCOUNT_JSON oder GOOGLE_SERVICE_ACCOUNT_FILE)."
                )
        except Exception as exc:
            raise GoogleDriveUnavailable(f"Ungültige Credentials: {exc}")

        try:
            self._drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
        except Exception as exc:
            raise GoogleDriveUnavailable(f"Konnte Google Drive Client nicht initialisieren: {exc}")

    def _ensure_or_create_child_folder(self, parent_id: str, name: str) -> str:
        files = (
            self._drive.files()
            .list(
                q=f"name = '{name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id, name)",
                pageSize=1,
            )
            .execute()
        )
        items = files.get("files", [])
        if items:
            return items[0]["id"]

        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = self._drive.files().create(body=file_metadata, fields="id").execute()
        return folder["id"]

    def upload_bytes(
        self,
        *,
        data: bytes,
        filename: str,
        project_id: int,
        category: str,
        mimetype: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Lädt die Datei nach: ROOT / project_<id> / <category> / filename
        Gibt (file_id, webViewLink) zurück.
        """
        self._ensure_client()

        # Unterordner sicherstellen
        project_folder = self._ensure_or_create_child_folder(self.root_folder_id, f"project_{project_id}")
        category_folder = self._ensure_or_create_child_folder(project_folder, category)

        from googleapiclient.http import MediaInMemoryUpload

        media = MediaInMemoryUpload(data, mimetype=mimetype or "application/octet-stream", resumable=False)
        metadata = {"name": filename, "parents": [category_folder]}
        created = (
            self._drive.files()
            .create(body=metadata, media_body=media, fields="id, webViewLink, webContentLink")
            .execute()
        )
        file_id = created.get("id")

        # Optional Link-Freigabe
        try:
            self._drive.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
            ).execute()
        except Exception:
            # Wenn Rechte bereits gesetzt sind, nicht blockieren
            pass

        details = self._drive.files().get(fileId=file_id, fields="webViewLink, webContentLink").execute()
        return file_id, details.get("webViewLink") or details.get("webContentLink") or ""





