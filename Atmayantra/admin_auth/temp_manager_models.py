from django.db import models


class TempManagerPersonal(models.Model):

    employee_name = models.CharField(max_length=200)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    employee_id = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()
    date_of_joining = models.DateField()
    location = models.CharField(max_length=200)

    # ✅ STORE PROFILE PHOTO IN DB
    profile_photo = models.BinaryField(null=True, blank=True)
    profile_photo_mimetype = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class TempManagerDocument(models.Model):

    manager = models.ForeignKey(TempManagerPersonal, on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=100)

    # ✅ STORE DOC IN DB
    file = models.BinaryField()
    file_mimetype = models.CharField(max_length=100, null=True, blank=True)


class TempManagerBank(models.Model):

    manager = models.OneToOneField(TempManagerPersonal, on_delete=models.CASCADE)

    account_holder_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20)
    upi_id = models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20)
