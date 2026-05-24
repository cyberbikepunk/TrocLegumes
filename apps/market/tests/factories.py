from datetime import date, timedelta

import factory

from apps.farms.tests.factories import FarmFactory, FarmProductFactory
from apps.market.models import Listing, Order, OrderItem, WantedListing, WantedResponse, Week


class WeekFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Week

    start_date = factory.Sequence(lambda n: date(2026, 1, 5) + timedelta(weeks=n))
    end_date = factory.LazyAttribute(lambda o: o.start_date + timedelta(days=6))
    is_active = False


class ListingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Listing

    farm_product = factory.SubFactory(FarmProductFactory)
    farm = factory.LazyAttribute(lambda o: o.farm_product.farm)
    week = factory.SubFactory(WeekFactory)
    quantity_available = "10.00"
    unit = "kg"
    price_per_unit = "3.00"
    is_active = True


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    buyer_farm = factory.SubFactory(FarmFactory)
    seller_farm = factory.SubFactory(FarmFactory)
    status = Order.Status.PENDING


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    listing = factory.SubFactory(ListingFactory)
    quantity = "2.00"
    unit_price = "3.00"
    total_price = "6.00"


class WantedListingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WantedListing

    farm = factory.SubFactory(FarmFactory)
    description = "Cherche des légumes bio"
    week = factory.SubFactory(WeekFactory)
    is_active = True
    is_fulfilled = False


class WantedResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WantedResponse

    wanted_listing = factory.SubFactory(WantedListingFactory)
    responding_farm = factory.SubFactory(FarmFactory)
    quantity_offered = "5.00"
    status = WantedResponse.Status.PENDING
