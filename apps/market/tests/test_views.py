import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.farms.tests.factories import FarmFactory, FarmProductFactory
from apps.market.tests.factories import ListingFactory, WeekFactory


@pytest.fixture
def active_week(db):
    return WeekFactory(is_active=True)


@pytest.fixture
def user_with_farm(db):
    farm = FarmFactory()
    user = UserFactory(farm=farm)
    user.save()
    return user


@pytest.fixture
def other_farm(db):
    return FarmFactory()


class TestMarketplaceView:
    def test_get_returns_200_anonymous(self, client, db):
        response = client.get(reverse("market:marketplace"))
        assert response.status_code == 200

    def test_shows_no_listings_without_active_week(self, client, db):
        WeekFactory(is_active=False)
        response = client.get(reverse("market:marketplace"))
        assert response.context["active_week"] is None

    def test_shows_listings_for_active_week(self, client, active_week):
        listing = ListingFactory(week=active_week, is_active=True)
        response = client.get(reverse("market:marketplace"))
        assert listing in response.context["listings_others"]

    def test_followed_listings_appear_in_followed_section(self, client, active_week, user_with_farm):
        from apps.farms.models import FarmFollow
        followed_farm = FarmFactory()
        FarmFollow.objects.create(follower_farm=user_with_farm.farm, followed_farm=followed_farm)
        listing = ListingFactory(week=active_week, is_active=True, farm=followed_farm,
                                  farm_product=FarmProductFactory(farm=followed_farm))
        client.force_login(user_with_farm)
        response = client.get(reverse("market:marketplace"))
        assert listing in response.context["listings_followed"]
        assert listing not in response.context["listings_others"]


class TestListingListView:
    def test_unauthenticated_redirects(self, client, db):
        response = client.get(reverse("market:listing_list"))
        assert response.status_code == 302

    def test_authenticated_returns_200(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("market:listing_list"))
        assert response.status_code == 200

    def test_shows_only_own_farm_listings(self, client, user_with_farm, active_week, other_farm):
        own = ListingFactory(
            farm=user_with_farm.farm,
            farm_product=FarmProductFactory(farm=user_with_farm.farm),
            week=active_week,
        )
        other = ListingFactory(
            farm=other_farm,
            farm_product=FarmProductFactory(farm=other_farm),
            week=active_week,
        )
        client.force_login(user_with_farm)
        response = client.get(reverse("market:listing_list"))
        listing_pks = [lst.pk for lst in response.context["listings"]]
        assert own.pk in listing_pks
        assert other.pk not in listing_pks


class TestListingCreateView:
    def test_unauthenticated_redirects(self, client, db):
        response = client.get(reverse("market:listing_create"))
        assert response.status_code == 302

    def test_no_active_week_redirects(self, client, user_with_farm):
        client.force_login(user_with_farm)
        response = client.get(reverse("market:listing_create"))
        assert response.status_code == 302

    def test_get_returns_200_with_active_week(self, client, user_with_farm, active_week):
        client.force_login(user_with_farm)
        response = client.get(reverse("market:listing_create"))
        assert response.status_code == 200

    def test_post_creates_listing(self, client, user_with_farm, active_week):
        product = FarmProductFactory(farm=user_with_farm.farm)
        client.force_login(user_with_farm)
        response = client.post(
            reverse("market:listing_create"),
            {
                "farm_product": product.pk,
                "quantity_available": "5.00",
                "unit": "kg",
                "price_per_unit": "2.50",
                "notes": "",
            },
        )
        assert response.status_code == 302
        from apps.market.models import Listing
        assert Listing.objects.filter(farm=user_with_farm.farm, farm_product=product).exists()


class TestListingUpdateView:
    def test_unauthenticated_redirects(self, client, active_week):
        listing = ListingFactory(week=active_week)
        response = client.get(reverse("market:listing_update", kwargs={"pk": listing.pk}))
        assert response.status_code == 302

    def test_owner_can_access(self, client, user_with_farm, active_week):
        listing = ListingFactory(
            farm=user_with_farm.farm,
            farm_product=FarmProductFactory(farm=user_with_farm.farm),
            week=active_week,
        )
        client.force_login(user_with_farm)
        response = client.get(reverse("market:listing_update", kwargs={"pk": listing.pk}))
        assert response.status_code == 200

    def test_non_owner_gets_403(self, client, user_with_farm, active_week, other_farm):
        listing = ListingFactory(
            farm=other_farm,
            farm_product=FarmProductFactory(farm=other_farm),
            week=active_week,
        )
        client.force_login(user_with_farm)
        response = client.get(reverse("market:listing_update", kwargs={"pk": listing.pk}))
        assert response.status_code == 403


class TestListingDeleteView:
    def test_owner_can_delete(self, client, user_with_farm, active_week):
        listing = ListingFactory(
            farm=user_with_farm.farm,
            farm_product=FarmProductFactory(farm=user_with_farm.farm),
            week=active_week,
        )
        client.force_login(user_with_farm)
        response = client.post(reverse("market:listing_delete", kwargs={"pk": listing.pk}))
        assert response.status_code == 302
        from apps.market.models import Listing
        assert not Listing.objects.filter(pk=listing.pk).exists()

    def test_non_owner_gets_403(self, client, user_with_farm, active_week, other_farm):
        listing = ListingFactory(
            farm=other_farm,
            farm_product=FarmProductFactory(farm=other_farm),
            week=active_week,
        )
        client.force_login(user_with_farm)
        response = client.post(reverse("market:listing_delete", kwargs={"pk": listing.pk}))
        assert response.status_code == 403
