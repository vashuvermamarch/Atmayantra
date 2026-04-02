from django.contrib import admin
from .models import DoctorCertification

@admin.register(DoctorCertification)
class DoctorCertificationAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'highest_degree', 'year_of_graduation', 'registration_number', 'yoga_certified')
    list_editable = ('yoga_certified',)
    list_filter = ('yoga_certified', 'highest_degree')
    search_fields = ('doctor__full_name', 'registration_number')
