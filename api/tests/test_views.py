from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Company, Category


class CategoryViewTests(APITestCase):
    fixtures = ["companies.json", "categories.json"]

    def setUp(self):
        self.company_a = Company.objects.get(name="A社")
        self.company_b = Company.objects.get(name="B社")

        self.root_category_a = Category.objects.get(company=self.company_a, parent_category=None)
        self.child_category_a = Category.objects.get(company=self.company_a, parent_category=self.root_category_a)

        self.root_category_b = Category.objects.get(company=self.company_b, parent_category=None)

    def test_list_returns_all_when_no_filter(self):
        res = self.client.get('/api/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        returned_ids = {item["id"] for item in res.data}

        self.assertIn(str(self.root_category_a.id), returned_ids)
        self.assertIn(str(self.child_category_a.id), returned_ids)
        self.assertIn(str(self.root_category_b.id), returned_ids)

    def test_list_filters_by_company_query_param(self):
        query = {
            "company": str(self.company_a.id),
        }
        res = self.client.get('/api/categories/', query)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        returned_ids = {item["id"] for item in res.data}

        self.assertIn(str(self.root_category_a.id), returned_ids)
        self.assertIn(str(self.child_category_a.id), returned_ids)
        self.assertNotIn(str(self.root_category_b.id), returned_ids)

    def test_retrieve_ok(self):
        res = self.client.get(f'/api/categories/{self.root_category_a.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data["id"], str(self.root_category_a.id))
        self.assertEqual(res.data["name"], self.root_category_a.name)
        self.assertEqual(str(res.data["company"]), str(self.company_a.id))

    def test_create(self):
        pass

    def test_update(self):
        pass

    def test_destroy(self):
        pass
