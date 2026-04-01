from django.db.models import Count, Q
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiResponse, extend_schema)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from library.filters import BookTitleFilter
from library.models import Author, BookItem, BookTitle, Genre, Loan
from library.services import send_loan_reminder
from library.serializers import (AuthorSerializer, BookAvailabilitySerializer,
                                  BookItemSerializer, BookTitleSerializer,
                                 GenreSerializer, LoanReminderResponseSerializer,
                                 LoanSerializer)


class StaffWriteAuthenticatedReadMixin:
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class StaffWritePublicReadMixin:
    def get_permissions(self):
        permission_classes = [AllowAny]
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ProtectedDeleteMixin:
    related_manager_name = None
    related_error_message = (
        "Cannot delete this object while it is linked to book titles."
    )

    def perform_destroy(self, instance):
        if getattr(instance, self.related_manager_name).exists():
            raise ValidationError({"detail": self.related_error_message})
        super().perform_destroy(instance)


# region API Docs
@extend_schema(
    tags=["Authors"],
    summary="Получить список авторов или создать автора",
    description=(
        "Возвращает список авторов для справочника каталога или создает нового автора. "
        "Чтение доступно только аутентифицированным пользователям, запись только сотрудникам."
    ),
    request=AuthorSerializer,
    responses={
        200: AuthorSerializer(many=True),
        201: AuthorSerializer,
        403: OpenApiResponse(description="Недостаточно прав для создания автора."),
    },
)
# endregion
class AuthorListCreateAPIView(
    StaffWriteAuthenticatedReadMixin, generics.ListCreateAPIView
):
    queryset = Author.objects.order_by("full_name", "id")
    serializer_class = AuthorSerializer


