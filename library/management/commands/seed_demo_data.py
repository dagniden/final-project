from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from library.models import Author, BookItem, BookTitle, Genre, Loan
from users.models import User


class Command(BaseCommand):
    help = "Seeds demo users, authors, genres, books, book items, and loans."

    def handle(self, *args, **options):
        staff_user = self._upsert_user(
            email="admin@example.com",
            username="admin",
            password="AdminPass123!",
            is_staff=True,
            first_name="Library",
            last_name="Admin",
            city="Moscow",
        )
        reader_user = self._upsert_user(
            email="reader@example.com",
            username="reader",
            password="ReaderPass123!",
            is_staff=False,
            first_name="Test",
            last_name="Reader",
            city="Saint Petersburg",
        )

        authors = {
            "Leo Tolstoy": self._upsert_author(
                full_name="Leo Tolstoy",
                birth_date="1828-09-09",
                death_date="1910-11-20",
                biography="Russian writer, author of War and Peace and Anna Karenina.",
            ),
            "Fyodor Dostoevsky": self._upsert_author(
                full_name="Fyodor Dostoevsky",
                birth_date="1821-11-11",
                death_date="1881-02-09",
                biography="Russian novelist known for psychological prose and philosophical themes.",
            ),
            "Jules Verne": self._upsert_author(
                full_name="Jules Verne",
                birth_date="1828-02-08",
                death_date="1905-03-24",
                biography="French novelist, a pioneer of adventure and science fiction.",
            ),
            "Agatha Christie": self._upsert_author(
                full_name="Agatha Christie",
                birth_date="1890-09-15",
                death_date="1976-01-12",
                biography="British writer known for detective fiction and Hercule Poirot.",
            ),
        }

        genres = {
            "Novel": self._upsert_genre(
                name="Novel",
                description="Long-form fictional prose.",
            ),
            "Classic": self._upsert_genre(
                name="Classic",
                description="Canonical works that remain widely read across generations.",
            ),
            "Science Fiction": self._upsert_genre(
                name="Science Fiction",
                description="Fiction exploring imagined science, technology, or futures.",
            ),
            "Detective": self._upsert_genre(
                name="Detective",
                description="Fiction centered on investigating crimes or mysteries.",
            ),
        }

        book_titles = {
            "War and Peace": self._upsert_book_title(
                title="War and Peace",
                description="Epic novel about Russian society during the Napoleonic era.",
                publication_year=1869,
                isbn="9780140447934",
                publisher="Penguin Classics",
                language="English",
                author_names=["Leo Tolstoy"],
                genre_names=["Novel", "Classic"],
                authors=authors,
                genres=genres,
            ),
            "Crime and Punishment": self._upsert_book_title(
                title="Crime and Punishment",
                description="Novel about morality, guilt, and redemption in Saint Petersburg.",
                publication_year=1866,
                isbn="9780140449136",
                publisher="Penguin Classics",
                language="English",
                author_names=["Fyodor Dostoevsky"],
                genre_names=["Novel", "Classic"],
                authors=authors,
                genres=genres,
            ),
            "Journey to the Center of the Earth": self._upsert_book_title(
                title="Journey to the Center of the Earth",
                description="Adventure novel about an expedition into a hidden world below Earth.",
                publication_year=1864,
                isbn="9780451532152",
                publisher="Signet Classics",
                language="English",
                author_names=["Jules Verne"],
                genre_names=["Science Fiction", "Classic"],
                authors=authors,
                genres=genres,
            ),
            "Murder on the Orient Express": self._upsert_book_title(
                title="Murder on the Orient Express",
                description="A Hercule Poirot mystery set aboard a luxury train.",
                publication_year=1934,
                isbn="9780007119318",
                publisher="HarperCollins",
                language="English",
                author_names=["Agatha Christie"],
                genre_names=["Detective", "Classic"],
                authors=authors,
                genres=genres,
            ),
        }

        book_items = {
            "INV-WP-001": self._upsert_book_item(
                inventory_number="INV-WP-001",
                book_title=book_titles["War and Peace"],
                status=BookItem.Status.AVAILABLE,
                location="Shelf A1",
            ),
            "INV-WP-002": self._upsert_book_item(
                inventory_number="INV-WP-002",
                book_title=book_titles["War and Peace"],
                status=BookItem.Status.UNAVAILABLE,
                location="Restoration Room",
            ),
            "INV-CP-001": self._upsert_book_item(
                inventory_number="INV-CP-001",
                book_title=book_titles["Crime and Punishment"],
                status=BookItem.Status.AVAILABLE,
                location="Shelf B2",
            ),
            "INV-JC-001": self._upsert_book_item(
                inventory_number="INV-JC-001",
                book_title=book_titles["Journey to the Center of the Earth"],
                status=BookItem.Status.AVAILABLE,
                location="Shelf C3",
            ),
            "INV-MO-001": self._upsert_book_item(
                inventory_number="INV-MO-001",
                book_title=book_titles["Murder on the Orient Express"],
                status=BookItem.Status.AVAILABLE,
                location="Shelf D4",
            ),
        }

        active_loan = self._upsert_active_loan(
            user=reader_user,
            book_item=book_items["INV-MO-001"],
            issued_at=timezone.now() - timedelta(days=2),
            due_date=timezone.localdate() + timedelta(days=12),
        )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write(
            "Staff user: admin@example.com / AdminPass123!"
        )
        self.stdout.write(
            "Reader user: reader@example.com / ReaderPass123!"
        )
        self.stdout.write(
            f"Authors: {Author.objects.count()}, Genres: {Genre.objects.count()}, "
            f"Book titles: {BookTitle.objects.count()}, Book items: {BookItem.objects.count()}, "
            f"Loans: {Loan.objects.count()}"
        )
        self.stdout.write(
            f"Active loan demo: {active_loan.book_item.inventory_number} -> {reader_user.email}"
        )

    def _upsert_user(self, *, email, username, password, is_staff, **extra_fields):
        user = User.objects.filter(Q(email=email) | Q(username=username)).first()
        if user is None:
            user = User(email=email, username=username)

        user.email = email
        user.username = username
        user.is_staff = is_staff
        user.is_superuser = is_staff
        user.is_active = True

        for field_name, value in extra_fields.items():
            setattr(user, field_name, value)

        user.set_password(password)
        user.save()
        return user

    def _upsert_author(self, **defaults):
        author, _ = Author.objects.update_or_create(
            full_name=defaults["full_name"],
            defaults=defaults,
        )
        return author

    def _upsert_genre(self, **defaults):
        genre, _ = Genre.objects.update_or_create(
            name=defaults["name"],
            defaults=defaults,
        )
        return genre

    def _upsert_book_title(
        self,
        *,
        title,
        description,
        publication_year,
        isbn,
        publisher,
        language,
        author_names,
        genre_names,
        authors,
        genres,
    ):
        book_title, _ = BookTitle.objects.update_or_create(
            isbn=isbn,
            defaults={
                "title": title,
                "description": description,
                "publication_year": publication_year,
                "publisher": publisher,
                "language": language,
            },
        )
        book_title.authors.set([authors[name] for name in author_names])
        book_title.genres.set([genres[name] for name in genre_names])
        return book_title

    def _upsert_book_item(self, *, inventory_number, book_title, status, location):
        book_item, _ = BookItem.objects.update_or_create(
            inventory_number=inventory_number,
            defaults={
                "book_title": book_title,
                "status": status,
                "location": location,
            },
        )
        return book_item

    def _upsert_active_loan(self, *, user, book_item, issued_at, due_date):
        active_loan = Loan.objects.filter(book_item=book_item, returned_at__isnull=True).first()
        if active_loan:
            if active_loan.user_id != user.id or active_loan.due_date != due_date:
                active_loan.user = user
                active_loan.issued_at = issued_at
                active_loan.due_date = due_date
                active_loan.returned_at = None
                active_loan.save()
            return active_loan

        return Loan.objects.create(
            user=user,
            book_item=book_item,
            issued_at=issued_at,
            due_date=due_date,
        )
