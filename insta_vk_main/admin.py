from django.contrib import admin
from .models import CustomUser, UserSettings
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(UserSettings)
