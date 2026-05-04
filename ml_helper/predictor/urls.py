from django.urls import path
from . import views

urlpatterns = [
    path('', views.predict_view, name='predict'),
    path('history/', views.prediction_history_view, name='prediction_history'),
    path('report/<int:pk>/', views.download_report, name='download_report'),
    path('api/prediction/<int:pk>/', views.prediction_detail_api, name='prediction_detail_api'),
]
