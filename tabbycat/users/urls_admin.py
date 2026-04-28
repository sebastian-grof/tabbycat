from django.urls import path

from . import views


urlpatterns = [
    path('roles/', views.RoleManagementView.as_view(), name='user-role-management'),
    path('invite/', views.InviteUserView.as_view(), name='invite-user'),
    path('accept/<uidb64>/<token>/', views.AcceptInvitationView.as_view(), name='accept-invitation'),
]
