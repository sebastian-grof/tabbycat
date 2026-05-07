from django.urls import include, path

from . import views

urlpatterns = [
    # Viewing
    path('',
        views.PublicResultsIndexView.as_view(),
        name='results-public-index'),
    path('debate/<int:pk>/scoresheets/',
        views.PublicBallotScoresheetsView.as_view(),
        name='results-public-scoresheet-view'),
    path('round/<int:round_seq>/', include([
        path('',
            views.PublicResultsForRoundView.as_view(),
            name='results-public-round'),

        # Public Ballots
        path('add/',
            views.PublicBallotSubmissionIndexView.as_view(),
            name='results-public-ballot-submission-index'),
        path('add/adjudicator/<int:adjudicator_pk>/',
            views.OldPublicNewBallotSetByIdUrlView.as_view(),
            name='old-results-public-ballotset-new-pk'),

        # Private Ballots
        path('adjudicator/<slug:url_key>/', include([
            path('debate/<int:debate_id>/add/',
                views.OldPublicNewBallotSetByRandomisedUrlView.as_view(),
                name='results-public-ballotset-new-randomised-debate'),
            path('debate/<int:debate_id>/view/',
                views.AdjudicatorPrivateUrlBallotScoresheetView.as_view(),
                name='results-privateurl-scoresheet-view-debate'),
            path('debate/<int:debate_id>/download-ballot/',
                views.AdjudicatorPrivateUrlJDLBallotDownloadView.as_view(),
                name='results-privateurl-jdl-ballot-xlsx-debate'),
            path('add/',
                views.OldPublicNewBallotSetByRandomisedUrlView.as_view(),
                name='results-public-ballotset-new-randomised'),
            path('view/',
                views.AdjudicatorPrivateUrlBallotScoresheetView.as_view(),
                name='results-privateurl-scoresheet-view'),
            path('download-ballot/',
                views.AdjudicatorPrivateUrlJDLBallotDownloadView.as_view(),
                name='results-privateurl-jdl-ballot-xlsx'),
        ])),

        path('speaker/<slug:url_key>/',
            views.SpeakerPrivateUrlBallotScoresheetView.as_view(),
            name='speaker-results-privateurl-scoresheet'),
        path('speaker/<slug:url_key>/download-ballot/',
            views.SpeakerPrivateUrlJDLBallotDownloadView.as_view(),
            name='speaker-results-privateurl-jdl-ballot-xlsx'),
    ])),

    path('added/',
        views.PostPublicBallotSetSubmissionURLView.as_view(),
        name='post-results-public-ballotset-new'),
]
