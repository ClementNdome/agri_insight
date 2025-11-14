from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    list_display = ('username', 'email', 'is_farmer', 'email_verified', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_farmer', 'email_verified', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'bio')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Agriculture Profile', {
            'fields': ('is_farmer', 'bio', 'crop_interests', 'phone_number', 'preferred_units')
        }),
        ('Verification', {
            'fields': ('email_verified',)
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Agriculture Profile', {
            'fields': ('is_farmer', 'crop_interests', 'preferred_units')
        }),
    )

