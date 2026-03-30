from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q


class Author(models.Model):
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField(blank=True, null=True)
    death_date = models.DateField(blank=True, null=True)
    biography = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name", "id"]

    def __str__(self):
        return self.full_name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class BookTitle(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    publication_year = models.PositiveSmallIntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=32, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    language = models.CharField(max_length=100, blank=True)
    authors = models.ManyToManyField(Author, related_name="book_titles")
    genres = models.ManyToManyField(Genre, related_name="book_titles", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["isbn"],
                condition=~Q(isbn=""),
                name="unique_non_empty_booktitle_isbn",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.items.filter(status=BookItem.Status.AVAILABLE).exists()


class BookItem(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        LOANED = "loaned", "Loaned"
        UNAVAILABLE = "unavailable", "Unavailable"

    book_title = models.ForeignKey(
        BookTitle,
        on_delete=models.PROTECT,
        related_name="items",
    )
    inventory_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["inventory_number", "id"]

    def __str__(self):
        return self.inventory_number


class Loan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loans",
    )
    book_item = models.ForeignKey(
        BookItem,
        on_delete=models.PROTECT,
        related_name="loans",
    )
    issued_at = models.DateTimeField()
    due_date = models.DateField()
    returned_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issued_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["book_item"],
                condition=Q(returned_at__isnull=True),
                name="unique_active_loan_per_book_item",
            ),
            models.CheckConstraint(
                condition=Q(returned_at__isnull=True)
                | Q(returned_at__gte=F("issued_at")),
                name="loan_returned_at_not_before_issued_at",
            ),
        ]

    def __str__(self):
        return f"{self.book_item} -> {self.user}"

    @property
    def is_active(self):
        return self.returned_at is None

    def clean(self):
        errors = {}
        previous_loan = None

        if self.due_date and self.issued_at and self.due_date < self.issued_at.date():
            errors["due_date"] = "Due date cannot be earlier than issue date."

        if self.returned_at and self.issued_at and self.returned_at < self.issued_at:
            errors["returned_at"] = "Return time cannot be earlier than issue time."

        if self.book_item_id:
            if self.pk:
                previous_loan = Loan.objects.filter(pk=self.pk).first()

            active_loans = Loan.objects.filter(
                book_item_id=self.book_item_id,
                returned_at__isnull=True,
            )

            if self.pk:
                active_loans = active_loans.exclude(pk=self.pk)

            if self.returned_at is None:
                if active_loans.exists():
                    errors["book_item"] = "This book item already has an active loan."

                must_be_available = (
                    previous_loan is None
                    or previous_loan.returned_at is not None
                    or previous_loan.book_item_id != self.book_item_id
                )

                current_status = self.book_item.status
                if must_be_available and current_status != BookItem.Status.AVAILABLE:
                    errors["book_item"] = "Only available book items can be issued."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        with transaction.atomic():
            super().save(*args, **kwargs)

            new_status = (
                BookItem.Status.AVAILABLE
                if self.returned_at is not None
                else BookItem.Status.LOANED
            )
            self.book_item.status = new_status
            self.book_item.save(update_fields=["status", "updated_at"])
