from django.test import TestCase
from django.utils.dateparse import parse_datetime

from api.models import Company, Category
from api.serializers.category import CategorySerializer


class CategorySerializerTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="A社")
        self.company_b = Company.objects.create(name="B社")

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
        self.root_category_b = Category.objects.create(
            company=self.company_b,
            name="B社の親カテゴリ",
            parent_category=None,
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

    def test_create_ok_parent_null(self):
        data = {
            "company": self.company.id,
            "name": "新規カテゴリ",
            "parent_category": None,
        }
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        obj = serializer.save()
        self.assertEqual(obj.company_id, self.company.id)
        self.assertEqual(obj.name, "新規カテゴリ")
        self.assertIsNone(obj.parent_category)

    def test_create_ok_parent_same_company(self):
        data = {
            "company": self.company.id,
            "name": "A社の子カテゴリ",
            "parent_category": self.root_category.id,
        }
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        obj = serializer.save()
        self.assertEqual(obj.parent_category_id, self.root_category.id)

    def test_create_ng_parent_different_company(self):
        data = {
            "company": self.company.id,
            "name": "他社親はNG",
            "parent_category": self.root_category_b.id,  # B社のカテゴリを親に指定
        }
        serializer = CategorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("parent_category", serializer.errors)

    def test_create_ng_unique_company_name_duplicate(self):
        data = {
            "company": self.company.id,
            "name": "子カテゴリ",
            "parent_category": None,
        }
        serializer = CategorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_create_ok_same_name_different_company(self):
        # A社にある名前でも、B社ならOK（ユニークは company + name）
        data = {
            "company": self.company_b.id,
            "name": "子カテゴリ",
            "parent_category": None,
        }
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_ng_different_company(self):
        instance = self.root_category
        data = {
            "company": self.company_b.id,
        }
        serializer = CategorySerializer(instance=instance, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("company", serializer.errors)

    def test_update_ng_parent_different_company(self):
        instance = self.child_category
        data = {
            "parent_category": self.root_category_b.id,  # B社のカテゴリを親に指定
        }
        serializer = CategorySerializer(instance=instance, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("parent_category", serializer.errors)

    def test_update_ok_same_values_on_self(self):
        # 既存の値のまま更新（自分自身は除外されるのでOK）
        instance = self.root_category
        data = {"name": "親カテゴリ"}  # 同名だが自分自身
        serializer = CategorySerializer(instance=instance, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_ng_unique_company_name_duplicate_excluding_self(self):
        # name を更新するとA社内で衝突する
        instance = self.child_category
        data = {"name": "親カテゴリ"}
        serializer = CategorySerializer(instance=instance, data=data, partial=True)

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_update_ng_parent_is_self(self):
        # 子カテゴリの親を自分自身にするのはNG
        instance = self.child_category
        data = {"parent_category": instance.id}
        serializer = CategorySerializer(instance=instance, data=data, partial=True)

        self.assertFalse(serializer.is_valid())
        self.assertIn("parent_category", serializer.errors)

    def test_update_ng_parent_is_ancestor(self):
        # 親カテゴリの親を子カテゴリにするのはNG
        instance = self.root_category
        data = {"parent_category": self.child_category.id}
        serializer = CategorySerializer(instance=instance, data=data, partial=True)

        self.assertFalse(serializer.is_valid())
        self.assertIn("parent_category", serializer.errors)
