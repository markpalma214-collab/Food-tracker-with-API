from django.contrib import admin
from .models import FoodEntry, UserProfile

admin.site.register(FoodEntry)
admin.site.register(UserProfile)
