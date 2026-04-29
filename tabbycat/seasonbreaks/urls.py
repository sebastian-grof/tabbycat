from django.urls import path

from . import views

urlpatterns = [
    path('', views.BreaksIndexView.as_view(), name='seasonbreaks-index'),
    path('access/', views.BreaksAccessView.as_view(), name='seasonbreaks-access'),
    path('<slug:season_slug>/', views.SeasonOverviewView.as_view(), name='seasonbreaks-season-overview'),
    path('<slug:season_slug>/tournaments/', views.SeasonTournamentsView.as_view(), name='seasonbreaks-tournaments'),
    path('<slug:season_slug>/identities/', views.SeasonIdentitiesView.as_view(), name='seasonbreaks-identities'),
    path('<slug:season_slug>/teams/', views.SeasonTeamsView.as_view(), name='seasonbreaks-teams'),
    path('<slug:season_slug>/speakers/', views.SeasonSpeakersView.as_view(), name='seasonbreaks-speakers'),
    path('<slug:season_slug>/quotas/', views.SeasonQuotasView.as_view(), name='seasonbreaks-quotas'),
    path('<slug:season_slug>/rankings/', views.SeasonRankingsView.as_view(), name='seasonbreaks-rankings'),
    path('<slug:season_slug>/adjudicators/', views.SeasonAdjudicatorsView.as_view(), name='seasonbreaks-adjudicators'),
]
