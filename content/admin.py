from django.contrib import admin
from django.utils import timezone
from content.models import ApiUsageLog


@admin.register(ApiUsageLog)
class ApiUsageLogAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'timestamp')
    list_filter = ('endpoint',)
    readonly_fields = ('endpoint', 'timestamp')
    ordering = ('-timestamp',)

    def changelist_view(self, request, extra_context=None):
        now = timezone.now()
        monthly_count = ApiUsageLog.objects.filter(
            endpoint='places',
            timestamp__year=now.year,
            timestamp__month=now.month,
        ).count()
        extra_context = extra_context or {}
        extra_context['monthly_places_count'] = monthly_count
        return super().changelist_view(request, extra_context=extra_context)
