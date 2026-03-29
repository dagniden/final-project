from rest_framework import serializers

from library.models import Author, Genre


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("id", "full_name", "birth_date", "death_date", "biography")
        read_only_fields = ("id",)

    def validate(self, attrs):
        birth_date = attrs.get("birth_date", getattr(self.instance, "birth_date", None))
        death_date = attrs.get("death_date", getattr(self.instance, "death_date", None))

        if birth_date and death_date and death_date < birth_date:
            raise serializers.ValidationError(
                {"death_date": "Death date cannot be earlier than birth date."}
            )

        return attrs


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name", "description")
        read_only_fields = ("id",)
