from django.contrib import admin
from .models import Club, Event, RescheduleRequest, Meeting, Announcement, ClubDocument

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'quota', 'get_leader', 'member_count', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)

    def get_leader(self, obj):
        leader = obj.get_leader()
        return leader.user.name if leader else "—"
    get_leader.short_description = "Leader"

    def member_count(self, obj):
        return obj.get_member_count()
    member_count.short_description = "Members"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'event_date', 'approval_status', 'rescheduled','location_name','latitude','longitude', 'created_by','qr_code')
    list_filter = ('approval_status', 'club')
    search_fields = ('title', 'club__name')
    readonly_fields = ('rescheduled',)


@admin.register(RescheduleRequest)
class RescheduleRequestAdmin(admin.ModelAdmin):
    list_display = ('event', 'club_leader', 'requested_at', 'status')
    list_filter = ('status',)
    search_fields = ('event__title', 'club_leader__name')


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('id', 'club', 'date_time')
    search_fields = ('club__name', 'agenda')
    ordering = ('-date_time',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'club', 'title', 'visible', 'created_at','created_by')
    list_filter = ('visible', 'club')
    search_fields = ('title', 'club__name')


@admin.register(ClubDocument)
class ClubDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'uploaded_at')
    search_fields = ('title', 'club__name')
    ordering = ('-uploaded_at',)

from .models import EventAttendance

@admin.register(EventAttendance)
class EventAttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'is_attending', 'checked_in', 'responded_at', 'checked_in_at')
    list_filter = ('is_attending', 'checked_in', 'event__club')
    search_fields = ('user__name', 'event__title', 'event__club__name')
    ordering = ('-responded_at',)
