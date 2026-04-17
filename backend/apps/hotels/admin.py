"""hotels admin 配置模块。"""

from django.contrib import admin

from apps.hotels.models import Hotel, RoomInventory, RoomType


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "city", "star", "min_price", "status", "is_recommended", "updated_at")
    list_filter = ("type", "status", "star", "city", "is_recommended")
    search_fields = ("name", "address", "city")
    list_editable = ("type", "status", "is_recommended")


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "hotel", "name", "bed_type", "base_price", "stock", "status")
    list_filter = ("status", "bed_type")
    search_fields = ("name", "hotel__name")


@admin.register(RoomInventory)
class RoomInventoryAdmin(admin.ModelAdmin):
    list_display = ("id", "room_type", "date", "price", "stock", "status")
    list_filter = ("status", "date")
    search_fields = ("room_type__name",)