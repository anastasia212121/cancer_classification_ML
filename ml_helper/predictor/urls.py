from django.urls import path
from . import views

urlpatterns = [
    path('', views.predict_view, name='predict'),
    path('history/', views.prediction_history_view, name='prediction_history'),
    
    # 🔽 ОБЯЗАТЕЛЬНО ДОБАВИТЬ: маршрут для API модального окна
    path('api/prediction/<int:pk>/', views.prediction_detail_api, name='prediction_detail_api'),
]
