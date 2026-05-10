from django.urls import path

from . import views

urlpatterns = [
    path('', views.PublicBreaksIndexView.as_view(), name='public-breaks-index'),
    path('<slug:season_slug>/', views.PublicBreaksSeasonView.as_view(), name='public-breaks-season'),
    path('<slug:season_slug>/regions/<int:region_id>/', views.PublicBreaksRegionView.as_view(), name='public-breaks-region'),
]
