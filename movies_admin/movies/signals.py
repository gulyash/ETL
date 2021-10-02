import datetime

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from movies.models import Filmwork


@receiver(post_save, sender="movies.Person")
def congratulatory(sender, instance, created, **kwargs):
    if created and instance.birth_date == datetime.date.today():
        print(f"У {instance.full_name} сегодня день рождения! 🥳")


def touch_movies(filmworks):
    q = "update content.film_work set updated_at = %s where id in %s"
    t = datetime.datetime.utcnow()
    ids = tuple(str(item.id) for item in filmworks)
    Filmwork.objects.raw(q, (t, ids))


@receiver(post_save, sender="movies.Genre")
def save_genre(instance, **kwargs):
    touch_movies(instance.filmwork_set.all())


@receiver(pre_delete, sender="movies.Genre")
def delete_genre(instance, **kwargs):
    touch_movies(instance.filmwork_set.all())


@receiver(post_save, sender="movies.Person")
def save_person(instance, **kwargs):
    touch_movies(instance.filmwork_set.all())


@receiver(pre_delete, sender="movies.Person")
def delete_person(instance, **kwargs):
    touch_movies(instance.filmwork_set.all())


@receiver(post_save, sender="movies.FilmworkGenre")
def save_film_genre(instance, **kwargs):
    touch_movies([instance.film_work])


@receiver(pre_delete, sender="movies.FilmworkGenre")
def delete_film_genre(sender, instance, **kwargs):
    touch_movies([instance.film_work])


@receiver(post_save, sender="movies.PersonFilmWork")
def save_film_person(sender, instance, **kwargs):
    touch_movies([instance.film_work])


@receiver(pre_delete, sender="movies.PersonFilmWork")
def delete_film_person(sender, instance, **kwargs):
    touch_movies([instance.film_work])
