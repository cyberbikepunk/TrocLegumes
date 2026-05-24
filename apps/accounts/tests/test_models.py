import pytest

from apps.farms.tests.factories import FarmFactory

from .factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserStr:
    def test_str_includes_name_and_email(self):
        user = UserFactory(first_name="Alice", last_name="Dupont", email="alice@example.com")
        assert "Alice" in str(user)
        assert "Dupont" in str(user)
        assert "alice@example.com" in str(user)


class TestUserFullName:
    def test_full_name(self):
        user = UserFactory(first_name="Alice", last_name="Dupont")
        assert user.full_name == "Alice Dupont"

    def test_full_name_strips_extra_whitespace(self):
        user = UserFactory(first_name="Alice", last_name="")
        assert user.full_name == "Alice"


class TestUserFarm:
    def test_user_without_farm(self):
        user = UserFactory(farm=None)
        assert user.farm is None

    def test_user_with_farm(self):
        farm = FarmFactory()
        user = UserFactory(farm=farm)
        assert user.farm == farm
        assert user in farm.members.all()
