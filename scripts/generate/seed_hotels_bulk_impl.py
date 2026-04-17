from __future__ import annotations

from collections import Counter
from datetime import timedelta
import importlib
import random
import shutil
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import CommandError
from django.db.models.deletion import ProtectedError
from django.utils import timezone


CITY_PROFILES = [
    {"name": "北京", "center": (39.9042, 116.4074), "phone": "010", "districts": ["朝阳区", "海淀区", "东城区"], "areas": ["国贸", "望京", "中关村", "三里屯"], "roads": ["建国路", "望京街", "知春路", "工体北路"], "landmarks": ["国家会议中心", "国贸CBD", "三里屯太古里"], "themes": ["商务会展", "城市度假", "亲子出游"]},
    {"name": "上海", "center": (31.2304, 121.4737), "phone": "021", "districts": ["浦东新区", "黄浦区", "静安区"], "areas": ["陆家嘴", "人民广场", "静安寺", "徐家汇"], "roads": ["世纪大道", "南京西路", "淮海中路", "龙腾大道"], "landmarks": ["外滩", "上海中心", "国家会展中心"], "themes": ["金融商旅", "都市夜景", "会奖出行"]},
    {"name": "广州", "center": (23.1291, 113.2644), "phone": "020", "districts": ["天河区", "越秀区", "海珠区"], "areas": ["珠江新城", "北京路", "琶洲", "长隆"], "roads": ["花城大道", "阅江中路", "天河北路", "新港东路"], "landmarks": ["广州塔", "广交会展馆", "长隆旅游度假区"], "themes": ["会展商旅", "家庭出游", "美食探索"]},
    {"name": "深圳", "center": (22.5431, 114.0579), "phone": "0755", "districts": ["南山区", "福田区", "罗湖区"], "areas": ["科技园", "车公庙", "海上世界", "前海"], "roads": ["深南大道", "科苑南路", "滨海大道", "福华路"], "landmarks": ["深圳湾公园", "世界之窗", "会展中心"], "themes": ["商务差旅", "科技出行", "滨海休闲"]},
    {"name": "杭州", "center": (30.2741, 120.1551), "phone": "0571", "districts": ["西湖区", "上城区", "滨江区"], "areas": ["西湖景区", "钱江新城", "奥体", "未来科技城"], "roads": ["解放东路", "龙井路", "江晖路", "文一西路"], "landmarks": ["西湖", "杭州奥体中心", "灵隐寺"], "themes": ["城市度假", "互联网商旅", "文化休闲"]},
    {"name": "成都", "center": (30.5728, 104.0668), "phone": "028", "districts": ["锦江区", "高新区", "青羊区"], "areas": ["春熙路", "金融城", "宽窄巷子", "东郊记忆"], "roads": ["天府大道", "人民南路", "红星路", "交子大道"], "landmarks": ["太古里", "环球中心", "宽窄巷子"], "themes": ["休闲慢旅", "商务会展", "美食打卡"]},
    {"name": "重庆", "center": (29.563, 106.5516), "phone": "023", "districts": ["渝中区", "江北区", "南岸区"], "areas": ["解放碑", "观音桥", "南滨路", "礼嘉"], "roads": ["民权路", "北城天街", "南滨路", "金渝大道"], "landmarks": ["洪崖洞", "来福士", "重庆国际博览中心"], "themes": ["山城夜景", "美食旅行", "会展差旅"]},
    {"name": "南京", "center": (32.0603, 118.7969), "phone": "025", "districts": ["玄武区", "建邺区", "秦淮区"], "areas": ["新街口", "河西", "夫子庙", "南站"], "roads": ["中山路", "江东中路", "汉中路", "软件大道"], "landmarks": ["夫子庙", "玄武湖", "南京国际博览中心"], "themes": ["历史文化", "商务差旅", "周末度假"]},
    {"name": "苏州", "center": (31.2989, 120.5853), "phone": "0512", "districts": ["姑苏区", "工业园区", "虎丘区"], "areas": ["观前街", "金鸡湖", "狮山", "独墅湖"], "roads": ["人民路", "旺墩路", "狮山路", "星港街"], "landmarks": ["金鸡湖", "拙政园", "苏州博览中心"], "themes": ["园林度假", "会展商旅", "亲子周末"]},
    {"name": "武汉", "center": (30.5928, 114.3055), "phone": "027", "districts": ["武昌区", "江汉区", "洪山区"], "areas": ["楚河汉街", "光谷", "江汉路", "王家湾"], "roads": ["中北路", "珞喻路", "解放大道", "鹦鹉大道"], "landmarks": ["黄鹤楼", "东湖", "武汉国际博览中心"], "themes": ["高校出行", "会展商旅", "家庭游玩"]},
    {"name": "西安", "center": (34.3416, 108.9398), "phone": "029", "districts": ["雁塔区", "碑林区", "未央区"], "areas": ["小寨", "高新", "钟楼", "曲江"], "roads": ["长安中路", "唐延路", "东大街", "曲江池东路"], "landmarks": ["大雁塔", "大唐不夜城", "钟楼"], "themes": ["历史文化", "会展商旅", "亲子研学"]},
    {"name": "天津", "center": (39.0842, 117.2009), "phone": "022", "districts": ["和平区", "河西区", "滨海新区"], "areas": ["小白楼", "梅江", "鼓楼", "滨海站"], "roads": ["南京路", "友谊路", "南门外大街", "响螺湾"], "landmarks": ["天津之眼", "国家会展中心", "五大道"], "themes": ["城市周末", "会展商旅", "海河夜景"]},
    {"name": "青岛", "center": (36.0671, 120.3826), "phone": "0532", "districts": ["市南区", "崂山区", "黄岛区"], "areas": ["五四广场", "石老人", "金沙滩", "浮山湾"], "roads": ["香港中路", "东海东路", "漓江西路", "澳门路"], "landmarks": ["奥帆中心", "崂山", "金沙滩"], "themes": ["滨海度假", "啤酒文化", "亲子海景"]},
    {"name": "厦门", "center": (24.4798, 118.0894), "phone": "0592", "districts": ["思明区", "湖里区", "集美区"], "areas": ["环岛路", "中山路", "软件园", "五缘湾"], "roads": ["演武路", "鹭江道", "观日路", "仙岳路"], "landmarks": ["鼓浪屿", "厦门大学", "会展中心"], "themes": ["海岛假期", "文艺漫游", "商务出行"]},
    {"name": "长沙", "center": (28.2282, 112.9388), "phone": "0731", "districts": ["芙蓉区", "岳麓区", "天心区"], "areas": ["五一广场", "梅溪湖", "南门口", "高铁南站"], "roads": ["黄兴路", "潇湘中路", "湘江中路", "劳动东路"], "landmarks": ["橘子洲", "IFS", "岳麓山"], "themes": ["夜生活", "城市度假", "会展差旅"]},
    {"name": "郑州", "center": (34.7466, 113.6254), "phone": "0371", "districts": ["金水区", "郑东新区", "二七区"], "areas": ["花园路", "CBD", "二七广场", "高铁东站"], "roads": ["商务内环路", "农业路", "中原中路", "东风路"], "landmarks": ["郑州东站", "如意湖", "二七纪念塔"], "themes": ["交通中转", "商务差旅", "会展活动"]},
    {"name": "昆明", "center": (25.0389, 102.7183), "phone": "0871", "districts": ["盘龙区", "五华区", "西山区"], "areas": ["翠湖", "滇池", "南屏街", "会展片区"], "roads": ["北京路", "广福路", "人民中路", "环湖东路"], "landmarks": ["滇池", "翠湖公园", "国际会展中心"], "themes": ["高原度假", "花海慢游", "会展商旅"]},
    {"name": "三亚", "center": (18.2528, 109.5119), "phone": "0898", "districts": ["吉阳区", "天涯区", "海棠区"], "areas": ["亚龙湾", "大东海", "海棠湾", "三亚湾"], "roads": ["亚龙湾路", "迎宾路", "海棠北路", "凤凰路"], "landmarks": ["亚龙湾", "蜈支洲岛", "免税城"], "themes": ["海滨度假", "亲子休闲", "蜜月旅行"]},
    {"name": "海口", "center": (20.044, 110.1983), "phone": "0898", "districts": ["美兰区", "龙华区", "秀英区"], "areas": ["国兴大道", "西海岸", "骑楼老街", "观澜湖"], "roads": ["国兴大道", "滨海大道", "海秀中路", "蓝天路"], "landmarks": ["假日海滩", "骑楼老街", "国际会展中心"], "themes": ["滨海度假", "家庭出游", "会展差旅"]},
    {"name": "沈阳", "center": (41.8057, 123.4315), "phone": "024", "districts": ["和平区", "沈河区", "浑南区"], "areas": ["太原街", "中街", "浑南", "奥体"], "roads": ["青年大街", "中华路", "浑南中路", "建设大路"], "landmarks": ["故宫", "中街", "奥体中心"], "themes": ["商务差旅", "东北美食", "冬季出行"]},
    {"name": "大连", "center": (38.914, 121.6147), "phone": "0411", "districts": ["中山区", "西岗区", "高新区"], "areas": ["东港", "星海广场", "青泥洼桥", "软件园"], "roads": ["人民路", "中山路", "黄河路", "软件园路"], "landmarks": ["星海广场", "东港商务区", "老虎滩"], "themes": ["海景度假", "商务会议", "夏季避暑"]},
    {"name": "哈尔滨", "center": (45.8038, 126.5349), "phone": "0451", "districts": ["道里区", "南岗区", "松北区"], "areas": ["中央大街", "会展中心", "群力", "太阳岛"], "roads": ["友谊路", "红旗大街", "学府路", "群力大道"], "landmarks": ["中央大街", "冰雪大世界", "太阳岛"], "themes": ["冰雪旅行", "会展商旅", "冬季度假"]},
    {"name": "乌鲁木齐", "center": (43.8256, 87.6168), "phone": "0991", "districts": ["天山区", "沙依巴克区", "新市区"], "areas": ["大巴扎", "友好", "会展片区", "高铁站"], "roads": ["新华南路", "友好北路", "会展大道", "北京中路"], "landmarks": ["国际大巴扎", "红山公园", "新疆国际会展中心"], "themes": ["新疆旅行", "会展商旅", "中转住宿"]},
    {"name": "拉萨", "center": (29.652, 91.1721), "phone": "0891", "districts": ["城关区", "柳梧新区", "堆龙德庆区"], "areas": ["布达拉宫", "八廓街", "柳梧", "文创园"], "roads": ["北京中路", "江苏大道", "林廓东路", "柳梧大道"], "landmarks": ["布达拉宫", "大昭寺", "罗布林卡"], "themes": ["高原旅行", "文化朝圣", "慢节奏度假"]},
]

