from django.test import TestCase
from django.utils.dateparse import parse_datetime

from api.models import Company, Category
from api.serializers.category import CategorySerializer


class CategorySerializerTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="A社")

        self.root_category = Category.objects.create(
            company=self.company,
            name="親カテゴリ",
            parent_category=None,
        )
        self.child_category = Category.objects.create(
            company=self.company,
            name="子カテゴリ",
            parent_category=self.root_category,
        )

    def _assert_iso_datetime_string(self, value):
        # DRFのDateTimeFieldは通常 ISO8601 文字列を返す
        self.assertIsInstance(value, str)
        # parseできることだけ確認（タイムゾーンの有無などは設定で変わるため）
        dt = parse_datetime(value)
        self.assertIsNotNone(dt, f"Invalid datetime string: {value}")

    def test_serialized_keys(self):
        serializer = CategorySerializer(instance=self.root_category)
        data = serializer.data

        expected_keys = {
            "id",
            "company",
            "name",
            "parent_category",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(data.keys()), expected_keys)

    def test_serialize_root_category(self):
        serializer = CategorySerializer(instance=self.root_category)
        data = serializer.data

        self.assertEqual(data["id"], str(self.root_category.id))
        self.assertEqual(str(data["company"]), str(self.company.id))
        self.assertEqual(data["name"], "親カテゴリ")
        self.assertIsNone(data["parent_category"])
        self._assert_iso_datetime_string(data["created_at"])
        self._assert_iso_datetime_string(data["updated_at"])

    def test_serialize_child_category(self):
        serializer = CategorySerializer(instance=self.child_category)
        data = serializer.data

        self.assertEqual(data["id"], str(self.child_category.id))
        self.assertEqual(str(data["company"]), str(self.company.id))
        self.assertEqual(data["name"], "子カテゴリ")
        self.assertEqual(str(data["parent_category"]), str(self.root_category.id))
        self._assert_iso_datetime_string(data["created_at"])
        self._assert_iso_datetime_string(data["updated_at"])

    def test_serialize_many(self):
        qs = Category.objects.filter(company=self.company).order_by("name")
        serializer = CategorySerializer(instance=qs, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)

        expected_ids = {
            str(self.root_category.id),
            str(self.child_category.id),
        }
        self.assertEqual({d["id"] for d in data}, expected_ids)
