from django.contrib import admin

from .models import ManagerDocument


@admin.register(ManagerDocument)
class ManagerDocumentAdmin(admin.ModelAdmin):
    list_display = ('manager', 'manager_doc_id', 'doc_type', 'file_mimetype', 'uploaded_at')
    list_filter = ('doc_type',)
    search_fields = ('manager__employee_name', 'doc_type')
