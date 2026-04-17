from django.contrib import admin
from .models import Translation


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ("source_text", "translated_text", "created_at")
    search_fields = ("source_text", "translated_text")
