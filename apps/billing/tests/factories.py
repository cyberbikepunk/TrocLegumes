import factory

from apps.accounts.tests.factories import UserFactory
from apps.billing.models import Settlement, TabEntry
from apps.farms.tests.factories import FarmFactory
from apps.market.tests.factories import OrderFactory


class SettlementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Settlement

    farm_a = factory.SubFactory(FarmFactory)
    farm_b = factory.SubFactory(FarmFactory)
    amount = "100.00"
    type = Settlement.Type.MONETARY
    method = Settlement.Method.VIREMENT
    description = "Règlement de test"
    proposed_by = factory.SubFactory(UserFactory)
    confirmed_by = None
    confirmed_at = None
    status = Settlement.Status.PENDING


class TabEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TabEntry

    farm = factory.SubFactory(FarmFactory)
    order = factory.SubFactory(OrderFactory)
    settlement = None
    amount = "50.00"
    balance_after = "50.00"
    entry_type = TabEntry.EntryType.ORDER
    description = "Commande #1 — test"
