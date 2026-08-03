"""
Обработка загружаемых изображений для панели.

Правила жёсткие и проверяются при загрузке: JPG/PNG/WebP, до 5 МБ, минимум по
стороне. При сохранении картинка обрезается по центру до нужной пропорции,
ужимается и конвертируется в WebP. Оригинал не хранится.
"""
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_BYTES = 5 * 1024 * 1024
_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image(f, min_side=600):
    """Проверяет формат, вес и минимальный размер. Кидает ValidationError."""
    if f.size > MAX_BYTES:
        raise ValidationError("Файл больше 5 МБ. Сожмите изображение.")
    try:
        img = Image.open(f)
        img.verify()  # быстрая проверка, что файл — картинка
    except Exception:
        raise ValidationError("Не удалось прочитать изображение.")
    f.seek(0)
    img = Image.open(f)
    if img.format not in _FORMATS:
        raise ValidationError("Только JPG, PNG или WebP.")
    w, h = img.size
    if min(w, h) < min_side:
        raise ValidationError(f"Минимальный размер — {min_side}×{min_side}px.")
    f.seek(0)


def process_image(f, ratio=(1, 1), width=1000, name="image"):
    """Центр-кроп до пропорции ratio, ужатие до width по ширине, WebP.

    Возвращает ContentFile (<name>.webp). Оригинал не сохраняется.
    """
    img = Image.open(f)
    img = ImageOps.exif_transpose(img)  # учесть поворот из EXIF
    if img.mode not in ("RGB",):
        img = img.convert("RGB")

    target = ratio[0] / ratio[1]
    w, h = img.size
    cur = w / h
    if cur > target:  # слишком широкое — режем по бокам
        new_w = int(h * target)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif cur < target:  # слишком высокое — режем сверху/снизу
        new_h = int(w / target)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    if img.width > width:
        img = img.resize((width, int(width / target)), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, "WEBP", quality=82, method=4)
    buf.seek(0)
    return ContentFile(buf.read(), name=f"{name}.webp")
