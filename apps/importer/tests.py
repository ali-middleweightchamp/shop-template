"""Тесты парсера прайса: кривые цены, наличие, пустые строки, колонки, дубли."""
import io
from decimal import Decimal

import openpyxl
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.catalog.models import Category, Product
from apps.importer import services


def make_xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile("price.xlsx", buf.getvalue())


class ParsePriceTests(TestCase):
    def test_dirty_prices(self):
        self.assertEqual(services.parse_price("12 500 сум"), Decimal("12500"))
        self.assertEqual(services.parse_price("12500,00"), Decimal("12500.00"))
        self.assertEqual(services.parse_price("1 234,50"), Decimal("1234.50"))
        self.assertEqual(services.parse_price("48\xa0500"), Decimal("48500"))

    def test_invalid_price_raises(self):
        for bad in ["абв", "", "—", "по запросу"]:
            with self.assertRaises(ValueError):
                services.parse_price(bad)


class ParseStockTests(TestCase):
    def test_variants(self):
        for v in ["да", "+", "1", "true", "bor", "ha", "Есть"]:
            self.assertTrue(services.parse_stock(v))
        for v in ["нет", "-", "0", "false", "yo'q", "yoq"]:
            self.assertFalse(services.parse_stock(v))

    def test_empty_defaults_true(self):
        self.assertTrue(services.parse_stock(""))


class AnalyzeTests(TestCase):
    def test_missing_required_columns(self):
        f = make_xlsx([["Артикул", "Категория"], ["A1", "Кат"]])
        res = services.analyze(f)
        self.assertIn("Название", res["missing_columns"])
        self.assertIn("Цена", res["missing_columns"])

    def test_empty_rows_skipped(self):
        f = make_xlsx([
            ["Название", "Цена"],
            ["Товар", "1000"],
            ["", ""],
            [None, None],
        ])
        res = services.analyze(f)
        self.assertEqual(res["rows_total"], 1)
        self.assertEqual(res["to_create"], 1)

    def test_broken_row_reported_with_number(self):
        f = make_xlsx([
            ["Название", "Цена"],
            ["Хороший", "1000"],
            ["Плохой", "абв"],
        ])
        res = services.analyze(f)
        self.assertEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["row"], 3)
        self.assertIn("цена", res["errors"][0]["message"].lower())

    def test_headers_case_and_uz_insensitive(self):
        f = make_xlsx([
            ["  АРТИКУЛ ", "nomi", "NARX", "birlik"],
            ["A1", "Товар", "5 000", "dona"],
        ])
        res = services.analyze(f)
        self.assertEqual(res["to_create"], 1)
        self.assertEqual(res["valid"][0]["unit"], "шт")


class ApplyTests(TestCase):
    def test_apply_creates_and_updates(self):
        f = make_xlsx([
            ["Артикул", "Название", "Категория", "Цена", "В наличии"],
            ["A1", "Первый", "Канц", "1000", "да"],
            ["", "Без артикула", "Канц", "2000", "нет"],
        ])
        res = services.apply(f)
        self.assertEqual(res["rows_created"], 2)
        self.assertEqual(res["rows_updated"], 0)
        self.assertTrue(Product.objects.filter(sku="A1").exists())
        # автогенерация артикула
        p = Product.objects.get(name_ru="Без артикула")
        self.assertTrue(p.sku)
        self.assertFalse(p.in_stock)
        # категория создана автоматически
        self.assertTrue(Category.objects.filter(name_ru="Канц").exists())

    def test_reimport_updates_by_sku(self):
        services.apply(make_xlsx([
            ["Артикул", "Название", "Цена"], ["A1", "Товар", "1000"],
        ]))
        res = services.apply(make_xlsx([
            ["Артикул", "Название", "Цена"], ["A1", "Товар изменён", "1500"],
        ]))
        self.assertEqual(res["rows_created"], 0)
        self.assertEqual(res["rows_updated"], 1)
        p = Product.objects.get(sku="A1")
        self.assertEqual(p.price, Decimal("1500"))
        self.assertEqual(Product.objects.filter(sku="A1").count(), 1)
