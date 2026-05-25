import pytest

from apps.market.models import Order, WantedResponse

from .factories import (
    ListingFactory,
    OrderFactory,
    OrderItemFactory,
    WantedListingFactory,
    WantedResponseFactory,
    WeekFactory,
)

pytestmark = pytest.mark.django_db


class TestWeekStr:
    def test_str_includes_dates(self):
        week = WeekFactory(start_date="2026-05-18", end_date="2026-05-24")
        assert "2026-05-18" in str(week)
        assert "2026-05-24" in str(week)


class TestWeekSave:
    def test_activating_week_deactivates_others(self):
        week1 = WeekFactory(is_active=True)
        week2 = WeekFactory(is_active=False)
        week2.is_active = True
        week2.save()
        week1.refresh_from_db()
        assert not week1.is_active
        assert week2.is_active

    def test_inactive_week_does_not_affect_others(self):
        week1 = WeekFactory(is_active=True)
        week2 = WeekFactory(is_active=False)
        week2.save()
        week1.refresh_from_db()
        assert week1.is_active


class TestListingStr:
    def test_str_includes_product_name_and_farm(self):
        listing = ListingFactory()
        result = str(listing)
        assert listing.farm_product.name in result
        assert listing.farm.name in result

    def test_farm_matches_farm_product_farm(self):
        listing = ListingFactory()
        assert listing.farm == listing.farm_product.farm


class TestOrder:
    def test_str_includes_pk_and_farms(self):
        order = OrderFactory()
        result = str(order)
        assert str(order.pk) in result
        assert order.buyer_farm.name in result
        assert order.seller_farm.name in result

    def test_str_includes_status_display(self):
        order = OrderFactory(status=Order.Status.PENDING)
        assert "En attente" in str(order)

    def test_default_status_is_pending(self):
        order = OrderFactory()
        assert order.status == Order.Status.PENDING

    def test_all_status_choices_exist(self):
        expected = {"pending", "accepted", "confirmed", "declined", "cancelled"}
        actual = {choice.value for choice in Order.Status}
        assert actual == expected


class TestOrderItemStr:
    def test_str_includes_product_name_and_quantity(self):
        item = OrderItemFactory(quantity="3.00")
        result = str(item)
        assert item.listing.farm_product.name in result
        assert "3" in result


class TestWantedListing:
    def test_str_includes_farm_and_description(self):
        listing = WantedListingFactory(description="Cherche 10kg de courges")
        result = str(listing)
        assert listing.farm.name in result
        assert "Cherche 10kg de courges" in result

    def test_str_truncates_long_description(self):
        long_desc = "x" * 100
        listing = WantedListingFactory(description=long_desc)
        # __str__ truncates to 50 chars
        assert len(str(listing)) < len(long_desc) + 50


class TestWantedResponse:
    def test_str_includes_responding_farm(self):
        response = WantedResponseFactory()
        assert response.responding_farm.name in str(response)

    def test_default_status_is_pending(self):
        response = WantedResponseFactory()
        assert response.status == WantedResponse.Status.PENDING

    def test_all_status_choices_exist(self):
        expected = {"pending", "accepted", "declined"}
        actual = {choice.value for choice in WantedResponse.Status}
        assert actual == expected
