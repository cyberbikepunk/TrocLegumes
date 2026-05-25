from unittest.mock import MagicMock, patch

import pytest
from django.db import IntegrityError

from .factories import CropCategoryFactory, FarmFactory, FarmFollowFactory, FarmProductFactory, InvitationFactory

pytestmark = pytest.mark.django_db


class TestFarmStr:
    def test_str_is_name(self):
        farm = FarmFactory(name="La Ferme des Collines")
        assert str(farm) == "La Ferme des Collines"


class TestCropCategoryStr:
    def test_str_is_name(self):
        category = CropCategoryFactory(name="Légumes")
        assert str(category) == "Légumes"


class TestFarmProductStr:
    def test_str_includes_product_name_and_farm(self):
        farm = FarmFactory(name="Ferme A")
        product = FarmProductFactory(name="Tomates cerises", farm=farm)
        assert "Tomates cerises" in str(product)
        assert "Ferme A" in str(product)


class TestFarmFollow:
    def test_str_shows_direction(self):
        follower = FarmFactory(name="Ferme A")
        followed = FarmFactory(name="Ferme B")
        follow = FarmFollowFactory(follower_farm=follower, followed_farm=followed)
        assert "Ferme A" in str(follow)
        assert "Ferme B" in str(follow)

    def test_unique_together_prevents_duplicate(self):
        farm_a = FarmFactory()
        farm_b = FarmFactory()
        FarmFollowFactory(follower_farm=farm_a, followed_farm=farm_b)
        with pytest.raises(IntegrityError):
            FarmFollowFactory(follower_farm=farm_a, followed_farm=farm_b)

    def test_reverse_follow_is_allowed(self):
        farm_a = FarmFactory()
        farm_b = FarmFactory()
        FarmFollowFactory(follower_farm=farm_a, followed_farm=farm_b)
        # B following A is a distinct row — must not raise
        follow = FarmFollowFactory(follower_farm=farm_b, followed_farm=farm_a)
        assert follow.pk is not None


class TestInvitation:
    def test_token_is_auto_generated(self):
        invitation = InvitationFactory()
        assert invitation.token
        assert len(invitation.token) > 10

    def test_two_invitations_have_different_tokens(self):
        inv1 = InvitationFactory()
        inv2 = InvitationFactory()
        assert inv1.token != inv2.token

    def test_str_includes_email(self):
        invitation = InvitationFactory(email="test@example.com")
        assert "test@example.com" in str(invitation)


class TestFarmGeocoding:
    def test_geocode_sets_coordinates_on_save(self):
        mock_location = MagicMock()
        mock_location.latitude = 48.8566
        mock_location.longitude = 2.3522
        with patch("apps.farms.models.Farm._geocode_address") as mock_geocode:
            FarmFactory(address="Paris, France")
        mock_geocode.assert_called_once()

    def test_geocode_address_updates_lat_lon(self):
        farm = FarmFactory(address="")
        mock_location = MagicMock(latitude=48.8566, longitude=2.3522)
        with patch("geopy.geocoders.Nominatim.geocode", return_value=mock_location):
            farm.address = "Paris, France"
            farm.save()
        farm.refresh_from_db()
        assert farm.latitude == pytest.approx(48.8566)
        assert farm.longitude == pytest.approx(2.3522)

    def test_address_change_clears_coordinates(self):
        farm = FarmFactory(address="Lyon", latitude=45.76, longitude=4.83)
        with patch("apps.farms.models.Farm._geocode_address"):
            farm.address = "Marseille"
            farm.save()
        farm.refresh_from_db()
        assert farm.latitude is None
        assert farm.longitude is None
