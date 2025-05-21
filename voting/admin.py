from django.contrib import admin
from .models import Election, Candidate, Vote, Position

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'election', 'votes')
    list_filter = ('position', 'election')
    readonly_fields = ('votes',)

class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'position', 'candidate', 'election', 'timestamp')
    list_filter = ('election', 'position')

admin.site.register(Election)
admin.site.register(Candidate, CandidateAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Position)
