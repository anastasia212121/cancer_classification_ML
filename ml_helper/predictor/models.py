from django.db import models

class PredictionHistory(models.Model):
    patient_id = models.CharField("ID пациента", max_length=100, blank=True, null=True)
    created_at = models.DateTimeField("Дата предсказания", auto_now_add=True)
    predicted_label = models.CharField("Предсказанный класс", max_length=255)
    confidence = models.FloatField("Уверенность (%)")
    top_genes = models.JSONField("Топ-10 генов", default=dict)
    alternatives = models.JSONField("Альтернативы", default=list)
    explanation = models.TextField(null=True, blank=True)
    input_file_name = models.CharField("Имя файла", max_length=255, blank=True, null=True)

    def __str__(self):
        pid = self.patient_id or "—"
        return f"{pid} | {self.predicted_label} ({self.confidence:.1f}%) | {self.created_at:%d.%m.%Y %H:%M}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Предсказание"
        verbose_name_plural = "История предсказаний"

class CancerLabelTranslation(models.Model):
    english_name = models.CharField("English label", max_length=255, unique=True)
    russian_name = models.CharField("Russian label", max_length=255)

    class Meta:
        verbose_name = "Перевод класса опухоли"
        verbose_name_plural = "Переводы классов опухолей"

    def __str__(self):
        return f"{self.english_name} → {self.russian_name}"
