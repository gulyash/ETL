from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from movies.models import Filmwork, RoleType


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ["get"]

    @staticmethod
    def _aggregate_person(role: str):
        return ArrayAgg(
            "persons__full_name", distinct=True, filter=Q(personfilmwork__role=role)
        )

    @classmethod
    def get_queryset(cls):
        return (
            Filmwork.objects.prefetch_related("genres", "persons")
            .values()
            .annotate(
                genres=ArrayAgg("genres__name", distinct=True),
                actors=cls._aggregate_person(RoleType.ACTOR),
                directors=cls._aggregate_person(RoleType.DIRECTOR),
                writers=cls._aggregate_person(RoleType.WRITER),
            )
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    model = Filmwork
    http_method_names = ["get"]
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            self.get_queryset(), self.paginate_by
        )
        return {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev": page.previous_page_number() if page.has_previous() else None,
            "next": page.next_page_number() if page.has_next() else None,
            "results": list(queryset),
        }


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    def get_context_data(self, **kwargs):
        return kwargs["object"]
