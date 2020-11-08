import json

from django.contrib import admin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.urls import path

from .models import EmailSubscriber


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    list_display = ("id", "email", "created_at")
    ordering = ("-created_at",)

    # Inject chart data on page load in the ChangeList view
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        queryset = response.context_data["cl"].queryset
        chart_data = self.chart_data(queryset)
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        response.context_data.update({"chart_data": as_json})
        return response

    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
            path("chart_data/", self.admin_site.admin_view(self.chart_data_endpoint))
        ]
        # NOTE! Our custom urls have to go before the default urls, because they
        # default ones match anything.
        return extra_urls + urls

    # JSON endpoint for generating chart data that is used for dynamic loading
    # via JS.
    def chart_data_endpoint(self, request):
        chart_data = self.chart_data(EmailSubscriber.objects)

        return JsonResponse(list(chart_data), safe=False)

    def chart_data(self, queryset):
        return (
            queryset.annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(y=Count("id"))
            .order_by("-date")
        )
