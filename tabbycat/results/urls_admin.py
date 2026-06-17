from django.urls import path

from . import criterion_views, views

urlpatterns = [
    # Criteria
    path('criteria/',
        criterion_views.CriterionManagementView.as_view(),
        name='criterion-management'),

    # Viewing
    path('round/<int:round_seq>/',
        views.AdminResultsEntryForRoundView.as_view(),
        name='results-round-list'),

    # Bulk ballot downloads
    path('round/<int:round_seq>/download-ballots/',
        views.RoundBallotsDownloadView.as_view(),
        name='results-round-download-ballots'),
    path('download-ballots/',
        views.TournamentBallotsDownloadView.as_view(),
        name='results-tournament-download-ballots'),

    # Inline Actions
    path('round/<int:round_seq>/postpone/<int:debate_id>/',
        views.PostponeDebateView.as_view(),
        name='results-postpone-debate'),

    # Ballots
    path('ballots/<int:pk>/edit/',
        views.AdminEditBallotSetView.as_view(),
        name='results-ballotset-edit'),
    path('debate/<int:debate_id>/new/',
        views.AdminNewBallotSetView.as_view(),
        name='results-ballotset-new'),

    # Ballots Old
    path('ballots/old/<int:pk>/edit/',
        views.OldAdminEditBallotSetView.as_view(),
        name='old-results-ballotset-edit'),
    path('debate/old/<int:debate_id>/new/',
        views.OldAdminNewBallotSetView.as_view(),
        name='old-results-ballotset-new'),

    path('debate/<int:debate_id>/merge/latest/',
        views.AdminMergeLatestBallotsView.as_view(),
        name='results-merge-latest'),
]
