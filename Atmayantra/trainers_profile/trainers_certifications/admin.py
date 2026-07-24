from django.contrib import admin
from .models import TrainerCertification

@admin.register(TrainerCertification)
class TrainerCertificationAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'highest_degree', 'specialization', 'year_of_graduation', 'yoga_certified')
    list_editable = ('yoga_certified',)
    list_filter = ('yoga_certified', 'highest_degree')
    search_fields = ('trainer__full_name', 'specialization', 'registration_number')
