from rest_framework import status
from rest_framework.test import APITestCase

from library.models import Author, BookTitle, Genre
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
