#!/usr/bin/env python3
"""
Unit-Tests für das Daily Deduction Timezone-Fix

Testet ob die has_daily_deduction_today() Funktion korrekt mit verschiedenen
Timezone-Szenarien umgeht.
"""

import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user_credits import UserCredits, PlanStatus


class TestDailyDeductionTimezone(unittest.TestCase):
    """Test-Klasse für Daily Deduction Timezone-Handling"""
    
    @classmethod
    def setUpClass(cls):
        """Erstelle Test-Datenbank"""
        # In-Memory SQLite für Tests
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)
    
    def setUp(self):
        """Setup vor jedem Test"""
        self.db = self.SessionLocal()
        
    def tearDown(self):
        """Cleanup nach jedem Test"""
        self.db.query(UserCredits).delete()
        self.db.commit()
        self.db.close()
    
    def test_naive_datetime_same_day(self):
        """Test: Naive datetime vom gleichen Tag sollte True zurückgeben"""
        user_credits = UserCredits(
            user_id=1,
            credits=100,
            plan_status=PlanStatus.PRO
        )
        
        # Setze naive datetime von heute
        today = datetime.now()
        user_credits.last_daily_deduction = today.replace(hour=10, minute=0, second=0, microsecond=0, tzinfo=None)
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertTrue(result, "Naive datetime vom gleichen Tag sollte als 'heute' erkannt werden")
    
    def test_naive_datetime_yesterday(self):
        """Test: Naive datetime von gestern sollte False zurückgeben"""
        user_credits = UserCredits(
            user_id=2,
            credits=100,
            plan_status=PlanStatus.PRO
        )
        
        # Setze naive datetime von gestern
        yesterday = datetime.now() - timedelta(days=1)
        user_credits.last_daily_deduction = yesterday.replace(hour=10, minute=0, second=0, microsecond=0, tzinfo=None)
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertFalse(result, "Naive datetime von gestern sollte nicht als 'heute' erkannt werden")
    
    def test_utc_aware_datetime_same_day(self):
        """Test: UTC-aware datetime vom gleichen Tag sollte True zurückgeben"""
        user_credits = UserCredits(
            user_id=3,
            credits=100,
            plan_status=PlanStatus.PRO
        )
        
        # Setze UTC-aware datetime von heute
        today_utc = datetime.now(timezone.utc)
        user_credits.last_daily_deduction = today_utc.replace(hour=10, minute=0, second=0, microsecond=0)
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertTrue(result, "UTC-aware datetime vom gleichen Tag sollte als 'heute' erkannt werden")
    
    def test_utc_aware_datetime_yesterday(self):
        """Test: UTC-aware datetime von gestern sollte False zurückgeben"""
        user_credits = UserCredits(
            user_id=4,
            credits=100,
            plan_status=PlanStatus.PRO
        )
        
        # Setze UTC-aware datetime von gestern
        yesterday_utc = datetime.now(timezone.utc) - timedelta(days=1)
        user_credits.last_daily_deduction = yesterday_utc.replace(hour=10, minute=0, second=0, microsecond=0)
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertFalse(result, "UTC-aware datetime von gestern sollte nicht als 'heute' erkannt werden")
    
    def test_non_utc_timezone_same_day(self):
        """Test: Nicht-UTC timezone vom gleichen Tag sollte True zurückgeben"""
        user_credits = UserCredits(
            user_id=5,
            credits=100,
            plan_status=PlanStatus.PRO
        )
        
        # Erstelle timezone offset (z.B. +02:00 für deutsche Sommerzeit)
        from datetime import tzinfo
        class CustomTimezone(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=2)
            def tzname(self, dt):
                return "CEST"
            def dst(self, dt):
                return timedelta(0)
        
        # Setze datetime mit Custom-Timezone von heute
        today_local = datetime.now(CustomTimezone())
        user_credits.last_daily_deduction = today_local.replace(hour=10, minute=0, second=0, microsecond=0)
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertTrue(result, "Nicht-UTC timezone vom gleichen Tag sollte als 'heute' erkannt werden")
    
    def test_none_last_deduction(self):
        """Test: None last_daily_deduction sollte False zurückgeben"""
        user_credits = UserCredits(
            user_id=6,
            credits=100,
            plan_status=PlanStatus.PRO,
            last_daily_deduction=None
        )
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertFalse(result, "None last_daily_deduction sollte False zurückgeben")
    
    def test_edge_case_midnight_utc(self):
        """Test: Edge-Case um Mitternacht UTC"""
        user_credits = UserCredits(
            user_id=7,
            credits=100,
            plan_status=PlanStatus.PRO
        )
        
        # Setze auf exakt Mitternacht UTC heute
        today_midnight_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        user_credits.last_daily_deduction = today_midnight_utc
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertTrue(result, "Mitternacht UTC heute sollte als 'heute' erkannt werden")
    
    def test_edge_case_just_before_midnight(self):
        """Test: Edge-Case kurz vor Mitternacht"""
        user_credits = UserCredits(
            user_id=8,
            credits=100,
            plan_status=PlanStatus.PRO
        )
        
        # Setze auf 23:59:59 UTC heute
        today_before_midnight = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=999999)
        user_credits.last_daily_deduction = today_before_midnight
        
        self.db.add(user_credits)
        self.db.commit()
        
        # Prüfe ob heute bereits abgezogen wurde
        result = user_credits.has_daily_deduction_today()
        
        self.assertTrue(result, "23:59:59 UTC heute sollte als 'heute' erkannt werden")


def run_tests():
    """Führe alle Tests aus"""
    # Test-Suite erstellen
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDailyDeductionTimezone)
    
    # Tests ausführen
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("Test-Zusammenfassung:")
    print(f"   Gesamt: {result.testsRun} Tests")
    print(f"   Erfolgreich: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Fehlgeschlagen: {len(result.failures)}")
    print(f"   Fehler: {len(result.errors)}")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Daily Deduction Timezone Tests")
    print("="*60)
    
    success = run_tests()
    
    if success:
        print("\nAlle Tests erfolgreich!")
        exit(0)
    else:
        print("\nEinige Tests sind fehlgeschlagen!")
        exit(1)

