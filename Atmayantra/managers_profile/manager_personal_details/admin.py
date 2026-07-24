from django.contrib import admin
from .models import ManagerPersonalDetails

@admin.register(ManagerPersonalDetails)
class ManagerPersonalDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'employee_id', 'designation', 'email', 'location', 'date_of_joining', 'profile_photo_preview')
    list_editable = ('designation', 'location')
    search_fields = ('employee_name', 'employee_id', 'email', 'contact_number')
    list_filter = ('designation', 'location', 'date_of_joining')
    ordering = ('-created_at',)
    readonly_fields = ('profile_photo_preview',)

    @admin.display(description="Has Photo")
    def profile_photo_preview(self, obj):
        return "Yes" if obj.profile_photo else "No"
