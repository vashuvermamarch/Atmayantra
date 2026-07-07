from django.contrib import admin

from .models import DoctorPersonalDetails, DoctorProfilePhoto


@admin.register(DoctorPersonalDetails)
class DoctorPersonalDetailsAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'contact_number', 'email', 'gender', 'city', 'state')
    list_editable = ('city', 'state')
    search_fields = ('full_name', 'contact_number', 'email')
    list_filter = ('gender', 'state', 'city')

@admin.register(DoctorProfilePhoto)
class DoctorProfilePhotoAdmin(admin.ModelAdmin):
    list_display = ('doctor',)
    search_fields = ('doctor__full_name', 'doctor__contact_number')
