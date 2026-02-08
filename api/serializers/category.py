from rest_framework import serializers

from api.models import Category, Company


class CategorySerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    parent_category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Category
        fields = [
            "id",
            "company",
            "name",
            "parent_category",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        company = attrs.get("company") or getattr(self.instance, "company", None)
        parent_category = attrs.get("parent_category", getattr(self.instance, "parent_category", None))

        # 親カテゴリの company チェック
        if parent_category is not None and company is not None:
            if parent_category.company_id != company.id:
                raise serializers.ValidationError({"parent_category": "親カテゴリは同一企業のカテゴリのみ指定できます。"})

        # 更新時に company を変更させない
        if self.instance is not None and company is not None:
            if company.id != self.instance.company_id:
                raise serializers.ValidationError({"company": "更新時に company は変更できません。"})

        # 自分自身 or 自分の子孫 を親にできない（循環参照防止）
        if self.instance is not None and parent_category is not None:
            cur = parent_category
            while cur is not None:
                if cur.id == self.instance.id:
                    raise serializers.ValidationError(
                        {"parent_category": "自分自身または自分の子孫カテゴリを親カテゴリには指定できません。"}
                    )
                cur = cur.parent_category

        return attrs
