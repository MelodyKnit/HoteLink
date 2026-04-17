"""apps/hotels/models.py —— 酒店与库存数据模型。"""

from django.db import models


class Hotel(models.Model):
    """酒店基础信息模型。"""
    STATUS_DRAFT = "draft"
    STATUS_ONLINE = "online"
    STATUS_OFFLINE = "offline"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "草稿"),
        (STATUS_ONLINE, "已上架"),
        (STATUS_OFFLINE, "已下架"),
    ]

    TYPE_HOTEL = "hotel"
    TYPE_HOMESTAY = "homestay"
    TYPE_SHORT_RENT = "short_rent"
    TYPE_CHOICES = [
        (TYPE_HOTEL, "酒店"),
        (TYPE_HOMESTAY, "民宿"),
        (TYPE_SHORT_RENT, "短租"),
    ]

    name = models.CharField(max_length=200, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_HOTEL, db_index=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    star = models.PositiveSmallIntegerField(default=3)
    phone = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.URLField(blank=True)
    images = models.JSONField(default=list, blank=True, help_text="酒店图片 URL 列表")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    facilities = models.JSONField(default=list, blank=True, help_text="设施标签列表，如 ['wifi','parking','pool']")
    tags = models.JSONField(default=list, blank=True, help_text="自定义标签，如 ['免费取消','含早','近地铁']")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_recommended = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hotel"
        verbose_name_plural = "Hotels"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.name


class RoomType(models.Model):
    """酒店房型定义模型。"""
    BED_SINGLE = "single"
    BED_DOUBLE = "double"
    BED_QUEEN = "queen"
    BED_TWIN = "twin"
    BED_FAMILY = "family"
    BED_TYPE_CHOICES = [
        (BED_SINGLE, "单人床"),
        (BED_DOUBLE, "双人床"),
        (BED_QUEEN, "大床"),
        (BED_TWIN, "双床"),
        (BED_FAMILY, "家庭床"),
    ]

    STATUS_ONLINE = "online"
    STATUS_OFFLINE = "offline"
    STATUS_CHOICES = [
        (STATUS_ONLINE, "已上架"),
        (STATUS_OFFLINE, "已下架"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="room_types")
    name = models.CharField(max_length=120)
    bed_type = models.CharField(max_length=20, choices=BED_TYPE_CHOICES, default=BED_QUEEN)
    area = models.PositiveIntegerField(default=20)
    breakfast_count = models.PositiveIntegerField(default=0)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_guest_count = models.PositiveIntegerField(default=2)
    stock = models.PositiveIntegerField(default=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ONLINE)
    image = models.URLField(blank=True, help_text="房型主图 URL")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Room Type"
        verbose_name_plural = "Room Types"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(fields=["hotel", "name"], name="uniq_room_type_name_per_hotel"),
        ]

    def __str__(self) -> str:
        return f"{self.hotel.name}-{self.name}"


class RoomInventory(models.Model):
    """房型按日期的价格与库存快照模型。"""
    STATUS_AVAILABLE = "available"
    STATUS_RESERVED = "reserved"
    STATUS_OCCUPIED = "occupied"
    STATUS_CLEANING = "cleaning"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_OFFLINE = "offline"
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "空闲可售"),
        (STATUS_RESERVED, "已预订"),
        (STATUS_OCCUPIED, "在住"),
        (STATUS_CLEANING, "清扫中"),
        (STATUS_MAINTENANCE, "维修中"),
        (STATUS_OFFLINE, "下线不可售"),
    ]

    room_type_id: int
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name="inventories")
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Room Inventory"
        verbose_name_plural = "Room Inventories"
        ordering = ["date", "room_type_id"]
        unique_together = ("room_type", "date")

    def __str__(self) -> str:
        return f"{self.room_type_id}-{self.date}"
