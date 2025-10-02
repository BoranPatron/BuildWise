"""
Stripe Payment Service für BuildWise Gebühren
Verwaltet Payment Links und Zahlungsabwicklung über Stripe
"""

import stripe
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from app.core.config import settings

# Initialisiere Stripe mit dem Secret Key
stripe.api_key = settings.stripe_secret_key


class StripePaymentService:
    """Service-Klasse für Stripe-Zahlungsintegration"""
    
    @staticmethod
    def create_payment_link(
        fee_id: int,
        amount: Decimal,
        currency: str = "eur",
        description: str = "",
        invoice_number: str = "",
        fee_percentage: float = 4.7
    ) -> Dict[str, Any]:
        """
        Erstellt einen Stripe Payment Link für eine BuildWise-Gebühr.
        
        Args:
            fee_id: ID der BuildWise-Gebühr
            amount: Bruttobetrag in der kleinsten Währungseinheit (z.B. Cent)
            currency: Währungscode (Standard: EUR)
            description: Beschreibung der Zahlung
            invoice_number: Rechnungsnummer
            fee_percentage: Provisionssatz in Prozent
            
        Returns:
            Dict mit payment_link_id und payment_link_url
            
        Raises:
            stripe.error.StripeError: Bei Fehlern in der Stripe-API
        """
        
        try:
            # Konvertiere Betrag in kleinste Währungseinheit (Cent)
            # Stripe erwartet Beträge in Cent (z.B. 470 EUR = 47000 Cent)
            amount_in_cents = int(float(amount) * 100)
            
            print(f"[StripeService] Erstelle Payment Link für Gebühr {fee_id}")
            print(f"   - Betrag: {amount} {currency.upper()} ({amount_in_cents} Cent)")
            print(f"   - Rechnungsnummer: {invoice_number}")
            
            # Bestimme Zahlungsmethoden basierend auf Währung
            # SEPA funktioniert nur mit EUR, CHF benötigt nur Kreditkarte
            currency_lower = currency.lower()
            if currency_lower == "eur":
                payment_methods = ["card", "sepa_debit"]
                print(f"   - Zahlungsmethoden: Kreditkarte + SEPA (EUR)")
            elif currency_lower == "chf":
                payment_methods = ["card"]
                print(f"   - Zahlungsmethoden: Kreditkarte (CHF)")
            else:
                # Für andere Währungen nur Kreditkarte
                payment_methods = ["card"]
                print(f"   - Zahlungsmethoden: Kreditkarte ({currency.upper()})")
            
            # Erstelle Checkout Session (nicht Payment Link!)
            # Checkout Sessions unterstützen success_url besser als Payment Links
            checkout_session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": currency_lower,
                        "unit_amount": amount_in_cents,
                        "product_data": {
                            "name": f"BuildWise Vermittlungsgebühr - {invoice_number}",
                            "description": description or f"Provision für Auftrag ({fee_percentage}%)",
                        },
                    },
                    "quantity": 1,
                }],
                metadata={
                    "fee_id": str(fee_id),
                    "invoice_number": invoice_number,
                    "type": "buildwise_fee",
                    "created_at": datetime.utcnow().isoformat()
                },
                success_url=f"{settings.stripe_payment_success_url}&fee_id={fee_id}",
                cancel_url=f"{settings.stripe_payment_cancel_url}&fee_id={fee_id}",
                payment_method_types=payment_methods,  # Dynamisch basierend auf Währung
                billing_address_collection="auto",
                phone_number_collection={
                    "enabled": True
                },
                custom_text={
                    "submit": {
                        "message": "Vielen Dank für Ihre Zahlung über BuildWise!"
                    }
                },
                allow_promotion_codes=False,
            )
            
            print(f"[StripeService] Checkout Session erfolgreich erstellt:")
            print(f"   - Session ID: {checkout_session.id}")
            print(f"   - URL: {checkout_session.url}")
            print(f"   - Success URL: {checkout_session.success_url}")
            
            return {
                "payment_link_id": checkout_session.id,
                "payment_link_url": checkout_session.url,
                "amount": float(amount),
                "currency": currency.upper(),
                "status": "created"
            }
            
        except stripe.error.CardError as e:
            # Kartenfehler
            print(f"[StripeService] Kartenfehler: {e.error.message}")
            raise Exception(f"Kartenfehler: {e.error.message}")
            
        except stripe.error.RateLimitError as e:
            # Zu viele Anfragen
            print(f"[StripeService] Rate Limit Fehler: {str(e)}")
            raise Exception("Zu viele Anfragen. Bitte versuchen Sie es später erneut.")
            
        except stripe.error.InvalidRequestError as e:
            # Ungültige Parameter
            print(f"[StripeService] Ungültige Anfrage: {str(e)}")
            raise Exception(f"Ungültige Anfrage: {str(e)}")
            
        except stripe.error.AuthenticationError as e:
            # Authentifizierungsfehler
            print(f"[StripeService] Authentifizierungsfehler: {str(e)}")
            raise Exception("Stripe-Authentifizierung fehlgeschlagen")
            
        except stripe.error.APIConnectionError as e:
            # Netzwerkfehler
            print(f"[StripeService] Netzwerkfehler: {str(e)}")
            raise Exception("Verbindung zu Stripe fehlgeschlagen")
            
        except stripe.error.StripeError as e:
            # Allgemeiner Stripe-Fehler
            print(f"[StripeService] Stripe-Fehler: {str(e)}")
            raise Exception(f"Stripe-Fehler: {str(e)}")
            
        except Exception as e:
            # Unerwarteter Fehler
            print(f"[StripeService] Unerwarteter Fehler: {str(e)}")
            raise Exception(f"Fehler beim Erstellen des Payment Links: {str(e)}")
    
    @staticmethod
    def retrieve_payment_link(payment_link_id: str) -> Dict[str, Any]:
        """
        Ruft einen existierenden Payment Link ab.
        
        Args:
            payment_link_id: Stripe Payment Link ID
            
        Returns:
            Dict mit Payment Link Daten
        """
        try:
            payment_link = stripe.PaymentLink.retrieve(payment_link_id)
            
            return {
                "payment_link_id": payment_link.id,
                "payment_link_url": payment_link.url,
                "active": payment_link.active,
                "metadata": payment_link.metadata
            }
            
        except stripe.error.StripeError as e:
            print(f"[StripeService] Fehler beim Abrufen des Payment Links: {str(e)}")
            raise Exception(f"Payment Link konnte nicht abgerufen werden: {str(e)}")
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Verifiziert die Webhook-Signatur von Stripe.
        
        Args:
            payload: Rohdaten des Webhooks
            sig_header: Stripe-Signature Header
            
        Returns:
            Dict mit Event-Daten
            
        Raises:
            ValueError: Bei ungültiger Signatur
        """
        
        if not settings.stripe_webhook_secret:
            print("[StripeService] WARNING: Kein Webhook Secret konfiguriert - verwende Test-Modus")
            # Im Test-Modus: Parse Event direkt ohne Signatur-Prüfung
            import json
            try:
                event = json.loads(payload)
                print(f"[StripeService] Test-Modus: Event-Type = {event.get('type', 'unknown')}")
                return event
            except json.JSONDecodeError as e:
                print(f"[StripeService] Ungültiger JSON im Webhook: {str(e)}")
                raise ValueError("Ungültiger JSON im Webhook Payload")
        
        try:
            # Verifiziere Signatur mit konfigurierbarer Toleranz
            event = stripe.Webhook.construct_event(
                payload, 
                sig_header, 
                settings.stripe_webhook_secret,
                tolerance=settings.stripe_webhook_tolerance
            )
            
            print(f"[StripeService] Webhook-Signatur erfolgreich verifiziert")
            print(f"   - Event ID: {event.get('id', 'unknown')}")
            print(f"   - Event Type: {event.get('type', 'unknown')}")
            
            return event
            
        except ValueError as e:
            print(f"[StripeService] Ungültiger Webhook Payload: {str(e)}")
            raise ValueError(f"Ungültiger Webhook Payload: {str(e)}")
            
        except stripe.error.SignatureVerificationError as e:
            print(f"[StripeService] Ungültige Webhook Signatur: {str(e)}")
            raise ValueError(f"Ungültige Webhook Signatur: {str(e)}")
            
        except Exception as e:
            print(f"[StripeService] Unerwarteter Fehler bei Signatur-Verifizierung: {str(e)}")
            raise ValueError(f"Webhook-Verifizierung fehlgeschlagen: {str(e)}")
    
    @staticmethod
    def process_payment_success(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verarbeitet ein erfolgreiches Zahlungs-Event von Stripe.
        
        Args:
            event_data: Stripe Event Daten
            
        Returns:
            Dict mit Zahlungsinformationen
        """
        
        try:
            # Extrahiere relevante Daten aus dem Event
            event_type = event_data.get("type")
            event_id = event_data.get("id", "unknown")
            data_object = event_data.get("data", {}).get("object", {})
            
            print(f"[StripeService] Verarbeite Event: {event_type} (ID: {event_id})")
            
            # Hole Metadaten
            metadata = data_object.get("metadata", {})
            fee_id = metadata.get("fee_id")
            invoice_number = metadata.get("invoice_number")
            
            if not fee_id:
                print(f"[StripeService] WARNING: Keine fee_id in Metadaten gefunden")
                print(f"   - Verfügbare Metadaten: {list(metadata.keys())}")
            
            # Hole Zahlungsinformationen - robuste Extraktion
            amount_total = data_object.get("amount_total", 0)
            amount_received = amount_total / 100 if amount_total else 0  # Cent zu Hauptwährung
            currency = data_object.get("currency", "eur").upper()
            payment_intent_id = data_object.get("payment_intent")
            
            # Zahlungsmethode - verschiedene Quellen prüfen
            payment_method = "unknown"
            if "payment_method_types" in data_object:
                payment_methods = data_object.get("payment_method_types", [])
                payment_method = payment_methods[0] if payment_methods else "unknown"
            
            # Zusätzliche Informationen
            customer_email = data_object.get("customer_details", {}).get("email")
            session_id = data_object.get("id")
            
            print(f"[StripeService] Zahlung erfolgreich verarbeitet:")
            print(f"   - Gebühr ID: {fee_id}")
            print(f"   - Rechnungsnummer: {invoice_number}")
            print(f"   - Betrag: {amount_received} {currency}")
            print(f"   - Payment Intent: {payment_intent_id}")
            print(f"   - Session ID: {session_id}")
            print(f"   - Zahlungsmethode: {payment_method}")
            print(f"   - Kunden-E-Mail: {customer_email}")
            
            return {
                "fee_id": int(fee_id) if fee_id and fee_id.isdigit() else None,
                "invoice_number": invoice_number,
                "amount_received": amount_received,
                "currency": currency,
                "payment_intent_id": payment_intent_id,
                "payment_method": payment_method,
                "session_id": session_id,
                "customer_email": customer_email,
                "event_type": event_type,
                "event_id": event_id,
                "paid_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[StripeService] Fehler beim Verarbeiten des Events: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Fehler bei der Zahlungsverarbeitung: {str(e)}")
    
    @staticmethod
    def get_payment_link_for_fee(
        fee_id: int,
        amount: Decimal,
        currency: str,
        description: str,
        invoice_number: str,
        fee_percentage: float
    ) -> Dict[str, Any]:
        """
        Erstellt oder ruft einen Payment Link für eine Gebühr ab.
        Dies ist die Hauptmethode für die API.
        
        Args:
            fee_id: ID der BuildWise-Gebühr
            amount: Bruttobetrag
            currency: Währungscode
            description: Beschreibung
            invoice_number: Rechnungsnummer
            fee_percentage: Provisionssatz
            
        Returns:
            Dict mit Payment Link Informationen
        """
        
        return StripePaymentService.create_payment_link(
            fee_id=fee_id,
            amount=amount,
            currency=currency,
            description=description,
            invoice_number=invoice_number,
            fee_percentage=fee_percentage
        )


# Alias für Backward-Kompatibilität mit subscription_service
StripeService = StripePaymentService
