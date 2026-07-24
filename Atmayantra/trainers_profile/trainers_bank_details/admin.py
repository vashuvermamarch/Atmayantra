from django.contrib import admin
from .models import TrainerBankDetails

@admin.register(TrainerBankDetails)
class TrainerBankDetailsAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'account_holder_name', 'account_number', 'account_type', 'ifsc_code')
    list_editable = ('account_type',)
    list_filter = ('account_type',)
    search_fields = ('trainer__full_name', 'account_holder_name', 'account_number')
