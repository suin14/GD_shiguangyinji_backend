from rest_framework import serializers
from .models import Character


class CharacterSerializer(serializers.ModelSerializer):
    """
    人物序列化器
    """

    class Meta:
        model = Character
        fields = [
            "character_id",
            "avatar",
            "name",
            "gender",
            "relationship",
            "birthday",
        ]
        read_only_fields = ["character_id"]

    def validate_gender(self, value):
        """
        验证性别字段
        """
        if value not in ["male", "female"]:
            raise serializers.ValidationError("性别必须是'male'或'female'")
        return value
