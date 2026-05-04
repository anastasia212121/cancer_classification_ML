from django.db.models import Q
from predictor.models import CancerLabelTranslation

def translate_label(label):
    if not label:
        return "—"

    label = label.strip()

    obj = CancerLabelTranslation.objects.filter(
        Q(english_name__iexact=label)
    ).first()

    return obj.russian_name if obj else label
