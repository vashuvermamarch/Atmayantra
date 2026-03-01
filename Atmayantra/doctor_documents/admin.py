from django.contrib import admin
from .models import DoctorDocument

@admin.register(DoctorDocument)
class DoctorDocumentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'doc_type', 'side', 'filename', 'content_type')
    list_filter = ('doc_type', 'content_type')
    search_fields = ('doctor__full_name', 'filename', 'doc_type')
