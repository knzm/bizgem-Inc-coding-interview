from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from api.models import Category
from api.serializers.category import CategorySerializer


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = Category.objects.select_related("company", "parent_category").order_by("-created_at")
        company_id = self.request.query_params.get("company")
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs

    def perform_destroy(self, instance):
        has_children = Category.objects.filter(parent_category=instance).exists()
        if has_children:
            raise ValidationError({"detail": "子カテゴリを持つカテゴリは削除できません。先に子カテゴリを削除または移動してください。"})

        return super().perform_destroy(instance)
