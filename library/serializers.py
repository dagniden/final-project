from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from library.models import Author, BookItem, BookTitle, Genre, Loan


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("id", "full_name", "birth_date", "death_date", "biography")
        read_only_fields = ("id",)
        extra_kwargs = {
            "full_name": {
                "help_text": "Полное имя автора для отображения в каталоге.",
            },
            "birth_date": {
                "help_text": "Дата рождения автора в формате YYYY-MM-DD.",
            },
            "death_date": {
                "help_text": "Дата смерти автора в формате YYYY-MM-DD, если применимо.",
            },
            "biography": {
                "help_text": "Краткая биография автора или служебное описание.",
            },
        }

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
        extra_kwargs = {
            "name": {
                "help_text": "Уникальное название жанра.",
            },
            "description": {
                "help_text": "Необязательное пояснение, что включает жанр.",
            },
        }


class BookTitleSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Author.objects.all(),
        help_text="Список идентификаторов авторов. Требуется минимум один автор.",
    )
    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        required=False,
        help_text="Список идентификаторов жанров. Поле можно не передавать.",
    )
    is_available = serializers.BooleanField(
        read_only=True,
        help_text="Агрегатная доступность книги: `true`, если есть хотя бы один доступный экземпляр.",
    )

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
        extra_kwargs = {
            "title": {"help_text": "Название книги."},
            "description": {
                "help_text": "Аннотация или краткое описание издания.",
            },
            "publication_year": {
                "help_text": "Год публикации издания.",
            },
            "isbn": {
                "help_text": "ISBN книги. При наличии должен быть уникальным.",
            },
            "publisher": {
                "help_text": "Название издательства.",
            },
            "language": {
                "help_text": "Язык издания.",
            },
            "created_at": {
                "help_text": "Дата и время создания карточки книги.",
            },
            "updated_at": {
                "help_text": "Дата и время последнего обновления карточки книги.",
            },
        }

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
            raise serializers.ValidationError(
                {"authors": "At least one author is required."}
            )
        return attrs


class BookAvailabilitySerializer(serializers.Serializer):
    book_id = serializers.IntegerField(help_text="Идентификатор карточки книги.")
    is_available = serializers.BooleanField(
        help_text="`true`, если у книги есть хотя бы один экземпляр со статусом `available`."
    )
    available_items_count = serializers.IntegerField(
        help_text="Количество доступных для выдачи экземпляров книги."
    )
    total_items_count = serializers.IntegerField(
        help_text="Общее количество зарегистрированных экземпляров книги."
    )


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
        extra_kwargs = {
            "book_title": {
                "help_text": "Идентификатор карточки книги, к которой относится экземпляр.",
            },
            "inventory_number": {
                "help_text": "Уникальный инвентарный номер экземпляра.",
            },
            "status": {
                "help_text": "Статус экземпляра: `available`, `loaned` или `unavailable`.",
            },
            "location": {
                "help_text": "Место хранения экземпляра в библиотеке.",
            },
            "created_at": {
                "help_text": "Дата и время регистрации экземпляра.",
            },
            "updated_at": {
                "help_text": "Дата и время последнего изменения экземпляра.",
            },
        }

    def validate_inventory_number(self, value):
        queryset = BookItem.objects.filter(inventory_number=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Book item with this inventory number already exists."
            )
        return value


class LoanSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(
        read_only=True,
        help_text="`true`, если книга еще не возвращена и выдача активна.",
    )

    class Meta:
        model = Loan
        fields = (
            "id",
            "user",
            "book_item",
            "issued_at",
            "due_date",
            "returned_at",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "is_active", "created_at", "updated_at")
        extra_kwargs = {
            "user": {
                "help_text": "Идентификатор пользователя, которому оформляется выдача.",
            },
            "book_item": {
                "help_text": "Идентификатор экземпляра книги. На момент выдачи он должен быть доступен.",
            },
            "issued_at": {
                "help_text": "Дата и время выдачи в формате ISO 8601.",
            },
            "due_date": {
                "help_text": "Плановая дата возврата в формате YYYY-MM-DD.",
            },
            "returned_at": {
                "help_text": "Дата и время возврата в формате ISO 8601. Для активной выдачи может быть `null`.",
            },
            "created_at": {
                "help_text": "Дата и время создания записи выдачи.",
            },
            "updated_at": {
                "help_text": "Дата и время последнего изменения записи выдачи.",
            },
        }

    def validate(self, attrs):
        if self.instance is not None:
            immutable_fields = {"user", "book_item", "issued_at"}
            provided_immutable_fields = immutable_fields.intersection(attrs)
            if provided_immutable_fields:
                raise serializers.ValidationError(
                    {
                        field: "This field cannot be updated after loan creation."
                        for field in provided_immutable_fields
                    }
                )

        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)


class LoanReminderResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="Результат обработки запроса на отправку напоминания.")
    loan_id = serializers.IntegerField(help_text="Идентификатор выдачи, для которой обработано напоминание.")
