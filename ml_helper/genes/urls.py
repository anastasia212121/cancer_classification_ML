from django.urls import path
from .views import GeneAnnotationView

app_name = 'genes'
urlpatterns = [
    path('api/genes/annotate/', GeneAnnotationView.as_view(), name='annotate'),
]
