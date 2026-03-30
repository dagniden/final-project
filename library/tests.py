from datetime import timedelta

from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from library.models import Author, BookItem, BookTitle, Genre, Loan
from users.models import User


class AuthorGenreAPITestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="reader",
            email="reader@example.com",
            password="ReaderPass123!",
        )
        self.author = Author.objects.create(full_name="Leo Tolstoy")
        self.genre = Genre.objects.create(name="Novel", description="Long-form fiction")

    def test_authenticated_user_can_get_authors_list(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/v1/authors")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["full_name"], self.author.full_name)

    def test_authenticated_user_can_get_author_detail(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f"/api/v1/authors/{self.author.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], self.author.full_name)

    def test_staff_can_create_author(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/authors",
            {
                "full_name": "Fyodor Dostoevsky",
                "birth_date": "1821-11-11",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Author.objects.filter(full_name="Fyodor Dostoevsky").exists())

    def test_regular_user_cannot_create_author(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/v1/authors",
            {"full_name": "Fyodor Dostoevsky"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_update_author(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/v1/authors/{self.author.id}",
            {"biography": "Russian writer."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        self.assertEqual(self.author.biography, "Russian writer.")

    def test_regular_user_cannot_update_author(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f"/api/v1/authors/{self.author.id}",
            {"biography": "Russian writer."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_delete_unlinked_author(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(f"/api/v1/authors/{self.author.id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Author.objects.filter(id=self.author.id).exists())

    def test_staff_cannot_delete_linked_author(self):
        book = BookTitle.objects.create(title="War and Peace")
        book.authors.add(self.author)
        self.client.force_authenticate(self.admin)

        response = self.client.delete(f"/api/v1/authors/{self.author.id}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Cannot delete author linked to book titles.",
        )

    def test_authenticated_user_can_get_genres_list(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/v1/genres")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.genre.name)

    def test_authenticated_user_can_get_genre_detail(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f"/api/v1/genres/{self.genre.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.genre.name)

    def test_staff_can_create_genre(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/genres",
            {"name": "Science Fiction", "description": "Speculative fiction"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Genre.objects.filter(name="Science Fiction").exists())

    def test_regular_user_cannot_create_genre(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/v1/genres",
            {"name": "Science Fiction"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_update_genre(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/v1/genres/{self.genre.id}",
            {"description": "Updated description"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.genre.refresh_from_db()
        self.assertEqual(self.genre.description, "Updated description")

    def test_regular_user_cannot_update_genre(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f"/api/v1/genres/{self.genre.id}",
            {"description": "Updated description"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_delete_unlinked_genre(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(f"/api/v1/genres/{self.genre.id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Genre.objects.filter(id=self.genre.id).exists())

    def test_staff_cannot_delete_linked_genre(self):
        book = BookTitle.objects.create(title="War and Peace")
        book.authors.add(self.author)
        book.genres.add(self.genre)
        self.client.force_authenticate(self.admin)

        response = self.client.delete(f"/api/v1/genres/{self.genre.id}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Cannot delete genre linked to book titles.",
        )

    def test_genre_name_must_be_unique(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/genres",
            {"name": self.genre.name},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)


class BookManagementAPITestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="reader",
            email="reader@example.com",
            password="ReaderPass123!",
        )
        self.author = Author.objects.create(full_name="Leo Tolstoy")
        self.second_author = Author.objects.create(full_name="Jane Austen")
        self.genre = Genre.objects.create(name="Novel")
        self.second_genre = Genre.objects.create(name="Drama")
        self.book = BookTitle.objects.create(
            title="War and Peace",
            publication_year=1869,
            isbn="9785170904153",
        )
        self.book.authors.add(self.author)
        self.book.genres.add(self.genre)
        self.other_book = BookTitle.objects.create(
            title="Pride and Prejudice",
            publication_year=1813,
        )
        self.other_book.authors.add(self.second_author)
        self.other_book.genres.add(self.second_genre)
        self.available_item = BookItem.objects.create(
            book_title=self.book,
            inventory_number="INV-001",
            status=BookItem.Status.AVAILABLE,
            location="Shelf A",
        )
        self.loaned_item = BookItem.objects.create(
            book_title=self.book,
            inventory_number="INV-002",
            status=BookItem.Status.LOANED,
            location="Shelf B",
        )
        self.other_item = BookItem.objects.create(
            book_title=self.other_book,
            inventory_number="INV-003",
            status=BookItem.Status.UNAVAILABLE,
        )

    def test_anonymous_user_can_get_books_list(self):
        response = self.client.get("/api/v1/books")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_anonymous_user_can_get_book_detail(self):
        response = self.client.get(f"/api/v1/books/{self.book.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.book.title)

    def test_staff_can_create_book(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/books",
            {
                "title": "Anna Karenina",
                "publication_year": 1877,
                "authors": [self.author.id],
                "genres": [self.genre.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BookTitle.objects.filter(title="Anna Karenina").exists())

    def test_regular_user_cannot_create_book(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/v1/books",
            {
                "title": "Anna Karenina",
                "authors": [self.author.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_requires_at_least_one_author(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/books",
            {
                "title": "Anna Karenina",
                "authors": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("authors", response.data)

    def test_book_isbn_must_be_unique(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/books",
            {
                "title": "Duplicate ISBN",
                "isbn": self.book.isbn,
                "authors": [self.author.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("isbn", response.data)

    def test_staff_can_update_book(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/v1/books/{self.book.id}",
            {"publisher": "The Russian Messenger"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.publisher, "The Russian Messenger")

    def test_staff_cannot_delete_book_with_items(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(f"/api/v1/books/{self.book.id}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Cannot delete book linked to book items.")

    def test_books_list_supports_combined_filters(self):
        response = self.client.get(
            "/api/v1/books",
            {
                "title": "war",
                "author": "tolstoy",
                "genre": "nov",
                "publication_year": 1869,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.book.id)

    def test_books_availability_is_public_and_aggregated(self):
        response = self.client.get(f"/api/v1/books/{self.book.id}/availability")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["book_id"], self.book.id)
        self.assertTrue(response.data["is_available"])
        self.assertEqual(response.data["available_items_count"], 1)
        self.assertEqual(response.data["total_items_count"], 2)

    def test_anonymous_user_can_get_book_items_list(self):
        response = self.client.get("/api/v1/book-items")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_anonymous_user_can_get_book_item_detail(self):
        response = self.client.get(f"/api/v1/book-items/{self.available_item.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["inventory_number"], self.available_item.inventory_number)

    def test_staff_can_create_book_item(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/book-items",
            {
                "book_title": self.book.id,
                "inventory_number": "INV-004",
                "status": BookItem.Status.AVAILABLE,
                "location": "Shelf C",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BookItem.objects.filter(inventory_number="INV-004").exists())

    def test_regular_user_cannot_create_book_item(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/v1/book-items",
            {
                "book_title": self.book.id,
                "inventory_number": "INV-004",
                "status": BookItem.Status.AVAILABLE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_items_list_supports_book_title_filter(self):
        response = self.client.get("/api/v1/book-items", {"book_title_id": self.book.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({item["id"] for item in response.data}, {self.available_item.id, self.loaned_item.id})

    def test_book_item_inventory_number_must_be_unique(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/book-items",
            {
                "book_title": self.book.id,
                "inventory_number": self.available_item.inventory_number,
                "status": BookItem.Status.AVAILABLE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inventory_number", response.data)

    def test_book_item_status_must_be_valid(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/v1/book-items",
            {
                "book_title": self.book.id,
                "inventory_number": "INV-999",
                "status": "broken",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_staff_cannot_delete_book_item_with_loans(self):
        loan_item = BookItem.objects.create(
            book_title=self.book,
            inventory_number="INV-005",
            status=BookItem.Status.AVAILABLE,
        )
        Loan.objects.create(
            user=self.user,
            book_item=loan_item,
            issued_at=timezone.now(),
            due_date=timezone.now().date() + timedelta(days=14),
        )
        self.client.force_authenticate(self.admin)

        response = self.client.delete(f"/api/v1/book-items/{loan_item.id}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Cannot delete book item linked to loans.")
