from django.contrib import admin
from .models import DoctorBankDetails

@admin.register(DoctorBankDetails)
class DoctorBankDetailsAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'account_holder_name', 'account_number', 'account_type', 'ifsc_code')
    list_editable = ('account_type',)
    list_filter = ('account_type',)
    search_fields = ('doctor__contact_number', 'account_holder_name', 'account_number')
