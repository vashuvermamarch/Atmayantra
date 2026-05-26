from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone_number', 'user_type', 'is_staff', 'is_active')
    list_editable = ('is_active', 'is_staff', 'user_type')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('phone_number', 'user_type')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Extra Fields', {'fields': ('phone_number', 'user_type')}),
    )
    search_fields = ('username', 'email', 'phone_number')
