import pytest
from django.urls import reverse

from apps.farms.tests.factories import FarmFactory

from .factories import UserFactory


@pytest.fixture
def user(db):
    u = UserFactory()
    u.save()  # persist hashed password so force_login session hash matches
    return u


@pytest.fixture
def user_with_farm(db):
    u = UserFactory(farm=FarmFactory())
    u.save()  # persist hashed password so force_login session hash matches
    return u


class TestLoginView:
    def test_get_returns_200(self, client, db):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200

    def test_authenticated_user_is_redirected(self, client, user):
        client.force_login(user)
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 302

    def test_valid_login_redirects_to_dashboard(self, client, db):
        u = UserFactory()
        u.save()  # persist hashed password
        response = client.post(
            reverse("accounts:login"),
            {"username": u.email, "password": "testpass123"},
        )
        assert response.status_code == 302


class TestRegisterView:
    def test_get_returns_200(self, client, db):
        response = client.get(reverse("accounts:register"))
        assert response.status_code == 200

    def test_authenticated_user_is_redirected(self, client, user):
        client.force_login(user)
        response = client.get(reverse("accounts:register"))
        assert response.status_code == 302

    def test_valid_registration_creates_user_and_redirects(self, client, db):
        response = client.post(
            reverse("accounts:register"),
            {
                "email": "nouveau@example.com",
                "first_name": "Jean",
                "last_name": "Dupont",
                "password1": "S3cur3P@ssw0rd!",
                "password2": "S3cur3P@ssw0rd!",
            },
        )
        assert response.status_code == 302


class TestDashboardView:
    def test_unauthenticated_redirects_to_login(self, client, db):
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/connexion/" in response["Location"]

    def test_authenticated_returns_200(self, client, user):
        client.force_login(user)
        response = client.get(reverse("dashboard"))
        assert response.status_code == 200

    def test_context_has_followed_farms(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("dashboard"))
        assert "followed_farms" in response.context
