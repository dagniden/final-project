import django_filters

from library.models import BookItem, BookTitle


class BookTitleFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    author = django_filters.CharFilter(
        field_name="authors__full_name",
        lookup_expr="icontains",
    )
    author_id = django_filters.NumberFilter(field_name="authors__id")
    genre = django_filters.CharFilter(
        field_name="genres__name",
        lookup_expr="icontains",
    )
    genre_id = django_filters.NumberFilter(field_name="genres__id")
    available = django_filters.BooleanFilter(method="filter_available")

    class Meta:
        model = BookTitle
        fields = [
            "title",
            "author",
            "author_id",
            "genre",
            "genre_id",
            "publication_year",
            "isbn",
            "available",
        ]

    def filter_available(self, queryset, name, value):
        del name

        available_queryset = queryset.filter(items__status=BookItem.Status.AVAILABLE)
        if value:
            return available_queryset
        return queryset.exclude(items__status=BookItem.Status.AVAILABLE)
