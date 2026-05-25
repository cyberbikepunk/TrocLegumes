from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.contrib.inlines.admin import TabularInline as UnfoldTabularInline

from .models import CropCategory, Farm, FarmFollow, FarmProduct, Invitation


@admin.register(Farm)
class FarmAdmin(UnfoldModelAdmin):
    list_display = ["name", "address", "phone", "is_active", "latitude", "longitude", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "address"]


@admin.register(CropCategory)
class CropCategoryAdmin(UnfoldModelAdmin):
    list_display = ["name", "icon"]
    search_fields = ["name"]


class FarmProductInline(UnfoldTabularInline):
    model = FarmProduct
    extra = 0
    fields = ["name", "crop_category", "default_unit", "default_price", "is_active"]
    autocomplete_fields = ["crop_category"]


@admin.register(FarmProduct)
class FarmProductAdmin(UnfoldModelAdmin):
    list_display = ["name", "farm", "crop_category", "default_unit", "default_price", "is_active"]
    list_filter = ["farm", "crop_category", "is_active"]
    search_fields = ["name", "farm__name"]
    autocomplete_fields = ["farm", "crop_category"]


@admin.register(FarmFollow)
class FarmFollowAdmin(UnfoldModelAdmin):
    list_display = ["follower_farm", "followed_farm", "created_at"]
    list_filter = ["follower_farm", "followed_farm"]
    autocomplete_fields = ["follower_farm", "followed_farm"]


@admin.register(Invitation)
class InvitationAdmin(UnfoldModelAdmin):
    list_display = ["email", "invited_by", "used_at", "created_at"]
    list_filter = ["used_at"]
    search_fields = ["email"]
    readonly_fields = ["token"]
    autocomplete_fields = ["invited_by"]
