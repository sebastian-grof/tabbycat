from django.urls import path

from . import views

urlpatterns = [
    path('', views.FeedbackExportIndexView.as_view(), name='feedbackexport-index'),
    path('history/', views.ExportHistoryView.as_view(), name='feedbackexport-history'),
    path('jobs/', views.ExportJobCreateView.as_view(), name='feedbackexport-job-create'),
    path('jobs/<int:pk>/', views.ExportJobView.as_view(), name='feedbackexport-job'),
    path('jobs/<int:pk>/status/', views.ExportJobStatusView.as_view(), name='feedbackexport-job-status'),
    path('jobs/<int:pk>/items/', views.ExportJobItemsView.as_view(), name='feedbackexport-job-items'),
    path('jobs/<int:pk>/<str:action>/', views.ExportJobControlView.as_view(), name='feedbackexport-job-control'),
    path('activity/', views.JudgeDataExportView.as_view(), name='feedbackexport-activity'),
    path('profiles/', views.FeedbackExportProfilesRedirectView.as_view(), name='feedbackexport-profiles'),
    path('events/', views.JudgeDataExportView.as_view(), name='feedbackexport-events'),
    path('access/', views.FeedbackExportAccessView.as_view(), name='feedbackexport-access'),
]
