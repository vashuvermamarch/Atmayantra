from django.contrib import admin
from django.apps import apps

for model in apps.get_app_config("trainers_certifications").get_models():
    admin.site.register(model)
