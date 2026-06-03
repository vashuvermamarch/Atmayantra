from django.db import models
from managers_profile.manager_personal_details.models import ManagerPersonalDetails


class ManagerDocument(models.Model):

    manager = models.ForeignKey(
        ManagerPersonalDetails,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    manager_doc_id = models.IntegerField(null=True, blank=True)

    doc_type = models.CharField(max_length=100)

    file = models.BinaryField()
    file_mimetype = models.CharField(max_length=100, null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("manager", "manager_doc_id")

    # ⭐ AUTO GENERATE ID HERE
    def save(self, *args, **kwargs):

        if not self.manager_doc_id:

            last_doc = ManagerDocument.objects.filter(
                manager=self.manager
            ).order_by("-manager_doc_id").first()

            if last_doc:
                self.manager_doc_id = last_doc.manager_doc_id + 1
            else:
                self.manager_doc_id = 1

        super().save(*args, **kwargs)
