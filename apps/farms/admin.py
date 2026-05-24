from django.contrib import admin

from .models import CropCategory, Farm, FarmFollow, FarmProduct, Invitation


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "address"]


@admin.register(CropCategory)
class CropCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "icon"]
    search_fields = ["name"]


class FarmProductInline(admin.TabularInline):
    model = FarmProduct
    extra = 0
    fields = ["name", "crop_category", "default_unit", "default_price", "is_active"]


@admin.register(FarmProduct)
class FarmProductAdmin(admin.ModelAdmin):
    list_display = ["name", "farm", "crop_category", "default_unit", "default_price", "is_active"]
    list_filter = ["farm", "crop_category", "is_active"]
    search_fields = ["name", "farm__name"]


@admin.register(FarmFollow)
class FarmFollowAdmin(admin.ModelAdmin):
    list_display = ["follower_farm", "followed_farm", "created_at"]
    list_filter = ["follower_farm", "followed_farm"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "invited_by", "used_at", "created_at"]
    list_filter = ["used_at"]
    search_fields = ["email"]
    readonly_fields = ["token"]
