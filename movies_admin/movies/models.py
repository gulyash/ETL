import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genre(TimeStampedMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("genre")
        verbose_name_plural = _("genres")
        db_table = '"content"."genre"'


class FilmworkGenre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    film_work = models.ForeignKey("Filmwork", on_delete=models.CASCADE)
    genre = models.ForeignKey("Genre", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '"content"."genre_film_work"'


class Person(TimeStampedMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(_("full_name"), max_length=255)
    birth_date = models.DateField(_("birth_date"), blank=True, null=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = _("person")
        verbose_name_plural = _("persons")
        db_table = '"content"."person"'


class RoleType(models.TextChoices):
    ACTOR = "actor", _("actor")
    DIRECTOR = "director", _("director")
    WRITER = "writer", _("writer")


class PersonFilmWork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    film_work = models.ForeignKey("Filmwork", on_delete=models.CASCADE)
    person = models.ForeignKey("Person", on_delete=models.CASCADE)
    role = models.CharField(_("role"), max_length=20, choices=RoleType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '"content"."person_film_work"'


class FilmworkType(models.TextChoices):
    MOVIE = "movie", _("movie")
    TV_SHOW = "tv_show", _("TV Show")


class Filmwork(TimeStampedMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True, null=True)
    creation_date = models.DateField(_("creation_date"), blank=True, null=True)
    certificate = models.TextField(_("certificate"), blank=True, null=True)
    file_path = models.FileField(
        _("file"), upload_to="film_works/", blank=True, null=True
    )
    rating = models.FloatField(
        _("rating"),
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        blank=True,
        null=True,
    )
    type = models.CharField(_("type"), max_length=20, choices=FilmworkType.choices)
    genres = models.ManyToManyField(Genre, through="FilmworkGenre")
    persons = models.ManyToManyField(Person, through="PersonFilmWork")

    class Meta:
        verbose_name = _("film_work")
        verbose_name_plural = _("filmworks")
        db_table = '"content"."film_work"'
