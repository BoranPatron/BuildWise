import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import os
from pathlib import Path

from ..core.config import get_settings


class EmailService:
    """E-Mail-Service für BuildWise mit SMTP-Integration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@buildwise.de")
        self.from_name = os.getenv("FROM_NAME", "BuildWise")
        
    def _create_message(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> MIMEMultipart:
        """Erstellt eine E-Mail-Nachricht"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email
        
        # HTML-Version
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Text-Version (falls angegeben)
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)
        
        return message
    
    def _send_email(self, message: MIMEMultipart) -> bool:
        """Sendet eine E-Mail über SMTP"""
        try:
            # Erstelle SMTP-Verbindung
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                # Sende E-Mail
                server.send_message(message)
            
            return True
        except Exception as e:
            print(f"❌ E-Mail-Sendefehler: {e}")
            return False
    
    def send_verification_email(self, to_email: str, verification_token: str, user_name: str) -> bool:
        """Sendet E-Mail-Verifizierung"""
        subject = "E-Mail-Adresse verifizieren - BuildWise"
        
        # Verifizierungs-URL
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"
        
        # HTML-Inhalt
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>E-Mail verifizieren - BuildWise</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BuildWise</h1>
                    <p>E-Mail-Adresse verifizieren</p>
                </div>
                <div class="content">
                    <h2>Hallo {user_name},</h2>
                    <p>vielen Dank für Ihre Registrierung bei BuildWise! Um Ihr Konto zu aktivieren, müssen Sie Ihre E-Mail-Adresse verifizieren.</p>
                    
                    <p>Klicken Sie auf den folgenden Button, um Ihre E-Mail-Adresse zu verifizieren:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">E-Mail verifizieren</a>
                    </div>
                    
                    <p>Falls der Button nicht funktioniert, kopieren Sie diese URL in Ihren Browser:</p>
                    <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px;">
                        {verification_url}
                    </p>
                    
                    <p><strong>Wichtig:</strong> Dieser Link ist 24 Stunden gültig.</p>
                    
                    <p>Falls Sie sich nicht bei BuildWise registriert haben, können Sie diese E-Mail ignorieren.</p>
                </div>
                <div class="footer">
                    <p>© 2024 BuildWise. Alle Rechte vorbehalten.</p>
                    <p>Diese E-Mail wurde automatisch generiert. Bitte nicht antworten.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text-Inhalt
        text_content = f"""
        E-Mail verifizieren - BuildWise
        
        Hallo {user_name},
        
        vielen Dank für Ihre Registrierung bei BuildWise! Um Ihr Konto zu aktivieren, müssen Sie Ihre E-Mail-Adresse verifizieren.
        
        Klicken Sie auf den folgenden Link, um Ihre E-Mail-Adresse zu verifizieren:
        {verification_url}
        
        Wichtig: Dieser Link ist 24 Stunden gültig.
        
        Falls Sie sich nicht bei BuildWise registriert haben, können Sie diese E-Mail ignorieren.
        
        © 2024 BuildWise. Alle Rechte vorbehalten.
        """
        
        message = self._create_message(to_email, subject, html_content, text_content)
        return self._send_email(message)
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Sendet Passwort-Reset E-Mail"""
        subject = "Passwort zurücksetzen - BuildWise"
        
        # Reset-URL
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        # HTML-Inhalt
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Passwort zurücksetzen - BuildWise</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #dc2626; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
                .warning {{ background-color: #fef2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BuildWise</h1>
                    <p>Passwort zurücksetzen</p>
                </div>
                <div class="content">
                    <h2>Hallo {user_name},</h2>
                    <p>Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.</p>
                    
                    <p>Klicken Sie auf den folgenden Button, um ein neues Passwort zu setzen:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Passwort zurücksetzen</a>
                    </div>
                    
                    <p>Falls der Button nicht funktioniert, kopieren Sie diese URL in Ihren Browser:</p>
                    <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px;">
                        {reset_url}
                    </p>
                    
                    <div class="warning">
                        <p><strong>⚠️ Sicherheitshinweis:</strong></p>
                        <ul>
                            <li>Dieser Link ist nur 1 Stunde gültig</li>
                            <li>Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail</li>
                            <li>Ihr aktuelles Passwort bleibt unverändert, bis Sie es ändern</li>
                        </ul>
                    </div>
                    
                    <p>Falls Sie diese Anfrage nicht gestellt haben, können Sie diese E-Mail sicher ignorieren.</p>
                </div>
                <div class="footer">
                    <p>© 2024 BuildWise. Alle Rechte vorbehalten.</p>
                    <p>Diese E-Mail wurde automatisch generiert. Bitte nicht antworten.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text-Inhalt
        text_content = f"""
        Passwort zurücksetzen - BuildWise
        
        Hallo {user_name},
        
        Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.
        
        Klicken Sie auf den folgenden Link, um ein neues Passwort zu setzen:
        {reset_url}
        
        ⚠️ Sicherheitshinweis:
        - Dieser Link ist nur 1 Stunde gültig
        - Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail
        - Ihr aktuelles Passwort bleibt unverändert, bis Sie es ändern
        
        Falls Sie diese Anfrage nicht gestellt haben, können Sie diese E-Mail sicher ignorieren.
        
        © 2024 BuildWise. Alle Rechte vorbehalten.
        """
        
        message = self._create_message(to_email, subject, html_content, text_content)
        return self._send_email(message)
    
    def send_welcome_email(self, to_email: str, user_name: str, user_type: str) -> bool:
        """Sendet Willkommens-E-Mail"""
        subject = "Willkommen bei BuildWise!"
        
        # HTML-Inhalt
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Willkommen bei BuildWise</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #059669; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #059669; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BuildWise</h1>
                    <p>Willkommen!</p>
                </div>
                <div class="content">
                    <h2>Hallo {user_name},</h2>
                    <p>herzlich willkommen bei BuildWise! 🎉</p>
                    
                    <p>Ihr Konto wurde erfolgreich erstellt und verifiziert. Sie können sich jetzt bei BuildWise anmelden und alle Funktionen nutzen.</p>
                    
                    <div style="text-align: center;">
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login" class="button">Jetzt anmelden</a>
                    </div>
                    
                    <h3>Was Sie als {user_type} erwartet:</h3>
                    <ul>
                        <li>Projektmanagement und -verwaltung</li>
                        <li>Kommunikation mit Dienstleistern</li>
                        <li>Dokumentenverwaltung</li>
                        <li>Und vieles mehr...</li>
                    </ul>
                    
                    <p>Falls Sie Fragen haben, stehen wir Ihnen gerne zur Verfügung.</p>
                    
                    <p>Viel Erfolg mit Ihren Projekten!</p>
                    <p>Ihr BuildWise-Team</p>
                </div>
                <div class="footer">
                    <p>© 2024 BuildWise. Alle Rechte vorbehalten.</p>
                    <p>Diese E-Mail wurde automatisch generiert. Bitte nicht antworten.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text-Inhalt
        text_content = f"""
        Willkommen bei BuildWise!
        
        Hallo {user_name},
        
        herzlich willkommen bei BuildWise! 🎉
        
        Ihr Konto wurde erfolgreich erstellt und verifiziert. Sie können sich jetzt bei BuildWise anmelden und alle Funktionen nutzen.
        
        Was Sie als {user_type} erwartet:
        - Projektmanagement und -verwaltung
        - Kommunikation mit Dienstleistern
        - Dokumentenverwaltung
        - Und vieles mehr...
        
        Falls Sie Fragen haben, stehen wir Ihnen gerne zur Verfügung.
        
        Viel Erfolg mit Ihren Projekten!
        Ihr BuildWise-Team
        
        © 2024 BuildWise. Alle Rechte vorbehalten.
        """
        
        message = self._create_message(to_email, subject, html_content, text_content)
        return self._send_email(message)
    
    def send_account_deletion_email(self, to_email: str, user_name: str) -> bool:
        """Sendet Bestätigungs-E-Mail für Kontolöschung"""
        subject = "Ihr BuildWise-Konto wurde gelöscht"
        
        # HTML-Inhalt
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Konto gelöscht - BuildWise</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #6b7280; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BuildWise</h1>
                    <p>Konto gelöscht</p>
                </div>
                <div class="content">
                    <h2>Hallo {user_name},</h2>
                    <p>Ihr BuildWise-Konto wurde erfolgreich gelöscht.</p>
                    
                    <p>Alle Ihre Daten wurden entsprechend der DSGVO-Anforderungen aus unserem System entfernt.</p>
                    
                    <p>Falls Sie sich entschieden haben, BuildWise wieder zu nutzen, können Sie sich jederzeit neu registrieren.</p>
                    
                    <p>Vielen Dank für die Nutzung von BuildWise!</p>
                </div>
                <div class="footer">
                    <p>© 2024 BuildWise. Alle Rechte vorbehalten.</p>
                    <p>Diese E-Mail wurde automatisch generiert. Bitte nicht antworten.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text-Inhalt
        text_content = f"""
        Konto gelöscht - BuildWise
        
        Hallo {user_name},
        
        Ihr BuildWise-Konto wurde erfolgreich gelöscht.
        
        Alle Ihre Daten wurden entsprechend der DSGVO-Anforderungen aus unserem System entfernt.
        
        Falls Sie sich entschieden haben, BuildWise wieder zu nutzen, können Sie sich jederzeit neu registrieren.
        
        Vielen Dank für die Nutzung von BuildWise!
        
        © 2024 BuildWise. Alle Rechte vorbehalten.
        """
        
        message = self._create_message(to_email, subject, html_content, text_content)
        return self._send_email(message)


# Globale Instanz
email_service = EmailService() 