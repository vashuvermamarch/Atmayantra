from django.contrib import admin
from django.apps import apps

for model in apps.get_app_config("trainers_personal_detials").get_models():
    admin.site.register(model)
