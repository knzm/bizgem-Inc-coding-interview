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

    def test_create_ok_parent_null(self):
        payload = {
            "company": str(self.company_a.id),
            "name": "新規カテゴリ",
            "parent_category": None,
        }
        res = self.client.post('/api/categories/', payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        created_id = res.data["id"]
        obj = Category.objects.get(id=created_id)
        self.assertEqual(obj.company_id, self.company_a.id)
        self.assertEqual(obj.name, "新規カテゴリ")
        self.assertIsNone(obj.parent_category)

    def test_create_ok_parent_same_company(self):
        payload = {
            "company": str(self.company_a.id),
            "name": "A社の子カテゴリ",
            "parent_category": str(self.root_category_a.id),
        }
        res = self.client.post('/api/categories/', payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        obj = Category.objects.get(id=res.data["id"])
        self.assertEqual(obj.parent_category_id, self.root_category_a.id)

    def test_create_ng_parent_different_company(self):
        payload = {
            "company": str(self.company_a.id),
            "name": "他社親はNG",
            "parent_category": str(self.root_category_b.id),  # B社のカテゴリ
        }
        res = self.client.post('/api/categories/', payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent_category", res.data)

    def test_create_ng_unique_company_name_duplicate(self):
        payload = {
            "company": str(self.company_a.id),
            "name": self.root_category_a.name,
            "parent_category": None,
        }
        res = self.client.post('/api/categories/', payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res.data)

    def test_update_ok(self):
        url = f'/api/categories/{self.child_category_a.id}/'
        payload = {"name": "子A(更新)"}
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.child_category_a.refresh_from_db()
        self.assertEqual(self.child_category_a.name, "子A(更新)")

    def test_update_ng_parent_is_self(self):
        url = f'/api/categories/{self.child_category_a.id}/'
        payload = {
            "parent_category": str(self.child_category_a.id),  # 自分を親に
        }
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent_category", res.data)

    def test_delete_ok(self):
        url = f'/api/categories/{self.child_category_a.id}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Category.objects.filter(id=self.child_category_a.id).exists())

    def test_delete_ng_with_children(self):
        url = f'/api/categories/{self.root_category_a.id}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("detail", res.data)

        self.assertTrue(Category.objects.filter(id=self.root_category_a.id).exists())
        self.assertTrue(Category.objects.filter(id=self.child_category_a.id).exists())
