from drf_spectacular.utils import OpenApiResponse, extend_schema
from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from library.models import Author, BookItem, BookTitle, Genre
from library.serializers import (AuthorSerializer, BookAvailabilitySerializer,
                                 BookItemSerializer, BookTitleSerializer,
                                 GenreSerializer)


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
    related_error_message = "Cannot delete this object while it is linked to book titles."

    def perform_destroy(self, instance):
        if getattr(instance, self.related_manager_name).exists():
            raise ValidationError({"detail": self.related_error_message})
        super().perform_destroy(instance)


@extend_schema(
    tags=["Authors"],
    summary="Получить список авторов или создать автора",
)
class AuthorListCreateAPIView(StaffWriteAuthenticatedReadMixin, generics.ListCreateAPIView):
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
class GenreListCreateAPIView(StaffWriteAuthenticatedReadMixin, generics.ListCreateAPIView):
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

    def get_queryset(self):
        queryset = BookTitle.objects.prefetch_related("authors", "genres", "items")
        params = self.request.query_params

        title = params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        author = params.get("author")
        if author:
            queryset = queryset.filter(authors__full_name__icontains=author)

        author_id = params.get("author_id")
        if author_id:
            queryset = queryset.filter(authors__id=author_id)

        genre = params.get("genre")
        if genre:
            queryset = queryset.filter(genres__name__icontains=genre)

        genre_id = params.get("genre_id")
        if genre_id:
            queryset = queryset.filter(genres__id=genre_id)

        publication_year = params.get("publication_year")
        if publication_year:
            queryset = queryset.filter(publication_year=publication_year)

        isbn = params.get("isbn")
        if isbn:
            queryset = queryset.filter(isbn=isbn)

        available = params.get("available")
        if available is not None:
            is_available = available.lower() in ("1", "true", "yes")
            status_filter = Q(items__status=BookItem.Status.AVAILABLE)
            if is_available:
                queryset = queryset.filter(status_filter)
            else:
                queryset = queryset.exclude(status_filter)

        return queryset.order_by("title", "id").distinct()


@extend_schema(
    tags=["Books"],
    summary="Получить, изменить или удалить карточку книги",
    responses={
        400: OpenApiResponse(
            description="Карточка книги связана с экземплярами и не может быть удалена."
        )
    },
)
class BookDetailAPIView(
    ProtectedDeleteMixin,
    StaffWritePublicReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = BookTitle.objects.prefetch_related("authors", "genres", "items")
    serializer_class = BookTitleSerializer
    related_manager_name = "items"
    related_error_message = "Cannot delete book linked to book items."


@extend_schema(
    tags=["Books"],
    summary="Получить агрегатную доступность карточки книги",
    responses={200: BookAvailabilitySerializer},
)
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


@extend_schema(
    tags=["Book Items"],
    summary="Получить список экземпляров книг или зарегистрировать экземпляр",
)
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


@extend_schema(
    tags=["Book Items"],
    summary="Получить, изменить или удалить экземпляр книги",
    responses={
        400: OpenApiResponse(
            description="Экземпляр книги связан с выдачами и не может быть удален."
        )
    },
)
class BookItemDetailAPIView(
    ProtectedDeleteMixin,
    StaffWritePublicReadMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = BookItem.objects.select_related("book_title")
    serializer_class = BookItemSerializer
    related_manager_name = "loans"
    related_error_message = "Cannot delete book item linked to loans."
