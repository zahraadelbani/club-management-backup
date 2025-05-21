from django.contrib import admin
from clubs.models import ClubDocument

""" @admin.register(ClubDocument)
class ClubDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'uploaded_at')
    search_fields = ('title', 'club__name')
    list_filter = ('club', 'uploaded_at') """