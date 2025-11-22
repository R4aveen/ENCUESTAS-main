from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "group", "telefono", "cargo"]
    search_fields = ["user__username", "user__email", "user__first_name", "user__last_name", "cargo"]
    list_filter = ["group"]
