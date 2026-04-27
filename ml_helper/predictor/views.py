from django.shortcuts import render
from .ml_model import predict_from_dataframe
from .models import PredictionHistory  # ← импортируем модель
from genes.services.gene_annotator import GeneAnnotator
import pandas as pd
import logging

logger = logging.getLogger(__name__)

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

            # 🔽 СОХРАНЯЕМ В БД (только первый результат, если файл содержит один образец)
            if prediction and len(prediction) > 0:
                res = prediction[0]
                PredictionHistory.objects.create(
                    patient_id=request.POST.get("patient_id", ""),
                    predicted_label=res["label"],
                    confidence=res["probability"],
                    top_genes=res.get("top_genes", {}),
                    alternatives=res.get("alternatives", []),
                    input_file_name=file.name
                )

        except Exception as e:
            error = f"Ошибка обработки: {str(e)}"
            logger.error(error, exc_info=True)
            print(f"\n[ERROR] {e}")
            prediction = None
            top_genes = []

    return render(request, "index.html", {
        "prediction": prediction,
        "error": error,
        "top_genes": top_genes,
    })

def prediction_history_view(request):
    history = PredictionHistory.objects.all()[:100]  # последние 100 записей
    return render(request, "history.html", {"history": history}) 