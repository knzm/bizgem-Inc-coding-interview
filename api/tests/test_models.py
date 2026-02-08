import time

from django.db import IntegrityError
from django.test import TestCase

from api.models import Company, Category


class CategoryModelTest(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="A社")
        self.company_b = Company.objects.create(name="B社")

    def test_create_category_uuid_pk(self):
        cat = Category.objects.create(company=self.company_a, name="営業", parent_category=None)
        self.assertIsNotNone(cat.id)
        self.assertEqual(len(str(cat.id)), 36)

    def test_parent_category_can_be_null(self):
        cat = Category.objects.create(company=self.company_a, name="ルート", parent_category=None)
        self.assertIsNone(cat.parent_category)

    def test_unique_constraint_company_and_name_duplicate_raises_integrity_error(self):
        Category.objects.create(company=self.company_a, name="営業", parent_category=None)

        with self.assertRaises(IntegrityError):
            Category.objects.create(company=self.company_a, name="営業", parent_category=None)

    def test_unique_constraint_allows_same_name_in_different_company(self):
        Category.objects.create(company=self.company_a, name="営業", parent_category=None)
        Category.objects.create(company=self.company_b, name="営業", parent_category=None)

        self.assertEqual(Category.objects.filter(name="営業").count(), 2)

    def test_created_at_is_not_changed_on_save(self):
        cat = Category.objects.create(company=self.company_a, name="営業", parent_category=None)
        created_before = cat.created_at

        time.sleep(0.01)

        cat.name = "営業(更新)"
        cat.save()
        cat.refresh_from_db()

        self.assertEqual(cat.created_at, created_before)

    def test_updated_at_changes_on_save(self):
        cat = Category.objects.create(company=self.company_a, name="営業", parent_category=None)
        updated_before = cat.updated_at

        time.sleep(0.01)

        cat.name = "営業(更新)"
        cat.save()
        cat.refresh_from_db()

        self.assertGreater(cat.updated_at, updated_before)
