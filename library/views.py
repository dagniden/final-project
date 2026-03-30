from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiResponse, extend_schema
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
                                 GenreSerializer, LoanSerializer)


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


@extend_schema(
    tags=["Authors"],
    summary="Получить список авторов или создать автора",
)
class AuthorListCreateAPIView(
    StaffWriteAuthenticatedReadMixin, generics.ListCreateAPIView
):
    queryset = Author.objects.order_by("full_name", "id")
    serializer_class = AuthorSerializer


@extend_schema(
    tags=["Authors"],
    summary="Получить, изменить или удалить автора",
    responses={
        400: OpenApiResponse(
            description="Автор связан с карточками книг и не может быть удален."
        )
    },
)
class AuthorDetailAPIView(
    ProtectedDeleteMixin,
    StaffWriteAuthenticatedReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    related_manager_name = "book_titles"
    related_error_message = "Cannot delete author linked to book titles."


@extend_schema(
    tags=["Genres"],
    summary="Получить список жанров или создать жанр",
)
class GenreListCreateAPIView(
    StaffWriteAuthenticatedReadMixin, generics.ListCreateAPIView
):
    queryset = Genre.objects.order_by("name", "id")
    serializer_class = GenreSerializer


@extend_schema(
    tags=["Genres"],
    summary="Получить, изменить или удалить жанр",
    responses={
        400: OpenApiResponse(
            description="Жанр связан с карточками книг и не может быть удален."
        )
    },
)
class GenreDetailAPIView(
    ProtectedDeleteMixin,
    StaffWriteAuthenticatedReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    related_manager_name = "book_titles"
    related_error_message = "Cannot delete genre linked to book titles."


@extend_schema(
    tags=["Books"],
    summary="Получить список карточек книг или создать карточку книги",
)
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
    responses={
        400: OpenApiResponse(
            description="Карточка книги связана с экземплярами и не может быть удалена."
        )
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
    responses={
        400: OpenApiResponse(
            description="Экземпляр книги связан с выдачами и не может быть удален."
        )
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


@extend_schema(
    tags=["Loans"],
    summary="Получить список выдач или оформить выдачу экземпляра книги",
)
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


@extend_schema(
    tags=["Loans"],
    summary="Получить информацию о выдаче или зафиксировать возврат",
)
class LoanDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = Loan.objects.select_related("user", "book_item", "book_item__book_title")
    serializer_class = LoanSerializer
    permission_classes = [IsAdminUser]


@extend_schema(
    tags=["Loans"],
    summary="Вручную отправить напоминание о возврате",
    responses={
        200: OpenApiResponse(description="Напоминание обработано заглушкой."),
        400: OpenApiResponse(description="Нельзя отправить напоминание по возвращенной выдаче."),
    },
)
class LoanReminderSendAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        loan = generics.get_object_or_404(
            Loan.objects.select_related("user", "book_item"),
            pk=pk,
        )
        return Response(send_loan_reminder(loan))
