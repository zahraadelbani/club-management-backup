from django.contrib import admin
from django.utils import timezone
from .models import MembershipTerminationRequest

@admin.register(MembershipTerminationRequest)
class MembershipTerminationRequestAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'club', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'club', 'created_at')
    search_fields = ('membership__user__name', 'club__name')
    ordering = ('-created_at',)
    actions = ['approve_requests', 'reject_requests']
    date_hierarchy = 'created_at'

    def get_user_name(self, obj):
        return obj.membership.user.name
    get_user_name.short_description = "User"

    def approve_requests(self, request, queryset):
        queryset.update(status="approved", reviewed_at=timezone.now())
        self.message_user(request, "Selected requests have been approved.")

    def reject_requests(self, request, queryset):
        queryset.update(status="rejected", reviewed_at=timezone.now())
        self.message_user(request, "Selected requests have been rejected.")

    approve_requests.short_description = "Approve selected termination requests"
    reject_requests.short_description = "Reject selected termination requests"