from django.urls import path

from . import views

urlpatterns = [
    path('', views.FeedbackExportIndexView.as_view(), name='feedbackexport-index'),
    path('profiles/', views.FeedbackExportProfilesView.as_view(), name='feedbackexport-profiles'),
    path('events/', views.FeedbackExportEventsView.as_view(), name='feedbackexport-events'),
    path('access/', views.FeedbackExportAccessView.as_view(), name='feedbackexport-access'),
]
