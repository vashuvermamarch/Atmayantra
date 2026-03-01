from django.contrib import admin
from .models import AdminUser


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ("contact_number", "name", "email", "is_verified")
    list_editable = ("is_verified",)
    search_fields = ("contact_number", "name", "email")
    list_filter = ("is_verified",)
    ordering = ("contact_number",)
