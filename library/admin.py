from django.contrib import admin

from library.models import Author, BookItem, BookTitle, Genre, Loan


class BookItemInline(admin.TabularInline):
    model = BookItem
    extra = 0
    fields = ("inventory_number", "status", "location", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    show_change_link = True


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "birth_date", "death_date")
    search_fields = ("full_name",)
    ordering = ("full_name", "id")


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name", "id")


@admin.register(BookTitle)
class BookTitleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "publication_year",
        "publisher",
        "language",
        "isbn",
        "display_is_available",
        "created_at",
    )
    list_filter = ("publication_year", "language", "genres")
    search_fields = ("title", "isbn", "publisher", "authors__full_name")
    ordering = ("title", "id")
    filter_horizontal = ("authors", "genres")
    readonly_fields = ("display_is_available", "created_at", "updated_at")
    inlines = (BookItemInline,)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                    "publication_year",
                    "isbn",
                    "publisher",
                    "language",
                )
            },
        ),
        ("Relations", {"fields": ("authors", "genres")}),
        ("System", {"fields": ("display_is_available", "created_at", "updated_at")}),
    )

    @admin.display(boolean=True, description="Available")
    def display_is_available(self, obj):
        return obj.is_available


@admin.register(BookItem)
class BookItemAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_number",
        "book_title",
        "status",
        "location",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("inventory_number", "book_title__title", "location")
    ordering = ("inventory_number", "id")
    autocomplete_fields = ("book_title",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "book_item",
        "book_title",
        "user",
        "display_is_active",
        "issued_at",
        "due_date",
        "returned_at",
    )
    list_filter = ("returned_at", "issued_at", "due_date", "book_item__status")
    search_fields = (
        "user__email",
        "user__username",
        "book_item__inventory_number",
        "book_item__book_title__title",
    )
    ordering = ("-issued_at", "-id")
    autocomplete_fields = ("user", "book_item")
    readonly_fields = ("display_is_active", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user", "book_item", "issued_at", "due_date", "returned_at")}),
        ("System", {"fields": ("display_is_active", "created_at", "updated_at")}),
    )

    @admin.display(description="Book title")
    def book_title(self, obj):
        return obj.book_item.book_title

    @admin.display(boolean=True, description="Active")
    def display_is_active(self, obj):
        return obj.is_active
