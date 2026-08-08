"""
Наполнение демо-каталога реальными тематическими фото из Wikimedia Commons.

Wikimedia — свободная лицензия (CC/PD), без API-ключа и водяных знаков. Команда
подбирает фото по ключевым словам названия товара/категории, прогоняет через
общий пайплайн обработки (центр-кроп → WebP) и проставляет в модель.

Это инструмент ДЛЯ ДЕМО (наполнить витрину для показа клиенту). В боевом
магазине продавец грузит свои фото через панель.

    python manage.py fetch_demo_images                # только у кого нет фото
    python manage.py fetch_demo_images --all          # перезалить всё
    python manage.py fetch_demo_images --categories    # только категории
    python manage.py fetch_demo_images --products      # только товары
"""
import time
import urllib.parse
import urllib.request
from io import BytesIO

from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product
from apps.panel.imaging import process_image

WIKI_API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia требует описательный User-Agent с контактом, иначе 429/robot policy.
UA = "shop-template-demo/1.0 (https://example.com; contact aliyuuuyu@gmail.com) Python-urllib"

# Слова в названии файла, по которым фото точно не про канцелярию (ложные срабатывания).
TITLE_REJECT = (
    ".svg", ".png", ".gif", "logo", "icon", "map", "diagram", "chart",
    "coat_of_arms", "olympic", "_ring", "ring_", "flag", "sport", "medal",
    "portrait", "person", "people", "woman", "man_", "child", "military",
    # мусор, пойманный на канцелярии: реклама, книги, письма, рендеры, каталоги
    "poster", "advert", "brand", "brieven", "envelope", "letter", "post_",
    "render", "game", "interior", "room", "catalog", "book_", "_book",
    "manuscript", "vintage", "1900", "19th", "18th", "engraving",
)

# Ключевое слово в названии (нижний регистр) → поисковый запрос к Wikimedia.
# Порядок важен: первое совпадение выигрывает, поэтому уточнения идут раньше общих.
PRODUCT_QUERIES = [
    # клей — РАНЬШЕ карандаша, иначе «клей-карандаш» ловит pencil
    ("клей-каранд", "glue stick"),
    ("клей пва", "pva glue bottle"),
    ("клей", "glue stick"),
    ("бумага цветн", "colored construction paper"),
    ("цветная a4", "colored construction paper"),
    ("стикер", "sticky notes"),
    ("бумага", "printer paper ream"),
    ("тетрад", "spiral notebook blank"),
    ("блокнот", "spiral notebook blank"),
    ("текстовыдел", "highlighter pen"),
    ("маркер для белой", "whiteboard marker"),
    ("набор маркер", "colored marker pens"),
    ("маркер", "marker pen"),
    ("ручка гел", "gel pen"),
    ("ручка", "ballpoint pen"),
    ("цветных каранд", "colored pencils"),
    ("цветные каранд", "colored pencils"),
    ("карандаш", "wooden pencil"),
    ("скотч малярн", "masking tape"),
    ("скотч", "adhesive tape roll"),
    ("папка-регистр", "lever arch file"),
    ("папка-конверт", "plastic document wallet"),
    ("папка с файл", "ring binder documents"),
    ("папка", "document folder"),
    ("файл", "sheet protector documents"),
    ("пенал", "pencil case"),
    ("краски акварел", "watercolor paint set"),
    ("пластилин", "colorful modeling clay"),
    ("рюкзак", "school backpack"),
    ("калькулятор", "desktop calculator"),
    ("степлер", "office stapler"),
    ("дырокол", "hole punch office"),
    ("нож канцеляр", "utility knife cutter"),
]

# Запрос для обложки категории (по русскому названию, нормализованному).
CATEGORY_QUERIES = {
    "бумага": "stack of white paper",
    "тетради и блокноты": "school exercise books",
    "ручки и маркеры": "colorful pens",
    "клей и скотч": "adhesive tape rolls",
    "папки и файлы": "lever arch files shelf",
    "школьные товары": "school supplies desk",
    "офисная техника": "stapler office",
}

