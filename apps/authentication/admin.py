"""
Admin configuration for authentication models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RefreshTokenBlacklist


class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model
    """
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'is_active', 'is_staff')
    list_filter = ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_verified',)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('email', 'is_verified')}),
    )


@admin.register(RefreshTokenBlacklist)
class RefreshTokenBlacklistAdmin(admin.ModelAdmin):
    """
    Admin for RefreshTokenBlacklist model
    """
    list_display = ('user', 'blacklisted_at', 'token_preview')
    list_filter = ('blacklisted_at',)
    search_fields = ('user__email', 'user__username')
    ordering = ('-blacklisted_at',)
    readonly_fields = ('token', 'user', 'blacklisted_at')

    def token_preview(self, obj):
        """Show first 50 characters of token"""
        return obj.token[:50] + '...' if len(obj.token) > 50 else obj.token
    token_preview.short_description = 'Token Preview'


admin.site.register(User, UserAdmin)
