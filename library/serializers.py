from rest_framework import serializers

from library.models import Author, BookItem, BookTitle, Genre


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


class BookTitleSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all(),
    )
    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        required=False,
    )
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = BookTitle
        fields = (
            "id",
            "title",
            "description",
            "publication_year",
            "isbn",
            "publisher",
            "language",
            "authors",
            "genres",
            "is_available",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "is_available", "created_at", "updated_at")

    def validate_authors(self, value):
        if not value:
            raise serializers.ValidationError("At least one author is required.")
        return value

    def validate_isbn(self, value):
        if not value:
            return value

        queryset = BookTitle.objects.filter(isbn=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Book with this ISBN already exists.")
        return value

    def validate(self, attrs):
        authors = attrs.get("authors")
        if self.instance is None and not authors:
            raise serializers.ValidationError({"authors": "At least one author is required."})
        return attrs


class BookAvailabilitySerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    is_available = serializers.BooleanField()
    available_items_count = serializers.IntegerField()
    total_items_count = serializers.IntegerField()


class BookItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookItem
        fields = (
            "id",
            "book_title",
            "inventory_number",
            "status",
            "location",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_inventory_number(self, value):
        queryset = BookItem.objects.filter(inventory_number=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("Book item with this inventory number already exists.")
        return value
