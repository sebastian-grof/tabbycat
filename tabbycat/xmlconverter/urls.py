from django.urls import path

from . import views

urlpatterns = [
    path('', views.ConverterView.as_view(), name='xmlconverter-index'),
    path('access/', views.ConverterAccessView.as_view(), name='xmlconverter-access'),
]
