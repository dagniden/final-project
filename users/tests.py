from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UsersAPITestCase(APITestCase):
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

    def test_register_user(self):
        response = self.client.post(
            "/api/v1/auth/register",
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_login_returns_tokens(self):
        response = self.client.post(
            "/api/v1/auth/login",
            {
                "email": self.user.email,
                "password": "ReaderPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_me_returns_current_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/v1/users/me")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_regular_user_cannot_get_users_list(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/v1/users")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_get_users_list(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/v1/users")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_get_user_detail(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(f"/api/v1/users/{self.user.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_user_can_get_own_detail(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f"/api/v1/users/{self.user.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_regular_user_cannot_get_another_user_detail(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f"/api/v1/users/{self.admin.id}")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DocumentationAPITestCase(APITestCase):
    def test_schema_endpoint_returns_openapi_document(self):
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "openapi:")
        self.assertContains(response, "paths:")

    def test_swagger_ui_endpoint_is_available(self):
        response = self.client.get("/api/docs/swagger/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "swagger")

    def test_redoc_endpoint_is_available(self):
        response = self.client.get("/api/docs/redoc/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "redoc")
