import logging
import pandas as pd

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .ml_model import predict_from_dataframe
from .models import PredictionHistory
from genes.services.gene_annotator import GeneAnnotator
from predictor.services.explanation_generator import ExplanationGenerator

from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle

from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

from predictor.services.label_translator import translate_label

logger = logging.getLogger(__name__)


@require_GET
def prediction_detail_api(request, pk):
    try:
        pred = PredictionHistory.objects.get(pk=int(pk))
        return JsonResponse({
            "id": pred.id,
            "patient_id": pred.patient_id or "—",
            "created_at": pred.created_at.isoformat(),
            "input_file_name": pred.input_file_name or "—",
            "predicted_label": translate_label(pred.predicted_label),
            "confidence": pred.confidence,
            "alternatives": pred.alternatives if isinstance(pred.alternatives, list) else [],
            "top_genes": pred.top_genes if isinstance(pred.top_genes, dict) else {},
            "explanation": pred.explanation,
        })
    except PredictionHistory.DoesNotExist:
        return JsonResponse({"error": "Запись не найдена"}, status=404)
    except ValueError:
        return JsonResponse({"error": "Некорректный ID"}, status=400)


def predict_view(request):
    prediction = None
    error = None
    top_genes = []
    explanation = ""
    report_id = None

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

            if prediction:
                for item in prediction:
                    item["label"] = translate_label(item["label"])

                    if item.get("alternatives"):
                        for alt in item["alternatives"]:
                            alt["label"] = translate_label(alt["label"])

            if gene_importance:
                sorted_genes = sorted(gene_importance.items(), key=lambda x: x[1], reverse=True)[:10]
                top_importance = {g: imp for g, imp in sorted_genes}

                annotator = GeneAnnotator(delay_between_requests=0.2)
                top_genes = annotator.annotate_genes(top_importance, top_n=10)

            if prediction:
                generator = ExplanationGenerator()
                explanation = generator.generate(prediction[0], top_genes or [])

            if prediction and len(prediction) > 0:
                res = prediction[0]
                
                obj = PredictionHistory.objects.create(
                    patient_id=request.POST.get("patient_id", "").strip() or None,
                    predicted_label=translate_label(res["label"]),
                    confidence=res["probability"],
                    top_genes=res.get("top_genes", {}),
                    alternatives=res.get("alternatives", []),
                    input_file_name=file.name,
                    explanation=explanation
                )

                report_id = obj.id

        except Exception as e:
            error = f"Ошибка обработки: {str(e)}"
            logger.error(error, exc_info=True)
            prediction = None
            top_genes = []
            explanation = ""
            report_id = None

    return render(request, "index.html", {
        "prediction": prediction,
        "error": error,
        "top_genes": top_genes,
        "explanation": explanation,
        "report_id": report_id
    })


def prediction_history_view(request):
    query = request.GET.get('q', '').strip()

    qs = PredictionHistory.objects.all().order_by('-created_at')

    if query:
        qs = qs.filter(patient_id__icontains=query)

    for obj in qs:
        obj.predicted_label_ru = translate_label(obj.predicted_label)

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

def download_report(request, pk):
    pdfmetrics.registerFont(TTFont('DejaVu', 'predictor/fonts/DejaVuSans.ttf'))

    pred = PredictionHistory.objects.get(pk=pk)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    doc.title = f"Report_{pred.predicted_label}_{pk}"
    doc.author = "Cancer Classification System"
    doc.subject = "Gene expression prediction report"

    styles = getSampleStyleSheet()

    normal_style = ParagraphStyle(
        name='NormalCyrillic',
        fontName='DejaVu',
        fontSize=11
    )

    title_style = ParagraphStyle(
        name='TitleCyrillic',
        fontName='DejaVu',
        fontSize=18,
        leading=22
    )

    heading_style = ParagraphStyle(
        name='HeadingCyrillic',
        fontName='DejaVu',
        fontSize=14,
        leading=18
    )    
    story = []

    story.append(Paragraph("Отчёт по предсказанию", title_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Пациент: {pred.patient_id or '—'}", normal_style))
    story.append(Paragraph(f"Диагноз: {translate_label(pred.predicted_label)}", normal_style))
    story.append(Paragraph(f"Уверенность: {pred.confidence:.2f}%", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Интерпретация:", heading_style))
    story.append(Paragraph(pred.explanation or "—", normal_style))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Топ-гены", heading_style))

    data = [["Ген", "Вклад", "Онкоген"]]

    top_genes = pred.top_genes or {}

    # сортировка по важности
    sorted_genes = sorted(top_genes.items(), key=lambda x: x[1], reverse=True)

    annotator = GeneAnnotator(delay_between_requests=0.2)

    annotated_genes = annotator.annotate_genes(
        {g: imp for g, imp in sorted_genes[:10]},
        top_n=10
    )

    for item in annotated_genes:
        data.append([
            item["gene"],
            f"{item.get('importance', 0):.4f}",
            "да" if item.get("cancer_related") else "—"
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))

    story.append(table)

    doc.build(story)

    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{pk}.pdf"'
    return response
