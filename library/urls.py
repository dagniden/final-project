from django.urls import path

from library.apps import LibraryConfig
from library.views import (AuthorDetailAPIView, AuthorListCreateAPIView,
                           BookAvailabilityAPIView, BookDetailAPIView,
                           BookItemDetailAPIView, BookItemListCreateAPIView,
                           BookListCreateAPIView, GenreDetailAPIView,
                           GenreListCreateAPIView, LoanDetailAPIView,
                           LoanListCreateAPIView, LoanReminderSendAPIView)

app_name = LibraryConfig.name

urlpatterns = [
    path("authors", AuthorListCreateAPIView.as_view(), name="author_list_create"),
    path("authors/<int:pk>", AuthorDetailAPIView.as_view(), name="author_detail"),
    path("genres", GenreListCreateAPIView.as_view(), name="genre_list_create"),
    path("genres/<int:pk>", GenreDetailAPIView.as_view(), name="genre_detail"),
    path("books", BookListCreateAPIView.as_view(), name="book_list_create"),
    path("books/<int:pk>", BookDetailAPIView.as_view(), name="book_detail"),
    path(
        "books/<int:pk>/availability",
        BookAvailabilityAPIView.as_view(),
        name="book_availability",
    ),
    path(
        "book-items", BookItemListCreateAPIView.as_view(), name="book_item_list_create"
    ),
    path(
        "book-items/<int:pk>", BookItemDetailAPIView.as_view(), name="book_item_detail"
    ),
    path("loans", LoanListCreateAPIView.as_view(), name="loan_list_create"),
    path("loans/<int:pk>", LoanDetailAPIView.as_view(), name="loan_detail"),
    path(
        "loans/<int:pk>/reminder/send",
        LoanReminderSendAPIView.as_view(),
        name="loan_reminder_send",
    ),
]
