"""Management command: 按名称关键词自动归类酒店类型（hotel/homestay/short_rent）。"""

from django.core.management.base import BaseCommand

from apps.hotels.models import Hotel


class Command(BaseCommand):
    help = "根据酒店名称中的关键词自动分类类型（民宿→homestay，短租/公寓→short_rent，其余→hotel）"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="仅预览分类结果，不实际修改数据")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        homestay_keywords = ["民宿", "客栈", "农家", "山居", "花园小院"]
        short_rent_keywords = ["短租", "公寓", "长租", "日租", "月租"]

        hotels = Hotel.objects.all()
        stats = {"hotel": 0, "homestay": 0, "short_rent": 0}

        for hotel in hotels:
            name = hotel.name
            new_type = Hotel.TYPE_HOTEL
            for kw in homestay_keywords:
                if kw in name:
                    new_type = Hotel.TYPE_HOMESTAY
                    break
            if new_type == Hotel.TYPE_HOTEL:
                for kw in short_rent_keywords:
                    if kw in name:
                        new_type = Hotel.TYPE_SHORT_RENT
                        break

            stats[new_type] += 1
            if hotel.type != new_type:
                self.stdout.write(f"  {'[DRY] ' if dry_run else ''}#{hotel.id} {hotel.name}: {hotel.type} → {new_type}")
                if not dry_run:
                    hotel.type = new_type
                    hotel.save(update_fields=["type"])

        self.stdout.write(self.style.SUCCESS(
            f"\n{'[预览模式] ' if dry_run else ''}分类完成: 酒店 {stats['hotel']} / 民宿 {stats['homestay']} / 短租 {stats['short_rent']}"
        ))
