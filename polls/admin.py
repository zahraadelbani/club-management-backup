from django.contrib import admin
from .models import Poll, Choice, PollVote

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "club", "created_by", "created_at", "is_active")
    list_filter = ("is_active", "created_at", "club")
    search_fields = ("question", "club__name", "created_by__name")
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "poll", "vote_count")
    search_fields = ("text", "poll__question")


@admin.register(PollVote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user", "poll", "choice", "voted_at")
    list_filter = ("voted_at",)
    search_fields = ("user__name", "poll__question", "choice__text")
