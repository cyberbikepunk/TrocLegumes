from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.contrib.inlines.admin import TabularInline as UnfoldTabularInline

from .models import Listing, Order, OrderItem, WantedListing, WantedResponse, Week


@admin.register(Week)
class WeekAdmin(UnfoldModelAdmin):
    list_display = ["__str__", "start_date", "end_date", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["start_date"]


class OrderItemInline(UnfoldTabularInline):
    model = OrderItem
    extra = 0
    fields = ["listing", "quantity", "unit_price", "total_price", "notes"]
    readonly_fields = ["total_price"]
    autocomplete_fields = ["listing"]


@admin.register(Listing)
class ListingAdmin(UnfoldModelAdmin):
    list_display = ["farm_product", "farm", "week", "quantity_available", "unit", "price_per_unit", "is_active"]
    list_filter = ["farm", "week", "is_active"]
    search_fields = ["farm_product__name", "farm__name"]
    list_select_related = ["farm_product", "farm", "week"]
    autocomplete_fields = ["farm_product", "farm", "week"]


@admin.register(Order)
class OrderAdmin(UnfoldModelAdmin):
    list_display = ["pk", "buyer_farm", "seller_farm", "status", "created_at"]
    list_filter = ["status", "buyer_farm", "seller_farm"]
    search_fields = ["buyer_farm__name", "seller_farm__name"]
    inlines = [OrderItemInline]
    autocomplete_fields = ["buyer_farm", "seller_farm"]


@admin.register(WantedListing)
class WantedListingAdmin(UnfoldModelAdmin):
    list_display = ["farm", "crop_category", "week", "is_fulfilled", "is_active", "created_at"]
    list_filter = ["farm", "week", "is_fulfilled", "is_active"]
    search_fields = ["description", "farm__name"]
    autocomplete_fields = ["farm", "crop_category", "week"]


@admin.register(WantedResponse)
class WantedResponseAdmin(UnfoldModelAdmin):
    list_display = ["responding_farm", "wanted_listing", "quantity_offered", "status", "created_at"]
    list_filter = ["status", "responding_farm"]
    search_fields = ["responding_farm__name"]
    autocomplete_fields = ["responding_farm", "wanted_listing"]