FACILITY_LABELS = {"wifi": "高速WiFi", "parking": "免费停车", "pool": "泳池", "gym": "健身房", "restaurant": "餐厅", "air_conditioning": "空调", "elevator": "电梯", "laundry": "洗衣服务", "luggage_storage": "行李寄存", "front_desk_24h": "24小时前台", "airport_shuttle": "接送机", "meeting_room": "会议室", "non_smoking": "无烟房", "pet_friendly": "可携宠", "kitchen": "厨房", "washing_machine": "洗衣机"}

TYPE_CONFIGS = {
    "hotel": {"prefixes": ["云栖", "柏悦", "星河", "铂瑞", "澜庭", "御景"], "suffixes": ["酒店", "大酒店", "国际酒店", "度假酒店", "精选酒店"], "need": ["wifi", "parking", "air_conditioning", "front_desk_24h", "luggage_storage"], "opt": ["pool", "gym", "restaurant", "laundry", "elevator", "airport_shuttle", "meeting_room", "non_smoking"], "price": (420, 1380), "stars": [3, 4, 4, 5, 5], "tags": ["免费取消", "含早", "近地铁", "商务出行", "亲子友好", "高分口碑", "会展优选", "景观房"]},
    "homestay": {"prefixes": ["慢居", "花筑", "归舍", "听风", "沐野", "庭见"], "suffixes": ["民宿", "客栈", "花园小院", "山居"], "need": ["wifi", "air_conditioning", "non_smoking"], "opt": ["parking", "laundry", "kitchen", "washing_machine", "pet_friendly", "luggage_storage"], "price": (188, 880), "stars": [2, 3, 3, 4], "tags": ["拍照出片", "亲子友好", "宠物友好", "庭院感", "长住友好", "近景区", "安静舒适", "可做饭"]},
    "short_rent": {"prefixes": ["城屿", "泊寓", "悦寓", "云舍", "悦享", "观城"], "suffixes": ["短租公寓", "日租公寓", "精品公寓", "行政公寓"], "need": ["wifi", "air_conditioning", "kitchen", "washing_machine"], "opt": ["parking", "elevator", "non_smoking", "pet_friendly", "laundry", "luggage_storage"], "price": (168, 760), "stars": [2, 3, 3, 4], "tags": ["可做饭", "洗衣方便", "长住友好", "高铁便利", "商务差旅", "家庭出游", "拎包入住", "性价比高"]},
}

