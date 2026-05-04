from django.contrib import admin
from .models import PredictionHistory, CancerLabelTranslation
from predictor.services.label_translator import translate_label


@admin.register(PredictionHistory)
class PredictionHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "patient_id",
        "get_predicted_label_ru",
        "confidence",
        "input_file_name",
    )

    list_filter = ("predicted_label", "created_at")
    search_fields = ("patient_id", "predicted_label")
    date_hierarchy = "created_at"

    def get_predicted_label_ru(self, obj):
        return translate_label(obj.predicted_label)

    get_predicted_label_ru.short_description = "Диагноз (RU)"

@admin.register(CancerLabelTranslation)
class CancerLabelTranslationAdmin(admin.ModelAdmin):
    list_display = ("english_name", "russian_name")
    search_fields = ("english_name", "russian_name")