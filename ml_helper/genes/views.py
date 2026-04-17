from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from .services.gene_annotator import GeneAnnotator
import json

@method_decorator(require_http_methods(["POST"]), name='dispatch')
class GeneAnnotationView(View):
    annotator = GeneAnnotator()
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            gene_importance = data.get('gene_importance', {})
            top_n = min(int(data.get('top_n', 10)), 50)
            
            if not gene_importance:
                return JsonResponse({'error': 'gene_importance is required'}, status=400)
            
            results = self.annotator.annotate_genes(gene_importance, top_n=top_n)
            
            return JsonResponse({'success': True, 'genes': results})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
