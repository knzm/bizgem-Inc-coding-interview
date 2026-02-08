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
