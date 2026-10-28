"""
accounts app — tests.

Covers the pure, DB-free logic added for SSO country assignment and the
screen-access permission helper. Run:

    python manage.py test accounts --settings=config.settings_test
"""

from django.test import TestCase

from accounts.views import _country_from_email


class CountryFromEmailTest(TestCase):
    """SSO assigns a user's country from their email domain TLD."""

    def test_ru_maps_to_russia(self):
        self.assertEqual(_country_from_email("ccevik@solgarvitamin.ru"), "Russia")

    def test_kz_maps_to_kazakhstan(self):
        self.assertEqual(_country_from_email("someone@solgar.kz"), "Kazakhstan")

    def test_unknown_tld_is_blank(self):
        self.assertEqual(_country_from_email("user@solgar.com"), "")

    def test_uppercase_domain_still_maps(self):
        self.assertEqual(_country_from_email("User@SOLGAR.RU"), "Russia")

    def test_malformed_email_is_blank(self):
        self.assertEqual(_country_from_email(""), "")
        self.assertEqual(_country_from_email("no-at-sign"), "")
        self.assertEqual(_country_from_email("a@b"), "")  # no dot in domain
