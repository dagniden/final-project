from django.urls import path

from library.apps import LibraryConfig
from library.views import (AuthorDetailAPIView, AuthorListCreateAPIView,
                           GenreDetailAPIView, GenreListCreateAPIView)

app_name = LibraryConfig.name

urlpatterns = [
    path("authors", AuthorListCreateAPIView.as_view(), name="author_list_create"),
    path("authors/<int:pk>", AuthorDetailAPIView.as_view(), name="author_detail"),
    path("genres", GenreListCreateAPIView.as_view(), name="genre_list_create"),
    path("genres/<int:pk>", GenreDetailAPIView.as_view(), name="genre_detail"),
]
