from django.contrib import admin
from .models import Feedback

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("display_user", "club", "category", "status", "created_at")
    list_filter = ("category", "status", "created_at")
    search_fields = ("submitted_by__name", "club__name", "content")
    readonly_fields = ("submitted_by", "category", "club", "created_at")

    def display_user(self, obj):
        return obj.display_user()
    display_user.short_description = "Submitted By"

admin.site.register(Feedback, FeedbackAdmin)

