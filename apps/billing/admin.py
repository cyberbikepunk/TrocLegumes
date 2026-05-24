from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from .models import Settlement, TabEntry


@admin.register(Settlement)
class SettlementAdmin(UnfoldModelAdmin):
    list_display = ["farm_a", "farm_b", "amount", "type", "status", "proposed_by", "created_at"]
    list_filter = ["type", "status", "farm_a", "farm_b"]
    search_fields = ["farm_a__name", "farm_b__name", "description"]
    readonly_fields = ["confirmed_at"]
    autocomplete_fields = ["farm_a", "farm_b", "proposed_by", "confirmed_by"]


@admin.register(TabEntry)
class TabEntryAdmin(UnfoldModelAdmin):
    list_display = ["farm", "amount", "balance_after", "entry_type", "created_at"]
    list_filter = ["entry_type", "farm"]
    search_fields = ["farm__name", "description"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["farm", "order", "settlement"]
