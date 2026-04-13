from __future__ import annotations

import random
import shutil
import importlib
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import CommandError
from django.db.models.deletion import ProtectedError


CITY_CENTERS = {
    "北京": (39.904200, 116.407400),
    "上海": (31.230400, 121.473700),
    "广州": (23.129100, 113.264400),
    "深圳": (22.543100, 114.057900),
    "杭州": (30.274100, 120.155100),
    "成都": (30.572800, 104.066800),
    "苏州": (31.298900, 120.585300),
    "南京": (32.060300, 118.796900),
    "武汉": (30.592800, 114.305500),
    "西安": (34.341600, 108.939800),
}

NAME_PREFIXES = ["云栖", "澜庭", "星河", "柏悦", "御景", "悦栖", "泊云", "漫心", "铂瑞", "望湖"]
NAME_SUFFIXES = ["酒店", "大酒店", "国际酒店", "度假酒店", "精选酒店", "轻奢酒店"]
AREAS = ["市中心", "高铁站", "会展", "湖畔", "滨江", "金融城", "老城区", "科技园"]

ROOM_TYPES = [
    {"name": "标准大床房", "bed_type": "queen", "area": 28, "breakfast_count": 1, "base_price": 468, "max_guest_count": 2, "stock": 20},
    {"name": "豪华双床房", "bed_type": "twin", "area": 36, "breakfast_count": 2, "base_price": 628, "max_guest_count": 2, "stock": 16},
    {"name": "家庭套房", "bed_type": "family", "area": 52, "breakfast_count": 3, "base_price": 888, "max_guest_count": 3, "stock": 12},
]


def add_arguments(parser) -> None:
    parser.add_argument("--count", type=int, default=200, help="生成酒店数量，默认 200")
    parser.add_argument("--images-dir", type=str, default="", help="图片目录，默认 <repo>/dist/images")
    parser.add_argument("--overwrite", action="store_true", help="清空现有酒店后重建")
    parser.add_argument("--seed", type=int, default=20260407, help="随机种子")