ROOM_TEMPLATES = {
    "hotel": [{"name": "标准大床房", "bed_type": "queen", "area": 28, "breakfast_count": 1, "base_price": 468, "max_guest_count": 2, "stock": 18}, {"name": "豪华双床房", "bed_type": "twin", "area": 36, "breakfast_count": 2, "base_price": 628, "max_guest_count": 2, "stock": 16}, {"name": "行政大床房", "bed_type": "queen", "area": 42, "breakfast_count": 2, "base_price": 768, "max_guest_count": 2, "stock": 12}, {"name": "家庭套房", "bed_type": "family", "area": 56, "breakfast_count": 3, "base_price": 988, "max_guest_count": 4, "stock": 8}],
    "homestay": [{"name": "温馨大床房", "bed_type": "queen", "area": 26, "breakfast_count": 1, "base_price": 258, "max_guest_count": 2, "stock": 6}, {"name": "庭院双床房", "bed_type": "twin", "area": 32, "breakfast_count": 2, "base_price": 338, "max_guest_count": 2, "stock": 5}, {"name": "亲子家庭房", "bed_type": "family", "area": 42, "breakfast_count": 2, "base_price": 458, "max_guest_count": 4, "stock": 4}],
    "short_rent": [{"name": "城景一居室", "bed_type": "queen", "area": 38, "breakfast_count": 0, "base_price": 228, "max_guest_count": 2, "stock": 7}, {"name": "商务双床套间", "bed_type": "twin", "area": 46, "breakfast_count": 0, "base_price": 298, "max_guest_count": 2, "stock": 6}, {"name": "家庭两居套房", "bed_type": "family", "area": 68, "breakfast_count": 0, "base_price": 428, "max_guest_count": 4, "stock": 4}],
}


