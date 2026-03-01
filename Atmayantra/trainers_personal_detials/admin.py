from django.contrib import admin
from .models import TrainerPersonalDetails

@admin.register(TrainerPersonalDetails)
class TrainerPersonalDetailsAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'contact_number', 'email', 'gender', 'city', 'state')
    list_editable = ('city', 'state')
    search_fields = ('full_name', 'contact_number', 'email')
    list_filter = ('gender', 'state', 'city')