FALLBACK_QUERY = "office stationery"


def _norm(s):
    return (s or "").strip().lower().rstrip(":").strip()


def wiki_search(query, limit=6):
    """Вернуть список URL пригодных фото (JPEG, не мелкие) по запросу."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",          # только файлы
        "gsrlimit": str(limit * 3),   # с запасом — часть отсеем
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": "1200",
        "format": "json",
    }
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    import json

    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.load(r)
    pages = (data.get("query") or {}).get("pages") or {}
    # сохраняем порядок релевантности из поиска
    ordered = sorted(pages.values(), key=lambda p: p.get("index", 999))
    out = []
    for p in ordered:
        title = (p.get("title") or "").lower()
        # отсекаем заведомо непродуктовые файлы
        if any(bad in title for bad in TITLE_REJECT):
            continue
        info = (p.get("imageinfo") or [{}])[0]
        if info.get("mime") != "image/jpeg":
            continue
        if (info.get("width") or 0) < 600 or (info.get("height") or 0) < 500:
            continue
        thumb = info.get("thumburl")
        if thumb:
            out.append(thumb)
        if len(out) >= limit:
            break
    return out


def fetch_bytes(url):
    # upload.wikimedia.org строг к ботам: пауза + описательный UA обязательны.
    time.sleep(1.1)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://commons.wikimedia.org/"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


class Command(BaseCommand):
    help = "Наполнить демо-каталог тематическими фото из Wikimedia Commons"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="перезалить даже там, где фото уже есть")
        parser.add_argument("--categories", action="store_true", help="только категории")
        parser.add_argument("--products", action="store_true", help="только товары")

    def handle(self, *args, **opts):
        do_cat = opts["categories"] or not opts["products"]
        do_prod = opts["products"] or not opts["categories"]
        replace = opts["all"]
        # пул скачанных картинок по запросу, чтобы не дёргать одно и то же дважды
        pool = {}
        used = set()

        def pick(query, ratio, width, name, avoid_dupes=True):
            """Скачать и обработать одно фото по запросу. None — если не нашли."""
            if query not in pool:
                pool[query] = wiki_search(query)
                time.sleep(0.4)  # вежливо к API
            for thumb in pool[query]:
                if avoid_dupes and thumb in used:
                    continue
                try:
                    raw = fetch_bytes(thumb)
                except Exception as e:
                    self.stderr.write(f"  скачать не вышло: {e}")
                    continue
                used.add(thumb)
                return process_image(BytesIO(raw), ratio=ratio, width=width, name=name)
            return None

        if do_cat:
            for c in Category.objects.all():
                if c.image and not replace:
                    continue
                q = CATEGORY_QUERIES.get(_norm(c.name_ru), FALLBACK_QUERY)
                cf = pick(q, ratio=(4, 3), width=1000, name=f"cat_{c.pk}")
                if cf:
                    c.image.save(cf.name, cf, save=True)
                    self.stdout.write(self.style.SUCCESS(f"CAT «{c.name_ru}» ← {q}"))
                else:
                    self.stderr.write(f"CAT «{c.name_ru}»: фото не найдено ({q})")

        if do_prod:
            for p in Product.objects.all():
                if p.image and not replace:
                    continue
                name = _norm(p.name_ru)
                q = next((query for kw, query in PRODUCT_QUERIES if kw in name), None)
                if q is None and p.category_id:
                    q = CATEGORY_QUERIES.get(_norm(p.category.name_ru), FALLBACK_QUERY)
                q = q or FALLBACK_QUERY
                cf = pick(q, ratio=(1, 1), width=900, name=f"prod_{p.pk}")
                if cf:
                    p.image.save(cf.name, cf, save=True)
                    self.stdout.write(self.style.SUCCESS(f"  «{p.name_ru}» ← {q}"))
                else:
                    self.stderr.write(f"  «{p.name_ru}»: фото не найдено ({q})")