def add_arguments(parser) -> None:
    parser.add_argument("--count", type=int, default=200, help="生成酒店数量，默认 200")
    parser.add_argument("--images-dir", type=str, default="", help="图片目录，默认 <repo>/dist/hotel_photo_crawler/photos")
    parser.add_argument("--overwrite", action="store_true", help="清空现有酒店后重建")
    parser.add_argument("--seed", type=int, default=20260407, help="随机种子")
    parser.add_argument("--inventory-days", type=int, default=15, help="每个房型生成未来库存天数，默认 15")


def iter_images(images_dir: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(p for p in images_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts)


def random_coord(city_profile: dict[str, Any]) -> tuple[float, float]:
    lat0, lng0 = city_profile["center"]
    return round(lat0 + random.uniform(-0.12, 0.12), 6), round(lng0 + random.uniform(-0.12, 0.12), 6)


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
        if candidate.casefold() not in used_names:
            used_names.add(candidate.casefold())
            return candidate
        suffix += 1


def build_album(image_pool: list[str], start_idx: int, album_size: int = 5) -> list[str]:
    if not image_pool:
        return []
    if len(image_pool) <= album_size:
        return image_pool[:]
    result: list[str] = []
    step = max(len(image_pool) // album_size, 1)
    idx = start_idx % len(image_pool)
    for _ in range(len(image_pool) * 2):
        image = image_pool[idx]
        if image not in result:
            result.append(image)
            if len(result) >= album_size:
                break
        idx = (idx + step) % len(image_pool)
    return result


def choose_hotel_type() -> str:
    value = random.random()
    if value < 0.56:
        return "hotel"
    if value < 0.82:
        return "homestay"
    return "short_rent"


def build_address(city_profile: dict[str, Any], district: str, area: str) -> str:
    return f"{city_profile['name']}{district}{random.choice(city_profile['roads'])}{random.randint(18, 388)}号{area}{random.choice(['A座', 'B座', '1号楼', '2号楼'])}"


def build_facilities(hotel_type: str, star: int) -> list[str]:
    config = TYPE_CONFIGS[hotel_type]
    facilities = list(config["need"])
    optional_count = 3 if hotel_type == "short_rent" or (hotel_type == "hotel" and star >= 4) else 2
    facilities.extend(random.sample(config["opt"], k=min(optional_count, len(config["opt"]))))
    return list(dict.fromkeys(facilities))


def build_tags(hotel_type: str, city_profile: dict[str, Any], area: str, min_price: int, rating: float) -> list[str]:
    tags = random.sample(TYPE_CONFIGS[hotel_type]["tags"], k=2)
    tags.append(random.choice(city_profile["themes"]))
    if "站" in area:
        tags.append("交通便利")
    if hotel_type == "hotel" and min_price >= 900:
        tags.append("高端精选")
    if rating >= 4.7:
        tags.append("住客好评")
    return list(dict.fromkeys(tags))[:4]


def build_description(hotel_type: str, city_profile: dict[str, Any], district: str, area: str, address: str, facilities: list[str], min_price: int) -> str:
    landmark = random.choice(city_profile["landmarks"])
    theme = random.choice(city_profile["themes"])
    facility_text = "、".join(FACILITY_LABELS[item] for item in facilities[:4])
    if hotel_type == "hotel":
        return f"酒店位于{city_profile['name']}{district}{area}板块，地址为{address}，距离{landmark}通勤便捷，整体定位偏向{theme}场景。客房与公共区域覆盖{facility_text}等服务，适合商务差旅、会展接待、周末度假与家庭短住。当前起订价约为{min_price}元，配套成熟，入住与出行都比较省心。"
    if hotel_type == "homestay":
        return f"民宿坐落于{city_profile['name']}{district}{area}附近，地址为{address}，周边可快速到达{landmark}。整体氛围更偏生活化与度假感，房间强调安静、舒适和在地体验，常用配置包含{facility_text}。适合情侣、亲子和朋友结伴出行，当前参考价约{min_price}元。"
    return f"短租公寓位于{city_profile['name']}{district}{area}片区，地址为{address}，前往{landmark}和周边商圈都很方便。产品定位偏向{theme}与长短住结合，房间提供{facility_text}等居住型配置，兼顾出差办公与家庭入住需求。当前参考起订价约{min_price}元。"


def build_hotel_name(city_profile: dict[str, Any], district: str, area: str, hotel_type: str) -> str:
    config = TYPE_CONFIGS[hotel_type]
    return f"{city_profile['name']}{district.replace('区', '')}{area}{random.choice(config['prefixes'])}{random.choice(config['suffixes'])}"


def build_phone(city_profile: dict[str, Any]) -> str:
    prefix = city_profile["phone"]
    return f"{prefix}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}" if len(prefix) > 3 else f"{prefix}-{random.randint(10000000, 99999999)}"


def build_room_templates(hotel_type: str, star: int) -> list[dict[str, Any]]:
    templates = [dict(item) for item in ROOM_TEMPLATES[hotel_type]]
    return templates[:3] if hotel_type == "hotel" and star <= 3 else templates


def build_room_description(hotel_type: str, room_name: str, city_profile: dict[str, Any], area: str) -> str:
    if hotel_type == "hotel":
        return f"{room_name}面向{area}商圈或周边城市景观，兼顾舒适睡眠、商务办公与短途休闲。"
    if hotel_type == "homestay":
        return f"{room_name}延续在地生活气质，适合慢节奏入住，方便体验{city_profile['name']}周边生活与景点。"
    return f"{room_name}提供更完整的居住型配置，适合短住、差旅与家庭分区休息。"


def generate_inventory_rows(room_type, base_price: int, inventory_days: int):
    RoomInventory = importlib.import_module("apps.hotels.models").RoomInventory
    today = timezone.localdate()
    rows = []
    for offset in range(inventory_days):
        day = today + timedelta(days=offset)
        weekend = 1.12 if day.weekday() >= 4 else 1.0
        price = round(base_price * weekend * random.uniform(0.93, 1.16))
        stock = max(room_type.stock - random.randint(0, max(room_type.stock // 3, 1)), 1)
        roll = random.random()
        if roll < 0.82:
            status = RoomInventory.STATUS_AVAILABLE
        elif roll < 0.91:
            status = RoomInventory.STATUS_RESERVED
        elif roll < 0.96:
            status = RoomInventory.STATUS_CLEANING
        else:
            status = RoomInventory.STATUS_MAINTENANCE
        rows.append(RoomInventory(room_type=room_type, date=day, price=price, stock=stock, status=status))
    return rows


def copy_images_to_media(images: list[Path]) -> list[str]:
    media_target = Path(settings.MEDIA_ROOT) / "seed" / "hotels"
    media_target.mkdir(parents=True, exist_ok=True)
    copied_urls: list[str] = []
    for image in images:
        target = media_target / image.name
        if not target.exists():
            shutil.copy2(image, target)
        copied_urls.append(f"{settings.MEDIA_URL}seed/hotels/{image.name}")
    return list(dict.fromkeys(copied_urls))


def run(command, *args, **options) -> Any:
    BookingOrder = importlib.import_module("apps.bookings.models").BookingOrder
    hotel_models = importlib.import_module("apps.hotels.models")
    Hotel = hotel_models.Hotel
    RoomInventory = hotel_models.RoomInventory
    RoomType = hotel_models.RoomType

    count = int(options.get("count", 200))
    inventory_days = int(options.get("inventory_days", 15))
    if count <= 0:
        raise CommandError("count 必须大于 0")
    if inventory_days <= 0:
        raise CommandError("inventory_days 必须大于 0")

    random.seed(int(options.get("seed", 20260407)))

    images_dir_opt = str(options.get("images_dir", "")).strip()
    images_dir = (
        Path(images_dir_opt).resolve()
        if images_dir_opt
        else (Path(settings.BASE_DIR).parent / "dist" / "hotel_photo_crawler" / "photos").resolve()
    )
    if not images_dir.exists():
        raise CommandError(f"图片目录不存在: {images_dir}")

    images = iter_images(images_dir)
    if not images:
        raise CommandError(f"未找到图片文件: {images_dir}")

    copied_urls = copy_images_to_media(images)
    random.shuffle(copied_urls)

    if options.get("overwrite"):
        command.stdout.write(command.style.WARNING("overwrite=true: 清空现有酒店、房型与库存数据"))
        try:
            RoomType.objects.all().delete()
            Hotel.objects.all().delete()
        except ProtectedError:
            referenced_room_type_ids = set(BookingOrder.objects.values_list("room_type_id", flat=True))
            RoomInventory.objects.exclude(room_type_id__in=referenced_room_type_ids).delete()
            RoomType.objects.exclude(id__in=referenced_room_type_ids).delete()
            Hotel.objects.update(status=Hotel.STATUS_OFFLINE, is_recommended=False)
            command.stdout.write(command.style.WARNING("检测到历史订单引用，已保留关联房型并将旧酒店下线，继续生成新数据"))

    used_hotel_names = {normalize_name(str(name)).casefold() for name in Hotel.objects.values_list("name", flat=True)}
    serial_start = Hotel.objects.count() + 1
    type_counter: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()
    room_counter = 0
    inventory_counter = 0

    for i in range(count):
        city_profile = random.choice(CITY_PROFILES)
        district = random.choice(city_profile["districts"])
        area = random.choice(city_profile["areas"])
        hotel_type = choose_hotel_type()
        config = TYPE_CONFIGS[hotel_type]
        star = random.choice(config["stars"])
        min_price = random.randint(*config["price"])
        rating = round(random.uniform(4.2, 4.9), 1)
        address = build_address(city_profile, district, area)
        facilities = build_facilities(hotel_type, star)
        tags = build_tags(hotel_type, city_profile, area, min_price, rating)
        cover = copied_urls[i % len(copied_urls)]
        album = build_album(copied_urls, start_idx=i * 5 + 2, album_size=5)
        if cover in album:
            album = [item for item in album if item != cover]
        album.insert(0, cover)
        album = album[:5]
        final_name = pick_unique_hotel_name(build_hotel_name(city_profile, district, area, hotel_type), used_hotel_names, serial_start + i)
        lat, lng = random_coord(city_profile)

        hotel = Hotel.objects.create(
            name=final_name,
            type=hotel_type,
            city=city_profile["name"],
            address=address,
            star=star,
            phone=build_phone(city_profile),
            description=build_description(hotel_type, city_profile, district, area, address, facilities, min_price),
            cover_image=cover,
            images=album,
            rating=rating,
            min_price=min_price,
            facilities=facilities,
            tags=tags,
            latitude=lat,
            longitude=lng,
            is_recommended=(rating >= 4.7 and i % 5 == 0),
            status=Hotel.STATUS_ONLINE,
        )

        inventory_rows = []
        for idx, room in enumerate(build_room_templates(hotel_type, star)):
            base_price = max(int(room["base_price"] * random.uniform(0.92, 1.28)), min_price - 30)
            room_type = RoomType.objects.create(
                hotel=hotel,
                name=room["name"],
                bed_type=room["bed_type"],
                area=room["area"] + random.randint(0, 8),
                breakfast_count=room["breakfast_count"],
                base_price=base_price,
                max_guest_count=room["max_guest_count"],
                stock=max(room["stock"] + random.randint(-2, 3), 2),
                status=RoomType.STATUS_ONLINE,
                image=album[min(idx + 1, len(album) - 1)] if album else cover,
                description=build_room_description(hotel_type, room["name"], city_profile, area),
            )
            room_counter += 1
            inventory_rows.extend(generate_inventory_rows(room_type, base_price, inventory_days))

        RoomInventory.objects.bulk_create(inventory_rows, batch_size=1000)
        inventory_counter += len(inventory_rows)
        type_counter[hotel_type] += 1
        city_counter[city_profile["name"]] += 1

        if (i + 1) % 100 == 0:
            command.stdout.write(f"进度：已生成 {(i + 1)}/{count} 家酒店，房型 {room_counter} 个，库存 {inventory_counter} 条")

    top_cities = "、".join(f"{city}({num})" for city, num in city_counter.most_common(10))
    command.stdout.write(command.style.SUCCESS(f"完成：新增酒店 {count} 家，其中酒店 {type_counter['hotel']} 家 / 民宿 {type_counter['homestay']} 家 / 短租 {type_counter['short_rent']} 家；新增房型 {room_counter} 个，新增库存 {inventory_counter} 条。"))
    if top_cities:
        command.stdout.write(f"城市覆盖（前10）：{top_cities}")
    return None
