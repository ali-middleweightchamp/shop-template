"""
Наполняет базу демонстрационными данными: категории, товары (ru/uz),
скидки и «хиты», а также демо-брендинг магазина.

Идемпотентно: товары и категории обновляются по slug/sku, поэтому команду
можно запускать повторно. Флаг --flush предварительно чистит каталог.

    manage.py seed_demo           # добавить/обновить демо-данные
    manage.py seed_demo --flush   # очистить каталог и засеять заново
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product, ProductAttribute
from apps.shopsettings.models import ShopSettings

# --- Категории: (slug, name_ru, name_uz) в порядке отображения ---
CATEGORIES = [
    ("cat-0", "Бумага и блокноты", "Qog‘oz va bloknotlar"),
    ("cat-1", "Ручки и маркеры", "Ruchka va markerlar"),
    ("cat-2", "Клей и скотч", "Yelim va skotch"),
    ("cat-3", "Папки и файлы", "Papka va fayllar"),
    ("cat-4", "Школьные товары", "Maktab tovarlari"),
    ("cat-5", "Офисная техника", "Ofis texnikasi"),
]

# --- Товары ---
# (sku, ru, uz, slug категории, цена, старая цена, ед., в наличии,
#  популярный, новинка, хит продаж)
PRODUCTS = [
    # Бумага и блокноты
    ("BUM-A4-500", "Бумага А4 SvetoCopy 80г, 500л", "A4 SvetoCopy qog‘oz 80g, 500 varaq", "cat-0", 48000, None, "шт", True, True, False, True),
    ("BUM-SC-500", "Бумага офисная A4 «SvetoCopy» 80 г/м², класс C, 500 листов", "A4 ofis qog‘ozi «SvetoCopy» 80 g/m², C klass, 500 varaq", "cat-0", 49000, 70000, "шт", True, True, False, False),
    ("TET-48", "Тетрадь 48л клетка", "Daftar 48 varaq, katak", "cat-0", 3500, None, "шт", True, False, False, False),
    ("TET-96-KLET", "Тетрадь общая 96 л. клетка, обложка мелованный картон", "Umumiy daftar 96 varaq, katak", "cat-0", 14500, 16500, "шт", True, True, False, False),
    ("BLK-A5-60", "Блокнот на пружине A5, 60л", "Prujinali bloknot A5, 60 varaq", "cat-0", 12500, None, "шт", True, False, True, False),
    ("BUM-A4-COL", "Бумага цветная A4, 100 листов, 5 цветов", "Rangli qog‘oz A4, 100 varaq, 5 rang", "cat-0", 32000, None, "упак", True, False, True, False),
    ("STIK-76", "Стикеры клейкие 76×76 мм, 100 листов", "Yopishqoq stikerlar 76×76 mm, 100 varaq", "cat-0", 6500, None, "упак", True, False, True, False),
    # Ручки и маркеры
    ("RCH-SIN-50", "Ручка шариковая синяя (уп. 50шт)", "Ko‘k sharikli ruchka (50 dona o‘ram)", "cat-1", 65000, None, "упак", True, False, False, True),
    ("RCH-AVT-50", "Ручка шариковая автоматическая синяя 0.7 мм (кор. 50 шт.)", "Avtomatik ko‘k sharikli ruchka 0.7 mm (50 dona quti)", "cat-1", 72000, 85000, "упак", True, True, False, False),
    ("MRK-BLK", "Маркер перманентный чёрный", "Qora doimiy marker", "cat-1", 6000, None, "шт", True, False, False, False),
    ("MRK-BOARD-4", "Набор маркеров для белой доски 4 цвета", "Oq doska uchun markerlar to‘plami 4 rang", "cat-1", 38000, None, "упак", True, True, True, False),
    ("TXT-YEL", "Текстовыделитель жёлтый", "Sariq matn ajratgich", "cat-1", 4200, None, "шт", True, False, False, False),
    ("RCH-GEL-12", "Ручка гелевая синяя 0.5 мм (уп. 12 шт)", "Gel ruchka ko‘k 0.5 mm (12 dona)", "cat-1", 24000, None, "упак", True, False, False, True),
    ("KAR-CH-12", "Карандаш чернографитный HB (уп. 12 шт)", "Oddiy qalam HB (12 dona)", "cat-1", 18000, None, "упак", True, False, False, True),
    ("MRK-4-NEON", "Набор текстовыделителей 4 цвета, неон", "Matn ajratgichlar to‘plami 4 rang, neon", "cat-1", 21000, 25000, "упак", True, False, True, False),
    # Клей и скотч
    ("KLY-21", "Клей-карандаш 21г", "Yelim-qalam 21g", "cat-2", 3800, None, "упак", True, False, False, False),
    ("KLY-21G", "Клей-карандаш 21 г, быстросохнущий, без запаха", "Yelim-qalam 21 g, tez quriydigan, hidsiz", "cat-2", 4200, None, "шт", False, False, False, False),
    ("SKT-48", "Скотч упаковочный 48мм×100м", "Qadoqlash skotchi 48mm×100m", "cat-2", 9500, None, "шт", True, False, False, True),
    ("KLY-PVA", "Клей ПВА 85 мл", "PVA yelim 85 ml", "cat-2", 5200, None, "шт", True, False, False, False),
    ("SKT-MAL", "Скотч малярный 48мм×40м", "Bo‘yoq skotchi 48mm×40m", "cat-2", 11000, None, "шт", True, False, True, False),
    # Папки и файлы
    ("PAP-SK", "Папка-скоросшиватель A4", "Papka-tikuvchi A4", "cat-3", 2100, None, "шт", True, False, False, False),
    ("PAP-REG-75", "Папка-регистратор А4 75 мм, ламинированный картон", "Papka-registrator A4 75 mm, laminatlangan karton", "cat-3", 23500, None, "шт", True, False, False, False),
    ("FIL-100", "Файл-вкладыш A4 (уп. 100шт)", "Fayl-qo‘shimcha A4 (100 dona o‘ram)", "cat-3", 28000, None, "упак", True, False, False, False),
    ("PAP-PL-20", "Папка с файлами, 20 вкладышей", "Fayllar bilan papka, 20 ta", "cat-3", 16000, None, "шт", True, False, False, False),
    ("PAP-KON", "Папка-конверт на кнопке A4", "Papka-konvert tugmali A4", "cat-3", 4500, None, "шт", True, False, True, False),
    # Школьные товары
    ("PEN-01", "Пенал school", "Penal school", "cat-4", 18000, None, "шт", True, False, True, False),
    ("KAR-12", "Набор цветных карандашей 12шт", "Rangli qalamlar to‘plami 12 dona", "cat-4", 14500, None, "упак", True, False, False, True),
    ("KRSK-12", "Краски акварельные, 12 цветов", "Akvarel bo‘yoqlar, 12 rang", "cat-4", 16500, None, "упак", True, False, False, True),
    ("PLAST-12", "Пластилин, 12 цветов", "Plastilin, 12 rang", "cat-4", 13000, 15000, "упак", True, False, True, False),
    ("RUK-40", "Рюкзак школьный, 40 л", "Maktab ryukzagi, 40 l", "cat-4", 185000, 220000, "шт", True, True, False, True),
    ("PENAL-2", "Пенал на 2 отделения", "2 bo‘limli penal", "cat-4", 26000, None, "шт", True, False, True, False),
    # Офисная техника
    ("KAL-12", "Калькулятор настольный 12р", "Stol kalkulyatori 12 razryad", "cat-5", 42000, 48000, "упак", True, True, False, True),
    ("STP-24", "Степлер №24", "Stepler №24", "cat-5", 15000, None, "шт", True, False, False, True),
    ("DYR-24", "Дырокол на 24 листа", "24 varaqli teshgich", "cat-5", 34000, None, "шт", True, False, False, False),
    ("NOZH-18", "Нож канцелярский 18 мм", "Kanselyariya pichog‘i 18 mm", "cat-5", 4800, None, "шт", True, False, True, False),
]

# --- Характеристики (демо) для части товаров: sku → [(название, значение), ...] ---
SPECS = {
    "BUM-A4-500": [("Бренд", "SvetoCopy"), ("Страна производства", "Россия"), ("Формат", "A4"), ("Плотность", "80 г/м²")],
    "MRK-4-NEON": [("Бренд", "Erich Krause"), ("Страна производства", "Россия"), ("Количество цветов", "4"), ("Тип упаковки", "упак")],
    "RCH-GEL-12": [("Бренд", "Erich Krause"), ("Цвет чернил", "Синий"), ("Толщина линии", "0.5 мм"), ("Страна производства", "Россия")],
    "KAL-12": [("Бренд", "Citizen"), ("Страна производства", "Япония"), ("Разрядность", "12"), ("Питание", "Батарея + солнечная")],
    "RUK-40": [("Бренд", "Deli"), ("Объём", "40 л"), ("Материал", "Полиэстер"), ("Возраст", "7+")],
    "KRSK-12": [("Бренд", "Гамма"), ("Количество цветов", "12"), ("Тип", "Акварель медовая")],
}

# --- Описания (демо) для части товаров: sku → (ru, uz) ---
DESCRIPTIONS = {
    "BUM-A4-500": (
        "Офисная бумага формата A4, плотность 80 г/м². Подходит для печати, "
        "копирования и факса. Белизна CIE 146%, не застревает в принтере. "
        "В пачке 500 листов.",
        "A4 formatidagi ofis qog‘ozi, zichligi 80 g/m². Chop etish, nusxa "
        "ko‘chirish va faks uchun mos. Bir pachkada 500 varaq.",
    ),
    "MRK-4-NEON": (
        "Набор текстовыделителей из 4 неоновых цветов со скошенным наконечником. "
        "Ширина линии 1–5 мм. Яркие чернила на водной основе не просвечивают бумагу.",
        "4 ta neon rangdagi matn ajratgichlar to‘plami, qiya uchli. Chiziq kengligi "
        "1–5 mm. Yorqin suv asosidagi siyoh qog‘ozdan o‘tmaydi.",
    ),
    "RUK-40": (
        "Вместительный школьный рюкзак объёмом 40 литров. Ортопедическая спинка, "
        "два основных отделения, боковые карманы. Прочная водоотталкивающая ткань.",
        "40 litrli sig‘imli maktab ryukzagi. Ortopedik orqa qismi, ikkita asosiy "
        "bo‘lim, yon cho‘ntaklar. Mustahkam suv o‘tkazmaydigan mato.",
    ),
    "KAL-12": (
        "Настольный калькулятор с 12-разрядным дисплеем. Двойное питание: батарея "
        "и солнечная панель. Крупные кнопки, функции расчёта наценки и процентов.",
        "12 razryadli displeyli stol kalkulyatori. Ikki tomonlama quvvat: batareya "
        "va quyosh paneli. Yirik tugmalar, foiz hisoblash funksiyasi.",
    ),
}

# Демо-брендинг применяем только к «пустому» магазину, чтобы не затирать
# реальные настройки владельца.
DEMO_SHOP = {
    "name_ru": "Канцтовары", "name_uz": "Kanstovarlar",
    "tagline_ru": "Всё для учёбы и офиса", "tagline_uz": "O'qish va ofis uchun hammasi",
    "description_ru": "Канцтовары и офисная бумага оптом в Ташкенте. Доставка по городу, заказ в один клик через Telegram.",
    "description_uz": "Toshkentda ulgurji kantstovarlar va ofis qog‘ozi. Shahar bo‘ylab yetkazib berish, Telegram orqali bir bosishda buyurtma.",
    "telegram_username": "kanstik_opt", "whatsapp_phone": "998712004040",
    "instagram_url": "https://instagram.com/kanstik_opt",
    "phone": "+998 71 200 40 40",
    "currency_label_ru": "сум", "currency_label_uz": "so‘m",
    "address_ru": "Ташкент, Чиланзар, рынок «Абу-Сахий», ряд 12",
    "work_hours_ru": "Пн–Сб 9:00–18:00",
    "order_message_header_ru": "Здравствуйте! Хочу заказать:",
    "min_order_amount": Decimal("200000.00"),
}


# ======================================================================
# Пресеты других ниш (шаблон универсален — канцтовары лишь дефолт).
# Компактные наборы, чтобы показать вертикаль. Структура товара та же:
# (sku, ru, uz, slug, цена, старая, ед., в наличии, популярное, новинка, хит)
# ======================================================================

TOYS_CATS = [
    ("toy-0", "Конструкторы", "Konstruktorlar"),
    ("toy-1", "Куклы", "Qo‘g‘irchoqlar"),
    ("toy-2", "Машинки", "Mashinalar"),
    ("toy-3", "Настольные игры", "Stol o‘yinlari"),
    ("toy-4", "Мягкие игрушки", "Yumshoq o‘yinchoqlar"),
]
TOYS_PRODUCTS = [
    ("TOY-CON-60", "Конструктор «Город», 60 деталей", "«Shahar» konstruktori, 60 detal", "toy-0", 120000, None, "набор", True, True, False, True),
    ("TOY-CON-90", "Конструктор «Космос», 90 деталей", "«Kosmos» konstruktori, 90 detal", "toy-0", 185000, 220000, "набор", True, False, True, False),
    ("TOY-DOLL-1", "Кукла «Принцесса», 30 см", "«Malika» qo‘g‘irchoq, 30 sm", "toy-1", 95000, None, "шт", True, True, False, False),
    ("TOY-DOLL-2", "Пупс интерактивный", "Interaktiv chaqaloq qo‘g‘irchoq", "toy-1", 145000, 175000, "шт", True, False, True, False),
    ("TOY-CAR-1", "Машинка гоночная инерционная", "Inertsion poyga mashinasi", "toy-2", 38000, None, "шт", True, False, False, True),
    ("TOY-CAR-2", "Грузовик-самосвал большой", "Katta samosval yuk mashinasi", "toy-2", 72000, None, "шт", True, True, False, False),
    ("TOY-GAME-1", "Настольная игра «Монополия»", "«Monopoliya» stol o‘yini", "toy-3", 110000, None, "набор", True, False, True, True),
    ("TOY-GAME-2", "Карточная игра UNO", "UNO kartochka o‘yini", "toy-3", 28000, 35000, "набор", True, False, False, False),
    ("TOY-PLU-1", "Мягкий медведь, 40 см", "Yumshoq ayiq, 40 sm", "toy-4", 85000, None, "шт", True, True, False, False),
    ("TOY-PLU-2", "Мягкий котик, 25 см", "Yumshoq mushukcha, 25 sm", "toy-4", 55000, None, "шт", True, False, True, False),
]
TOYS_SHOP = {
    "name_ru": "Мир игрушек", "name_uz": "O‘yinchoqlar olami",
    "tagline_ru": "Радость для детей каждый день", "tagline_uz": "Bolalarga har kuni quvonch",
    "description_ru": "Игрушки для детей всех возрастов в Ташкенте. Доставка по городу, заказ через Telegram.",
    "description_uz": "Toshkentda barcha yoshdagi bolalar uchun o‘yinchoqlar. Telegram orqali buyurtma.",
    "telegram_username": "toys_demo", "whatsapp_phone": "998900000001",
    "currency_label_ru": "сум", "currency_label_uz": "so‘m",
    "order_message_header_ru": "Здравствуйте! Хочу заказать игрушки:",
    "min_order_amount": Decimal("100000.00"),
}

EL_CATS = [
    ("el-0", "Смартфоны", "Smartfonlar"),
    ("el-1", "Наушники", "Quloqchinlar"),
    ("el-2", "Аксессуары", "Aksessuarlar"),
    ("el-3", "Зарядки и кабели", "Quvvatlagich va kabellar"),
    ("el-4", "Умный дом", "Aqlli uy"),
]
EL_PRODUCTS = [
    ("EL-PHN-1", "Смартфон Galaxy A15, 128 ГБ", "Galaxy A15 smartfon, 128 GB", "el-0", 2450000, 2700000, "шт", True, True, False, True),
    ("EL-PHN-2", "Смартфон Redmi Note 13, 256 ГБ", "Redmi Note 13 smartfon, 256 GB", "el-0", 2890000, None, "шт", True, True, False, False),
    ("EL-EAR-1", "Наушники TWS беспроводные", "Simsiz TWS quloqchin", "el-1", 320000, 390000, "шт", True, False, True, True),
    ("EL-EAR-2", "Наушники проводные с микрофоном", "Mikrofonli simli quloqchin", "el-1", 65000, None, "шт", True, False, False, False),
    ("EL-ACC-1", "Чехол силиконовый прозрачный", "Shaffof silikon g‘ilof", "el-2", 35000, None, "шт", True, False, False, True),
    ("EL-ACC-2", "Защитное стекло 9H", "9H himoya oynasi", "el-2", 25000, None, "шт", True, True, False, False),
    ("EL-CHG-1", "Зарядное устройство 65 Вт", "65 Vt quvvatlagich", "el-3", 145000, None, "шт", True, False, True, False),
    ("EL-CBL-1", "Кабель USB-C, 1 м", "USB-C kabel, 1 m", "el-3", 28000, 35000, "шт", True, False, False, False),
    ("EL-SMH-1", "Умная лампа RGB", "Aqlli RGB lampa", "el-4", 95000, None, "шт", True, True, False, False),
    ("EL-SMH-2", "Умная розетка Wi-Fi", "Aqlli Wi-Fi rozetka", "el-4", 120000, None, "шт", True, False, True, False),
]
EL_SHOP = {
    "name_ru": "ТехноМаркет", "name_uz": "TexnoMarket",
    "tagline_ru": "Гаджеты и электроника по честным ценам", "tagline_uz": "Halol narxlarda gadjet va elektronika",
    "description_ru": "Смартфоны, аксессуары и умный дом в Ташкенте. Гарантия, доставка, заказ через Telegram.",
    "description_uz": "Toshkentda smartfon, aksessuar va aqlli uy. Kafolat, yetkazib berish, Telegram orqali buyurtma.",
    "telegram_username": "techno_demo", "whatsapp_phone": "998900000002",
    "currency_label_ru": "сум", "currency_label_uz": "so‘m",
    "order_message_header_ru": "Здравствуйте! Интересует техника:",
    "min_order_amount": Decimal("0.00"),
}

PF_CATS = [
    ("pf-0", "Мужская парфюмерия", "Erkaklar parfyumeriyasi"),
    ("pf-1", "Женская парфюмерия", "Ayollar parfyumeriyasi"),
    ("pf-2", "Унисекс", "Uniseks"),
    ("pf-3", "Наборы", "To‘plamlar"),
    ("pf-4", "Миниатюры", "Miniaturalar"),
]
PF_PRODUCTS = [
    ("PF-M-1", "Dior Sauvage EDT, 100 мл", "Dior Sauvage EDT, 100 ml", "pf-0", 980000, None, "шт", True, True, False, True),
    ("PF-M-2", "Hugo Boss Bottled, 100 мл", "Hugo Boss Bottled, 100 ml", "pf-0", 720000, 850000, "шт", True, False, True, False),
    ("PF-W-1", "Chanel Chance EDP, 50 мл", "Chanel Chance EDP, 50 ml", "pf-1", 1250000, None, "шт", True, True, False, True),
    ("PF-W-2", "Lancôme La Vie Est Belle, 75 мл", "Lancôme La Vie Est Belle, 75 ml", "pf-1", 1150000, None, "шт", True, False, True, False),
    ("PF-U-1", "Tom Ford Oud Wood, 50 мл", "Tom Ford Oud Wood, 50 ml", "pf-2", 1800000, None, "шт", True, True, False, False),
    ("PF-U-2", "CK One EDT, 100 мл", "CK One EDT, 100 ml", "pf-2", 420000, 490000, "шт", True, False, False, True),
    ("PF-SET-1", "Подарочный набор мужской", "Erkaklar sovg‘a to‘plami", "pf-3", 560000, None, "набор", True, False, True, False),
    ("PF-SET-2", "Подарочный набор женский", "Ayollar sovg‘a to‘plami", "pf-3", 620000, 720000, "набор", True, True, False, False),
    ("PF-MIN-1", "Миниатюра мужская, 10 мл", "Erkaklar miniaturasi, 10 ml", "pf-4", 120000, None, "шт", True, False, True, False),
    ("PF-MIN-2", "Миниатюра женская, 10 мл", "Ayollar miniaturasi, 10 ml", "pf-4", 130000, None, "шт", True, False, False, False),
]
PF_SHOP = {
    "name_ru": "Парфюм-Холл", "name_uz": "Parfyum Hall",
    "tagline_ru": "Оригинальная парфюмерия", "tagline_uz": "Original parfyumeriya",
    "description_ru": "Оригинальные ароматы для него и для неё в Ташкенте. Заказ через Telegram.",
    "description_uz": "Toshkentda u va u uchun original хушбo‘y hidlar. Telegram orqali buyurtma.",
    "telegram_username": "parfum_demo", "whatsapp_phone": "998900000003",
    "currency_label_ru": "сум", "currency_label_uz": "so‘m",
    "order_message_header_ru": "Здравствуйте! Хочу заказать парфюм:",
    "min_order_amount": Decimal("0.00"),
}

PRESETS = {
    "stationery": {"categories": CATEGORIES, "products": PRODUCTS, "specs": SPECS, "descriptions": DESCRIPTIONS, "shop": DEMO_SHOP},
    "toys": {"categories": TOYS_CATS, "products": TOYS_PRODUCTS, "specs": {}, "descriptions": {}, "shop": TOYS_SHOP},
    "electronics": {"categories": EL_CATS, "products": EL_PRODUCTS, "specs": {}, "descriptions": {}, "shop": EL_SHOP},
    "perfume": {"categories": PF_CATS, "products": PF_PRODUCTS, "specs": {}, "descriptions": {}, "shop": PF_SHOP},
}


class Command(BaseCommand):
    help = "Наполняет базу демо-данными выбранной ниши (по умолчанию канцтовары)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true",
            help="Удалить все категории и товары перед наполнением.",
        )
        parser.add_argument(
            "--preset", default="stationery", choices=list(PRESETS.keys()),
            help="Ниша демо-данных: stationery (по умолчанию), toys, electronics, perfume.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        preset = PRESETS[options["preset"]]
        categories_data = preset["categories"]
        products_data = preset["products"]
        specs_data = preset["specs"]
        descriptions_data = preset["descriptions"]
        shop_data = preset["shop"]

        if options["flush"]:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Каталог очищен (--flush)."))

        # --- Категории ---
        cats = {}
        for order, (slug, ru, uz) in enumerate(categories_data):
            cat, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": ru, "name_ru": ru, "name_uz": uz, "order": order, "is_active": True},
            )
            cats[slug] = cat

        # --- Товары ---
        for order, row in enumerate(products_data):
            sku, ru, uz, cat_slug, price, old, unit, in_stock, featured, is_new, best = row
            desc_ru, desc_uz = descriptions_data.get(sku, ("", ""))
            product, _created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": ru, "name_ru": ru, "name_uz": uz,
                    "description": desc_ru, "description_ru": desc_ru, "description_uz": desc_uz,
                    "category": cats[cat_slug],
                    "price": Decimal(price),
                    "old_price": Decimal(old) if old else None,
                    "unit": unit,
                    "in_stock": in_stock,
                    "is_active": True,
                    "is_featured": featured,
                    "is_new": is_new,
                    "is_bestseller": best,
                    "order": order,
                },
            )
            # Характеристики: пересоздаём, чтобы команда оставалась идемпотентной
            if sku in specs_data:
                product.attributes.all().delete()
                for i, (name, value) in enumerate(specs_data[sku]):
                    ProductAttribute.objects.create(product=product, name=name, value=value, order=i)

        # --- Демо-брендинг (только если магазин ещё не настроен) ---
        shop = ShopSettings.get_solo()
        # Признак «магазин ещё не настроен» — не указан Telegram (обязательное поле
        # для реального магазина). Имя имеет дефолт из миграции, поэтому по нему нельзя.
        if not (shop.telegram_username or "").strip():
            for field, value in shop_data.items():
                setattr(shop, field, value)
            shop.save()
            self.stdout.write(self.style.SUCCESS("Демо-брендинг магазина применён."))
        else:
            self.stdout.write("Магазин уже настроен — брендинг не трогаю.")

        self.stdout.write(self.style.SUCCESS(
            f"Готово: {Category.objects.count()} категорий, {Product.objects.count()} товаров."
        ))
