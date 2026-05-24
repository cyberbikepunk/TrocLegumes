from django.contrib import admin

from .models import Listing, Order, OrderItem, WantedListing, WantedResponse, Week


@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ["__str__", "start_date", "end_date", "is_active", "created_at"]
    list_filter = ["is_active"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["listing", "quantity", "unit_price", "total_price", "notes"]
    readonly_fields = ["total_price"]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ["farm_product", "farm", "week", "quantity_available", "unit", "price_per_unit", "is_active"]
    list_filter = ["farm", "week", "is_active"]
    search_fields = ["farm_product__name", "farm__name"]
    list_select_related = ["farm_product", "farm", "week"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["pk", "buyer_farm", "seller_farm", "status", "created_at"]
    list_filter = ["status", "buyer_farm", "seller_farm"]
    inlines = [OrderItemInline]


@admin.register(WantedListing)
class WantedListingAdmin(admin.ModelAdmin):
    list_display = ["farm", "crop_category", "week", "is_fulfilled", "is_active", "created_at"]
    list_filter = ["farm", "week", "is_fulfilled", "is_active"]
    search_fields = ["description", "farm__name"]


@admin.register(WantedResponse)
class WantedResponseAdmin(admin.ModelAdmin):
    list_display = ["responding_farm", "wanted_listing", "quantity_offered", "status", "created_at"]
    list_filter = ["status", "responding_farm"]
