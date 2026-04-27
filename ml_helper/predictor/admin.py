from django.contrib import admin
from .models import PredictionHistory

@admin.register(PredictionHistory)
class PredictionHistoryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "patient_id", "predicted_label", "confidence", "input_file_name")
    list_filter = ("predicted_label", "created_at")
    search_fields = ("patient_id", "predicted_label")
    date_hierarchy = "created_at"
