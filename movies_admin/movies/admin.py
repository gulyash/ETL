from django.contrib import admin
from .models import Filmwork, Person, Genre, PersonFilmWork, FilmworkGenre


class PersonFilmWorkInline(admin.TabularInline):
    model = PersonFilmWork
    extra = 0


class FilmworkGenreInline(admin.TabularInline):
    model = FilmworkGenre
    extra = 0


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'creation_date', 'rating')
    list_filter = ('type',)
    search_fields = ('title', 'description', 'id')

    fields = (
        'title', 'type', 'description', 'creation_date', 'certificate',
        'file_path', 'rating',
    )
    inlines = [
        PersonFilmWorkInline,
        FilmworkGenreInline
    ]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date')
    fields = ('full_name', 'birth_date')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    fields = ('name', 'description')
