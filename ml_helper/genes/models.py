from django.db import models


class Translation(models.Model):
    source_text = models.TextField()
    normalized_text = models.TextField(unique=True)
    translated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.source_text