def iter_images(images_dir: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return [p for p in images_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def random_coord(city: str) -> tuple[float, float]:
    lat0, lng0 = CITY_CENTERS[city]
    lat = lat0 + random.uniform(-0.08, 0.08)
    lng = lng0 + random.uniform(-0.08, 0.08)
    return round(lat, 6), round(lng, 6)


def normalize_name(value: str) -> str:
    return " ".join((value or "").strip().split())


def pick_unique_hotel_name(base_name: str, used_names: set[str], serial_fallback: int) -> str:
    normalized_base = normalize_name(base_name)
    candidate = normalized_base
    if candidate and candidate.casefold() not in used_names:
        used_names.add(candidate.casefold())
        return candidate

    candidate = f"{normalized_base}-{serial_fallback}"
    if candidate.casefold() not in used_names:
        used_names.add(candidate.casefold())
        return candidate

    suffix = 2
    while True:
        candidate = f"{normalized_base}-{serial_fallback}-{suffix}"
        key = candidate.casefold()
        if key not in used_names:
            used_names.add(key)
            return candidate
        suffix += 1


def build_album(image_pool: list[str], start_idx: int, album_size: int = 4) -> list[str]:
    if not image_pool:
        return []
    total = len(image_pool)
    if total == 1:
        return [image_pool[0]]

    result: list[str] = []
    step = max(total // max(album_size, 1), 1)
    idx = start_idx % total
    for _ in range(total):
        url = image_pool[idx]
        if url not in result:
            result.append(url)
            if len(result) >= album_size:
                break
        idx = (idx + step) % total
    return result


def run(command, *args, **options) -> Any:
    BookingOrder = importlib.import_module("apps.bookings.models").BookingOrder
    hotel_models = importlib.import_module("apps.hotels.models")
    Hotel = hotel_models.Hotel
    RoomType = hotel_models.RoomType

    count = int(options.get("count", 200))
    if count <= 0:
        raise CommandError("count 必须大于 0")

    random.seed(int(options.get("seed", 20260407)))

    images_dir_opt = str(options.get("images_dir", "")).strip()
    if images_dir_opt:
        images_dir = Path(images_dir_opt).resolve()
    else:
        images_dir = (Path(settings.BASE_DIR).parent / "dist" / "images").resolve()

    if not images_dir.exists():
        raise CommandError(f"图片目录不存在: {images_dir}")

    images = iter_images(images_dir)
    if not images:
        raise CommandError(f"未找到图片文件: {images_dir}")

    media_target = Path(settings.MEDIA_ROOT) / "seed" / "hotels"
    media_target.mkdir(parents=True, exist_ok=True)

    copied_urls: list[str] = []
    for img in images:
        target = media_target / img.name
        if not target.exists():
            shutil.copy2(img, target)
        copied_urls.append(f"{settings.MEDIA_URL}seed/hotels/{img.name}")
    copied_urls = list(dict.fromkeys(copied_urls))
    random.shuffle(copied_urls)

    if options.get("overwrite"):
        command.stdout.write(command.style.WARNING("overwrite=true: 清空现有酒店和房型数据"))
        try:
            RoomType.objects.all().delete()
            Hotel.objects.all().delete()
        except ProtectedError:
            referenced_room_type_ids = set(BookingOrder.objects.values_list("room_type_id", flat=True))
            RoomType.objects.exclude(id__in=referenced_room_type_ids).delete()
            Hotel.objects.update(status=Hotel.STATUS_OFFLINE, is_recommended=False)
            command.stdout.write(command.style.WARNING("检测到历史订单引用，已改为软覆盖：旧酒店下线，继续生成新数据"))

    cities = list(CITY_CENTERS.keys())
    serial_start = Hotel.objects.count() + 1
    used_hotel_names = {normalize_name(str(name)).casefold() for name in Hotel.objects.values_list("name", flat=True)}
    created = 0
    for i in range(count):
        city = random.choice(cities)
        area = random.choice(AREAS)
        name = f"{city}{area}{random.choice(NAME_PREFIXES)}{random.choice(NAME_SUFFIXES)}"
        lat, lng = random_coord(city)
        min_price = random.randint(320, 1180)
        rating = round(random.uniform(4.1, 4.9), 1)
        star = random.choice([3, 4, 4, 5])
        cover = copied_urls[i % len(copied_urls)]
        album = build_album(copied_urls, start_idx=i * 3 + 1, album_size=4)
        if cover in album:
            album = [img for img in album if img != cover]
        album.insert(0, cover)
        album = album[:4]

        final_name = pick_unique_hotel_name(name, used_hotel_names, serial_start + i)

        hotel = Hotel.objects.create(
            name=final_name,
            city=city,
            address=f"{city}{area}{random.randint(1, 199)}号",
            star=star,
            phone=f"400-86{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            description=f"位于{city}{area}，交通便捷，适合商务出行与休闲旅游。",
            cover_image=cover,
            images=album,
            rating=rating,
            min_price=min_price,
            latitude=lat,
            longitude=lng,
            is_recommended=(i % 4 == 0),
            status=Hotel.STATUS_ONLINE,
        )

        for room in ROOM_TYPES:
            base_price = int(room["base_price"] * random.uniform(0.9, 1.25))
            room_name = normalize_name(str(room["name"]))
            exists_same_room = RoomType.objects.filter(hotel=hotel, name__iexact=room_name).exists()
            if exists_same_room:
                command.stdout.write(command.style.WARNING(f"跳过重复房型：hotel={hotel.id} name={room_name}"))
                continue
            RoomType.objects.create(
                hotel=hotel,
                name=room_name,
                bed_type=room["bed_type"],
                area=room["area"],
                breakfast_count=room["breakfast_count"],
                base_price=base_price,
                max_guest_count=room["max_guest_count"],
                stock=room["stock"],
                status=RoomType.STATUS_ONLINE,
                image=album[min(1, len(album) - 1)] if album else cover,
                description=f"{room['name']}，舒适安静，适合入住。",
            )

        created += 1

    command.stdout.write(command.style.SUCCESS(f"完成：新增酒店 {created} 家，房型 {created * len(ROOM_TYPES)} 个。"))
    return None
