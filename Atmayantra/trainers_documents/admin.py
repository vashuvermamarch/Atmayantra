from django.contrib import admin

from .models import TrainerDocument


@admin.register(TrainerDocument)
class TrainerDocumentAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'document_type', 'side', 'document_mimetype', 'uploaded_at')
    list_filter = ('document_type', 'side')
    search_fields = ('trainer__full_name', 'document_type')
