from django.contrib import admin
from .models import ManagerBankDetails

@admin.register(ManagerBankDetails)
class ManagerBankDetailsAdmin(admin.ModelAdmin):
    list_display = ('manager', 'account_holder_name', 'bank_name', 'account_number', 'account_type', 'ifsc_code')
    list_filter = ('bank_name', 'account_type')
    search_fields = ('manager__employee_name', 'account_holder_name', 'account_number')
