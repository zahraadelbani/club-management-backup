from django.contrib import admin
from .models import ClubAnalytics

@admin.register(ClubAnalytics)
class ClubAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'club',
        'total_members',
        'total_events',
        'total_polls',
        'members_percentage_display'
    )
    readonly_fields = ('total_members', 'total_events', 'total_polls')

    def members_percentage_display(self, obj):
        return f"{obj.members_percentage()}%"
    members_percentage_display.short_description = "Membership %"
