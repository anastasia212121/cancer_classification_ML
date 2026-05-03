import logging
import pandas as pd

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .ml_model import predict_from_dataframe
from .models import PredictionHistory
from genes.services.gene_annotator import GeneAnnotator

logger = logging.getLogger(__name__)


@require_GET
def prediction_detail_api(request, pk):
    """API: возвращает полные данные предсказания по ID"""
    try:
        pred = PredictionHistory.objects.get(pk=int(pk))
        return JsonResponse({
            "id": pred.id,
            "patient_id": pred.patient_id or "—",
            "created_at": pred.created_at.isoformat(),
            "input_file_name": pred.input_file_name or "—",
            "predicted_label": pred.predicted_label,
            "confidence": pred.confidence,
            "alternatives": pred.alternatives if isinstance(pred.alternatives, list) else [],
            "top_genes": pred.top_genes if isinstance(pred.top_genes, dict) else {},
        })
    except PredictionHistory.DoesNotExist:
        return JsonResponse({"error": "Запись не найдена"}, status=404)
    except ValueError:
        return JsonResponse({"error": "Некорректный ID"}, status=400)


def predict_view(request):
    prediction = None
    error = None
    top_genes = []

    if request.method == "POST":
        try:
            file = request.FILES.get("file")
            if not file:
                raise ValueError("Файл не загружен. Выберите CSV.")

            if not file.name.lower().endswith('.csv'):
                raise ValueError("Разрешены только файлы формата CSV.")

            if file.size > 10 * 1024 * 1024:
                raise ValueError("Размер файла превышает допустимый лимит (10 МБ).")

            df = pd.read_csv(file)
            if df.empty:
                raise ValueError("Загруженный файл пуст.")

            prediction, gene_importance = predict_from_dataframe(df)

            if gene_importance:
                sorted_genes = sorted(gene_importance.items(), key=lambda x: x[1], reverse=True)[:10]
                top_importance = {g: imp for g, imp in sorted_genes}

                annotator = GeneAnnotator(delay_between_requests=0.2)
                top_genes = annotator.annotate_genes(top_importance, top_n=10)

            # Сохраняем в БД
            if prediction and len(prediction) > 0:
                res = prediction[0]
                PredictionHistory.objects.create(
                    patient_id=request.POST.get("patient_id", "").strip() or None,
                    predicted_label=res["label"],
                    confidence=res["probability"],
                    top_genes=res.get("top_genes", {}),
                    alternatives=res.get("alternatives", []),
                    input_file_name=file.name
                )

        except Exception as e:
            error = f"Ошибка обработки: {str(e)}"
            logger.error(error, exc_info=True)
            prediction = None
            top_genes = []

    return render(request, "index.html", {
        "prediction": prediction,
        "error": error,
        "top_genes": top_genes,
    })


def prediction_history_view(request):
    query = request.GET.get('q', '').strip()
    qs = PredictionHistory.objects.all().order_by('-created_at')
    
    if query:
        qs = qs.filter(patient_id__icontains=query)
        
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    return render(request, 'history.html', {
        'page_obj': page_obj,
        'query': query
    })