# region API Docs
@extend_schema(
    tags=["Authors"],
    summary="Получить, изменить или удалить автора",
    description=(
        "Возвращает карточку автора, обновляет его данные или удаляет запись, если автор "
        "не связан с карточками книг."
    ),
    request=AuthorSerializer,
    responses={
        200: AuthorSerializer,
        204: OpenApiResponse(description="Автор успешно удален."),
        400: OpenApiResponse(
            description="Автор связан с карточками книг и не может быть удален."
        ),
        403: OpenApiResponse(description="Недостаточно прав для изменения или удаления автора."),
    },
)
# endregion
class AuthorDetailAPIView(
    ProtectedDeleteMixin,
    StaffWriteAuthenticatedReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    related_manager_name = "book_titles"
    related_error_message = "Cannot delete author linked to book titles."


# region API Docs
@extend_schema(
    tags=["Genres"],
    summary="Получить список жанров или создать жанр",
    description=(
        "Возвращает справочник жанров или создает новый жанр для классификации книг. "
        "Чтение доступно только аутентифицированным пользователям, запись только сотрудникам."
    ),
    request=GenreSerializer,
    responses={
        200: GenreSerializer(many=True),
        201: GenreSerializer,
        403: OpenApiResponse(description="Недостаточно прав для создания жанра."),
    },
)
# endregion
class GenreListCreateAPIView(
    StaffWriteAuthenticatedReadMixin, generics.ListCreateAPIView
):
    queryset = Genre.objects.order_by("name", "id")
    serializer_class = GenreSerializer


# region API Docs
@extend_schema(
    tags=["Genres"],
    summary="Получить, изменить или удалить жанр",
    description=(
        "Возвращает карточку жанра, обновляет ее или удаляет, если жанр не используется "
        "в карточках книг."
    ),
    request=GenreSerializer,
    responses={
        200: GenreSerializer,
        204: OpenApiResponse(description="Жанр успешно удален."),
        400: OpenApiResponse(
            description="Жанр связан с карточками книг и не может быть удален."
        ),
        403: OpenApiResponse(description="Недостаточно прав для изменения или удаления жанра."),
    },
)
# endregion
class GenreDetailAPIView(
    ProtectedDeleteMixin,
    StaffWriteAuthenticatedReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    related_manager_name = "book_titles"
    related_error_message = "Cannot delete genre linked to book titles."


# region API Docs
@extend_schema(
    tags=["Books"],
    summary="Получить список карточек книг или создать карточку книги",
    description=(
        "Возвращает каталог карточек книг с фильтрацией и сортировкой или создает новую карточку книги. "
        "Чтение публично, запись доступна только сотрудникам библиотеки."
    ),
    request=BookTitleSerializer,
    parameters=[
        OpenApiParameter(name="title", type=str, location=OpenApiParameter.QUERY, description="Поиск по части названия книги без учета регистра."),
        OpenApiParameter(name="author", type=str, location=OpenApiParameter.QUERY, description="Поиск по части имени автора."),
        OpenApiParameter(name="author_id", type=int, location=OpenApiParameter.QUERY, description="Фильтр по идентификатору автора."),
        OpenApiParameter(name="genre", type=str, location=OpenApiParameter.QUERY, description="Поиск по части названия жанра."),
        OpenApiParameter(name="genre_id", type=int, location=OpenApiParameter.QUERY, description="Фильтр по идентификатору жанра."),
        OpenApiParameter(name="publication_year", type=int, location=OpenApiParameter.QUERY, description="Фильтр по году публикации."),
        OpenApiParameter(name="isbn", type=str, location=OpenApiParameter.QUERY, description="Фильтр по точному ISBN."),
        OpenApiParameter(name="available", type=bool, location=OpenApiParameter.QUERY, description="Фильтр по агрегатной доступности книги."),
        OpenApiParameter(
            name="ordering",
            type=str,
            location=OpenApiParameter.QUERY,
            description=(
                "Сортировка по полям `title`, `publication_year`, `created_at`, `updated_at`, `id`. "
                "Для обратного порядка используйте префикс `-`."
            ),
        ),
    ],
    responses={
        200: BookTitleSerializer(many=True),
        201: BookTitleSerializer,
        400: OpenApiResponse(
            description="Ошибка валидации. Например, не передан автор или ISBN уже занят."
        ),
        403: OpenApiResponse(description="Недостаточно прав для создания карточки книги."),
    },
    examples=[
        OpenApiExample(
            "Создание карточки книги",
            value={
                "title": "Anna Karenina",
                "publication_year": 1877,
                "isbn": "9780140449174",
                "publisher": "Penguin Classics",
                "language": "ru",
                "authors": [1],
                "genres": [1],
            },
            request_only=True,
        )
    ],
)
# endregion
class BookListCreateAPIView(StaffWritePublicReadMixin, generics.ListCreateAPIView):
    serializer_class = BookTitleSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BookTitleFilter
    ordering_fields = ["title", "publication_year", "created_at", "updated_at", "id"]
    ordering = ["title", "id"]

    def get_queryset(self):
        return BookTitle.objects.prefetch_related("authors", "genres", "items").distinct()


# region API Docs
@extend_schema(
    tags=["Books"],
    summary="Получить, изменить или удалить карточку книги",
    description=(
        "Возвращает подробную карточку книги, обновляет ее или удаляет. Удаление запрещено, "
        "если к карточке уже привязаны экземпляры книги."
    ),
    request=BookTitleSerializer,
    responses={
        200: BookTitleSerializer,
        204: OpenApiResponse(description="Карточка книги успешно удалена."),
        400: OpenApiResponse(
            description="Карточка книги связана с экземплярами и не может быть удалена."
        ),
        403: OpenApiResponse(description="Недостаточно прав для изменения или удаления карточки книги."),
    },
)
# endregion
class BookDetailAPIView(
    ProtectedDeleteMixin,
    StaffWritePublicReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = BookTitle.objects.prefetch_related("authors", "genres", "items")
    serializer_class = BookTitleSerializer
    related_manager_name = "items"
    related_error_message = "Cannot delete book linked to book items."


# region API Docs
@extend_schema(
    tags=["Books"],
    summary="Получить агрегатную доступность карточки книги",
    description=(
        "Возвращает агрегированную информацию по экземплярам книги: общее количество, число "
        "доступных экземпляров и итоговый флаг доступности."
    ),
    responses={200: BookAvailabilitySerializer},
)
# endregion
class BookAvailabilityAPIView(StaffWritePublicReadMixin, generics.RetrieveAPIView):
    queryset = BookTitle.objects.annotate(
        total_items_count=Count("items", distinct=True),
        available_items_count=Count(
            "items",
            filter=Q(items__status=BookItem.Status.AVAILABLE),
            distinct=True,
        ),
    )
    serializer_class = BookAvailabilitySerializer

    def retrieve(self, request, *args, **kwargs):
        book = self.get_object()
        serializer = self.get_serializer(
            {
                "book_id": book.id,
                "is_available": book.available_items_count > 0,
                "available_items_count": book.available_items_count,
                "total_items_count": book.total_items_count,
            }
        )
        return Response(serializer.data)


# region API Docs
@extend_schema(
    tags=["Book Items"],
    summary="Получить список экземпляров книг или зарегистрировать экземпляр",
    description=(
        "Возвращает список физических экземпляров книг с фильтрацией или создает новый экземпляр. "
        "Чтение публично, запись доступна только сотрудникам библиотеки."
    ),
    request=BookItemSerializer,
    parameters=[
        OpenApiParameter(name="book_title_id", type=int, location=OpenApiParameter.QUERY, description="Фильтр по идентификатору карточки книги."),
        OpenApiParameter(name="status", type=str, location=OpenApiParameter.QUERY, description="Фильтр по статусу экземпляра: `available`, `loaned`, `unavailable`."),
        OpenApiParameter(name="inventory_number", type=str, location=OpenApiParameter.QUERY, description="Поиск по части инвентарного номера экземпляра."),
    ],
    responses={
        200: BookItemSerializer(many=True),
        201: BookItemSerializer,
        400: OpenApiResponse(
            description="Ошибка валидации. Например, повторяющийся инвентарный номер или некорректный статус."
        ),
        403: OpenApiResponse(description="Недостаточно прав для создания экземпляра книги."),
    },
)
# endregion
class BookItemListCreateAPIView(StaffWritePublicReadMixin, generics.ListCreateAPIView):
    serializer_class = BookItemSerializer

    def get_queryset(self):
        queryset = BookItem.objects.select_related("book_title")
        params = self.request.query_params

        book_title_id = params.get("book_title_id")
        if book_title_id:
            queryset = queryset.filter(book_title_id=book_title_id)

        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        inventory_number = params.get("inventory_number")
        if inventory_number:
            queryset = queryset.filter(inventory_number__icontains=inventory_number)

        return queryset.order_by("inventory_number", "id")


# region API Docs
@extend_schema(
    tags=["Book Items"],
    summary="Получить, изменить или удалить экземпляр книги",
    description=(
        "Возвращает экземпляр книги, обновляет его данные или удаляет. Удаление запрещено, "
        "если по экземпляру уже есть записи выдачи."
    ),
    request=BookItemSerializer,
    responses={
        200: BookItemSerializer,
        204: OpenApiResponse(description="Экземпляр книги успешно удален."),
        400: OpenApiResponse(
            description="Экземпляр книги связан с выдачами и не может быть удален."
        ),
        403: OpenApiResponse(description="Недостаточно прав для изменения или удаления экземпляра книги."),
    },
)
# endregion
class BookItemDetailAPIView(
    ProtectedDeleteMixin,
    StaffWritePublicReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = BookItem.objects.select_related("book_title")
    serializer_class = BookItemSerializer
    related_manager_name = "loans"
    related_error_message = "Cannot delete book item linked to loans."


# region API Docs
@extend_schema(
    tags=["Loans"],
    summary="Получить список выдач или оформить выдачу экземпляра книги",
    description=(
        "Возвращает список выдач с фильтрацией или оформляет новую выдачу экземпляра книги. "
        "Операции доступны только сотрудникам библиотеки."
    ),
    request=LoanSerializer,
    parameters=[
        OpenApiParameter(name="user_id", type=int, location=OpenApiParameter.QUERY, description="Фильтр по идентификатору пользователя."),
        OpenApiParameter(name="book_item_id", type=int, location=OpenApiParameter.QUERY, description="Фильтр по идентификатору экземпляра книги."),
        OpenApiParameter(name="active", type=bool, location=OpenApiParameter.QUERY, description="Фильтр по активности выдачи: `true` для незавершенных, `false` для возвращенных."),
    ],
    responses={
        200: LoanSerializer(many=True),
        201: LoanSerializer,
        400: OpenApiResponse(
            description=(
                "Ошибка валидации. Например, экземпляр уже выдан, недоступен или дата возврата раньше даты выдачи."
            )
        ),
        403: OpenApiResponse(description="Эндпоинт доступен только сотрудникам библиотеки."),
    },
    examples=[
        OpenApiExample(
            "Оформление выдачи",
            value={
                "user": 5,
                "book_item": 12,
                "issued_at": "2026-03-30T10:00:00Z",
                "due_date": "2026-04-13",
            },
            request_only=True,
        )
    ],
)
# endregion
class LoanListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LoanSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Loan.objects.select_related("user", "book_item", "book_item__book_title")
        params = self.request.query_params

        user_id = params.get("user_id")
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        book_item_id = params.get("book_item_id")
        if book_item_id:
            queryset = queryset.filter(book_item_id=book_item_id)

        active = params.get("active")
        if active is not None:
            is_active = active.lower() in ("1", "true", "yes")
            if is_active:
                queryset = queryset.filter(returned_at__isnull=True)
            else:
                queryset = queryset.filter(returned_at__isnull=False)

        return queryset.order_by("-issued_at", "-id")


# region API Docs
@extend_schema(
    tags=["Loans"],
    summary="Получить информацию о выдаче или зафиксировать возврат",
    description=(
        "Возвращает запись выдачи или обновляет ее для фиксации возврата. После создания нельзя "
        "изменять `user`, `book_item` и `issued_at`."
    ),
    request=LoanSerializer,
    responses={
        200: LoanSerializer,
        400: OpenApiResponse(
            description=(
                "Ошибка валидации. Например, попытка изменить неизменяемые поля или передать `returned_at` раньше `issued_at`."
            )
        ),
        403: OpenApiResponse(description="Эндпоинт доступен только сотрудникам библиотеки."),
    },
)
# endregion
class LoanDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = Loan.objects.select_related("user", "book_item", "book_item__book_title")
    serializer_class = LoanSerializer
    permission_classes = [IsAdminUser]


# region API Docs
@extend_schema(
    tags=["Loans"],
    summary="Вручную отправить напоминание о возврате",
    description=(
        "Запускает обработку напоминания по активной выдаче. В текущей реализации возвращает "
        "stub-ответ, который подтверждает обработку запроса."
    ),
    request=None,
    responses={
        200: LoanReminderResponseSerializer,
        400: OpenApiResponse(description="Нельзя отправить напоминание по возвращенной выдаче."),
        403: OpenApiResponse(description="Эндпоинт доступен только сотрудникам библиотеки."),
    },
    examples=[
        OpenApiExample(
            "Успешная обработка напоминания",
            value={"detail": "Reminder sending is not configured yet.", "loan_id": 1},
            response_only=True,
            status_codes=["200"],
        )
    ],
)
# endregion
class LoanReminderSendAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        loan = generics.get_object_or_404(
            Loan.objects.select_related("user", "book_item"),
            pk=pk,
        )
        return Response(send_loan_reminder(loan))
