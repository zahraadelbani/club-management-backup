from django.contrib import admin
from .models import User,Membership
from django.contrib import admin
from django_otp_webauthn.models import (
    WebAuthnCredential,
    WebAuthnAttestation,
    WebAuthnUserHandle,
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("name", "email")

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "club", "membership_type", "created_at")
    list_filter = ("membership_type", "club")
    search_fields = ("user__name", "club__name")

@admin.register(WebAuthnCredential)
class WebAuthnCredentialAdmin(admin.ModelAdmin):
    list_display    = ('user', 'name', 'created_at')
    readonly_fields = (
        'credential_id',
        'public_key',
        'sign_count',
        # add any other fields you’d like to peek at
    )
    fields = (
        'user',
        'name',
        'confirmed',
        'credential_id',
        'public_key',
        'sign_count',
    )
admin.site.register(WebAuthnAttestation)
admin.site.register(WebAuthnUserHandle)
