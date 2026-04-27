from django.urls import path
from . import views


urlpatterns = [
    path('', views.predict_view, name='predict'),
    path('history/', views.prediction_history_view, name='prediction_history'),  # ← новый маршрут
]
