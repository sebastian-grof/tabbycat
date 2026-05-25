from django.urls import path

from . import views

urlpatterns = [
    path('', views.FeedbackExportIndexView.as_view(), name='feedbackexport-index'),
    path('activity/', views.JudgeDataExportView.as_view(), name='feedbackexport-activity'),
    path('profiles/', views.FeedbackExportProfilesRedirectView.as_view(), name='feedbackexport-profiles'),
    path('events/', views.JudgeDataExportView.as_view(), name='feedbackexport-events'),
    path('access/', views.FeedbackExportAccessView.as_view(), name='feedbackexport-access'),
]
