"""修复酒店基础数据：重名去重、房型去重、图片分配优化。"""

from __future__ import annotations

import hashlib
import random
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from apps.bookings.models import BookingOrder
from apps.hotels.models import Hotel, RoomType


def normalize_name(value: str) -> str:
    return " ".join((value or "").strip().split())


def build_unique_name(base_name: str, existing_keys: set[str], suffix_seed: str, max_length: int) -> str:
    normalized = normalize_name(base_name) or "未命名"
    candidate = normalized
    if candidate.casefold() not in existing_keys:
        existing_keys.add(candidate.casefold())
        return candidate[:max_length]

    serial = 1
    while True:
        candidate = f"{normalized}-{suffix_seed}-{serial}"
        truncated = candidate[:max_length]
        key = truncated.casefold()
        if key not in existing_keys:
            existing_keys.add(key)
            return truncated
        serial += 1


def iter_images(images_dir: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(
        [p for p in images_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts],
        key=lambda p: str(p).lower(),
    )


def build_album(image_pool: list[str], start_idx: int, album_size: int) -> list[str]:
    if not image_pool:
        return []
    total = len(image_pool)
    if total == 1:
        return [image_pool[0]]

    step = max(total // max(album_size, 1), 1)
    index = start_idx % total
    album: list[str] = []
    for _ in range(total):
        image_url = image_pool[index]
        if image_url not in album:
            album.append(image_url)
            if len(album) >= album_size:
                break
        index = (index + step) % total
    return album


class Command(BaseCommand):
    help = "修复酒店数据：删除可删的重名酒店/重名房型，并优化酒店与房型图片分配"

    def add_arguments(self, parser):
        parser.add_argument("--images-dir", type=str, default="", help="图库目录，默认 <repo>/dist/images")
        parser.add_argument("--seed", type=int, default=20260413, help="图片分配随机种子")
        parser.add_argument("--album-size", type=int, default=6, help="每家酒店图片数量（含封面）")
        parser.add_argument("--dry-run", action="store_true", help="仅预览修复计划，不写入数据库")

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run", False))
        seed = int(options.get("seed", 20260413))
        album_size = max(int(options.get("album_size", 6)), 1)

        images_dir_opt = str(options.get("images_dir", "")).strip()
        if images_dir_opt:
            images_dir = Path(images_dir_opt).resolve()
        else:
            images_dir = (Path(settings.BASE_DIR).parent / "dist" / "images").resolve()

        if not images_dir.exists():
            raise CommandError(f"图片目录不存在: {images_dir}")

        image_files = iter_images(images_dir)
        if not image_files:
            raise CommandError(f"未找到可用图片: {images_dir}")

        random.seed(seed)

        media_target = Path(settings.MEDIA_ROOT) / "gallery" / "hotels"
        if not dry_run:
            media_target.mkdir(parents=True, exist_ok=True)

        image_urls: list[str] = []
        for image in image_files:
            suffix = image.suffix.lower()
            digest = hashlib.md5(image.read_bytes()).hexdigest()[:10]
            target_name = f"{image.stem[:40]}-{digest}{suffix}"
            target_path = media_target / target_name
            if not dry_run and not target_path.exists():
                shutil.copy2(image, target_path)
            image_urls.append(f"{settings.MEDIA_URL}gallery/hotels/{target_name}")

        image_urls = list(dict.fromkeys(image_urls))
        random.shuffle(image_urls)

        stats = {
            "hotel_deleted": 0,
            "hotel_renamed": 0,
            "room_deleted": 0,
            "room_renamed": 0,
            "hotel_image_updated": 0,
            "room_image_updated": 0,
        }

        self._repair_duplicate_hotels(stats, dry_run=dry_run)
        self._repair_duplicate_room_types(stats, dry_run=dry_run)
        self._refresh_images(stats, image_urls=image_urls, album_size=album_size, dry_run=dry_run)

        action_label = "预览完成" if dry_run else "修复完成"
        self.stdout.write(self.style.SUCCESS(action_label))
        for key, value in stats.items():
            self.stdout.write(f"{key}: {value}")

    def _repair_duplicate_hotels(self, stats: dict[str, int], *, dry_run: bool):
        hotels = list(Hotel.objects.only("id", "name").order_by("id"))
        existing_keys = {normalize_name(h.name).casefold() for h in hotels}

        order_counts: dict[int, int] = {}
        for row in BookingOrder.objects.values("hotel_id").annotate(total=Count("id")):
            order_counts[int(row["hotel_id"])] = int(row["total"])

        grouped: dict[str, list[Hotel]] = {}
        for hotel in hotels:
            key = normalize_name(hotel.name).casefold()
            grouped.setdefault(key, []).append(hotel)

        for group in grouped.values():
            if len(group) <= 1:
                continue
            ordered = sorted(group, key=lambda h: (-order_counts.get(h.id, 0), h.id))
            keeper = ordered[0]
            for duplicate in ordered[1:]:
                has_orders = order_counts.get(duplicate.id, 0) > 0
                if has_orders:
                    new_name = build_unique_name(duplicate.name, existing_keys, f"重复{duplicate.id}", 200)
                    if new_name != duplicate.name:
                        stats["hotel_renamed"] += 1
                        if not dry_run:
                            Hotel.objects.filter(id=duplicate.id).update(name=new_name)
                    continue
                stats["hotel_deleted"] += 1
                if not dry_run:
                    duplicate.delete()
            existing_keys.add(normalize_name(keeper.name).casefold())

    def _repair_duplicate_room_types(self, stats: dict[str, int], *, dry_run: bool):
        order_counts: dict[int, int] = {}
        for row in BookingOrder.objects.values("room_type_id").annotate(total=Count("id")):
            order_counts[int(row["room_type_id"])] = int(row["total"])

        for hotel in Hotel.objects.only("id").order_by("id"):
            room_types = list(RoomType.objects.filter(hotel_id=hotel.id).only("id", "name").order_by("id"))
            existing_keys = {normalize_name(room.name).casefold() for room in room_types}
            grouped: dict[str, list[RoomType]] = {}
            for room in room_types:
                key = normalize_name(room.name).casefold()
                grouped.setdefault(key, []).append(room)

            for group in grouped.values():
                if len(group) <= 1:
                    continue
                ordered = sorted(group, key=lambda r: (-order_counts.get(r.id, 0), r.id))
                keeper = ordered[0]
                for duplicate in ordered[1:]:
                    has_orders = order_counts.get(duplicate.id, 0) > 0
                    if has_orders:
                        new_name = build_unique_name(duplicate.name, existing_keys, f"重复{duplicate.id}", 120)
                        if new_name != duplicate.name:
                            stats["room_renamed"] += 1
                            if not dry_run:
                                RoomType.objects.filter(id=duplicate.id).update(name=new_name)
                        continue
                    stats["room_deleted"] += 1
                    if not dry_run:
                        duplicate.delete()
                existing_keys.add(normalize_name(keeper.name).casefold())

    def _refresh_images(self, stats: dict[str, int], *, image_urls: list[str], album_size: int, dry_run: bool):
        if not image_urls:
            return

        hotels = list(Hotel.objects.order_by("id"))
        for idx, hotel in enumerate(hotels):
            cover = image_urls[idx % len(image_urls)]
            album = build_album(image_urls, start_idx=idx * 2 + 1, album_size=album_size)
            if cover in album:
                album = [img for img in album if img != cover]
            album.insert(0, cover)
            album = album[:album_size]

            changed = hotel.cover_image != cover or (hotel.images or []) != album
            if not changed:
                continue
            stats["hotel_image_updated"] += 1
            if not dry_run:
                Hotel.objects.filter(id=hotel.id).update(cover_image=cover, images=album)

        room_types = list(RoomType.objects.order_by("id"))
        for idx, room_type in enumerate(room_types):
            image = image_urls[(idx * 3 + 1) % len(image_urls)]
            if room_type.image == image:
                continue
            stats["room_image_updated"] += 1
            if not dry_run:
                RoomType.objects.filter(id=room_type.id).update(image=image)
