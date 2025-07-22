#!/usr/bin/env python3
"""
Stripe Service für BuildWise Subscription Management
"""

import stripe
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..core.config import settings

# Stripe konfigurieren
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')

class StripeService:
    """Service für Stripe-Integration"""
    
    # Stripe Price IDs (werden in .env konfiguriert)
    PRO_MONTHLY_PRICE_ID = os.getenv('STRIPE_PRO_MONTHLY_PRICE_ID', 'price_monthly_test')
    PRO_YEARLY_PRICE_ID = os.getenv('STRIPE_PRO_YEARLY_PRICE_ID', 'price_yearly_test')
    
    @staticmethod
    async def create_customer(email: str, name: str) -> Optional[Dict[str, Any]]:
        """Erstellt einen neuen Stripe Customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'platform': 'buildwise',
                    'created_via': 'api'
                }
            )
            return {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'created': customer.created
            }
        except stripe.error.StripeError as e:
            print(f"❌ Stripe Customer Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error creating customer: {e}")
            return None
    
    @staticmethod
    async def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Erstellt eine Stripe Checkout Session"""
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'platform': 'buildwise'
                },
                subscription_data={
                    'metadata': {
                        'user_id': str(user_id),
                        'platform': 'buildwise'
                    }
                }
            )
            return {
                'id': session.id,
                'url': session.url,
                'customer': session.customer,
                'payment_status': session.payment_status
            }
        except stripe.error.StripeError as e:
            print(f"❌ Stripe Checkout Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error creating checkout: {e}")
            return None
    
    @staticmethod
    async def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
        """Holt Subscription-Details von Stripe"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                'id': subscription.id,
                'status': subscription.status,
                'customer': subscription.customer,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'items': [{
                    'price_id': item.price.id,
                    'product_id': item.price.product
                } for item in subscription.items.data]
            }
        except stripe.error.StripeError as e:
            print(f"❌ Stripe Subscription Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error getting subscription: {e}")
            return None
    
    @staticmethod
    async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> bool:
        """Kündigt eine Subscription"""
        try:
            if at_period_end:
                # Kündigung am Ende der Periode
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Sofortige Kündigung
                stripe.Subscription.delete(subscription_id)
            return True
        except stripe.error.StripeError as e:
            print(f"❌ Stripe Cancel Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error canceling subscription: {e}")
            return False
    
    @staticmethod
    async def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
        """Holt Customer-Details von Stripe"""
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'created': customer.created,
                'subscriptions': [sub.id for sub in customer.subscriptions.data]
            }
        except stripe.error.StripeError as e:
            print(f"❌ Stripe Customer Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error getting customer: {e}")
            return None
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        """Verifiziert Stripe Webhook Signature"""
        try:
            webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
            if not webhook_secret:
                print("❌ STRIPE_WEBHOOK_SECRET nicht konfiguriert")
                return False
            
            stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            print("❌ Stripe Webhook Signature ungültig")
            return False
        except Exception as e:
            print(f"❌ Webhook Verification Error: {e}")
            return False
    
    @staticmethod
    def parse_webhook_event(payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
        """Parsed ein Stripe Webhook Event"""
        try:
            webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
            if not webhook_secret:
                return None
            
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except Exception as e:
            print(f"❌ Webhook Parse Error: {e}")
            return None
    
    @staticmethod
    def get_price_info(price_id: str) -> Dict[str, Any]:
        """Gibt Preis-Informationen zurück"""
        price_info = {
            StripeService.PRO_MONTHLY_PRICE_ID: {
                'name': 'BuildWise Pro Monthly',
                'amount': 1299,  # 12.99 CHF in Rappen
                'currency': 'chf',
                'interval': 'month',
                'plan': 'pro'
            },
            StripeService.PRO_YEARLY_PRICE_ID: {
                'name': 'BuildWise Pro Yearly',
                'amount': 13000,  # 130 CHF in Rappen
                'currency': 'chf',
                'interval': 'year',
                'plan': 'pro'
            }
        }
        return price_info.get(price_id, {})
    
    @staticmethod
    def format_amount(amount_in_cents: int, currency: str = 'chf') -> str:
        """Formatiert Betrag für Anzeige"""
        if currency.lower() == 'chf':
            return f"{amount_in_cents / 100:.2f} CHF"
        return f"{amount_in_cents / 100:.2f} {currency.upper()}" 