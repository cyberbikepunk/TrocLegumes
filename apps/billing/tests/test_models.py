import pytest

from apps.billing.models import Settlement, TabEntry

from .factories import SettlementFactory, TabEntryFactory

pytestmark = pytest.mark.django_db


class TestSettlement:
    def test_str_includes_farms_and_amount(self):
        settlement = SettlementFactory(amount="150.00")
        result = str(settlement)
        assert settlement.farm_a.name in result
        assert settlement.farm_b.name in result
        assert "150" in result

    def test_default_status_is_pending(self):
        settlement = SettlementFactory()
        assert settlement.status == Settlement.Status.PENDING

    def test_all_type_choices_exist(self):
        expected = {"monetary", "labor", "mutual_writeoff"}
        actual = {choice.value for choice in Settlement.Type}
        assert actual == expected

    def test_all_status_choices_exist(self):
        expected = {"pending", "confirmed", "disputed"}
        actual = {choice.value for choice in Settlement.Status}
        assert actual == expected

    def test_confirmed_by_is_nullable(self):
        settlement = SettlementFactory(confirmed_by=None)
        assert settlement.confirmed_by is None


class TestTabEntry:
    def test_str_includes_farm_and_amount(self):
        entry = TabEntryFactory(amount="75.00")
        result = str(entry)
        assert entry.farm.name in result
        assert "75" in result

    def test_str_shows_sign_for_credit(self):
        entry = TabEntryFactory(amount="50.00")
        assert "+" in str(entry)

    def test_str_shows_sign_for_debit(self):
        entry = TabEntryFactory(amount="-50.00")
        assert "-" in str(entry)

    def test_all_entry_type_choices_exist(self):
        expected = {"order", "settlement", "adjustment"}
        actual = {choice.value for choice in TabEntry.EntryType}
        assert actual == expected

    def test_order_and_settlement_are_nullable(self):
        entry = TabEntryFactory(order=None, settlement=None, entry_type=TabEntry.EntryType.ADJUSTMENT)
        assert entry.order is None
        assert entry.settlement is None
