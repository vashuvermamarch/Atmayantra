from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_no = models.CharField(max_length=15, unique=True)
    message = models.TextField()

    def __str__(self):
        return self.name