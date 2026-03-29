from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from library.models import Author, Genre
from library.serializers import AuthorSerializer, GenreSerializer


class StaffWriteAuthenticatedReadMixin:
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
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
